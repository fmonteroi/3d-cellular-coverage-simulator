# Module 'PLOT_access_network'
# Created 06/05/2021 (version 6.0)
# Modified 06/05/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.ACCESS_NETWORK.access_network import AccessNetwork
import matplotlib.pyplot as plt
import networkx as nx
import math as m


def abstract_access_graph(access_network: AccessNetwork, label_offset: float = 1.0):

    labels = dict()
    labels_positions = dict()
    positions = dict()

    graph = access_network.AN_graph

    num_nodes = len(graph.nodes)
    angle_division = 360 / num_nodes
    relative_angle_per_node = 0

    for current_node in graph.nodes:

        labels[current_node] = graph.nodes[current_node]["name_node"]

        current_position = (m.cos(m.radians(relative_angle_per_node)), m.sin(m.radians(relative_angle_per_node)))
        positions[current_node] = current_position
        labels_positions[current_node] = (current_position[0], current_position[1]+(label_offset/10))

        relative_angle_per_node += angle_division

    plt.figure()
    nx.draw_networkx(graph, pos=positions, style="dashed", with_labels=False, node_size=200, node_shape='o')
    nx.draw_networkx_labels(graph, labels_positions, labels, font_size=10, font_color='b')
