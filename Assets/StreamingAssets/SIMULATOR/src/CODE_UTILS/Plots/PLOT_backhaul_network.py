# Module 'PLOT_backhaul_network'
# Created 03/05/2021 (version 6.0)
# Modified 03/05/2021 (version 6.0) - Jose Javier Rico Palomo

import matplotlib.pyplot as plt
from SIMULATOR.src.CELLULAR_NETWORK.backhaul.backhaul_network import BackhaulNetwork
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
import networkx as nx
from typing import *


def abstract_backhaul_graph(backhaul_network: BackhaulNetwork, base_stations: Dict[str, BaseStation], label_offset: float = 2.0):

    positions = dict()
    labels_positions = dict()
    labels_macro = dict()
    nodes_macro = []
    labels_small = dict()
    nodes_small = []

    graph = backhaul_network.BN_graph

    for current_node in graph.nodes:
        current_position = base_stations[current_node].BS_position

        positions[current_node] = current_position
        labels_positions[current_node] = (current_position[0], current_position[1]+label_offset)

        if base_stations[current_node].BS_id.startswith("MACRO"):
            nodes_macro.append(current_node)
            labels_macro[current_node] = base_stations[current_node].BS_id

        elif base_stations[current_node].BS_id.startswith("SMALL"):
            nodes_small.append(current_node)
            labels_small[current_node] = base_stations[current_node].BS_id

    plt.figure()

    nx.draw_networkx(graph, pos=positions, style="dashed", with_labels=False, nodelist=nodes_macro, node_size=100, node_shape='^')
    nx.draw_networkx(graph, pos=positions, style="dashed", with_labels=False, nodelist=nodes_small, node_size=50, node_shape='^')

    nx.draw_networkx_labels(graph, labels_positions, labels_small, font_size=10, font_color='b')
    nx.draw_networkx_labels(graph, labels_positions, labels_macro, font_size=10, font_color='b')
