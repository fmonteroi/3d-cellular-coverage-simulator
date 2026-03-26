# Module 'exceptions'
# Created 18/01/2021 (version 6.0)
# Modified 1/03/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *
from SIMULATOR.src.EVENTS.mn_event import ReconnectUser


class ConnectionDoesntExist(Exception):
    """ The connection to be deleted does not exist on the device """

    def __init__(self, connection_id: str):
        self.connection_id = connection_id

    def __str__(self):
        return "Connection doesnt exist (" + self.connection_id + ")"


class ConditionalParameterIsDefault(Exception):
    """ The conditional parameter should not be the default """

    def __init__(self, parameter: str):
        self.parameter = parameter

    def __str__(self):
        return "Conditional parameter is default (" + self.parameter + ")"


class ConfigurationNotFound(Exception):
    """ The introduced configuration is not implemented in the simulator """

    def __init__(self, configuration: str):
        self.configuration = configuration

    def __str__(self):
        return "Configuration not found (" + self.configuration + ")"


class InvalidNegativeValue(Exception):
    """ The value can not be a negative float or int """

    def __init__(self, value: float):
        self.value = value

    def __str__(self):
        return "Invalid negative value (" + str(self.value) + ")"


class AccessToDisableBS(Exception):
    """ The base station that it is trying to access is switched off. """

    def __init__(self, bs_id: str):
        self.bs_id = bs_id

    def __str__(self):
        return "BS switched off (" + self.bs_id + ")"


class UserOutOfBandwidth(Exception):
    """ A user (or list of users) is out of bandwidth when another user has connected to his base station. """

    def __init__(self, users_id: List[str], new_dict_allocated_bw_to_users: Dict[str, float] = None):
        self.users_id = users_id
        self.new_dict_allocated_bw_to_users = new_dict_allocated_bw_to_users

    def __str__(self):
        return "A user (or many) is out of bandwidth (" + str(self.users_id) + ")"


class LowPriorityUser(Exception):
    """ A user does not have sufficient priority (compared to other users already connected) to carry out the selected plannification. """

    def __init__(self, user_id: str):
        self.user_id = user_id

    def __str__(self):
        return "A user is out of bandwidth (" + self.user_id + ")"


class ReconnectUserNeeded(Exception):
    """ A user, or list of users, need to be reconnected to another BS """

    def __init__(self, events: List[ReconnectUser]):
        self.reconnect_events = events

    def __str__(self):
        aux_users_str = ""
        for i in range(0, len(self.reconnect_events)):
            aux_users_str += self.reconnect_events[i].MNEVENT_user_id + ", "
        return "the reconnection events for users " + aux_users_str + " have been triggered."


class ImpossibleToCreateFronthaulNetwork(Exception):
    """ Fronthaul network cannot create because exist an inconsistency between macro base station nodes and router nodes """

    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return "Impossible to create fronthaul network: " + self.reason
