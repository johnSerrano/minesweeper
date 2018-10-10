import itertools
import random
from collections import defaultdict, namedtuple

DEFAULT_X = 15
DEFAULT_Y = 15
DEFAULT_NUM_MINES = 40


class HitMineException(Exception):
    pass


class Square(object):
    def __init__(self, hidden=True, mine=False):
        self.hidden = hidden
        self.mine = mine
        self.adjacent = -1


class MinesweeperBoard(object):
    def __init__(self, board):
        assert set(board) <= set("\n .X"), "Board contains invalid characters"

        lines = [line.split() for line in board.split("\n")]
        l = len(lines[0])
        assert all(len(line) == l for line in lines), "Board should be rectangular"
        self.x = len(lines)
        self.y = l

        self.squares = []
        for line in lines:
            self.squares.append([Square(mine=square=='X') for square in line])

        self.flags = set([])

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            return cls(f.read())

    def reveal_square(self, x, y):
        self.squares[x][y].hidden = False

        if self.squares[x][y].mine:
            raise HitMineException()

        # Load adjacent. I don't know if there's any reason to do this lazily.
        total = 0
        for dx, dy in list(itertools.product([1, -1, 0], repeat=2)):
            if x+dx < 0 or y+dy < 0 or x+dx >= self.x or y+dy >= self.y:
                continue
            if self.squares[x+dx][y+dy].mine:
                total += 1

        self.squares[x][y].adjacent = total

    def get_square(self, x, y):
        if self.squares[x][y].hidden:
            return None

        return self.squares[x][y]

    def flag_square(self, x, y):
        assert self.squares[x][y].hidden, "Cannot flag revealed square"
        self.flags.add((x, y))

    def pretty_string(self, color=True):
        if color:
            mine_repr = "\33[31mX\33[0m"
            flag_repr = "\33[32mF\33[0m"
        else:
            mine_repr = "X"
            flag_repr = "F"

        representation = []
        for x in range(self.x):
            row_repr = []
            for y in range(self.y):
                square = self.squares[x][y]
                if (x, y) in self.flags:
                    row_repr.append(flag_repr)
                elif square.hidden:
                    row_repr.append(".")
                elif square.mine:
                    row_repr.append(mine_repr)
                else:
                    if square.adjacent == 0:
                        count_repr = " "
                    elif color:
                        count_repr = "\33[94m{}\33[0m".format(str(square.adjacent))
                    else:
                        count_repr = str(square.adjacent)
                    row_repr.append(count_repr)
            representation.append(" ".join(row_repr))
        return "\n".join(representation)

    def __str__(self):
        return self.pretty_string(color=False)


