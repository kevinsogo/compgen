from itertools import chain
from functools import wraps

from kg.utils import * ### @import
from .utils import * ### @import 'kg.graphs.utils'

class TreeGenError(GraphError): ...

def tree_pgen(pgen):
    @wraps(pgen)
    def make_tree(rand, nodes, *args, shuff=True, randswap=True, relabel=True, weeds=0.0, **kwargs):
        nodes = node_arg(nodes)
        if relabel: rand.shuffle(nodes)
        cweeds = int(len(nodes) * weeds)
        mains = len(nodes) - cweeds
        if not (cweeds >= 0 and mains >= 1): raise TreeGenError(f"Invalid weeds: n={n} weeds={weeds}")
        edges = []
        for i, j in chain(pgen(rand, mains, *args, **kwargs), pgen_random_tree(rand, len(nodes), start=mains)):
            if not (0 <= j < i < len(nodes)): raise TreeGenError(f"Invalid edge {i} {j} (n={len(nodes)})")
            if randswap and rand.randrange(2): i, j = j, i
            edges.append((nodes[i], nodes[j]))
        if shuff: rand.shuffle(edges)
        return edges
    return make_tree

def pgen_random_tree(rand, n, *, start=1):
    for i in range(start, n): yield i, rand.randrange(i)

def pgen_broomy_tree(rand, n, *, branches=1, leaves=0.5, randleaves=False):
    cleaves = int(n * leaves)
    trunk = n - cleaves
    if not (trunk >= branches >= 1 and cleaves >= 0): raise TreeGenError(
            f"Invalid/unusable broomy args: {n} {branches} {leaves} Got cleaves={cleaves} trunk={trunk}")
    for i in range(1, n):
        if i < trunk:
            yield i, max(0, i - branches)
        else:
            j = trunk - branches + (i - trunk) % branches
            assert i % branches == j % branches
            if randleaves: j = rand.randrange(j, i, branches)
            yield i, j

gen_random_tree = tree_pgen(pgen_random_tree)
gen_broomy_tree = tree_pgen(pgen_broomy_tree)

@tree_pgen
def gen_star_tree(rand, n):
    for i in range(1, n): yield i, 0

@tree_pgen
def gen_line_tree(rand, n, *, cactus=0):
    for i in range(1, n):
        yield i, i - 1 - (i - 1) % (cactus + 1)