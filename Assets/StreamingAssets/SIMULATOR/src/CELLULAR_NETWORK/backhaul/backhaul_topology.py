# Module 'backhaul_topology'
# Created 27/03/2020 (version 4.0)
# Modified 03/05/2021 (version 6.0) - Jose Javier Rico Palomo

import itertools
import random
import networkx as nx


def complete_mesh_topology(graph: nx.Graph):
    """
        It generates a graph for a backhaul topology where all que base stations are connected with each others.

        :param graph: backhaul network graph, only with nodes (base stations), without any edge.

        :return [object (NetworkX.Graph)] graph: modified backhaul network graph with edges.
    """

    edges = itertools.combinations(graph.nodes, 2)
    graph.add_edges_from(edges)

    return graph


def random_topology(graph: nx.Graph):
    """
        It generates a graph for a backhaul topology where the link between base stations are randomly distributed.

        :param graph: backhaul network graph, only with nodes (base stations), without any edge.

        :return [object (NetworkX.Graph)] graph: modified backhaul network graph with edges.
    """

    for i in graph.nodes:

        flag = False
        peer = 0
        while not flag:
            peer = random.choice(list(graph.nodes))
            flag = True if peer != i else False

        graph.add_edge(i, peer)

    return graph


def macro_linear_topology(graph: nx.Graph):
    """
        It generates the links between macro base stations, generating a partial path graph.

        :param graph: backhaul network graph, only with nodes (base stations), without any edge.

        :return [object (NetworkX.Graph)] graph: modified backhaul network graph with edges (only in macro base stations).
    """

    macro_nodes = []

    # Store auxiliary all the nodes who are macro base stations in a list
    [macro_nodes.append(BS) for BS in graph.nodes if BS.startswith("MACRO")]

    # Create edge between macro base stations only, creating a path graph
    for i in range(1, len(macro_nodes)):
        graph.add_edge(macro_nodes[i - 1], macro_nodes[i])

    return graph

# TODO: structured topology
