# Module 'geometry_formulas'
# Created 10/02/2020 (version 3.0)
# Modified 20/01/2021 (version 6.0) - Jose Javier Rico Palomo

import math as m
import networkx as nx
from typing import *
from shapely.geometry import LineString


def euclidean_distance(position1: Tuple[float, float], position2: Tuple[float, float], elevation_tx: float = 0.0, elevation_rx: float = 0.0):
    """
        Calculates the three-dimensional euclidean distance between two points, given the coordinates, taking into account their heights.

        :param position1: X and Y coordinates of the transmitter or the first position -> (x,y).
        :param position2: X and Y coordinates of the receiver or the second position -> (x,y).
        :param* elevation_tx: height of the transmitter (in meters). Defaults to 0.
        :param* elevation_rx: height of the receiver (in meters). Defaults to 0.

        :return [float] distance: three-dimensional distance between transmitter and receiver.
    """

    distance = m.sqrt((position1[0]-position2[0])**2 + (position1[1]-position2[1])**2 + (elevation_rx-elevation_tx)**2)

    return distance


def dijkstra(graph: nx.graph, initial_node: int, final_node: int):
    """
        Given a graph, found the shortest path from a start node to an end node, taking into account the number of jumps.

        :param graph: graph to calculate the shortest path.
        :param initial_node: position of the initial node of the path. Relative position in the graph structure.
        :param final_node: position of the final node of the path. Relative position in the graph structure.

        :return [list of ints / int] shortest_path: position of the nodes on the shortest path (from the start node to the end node). If the path not found, it returns 0.
    """

    shortest_path = nx.dijkstra_path(graph, initial_node, final_node)

    return shortest_path if shortest_path != "None" else 0  # If the networkx library return "None", the path has not been found


def calculate_incident_angle(rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
    """
        It calculates the incident angle between a transmitter and a receiver in the XY plane and ZY plane.
        Necessary to calculate the attenuation factor in a antenna radiation pattern.

        :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
        :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
        :param* rx_height: height of the transmitter (in meters). Defaults to 0.
        :param* tx_height: height of the receiver (in meters). Defaults to 0.

        :return [tuple of floats] incident_angles: incident angle in XY plane (pos 0) and incident angle in ZY plane (pos 1).

        :raise ValueError: occurs when a value is not valid.
    """

    # X and Y plane
    line_tx_rx = LineString([rx_position, tx_position])

    # Obtain the quadrant in which the receiver is located with respect to the coordinate axis of the transmitter.

    if rx_position[0] >= tx_position[0] and rx_position[1] > tx_position[1]:  # first quadrant
        aux_point = (rx_position[0], tx_position[1])  # Intersection between the X-axis and its perpendicular passing through the receiving point
        accumulative_angle = 0

    elif rx_position[0] < tx_position[0] and rx_position[1] >= tx_position[1]:  # second quadrant
        aux_point = (tx_position[0], rx_position[1])  # Intersection between the Y-axis and its perpendicular passing through the receiving point
        accumulative_angle = 0 + 90

    elif rx_position[0] <= tx_position[0] and rx_position[1] < tx_position[1]:  # third quadrant
        aux_point = (rx_position[0], tx_position[1])  # Intersection between the X-axis and its perpendicular passing through the receiving point
        accumulative_angle = 0 + 180

    elif rx_position[0] > tx_position[0] and rx_position[1] < tx_position[1]:  # forth quadrant
        aux_point = (tx_position[0], rx_position[1])  # Intersection between the Y-axis and its perpendicular passing through the receiving point
        accumulative_angle = 0 + 270

    else:
        raise ValueError

    aux_line = LineString([tx_position, aux_point])

    # Calculate the angle between 'line_tx_rx' and 'aux_line'
    angle_beta = m.acos(line_tx_rx.length / aux_line.length)  # cos(B) = |line1| / |line2| (in a rectangular triangle)

    incident_angle_x = angle_beta + accumulative_angle

    # Y and Z plane
    if rx_height == 1 and tx_height == 1:
        incident_angle_z = 0

    else:
        distance_3d_tx_rx = euclidean_distance(tx_position, rx_position, elevation_tx=tx_height, elevation_rx=rx_height)
        distance_2d_tx_rx = euclidean_distance(tx_position, rx_position)
        incident_angle_z = m.acos(distance_3d_tx_rx / distance_2d_tx_rx)  # cos(B) = |line1| / |line2| (in a rectangular triangle)

    angles = (incident_angle_x, incident_angle_z)

    return angles


def haversine_distance(p1_latlon: str, p2_latlon: str, earth_radius: float = 6371):
    """
        It calculates the haversine distance between two points, according to earth geometry.
        Determines the great-circle distance between two points on a sphere given their longitudes and latitudes.
        [REF] https://en.wikipedia.org/wiki/Haversine_formula

        :param p1_latlon: latitude and longitude of first point (in radians) -> Example = "39'67,-6'8".
        :param p2_latlon: latitude and longitude of second point (in radians) -> Example = "39'67,-6'8".
        :param* earth_radius: radius of the circumference of the earth (in kilometers). Defaults to 6371.

        :return [float] total_distance: haversine distance between p1 and p2 (in meters).
    """

    p1_lat_rad = m.radians(float(p1_latlon.split(",")[0]))
    p1_lon_rad = m.radians(float(p1_latlon.split(",")[1]))
    p2_lat_rad = m.radians(float(p2_latlon.split(",")[0]))
    p2_lon_rad = m.radians(float(p2_latlon.split(",")[1]))

    d_lon = p2_lon_rad - p1_lon_rad
    d_lat = p2_lat_rad - p1_lat_rad

    a = m.sin(d_lat / 2)**2 + m.cos(p1_lat_rad) * m.cos(p2_lat_rad) * m.sin(d_lon / 2)**2
    c = 2 * m.asin(m.sqrt(a))

    total_distance = c * earth_radius * 1000

    return total_distance


def latlon_to_xy(origin_latlon, p_latlon):
    """
        It transforms one point, given in latitude and longitude coordinates, to cartesian point in XY plane, given the first point as (0,0) reference.
        
        :param origin_latlon: latitude and longitude of origin point (in radians) -> Example = "39'67,-6'8".
        :param p_latlon: latitude and longitude of the point to be transformed (in radians) -> Example = "39'67,-6'8".
    
        :return [tuple of floats] p_2_xy: point transformed to cartesian axes -> (x,y).
    """

    p1_lat = origin_latlon.split(",")[0]
    p1_lon = origin_latlon.split(",")[1]
    p2_lat = p_latlon.split(",")[0]
    p2_lon = p_latlon.split(",")[1]

    p_y_latlon = p2_lat+","+p1_lon
    p_x_latlon = p1_lat+","+p2_lon

    p_2_y = haversine_distance(origin_latlon, p_y_latlon)
    p_2_x = haversine_distance(origin_latlon, p_x_latlon)
    p_2_xy = (p_2_x, p_2_y)

    return p_2_xy
