# Class 'BsBackhaulBlock'
# Created 07/04/2021 (version 6.0)
# Modified 08/04/2021 (version 6.0) - Jose Javier Rico Palomo

import json
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.bs_antennas import BSAntenna, DirectionalAntenna
from SIMULATOR.src.CODE_UTILS.exceptions import InvalidNegativeValue, ConfigurationNotFound
from typing import *
import sys


class BsBackhaulBlock:
    """
        It composes the base stations. It simulates the behaviour of the part of the base station responsible for the management of the backhaul links and their integration into the cellular network.
        It opens and closes links to other base stations, switching antennas on and off.

        Attributes
        ----------
        - BB_id [str]: backhaul block identifier.
        - BB_available_bandwidth [float]: free bandwidth for the backhaul links.
        - BB_antennas [dict]: antennas responsible for connections to other base stations.
        - BB_links [dict]: links between the base station and the other base stations, which make up the backhaul network.
        - BB_assigned_bandwidth [dict]: bandwidth allocated to each backhaul link.
        - __max_backhaul_bandwidth [float]: bandwidth reserved for the backhaul portion of the base station.
        - __num_links [int]: number of active links.
        - BB_antenna_parameters [dict]: parameters of the backhaul antennas.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - add_backhaul_link: it adds a backhaul link to a Base Station.
        - remove_backhaul_link: it removes a backhaul link from a base station.
        - __recalculate_antenna_bandwidth (private): it recalculates the assigned bandwidth to the antennas.
        - get_max_backhaul_bandwidth: returns the total bandwidth available for backhaul links.
    """

    BB_id: str = ""  # Example = "BACKHAUL_BLOCK_1"
    BB_available_bandwidth: float = 0.0  # MHz
    BB_antennas: Dict[str, BSAntenna] = dict()  # key = antenna id, value = antenna object
    BB_links: Dict[str, str] = dict()  # key = antenna id, value = backhaul link id
    BB_assigned_bandwidth: Dict[str, float] = dict()  # key = antenna id, value = assigned bandwidth to antenna (in MHz)
    __max_backhaul_bandwidth: float = 0.0  # MHz
    __num_links: int = 0  # absolute units
    BB_antenna_parameters: dict = dict()

    def __init__(self, bs_id: str, dedicated_bandwidth: float, antenna_parameters: dict):
        """
            'Init' method of the class 'BackhaulBlock'.
            Constructor. Parametrized the object according to the entered parameters.

            :param bs_id: identifier of the base station that have the backhaul block -> Example = "MACRO_BS_7".
            :param dedicated_bandwidth: bandwidth reserved for the backhaul portion of the base station (in MHz).
            :param antenna_parameters: parameters of the backhaul antennas.
        """

        # Initialize dicts
        self.BB_antennas = dict()
        self.BB_links = dict()
        self.BB_assigned_bandwidth = dict()

        self.BB_id = "BACKHAUL_BLOCK_" + bs_id.split("_")[2]
        self.__max_backhaul_bandwidth = dedicated_bandwidth
        self.BB_available_bandwidth = self.__max_backhaul_bandwidth
        self.BB_antenna_parameters = antenna_parameters

    def __str__(self):
        """
            'To-string' method of the class 'BackhaulBlock'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.BB_id
        l2 = " - Max backhaul bandwidth: " + str(self.__max_backhaul_bandwidth) + " MHz"
        l3 = " - Available bandwidth: " + str(self.BB_available_bandwidth) + " MHz"
        l4 = " - Assigned bandwidth: " + str(self.BB_assigned_bandwidth)
        l5 = " - Active backhaul links: " + str(self.BB_links)
        l6 = " - Number of active links: " + str(self.__num_links)
        l7 = " - Active backhaul antennas: " + str([A for A in self.BB_antennas.keys()])
        l8 = " - Antenna parameters: " + str(self.BB_antenna_parameters)

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7 + "\n" + l8

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/backhaul_blocks/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/backhaul_blocks/".
        """

        data_dump = dict()
        bb_data = dict()

        bb_data["max_bandwidth"] = self.__max_backhaul_bandwidth
        bb_data["assigned_bandwidth"] = self.BB_assigned_bandwidth
        bb_data["available_bandwidth"] = self.BB_available_bandwidth
        bb_data["active_links"] = self.BB_links
        bb_data["num_links"] = self.__num_links
        bb_data["active_antennas"] = self.BB_antennas.keys()
        bb_data["antenna_parameters"] = self.BB_antenna_parameters

        data_dump[time] = bb_data

        with open(file_path + self.BB_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def add_backhaul_link(self, link_id: str):
        """
            It adds a backhaul link to a Base Station.

            :param link_id: identifier of the link to be added.
        """

        # Calculate the assigned bandwidth
        if self.BB_antenna_parameters["bandwidth"] < self.BB_available_bandwidth:
            bw = self.BB_antenna_parameters["bandwidth"]

        else:

            bw = self.__max_backhaul_bandwidth / (len(self.BB_antennas)+1)

            try:
                self.__recalculate_antenna_bandwidth(bw)
            except InvalidNegativeValue as e:  # Catch exception if occurs (parameter "self.BB_available_bandwidth")
                print(e)
                sys.exit(1)

        if self.BB_available_bandwidth < 0:
            raise InvalidNegativeValue(self.BB_available_bandwidth)

        # Create antenna
        antenna_id = "BACKHAUL_ANTENNA_"+str(len(self.BB_links)+1)
        height = self.BB_antenna_parameters["height"]
        frequency = self.BB_antenna_parameters["frequency"]
        azimuth = 10  # ! self.BB_antenna_parameters["azimuth"]  # TODO: calculate azimuth
        sr_azimuth = self.BB_antenna_parameters["scanning_range_azimuth"]
        tilt = 0  # ! self.BB_antenna_parameters["tilt"]  # TODO: calculate tilt
        sr_tilt = self.BB_antenna_parameters["scanning_range_tilt"]
        subpanel_configuration = dict({"n_panels": 1, "n_tx_per_panel": self.BB_antenna_parameters["n_tx"], "beams_configuration": {"beams_per_panel": 1, "p_tx_per_beam": self.BB_antenna_parameters["p_tx"], "gain_per_beam": self.BB_antenna_parameters["gain"], "z_width": 0, "y_width": 0}})
        radiation_pattern = "/home/jricopal/Escritorio/Mgain_34GHz_360.mat"  # TODO: self.BB_antenna_parameters["radiation_pattern_file"]
        antenna = DirectionalAntenna(antenna_id, "backhaul", None, None, height, frequency, bw, azimuth, sr_azimuth, tilt, sr_tilt, subpanel_configuration, radiation_pattern)

        # Update attributes
        self.BB_antennas[antenna.ANTENNA_id] = antenna
        self.BB_links[antenna.ANTENNA_id] = link_id
        self.BB_assigned_bandwidth[antenna.ANTENNA_id] = antenna.ANTENNA_bandwidth
        self.BB_available_bandwidth -= self.BB_assigned_bandwidth[antenna.ANTENNA_id]
        self.__num_links += 1

    def remove_backhaul_link(self, link_id: str):
        """
            It removes a backhaul link from a base station.

            :param link_id: identifier of the link to be removed.
        """

        antenna = None

        # Select the antenna who has the link opened
        for current_antenna in self.BB_links.keys():
            if self.BB_links[current_antenna] == link_id:
                antenna = self.BB_antennas[current_antenna]

        # If not found, raise an exception
        if antenna is None:
            raise ConfigurationNotFound(link_id)

        else:

            # Remove the antenna and the link from attributes
            del self.BB_links[antenna.ANTENNA_id]
            self.BB_available_bandwidth += self.BB_assigned_bandwidth[antenna.ANTENNA_id]
            del self.BB_assigned_bandwidth[antenna.ANTENNA_id]
            del self.BB_antennas[antenna.ANTENNA_id]
            self.__num_links -= 1

            # Recalculates the assigned bandwidth to other links
            if self.BB_antenna_parameters["bandwidth"]*len(self.BB_antennas) > 0:
                self.__recalculate_antenna_bandwidth(self.BB_antenna_parameters["bandwidth"])

            else:
                bw = self.__max_backhaul_bandwidth / len(self.BB_antennas)
                self.__recalculate_antenna_bandwidth(bw)

    def __recalculate_antenna_bandwidth(self, bandwidth_per_antenna: float):
        """
            It recalculates the assigned bandwidth to the antennas.

            :param bandwidth_per_antenna: assigned bandwidth to the antenna.
        """

        # Reset the available bandwidth
        self.BB_available_bandwidth = self.__max_backhaul_bandwidth

        # Reallocate the bandwidth in the active antennas
        for current_antenna in self.BB_antennas.keys():
            self.BB_antennas[current_antenna].ANTENNA_bandwidth = bandwidth_per_antenna
            self.BB_assigned_bandwidth[current_antenna] = self.BB_antennas[current_antenna].ANTENNA_bandwidth

            # Remove available bandwidth
            self.BB_available_bandwidth -= self.BB_assigned_bandwidth[current_antenna]

            if self.BB_available_bandwidth < 0:
                raise InvalidNegativeValue(self.BB_available_bandwidth)

    def get_max_backhaul_bandwidth(self):
        """
            Returns the total bandwidth available for backhaul links.

            :return [float] total_bandwidth: total bandwidth (in MHz).
        """

        return self.__max_backhaul_bandwidth
