from .utils import * ### @import 'kg.graphs.utils'

### @@ rem {
# TODO
# function that returns details about the graph
### @@ }
def tree_details(nodes, edges, *, root=None):
    nodes = make_nodes(nodes)
    if root is None: root = nodes[0]
    if root not in nodes: raise GraphError(f"Root not in nodes")
    adj = make_adj(nodes, edges)
    if not is_tree(nodes, edges): raise GraphError("The graph is not a tree")
    max_depth = -float('inf')
    max_deg = max(map(len, adj.values()))
    diami, diamj, diam = diameter(nodes, adj)
    for data in bfs_data(nodes, adj):
        max_depth = max(data.depth, max_depth)
    return {
        'root': root,
        'diameter': diam,
        'height': max_depth,
        'max_deg': max_deg,
    }
