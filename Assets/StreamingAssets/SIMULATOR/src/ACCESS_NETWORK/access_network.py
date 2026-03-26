# Class 'AccessNetwork'
# Created 11/05/2020 (version 5.0)
# Modified 29/01/2020 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
from SIMULATOR.src.ACCESS_NETWORK.network_device import Router
import SIMULATOR.src.ACCESS_NETWORK.network_topology as nt
from SIMULATOR.src.LINKS.link import Link
import SIMULATOR.src.LINKS.link_generation as lg
import random as rd
import sys
import networkx
import json
from typing import *


class AccessNetwork:
    """
        Class AccessNetwork.
        Simulates the behaviour of an access network (layer-3 devices and its connections).
        Its composed for 'NetworkDevice' (Class Router).

        Attributes
        ----------
        - AN_id [str]: access network identifier.
        - AN_links [dict of objects (SIMULATOR.Link)]: connections of the access networks. Link between layer-3 devices and its identifiers.
        - AN_routers [dict of objects (SIMULATOR.Router)]: layer-3 devices that compose the access network.
        - AN_graph [object (NetworkX.Graph)]: access network graph. The nodes will be the layer-3 devices and the vertices will be the links between them.
        - __topology (private) [str]: topology chosen to generate the access network.
        - __num_routers (private) [int]: number of routers that compose the network.
        - __num_links (private) [int]: number of links that compose the network.
        - __configuration (private) [str]: predefined configuration of the access network.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_access_network (private): generates the router, the graph and the links of the access network if predefined configuration is not set.
    """

    AN_id: str = ""  # Example: "ACCESSNETWORK_1"
    AN_links: Dict[str, Link] = dict()  # key = link id, value = link object
    AN_routers: Dict[str, Router] = dict()  # key = router id, value = router object
    AN_graph: networkx.Graph = None
    __topology: str = ""  # "path" / "mesh_complete"
    __num_routers: int = 0
    __num_links: int = 0
    __configuration: str = ""  # "None" / "CONFIGURATION_TEST" / "CONFIGURATION_ART1"

    def __init__(self, an_id: str, an_configuration: str = "None", topology: str = "None", link_capacity: int = 0, router_parameters: dict = None):
        """
            'Init' method of the class 'AccessNetwork'.
            Constructor. Parametrized the object according to the entered parameters.

            :param an_id: access network identifier -> Example = "ACCESSNETWORK_0".
            :param* an_configuration: predefined configuration of the access network. Defaults to "None".
            :param* topology: topology chosen to generate the access network -> "path" / "mesh_complete". Defaults to "None".
            :param* link_capacity: capacity of the links between routers (in Mbps). Defaults to 0.
            :param* router_parameters: configuration to the routers for its generation. Defaults to None.

            :raise ConditionalParameterIsDefault: occurs when the conditional parameters have default values (if the default configuration is not configured).
            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "topology").
        """

        self.AN_id = an_id
        self.__configuration = an_configuration

        # * Add as many configurations as implemented in "network_topology"
        if self.__configuration == "test":
            self.AN_routers, self.AN_links, self.AN_graph = nt.configuration_test()
            self.__topology = "CONFIGURATION_TEST"

        elif self.__configuration == "art1":
            self.AN_routers, self.AN_links, self.AN_graph = nt.configuration_art1()
            self.__topology = "CONFIGURATION_ART1"

        elif self.__configuration == "None":  # No predefined configuration selected (check if conditional parameters are parametrized)

            # Check if conditional parameters have the default value
            if topology is AccessNetwork.__init__.__defaults__[1]:
                raise ConditionalParameterIsDefault("topology")

            if link_capacity is AccessNetwork.__init__.__defaults__[2]:
                raise ConditionalParameterIsDefault("link_capacity")

            if router_parameters is AccessNetwork.__init__.__defaults__[3]:
                raise ConditionalParameterIsDefault("router_parameters")

            # If all the conditional parameters are added by configuration, generate the network
            self.__topology = topology

            try:
                self.AN_graph, self.AN_routers, self.AN_links = self.__generate_access_network(router_parameters, link_capacity)

            except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "topology")
                print(e)
                sys.exit(2)

        self.__num_routers = len(self.AN_routers)
        self.__num_links = len(self.AN_links)

    def __str__(self):
        """
            'To-string' method of the class 'AccessNetwork'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.AN_id
        l2 = " - Predefined configuration: " + self.__configuration
        l3 = " - Topology: " + self.__topology
        l4 = " - Number of routers: " + str(self.__num_routers)
        l5 = " - Number of links: " + str(self.__num_links)
        l6 = " - Routers: " + str([R for R in self.AN_routers.keys()])
        l7 = " - Links: " + str([L for L in self.AN_links.keys()])

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6+"\n"+l7

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/access_network/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the access network. Defaults to "/SIMULATOR/Results/access_network/".
        """

        data_dump = dict()
        access_network_data = dict()

        access_network_data["links"] = self.AN_links
        access_network_data["routers"] = self.AN_routers
        access_network_data["graph"] = self.AN_graph
        access_network_data["topology"] = self.__topology
        access_network_data["num_routers"] = self.__num_routers
        access_network_data["num_links"] = self.__num_links
        access_network_data["configuration"] = self.__configuration

        data_dump[time] = access_network_data

        with open(file_path+self.AN_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_access_network(self, router_parameters: dict, link_capacity: int):
        """
            It generates the router according to the configuration entered.
            It generates the graph of the access network, as well as the connections between the routers.

            :param router_parameters: configuration to the routers for its generation.
            :param link_capacity: capacity of the links between routers (in Mbps).

            :return [object (NetworkX.Graph)] graph: access network graph. The nodes will be the layer-3 devices and the vertices will be the links between them.
            :return [dict of objects (SIMULATOR.Routers)] routers: layer-3 devices that compose the access network.
            :return [dict of objects (SIMULATOR.Link)] links: connections of the access networks. Link between layer-3 devices and its identifiers.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        routers = dict()
        network_links = dict()

        # Generate the routers
        for i in range(0, router_parameters["num_routers"]):
            current_resources = rd.randint(router_parameters["min_resources"], router_parameters["max_resources"])  # Calculate random resources (from min to max)
            current_router = Router("ROUTER_"+str(i+1), current_resources, router_parameters["economic_model"], router_parameters["power_model"])
            routers.update({current_router.ND_id: current_router})

        # Generate the network graph
        graph = nt.generate_access_network_graph(routers)

        # Generate the network topology
        # * Add as many topologies as implemented in "network_topology"
        if self.__topology == "path":
            graph = nt.linear_topology(graph)

        elif self.__topology == "mesh_complete":
            graph = nt.complete_mesh_topology(graph)

        else:
            raise ConfigurationNotFound(self.__topology)

        # Iterate the graph edges
        i = 0
        for E in graph.edges:

            device_source_id = graph.nodes[E[0]]["name_node"]
            device_peer_id = graph.nodes[E[1]]["name_node"]

            # Create the empty link
            try:
                link_parameters = dict({"capacity": link_capacity})
                link = lg.generate_links("AN_LINK_"+str(i+1), routers[device_source_id], routers[device_peer_id], "access_network", "EMPTY", link_parameters=link_parameters)

            except ConfigurationNotFound:
                print("The introduced configuration is not implemented in the simulator")
                sys.exit("Configuration error")

            # Add link to the network structure
            routers[device_source_id].ND_links_bh.append(link.LINK_id)  # Origin router
            routers[device_peer_id].ND_links_bh.append(link.LINK_id)  # Destination router
            network_links[link.LINK_id] = link  # access network links
            graph[E[0]][E[1]]["name_edge"] = link.LINK_id  # access network graph

            i += 1

        return graph, routers, network_links
