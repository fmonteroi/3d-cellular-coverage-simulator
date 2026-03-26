# Class 'Channel'
# Created 06/04/2018 (version 1.0)
# Modified 21/01/2021 (version 6.0) - Jose Javier Rico Palomo

from __future__ import annotations

import configparser
import os.path
import math as m
import sys
from numpy.random import randn
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound
import SIMULATOR.src.MATH_UTILS.formulas as f
from shapely.geometry import Point, Polygon, LineString
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
from numpy.linalg import det
from numpy import identity as eye
import numpy as np
import itertools
from typing import *
import json

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from SIMULATOR.src.MAP.simulation_map import SimulationMap


class Channel:
    """
        Class 'Channel'.
        Simulates the behaviour of a propagation channel according to its environment, type of scenario and characteristics.
        It contains the necessary method for the channels own calculation (free space losses, capacity, etc...).
        The Channels are included in the simulation map and in the links.

        Attributes
        ----------
        - CHANNEL_id [str]: channel identifier.
        - __scenario (private) [str]: scenario type.
        - __environment (private) [str]: line of sight.
        - __model_parameters (private) [dict]: necessary parameters for the channel characterization. They are collected from the channel model configuration files.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __get_model_parameters (private): it collects the parameters of the scenario according to the model chosen when creating the object.
        - path_loss: it calculates free space losses as a function of transmitter-receiver distance, operating frequency and model-specific parameters.
        - link_budget (class method): it calculates the received power in dBm by the receiver of a radio link (classic power link budget formula).
        - sinr (class method): it calculates the signal-to-interference-plus-noise-ratio level as a function of link bandwidth, received power and received interferences from others antennas.
        - spectral_efficiency_mimo (class method): it calculates the spectral efficiency (theoretical capacity) of the link according to the number of transmitting and receiving antennas and the sinr level.
        - capacity_shannon (class method): it calculates the channel capacity according to Shannon's formula.
        - weight_channels (class method): it weights the propagation channels when a link goes through more than one channel. It is used for the calculation of weighted losses.
        - weight_losses (class method): it calculates the free space loss according to the previously calculated weighted channels.
    """

    CHANNEL_id = ""  # Example: "CHANNEL_1"
    __scenario = ""  # "UMa" (Urban MacroCell) / "Umi" (Urban Microcell) / "Ind" (Indoor) / "Rural" (Rural MacroCell)
    __environment = ""  # "LOS" (Line of sight) / "NLOS" (No line of sight)
    __model_parameters = dict()

    def __init__(self, channel_id: str, scenario: str, environment: str, losses_model: str, model_parameters: dict = None, config_file_path: str = "SIMULATOR/Configuration/model_config/channels/"):
        """
            'Init' method of the class 'Channel'.
            Constructor. Parametrized the object according to the entered parameters.

            :param channel_id: channel identifier -> Example = "CHANNEL_1".
            :param scenario: scenario type -> "UMa" (Urban MacroCell) / "Umi" (Urban Microcell) / "Ind" (Indoor) / "Rural" (Rural MacroCell).
            :param environment: line of sight -> "LOS" (Line of sight) / "NLOS" (No line of sight).
            :param losses_model: losses model to calculate the channel. Parameterised for the whole simulation. Necessary to obtain the parameters -> "ABG" / "CI" / "FSPL".
            :param* model_parameters: predefined parameters for configuring the channel. Defaults to None.
            :param* config_file_path: path to the folder containing the configuration file of the channel models. Defaults to "SIMULATOR/Configuration/model_config/channels/".

            :except FileExistsError: THE PROGRAM WILL EXIT IF 'FILE EXIST ERROR' EXCEPTIONS OCCURS (file in 'SIMULATOR/Configuration/model_config/channels/').
            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "losses_model").
        """

        self.CHANNEL_id = channel_id
        self.__scenario = scenario
        self.__environment = environment

        try:
            self.__model_parameters = self.__get_model_parameters(config_file_path, losses_model) if model_parameters is None else model_parameters

        except FileExistsError as e1:  # Catch exception if occurs (if configuration file doesnt exist)
            print(e1)
            sys.exit(3)

        except ConfigurationNotFound as e2:  # Catch exception if occurs (parameter 'losses_model')
            print(e2)
            sys.exit(2)

    def __str__(self):
        """
            'To-string' method of the class 'Channel'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.CHANNEL_id
        l2 = " - Scenario type: " + self.__scenario
        l3 = " - Environment type: " + self.__environment
        l4 = " - Losses model: " + self.__model_parameters["losses_model"]
        l5 = " - Model parameters: " + str([P for P in self.__model_parameters.values()])

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/simulation_map/propagation_channels/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the propagation channels. Defaults to "/SIMULATOR/Results/simulation_map/propagation_channels/".
        """

        data_dump = dict()
        channel_data = dict()

        channel_data["scenario"] = self.__scenario
        channel_data["environment"] = self.__environment

        data_dump[time] = channel_data

        with open(file_path + self.CHANNEL_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __get_model_parameters(self, file_path: str, losses_model: str):
        """
            It collects the parameters of the scenario according to the model chosen when creating the object.
            Depending on the chosen loss model, the parameter dict will have one format or another.

            :param file_path: path to the folder containing the configuration file of the channel models.
            :param losses_model: losses model to calculate the channel. Parameterised for the whole simulation. Necessary to obtain the parameters (token) -> "ABG" / "CI" / "FSPL".

            :return [dict] parameters: parameters for configuring the channel. Depending on the chosen losses model, the dict will contain one or other values.

            :raise FileNotFoundError: occurs when the file you want to access does not exist.
            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        parameters = dict()

        file_name = "SCENARIO_" + self.__scenario + "_" + self.__environment  # Example = "SCENARIO_Umi_NLOS".

        # Open the file in read by tokens mode
        config_file = configparser.ConfigParser()

        if os.path.isfile(file_path + file_name):  # Check if file exist
            config_file.read(file_path + file_name)
        else:  # If doest exist, raise and exception
            raise FileNotFoundError(file_path + file_name)

        # Read and collect the parameters
        parameters["losses_model"] = losses_model

        if losses_model == "ABG":
            parameters["alpha"] = config_file[losses_model]["alpha"]
            parameters["beta"] = config_file[losses_model]["beta"]
            parameters["gamma"] = config_file[losses_model]["gamma"]
            parameters["shadow_factor"] = config_file[losses_model]["shadow_factor"]

        elif losses_model == "CI":
            parameters["n"] = config_file[losses_model]["n"]
            parameters["d0"] = config_file[losses_model]["d0"]
            parameters["shadow_factor"] = config_file[losses_model]["shadow_factor"]

        elif losses_model == "FSPL":
            pass  # No parameters are necessary for this losses model

        else:
            raise ConfigurationNotFound(losses_model)

        return parameters

    def path_loss(self, distance: float, frequency: float):
        """
            It calculates free space losses as a function of transmitter-receiver distance, operating frequency and model-specific parameters.
            Depending on the propagation losses model selected, one formula or another will be used.
            [REF] T. S. Rappaport et al, “Investigation of Prediction Accuracy, Sensitivity, and Parameter Stability of Large-Scale Propagation Path Loss Models for 5g Wireless Communications,” arXiv:1603.04404 [cs, math], Mar. 2016, arXiv: 1603.04404.

            :param distance: distance between transmitter and receiver (in meters). Can be 2D or 3D, depending on the model.
            :param frequency: operating frequency of the transmitted wave (in GHz).

            :return [float] losses: free space losses of the signal (in dB).
        """

        c = 3e8  # light speed
        losses = -1

        if self.__model_parameters["losses_model"] == "ABG":

            alpha = float(self.__model_parameters["alpha"])
            beta = float(self.__model_parameters["beta"])
            gamma = float(self.__model_parameters["gamma"])
            shadow_factor = float(self.__model_parameters["shadow_factor"])

            losses_abg = 10 * alpha * m.log10(distance) + beta + 10 * gamma * m.log10(frequency) + shadow_factor * randn()
            losses = losses_abg

        elif self.__model_parameters["losses_model"] == "CI":

            n = float(self.__model_parameters["n"])
            d_0 = float(self.__model_parameters["d0"])
            shadow_factor = float(self.__model_parameters["shadow_factor"])

            losses_fspl = 20 * m.log10((4 * m.pi * frequency * d_0 * 1000000000) / c)
            losses_ci = losses_fspl + 10 * n * m.log10(distance / d_0) + shadow_factor * randn()
            losses = losses_ci

        elif self.__model_parameters["losses_model"] == "FSPL":

            losses_fspl = 20 * m.log10((4 * m.pi * frequency * distance * 1000000000) / c)
            losses = losses_fspl

        return losses

    @classmethod
    def link_budget(cls, tx_power: float, tx_gain: float, rx_gain: float, path_losses: float, line_losses: float = 0.0):
        """
            It calculates the received power in dBm by the receiver of a radio link (classic power link budget formula).

            :param tx_power: power of the transmitter antenna (in dBm).
            :param tx_gain: gain of the transmitter antenna (in dBi).
            :param rx_gain: gain of the receiver antenna (in dBi).
            :param path_losses: free space losses of the link (in dB).
            :param* line_losses: antennas transmission lines losses. Defaults to 0.

            :return [float] rx_signal_dbm: power detected in the receiver antenna (in dBm).
        """

        rx_signal_dbm = tx_power - 2 * line_losses + tx_gain - path_losses + rx_gain
        return rx_signal_dbm

    @classmethod
    def sinr(cls, rx_power: float, bandwidth: float, interferences: float):
        """
            It calculates the signal-to-interference-plus-noise-ratio level as a function of link bandwidth, received power and received interferences from others antennas.
            The bandwidth is used to calculate the link noise.

            :param rx_power: power detected in the receiver antenna (in mW).
            :param bandwidth: bandwidth allocated to the link (in MHz).
            :param interferences: sum of the interferences (received power) by each of the other antennas (in mW).

            :return [float] sinr_db: signal-to-interference-plus-noise-ratio level in the receiver (in dBm).
        """

        noise_db = -174 + 10*m.log10(bandwidth*1000000)
        noise_units = f.to_units(noise_db)

        sinr_units = rx_power / (noise_units + interferences)
        sinr_db = f.to_db(sinr_units)

        return sinr_db

    @classmethod
    def spectral_efficiency_mimo(cls, n_tx: int, n_rx: int, sinr_db: float):
        """
            It calculates the spectral efficiency (theoretical capacity) of the link according to the number of transmitting and receiving antennas and the sinr level.
            [REF] Foschini, G., Gans, M. On Limits of Wireless Communications in a Fading Environment when Using Multiple Antennas. Wireless Personal Communications 6, 311–335 (1998).

            :param n_tx: number of transmitting antennas.
            :param n_rx: number of receiving antennas.
            :param sinr_db: signal-to-interference-plus-noise-ratio level of the link (in dB).

            :return [float] spectral_efficiency: theoretical mean capacity of the link (in bps/Hz).
        """

        samples = 10  # Number of samples
        num_matrix = 8  # Number of H-matrix to calculate

        sinr_db = [sinr_db] if isinstance(sinr_db, list) is False else sinr_db

        sinr = []
        [sinr.append(f.to_units(sinr_db[i])) for i in range(0, len(sinr_db))]

        h = np.empty((n_tx, n_rx, samples), dtype=np.complex)  # Empty complex matrix (H-matrix)
        tc_aux = np.empty((num_matrix, len(sinr), samples), dtype=np.complex)  # Theoretical capacity auxiliary matrix (without mean)
        h_t = []  # Random H-matrix vector
        tc = np.empty((num_matrix, len(sinr)))  # Theoretical capacity vector (in mean)

        for i in range(0, num_matrix):  # Random H-matrix generation

            complex_matrix_aux_1 = randn(n_tx, n_rx, samples)  # Random auxiliary matrix
            complex_matrix_aux_2 = randn(n_tx, n_rx, samples)  # Random auxiliary matrix

            for c1 in range(0, n_tx):
                for c2 in range(0, n_rx):
                    for c3 in range(0, samples):
                        h[c1][c2][c3] = complex(complex_matrix_aux_1[c1][c2][c3], complex_matrix_aux_2[c1][c2][c3]) / m.sqrt(2)  # Generates random H-matrix
                        h_t.append(h)  # Store the H-matrix in the 'h_t' vector

            for j in range(0, len(sinr)):  # SNR
                for k in range(0, samples):  # Samples

                    tc_aux[i][j][k] = m.log2(abs(det(eye(n_tx) + (sinr[j] / n_rx * np.dot(h[:, :, k], h[:, :, k].conj().transpose())))))  # Calculates theoretical capacity by previously calculated H-matrix

                tc[i][j] = abs(tc_aux[i][j].mean())

        spectral_efficiency_aux = sum(tc) / len(tc)
        spectral_efficiency = spectral_efficiency_aux[0]  # bps/Hz

        return spectral_efficiency

    @classmethod
    def capacity_shannon(cls, sinr: float, bandwidth: float):
        """
            It calculates the channel capacity according to Shannon's formula.
            [REF] https://en.wikipedia.org/wiki/Channel_capacity

            :param sinr: assigned bandwidth to the link (in MHz).
            :param bandwidth: signal-to-interference-plus-noise-ratio level of the link (in dB).

            :return [float] capacity: maximum capacity supported by the link by shannon formula (in Mbps)
        """

        capacity_shannon = bandwidth * m.log2(1+f.to_units(sinr))

        return capacity_shannon

    @classmethod
    def weight_channels(cls, pos_source: Tuple[float, float], pos_peer: Tuple[float, float], simulation_map: SimulationMap, tx_height: float = 0.0, rx_height: float = 0.0):
        """
            It weights the propagation channels when a link goes through more than one channel. It is used for the calculation of weighted losses.

            O1 ------ |  --------------- |  -------------------- O2  -> total_distance
            O1 ------ X1                                             -> d_1 = distance(O1,X1)
            O1 ------ X1 --------------- X2                          -> d_2 = distance(O1,X2) - distance(O1,X1)
            O1 ------ X1 --------------- X2 -------------------- O2  -> d_3 = distance(O1,O2) - distance(O1,X2)
                                                                     -> d_n = distance(O1,Xn) - distance(O,Xn-1)

            :param pos_source: X and Y position of the transmitter antenna -> (x,y).
            :param pos_peer: X and Y position of the receiver antenna -> (x,y).
            :param simulation_map: map generated for the simulation.
            :param* tx_height: tilt of the transmitter antenna (in meters). Defaults to 0.
            :param* rx_height: tilt of the receiver antenna (in meters). Defaults to 0.

            :return [tuple of object (SIMULATOR.Channel) and Float] weighted_channels: channels through which the link passes and distances (in meters) travelled on each channel.
        """

        weighted_channels = []
        same_polygon = False
        aux_distances = []  # [ (0) [intersection_point_p1, distance_source_p1], (1) [intersection_point_p2, distance_source_p2], ... ]

        # Origin and destination points (class "shapely.geometry.Point")
        point_source = Point(pos_source)
        point_peer = Point(pos_peer)

        # It calculates the inclination angle (for 3D distance) -> Tg(a) = opposite_side / adjacent_side
        tg_a = abs(tx_height - rx_height) / gf.euclidean_distance(pos_source, pos_peer) if tx_height > 0 and rx_height > 0 else 0

        # Iterate polygons
        for current_channel in simulation_map.MAP_channel_tessellation.keys():

            current_polygon = Polygon(simulation_map.MAP_channel_tessellation[current_channel]["polygon"][0])

            # If both points stay in the same polygon
            if current_polygon.contains(point_source) and current_polygon.contains(point_peer):
                weighted_channels.append([current_channel, gf.euclidean_distance(pos_source, pos_peer, elevation_tx=tx_height, elevation_rx=rx_height)])
                same_polygon = True

        # If the points do not stay in the same polygon
        if same_polygon is False:

            # It creates the origin-destination line
            line = LineString([pos_source, pos_peer])

            # Iterate polygons
            for current_channel in simulation_map.MAP_channel_tessellation.keys():
                current_polygon = simulation_map.MAP_channel_tessellation[current_channel]["polygon"]

                # Iterate edges
                for e in range(0, len(current_polygon[1])):
                    current_edge = current_polygon[1][e]

                    # Check if intersection exist
                    if line.intersects(current_edge):  # the edges are already 'LineString'

                        # It calculates the intersection point
                        intersection_pos = (line.intersection(current_edge).x, line.intersection(current_edge).y)

                        # It calculates the intersection point height
                        intersection_point_height = rx_height + (tg_a * gf.euclidean_distance(pos_source, intersection_pos)) if tx_height > 0 and rx_height > 0 else 0

                        # It calculates and adds the 3D distance to the aux distance array
                        aux_distances.append([intersection_pos, gf.euclidean_distance(pos_source, intersection_pos, elevation_tx=tx_height, elevation_rx=intersection_point_height)])

            # It removes equal elements in the aux distance array
            # The intersections with the edges are duplicated because two contiguous polygons have that edge added separately
            aux_distances.sort()
            aux_distances = list(aux_distances for aux_distances, _ in itertools.groupby(aux_distances))

            # It adds the origin (distance equal to 0) and the destination (distance between source and peer) in the aux distance vector
            aux_distances.append([pos_source, 0])  # Source
            aux_distances.append([pos_peer, gf.euclidean_distance(pos_source, pos_peer, elevation_tx=tx_height, elevation_rx=rx_height)])  # Destination

            # It sorts the aux distance vector from smallest to largest
            aux_distances = sorted(aux_distances, key=lambda array_distances: array_distances[1])

            # It finds out the propagation channels the middle point of the intersections is located and stores the distance between the points of interest (origin, intersections and destination).
            for i in range(0, len(aux_distances) - 1):
                middle_point = Point((aux_distances[i][0][0] + aux_distances[i + 1][0][0]) / 2, (aux_distances[i][0][1] + aux_distances[i + 1][0][1]) / 2)
                channel_distance = aux_distances[i + 1][1] - aux_distances[i][1]

                # Iterate polygons
                for current_channel in simulation_map.MAP_channel_tessellation.keys():
                    current_polygon = Polygon(simulation_map.MAP_channel_tessellation[current_channel]["polygon"][0])

                    # It stores the propagation channel in which the middle point is located and its distance
                    if current_polygon.contains(middle_point):
                        weighted_channels.append([current_channel, channel_distance])

        return weighted_channels

    @classmethod
    def weight_losses(cls, weighted_channels: List[Tuple[str, float]], frequency: float, simulation_map: SimulationMap):
        """
            It calculates the free space loss according to the previously calculated weighted channels.

            :param weighted_channels: list of weighted channel in the link (Object SIMULATOR.Channel and distance in meters) -> [ (channel1,d1), (channel2,d2),... ]
            :param frequency: operation frequency of the transmitter antenna (in GHz).
            :param simulation_map: map generated for the simulation.

            :return [float] total_losses: total free space loss in whole link (in dB).
        """

        total_losses = []
        distances = []
        # Calculate total distance
        [distances.append(weighted_channels[c][1]) for c in range(0, len(weighted_channels))]

        # Calculate total losses in the channel
        for c in range(0, len(weighted_channels)):
            current_loss = simulation_map.MAP_channel_tessellation[weighted_channels[c][0]]["channel"].path_loss(sum(distances), frequency)  # Loss of the whole link as if there was only one channel
            weight = weighted_channels[c][1] / sum(distances)  # Weight of that channel in relation to the total (as a percentage of 1)
            total_losses.append(current_loss * weight)  # Weighted loss

        return sum(total_losses)
