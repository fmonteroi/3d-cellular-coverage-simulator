# Module 'fronthaul_topology'
# Created 13/02/2020 (version 3.0)
# Modified 15/05/2021 (version 6.0) - Jose Javier Rico Palomo

import random
from SIMULATOR.src.CODE_UTILS.exceptions import ImpossibleToCreateFronthaulNetwork
import itertools
import networkx as nx


def unique_topology(graph: nx.Graph):
    """
        It generates a fronthaul topology where one router is connected with one macro base station.
        It is necessary that the macro and router nodes have the same length.

        :param graph: fronthaul network graph, only with nodes (base stations and routers), without any edge.

        :return [object (NetworkX.Graph)] graph: modified fronthaul network graph with edges.
    """

    macro_nodes = []
    router_nodes = []

    # Store auxiliary all the nodes who are macro base stations in a list
    [macro_nodes.append(BS) for BS in graph.nodes if BS.startswith("MACRO")]

    # Store auxiliary all the nodes who are routers in a list
    [router_nodes.append(R) for R in graph.nodes if R.startswith("ROUTER")]

    if len(macro_nodes) != len(router_nodes):
        raise ImpossibleToCreateFronthaulNetwork("Macro and router nodes have not the same length (unique topology)")

    else:

        # Create edge between macro base stations and router only,
        for i in range(0, len(macro_nodes)):
            graph.add_edge(macro_nodes[i], router_nodes[i])

    return graph


def complete_mesh_topology(graph: nx.Graph):
    """
        It generates a graph for a fronthaul topology where all que base stations are connected with all routers.

        :param graph: backhaul network graph, only with nodes (base stations), without any edge.

        :return [object (NetworkX.Graph)] graph: modified backhaul network graph with edges.
    """

    macro_nodes = []
    router_nodes = []

    # Store auxiliary all the nodes who are macro base stations in a list
    [macro_nodes.append(BS) for BS in graph.nodes if BS.startswith("MACRO")]

    # Store auxiliary all the nodes who are routers in a list
    [router_nodes.append(R) for R in graph.nodes if R.startswith("ROUTER")]

    for i in range(0, len(router_nodes)):
        for j in range(0, len(macro_nodes)):
            graph.add_edge(router_nodes[i], macro_nodes[j])

    return graph


def random_topology(graph: nx.Graph):
    """
        It generates a graph for a fronthaul topology where the link between base stations and routers are randomly distributed.

        :param graph: fronthaul network graph, only with nodes (base stations and routers), without any edge.

        :return [object (NetworkX.Graph)] graph: modified fronthaul network graph with edges.
    """

    macro_nodes = []
    router_nodes = []

    # Store auxiliary all the nodes who are macro base stations in a list
    [macro_nodes.append(BS) for BS in graph.nodes if BS.startswith("MACRO")]

    # Store auxiliary all the nodes who are routers in a list
    [router_nodes.append(R) for R in graph.nodes if R.startswith("ROUTER")]

    # Add random edges between router and macro nodes
    [graph.add_edge(random.choice(router_nodes), macro_nodes[i]) for i in range(0, len(macro_nodes))]

    return graph
