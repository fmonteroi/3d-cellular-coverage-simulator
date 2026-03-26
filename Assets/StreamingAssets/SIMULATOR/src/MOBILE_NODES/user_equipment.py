# Class 'UserEquipment' class 'UE_Antenna', class 'UESim', class 'UeSimpleSim', class 'UeDualSim'
# Created 25/05/2018 (version 1.0)
# Modified 22/04/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.LINKS.rf_link import RFLink
from SIMULATOR.src.EVENTS.mn_event import MNConnectionStart, MNConnectionEnd
from SIMULATOR.src.TRAFFIC.connections import MNConnection
from SIMULATOR.src.TRAFFIC import traffic_generation as tg
from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
from typing import *
import json
import sys


class UEAntenna:
    """
        Class UEAntenna.
        It simulates the behaviour of an generic antenna located in a user equipment device. It is used for channel and radio link calculation.

        Attributes
        ----------
        - UEANTENNA_id [str]: UE antenna identifier.
        - UEANTENNA_height [float]: tilt of the UE antenna.
        - UEANTENNA_nrx [int]: number of mimo receiver antennas.
        - UEANTENNA_gain [float]: receiver antenna gain.
        - UEANTENNA_rx_power [float]: power of the receiver antenna.
        - UEANTENNA_bandwidth [float]: bandwidth allocated by the base station for the UE antenna link.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    UEANTENNA_id: str = ""  # Example: "UEANTENNA_1"
    UEANTENNA_height: float = 0.0  # m
    UEANTENNA_nrx: int = 0  # absolute units
    UEANTENNA_gain: float = 0.0  # dBi
    UEANTENNA_rx_power: float = 0.0  # dBm
    UEANTENNA_bandwidth: float = 0.0  # MHz

    def __init__(self, antenna_id: str, height: float, n_rx: int, gain: float, assigned_bandwidth: float):
        """
            'Init' method of the class 'UEAntenna'.
            Constructor. Parametrized the object according to the entered parameters.

            :param antenna_id: antenna identifier -> Example: "UEANTENNA_1".
            :param height: tilt of the UE antenna (in meters).
            :param n_rx: number of mimo receiver antennas.
            :param gain: receiver antenna gain (in dBi).
            :param assigned_bandwidth: bandwidth allocated by the base station for the UE antenna link (in MHz).
        """

        self.UEANTENNA_id = antenna_id
        self.UEANTENNA_height = height
        self.UEANTENNA_nrx = n_rx
        self.UEANTENNA_gain = gain
        self.UEANTENNA_bandwidth = assigned_bandwidth

    def __str__(self):
        """
            'To-string' method of the class 'UEAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.UEANTENNA_id
        l2 = " - Height: " + str(self.UEANTENNA_height) + " m"
        l3 = " - Number of receiver antennas: " + str(self.UEANTENNA_nrx)
        l4 = " - Gain: " + str(self.UEANTENNA_gain) + " dBi"
        l5 = " - RX power: " + str(self.UEANTENNA_rx_power) + "dBm"
        l6 = " - Assigned bandwidth: " + str(self.UEANTENNA_bandwidth) + " MHz"

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/user_equipments/ue_antennas/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the ue antennas. Defaults to "/SIMULATOR/Results/users/user_equipments/ue_antennas/".
        """

        data_dump = dict()
        ueantenna_data = dict()

        ueantenna_data["height"] = self.UEANTENNA_height
        ueantenna_data["nrx"] = self.UEANTENNA_nrx
        ueantenna_data["gain"] = self.UEANTENNA_gain
        ueantenna_data["rx_power"] = self.UEANTENNA_rx_power
        ueantenna_data["bandwidth"] = self.UEANTENNA_bandwidth

        data_dump[time] = ueantenna_data

        with open(file_path + self.UEANTENNA_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class UESim:
    """
        Abstract class UESim.
        It simulates the behaviour of a sim card of a mobile terminal.
        It stores the links that the user equipment has open with the base stations (one or several), depending on the type of multi connectivity selected.
        The SIM can be Simple or Dual.

        Attributes
        ----------
        - SIM_id [str]: sim identifier.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    SIM_id: str = ""  # Example: "SIM_1"

    def __str__(self):
        """
            'To-string' method of the class 'Sim'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.SIM_id

        return l1

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        sim_data = dict()

        sim_data["id"] = self.SIM_id

        return sim_data

    def get_bs_connected(self, link: str = "principal"):
        """
            Interface of bs connected function for UeSim.
            It returns the base station to which the UE is connected.

            :param* link: type of link to select -> "principal" / "secondary". Defaults to "principal".

            :return bs_connected: base station identifier to which the UE is connected. "empty" is no link are available.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        return "_"


