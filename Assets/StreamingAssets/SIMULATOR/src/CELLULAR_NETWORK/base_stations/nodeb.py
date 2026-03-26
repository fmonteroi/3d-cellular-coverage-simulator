# Class 'NodeB'
# Created 13/02/2020 (version 3.0)
# Modified 24/02/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *
import json
from SIMULATOR.src.MECHANISMS import bandwidth_allocation as alloc_bw
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound, UserOutOfBandwidth, LowPriorityUser
from SIMULATOR.src.MODELS.power_models import PowerModel
from SIMULATOR.src.MODELS.economic_models import EconomicModel


class NodeB:
    """
        It composes the base stations. It simulates the behaviour of the commutation central of a base station (nodeB in LTE).
        It collects the connected users to a base station and its connections.

        Attributes
        ----------
        - NODEB_id [str]: node identifier.
        - NODEB_economic_model [object (SIMULATOR.EconomicModel)]: economic cost model of the device. Used to calculate the total costs of the device.
        - NODEB_power_model [object (SIMULATOR.PowerModel)]: power consumption model of the device. Used to calculate the total consumed power of the device.
        - NODEB_users [dict]: identifier of the users connected to the BS and its priority.
        - NODEB_assigned_bandwidth [dict]: users connected to the base station and their allocated bandwidth.
        - NODEB_bandwidth_requirement [dict]: bandwidth requirements of users (which do not have to be equal to the allocated bandwidth).
        - NODEB_user_bandwidth [float]: bandwidth available to allocate to assigned users.
        - __total_user_bandwidth (private) [float]: total bandwidth available to allocate to assigned users.
        - __bandwidth_plannification (private) [str]: bandwidth allocation planning for users.
        - NODEB_active_connections [list of str]: identifier of the active connections in the BS.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - recalculate_assigned_bandwidth: it reallocates available bandwidth on a plannification basis when a user attempts to connect to the base station.
        - reallocate_bandwidth_when_user_disconnect: it recalculates the bandwidth available by the base station according to the connected users, after another user has disconnected.
        - get_total_bandwidth: returns the total bandwidth available for users.

    """

    NODEB_id: str = ""  # Example = "NODEB_1"
    NODEB_economic_model: EconomicModel = None
    NODEB_power_model: PowerModel = None
    NODEB_users: Dict[str, int] = dict()  # key = user id, value = user priority
    NODEB_assigned_bandwidth: Dict[str, float] = dict()  # key = user id, value = assigned bandwidth for this user in MHz
    NODEB_bandwidth_requirement: Dict[str, float] = dict()  # key = user id, value = bandwidth requirement in MHz
    NODEB_available_user_bandwidth: float = 0.0  # MHz
    __total_user_bandwidth: float = 0.0  # MHz
    __bandwidth_plannification: str = ""  # "discard" / "standard" / "priority"
    NODEB_active_connections: List[str] = []  # Example = ["CONN_1", "CONN_2"]
    
    def __init__(self, nodeb_id: str, economic_model: EconomicModel, power_model: PowerModel, total_user_bandwidth: float, bandwidth_plannification: str, active_connections: List[str] = None):
        """
            'Init' method of the class 'NodeB'.
            Constructor. Parametrized the object according to the entered parameters.

            :param nodeb_id: node identifier -> Example = "NODEB_1".
            :param economic_model: economic cost model of the device. Used to calculate the total costs of the device.
            :param power_model: power consumption model of the device. Used to calculate the total consumed power of the device.
            :param* active_connections: identifier of the active connections in the BS -> Example = ["CONN_1", "CONN_2"]. Defaults to "None".
        """

        self.NODEB_id = nodeb_id
        self.NODEB_economic_model = economic_model
        self.NODEB_power_model = power_model
        self.__total_user_bandwidth = total_user_bandwidth
        self.NODEB_available_user_bandwidth = self.__total_user_bandwidth
        self.__bandwidth_plannification = bandwidth_plannification
        self.NODEB_users = dict()
        self.NODEB_assigned_bandwidth = dict()
        self.NODEB_bandwidth_requirement = dict()
        self.NODEB_active_connections = [] if active_connections is None else active_connections

    def __str__(self):
        """
            'To-string' method of the class 'NodeB'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.NODEB_id
        l2 = " - Economic Model: None" if self.NODEB_economic_model is None else " - Economic Model: " + self.NODEB_economic_model.EM_id
        l3 = " - Power Model: None" if self.NODEB_power_model is None else " - Power Model: " + self.NODEB_power_model.PM_id
        l4 = " - Users connected: None" if len(self.NODEB_users.keys()) == 0 else " - Users connected: " + str(self.NODEB_users.keys())
        l5 = " - Active connections: None" if len(self.NODEB_active_connections) == 0 else " - Active connections: " + str(self.NODEB_active_connections)
        l6 = " - Total user bandwidth: " + str(self.__total_user_bandwidth) + " MHz"
        l7 = " - Available user bandwidth: " + str(self.NODEB_available_user_bandwidth) + " MHz"
        l8 = " - Assigned UE bandwidth: " + str(self.NODEB_assigned_bandwidth)
        l9 = " - UE bandwidth plannification: " + self.__bandwidth_plannification
        l10 = " - Bandwidth requirement: None" if len(self.NODEB_bandwidth_requirement.keys()) == 0 else " - Bandwidth requirement: " + str(self.NODEB_users)

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7 + "\n" + l8 + "\n" + l9 + "\n" + l10

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_network/base_stations/cells/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_network/base_stations/cells/".
        """

        data_dump = dict()
        nodeb_data = dict()

        nodeb_data["economic_model"] = "None" if self.NODEB_economic_model is None else self.NODEB_economic_model.EM_id
        nodeb_data["power_model"] = "None" if self.NODEB_power_model is None else self.NODEB_power_model.PM_id
        nodeb_data["connected_users"] = "None" if len(self.NODEB_users.keys()) == 0 else str(self.NODEB_users.keys())
        nodeb_data["assigned_bandwidth"] = self.NODEB_assigned_bandwidth
        nodeb_data["active_connections"] = "None" if len(self.NODEB_active_connections) == 0 else str(self.NODEB_active_connections)
        nodeb_data["available_user_bandwidth"] = self.NODEB_available_user_bandwidth
        nodeb_data["total_user_bandwidth"] = self.__total_user_bandwidth
        nodeb_data["bandwidth_plannification"] = self.__bandwidth_plannification
        nodeb_data["bandwidth_requirement"] = self.NODEB_bandwidth_requirement

        data_dump[time] = nodeb_data

        with open(file_path + self.NODEB_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def recalculate_assigned_bandwidth(self, user_id, requirement, priority):
        """
            It reallocates available bandwidth on a plannification basis when a user attempts to connect to the base station.

            :param user_id: candidate user identifier -> Example: "USER_1".
            :param requirement: bandwidth needed by the user (in MHz).
            :param priority: priority that the user has in the network according to its type (absolute units).

            :return [int or list of str]: user_correctly_connected: stores the success/failure status of the attempt to allocate bandwidth to the user.
                -> return str list ["user_1","user_2",...]: the user has correctly connected but "users_ids" users has been discarded from the base station.
                -> return -4: the user cannot connect because it would cause another user to be discarded.
                -> return -3: the user is unable to connect due to low priority.
                -> return -2: the user was discarded.
                -> return -1: the user cannot connect because he needs more bandwidth than the total bandwidth available by the base station.
                -> return 1: the user has correctly connected.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
            :except LowPriorityUser: occurs when the user does not have sufficient priority to connect to the base station according to the chosen plannification.
            :except UserOutOfBandwidth: occurs when another user has run out of available bandwidth due to the evaluated users connection.
        """

        # If the user bandwidth requirement is bigger than total bandwidth of the base station...
        if requirement > self.__total_user_bandwidth:
            user_correctly_connected = -1  # The user cannot connect because he needs more bandwidth than the total bandwidth available by the base station

        # If required bandwidth is available without the need to reallocate it...
        elif self.NODEB_available_user_bandwidth > requirement:
            self.NODEB_assigned_bandwidth[user_id] = requirement
            self.NODEB_available_user_bandwidth -= requirement
            user_correctly_connected = 1  # The user has correctly connected

        # If not have available bandwidth for the user
        else:

            try:

                if self.__bandwidth_plannification == "discard":
                    user_correctly_connected = -2  # The user was discarded

                elif self.__bandwidth_plannification == "standard":
                    self.NODEB_assigned_bandwidth = alloc_bw.standard_allocation(user_id, self.__total_user_bandwidth, self.NODEB_assigned_bandwidth.copy())
                    user_correctly_connected = 1  # The user has correctly connected

                elif self.__bandwidth_plannification == "simple_priority":
                    self.NODEB_assigned_bandwidth = alloc_bw.simple_priority_allocation(user_id, self.NODEB_available_user_bandwidth, priority, requirement, self.NODEB_users, self.NODEB_assigned_bandwidth.copy())
                    user_correctly_connected = 1  # The user has correctly connected

                elif self.__bandwidth_plannification == "partial_outweigh_priority":
                    self.NODEB_assigned_bandwidth = alloc_bw.partial_outweigh_priority_allocation(user_id, self.NODEB_available_user_bandwidth, priority, requirement, self.NODEB_users, self.NODEB_assigned_bandwidth.copy())
                    user_correctly_connected = 1  # The user has correctly connected

                elif self.__bandwidth_plannification == "total_outweigh_priority":
                    self.NODEB_assigned_bandwidth = alloc_bw.total_outweigh_priority_allocation(user_id, self.NODEB_available_user_bandwidth, priority, requirement, self.NODEB_users, self.NODEB_assigned_bandwidth.copy())
                    user_correctly_connected = 1  # The user has correctly connected

                elif self.__bandwidth_plannification == "discard_priority":
                    self.NODEB_assigned_bandwidth = alloc_bw.discard_priority_allocation(user_id, self.NODEB_available_user_bandwidth, priority, requirement, self.NODEB_users, self.NODEB_assigned_bandwidth.copy())
                    user_correctly_connected = 1  # The user has correctly connected

                else:
                    raise ConfigurationNotFound(self.__bandwidth_plannification)

                # Update the BS available bandwidth after the reallocation (apart from selected plannification)
                self.NODEB_available_user_bandwidth = self.__total_user_bandwidth - sum(self.NODEB_assigned_bandwidth.values())  # MHz

            except LowPriorityUser:  # catch an exception if the user does not have sufficient priority (compared to other users already connected) to carry out the selected plannification.
                user_correctly_connected = -3  # User is unable to connect due to low priority.

            except UserOutOfBandwidth as e2:  # catch an exception if a user has been dropped because it has run out of available bandwidth

                # If the plannification is a discard plannification, it returns the identifiers of the users that has been discarded.
                if self.__bandwidth_plannification == "discard_priority":
                    user_correctly_connected = e2.users_id
                    self.NODEB_assigned_bandwidth = e2.new_dict_allocated_bw_to_users

                else:  # Otherwise, the user cannot connect because it would cause another user to be discarded.
                    user_correctly_connected = -4

        return user_correctly_connected

    def reallocate_bandwidth_when_user_disconnect(self):
        """
            It recalculates the bandwidth available by the base station according to the connected users, after another user has disconnected.

            :raise ValueError: occurs when a value is not valid.
        """

        # Check if bandwidth is available for all users
        if sum(self.NODEB_bandwidth_requirement.values()) <= self.__total_user_bandwidth:  # If all users bandwidth requirements can be met...

            self.NODEB_available_user_bandwidth = self.__total_user_bandwidth

            for USER in self.NODEB_users.keys():
                self.NODEB_assigned_bandwidth[USER] = self.NODEB_bandwidth_requirement[USER]
                self.NODEB_available_user_bandwidth -= self.NODEB_assigned_bandwidth[USER]

                if self.NODEB_available_user_bandwidth < 0:  # raise an exception if there has been an error in execution and the available bandwidth remains negative
                    raise ValueError

        else:  # If they cannot be satisfied, it is necessary to recalculate according to plannification

            if self.__bandwidth_plannification == "discard" or self.__bandwidth_plannification == "standard":
                bw_per_user = self.NODEB_available_user_bandwidth / len(self.NODEB_users)
                for USER in self.NODEB_users.keys():
                    self.NODEB_assigned_bandwidth[USER] = self.NODEB_bandwidth_requirement[USER] if bw_per_user >= self.NODEB_bandwidth_requirement[USER] else bw_per_user
                    self.NODEB_available_user_bandwidth -= self.NODEB_assigned_bandwidth[USER]

            elif self.__bandwidth_plannification.endswith("priority"):
                sum_priorities = sum(self.NODEB_users.values())
                for USER in self.NODEB_users.keys():
                    current_weight = self.NODEB_users[USER] / sum_priorities
                    self.NODEB_assigned_bandwidth[USER] = self.NODEB_available_user_bandwidth * current_weight
                    self.NODEB_available_user_bandwidth -= self.NODEB_assigned_bandwidth[USER]

    def get_total_bandwidth(self):
        """
            Returns the total bandwidth available for users.

            :return [float] total_bandwidth: total bandwidth (in MHz).
        """

        return self.__total_user_bandwidth
