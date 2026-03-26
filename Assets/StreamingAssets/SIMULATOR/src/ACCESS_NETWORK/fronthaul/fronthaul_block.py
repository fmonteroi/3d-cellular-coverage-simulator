# Class 'BsFronthaulBlock'
# Created 07/04/2021 (version 6.0)
# Modified 08/04/2021 (version 6.0) - Jose Javier Rico Palomo

import json
from SIMULATOR.src.CODE_UTILS.exceptions import InvalidNegativeValue
import sys


class BsFronthaulBlock:
    """
        It composes the base stations. It simulates the behaviour of the part of the base station responsible for the management of the fronthaul links and their integration into the cellular network.
        It opens and closes links between base stations and routers.

        Attributes
        ----------
        - FB_id [str]: fronthaul block identifier.
        - FB_available_bandwidth [float]: free bandwidth for the fronthaul links.
        - FB_links [dict]: links between the base station and routers, which make up the fronthaul network.
        - FB_assigned_bandwidth [dict]: bandwidth allocated to each fronthaul link.
        - __max_fronthaul_bandwidth [float]: bandwidth reserved for the fronthaul portion of the base station.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - add_fronthaul_link: it adds a fronthaul link to a Base Station.
        - remove_fronthaul_link: it removes a fronthaul link from a base station.
        - __recalculate_link_bandwidth (private): it recalculates the assigned bandwidth to the links.
    """

    FB_id: str = ""  # Example = "FRONTHAUL_BLOCK_1"
    FB_available_bandwidth: float = 0.0  # MHz
    FB_links: dict = dict()  # key = device id, value = fronthaul link id
    FB_assigned_bandwidth: dict = dict()  # key = link id, value = assigned bandwidth to the link (in MHz)
    __max_fronthaul_bandwidth: float = 0.0  # MHz

    def __init__(self, bs_id: str, dedicated_bandwidth: float):
        """
            'Init' method of the class 'FronthaulBlock'.
            Constructor. Parametrized the object according to the entered parameters.

            :param bs_id: identifier of the base station that have the fronthaul block -> Example = "MACRO_BS_7".
            :param dedicated_bandwidth: bandwidth reserved for the fronthaul portion of the base station (in MHz).
        """

        self.FB_id = "FRONTHAUL_BLOCK_" + bs_id.split("_")[2]
        self.__max_fronthaul_bandwidth = dedicated_bandwidth
        self.FB_available_bandwidth = self.__max_fronthaul_bandwidth

    def __str__(self):
        """
            'To-string' method of the class 'FronthaulBlock'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.FB_id
        l2 = " - Max fronthaul bandwidth: " + str(self.__max_fronthaul_bandwidth) + " MHz"
        l3 = " - Available bandwidth: " + str(self.FB_available_bandwidth) + " MHz"
        l4 = " - Assigned bandwidth: " + str(self.FB_assigned_bandwidth)
        l5 = " - Active fronthaul links: " + str(self.FB_links)

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/fronthaul_blocks/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/fronthaul_blocks/".
        """

        data_dump = dict()
        fb_data = dict()

        fb_data["max_bandwidth"] = self.__max_fronthaul_bandwidth
        fb_data["assigned_bandwidth"] = self.FB_assigned_bandwidth
        fb_data["available_bandwidth"] = self.FB_available_bandwidth
        fb_data["active_links"] = self.FB_links

        data_dump[time] = fb_data

        with open(file_path + self.FB_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def add_fronthaul_link(self, link_id: str, bandwidth_requirement: float, macro_id: str):
        """
            It adds a fronthaul link to a Base Station.

            :param link_id: identifier of the link to be added.
            :param bandwidth_requirement: bandwidth required for the link.
            :param macro_id: identifier of the macro base station that is to open the link.
        """

        # Calculate the assigned bandwidth
        if bandwidth_requirement > self.FB_available_bandwidth:
            bw = bandwidth_requirement

        else:

            bw = self.__max_fronthaul_bandwidth / len(self.FB_links) + 1

            try:
                self.__recalculate_link_bandwidth(bw)

            except InvalidNegativeValue as e:  # Catch exception if occurs (parameter "self.FB_available_bandwidth")
                print(e)
                sys.exit(1)

        self.FB_available_bandwidth -= bw

        if self.FB_available_bandwidth < 0:
            raise InvalidNegativeValue(self.FB_available_bandwidth)

        # Update attributes
        self.FB_links[macro_id] = link_id
        self.FB_assigned_bandwidth[link_id] = bw

    def remove_fronthaul_link(self, link_id: str, bandwidth_requirement: float):
        """
            It removes a fronthaul link from a base station.

            :param link_id: identifier of the link to be removed.
            :param bandwidth_requirement: bandwidth required for the link.
        """

        # Select the macro base station who has the link opened
        macro_bs_id = ""
        for current_bs in self.FB_links.keys():
            if self.FB_links[current_bs] == link_id:
                macro_bs_id = current_bs

        del self.FB_links[macro_bs_id]

        # Select the bandwidth that are assigned to the link
        bw = self.FB_assigned_bandwidth[link_id]
        self.FB_available_bandwidth += bw
        del self.FB_assigned_bandwidth[link_id]

        # Reallocate the bandwidth
        flag = False
        for current_link in self.FB_assigned_bandwidth.keys():

            if bandwidth_requirement > self.FB_assigned_bandwidth[current_link]:
                flag = True

        if flag:
            self.__recalculate_link_bandwidth(bandwidth_requirement)

    def __recalculate_link_bandwidth(self, bandwidth_per_link: float):
        """
            It recalculates the assigned bandwidth to the links.

            :param bandwidth_per_link: assigned bandwidth to the link.
        """

        # Reset the available bandwidth
        self.FB_available_bandwidth = self.__max_fronthaul_bandwidth

        # Reallocate the bandwidth in the active links
        for current_link in self.FB_links.values():
            self.FB_assigned_bandwidth[current_link] = bandwidth_per_link

            # Remove available bandwidth
            self.FB_available_bandwidth -= self.FB_assigned_bandwidth[current_link]

            if self.FB_available_bandwidth < 0:
                raise InvalidNegativeValue(self.FB_available_bandwidth)