class UeSimpleSim(UESim):
    """
        Subclass UeSimpleSim. Inheritance of abstract class 'UESim'.
        It simulates the behaviour of a single link SIM.

        Attributes
        ----------
        - SIM_link [object (SIMULATOR.RFLink)]: link between the user and the cellular network.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    SIM_link: RFLink = None

    def __init__(self, sim_id: str):
        """
            'Init' method of the class 'UeSimpleSim'. Inheritance of abstract class 'UeSim'.
            Constructor. Parametrized the object according to the entered parameters.

            :param sim_id: sim identifier.
        """

        self.SIM_id = sim_id  # superclass attribute
        # TODO: self.SIM_link = generate_link() #BaseStations, link_planification_parameters
        # TODO: exceptions control if configuration doesnt exist

    def __str__(self):
        """
            'To-string' method of the subclass 'UeSimpleSim'. Inheritance of abstract class 'UeSim'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - UE Link: " + self.SIM_link.LINK_id

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/user_equipments/ue_sims/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/users/user_equipments/ue_sims/".
        """

        data_dump = dict()
        sim_data = super().to_dict()

        sim_data["ue_link"] = self.SIM_link.to_dict()

        data_dump[time] = sim_data

        with open(file_path + self.SIM_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def get_bs_connected(self, link: str = "principal"):
        """
            Override interface method get_bs_connected for UeSim.
            Characterisation of bs connected for no multiconnectivity mode.

            :param* link: type of link to select -> "principal" / "secondary". Defaults to "principal".

            :return bs_connected: base station identifier to which the UE is connected. "empty" is no link are available.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        return self.SIM_link.LINK_peer if self.SIM_link is not None else "empty"


class UeDualSim(UESim):
    """
        Subclass UeDualSim. Inheritance of abstract class 'UESim'.
        It simulates the behaviour of a dual link SIM.

        Attributes
        ----------
        - SIM_principal_link [object (SIMULATOR.RFLink)]: principal link between the user and the cellular network.
        - SIM_secondary_link [object (SIMULATOR.RFLink)]: secondary link between the user and the cellular network.
        - __multiconnectivity_mode (private) [str]: multiconnectivity standard selected by parameter.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    SIM_principal_link: RFLink = None
    SIM_secondary_link: RFLink = None
    __multiconnectivity_mode: str = ""

    def __init__(self, sim_id: str, multiconnectivity_mode: str = "None"):
        """
            'Init' method of the class 'UeDualSim'. Inheritance of abstract class 'UeSim0.
            Constructor. Parametrized the object according to the entered parameters.

            :param sim_id: sim identifier.
            :param* multiconnectivity_mode: multiconnectivity standard selected. Defaults to "None".
        """

        self.SIM_id = sim_id  # superclass attribute
        self.__multiconnectivity_mode = multiconnectivity_mode
        # TODO: self.SIM_links = generate_links() #BaseStations, link_planification_parameters, multiconnectivity_parameters
        # TODO: exceptions control if configuration doesnt exist

    def __str__(self):
        """
            'To-string' method of the subclass 'UeDualSim'. Inheritance of abstract class 'UeSim'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Principal link: " + self.SIM_principal_link.LINK_id
        l3 = " - Secondary link: " + self.SIM_secondary_link.LINK_id
        l4 = " - Multiconnectivity planification: " + self.__multiconnectivity_mode

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/user_equipments/ue_sims/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/users/user_equipments/ue_sims/".
        """

        data_dump = dict()
        sim_data = super().to_dict()

        sim_data["principal_link"] = self.SIM_principal_link.to_dict()
        sim_data["secondary_link"] = self.SIM_secondary_link.to_dict()
        sim_data["multiconnectivity_mode"] = self.__multiconnectivity_mode

        data_dump[time] = sim_data

        with open(file_path + self.SIM_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def get_bs_connected(self, link: str = "principal"):
        """
            Override interface method get_bs_connected for UeSim.
            Characterisation of bs connected for multiconnectivity mode.

            :param* link: type of link to select -> "principal" / "secondary". Defaults to "principal".

            :return bs_connected: base station identifier to which the UE is connected. "empty" is no link are available.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        if link == "principal":
            return self.SIM_principal_link.LINK_peer if self.SIM_principal_link is not None else "empty"

        elif link == "secondary":
            return self.SIM_secondary_link.LINK_peer if self.SIM_secondary_link is not None else "empty"

        else:
            raise ConfigurationNotFound(link)


