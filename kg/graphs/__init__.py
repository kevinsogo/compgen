def is_tree(nodes, edges):
    nodes = list(nodes)
    edges = list(edges)
    return len(edges) == len(nodes) - 1 and is_connected(nodes, edges)

def is_connected(nodes, edges):
    nodes = list(nodes)
    adj = {i: [] for i in nodes}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    stack = [nodes[0]]
    vis = set(stack)
    while stack:
        i = stack.pop()
        for j in adj[i]:
            if j not in vis:
                vis.add(j)
                stack.append(j)
    return len(vis) == len(nodes)

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
