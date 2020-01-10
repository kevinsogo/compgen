from itertools import chain
from functools import wraps

from kg.utils import * ### @import
from .utils import * ### @import 'kg.graphs.utils'

class TreeGenError(GraphError): ...

def tree_pgen(pgen):
    @wraps(pgen)
    def make_tree(rand, nodes, *args, shuff=True, randswap=True, relabel=True, weeds=0.0, **kwargs):
        nodes = make_nodes(nodes)
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
    if not (trunk >= branches >= 1 and cleaves >= 0):
        raise TreeGenError(f"Invalid/unusable broomy args: {n} {branches} {leaves} Got cleaves={cleaves} trunk={trunk}")
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

def shuff_labels(rand, nodes, edges): # TODO merge with 'graph_relabel'...
    nodes = make_nodes(nodes)
    assert len(set(nodes)) == len(nodes)
    newlabel = dict(zip(nodes, rand.shuff(nodes)))
    return [(newlabel[x], newlabel[y], *r) for x, y, *r in edges]

def rand_swaps(rand, nodes, edges):
    nodes = make_nodes(nodes)
    def rand_swap(x, y, *r):
        if rand.randrange(2): x, y = y, x
        return (x, y, *r)
    return [rand_swap(*e) for e in edges]

def rand_traverse(*args, **kwargs):
    return [i for i, p, d in rand_traverse_data(*args, **kwargs)]

# TODO add start_all, etc.
def rand_traverse_data(rand, nodes, edges, *, start=None):
    nodes = make_nodes(nodes)
    if start is None: start = nodes[0]
    if start not in nodes: raise GraphError(f"Failed to traverse: {start} not in nodes (n={len(nodes)})")
    adj = make_adj(nodes, edges)
    coll = [(start, 0)]
    parent = {start: start}
    while coll:
        idx = rand.randrange(len(coll))
        coll[idx], coll[-1] = coll[-1], coll[idx]
        i, d = coll.pop()
        yield GraphTraversalData(i, parent[i], d, source=start)
        for j in adj[i]:
            if j not in parent:
                parent[j] = i
                coll.append((j, d + 1))
