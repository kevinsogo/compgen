from .utils import * ### @import 'kg.grids.utils'

from kg.utils import * ### @import
from kg.graphs.utils import * ### @import

class GridError(Exception): ...

dirs4 = tuple((i, j) for i, j in product([-1, 0, 1], repeat=2) if abs(i) + abs(j) == 1)
dirs8 = tuple((i, j) for i, j in product([-1, 0, 1], repeat=2) if max(abs(i), abs(j)) == 1)

def dimensions(grid):
    if not grid: raise GridError("Grid cannot be empty")
    if not isinstance(grid, list): raise GridError("Grid must be a list")
    for row in grid:
        if not row: raise GridError("Row cannot be empty")
        if not isinstance(row, list): raise GridError("Grid must be a list of lists")
    if len(set(map(len, grid))) > 1: raise GridError("Row lengths must be the same")
    return len(grid), len(grid[0])

def make_graph(grid, *tiles, dirs=dirs4):
    if not tiles: tiles = set(*grid)
    r, c = dimensions(grid)
    nodes = {(i, j) for i, j in product(range(r), range(c)) if grid[i][j] in tiles}
    edges = []
    for i, j in nodes:
        for di, dj in dirs:
            ni, nj = i + di, j + dj
            if (ni, nj) in nodes:
                edges.append(((i, j), (ni, nj)))
    return nodes, edges
