# Module 'PLOT_simulation_map'
# Created 04/05/2021 (version 6.0)
# Modified 04/05/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
import matplotlib.pyplot as plt
from typing import *
import numpy as np


def complete_scenario(simulation_map: SimulationMap, show_channel_points: bool = False, bs_labels: bool = False, base_stations_dict: Dict[str, BaseStation] = None, color_intensity: float = 0.1):

    fig = plt.figure()

    # Select the limits of the figure
    plt.xlim(0, simulation_map.MAP_size)
    plt.ylim(0, simulation_map.MAP_size)

    # Channels point and tessellations
    channel_points = []
    for current_channel in simulation_map.MAP_channel_tessellation.keys():
        current_point = simulation_map.MAP_channel_tessellation[current_channel]["point"]
        channel_points.append([current_point, current_channel])

    polygons = simulation_map.get_channel_voronoi_2d()
    regions, edges = polygons[0], polygons[1]
    edges = np.array(edges)

    for region in regions:  # Colouring channels
        polygon = edges[region]
        plt.fill(*zip(*polygon), alpha=color_intensity)

    if show_channel_points:
        for i in range(0, len(channel_points)):
            plt.plot(channel_points[i][0][0], channel_points[i][0][1], 'ko')
            plt.text(channel_points[i][0][0], channel_points[i][0][1] + 1, channel_points[i][1], horizontalalignment='right')

    # Device points
    macro_points = simulation_map.MAP_device_tessellation["macro"]["points"]
    for i in range(0, len(macro_points)):
        plt.plot(macro_points[i][0], macro_points[i][1], 'bx')

        if bs_labels is True:
            current_label = find_bs_label(macro_points[i], base_stations_dict)
            plt.text(macro_points[i][0], macro_points[i][1] + 1.5, current_label, color="b", horizontalalignment='right')

    if len(simulation_map.MAP_device_tessellation) == 2:

        small_points = simulation_map.MAP_device_tessellation["small"]["points"]
        for i in range(0, len(small_points)):
            plt.plot(small_points[i][0], small_points[i][1], 'b^')

            if bs_labels is True:
                current_label = find_bs_label(small_points[i], base_stations_dict)
                plt.text(small_points[i][0], small_points[i][1] + 1.5, current_label, color="b", horizontalalignment='right')

    axes = plt.gca()

    return fig, axes


def find_bs_label(position: Tuple[float, float], base_stations_dict):

    bs_label = "None"

    for BS in base_stations_dict.values():

        if BS.BS_position == position:
            bs_label = BS.BS_id

    return bs_label
