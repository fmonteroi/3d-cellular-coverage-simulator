# Module 'tessellations'
# Created 06/03/2020 (version 3.0)
# Modified 29/01/2021 (version 6.0) - Jose Javier Rico Palomo

from scipy.spatial import Voronoi
import numpy as np
import math as m
from SIMULATOR.src.GEOMETRY import point_process as pp
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound, ConditionalParameterIsDefault
from typing import *


def generate_tessellations(tessellations: str, points: List[Tuple[float, float]] = None, size: float = 0, hexagon_radius: float = 0.0):
    """
        Generates the chosen tessellation according to the entered parameters.

        :param tessellations: chosen tessellation.
        :param* points: pre-generated point for voronoi tessellation -> [(x,y), (x,y), ...]. Defaults to None.
        :param* size: size of one of the sides of the scenario, taking into account square scenarios (in meters). Defaults to 0.
        :param* hexagon_radius: radius of the hexagons to be generated (in meters). Defaults to 0.

        :return [2-pos list] FOR HEXAGONAL TESSELLATION: array of tuples for hexagon center points (pos 0) and array of arrays for hexagon vertices (pos 1).
        :return [1-pos list] FOR VORONOI TESSELLATION: Object (Scipy.spatial.Voronoi) of the generated diagram.
        :return [2-pos list] FOR FINITE VORONOI TESSELLATION: Object (Scipy.spatial.Voronoi) of the generated diagram (pos 0) and finite regions of the voronoi diagram (pos 1, subpos 0) and the generated regions (pos 1, subpos 1).

        :except ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        :except ConditionalParameterIsDefault: occurs when the conditional parameters have default values (if the default configuration is not configured).
    """

    if tessellations == "hexagonal":

        # Check if conditional parameters have the default value
        if size is generate_tessellations.__defaults__[1]:
            raise ConditionalParameterIsDefault("size")

        if hexagon_radius is generate_tessellations.__defaults__[2]:
            raise ConditionalParameterIsDefault("hexagon_radius")

        generated_points, generated_polygons = hexagonal_tessellation(hexagon_radius, size)
        return [generated_points, generated_polygons]

    elif tessellations == "voronoi":

        # Check if conditional parameters have the default value
        if points is generate_tessellations.__defaults__[0]:
            raise ConditionalParameterIsDefault("points")

        return [voronoi_tessellation(points)]  # ! points[0]

    elif tessellations == "finite_voronoi":

        # Check if conditional parameters have the default value
        if points is generate_tessellations.__defaults__[0]:
            raise ConditionalParameterIsDefault("points")

        if size is generate_tessellations.__defaults__[1]:
            raise ConditionalParameterIsDefault("size")
        
        generated_diagram = voronoi_tessellation(points)
        generated_regions, generated_vertices = voronoi_finite_polygons_2d(generated_diagram, radius=size*10)

        return [generated_diagram, [generated_regions, generated_vertices]]

    else:
        raise ConfigurationNotFound(tessellations)


def voronoi_tessellation(points):
    """
        Generation of a tessellation based on a voronoi diagram of given points.
        [REF] S. N. Chiu, Stochastic Geometry and Its Applications.

        :param points: X and Y positions of the points that govern the tessellation -> [(x,y), (x,y), ...].

        :return [object (Scipy.spatial.Voronoi)] diagram: generated voronoi diagram.
    """

    diagram = Voronoi(points, qhull_options="Qbb Qc Qx")

    return diagram


def voronoi_finite_polygons_2d(voronoi_diagram: Voronoi, radius: float = 0.0):
    """
        Cuts out an infinite voronoi diagram to make it finite.
        For plot the cut out diagram, it is necessary to transform the vertices to "np.array" -> vertices = np.array(vertices)
        [REF] https://gist.github.com/pv/8036995

        :param voronoi_diagram: generated voronoi diagram.
        :param* radius: size of the frame that delimits the diagram (in meters). Defaults to 0.

        :return [list of lists] new_regions: edges of the enclosed polygons of the new generated voronoi diagram.
        :return [list of lists] new_vertices: vertices of the enclosed polygons of the new generated voronoi diagram.
    """

    new_regions = []
    new_vertices = voronoi_diagram.vertices.tolist()

    center = voronoi_diagram.points.mean(axis=0)

    if radius is None:
        radius = voronoi_diagram.points.ptp().max() * 2

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(voronoi_diagram.ridge_points, voronoi_diagram.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(voronoi_diagram.point_region):
        vertices = voronoi_diagram.regions[region]

        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)  # finite region
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:

            if v2 < 0:
                v1, v2 = v2, v1

            if v1 >= 0:  # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = voronoi_diagram.points[p2] - voronoi_diagram.points[p1]  # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = voronoi_diagram.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = voronoi_diagram.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, new_vertices


