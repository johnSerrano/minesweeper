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

        self.squares = []
        for line in lines:
            self.squares.append([Square(mine=square=='X') for square in line])

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            return cls(f.read())

    def reveal_square(self, x, y):
        self.squares[x][y].hidden = False
        return (self.squares[x][y].mine, self.num_adjacent(x, y))

    def num_adjacent(self, x, y):
        # this count will include itself, which doesn't matter, because if you're
        # checking a mined square, you lose
        if self.squares[x][y].adjacent != -1:
            # I don't really know how much time we save by being lazy here.
            return self.squares[x][y].adjacent

        total = 0
        for dx, dy in list(itertools.product([1, -1, 0], repeat=2)):
            try:
                if self.squares[x+dx][y+dy].mine:
                    total += 1
            except IndexError:
                # laziness level over 9000.
                pass

        self.squares[x][y].adjacent = total
        return total

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
    for x in range(DEFAULT_X):
        for y in range(DEFAULT_Y):
            board.reveal_square(x, y)
    print board.pretty_string(color=True)

if __name__ == "__main__":
    main()
