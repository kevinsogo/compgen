from collections import deque

from kg.utils import * ### @import

class GraphError(Exception): ...
class ToposortError(GraphError): ...

class _NodeList(list): ...
class _Adj(dict): ...

def make_nodes(nodes):
    if isinstance(nodes, _NodeList): return nodes
    nodes = _NodeList(range(1, nodes+1) if isinstance(nodes, int) else nodes)
    if not nodes: raise GraphError("Node list cannot be empty")
    return nodes

def make_adj(nodes, edges, *, directed=False):
    if isinstance(edges, _Adj): return edges
    nodes = make_nodes(nodes)
    if isinstance(edges, dict):
        if sorted(edges.keys()) != sorted(nodes): raise GraphError("Invalid adjaacency list")
        return edges
    adj = _Adj((i, []) for i in nodes)
    for a, b, *rest in edges:
        adj[a].append(b)
        if not directed: adj[b].append(a)
    return adj

def is_tree(nodes, edges):
    nodes = make_nodes(nodes)
    edges = list(edges)
    return len(edges) == len(nodes) - 1 and is_connected(nodes, edges)

def is_connected(nodes, edges):
    nodes = make_nodes(nodes)
    return len(nodes) == len(bfs(nodes, edges, directed=False))

def is_simple(nodes, edges, *, directed=False):
    nodes = make_nodes(nodes)
    found_edges = set()
    for a, b, *rest in edges:
        if a not in nodes: raise ValueError(f"Invalid node: {a}")
        if b not in nodes: raise ValueError(f"Invalid node: {b}")
        if not directed and a > b: a, b = b, a
        if a == b or (a, b) in found_edges: return False
        found_edges.add((a, b))
    return True

def bfs(*args, **kwargs):
    return [data.node for data in bfs_data(*args, **kwargs)]

def dfs(*args, **kwargs):
    return [data.node for data in dfs_data(*args, **kwargs)]

class GraphTraversalData:
    def __init__(self, node, parent, depth, **extras):
        self.node = node
        self.parent = parent
        self.depth = depth
        self.extras = extras
        super().__init__()

    def __iter__(self):
        yield self.node
        yield self.parent
        yield self.depth

def bfs_data(nodes, edges, *, start=None, start_all=False, directed=False):
    nodes = make_nodes(nodes)
    if start_all and start is not None:
        raise GraphError(
                f"You can't pass start={start} if "
                f"start_all={start_all} is true (n={len(nodes)})")
    starts = nodes if start_all else [start] if start is not None else [nodes[0]]
    adj = make_adj(nodes, edges, directed=directed)
    if any(start not in adj for start in starts):
        raise GraphError(f"Failed to BFS: {start} not in nodes (n={len(nodes)})")
    parent = {}
    for start in starts:
        if start in parent: continue
        queue = deque([(start, 0)])
        parent[start] = start
        while queue:
            i, d = queue.popleft()
            yield GraphTraversalData(i, parent[i], d, source=start)
            for j in adj[i]:
                if j not in parent:
                    parent[j] = i
                    queue.append((j, d + 1))

def dfs_data(nodes, edges, *, start=None, start_all=False, directed=False):
    nodes = make_nodes(nodes)
    if start_all and start is not None:
        raise GraphError(
                f"You can't pass start={start} if "
                f"start_all={start_all} is true (n={len(nodes)})")
    starts = nodes if start_all else [start] if start is not None else [nodes[0]]
    adj = make_adj(nodes, edges, directed=directed)
    if any(start not in adj for start in starts):
        raise GraphError(f"Failed to DFS: {start} not in nodes (n={len(nodes)})")
    parent = {}
    for start in starts:
        if start in parent: continue
        stack = [(start, 0)]
        parent[start] = start
        while stack:
            i, d = stack.pop()
            yield GraphTraversalData(i, parent[i], d, source=start)
            for j in reversed(adj[i]): # reverse adjacency for "canonicity"
                if j not in parent:
                    parent[j] = i
                    stack.append((j, d + 1))

def farthest(nodes, edges, *, start):
    return bfs(nodes, edges, start=start)[-1]

def diameter(nodes, edges):
    nodes = make_nodes(nodes)
    adj = make_adj(nodes, edges)
    i = farthest(nodes, adj, start=nodes[0])
    for b in bfs_data(nodes, adj, start=i):
        ...
    return i, b.node, b.depth

@listify
def bipartition(nodes, edges):
    nodes = make_nodes(nodes)
    adj = make_adj(nodes, edges)
    vis = set()
    for s in nodes:
        if s in vis: continue
        gr = ([], [])
        for data in bfs_data(nodes, edges, start=s):
            vis.add(data.node)
            gr[data.depth % 2].append(data.node)
        yield gr

def graph_relabel(nodes, edges, new_nodes):
    nodes = make_nodes(nodes)
    new_nodes = make_nodes(new_nodes)
    if sorted(nodes) != sorted(new_nodes): raise GraphError("Invalid node permutation")
    bago = dict(zip(nodes, new_nodes))
    return [(bago[i], bago[j], *rest) for i, j, *rest in edges]

@listify
def connected_components(nodes, edges):
    nodes = make_nodes(nodes)
    adj = make_adj(nodes, edges)
    vis = set()
    for i in nodes:
        if i not in vis:
            js = bfs(nodes, adj, start=i)
            vis |= set(js)
            yield js

@listify
def topologically_sort(nodes, edges):
    nodes = make_nodes(nodes)
    adj = make_adj(nodes, edges, directed=True)

    deg = {node: 0 for node in nodes}
    for i in nodes:
        for j in adj[i]: deg[j] += 1
    goods = deque(i for i in nodes if deg[i] == 0)
    while goods:
        i = goods.popleft()
        yield i
        for j in adj[i]:
            deg[j] -= 1
            if deg[j] == 0: goods.append(j)

    if any(deg.values()):
        raise ToposortError(f"Failed to toposort: the graph is not acyclic (n={len(nodes)})")

def is_acyclic(nodes, edges, *, directed=False):
    if directed:
        try:
            topologically_sort(nodes, edges)
            return True
        except ToposortError:
            return False
    else:
        raise GraphError("is_acyclic not yet supported for undirected graphs. "
                "I know, I know, it's not hard to code, but I'm lazy. I'll code it "
                "when I need it :D If you need it now, either tell me, or just write "
                "it yourself and make a pull/merge request. Thanks!!")
