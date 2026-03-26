# Module 'predefined_scenarios'
# Created 03/06/2020 (version 5.0)
# Modified 03/05/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *

from shapely.geometry import Polygon, LineString

from SIMULATOR.src.GEOMETRY import tessellations
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel


def structured_diagram(channel_points: List[Tuple[float, float]], channels: List[Channel], voronoi_2d: list):
    """
        Its generates the structure where store the channel tessellation.

        :param channel_points: X and Y positions of the central points of the generated propagation channels -> [(x,y), (x,y), ...].
        :param channels: propagation channels generated according to the scenarios distributed over the map.
        :param voronoi_2d: structure returned by the generation of the voronoi diagram of the channels.

        :return [dict] channel_tessellation: structure of the generated channel and the tessellations.
    """

    channel_tessellations = dict()
    polygons = []

    # Create polygons
    regions, vertices = voronoi_2d[0], voronoi_2d[1]
    for i in range(0, len(regions)):  # Iterate regions
        current_region = regions[i]

        vertices_coords = []
        for j in range(0, len(current_region)):  # Iterate index (of vertices) inside regions
            current_index = current_region[j]
            current_vertex = vertices[current_index]

            vertices_coords.append(current_vertex)

        polygons.append(Polygon(vertices_coords))

    # Calculate edges
    for i in range(0, len(polygons)):

        vertices = list(polygons[i].exterior.coords)

        edges = []
        for j in range(0, len(vertices) - 1):
            current_edge = LineString([vertices[j], vertices[j + 1]])
            edges.append(current_edge)

        current_polygon = [vertices, edges]

        # Store the channel in a selected structure
        current_channel_tessellation = dict()
        current_channel_tessellation["point"] = channel_points[i]
        current_channel_tessellation["channel"] = channels[i]
        current_channel_tessellation["polygon"] = current_polygon
        channel_tessellations[channels[i].CHANNEL_id] = current_channel_tessellation

    return channel_tessellations


# ------------------------------------------------------------ #


def configuration_test_adp5g_scenario():
    """
        "Autonomous Drive Pilot 5G" scenario test.
        Default test configuration for the simulation of an autonomous vehicle moving around the campus of Caceres.
        Simulation carried out for the "5G Pilot" project in collaboration with Gamma Solutions and Robolab research group.
        The scenario has been generated based on the antenna locations provided by the company Gamma Solutions.
        Latitude and longitude of the actual scenario: (39°28'34.5"N, 6°20'47.9"W) -> (39°28'59.6"N, 6°20'15.2"W).

        :return [dict] simulation_adp5g_parameters: simulation scenario parameters generated for the ADPG5G test.
    """

    map_size = 780  # m

    # Channel configuration
    channel_points = [(232, 633), (249, 327), (197, 77), (528, 162), (707, 154), (664, 419), (721, 682), (467, 669)]
    channel_config = ["Umi LOS", "Umi LOS", "UMa LOS", "UMa LOS", "Umi LOS", "Umi LOS", "UMa LOS", "UMa LOS"]

    channel_parameters = dict()
    channel_parameters["number_of_points"] = len(channel_points)
    channel_parameters["losses_model"] = "ABG"

    # Device configuration
    bs_level = "small"  # Only small level
    bs_points = [(298, 352), (430, 325), (325, 245), (237, 426), (627, 385)]

    device_parameters = dict()
    device_parameters["small"]["tessellation"] = "voronoi"
    device_parameters["small"]["number_of_antennas"] = len(bs_points)

    # Device tessellation
    polygons = tessellations.generate_tessellations(device_parameters["small"]["tessellation"], points=bs_points)

    device_tessellation = dict()
    device_tessellation[bs_level]["points"] = bs_points
    device_tessellation[bs_level]["polygons"] = polygons

    # Channel tessellation
    voronoi_diagram, channel_voronoi_2d = tessellations.generate_tessellations("finite_voronoi", points=channel_points, size=map_size)

    # Distribute channels
    channels = []
    for i in range(0, channel_parameters["number_of_points"]):
        c = Channel("CHANNEL_" + str(i + 1), channel_config[i].split(" ")[0], channel_config[i].split(" ")[1], channel_parameters["losses_model"])
        channels.append(c)

    channel_tessellation = structured_diagram(channel_points, channels, channel_voronoi_2d)

    configuration_adp5g_parameters = dict()
    configuration_adp5g_parameters["map_size"] = map_size
    configuration_adp5g_parameters["device_tessellation"] = device_tessellation
    configuration_adp5g_parameters["channel_tessellation"] = channel_tessellation
    configuration_adp5g_parameters["device_parameters"] = device_parameters
    configuration_adp5g_parameters["channel_parameters"] = channel_parameters
    configuration_adp5g_parameters["channel_voronoi_2d"] = channel_voronoi_2d

    return configuration_adp5g_parameters


