# Class 'BackhaulNetwork'
# Created 20/04/2020 (version 4.0)
# Modified 14/04/2021 (version 6.0) - Jose Javier Rico Palomo

import networkx as nx
from typing import *
import SIMULATOR.src.CELLULAR_NETWORK.backhaul.backhaul_topology as backhaul_topology
from SIMULATOR.src.LINKS.link import Link
import SIMULATOR.src.LINKS.link_generation as lg
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound, ConditionalParameterIsDefault
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
from SIMULATOR.src.MAP.simulation_map import SimulationMap
import sys
import json
import random


class BackhaulNetwork:
    """
        Class BackhaulNetwork.
        Simulates the behaviour of an backhaul network (connections between base stations).

        Attributes
        ----------
        - BN_id [str]: backhaul network identifier.
        - BN_links [dict of objects (SIMULATOR.Link)]: connections of the backhaul network. Link between base stations and its identifiers.
        - BN_graph [object (NetworkX.Graph)]: backhaul network graph. The nodes will be the base stations and the edges will be the links between them.
        - __topology (private) [str]: topology chosen to generate the backhaul network.
        - __num_links (private) [int]: number of links that compose the backhaul network.
        - __configuration (private) [str]: predefined configuration of the backhaul network.
        - __link_technology (private) [str]: technology used for the links.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_backhaul_network (private): it generates the connections of the backhaul network (links between base stations). It creates the graph, the topology and the link objects.
    """

    BN_id: str = ""  # Example = "BACKHAUL_NETWORK_0"
    BN_links: Dict[str, Link] = dict()  # key link_id values key object
    BN_graph: nx.Graph = None
    __topology: str = ""  # "random" / "structured" / "complete_mesh"
    __num_links: int = 0
    __configuration: str = ""  # "CONFIGURATION_TEST" / "CONFIGURATION_ART1"
    __link_technology: str = ""  # "RF" / "FO" / "mixed"

    def __init__(self, bn_id: str, base_stations: Dict[str, BaseStation], link_parameters: dict, simulation_map: SimulationMap, configuration: str = "None", topology: str = "None", link_technology: str = "None"):
        """
            'Init' method of the class 'BackhaulNetwork'.
            Constructor. Parametrized the object according to the entered parameters.

            :param bn_id: backhaul network identifier -> Example = "BACKHAUL_NETWORK_0".
            :param base_stations: base stations generated for the simulation.
            :param link_parameters: parameters of the link depending of the chosen technology.
            :param* simulation_map: simulation map.
            :param* configuration: predefined configuration of the backhaul network -> "CONFIGURATION_TEST" / "CONFIGURATION_ART1".
            :param* topology: topology chosen to generate the backhaul network -> "random" / "structured" / "complete_mesh".
            :param* link_technology: technology used for the links -> "RF" / "FO" / "mixed".
        """

        self.BN_id = bn_id
        self.__configuration = configuration

        # * Add as many configurations as implemented in "backhaul_topology"
        # if self.__configuration == "test":  # Add comment on the "backhaul_topology" method
        # elif self.__configuration == "art1":  # Add comment on the "backhaul_topology" method

        if self.__configuration == "None":  # No predefined configuration selected (check if conditional parameters are parametrized)

            # Check if conditional parameters have the default value
            if topology is BackhaulNetwork.__init__.__defaults__[1]:
                raise ConditionalParameterIsDefault("topology")

            if link_technology is BackhaulNetwork.__init__.__defaults__[2]:
                raise ConditionalParameterIsDefault("link_technology")

            # If all the conditional parameters are added by configuration, generate the network
            self.__topology = topology
            self.__link_technology = link_technology

            try:
                self.BN_graph, self.BN_links = self.__generate_backhaul_network(base_stations, link_parameters, simulation_map)

            except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "topology")
                print(e)
                sys.exit(2)

            self.__num_links = len(self.BN_links)

    def __str__(self):
        """
            'To-string' method of the class 'BackhaulNetwork'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.BN_id
        l2 = " - Predefined configuration: " + self.__configuration
        l3 = " - Topology: " + self.__topology
        l4 = " - Link technology: " + self.__link_technology
        l5 = " - Number of links: " + str(self.__num_links)
        l6 = " - Links: " + str([L for L in self.BN_links.keys()])

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/backhaul_network/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the access network. Defaults to "/SIMULATOR/Results/cellular_network/backhaul_network/".
        """

        data_dump = dict()
        backhaul_network_data = dict()

        backhaul_network_data["links"] = self.BN_links
        backhaul_network_data["graph"] = self.BN_graph
        backhaul_network_data["topology"] = self.__topology
        backhaul_network_data["link_technology"] = self.__link_technology
        backhaul_network_data["num_links"] = self.__num_links
        backhaul_network_data["configuration"] = self.__configuration

        data_dump[time] = backhaul_network_data

        with open(file_path+self.BN_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_backhaul_network(self, base_stations: Dict[str, BaseStation], link_parameters: dict, simulation_map: SimulationMap):
        """
            It generates the connections of the backhaul network (links between base stations).
            It creates the graph, the topology and the link objects.

            :param base_stations: base stations generated for the simulation.
            :param link_parameters: parameters of the link depending of the chosen technology.
            :param simulation_map: simulation map.

            :return [object (NetworkX.Graph)] graph: connections of the backhaul network. Link between base stations and its identifiers.
            :return [dict] links: backhaul network graph. The nodes will be the base stations and the edges will be the links between them.
        """

        graph = nx.Graph()
        links = dict()

        # Generate a graph only with nodes (base stations without links)
        [graph.add_node(BS) for BS in base_stations.keys()]

        # Generate the edges in function of topology
        # * Add as many topologies as implemented in "backhaul_topology"
        if self.__topology == "random":
            graph = backhaul_topology.random_topology(graph)

        elif self.__topology == "complete_mesh":
            graph = backhaul_topology.complete_mesh_topology(graph)

        # Generate the backhaul network (links)
        i = 0
        for current_edge in graph.edges:

            device_source = current_edge[0]
            device_peer = current_edge[1]

            # Generate link
            base_stations[device_source].BS_backhaul_block.add_backhaul_link("BACKHAUL_LINK_"+str(i+1))
            base_stations[device_peer].BS_backhaul_block.add_backhaul_link("BACKHAUL_LINK_"+str(i+1))

            technology = self.__link_technology if self.__link_technology != "random" else random.choice(["RF", "FO"])
            current_link = lg.generate_links("BACKHAUL_LINK_"+str(i+1), base_stations[device_source], base_stations[device_peer], "backhaul", technology, simulation_map=simulation_map, link_parameters=link_parameters, base_stations=base_stations)

            # Add link to the structures
            links[current_link.LINK_id] = current_link  # Backhaul links
            graph.edges[current_edge[0], current_edge[1]]["name_edge"] = current_link.LINK_id  # Backhaul graph

            i += 1

        return graph, links
