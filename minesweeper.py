import itertools
import random
from collections import namedtuple

DEFAULT_X = 15
DEFAULT_Y = 15
DEFAULT_NUM_MINES = 40


class Square(object):
    def __init__(self, hidden=True, mine=False, adjacent=-1):
        self.hidden = hidden
        self.mine = mine
        self.adjacent = adjacent


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

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            return cls(f.read())

    def reveal_square(self, x, y):
        self.squares[x][y].hidden = False

        # Load adjacent. I don't know if there's any reason to do this lazily.
        total = 0
        for dx, dy in list(itertools.product([1, -1, 0], repeat=2)):
            try:
                if self.squares[x+dx][y+dy].mine:
                    total += 1
            except IndexError:
                # laziness level over 9000.
                pass

        self.squares[x][y].adjacent = total

    def get_square(self, x, y):
        if self.squares[x][y].hidden:
            return None
        return self.squares[x][y]

    def pretty_string(self, color=False):
        if color:
            mine_repr = "\33[31mX\33[0m"
        else:
            mine_repr = "X"

        representation = []
        for row in self.squares:
            row_repr = []
            for square in row:
                if square.hidden:
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
        return self.pretty_string()


class Solver(object):
    def __init__(self, board):
        self.board = board
        self.mines = set([]) # set of tuple coords

    def get_hidden_coords(self):
        # Really we should keep track of these when we reveal squares, instead of
        # recreating the set every time we need it. That might be a non-negligible
        # performance improvement.
        hidden_coords = set([])
        for x, y in itertools.product(range(self.board.x), range(self.board.y)):
            if self.board.get_square(x, y) is None:
                hidden_coords.add((x, y))
        return hidden_coords

    def solve(self):
        # TODO: keep track of the solution so we can display it and prove we really
        # did solve the puzzle.

        # Exit when a mine is revealed or only mines remain to be revealed
        # TODO: add things to self.mines
        while self.mines < self.get_hidden_coords():
            # TODO: need some better exit conditions
            self.deduce()
            self.guess()
            print self.board.pretty_string(color=True)
            print "=" * self.board.y

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
        if self.board.get_square(*guessed).mine:
            self.mines.add(guessed)
        return guessed


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
    solver.solve()

if __name__ == "__main__":
    main()