def configuration_test():
    """
        Generated generic scenario for testing simulations.
        Default test configuration for the simulation of an entire environment.

        :return [dict] simulation_map_parameters: simulation scenario parameters generated for the testing simulations.
    """

    map_size = 1000  # m

    # Channel configuration
    channel_points = [(232, 633), (249, 327), (197, 77), (528, 162), (707, 154), (664, 419)]
    channel_config = ["Umi LOS", "Umi NLOS", "UMa LOS", "UMa NLOS", 'Indoor LOS', 'Indoor NLOS']

    channel_parameters = dict()
    channel_parameters["number_of_points"] = len(channel_points)
    channel_parameters["losses_model"] = "ABG"  # "CI" / "FSPL"

    # Device configuration and tessellation
    device_parameters = dict({"macro": dict(), "small": dict()})
    device_tessellation = dict({"macro": dict(), "small": dict()})

    bs_points_macro = [(25, 37), (580, 595), (199, 875), (900, 100)]
    device_parameters["macro"]["tessellation"] = "voronoi"
    device_parameters["macro"]["number_of_antennas"] = len(bs_points_macro)
    polygons_macro = tessellations.generate_tessellations(device_parameters["macro"]["tessellation"], points=bs_points_macro)
    device_tessellation["macro"]["points"] = bs_points_macro
    device_tessellation["macro"]["polygons"] = polygons_macro

    bs_points_small = [(298, 352), (430, 325), (325, 245), (237, 426), (627, 385)]
    device_parameters["small"]["tessellation"] = "voronoi"
    device_parameters["small"]["number_of_antennas"] = len(bs_points_small)
    polygons_small = tessellations.generate_tessellations(device_parameters["small"]["tessellation"], points=bs_points_small)
    device_tessellation["small"]["points"] = bs_points_small
    device_tessellation["small"]["polygons"] = polygons_small

    # Channel tessellation
    voronoi_diagram, channel_voronoi_2d = tessellations.generate_tessellations("finite_voronoi", points=channel_points, size=map_size)

    # Distribute channels
    channels = []
    for i in range(0, channel_parameters["number_of_points"]):
        c = Channel("CHANNEL_" + str(i + 1), channel_config[i].split(" ")[0], channel_config[i].split(" ")[1], channel_parameters["losses_model"])
        channels.append(c)

    channel_tessellation = structured_diagram(channel_points, channels, channel_voronoi_2d)

    configuration_map_parameters = dict()
    configuration_map_parameters["map_size"] = map_size
    configuration_map_parameters["device_tessellation"] = device_tessellation
    configuration_map_parameters["channel_tessellation"] = channel_tessellation
    configuration_map_parameters["device_parameters"] = device_parameters
    configuration_map_parameters["channel_parameters"] = channel_parameters
    configuration_map_parameters["channel_voronoi_2d"] = channel_voronoi_2d

    return configuration_map_parameters


def configuration_jitel_2021():
    """
        Generated scenario for jitel 2021 conference paper simulations.
        4 macro base stations, 20 small base stations and UMa scenario in whole simulation map.

        :return [dict] simulation_map_parameters: simulation scenario parameters generated for the testing simulations.
    """

    map_size = 12000  # ? Size of the map -> 12 Km x 12 Km = 144 Km2

    # Channel configuration
    channel_points = [(1, 1), (232, 633), (249, 327), (197, 77)]  # Does not matter because is always the same propagation scenario (UMa)
    channel_config = ["UMa LOS", "UMa LOS", "UMa LOS", "UMa LOS"]

    channel_parameters = dict()
    channel_parameters["number_of_points"] = len(channel_points)
    channel_parameters["losses_model"] = "ABG"

    # Device configuration and tessellation
    device_parameters = dict({"macro": dict(), "small": dict()})
    device_tessellation = dict({"macro": dict(), "small": dict()})

    bs_points_macro = [(2900, 9000), (3100, 3000), (8250, 2500), (10075, 7500)]
    device_parameters["macro"]["tessellation"] = "voronoi"
    device_parameters["macro"]["number_of_antennas"] = len(bs_points_macro)
    polygons_macro = tessellations.generate_tessellations(device_parameters["macro"]["tessellation"], points=bs_points_macro)
    device_tessellation["macro"]["points"] = bs_points_macro
    device_tessellation["macro"]["polygons"] = polygons_macro

    bs_points_small = [(1450, 1000), (2000, 5000), (2050, 11025), (3000, 6090), (4000, 900), (5000, 2900), (4700, 5000), (4500, 7000), (5100, 5800),
                       (6100, 3100), (6050, 6050), (5795, 8090), (7500, 1350), (7700, 4000), (8700, 5000), (7000, 6871), (6900, 800), (7800, 10000),
                       (10000, 2950), (10700, 6125)]
    device_parameters["small"]["tessellation"] = "voronoi"
    device_parameters["small"]["number_of_antennas"] = len(bs_points_small)
    polygons_small = tessellations.generate_tessellations(device_parameters["small"]["tessellation"], points=bs_points_small)
    device_tessellation["small"]["points"] = bs_points_small
    device_tessellation["small"]["polygons"] = polygons_small

    # Channel tessellation
    voronoi_diagram, channel_voronoi_2d = tessellations.generate_tessellations("finite_voronoi", points=channel_points, size=map_size)

    # Distribute channels
    channels = []
    for i in range(0, channel_parameters["number_of_points"]):
        c = Channel("CHANNEL_" + str(i + 1), channel_config[i].split(" ")[0], channel_config[i].split(" ")[1], channel_parameters["losses_model"])
        channels.append(c)

    channel_tessellation = structured_diagram(channel_points, channels, channel_voronoi_2d)

    configuration_map_parameters = dict()
    configuration_map_parameters["map_size"] = map_size
    configuration_map_parameters["device_tessellation"] = device_tessellation
    configuration_map_parameters["channel_tessellation"] = channel_tessellation
    configuration_map_parameters["device_parameters"] = device_parameters
    configuration_map_parameters["channel_parameters"] = channel_parameters
    configuration_map_parameters["channel_voronoi_2d"] = channel_voronoi_2d

    return configuration_map_parameters


