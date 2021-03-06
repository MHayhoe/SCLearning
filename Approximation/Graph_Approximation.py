import numpy as np
import networkx as nx
import scipy as sp
from collections import Counter


# Given a graph G (as an adjacency matrix A) and threshold eps, returns a spectral sparsifier H such that
# (1-eps)L_G <= L_H <= (1+eps)L_G, in the sense of PSD ordering.
def spectral_sparsifier(A, eps, zero_threshold=0):
    # Find the incidence matrix B, edge weight matrix W, Laplacian L and its pseudoinverse Lp.
    H = nx.from_numpy_matrix(A)
    B = nx.linalg.incidence_matrix(H, oriented=True).T
    W = sp.sparse.diags([e[-1] for e in H.edges.data("weight", default=1)])
    L = B.T @ W @ B
    Lp = np.linalg.pinv(L.todense())

    # Compute effective resistance of the edges
    R_e = np.diag(B @ Lp @ B.T)

    # Parameters for selection of edges
    c = 1
    n = len(H.nodes)
    m = W.shape[0]
    q = np.ceil(9 * c ** 2 * n * np.log(n) / eps ** 2).astype('int')
    print('Sampled {:.1f} times the number of edges'.format(q/m))

    # Selection probabilities, proportional to edge weights and effective resistances
    probs = W @ R_e / np.sum(W @ R_e)

    # Sample to obtain new edge weights, which are zero if an edge was never selected.
    rng = np.random.default_rng(0)
    edge_indices = rng.choice(m, size=q, replace=True, p=probs, axis=1)
    W_vals = [e[-1] for e in H.edges.data("weight", default=1)] / (probs*q)
    edge_counts = Counter(edge_indices)
    edge_ids = [(a,b) for a,b in G.edges()]

    W_H = {edge_ids[ei]: W_vals[ei] * edge_counts[ei] for ei in range(m)}

    # Set edge weights accordingly and return the resulting adjacency matrix, removing edges with weights that are
    # close to zero
    nx.set_edge_attributes(H, W_H, "weight")
    zero_edge_ids = [(a, b) for a, b, attrs in H.edges(data=True) if attrs["weight"] <= zero_threshold]
    H.remove_edges_from(zero_edge_ids)
    print('Removed {} edges which were not sampled'.format(len(zero_edge_ids)))

    return H