class Solver(object):
    def __init__(self, board):
        self.board = board

    def get_hidden_coords(self):
        # Maybe consider not recreating this every time you access it.
        hidden_coords = set([])
        for x, y in itertools.product(range(self.board.x), range(self.board.y)):
            if self.board.get_square(x, y) is None:
                hidden_coords.add((x, y))
        return hidden_coords - self.board.flags

    def solve(self):
        # TODO: keep track of the solution so we can display it and prove we really
        # did solve the puzzle. Should return all our steps.

        try:
            num_guesses = 0
            while self.get_hidden_coords():
                num_guesses += 1
                self.guess()
                self.deduce()
        except HitMineException:
            hidden = len(self.get_hidden_coords())
            percent = (1 - hidden / float(self.board.x * self.board.y)) * 100
            print "Hit a mine! {}% revealed".format(percent)
        else:
            print "Solved!"

        print "used {} guesses".format(num_guesses)

        print self.board.pretty_string()

    def get_bounded_sets(self):
        # These bounded sets are at the core of our solution. They represent a set
        # of squares that must contain a number of mines between some minimum and
        # maximum value. This function discovers those sets and returns a dict
        # mapping sets of squares to their minimum and maximum values.
        set_metadata = {} # Tuple of (min_mines, max_mines)

        def get_neighbors_info(x, y):
            hidden_neighbors = set([])
            total_flags = 0
            for dx, dy in list(itertools.product([1, -1, 0], repeat=2)):
                if (x+dx, y+dy) in self.board.flags:
                    total_flags += 1
                    continue
                if (x+dx < 0
                    or y+dy < 0
                    or x+dx >= self.board.x
                    or y+dy >= self.board.y):
                    continue
                if self.board.get_square(x+dx, y+dy) is None:
                    hidden_neighbors.add((x+dx, y+dy))
            return frozenset(hidden_neighbors), total_flags

        square_to_sets = defaultdict(list)

        # Generate all sets defined by revealed squares
        for x, y in itertools.product(range(self.board.x), range(self.board.y)):
            square = self.board.get_square(x, y)
            if square is None:
                continue

            set_coords, num_flags = get_neighbors_info(x, y)
            for sq in set_coords:
                square_to_sets[sq].append(set_coords)

            mines_left = square.adjacent - num_flags
            if set_coords in set_metadata:
                assert set_metadata[set_coords] == (mines_left, mines_left)
            else:
                set_metadata[set_coords] = (mines_left, mines_left)

        frontier = set([])
        previous = set_metadata.keys()
        while len(previous) != 0:
            for known_set in previous:
                known_min, known_max = set_metadata[known_set]
                known_max_safe = len(known_set) - known_min

                intersecting_sets = set([])
                for sq in known_set:
                    intersecting_sets.update(set(square_to_sets[sq]))
                intersecting_sets -= known_set

                for intersector in intersecting_sets:
                    # From each pair of overlapping sets, we can create three new
                    # sets with known minimum and maximum mine populations: the
                    # intersection and both differences. By discovering these sets,
                    # the algorithm is able to utilize the subtle restrictions
                    # neighboring sets impose on each other.

                    intersector_min, intersector_max = set_metadata[intersector]
                    intersector_max_safe = len(intersector) - intersector_min
                    min_max_safe = min(known_max_safe, intersector_max_safe)

                    # intersection:
                    intersection = intersector & known_set
                    intersection_min = min(0, len(intersection) - min_max_safe)
                    intersection_max = min(
                        len(intersection), intersector_max, known_max
                    )
                    if intersection in set_metadata:
                        old_min, old_max = set_metadata[intersection]
                        intersection_min = max(old_min, intersection_min)
                        intersection_max = min(old_max, intersection_max)
                    else:
                        frontier.add(intersection)

                    set_metadata[intersection] = (intersection_min, intersection_max)

                    for square in intersection:
                        square_to_sets[square].append(intersection)


                    # difference:
                    # we only need to take the difference in one direction, because
                    # we're iterating over every set. We'll get the other difference
                    # when intersector and known_set are reversed.

                    difference = known_set - intersection
                    difference_min = max(0, known_min - intersection_max)
                    difference_max = min(len(difference),
                                         known_max - intersection_min)

                    if difference in set_metadata:
                        old_min, old_max = set_metadata[difference]
                        difference_min = max(old_min, difference_min)
                        difference_max = min(old_max, difference_max)
                    else:
                        frontier.add(difference)

                    set_metadata[difference] = (difference_min, difference_max)

                    for square in difference:
                        square_to_sets[square].append(difference)


            previous = frontier.copy()
            frontier = set([])

        return set_metadata

    def deduce(self):
        # Reveal as much of the board based on deductive rules as we can
        old_sets = {}
        new_sets = self.get_bounded_sets()

        def sets_equal(old, new):
            if len(old) != len(new):
                return False
            for k, v in old.iteritems():
                if k not in new or new[k] != v:
                    return False
            return True

        while not sets_equal(old_sets, new_sets):
            for squares, (min_mines, max_mines) in new_sets.iteritems():
                if min_mines != max_mines:
                    continue
                if max_mines == 0:
                    for square in squares:
                        self.board.reveal_square(*square)
                elif max_mines == len(squares):
                    for square in squares:
                        self.board.flag_square(*square)

            old_sets = new_sets
            new_sets = self.get_bounded_sets()


    def guess(self):
        # TODO: improve guessing logic.
        # Select a square on the board to reveal when uncertain. The square is not
        # guaranteed to be free of mines, but should be selected to maximize this
        # probability. For now, I'll pick one at random, but the idea is to
        # consider mine probability in the future, as well as some other hueristics
        # (whether it is close or far from revealed squares, if it is near an edge)
        
        guessed = random.choice(tuple(self.get_hidden_coords()))
        self.board.reveal_square(*guessed)


def create_puzzle(x, y, num_mines):
    if (x * y) < num_mines:
        raise ValueError("num_mines is greater than number of available squares")

    coords = [(i, j) for i in range(x) for j in range(y)]
    mines = set(random.sample(coords, num_mines))

    board = []
    for i in range(x):
        row = []
        for j in range(y):
            if (i,j) in mines:
                row.append('X')
            else:
                row.append('.')
        board.append(" ".join(row))
    return "\n".join(board)


def main():
    puzzle = create_puzzle(DEFAULT_X, DEFAULT_Y, DEFAULT_NUM_MINES)
    board = MinesweeperBoard(puzzle)
    solver = Solver(board)
    try:
        solver.solve()
    except HitMineException:
        print board.pretty_string()
        print "Hit a mine!"

if __name__ == "__main__":
    main()
