# Adaptation on Kruskal's algorithm as defined at https://en.wikipedia.org/wiki/Kruskal%27s_algorithm.
# Returns: a list of the edges chosen to be in the Minimal Spanning Tree.
def kruskal(vertices, edges):
    # create a forest F, where each vertex in the graph is a separate tree
    F = [] 
    for v in vertices:
        F.append([v])
    
    # create a set S containing all the edges in the graph
    S = edges.copy()
    spanning_edges = []
    
    while len(S) != 0 and len(F) != 1: # If a forest only has one element, it is a spanning tree.
        edge = S[0]
        u = edge[0]
        v = edge[1]
        for first in range(len(F)):
            if u in F[first] and not v in F[first]:
                spanning_edges.append(edge)
                for second in range(len(F)):
                    if v in F[second]:
                        F[first] = F[first] + F[second]
                        F.pop(second)
                        break
                break
        S = S[1:]
        	
    return spanning_edges 