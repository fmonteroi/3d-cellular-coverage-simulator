# Class 'FronthaulNetwork'
# Created 13/02/2020 (version 3.0)
# Modified 15/05/2021 (version 6.0) - Jose Javier Rico Palomo

import networkx as nx
from typing import *
import sys
import json
import random
from SIMULATOR.src.LINKS.link import Link
import SIMULATOR.src.LINKS.link_generation as lg
from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import MacroBS, SmallBS
from SIMULATOR.src.ACCESS_NETWORK.network_device import Router
from SIMULATOR.src.MAP.simulation_map import SimulationMap
import SIMULATOR.src.ACCESS_NETWORK.fronthaul.fronthaul_topology as fronthaul_topology


class FronthaulNetwork:
    """
        Class FronthaulNetwork.
        Simulates the behaviour of an fronthaul network (connections between macro base stations and routers).

        Attributes
        ----------
        - FN_id [str]: fronthaul network identifier.
        - FN_links [dict of objects (SIMULATOR.Link)]: connections of the fronthaul network. Link between macro base stations and routers and its identifiers.
        - FN_graph [object (NetworkX.Graph)]: fronthaul network graph. The nodes will be the macro base stations and routers and the edges will be the links between them.
        - __topology (private) [str]: topology chosen to generate the fronthaul network.
        - __num_links (private) [int]: number of links that compose the fronthaul network.
        - __configuration (private) [str]: predefined configuration of the fronthaul network.
        - __link_technology (private) [str]: technology used for the links.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_fronthaul_network (private): it generates the connections of the fronthaul network (links between macro base stations and routers). It creates the graph, the topology and the link objects.
    """

    FN_id: str = ""  # Example = "FRONTHAUL_NETWORK_0"
    FN_links: Dict[str, Link] = dict()  # key link_id values key object
    FN_graph: nx.Graph = None
    __topology: str = ""  # "random" / "unique" / "complete_mesh"
    __num_links: int = 0
    __configuration: str = ""  # "CONFIGURATION_TEST" / "CONFIGURATION_ART1"
    __link_technology: str = ""  # "RF" / "FO" / "mixed"

    def __init__(self, fn_id: str, base_stations: Dict[str, Union[MacroBS, SmallBS]], routers: Dict[str, Router], link_parameters: dict, simulation_map: SimulationMap, configuration: str = "None", topology: str = "None", link_technology: str = "None"):
        """
            'Init' method of the class 'FronthaulNetwork'.
            Constructor. Parametrized the object according to the entered parameters.

            :param fn_id: fronthaul network identifier -> Example = "FRONTHAUL_NETWORK_0".
            :param base_stations: base stations generated for the simulation.
            :param routers: router generated for the simulation.
            :param link_parameters: parameters of the link depending of the chosen technology.
            :param* simulation_map: simulation map.
            :param* configuration: predefined configuration of the fronthaul network -> "CONFIGURATION_TEST" / "CONFIGURATION_ART1".
            :param* topology: topology chosen to generate the fronthaul network -> "random" / "unique" / "complete_mesh".
            :param* link_technology: technology used for the links -> "RF" / "FO" / "mixed".
        """

        self.FN_id = fn_id
        self.__configuration = configuration

        # * Add as many configurations as implemented in "fronthaul_topology"
        # if self.__configuration == "test":  # Add comment on the "fronthaul_topology" method
        # elif self.__configuration == "art1":  # Add comment on the "fronthaul_topology" method

        if self.__configuration == "None":  # No predefined configuration selected (check if conditional parameters are parametrized)

            # Check if conditional parameters have the default value
            if topology is FronthaulNetwork.__init__.__defaults__[1]:
                raise ConditionalParameterIsDefault("topology")

            if link_technology is FronthaulNetwork.__init__.__defaults__[2]:
                raise ConditionalParameterIsDefault("link_technology")

            # If all the conditional parameters are added by configuration, generate the network
            self.__topology = topology
            self.__link_technology = link_technology

            try:
                self.FN_graph, self.FN_links = self.__generate_fronthaul_network(base_stations, routers, link_parameters, simulation_map)

            except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "topology")
                print(e)
                sys.exit(2)

            self.__num_links = len(self.FN_links)

    def __str__(self):
        """
            'To-string' method of the class 'FronthaulNetwork'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.FN_id
        l2 = " - Predefined configuration: " + self.__configuration
        l3 = " - Topology: " + self.__topology
        l4 = " - Link technology: " + self.__link_technology
        l5 = " - Number of links: " + str(self.__num_links)
        l6 = " - Links: " + str([L for L in self.FN_links.keys()])

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/access_network/fronthaul_network/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the access network. Defaults to "/SIMULATOR/Results/access_network/fronthaul_network/".
        """

        data_dump = dict()
        fronthaul_network_data = dict()

        fronthaul_network_data["links"] = self.FN_links
        fronthaul_network_data["graph"] = self.FN_graph
        fronthaul_network_data["topology"] = self.__topology
        fronthaul_network_data["link_technology"] = self.__link_technology
        fronthaul_network_data["num_links"] = self.__num_links
        fronthaul_network_data["configuration"] = self.__configuration

        data_dump[time] = fronthaul_network_data

        with open(file_path+self.FN_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_fronthaul_network(self, base_stations: Dict[str, Union[MacroBS, SmallBS]], routers: Dict[str, Router], link_parameters: dict, simulation_map: SimulationMap):
        """
            It generates the connections of the fronthaul network (links between macro base stations and routers).
            It creates the graph, the topology and the link objects.

            :param base_stations: macro base stations generated for the simulation.
            :param routers: routers generated for the simulation.
            :param link_parameters: parameters of the link depending of the chosen technology.
            :param simulation_map: simulation map.

            :return [object (NetworkX.Graph)] graph: connections of the fronthaul network. Link between macro base stations and routers and its identifiers.
            :return [dict] links: fronthaul network graph. The nodes will be the macro base stations or routers and the edges will be the links between them.
        """

        graph = nx.Graph()
        links = dict()

        # Generate a graph only with nodes (macro base stations and routers without links)
        [graph.add_node(BS) for BS in base_stations.keys() if BS.startswith("MACRO")]  # Only macro BS
        [graph.add_node(R) for R in routers.keys()]

        # Generate the edges in function of topology
        # * Add as many topologies as implemented in "fronthaul_topology"
        if self.__topology == "random":
            graph = fronthaul_topology.random_topology(graph)

        elif self.__topology == "complete_mesh":
            graph = fronthaul_topology.complete_mesh_topology(graph)

        elif self.__topology == "unique":
            graph = fronthaul_topology.unique_topology(graph)

        # Generate the fronthaul network (links)
        i = 0
        for current_edge in graph.edges:

            device_source_id = graph.nodes[current_edge[0]]
            device_peer_id = graph.nodes[current_edge[1]]

            # Generate link
            technology = self.__link_technology if self.__link_technology != "random" else random.choice(["RF", "FO"])
            current_link = lg.generate_links("FRONTHAUL_LINK_"+str(i+1), base_stations[device_source_id] if device_source_id in base_stations.keys() else routers[device_source_id], base_stations[device_peer_id] if device_peer_id in base_stations.keys() else routers[device_peer_id], "fronthaul", technology, simulation_map=simulation_map, link_parameters=link_parameters)

            # Add link to the structures
            self.FN_links[current_link.LINK_id] = current_link  # fronthaul links
            current_edge["name_edge"] = current_link.LINK_id  # fronthaul graph
            base_stations[device_source_id].MBS_fronthaul_block.add_fronthaul_link(current_link.LINK_id) if device_source_id in base_stations.keys() else routers[device_source_id].ND_links_fh.append(current_link.LINK_id)
            base_stations[device_peer_id].MBS_fronthaul_block.add_fronthaul_link(current_link.LINK_id) if device_peer_id in base_stations.keys() else routers[device_peer_id].ND_links_fh.append(current_link.LINK_id)

            i += 1

        return graph, links
