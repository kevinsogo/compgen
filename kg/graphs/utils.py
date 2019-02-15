from collections import deque

class GraphError(Exception): ...

def node_arg(nodes):
    nodes = list(range(1, nodes+1) if isinstance(nodes, int) else nodes)
    if not nodes: raise GraphError("Node list cannot be empty")
    return nodes

def make_adj(nodes, edges):
    nodes = node_arg(nodes)
    if isinstance(edges, dict):
        if sorted(edges.keys()) != sorted(nodes): raise GraphError("")
        return edges
    adj = {i: [] for i in nodes}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj

def is_tree(nodes, edges):
    nodes = node_arg(nodes)
    edges = list(edges)
    return len(edges) == len(nodes) - 1 and is_connected(nodes, edges)

def is_connected(nodes, edges):
    nodes = node_arg(nodes)
    return len(nodes) == len(bfs(nodes, edges))

def is_simple(nodes, edges):
    nodes = set(nodes)
    found_edges = set()
    for a, b in edges:
        if a not in nodes: raise ValueError(f"Invalid node: {a}")
        if b not in nodes: raise ValueError(f"Invalid node: {b}")
        if a > b: a, b = b, a
        if a == b or (a, b) in found_edges: return False
        found_edges.add((a, b))
    return True

def bfs(*args, **kwargs):
    return [i for i, p, d in bfs_data(*args, **kwargs)]

def dfs(*args, **kwargs):
    return [i for i, p, d in dfs_data(*args, **kwargs)]

def bfs_data(nodes, edges, *, start=None):
    nodes = node_arg(nodes)
    if start is None: start = nodes[0]
    if start not in nodes: raise GraphError(f"Failed to BFS: {start} not in nodes (n={len(nodes)})")
    adj = make_adj(nodes, edges)
    queue = deque([(start, 0)])
    parent = {start: start}
    while queue:
        i, d = queue.popleft()
        yield i, parent[i], d
        for j in adj[i]:
            if j not in parent:
                parent[j] = i
                queue.append((j, d + 1))

def dfs_data(nodes, edges, *, start=None):
    nodes = node_arg(nodes)
    if start is None: start = nodes[0]
    if start not in nodes: raise GraphError(f"Failed to DFS: {start} not in nodes (n={len(nodes)})")
    adj = make_adj(nodes, edges)
    # reverse adjacency for "canonicity"
    for i, adg in adj: adg[:] = adg[::-1]
    stack = [(start, 0)]
    parent = {start: start}
    while stack:
        i, d = stack.pop()
        yield i, parent[i], d
        for j in adj[i]:
            if j not in parent:
                parent[j] = i
                stack.append(j)

def farthest(nodes, edges, *, start):
    return bfs(nodes, edges, start=start)[-1]

def diameter(nodes, edges):
    nodes = node_arg(nodes)
    adj = make_adj(nodes, edges)
    i = farthest(nodes, adj, start=nodes[0])
    b = list(bfs_data(nodes, adj, start=i))
    j, p, d = b[-1]
    return i, j, d