class UserEquipment:
    """
        Class 'UserEquipment'.
        it simulates the behaviour of a mobile terminal. Each user has one. It acts as a receiver of the radio links with base stations.

        Attributes
        ----------
        - UE_id [str]: user equipment identifier.
        - UE_antenna [object (SIMULATOR.UEAntenna)]: mobile terminal antenna (receiver).
        - UE_sim [object (SIMULATOR.UESim)]: sim card of the mobile terminal where the links are stored.
        - UE_connections_start [list of events (SIMULATOR.MNConnectionStart)]: connections started by the mobile terminal (events).
        - UE_connections_end [list of events (SIMULATOR.MNConnectionEnd)]: connections ended by the mobile terminal (events).

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    UE_id: str = ""  # Example: "UE_1"
    UE_antenna: UEAntenna = None
    UE_sim: Union[UeSimpleSim, UeDualSim] = None
    UE_connections_start: List[MNConnectionStart] = []  # Example = [ConnStart_1, ConnStart_2]
    UE_connections_end: List[MNConnectionEnd] = []  # Example = [ConnEnd_1, ConnEnd_2]

    def __init__(self, ue_id: str, antenna_parameters: dict, sim_parameters: dict, traffic_parameters: dict, assigned_bandwidth: float, user_id: str):
        """
            'Init' method of the class 'Sim'.
            Constructor. Parametrized the object according to the entered parameters.

            :param ue_id: UE identifier -> Example: "UE_1".
            :param antenna_parameters: configuration of the terminal antenna.
            :param sim_parameters: configuration of the terminal sim card.
            :param traffic_parameters: configuration of the traffic model.
            :param assigned_bandwidth: bandwidth allocated by the base station for the UE antenna link (in MHz).
            :param user_id: identifier of the user creating the UE -> Example: "USER_7".
        """

        self.UE_id = ue_id
        self.UE_antenna = UEAntenna("UEANTENNA_1", antenna_parameters["height"], antenna_parameters["n_rx"], antenna_parameters["gain"], assigned_bandwidth)

        if sim_parameters["type"] == "dual":
            self.UE_sim = UeDualSim("DUAL_SIM_1", multiconnectivity_mode=sim_parameters["multiconnectivity_mode"])

        else:
            self.UE_sim = UeSimpleSim("SIMPLE_SIM_1")

        self.UE_connections_start, self.UE_connections_end = self.__generate_connections(traffic_parameters, user_id)

    def __str__(self):
        """
            'To-string' method of the class 'UserEquipment'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.UE_id
        l2 = " - antenna: " + self.UE_antenna.UEANTENNA_id
        l3 = " - sim: " + self.UE_sim.SIM_id

        conn_start_ids = ""
        for i in range(0, len(self.UE_connections_start)):
            conn_start_ids += self.UE_connections_start[i].EVENT_id + ", "

        l4 = " - connections start: None" if len(self.UE_connections_start) == 0 else " - connections start: " + conn_start_ids

        conn_end_ids = ""
        for i in range(0, len(self.UE_connections_end)):
            conn_end_ids += self.UE_connections_end[i].EVENT_id + ", "

        l5 = " - connections end: None" if len(self.UE_connections_end) == 0 else " - connections end: " + conn_end_ids

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/user_equipments/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the ue. Defaults to "/SIMULATOR/Results/users/user_equipments/".
        """

        data_dump = dict()
        ue_data = dict()

        ue_data["antenna"] = self.UE_antenna.UEANTENNA_id
        ue_data["sim"] = self.UE_sim.SIM_id

        if len(self.UE_connections_start) == 0:
            ue_data["connections_start"] = "None"

        else:
            conn_start = dict()

            for i in range(0, len(self.UE_connections_start)):
                conn_start = conn_start[self.UE_connections_start[i].EVENT_id] = self.UE_connections_start[i].to_dict()

            ue_data["connections_start"] = conn_start

        if len(self.UE_connections_end) == 0:
            ue_data["connections_end"] = "None"

        else:
            conn_end = dict()

            for i in range(0, len(self.UE_connections_end)):
                conn_end = conn_end[self.UE_connections_end[i].EVENT_id] = self.UE_connections_end[i].to_dict()

            ue_data["connections_end"] = conn_end

        data_dump[time] = ue_data

        with open(file_path + self.UE_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_connections(self, traffic_parameters: dict, user_id: str):
        """
            It generates the connection started and ended events from the structure generated by the traffic models.

            :param traffic_parameters: configuration of the traffic model.
            :param user_id: identifier of the user creating the UE -> Example: "USER_7".

            :return [list of objects (SIMULATOR.MNConnStart)] connections_start: started connection events.
            :return [list of objects (SIMULATOR.MNConnEnd)] connections_end: ended connection events.

            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "traffic_model").
            :except ConditionalParameterIsDefault: THE PROGRAM WILL EXIT IF 'CONDITIONAL PARAMETER IS DEFAULT' EXCEPTIONS OCCURS.
        """

        connections_start = []
        connections_end = []

        traffic_model = traffic_parameters["model"]

        if traffic_model == "generic_demand":

            num_demands = traffic_parameters["num_demands"]
            min_time = traffic_parameters["min_time"]
            max_time = traffic_parameters["max_time"]
            simulation_time = traffic_parameters["simulation_time"]
            min_size = traffic_parameters["min_size"]
            max_size = traffic_parameters["max_size"]
            min_duration = traffic_parameters["min_duration"]
            max_duration = traffic_parameters["max_duration"]

            arrivals, sizes, durations = tg.generic_demand(num_demands, min_time, max_time, simulation_time, min_size, max_size, min_duration, max_duration)

        else:  # Traffic models

            try:
                time = traffic_parameters["time"]
                rate = traffic_parameters["rate"] if "rate" in traffic_parameters else 0
                min_size = traffic_parameters["min_size"] if "min_size" in traffic_parameters else 0
                max_size = traffic_parameters["max_size"] if "max_size" in traffic_parameters else 0
                min_duration = traffic_parameters["min_duration"] if "min_duration" in traffic_parameters else 0
                max_duration = traffic_parameters["max_duration"] if "max_duration" in traffic_parameters else 0
                time_between_packets = traffic_parameters["time_between_packets"] if "time_between_packets" in traffic_parameters else 0
                fps = traffic_parameters["fps"] if "fps" in traffic_parameters else 0

                arrivals, sizes, durations = tg.generate_traffic(traffic_model, time, rate=rate, min_size=min_size, max_size=max_size, min_duration=min_duration, max_duration=max_duration, time_between_packets=time_between_packets, fps=fps)

            except ConfigurationNotFound as e1:  # Catch exception if occurs (parameter "traffic_model")
                print(e1)
                sys.exit(2)

            except ConditionalParameterIsDefault as e2:  # Catch exception if occurs (default parameters)
                print(e2)
                sys.exit(2)

        for i in range(0, len(arrivals)):

            peer_id = self.UE_sim.SIM_id  # TODO: self.UE_sim.get_link().LINK_id
            current_connection = MNConnection("CONN_"+str(i+1), user_id, peer_id, traffic_model, sizes[i], durations[i], priority=5)

            current_connection_start = MNConnectionStart("STARTCONN_"+str(i+1), arrivals[i], user_id, current_connection)
            connections_start.append(current_connection_start)

            current_connection_end = MNConnectionEnd("ENDCONN_"+str(i+1), arrivals[i]+durations[i], user_id, current_connection_start.EVENT_id)
            connections_end.append(current_connection_end)

        return connections_start, connections_end
