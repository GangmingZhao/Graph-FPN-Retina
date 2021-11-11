import tensorflow as tf
import numpy as np
import dgl
import datetime
import pdb
import os, sys

src_dir = os.path.dirname(os.path.realpath(__file__))
while not src_dir.endswith("src"):
    src_dir = os.path.dirname(src_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from model.Graph import *

def stochastic_create_edges(g, n_edges = 0):
    assert n_edges>g.num_nodes(), "number of edges is smaller than that of nodes"

    with tf.device('/CPU:0'): # It seems that CPU works faster than GPU in edges creations
        max_edges = (g.num_nodes()-1) * g.num_nodes() // 2  # (0 + g.num_nodes()-1) * g.num_nodes() / 2 

        # Ensure that every nodes has least one edge 
        for i in range(1, g.num_nodes()-1):
            j = np.random.randint(i+1, g.num_nodes())
            g.add_edges(tf.constant([i], dtype = "int64"), tf.constant([j], dtype = "int64"))
        
        # Add the reset of edges
        if n_edges:
            while g.num_edges() < n_edges and g.num_edges() < max_edges:
                i = np.random.randint(0, g.num_nodes())
                j = np.random.randint(0, g.num_nodes())
                g.add_edges(tf.constant([i], dtype = "int64"), tf.constant([j], dtype = "int64")) if not (g.has_edges_between(i,j) or g.has_edges_between(j,i) or i == j) else 0
                if g.num_edges() == max_edges:
                    break
    return dgl.add_reverse_edges(g, copy_ndata = True)


def heterograph(name_n_feature, dim_n_feature):
    graph_data = {
        ('n', 'contextual', 'n'): (tf.constant([0, 1]), tf.constant([1, 2])),
        ('n', 'hierarchical', 'n'): (tf.constant([0, 1]), tf.constant([1, 2]))
        }
    g = dgl.heterograph(graph_data)
    g.nodes['n'].data[name_n_feature] = tf.ones([g.num_nodes(), dim_n_feature])
    return dgl.to_bidirected(g, copy_ndata = True)


def hetero_add_edges(g, u, v, edges):
    if isinstance(u,int):
        g.add_edges(tf.constant([u]), tf.constant([v]), etype = edges)
    else:
        g.add_edges(tf.constant(u), tf.constant(v), etype = edges)
    return dgl.to_bidirected(g, copy_ndata = True)


def hetero_add_n_feature(g, name_n_feature, indice_node, val):
    g.nodes['n'].data[name_n_feature][indice_node]= val
    return g


def hetero_subgraph(g, edges):
    return dgl.edge_type_subgraph(g, [edges])


if __name__ == "__main__":
    dim_h = 3
    g = heterograph("x", 256)
    subg = hetero_subgraph(g, "hierarchical")
    # print(subg.edges())
    lay1 = contextual_layers(subg.ndata['x'].shape[1], 256)

    features = subg.ndata['x']
    # print(features)
    h_out = tf.squeeze(lay1(subg, features))

    subg.apply_nodes(lambda nodes: {'x' : h_out})
    print(g.ndata["x"])

    # print(subg.edges())
    # print(g.nodes['n'].data['x'])
    # hetero_add_n_feature(g, "x", 0, tf.constant([1,2,3,4]))
    # print(g.edges(etype = "contextual"))
    # g = hetero_add_edges(g, 0, 2, "contextual")
    # print(g.edges(etype = "contextual"))
    # print(g.ndata["x"][0])
    

    # starttime = datetime.datetime.now()
    # g1 = dgl.graph(([0], [1]), num_nodes = 4096)
    # g1 = stochastic_create_edges(g1,100000)
    # endtime = datetime.datetime.now()
    # print((endtime - starttime).seconds)