def hexagonal_tessellation(radius: float, size: float):
    """
        Generation of a hexagonal tessellation.
        The points are generated in the centre of the hexagons once the polygons are generated, it is not passed as a parameter.
        [REF] https://gist.github.com/urschrei/17cf0be92ca90a244a91

        :param radius: radius of the hexagons to be generated (in meters).
        :param size: size of one of the sides of the scenario, taking into account square scenarios (in meters).

        :return [list of tuples] generated_points: X and Y positions of the centres of the generated hexagons -> [(x,y), (x,y), ...].
        :return [list of lists] generated_polygons: X and Y positions of the edges that compose the generated hexagons.
    """

    generated_polygons = []
    points = []

    # start_x = 0 + radius
    # start_y = 0 + radius
    end_x = size - 2 * radius
    end_y = size - 2 * radius

    sl = (2 * radius) * m.tan(m.pi / 6)
    p = sl * 0.5
    b = sl * m.cos(m.radians(30))
    w = b * 2
    h = 2 * sl

    start_x = 0 - radius  # start_x - w
    start_y = 0 - radius  # start_y - h
    end_x = end_x + w
    end_y = end_y + h

    orig_x = start_x
    # orig_y = start_y

    x_offset = b
    y_offset = 3 * p

    row = 1
    counter = 0

    while start_y < end_y:

        if row % 2 == 0:
            start_x = orig_x + x_offset

        else:
            start_x = orig_x

        while start_x < end_x:

            p1x = start_x
            p1y = start_y + p
            p2x = start_x
            p2y = start_y + (3 * p)
            p3x = start_x + b
            p3y = start_y + h
            p4x = start_x + w
            p4y = start_y + (3 * p)
            p5x = start_x + w
            p5y = start_y + p
            p6x = start_x + b
            p6y = start_y
            poly = [(p1x, p1y), (p2x, p2y), (p3x, p3y), (p4x, p4y), (p5x, p5y), (p6x, p6y), (p1x, p1y)]

            generated_polygons.append(poly)
            points.append(((p1x + p4x) / 2, (p1y + p4y) / 2))

            counter += 1
            start_x += w

        start_y += y_offset
        row += 1

    return points, generated_polygons


def hexagon_voronoi(hexagon_radius: float, size: float, sigma: float, alpha: float = 0.0, points_per_hexagon: int = 0, voronoi_point_process: str = "poisson"):
    """
        Generation of a hexagonal tessellation with a voronoi tessellation in each hexagon.
        The macro cells are generated following a hexagonal tessellation, and the small cells are generated according to a specific point process in each hexagon.

        :param hexagon_radius: radius of the hexagons to be generated (in meters).
        :param size: size of one of the sides of the scenario, taking into account square scenarios (in meters).
        :param sigma: variance of the gaussian distribution used for the point generation in each hexagon (absolute units).
        :param* alpha: density of the poisson point process if the number of points has not been specified (absolute units). Defaults to 0.
        :param* points_per_hexagon: number of points in each hexagon to be distributed according to poisson process. Defaults to 0.
        :param* voronoi_point_process: point process to generate voronoi tessellation points. Defaults to "poisson".

        :return [list of tuples] macro_points: X and Y positions of the centres of the generated hexagons -> [(x,y), (x,y), ...].
        :return [list of tuples] small_points: X and Y positions of the edges that compose the generated hexagons -> [(x,y), (x,y), ...].
        :return [list of lists] macro_polygons: X and Y position of the points generated for voronoi tessellation.
        :return [object (Scipy.spatial.Voronoi)] small_polygons: generated voronoi diagram.

        :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
    """

    # Macro generation
    macro_points, macro_polygons = hexagonal_tessellation(hexagon_radius, size)

    # Small generation
    if voronoi_point_process == "poisson":
        small_points = pp.poisson_in_hex(macro_points, sigma, points_per_hexagon=points_per_hexagon, alpha=alpha)
    # * Add different generations of location for small cells (elif)
    else:
        raise ConfigurationNotFound(voronoi_point_process)

    small_polygons = voronoi_tessellation(small_points)

    return macro_points, small_points, macro_polygons, small_polygons