def configuration_resource_management_paper():
    """
        Generated scenario for RAN-slicing resource management paper (IEEE Access).
        4 macro base stations, 20 small base stations and Umi scenario in whole simulation map.

        :return [dict] simulation_map_parameters: simulation scenario parameters generated for the testing simulations.
    """

    map_size = 12000  # ? Size of the map -> 12 Km x 12 Km = 144 Km2

    # Channel configuration
    channel_points = [(7840, 5600), (5450, 11300), (5200, 5570), (1670, 1140)]  # Does not matter because is always the same propagation scenario (UMa)
    channel_config = ["Umi LOS", "Umi LOS", "Umi LOS", "Umi LOS"]

    channel_parameters = dict()
    channel_parameters["number_of_points"] = len(channel_points)
    channel_parameters["losses_model"] = "ABG"

    # Device configuration and tessellation
    device_parameters = dict({"macro": dict(), "small": dict()})
    device_tessellation = dict({"macro": dict(), "small": dict()})

    bs_points_macro = [(2900, 9000), (3100, 3000), (8250, 2500), (10075, 7500)]
    device_parameters["macro"]["tessellation"] = "voronoi"
    device_parameters["macro"]["number_of_antennas"] = len(bs_points_macro)
    polygons_macro = tessellations.generate_tessellations(device_parameters["macro"]["tessellation"], points=bs_points_macro)
    device_tessellation["macro"]["points"] = bs_points_macro
    device_tessellation["macro"]["polygons"] = polygons_macro

    bs_points_small = [(1450, 1000), (2000, 5000), (2050, 11025), (3000, 6090), (4000, 900), (5000, 2900), (4700, 5000), (4500, 7000), (5100, 5800),
                       (6100, 3100), (6050, 6050), (5795, 8090), (7500, 1350), (7700, 4000), (8700, 5000), (7000, 6871), (6900, 800), (7800, 10000),
                       (10000, 2950), (10700, 6125)]
    device_parameters["small"]["tessellation"] = "voronoi"
    device_parameters["small"]["number_of_antennas"] = len(bs_points_small)
    polygons_small = tessellations.generate_tessellations(device_parameters["small"]["tessellation"], points=bs_points_small)
    device_tessellation["small"]["points"] = bs_points_small
    device_tessellation["small"]["polygons"] = polygons_small

    # Channel tessellation
    voronoi_diagram, channel_voronoi_2d = tessellations.generate_tessellations("finite_voronoi", points=channel_points, size=map_size)

    # Distribute channels
    channels = []
    for i in range(0, channel_parameters["number_of_points"]):
        c = Channel("CHANNEL_" + str(i + 1), channel_config[i].split(" ")[0], channel_config[i].split(" ")[1], channel_parameters["losses_model"])
        channels.append(c)

    channel_tessellation = structured_diagram(channel_points, channels, channel_voronoi_2d)

    configuration_map_parameters = dict()
    configuration_map_parameters["map_size"] = map_size
    configuration_map_parameters["device_tessellation"] = device_tessellation
    configuration_map_parameters["channel_tessellation"] = channel_tessellation
    configuration_map_parameters["device_parameters"] = device_parameters
    configuration_map_parameters["channel_parameters"] = channel_parameters
    configuration_map_parameters["channel_voronoi_2d"] = channel_voronoi_2d

    return configuration_map_parameters
