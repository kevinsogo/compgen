import itertools

from kg.utils import * ### @import
from .utils import * ### @import 'kg.grids.utils'

class GridGenError(GridError): ...

class Tile:
    def __init__(self, *values, ct=None, minct=0, maxct=float('inf'), weight=1.0, locs=[]):
        if weight < 0: raise ValueError(f"weight must be nonnegative: {weight}")
        if not 0 <= minct <= maxct: raise ValueError(f"Invalid range: [{minct}, {maxct}]")
        if ct is not None:
            if not minct <= ct <= maxct: raise ValueError(f"Invalid ct={ct}: not in range [{minct}, {maxct}]")
            minct = maxct = ct

        self.values = values
        self.minct = minct
        self.maxct = maxct
        self.weight = weight
        self.locs = locs
        super().__init__()

class _CTile:
    def __init__(self, tile):
        self.values = tile.values
        self.minct = tile.minct
        self.maxct = tile.maxct
        self.weight = tile.weight
        self.locs = tile.locs
        self.count = 0
        self.norm()
        super().__init__()

    def norm(self):
        if self.count > self.maxct: raise GridGenError(f"Exceeded {maxct} cells for tile {self.values}")
        if self.count == self.maxct: self.weight = 0

    def get(self, rand):
        self.count += 1
        self.norm()
        return rand.choice(self.values)


def gen_random_grid(rand, r, c, *tiles):
    if not tiles: tiles = [True, False]
    tiles = [_CTile(tile if isinstance(tile, Tile) else Tile(tile)) for tile in tiles]
    if not (r >= 1 and c >= 1): raise ValueError(f"The dimensions must be positive: {r} {c}")
    empty = object()
    grid = [[empty]*c for i in range(r)]

    def set_cell(i, j, v):
        if not 0 <= i < len(grid) and 0 <= j < len(grid[i]): raise GridGenError(f"Invalid cell: {i, j}")
        if grid[i][j] is not empty: raise GridGenError(f"Duplicate cell: {i, j}")
        grid[i][j] = v

    for tile in tiles:
        for i, j in tile.locs:
            set_cell(i, j, tile.get(rand))

    cells = rand.shuff((i, j) for i, j in itertools.product(range(r), range(c)) if grid[i][j] is empty)

    # fill minc
    for tile in tiles:
        while tile.count < tile.minct:
            if not cells: raise GridGenError("No cells remaining!")
            set_cell(*cells.pop(), tile.get(rand))

    for i, j in cells:
        v = rand.random() * sum(tile.weight for tile in tiles)
        for tile in tiles:
            if v >= tile.weight:
                v -= tile.weight
            else:
                set_cell(i, j, tile.get(rand))
                break
        else: raise GridGenError("No tiles remaining!")

    assert all(val is not empty for row in grid for val in row)

    return grid

### @@ if False {

# TODO do gen_connected_grid # multiple components and stuff...

# dirs4 = tuple((i, j) for i, j in itertools.product([-1, 0, 1], repeat=2) if abs(i) + abs(j) == 1)
# dirs8 = tuple((i, j) for i, j in itertools.product([-1, 0, 1], repeat=2) if max(abs(i), abs(j)) == 1)

# class Choicer:
#     def __init__(self, values):
#         self.values = list(values)
#         self.indices = {v: i for i, v in enumerate(self.values)}
#         self.tree = SegTree(0, len(self.values))
#         super().__init__()

#     def set(self, i, v):
#         self.tree.set(self.indices[i], v)

#     def take(self, v):
#         node = self.tree
#         pos = 0
#         while True:
#             assert 0 <= v < node.s
#             if not node.l:
#                 break
#             elif v < node.l.v:
#                 node = node.l
#             else:
#                 pos += node.l.v
#                 v -= node.l.v
#                 node = node.r

#         self.set(pos, 0)
#         return self.values[pos]

#     def __len__(self):
#         return self.tree.s

### @@ }
