# Class 'Link' (abstract)
# Created 03/03/2020 (version 3.0)
# Modified 02/02/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.CODE_UTILS.exceptions import ConnectionDoesntExist
from SIMULATOR.src.TRAFFIC.connections import MNConnection
from typing import *
import json


class Link:
    """
        Class Link.
        It simulates the behavior of a link between two devices without considering the propagation channel properties.
        Its a simple binary connection with a available resources (capacity).
        The link can be simple, microwave link or fiber optic link.

        Attributes
        ----------
        - LINK_id [str]: link identifier.
        - LINK_source [str]: origin device identifier of the link.
        - LINK_peer [str]: destination device identifier of the link.
        - LINK_active_connections [list of str]: identifier of the active connections in the link.
        - LINK_capacity [float]: available capacity on the link at every moment of time. Used to simulate incoming connections.
        - LINK_bandwidth [float]: assigned bandwidth to the link. Used to calculate the capacity and other properties.
        - LINK_BxD [float]: maximum amount of data on the network circuit at any given time. The product of a link capacity and its round-trip delay time.
        - LINK_type [str]: type of link depending on the network it is on.
        - __max_capacity (private) [float]: maximum capacity on the link at the time it was created.
        - __latency (private) [float]: link propagation latency only in uplink or downlink direction.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __add_capacity (private): add capacity available through the link.
        - __remove_capacity (private): remove available capacity through the link.
        - __check_block (private): checks whether the link is in a block situation under a specific demand.
        - add_connection: add, if the block doest exist, the incoming connection to the link, by subtracting capacity where proceed.
        - remove_connection: remove, if exist, the ended connection, freeing up capacity in the link.
        - generate_link (class method): it generates a link given the source and destination devices and some parameters.
    """

    LINK_id: str = ""  # Example = "LINK_1"
    LINK_source: str = ""  # Example = "UE_7"
    LINK_peer: str = ""  # Example = "BS_2"
    LINK_active_connections: List[str] = []  # Example = ["CONN_1", "CONN_2"]
    LINK_capacity: float = 0.0  # Mbps
    LINK_bandwidth: float = 0.0  # MHz
    LINK_BxD: float = 0.0  # Mb
    LINK_type: str = ""  # "ue" / "fronthaul" / "backhaul"
    __max_capacity: float = 0.0  # Mbps
    __latency: float = 0.0  # ms

    def __init__(self, link_id: str, source_id: str, peer_id: str, link_type: str, assigned_bandwidth: float, throughput: float = 0.0, capacity: float = 0.0, latency: float = 0.0, active_connections: List[str] = None):
        """
            'Init' method of the class 'Link'.
            Constructor. Parametrized the object according to the entered parameters.

            :param link_id: link identifier -> Example = "LINK_1".
            :param source_id: origin device identifier of the link -> Example = "UE_7".
            :param peer_id: destination device identifier of the link -> Example = "BS_2".
            :param link_type: type of link depending on the network it is on -> "ue" / "fronthaul" / "backhaul" / "layer3".
            :param assigned_bandwidth: assigned bandwidth to the link (in MHz).
            :param* throughput: capacity consumed by data passing through the link (in Mbps). Defaults to 0.
            :param* capacity: maximum capacity on the link at the time it was created (in Mbps). Defaults to 0.
            :param* latency: link propagation latency only in uplink or downlink direction (in ms). Defaults to 0.
            :param* active_connections: identifier of the active connections in the link -> Example = ["CONN_1", "CONN_2"]. Defaults to None.
        """

        self.LINK_id = link_id
        self.LINK_source = source_id
        self.LINK_peer = peer_id
        self.LINK_type = link_type
        self.__max_capacity = capacity
        self.LINK_bandwidth = assigned_bandwidth
        self.LINK_active_connections = [] if active_connections is None else active_connections
        self.LINK_capacity = self.__max_capacity
        self.__latency = latency
        self.LINK_BxD = Link.bandwidth_delay_product(self.__latency, self.LINK_capacity)
        self.LINK_throughput = throughput

    def __str__(self):
        """
            'To-string' method of the class 'Link'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.LINK_id
        l2 = " - Source device: " + self.LINK_source
        l3 = " - Peer device: " + self.LINK_peer
        l4 = " - Link type: " + self.LINK_type
        l5 = " - Assigned bandwidth: " + str(self.LINK_bandwidth) + " MHz."
        l6 = " - Maximum capacity: " + str(self.__max_capacity) + " Mbps."
        l7 = " - One-side latency: " + str(self.__latency) + " ms."

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        link_data = dict()

        link_data["id"] = self.LINK_id
        link_data["source"] = self.LINK_source
        link_data["peer"] = self.LINK_peer
        link_data["type"] = self.LINK_type
        link_data["assigned_bandwidth"] = self.LINK_bandwidth
        link_data["max_capacity"] = self.__max_capacity
        link_data["available_capacity"] = self.LINK_capacity
        link_data["active_connections"] = "None" if len(self.LINK_active_connections) == 0 else str(self.LINK_active_connections)
        link_data["latency"] = self.__latency
        link_data["BxD"] = self.LINK_BxD

        return link_data

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the links. Defaults to "/SIMULATOR/Results/".
        """

        sub_path = ""
        data_dump = dict()
        link_data = self.to_dict()

        data_dump[time] = link_data

        if self.LINK_type == "backhaul":
            sub_path = "/cellular_network/backhaul/links/"
        elif self.LINK_type == "fronthaul":
            sub_path = "/access_network/fronthaul/links/"
        elif self.LINK_type == "ue":
            sub_path = "/users/user_equipment/links/"
        elif self.LINK_type == "layer3":
            sub_path = "/access_network/links/"

        with open(file_path + sub_path + self.LINK_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __add_capacity(self, capacity: float):
        """
            Add capacity available through the link.
            If want to add more capacity than the maximum allowed (initial), only the maximum allowed (with which it is created) is added.
            If the maximum is not exceeded, they are added without restriction.

            :param capacity: amount of capacity to be added (in Mbps).
        """

        if self.LINK_capacity + capacity > self.__max_capacity:  # If want to add more capacity than the maximum allowed
            self.LINK_capacity = self.__max_capacity  # The maximum allowed (with which it is created) is added

        else:  # If the maximum is not exceeded, the resources are added.
            self.LINK_capacity = self.LINK_capacity + capacity

    def __remove_capacity(self, capacity: float):
        """
            Remove capacity resources through the link.
            It is necessary to check if block exist before remove the capacity (outside the method).

            :param capacity: amount of capacity to be removed (in Mbps).
        """

        if self.LINK_capacity - capacity >= 0:  # If demand can be met, it does so and remove capacity
            self.LINK_capacity = self.LINK_capacity - capacity

    def __check_block(self, capacity: float):
        """
            Checks whether the device is in a block situation under a specific demand (measured in capacity).
            If the device runs out of capacity to meet the demand, there is a block.

            :param capacity: amount of demand capacity (in Mbps).

            :return [boolean] block: router status (whether if has been blocked or not).
        """

        block = False

        if self.LINK_capacity - capacity < 0:  # If the available capacity reach zero, the link runs out of capacity to meet demands
            block = True

        return block

    def add_connection(self, connection: MNConnection):
        """
            Add, if the block doest exist, the incoming connection to the link, by subtracting capacity where proceed.
            If there are no capacity available, it warns that the connection will be blocked. The blocked must be checked when the method is called.

            :param connection: incoming connection to the device.

            :return [boolean] block: connection status (whether of not is has been ruled out due to lack of capacity).
        """

        block = False

        if self.__check_block(connection.MNCONN_demand) is True:  # Check if block exists
            block = True  # If block exist, block the connection

        else:  # If block doesnt exist, add the connection and remove resources from device
            self.__remove_capacity(connection.MNCONN_demand)
            self.LINK_active_connections.append(connection.MNCONN_id)

        return block

    def remove_connection(self, connection: MNConnection):
        """
            Remove, if exist, the ended connection, freeing up capacity in the link.
            If doest exist, return an exception (type 'SIMULATOR.ConnectionDoestExist').

            :param connection: ended connection.

            :raise ConnectionDoesntExist: occurs when the connection that are trying to remove doesnt exist.
        """

        # Check if the connection are active in the router
        if connection.MNCONN_id in self.LINK_active_connections:  # If exist, delete the connection from active_connections array and add capacity
            self.LINK_active_connections.remove(connection.MNCONN_id)
            self.__add_capacity(connection.MNCONN_demand)

        else:  # If doest exist, raise an exception
            raise ConnectionDoesntExist(connection.MNCONN_id)

    @classmethod
    def bandwidth_delay_product(cls, latency: float, capacity: float):
        """
            It calculates maximum amount of data on the network circuit at any given time.
            The bandwidth-delay product is the product of a data links capacity (in bits per second) and its round-trip delay time (in seconds).
            [REF] https://en.wikipedia.org/wiki/Bandwidth-delay_product

            :param latency: link propagation latency only in uplink or downlink direction (in ms).
            :param capacity: channel data rate (in Mbps).

            :return [float] bxd: bandwidth-delay product (in Mb).
        """

        latency_in_seconds = latency / 1000
        rtt = 2 * latency_in_seconds  # round-trip time
        bxd = rtt * capacity

        return bxd
