# Class 'BaseStation' (abstract), class 'MacroBS', class 'SmallBS'
# Created 01/08/2019 (version 2.0)
# Modified 08/04/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *
import sys
import json
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.bs_antennas import BSAntenna, OmnidirectionalAntenna, DirectionalAntenna, TriSectorAntenna
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.cell import Cell
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.nodeb import NodeB
from SIMULATOR.src.CODE_UTILS.exceptions import AccessToDisableBS, ReconnectUserNeeded, ConfigurationNotFound
from SIMULATOR.src.EVENTS.mn_event import ReconnectUser
from SIMULATOR.src.EVENTS.bs_event import BsStep
from SIMULATOR.src.MODELS import mobility_models
from SIMULATOR.src.GEOMETRY import geometry_formulas as gf
from SIMULATOR.src.MODELS.power_models import PowerModel
from SIMULATOR.src.MODELS.economic_models import EconomicModel
from SIMULATOR.src.CELLULAR_NETWORK.backhaul.backhaul_block import BsBackhaulBlock
from SIMULATOR.src.ACCESS_NETWORK.fronthaul.fronthaul_block import BsFronthaulBlock
import random as rd


class BaseStation:
    """
        Abstract class BaseStations.
        It simulates the behaviour of a radio tower, to which users will connect to obtain service from the network.
        The base station can be Macro or Small.

        Attributes
        ----------
        - BS_id [str]: base station identifier.
        - BS_state [str]: stores the current status of the base station (whether it is off, on, or otherwise)
        - BS_position [tuple of floats]: current X and Y position of the base station (related to the simulation scenario).
        - BS_economic_model [object (SIMULATOR.EconomicModel)]: economic cost model of the device. Used to calculate the total costs of the device.
        - BS_power_model [object (SIMULATOR.PowerModel)]: power consumption model of the device. Used to calculate the total consumed power of the device.
        - BS_cell [object (SIMULATOR.Cell)]: coverage cell creating the base station.
        - BS_node [object (SIMULATOR.NodeB)]: base station node, in charge of computation and user management.
        - BS_antenna [object (SIMULATOR.BSAntenna)]: base station antenna that connects users.
        - BS_backhaul_block [object (SIMULATOR.BsBackhaulBlock)]: structure that stores the backhaul functionalities of the base station.
        - BS_sleep_time [float]: time in which the base station has been switched off.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    BS_id: str = ""  # Example = "BS_1"
    BS_state: str = "ON"  # "ON" / "OFF"
    BS_position: Tuple[float, float] = (0.0, 0.0)  # (x,y)
    BS_economic_model: EconomicModel = None
    BS_power_model: PowerModel = None
    BS_cell: Cell = None
    BS_node: NodeB = None
    BS_antenna: BSAntenna = None
    BS_backhaul_block: BsBackhaulBlock = None
    BS_sleep_time: float = 0.0  # s

    def __str__(self):
        """
            'To-string' method of the abstract class 'BaseStation'.
            Information for output by file or by screen of results.
        """

        l1 = " - id " + self.BS_id
        l2 = " - State: " + self.BS_state
        l3 = " - Position: " + str(self.BS_position)
        l4 = " - Economic Model: None" if self.BS_economic_model is None else " - Economic Model: " + self.BS_economic_model.EM_id
        l5 = " - Power Model: None" if self.BS_power_model is None else " - Power Model: " + self.BS_power_model.PM_id
        l6 = " - Cell: " + self.BS_cell.CELL_id
        l7 = " - Node: " + self.BS_node.NODEB_id
        l8 = " - Antenna: " + self.BS_antenna.ANTENNA_id
        l9 = " - Backhaul block: " + self.BS_backhaul_block.BB_id
        l10 = " - Sleep time: " + str(self.BS_sleep_time) + " seconds."

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7 + "\n" + l8 + "\n" + l9 + "\n" + l10

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        bs_data = dict()

        bs_data["state"] = self.BS_state
        bs_data["economic_model"] = "None" if self.BS_economic_model is None else self.BS_economic_model.EM_id
        bs_data["power_model"] = "None" if self.BS_power_model is None else self.BS_power_model.PM_id
        bs_data["cell"] = self.BS_cell.CELL_id
        bs_data["node"] = self.BS_node.NODEB_id
        bs_data["antenna"] = self.BS_antenna.ANTENNA_id
        bs_data["sleep_time"] = self.BS_sleep_time
        bs_data["backhaul_block"] = self.BS_backhaul_block.BB_id
        bs_data["backhaul_links"] = self.BS_backhaul_block.BB_links

        return bs_data

    def connect_user(self, user_id: str, priority: int, requirement: float, current_simulation_time: float, reconnect_plannification: str):
        """
            It adds a user to the base station, if applicable, reallocates bandwidth and updates the information.

            :param user_id: candidate user identifier -> Example: "USER_1".
            :param priority: priority that the user has in the network according to its type (absolute units).
            :param requirement: bandwidth needed by the user (in MHz).
            :param current_simulation_time: time at which the method is executed (in seconds).
            :param reconnect_plannification: planning for the reconnection of the users -> "standard" / "multiconnectivity" / "resource_pool" / "channel_estimation" / "dedicate_path".

            :return [float] assigned_bandwidth: bandwidth allocated to the user to be connected (in MHz). -1 if you have not been able to connect.

            :raise AccessToDisableBS: occurs when try to access to a disabled BS.
            :raise ReconnectUserNeeded: occurs when one or several users need to be reconnected to another BS.
            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "bandwidth_plannification").
        """

        assigned_bandwidth = -1

        # Check if BS is off
        if self.BS_state == "OFF":
            raise AccessToDisableBS(self.BS_id)

        # Check if user can be connected (depending on the bandwidth requirement) and recalculate bandwidth assignation if proceed
        try:
            user_correctly_connected = self.BS_node.recalculate_assigned_bandwidth(user_id, requirement, priority)

        except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "bandwidth_plannification")
            print(e)
            sys.exit(2)

        # Check the status code that recalculate bandwidth method returns
        if isinstance(user_correctly_connected, list):  # The user has correctly connected but "users_ids" users has been discarded from the base station
            reconnect_events = []
            for i in range(0, len(user_correctly_connected)):
                current_event = ReconnectUser("USERRECONNECT_"+str(i), current_simulation_time, user_id, self.BS_id, "low_priority", reconnect_plannification)
                reconnect_events.append(current_event)
            raise ReconnectUserNeeded(reconnect_events)

        elif isinstance(user_correctly_connected, int) and user_correctly_connected == -4:  # The user cannot connect because it would cause another user to be discarded
            assigned_bandwidth = -1

        elif isinstance(user_correctly_connected, int) and user_correctly_connected == -3:  # The user is unable to connect due to low priority
            assigned_bandwidth = -1

        elif isinstance(user_correctly_connected, int) and user_correctly_connected == -2:  # The user was discarded
            assigned_bandwidth = -1

        elif isinstance(user_correctly_connected, int) and user_correctly_connected == -1:  # The user cannot connect because he needs more bandwidth than the total bandwidth available by the base station
            assigned_bandwidth = -1

        elif isinstance(user_correctly_connected, int) and user_correctly_connected == 1:  # The user has correctly connected
            self.BS_node.NODEB_users[user_id] = priority  # Add user to BS node and recalculate its bandwidth
            self.BS_node.NODEB_bandwidth_requirement[user_id] = requirement
            assigned_bandwidth = self.BS_node.NODEB_assigned_bandwidth[user_id]

        return assigned_bandwidth

    def disconnect_user(self, user_id: str):
        """
            It removes a user from the base station and recalculates bandwidth for those who stay connected.

            :param user_id: candidate user identifier -> Example: "USER_1".

            :raise AccessToDisableBS: occurs when try to access to a disabled BS.
            :except ValueError: THE PROGRAM WILL EXIT IF 'VALUE ERROR' EXCEPTIONS OCCURS.
        """

        # Check if BS is off
        if self.BS_state == "OFF":
            raise AccessToDisableBS(self.BS_id)

        # Add allocated bandwidth to total available bandwidth
        self.BS_node.NODEB_available_user_bandwidth += self.BS_node.NODEB_assigned_bandwidth[user_id]

        # Remove user from the nodeb register
        del self.BS_node.NODEB_users[user_id]
        del self.BS_node.NODEB_bandwidth_requirement[user_id]
        del self.BS_node.NODEB_assigned_bandwidth[user_id]

        # Reallocate BS bandwidth
        try:

            if len(self.BS_node.NODEB_users) > 0:
                self.BS_node.reallocate_bandwidth_when_user_disconnect()

        except ValueError as e:  # Catch exception if occurs (value error)
            print(e)
            sys.exit(1)


class MacroBS(BaseStation):
    """
        Subclass MacroBS. Inheritance of abstract class 'BaseStation'.
        It simulates the behaviour of a Macro base station.

        Attributes
        ----------
        - MBS_fronthaul_block [object (SIMULATOR.BsBackhaulBlock: structure that stores the fronthaul functionalities of the macro base station.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    MBS_fronthaul_block: BsFronthaulBlock = None

    def __init__(self, bs_id: str, position: Tuple[float, float], economic_model: Union[None, EconomicModel], power_model: Union[None, PowerModel], nodeb_configuration: dict,  antenna_configuration: dict, backhaul_bandwidth: float, fronthaul_bandwidth: float, state: str = "ON", active_connections: List[str] = None):
        """
            'Init' method of the subclass 'MacroBS'. Inheritance of abstract class 'BaseStation'.
            Constructor. Parametrized the object according to the entered parameters.

            :param bs_id: base station identifier -> Example = "MACRO_BS_1".
            :param position: current X and Y position of the base station -> (x,y).
            :param economic_model: economic cost model of the device.
            :param power_model: power consumption model of the device.
            :param nodeb_configuration: configuration of the nodeb.
            :param antenna_configuration: configuration of the antenna.
            :param backhaul_bandwidth: bandwidth reserved for the backhaul portion of the base station (in MHz).
            :param fronthaul_bandwidth: bandwidth reserved for the fronthaul portion of the base station (in MHz).
            :param* state: stores the current status of the base station -> "ON" / "OFF". Defaults to "ON".
            :param* active_connections: identifier of the active connections in the BS -> Example = ["CONN_1", "CONN_2"]. Defaults to "None".

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        self.BS_id = bs_id  # Super-class attribute
        self.BS_state = state  # Super-class attribute
        self.BS_position = position  # Super-class attribute
        self.BS_economic_model = economic_model  # Super-class attribute
        self.BS_power_model = power_model  # Super-class attribute
        self.BS_cell = Cell("CELL_"+self.BS_id.split("_")[2], "MACRO")  # Super-class attribute

        nodeb_economic_model = nodeb_configuration["economic_model"]
        nodeb_power_model = nodeb_configuration["power_model"]
        nodeb_user_bandwidth = nodeb_configuration["total_user_bandwidth"]
        nodeb_bandwidth_plannification = nodeb_configuration["bandwidth_plannification"]
        self.BS_node = NodeB("NODEB_"+self.BS_id.split("_")[2], nodeb_economic_model, nodeb_power_model, nodeb_user_bandwidth, nodeb_bandwidth_plannification, active_connections=active_connections)  # Super-class attribute

        antenna_model = antenna_configuration["antenna_model"]
        antenna_economic_model = antenna_configuration["economic_model"]
        antenna_power_model = antenna_configuration["power_model"]
        antenna_height = antenna_configuration["height"]

        antenna_bandwidth = self.BS_node.NODEB_available_user_bandwidth

        if antenna_model == "omnidirectional":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "tx_power" in antenna_configuration:
                antenna_tx_power = antenna_configuration["tx_power"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "ntx" in antenna_configuration:
                antenna_ntx = antenna_configuration["ntx"]
            else:
                raise ConfigurationNotFound("antenna_ntx")

            if "gain" in antenna_configuration:
                antenna_gain = antenna_configuration["gain"]
            else:
                raise ConfigurationNotFound("antenna_gain")

            self.BS_antenna = OmnidirectionalAntenna("ANTENNA_"+self.BS_id.split("_")[2], "MACRO", antenna_economic_model, antenna_power_model, antenna_height, antenna_ntx, antenna_frequency, antenna_gain, antenna_tx_power, antenna_bandwidth)  # Super-class attribute

        elif antenna_model == "directional":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "azimuth" in antenna_configuration:
                antenna_azimuth = antenna_configuration["azimuth"]
            else:
                raise ConfigurationNotFound("antenna_azimuth")

            if "scanning_range_azimuth" in antenna_configuration:
                antenna_scanning_range_azimuth = antenna_configuration["scanning_range_azimuth"]
            else:
                raise ConfigurationNotFound("antenna_scanning_range_azimuth")

            if "tilt" in antenna_configuration:
                antenna_tilt = antenna_configuration["tilt"]
            else:
                raise ConfigurationNotFound("antenna_tilt")

            if "scanning_range_tilt" in antenna_configuration:
                antenna_scanning_range_tilt = antenna_configuration["scanning_range_tilt"]
            else:
                raise ConfigurationNotFound("antenna_scanning_range_tilt")

            if "subpanel_configuration" in antenna_configuration:
                antenna_subpanel_configuration = antenna_configuration["subpanel_configuration"]
            else:
                raise ConfigurationNotFound("antenna_subpanel_configuration")

            if "radiation_pattern_file" in antenna_configuration:
                antenna_radiation_pattern_file = antenna_configuration["radiation_pattern_file"]
            else:
                raise ConfigurationNotFound("antenna_radiation_pattern_file")

            self.BS_antenna = DirectionalAntenna("ANTENNA_"+self.BS_id.split("_")[2], "MACRO", antenna_economic_model, antenna_power_model, antenna_height, antenna_frequency, antenna_bandwidth, antenna_azimuth, antenna_scanning_range_azimuth, antenna_tilt, antenna_scanning_range_tilt, antenna_subpanel_configuration, antenna_radiation_pattern_file)  # Super-class attribute

        elif antenna_model == "trisector":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "subpanel_configuration" in antenna_configuration:
                antenna_subpanel_configuration = antenna_configuration["subpanel_configuration"]
            else:
                raise ConfigurationNotFound("antenna_subpanel_configuration")

            if "radiation_pattern_file" in antenna_configuration:
                antenna_radiation_pattern_file = antenna_configuration["radiation_pattern_file"]
            else:
                raise ConfigurationNotFound("antenna_radiation_pattern_file")

            self.BS_antenna = TriSectorAntenna("ANTENNA_"+self.BS_id.split("_")[2], "MACRO", antenna_economic_model, antenna_power_model, antenna_height, antenna_frequency, antenna_bandwidth, antenna_radiation_pattern_file, antenna_subpanel_configuration)

        else:
            raise ConfigurationNotFound("antenna_model")

        # * "AntennaRSS" init

        self.BS_backhaul_block = BsBackhaulBlock(self.BS_id, backhaul_bandwidth, antenna_configuration["backhaul_antennas_parameters"])
        self.MBS_fronthaul_block = BsFronthaulBlock(self.BS_id, fronthaul_bandwidth)

    def __str__(self):
        """
            'To-string' method of the subclass 'MacroBS'. Inheritance of abstract class 'BaseStation'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Fronthaul block: " + self.MBS_fronthaul_block.FB_id

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/".
        """

        data_dump = dict()
        bs_data = self.to_dict()

        bs_data["fronthaul_block"] = self.MBS_fronthaul_block.FB_id

        data_dump[time] = bs_data

        with open(file_path + self.BS_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class SmallBS(BaseStation):
    """
        Subclass SmallBS. Inheritance of abstract class 'BaseStation'.
        It simulates the behaviour of a Small base station (micro, pico or femto).

        Attributes
        ----------
        - SBS_type [str]: type of small base station.
        - SBS_steps [list of objects (SIMULATOR.Step)]: steps generated by the base station (events).
        - __mobility_parameters (private) [dict]: parameters of the mobility model used for generate BsSteps.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_mobility (private): it generates the movement (bs steps objects) that the small bs will follow through during the simulation.
    """

    SBS_type: str = ""  # "MICRO" / "PICO" / "FEMTO"
    SBS_steps: List[BsStep] = []  # Example = [BsStep_1, BsStep_2]
    __mobility_parameters: dict = dict()  # ["model"], ["min_speed"], ["max_speed"], ["predefined_steps"], ["movement_time"], ["movement_height"]

    def __init__(self, bs_id: str, bs_type: str, position: Tuple[float, float], economic_model: Union[None, EconomicModel], power_model: Union[None, PowerModel], nodeb_configuration: dict,  antenna_configuration: dict, backhaul_bandwidth: float, state: str = "ON", active_connections: List[str] = None, mobility_configuration: dict = None):
        """
            'Init' method of the subclass 'SmallBS'. Inheritance of abstract class 'BaseStation'.
            Constructor. Parametrized the object according to the entered parameters.

            :param bs_id: base station identifier -> Example = "MACRO_BS_1".
            :param bs_type: type of small base station -> "MICRO" / "PICO" / "FEMTO".
            :param position: current X and Y position of the base station -> (x,y).
            :param economic_model: economic cost model of the device.
            :param power_model: power consumption model of the device.
            :param nodeb_configuration: configuration of the nodeb.
            :param antenna_configuration: configuration of the antenna.
            :param backhaul_bandwidth: bandwidth reserved for the backhaul portion of the base station (in MHz).
            :param* state: stores the current status of the base station -> "ON" / "OFF". Defaults to "ON".
            :param* active_connections: identifier of the active connections in the BS -> Example = ["CONN_1", "CONN_2"]. Defaults to "None".
            :param* mobility_configuration: information on the characteristics of the step.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "mobility_model").
        """

        self.BS_id = bs_id  # Super-class attribute
        self.SBS_type = bs_type
        self.BS_state = state  # Super-class attribute
        self.BS_position = position  # Super-class attribute
        self.BS_economic_model = economic_model  # Super-class attribute
        self.BS_power_model = power_model
        self.BS_cell = Cell("CELL_"+self.BS_id.split("_")[2], "SMALL")  # Super-class attribute

        nodeb_economic_model = nodeb_configuration["economic_model"]
        nodeb_power_model = nodeb_configuration["power_model"]
        nodeb_user_bandwidth = nodeb_configuration["total_user_bandwidth"]
        nodeb_bandwidth_plannification = nodeb_configuration["bandwidth_plannification"]
        self.BS_node = NodeB("NODEB_"+self.BS_id.split("_")[2], nodeb_economic_model, nodeb_power_model, nodeb_user_bandwidth, nodeb_bandwidth_plannification, active_connections=active_connections)  # Super-class attribute

        antenna_model = antenna_configuration["antenna_model"]
        antenna_economic_model = antenna_configuration["economic_model"]
        antenna_power_model = antenna_configuration["power_model"]
        antenna_height = antenna_configuration["height"]

        antenna_bandwidth = self.BS_node.NODEB_available_user_bandwidth

        if antenna_model == "omnidirectional":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "tx_power" in antenna_configuration:
                antenna_tx_power = antenna_configuration["tx_power"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "ntx" in antenna_configuration:
                antenna_ntx = antenna_configuration["ntx"]
            else:
                raise ConfigurationNotFound("antenna_ntx")

            if "gain" in antenna_configuration:
                antenna_gain = antenna_configuration["gain"]
            else:
                raise ConfigurationNotFound("antenna_gain")

            self.BS_antenna = OmnidirectionalAntenna("ANTENNA_"+self.BS_id.split("_")[2], "SMALL", antenna_economic_model, antenna_power_model, antenna_height, antenna_ntx, antenna_frequency, antenna_gain, antenna_tx_power, antenna_bandwidth)  # Super-class attribute

        elif antenna_model == "directional":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "azimuth" in antenna_configuration:
                antenna_azimuth = antenna_configuration["azimuth"]
            else:
                raise ConfigurationNotFound("antenna_azimuth")

            if "scanning_range_azimuth" in antenna_configuration:
                antenna_scanning_range_azimuth = antenna_configuration["scanning_range_azimuth"]
            else:
                raise ConfigurationNotFound("antenna_scanning_range_azimuth")

            if "tilt" in antenna_configuration:
                antenna_tilt = antenna_configuration["tilt"]
            else:
                raise ConfigurationNotFound("antenna_tilt")

            if "scanning_range_tilt" in antenna_configuration:
                antenna_scanning_range_tilt = antenna_configuration["scanning_range_tilt"]
            else:
                raise ConfigurationNotFound("antenna_scanning_range_tilt")

            if "subpanel_configuration" in antenna_configuration:
                antenna_subpanel_configuration = antenna_configuration["subpanel_configuration"]
            else:
                raise ConfigurationNotFound("antenna_subpanel_configuration")

            if "radiation_pattern_file" in antenna_configuration:
                antenna_radiation_pattern_file = antenna_configuration["radiation_pattern_file"]
            else:
                raise ConfigurationNotFound("antenna_radiation_pattern_file")

            self.BS_antenna = DirectionalAntenna("ANTENNA_"+self.BS_id.split("_")[2], "SMALL", antenna_economic_model, antenna_power_model, antenna_height, antenna_frequency, antenna_bandwidth, antenna_azimuth, antenna_scanning_range_azimuth, antenna_tilt, antenna_scanning_range_tilt, antenna_subpanel_configuration, antenna_radiation_pattern_file)  # Super-class attribute

        elif antenna_model == "directional":

            if "frequency" in antenna_configuration:
                antenna_frequency = antenna_configuration["frequency"]
            else:
                raise ConfigurationNotFound("antenna_frequency")

            if "subpanel_configuration" in antenna_configuration:
                antenna_subpanel_configuration = antenna_configuration["subpanel_configuration"]
            else:
                raise ConfigurationNotFound("antenna_subpanel_configuration")

            if "radiation_pattern_file" in antenna_configuration:
                antenna_radiation_pattern_file = antenna_configuration["radiation_pattern_file"]
            else:
                raise ConfigurationNotFound("antenna_radiation_pattern_file")

            self.BS_antenna = TriSectorAntenna("ANTENNA_" + self.BS_id.split("_")[2], "SMALL", antenna_economic_model, antenna_power_model, antenna_height, antenna_frequency, antenna_bandwidth, antenna_radiation_pattern_file, antenna_subpanel_configuration)

        else:
            raise ConfigurationNotFound("antenna_model")

        # * add "AntennaRSS" init

        self.BS_backhaul_block = BsBackhaulBlock(self.BS_id, backhaul_bandwidth, antenna_configuration["backhaul_antennas_parameters"])

        if mobility_configuration is not SmallBS.__init__.__defaults__[2]:
            self.__mobility_parameters = mobility_configuration

            try:
                self.__generate_mobility()  # Generate steps

            except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "mobility_model")
                print(e)
                sys.exit(2)

    def __str__(self):
        """
            'To-string' method of the subclass 'SmallBS'. Inheritance of abstract class 'BaseStation'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Mobility model: " + self.__mobility_parameters["model"] if "model" in self.__mobility_parameters else " - Mobility model: None"

        steps_str = ""
        for i in range(0, len(self.SBS_steps)):
            steps_str += self.SBS_steps[i].EVENT_id + ", "
        l3 = " - Steps: " + steps_str

        return l1 + "\n" + l2 + "\n" + l3

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/".
        """

        data_dump = dict()
        bs_data = self.to_dict()

        bs_data["mobility_model"] = self.__mobility_parameters["model"] if "model" in self.__mobility_parameters else "None"

        if len(self.SBS_steps) == 0:
            bs_data["steps"] = "None"

        else:
            steps = dict()

            for i in range(0, len(self.SBS_steps)):
                steps = steps[self.SBS_steps[i].EVENT_id] = self.SBS_steps[i].to_dict()

            bs_data["steps"] = steps

        data_dump[time] = bs_data

        with open(file_path + self.BS_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_mobility(self):
        """
            It generates the movement (steps objects) that the base station will follow through during the simulation.

            :return [list of objects] bs_steps: generated steps by small bs.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        bs_steps = []
        movements = []  # list where the yield is stored

        # Check if step position are predefined by parameter (check if "predefined_step" key exist in mobility parameter dict)
        if self.__mobility_parameters.get("predefined_steps") is None:

            model = self.__mobility_parameters["model"]
            min_speed = self.__mobility_parameters["min_speed"]
            max_speed = self.__mobility_parameters["max_speed"]
            mean_speed = (min_speed + max_speed)/2
            movement_time = self.__mobility_parameters["movement_time"]
            movement_height = (self.__mobility_parameters["movement_height"], self.__mobility_parameters["movement_height"])

            time = 0
            current_speed = 0
            traveled_distance = 0
            consumed_time = 0
            last_position = (0, 0)

            if model == "RWP":
                mm = mobility_models.random_waypoint(1, dimensions=movement_height, velocity=(min_speed, max_speed), wt_max=1)

            elif model == "RW":
                mm = mobility_models.random_walk(1, dimensions=movement_height, velocity=mean_speed)

            elif model == "RD":
                mm = mobility_models.random_direction(1, dimensions=movement_height, velocity=(min_speed, max_speed), wt_max=1)

            elif model == "FF":
                mm = mobility_models.gauss_markov(1, dimensions=movement_height, velocity_mean=mean_speed, alpha=0.99)

            else:
                raise ConfigurationNotFound("mobility_model")

            i = 0
            for xy in mm:  # iter (yield)

                i = i + 1
                movements.append(xy)
                accumulative_time = time

                if i == 2:  # init position

                    first_step_info = dict()
                    first_step_info["speed"] = current_speed
                    first_step_info["distance"] = traveled_distance
                    first_step_info["consumed_time"] = consumed_time

                    first_position = (movements[0][0], movements[0][1]) if model == "FF" else (movements[0][0][0], movements[0][0][1])
                    self.BS_position = first_position
                    first_step = BsStep("STEP_"+str(i-1), time, self.BS_id, first_position, first_step_info)
                    bs_steps.append(first_step)
                    last_position = first_position

                elif i > 2:

                    if accumulative_time < movement_time:

                        # Calculate position (obtained by mobility model)
                        current_position = (movements[i - 1][0], movements[i - 1][1]) if model == "FF" else (movements[i - 1][0][0], movements[i - 1][0][1])

                        current_distance = gf.euclidean_distance(current_position, last_position)

                        # Calculate speed
                        if model == "RWP":
                            current_speed = movements[i - 1][1]  # obtained by mobility model

                        elif model == "RW" or model == "FF" or model == "RD":
                            current_speed = mean_speed

                        current_interval = current_distance / current_speed  # It calculates the consumed time -> speed = space / time
                        time = accumulative_time + current_interval  # It calculates the instant of time at which the event happens

                        step_info = dict()
                        step_info["speed"] = current_speed
                        step_info["distance"] = traveled_distance
                        step_info["consumed_time"] = consumed_time

                        s = BsStep("STEP_" + str(i-1), time, self.BS_id, current_position, step_info)
                        bs_steps.append(s)

                        last_position = current_position

                    else:
                        break

        else:

            current_step_time = 0

            steps_positions = self.__mobility_parameters["predefined_steps"]
            self.BS_position = steps_positions[0]

            for i in range(0, len(steps_positions)):

                step_info = dict()
                step_info["speed"] = self.__mobility_parameters["min_speed"] + (rd.random()*(self.__mobility_parameters["max_speed"]-self.__mobility_parameters["min_speed"]))
                step_info["distance"] = gf.euclidean_distance(steps_positions[i-1], steps_positions[i]) if i > 0 else 0
                step_info["consumed_time"] = step_info["distance"] / step_info["speed"]  # v = e / t -> t = e / v

                current_step_time += step_info["consumed_time"]

                current_step = BsStep("STEP_"+str(i+1), current_step_time, self.BS_id, steps_positions[i], step_info)
                bs_steps.append(current_step)

        return bs_steps
