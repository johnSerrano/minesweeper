import itertools
import random
from collections import namedtuple

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
            try:
                if self.squares[x+dx][y+dy].mine:
                    total += 1
            except IndexError:
                pass

        self.squares[x][y].adjacent = total

    def get_square(self, x, y):
        if self.squares[x][y].hidden:
            return None

        return self.squares[x][y]

    def flag_square(self, x, y):
        if not self.squares[x][y].hidden:
            raise RuntimeError("Cannot flag revealed square")

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
                    row.repr.append(flag_repr)
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

        while self.get_hidden_coords():
            self.deduce()
            self.guess()
            print self.board.pretty_string()
            print "=" * self.board.y*2

    def deduce(self):
        # TODO: deductive solving
        # Reveal as much of the board based on deductive rules as we can.
        return

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
