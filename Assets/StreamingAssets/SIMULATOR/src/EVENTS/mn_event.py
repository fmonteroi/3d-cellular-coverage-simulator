# Class 'MN_event' (abstract), 'Step', 'MN_Connection_start', 'MN_Connection_end'
# Created 04/10/2019 (version 2.0)
# Modified 09/02/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.EVENTS.event import Event
from SIMULATOR.src.TRAFFIC.connections import MNConnection
from typing import *
import json


class MNEvent(Event):
    """
        Abstract subclass MNEvent. Inheritance of abstract class 'Event'.
        Events that can only be performed by mobile nodes.
        The MN events can be Step, Connection_start and Connection_end.

        Attributes
        ----------
        - MNEVENT_user_id [str]: identifier of the user which execute this event.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    MNEVENT_user_id: str = ""  # Example: "USER_2"

    def __str__(self):
        """
            'To-string' method of the abstract subclass 'MNEvent'. Inheritance of abstract class 'Event'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = "  - User: " + self.MNEVENT_user_id

        return l1 + "\n" + l2

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        event_data = super().to_dict()

        event_data["user_id"] = self.MNEVENT_user_id

        return event_data


class Step(MNEvent):
    """
        Subclass Step. Inheritance of abstract class 'MNEvent'.
        The step is the minimum unit of user movement. The network updates its variables when a user takes a step.
        At each step, the signal-to-noise level, transmission power, power consumption, etc., will be different, as it will be in a different position and at a different distance from the base stations.

        Attributes
        ----------
        - STEP_position [tuple of floats]: X and Y position where the step ends.
        - STEP_info [dict]: information on the characteristics of the step.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    STEP_position: Tuple[float, float] = (0.0, 0.0)  # (x,y)
    STEP_info: dict = dict()  # ["speed"], ["distance"], ["consumed_time"]

    def __init__(self, event_id: str, event_time: float, user_id: str, position: Tuple[float, float], step_info: dict):
        """
            'Init' method of the subclass 'Step'. Inheritance of abstract class 'MNEvent'.
            Constructor. Parametrized the object according to the entered parameters.

            :param event_id: step identifier -> Example = "STEP_2".
            :param event_time: time instant at which event occurs (in seconds).
            :param user_id: identifier of the user which execute this event -> Example = "USER_2".
            :param position: X and Y position where the step ends -> (x,y).
            :param step_info: information on the characteristics of the step.
        """

        self.EVENT_id = event_id  # Super-super class attribute
        self.EVENT_time = event_time  # Super-super class attribute
        self.MNEVENT_user_id = user_id  # Superclass attribute
        self.STEP_position = position
        self.STEP_info = step_info

    def __str__(self):
        """
            'To-string' method of the class 'Step'. Inheritance of abstract class 'MNEvent'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Position: " + str(self.STEP_position)
        l3 = " - Current speed: " + str(self.STEP_info["speed"]) + " m/s"
        l4 = " - Traveled distance: " + str(self.STEP_info["distance"]) + " m"
        l5 = " - Consumed time: " + str(self.STEP_info["consumed_time"]) + " s"

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/events/steps/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the step events. Defaults to "/SIMULATOR/Results/events/steps/".
        """

        data_dump = dict()
        step_data = super().to_dict()

        step_data["position"] = self.STEP_position
        step_data["speed"] = self.STEP_info["speed"]
        step_data["distance"] = self.STEP_info["distance"]
        step_data["consumed_time"] = self.STEP_info["consumed_time"]

        data_dump[time] = step_data

        with open(file_path + self.EVENT_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class MNConnectionStart(MNEvent):
    """
        Subclass MNConnectionStart. Inheritance of abstract class 'MNEvent'.
        It simulates the start of a user connection. It must consume peer and link resources.

        Attributes
        ----------
        - MNCONNS_connection [object (SIMULATOR.MNConnection)]: connection that is about to start.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    MNCONNS_connection: MNConnection = None

    def __init__(self, event_id: str, event_time: float, user_id: str, connection: MNConnection):
        """
            'Init' method of the subclass 'MNConnectionStart'. Inheritance of abstract class 'MNEvent'.
            Constructor. Parametrized the object according to the entered parameters.

            :param event_id: started connection identifier -> Example = "STARTCONN_2".
            :param event_time: time instant at which event occurs (in seconds).
            :param user_id: identifier of the user which execute this event -> Example = "USER_2".
            :param connection: connection object that is about to start.
        """

        self.EVENT_id = event_id  # Super-super class attribute
        self.EVENT_time = event_time  # Super-super class attribute
        self.MNEVENT_user_id = user_id  # Superclass attribute
        self.MNCONNS_connection = connection

    def __str__(self):
        """
            'To-string' method of the class 'MNConnectionStart'. Inheritance of abstract class 'MNEvent'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Connection id: " + self.MNCONNS_connection.MNCONN_id

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/events/connection_start/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the connection start events. Defaults to "/SIMULATOR/Results/events/connection_start/".
        """

        data_dump = dict()
        connection_data = super().to_dict()

        connection_data["connection_id"] = self.MNCONNS_connection.MNCONN_id

        data_dump[time] = connection_data

        with open(file_path + "/" + self.MNEVENT_user_id + "/" + self.EVENT_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class MNConnectionEnd(MNEvent):
    """
        Subclass MNConnectionEnd. Inheritance of abstract class 'MNEvent'.
        It simulates the end of a user connection. It must release peer and link resources.

        Attributes
        ----------
        - MNCONNE_connection_star_id [str]: connection identifier that started and is going to be finalised.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    MNCONNE_connection_star_id: str = ""  # Example = "STARTCONN_4"

    def __init__(self, event_id: str, event_time: float, user_id: str, connection_start_id: str):
        """
            'Init' method of the subclass 'MNConnectionEnd'. Inheritance of abstract class 'MNEvent'.
            Constructor. Parametrized the object according to the entered parameters.

            :param event_id: ended connection identifier -> Example = "ENDCONN_2".
            :param event_time: time instant at which event occurs (in seconds).
            :param user_id: identifier of the user which execute this event -> Example = "USER_2".
            :param connection_start_id: connection identifier that started and is going to be finalised -> Example = "STARTCONN_4".
        """

        self.EVENT_id = event_id  # Super-super class attribute
        self.EVENT_time = event_time  # Super-super class attribute
        self.MNEVENT_user_id = user_id  # Superclass attribute
        self.MNCONNE_connection_star_id = connection_start_id

    def __str__(self):
        """
            'To-string' method of the class 'MNConnectionEnd'. Inheritance of abstract class 'MNEvent'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Started connection id: " + self.MNCONNE_connection_star_id

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/events/connection_end/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the connection end events. Defaults to "/SIMULATOR/Results/events/connection_end/".
        """

        data_dump = dict()
        connection_data = super().to_dict()

        connection_data["connection_start_id"] = self.MNCONNE_connection_star_id

        data_dump[time] = connection_data

        with open(file_path + "/" + self.MNEVENT_user_id + "/" + self.EVENT_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class ReconnectUser(MNEvent):
    """
        Subclass ReconnectUser. Inheritance of abstract class 'MNEvent'.
        It stores a users need for reconnection due to a disconnection from his base station.
        The reconnection request event is not generated at the beginning of the simulation to be sorted in the event vector.
        It is created on an as-needed basis during the course of the simulation to be added to the vector dynamically.

        Attributes
        ----------
        - RCONNU_old_bs [str]: identifier of the base station that has discarded the user.
        - RCONNU_reason [str]: reason why the user needs to reconnect to another base station.
        - __reconnect_plannification (private) [str]: planning for the reconnection of the users, chosen according to configuration.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    RCONNU_old_bs: str = ""  # Example = "BS_5"
    RCONNU_reason: str = ""  # "low_priority" / "bs_down"
    __reconnect_plannification: str = ""  # "standard" / "multiconnectivity" / "resource_pool" / "channel_estimation" / "dedicate_path"

    def __init__(self, event_id: str, event_time: float, user_id: str, old_bs: str, reason: str, reconnect_plannification: str):
        """
            'Init' method of the subclass 'ReconnectUser'. Inheritance of abstract class 'MNEvent'.
            Constructor. Parametrized the object according to the entered parameters.

            :param event_id: event identifier -> Example = "USERRECONNECT_2".
            :param event_time: time instant at which event occurs (in seconds).
            :param user_id: identifier of the user which execute this event -> Example = "USER_2".
            :param old_bs: identifier of the base station that has discarded the user -> Example = "BS_5".
            :param reason: reason why the user needs to reconnect to another base station -> "low_priority" / "bs_down".
            :param reconnect_plannification: planning for the reconnection of the users -> "standard" / "multiconnectivity" / "resource_pool" / "channel_estimation" / "dedicate_path".
        """

        self.EVENT_id = event_id  # Super-super class attribute
        self.EVENT_time = event_time  # Super-super class attribute
        self.MNEVENT_user_id = user_id  # Superclass attribute
        self.RCONNU_old_bs = old_bs
        self.RCONNU_reason = reason
        self.__reconnect_plannification = reconnect_plannification

    def __str__(self):
        """
            'To-string' method of the class 'ReconnectUser'. Inheritance of abstract class 'MNEvent'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Old BS: " + self.RCONNU_old_bs
        l3 = " - Reason: " + self.RCONNU_reason
        l4 = " - Reconnect plannification: " + self.__reconnect_plannification

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/events/reconnections/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the step events. Defaults to "/SIMULATOR/Results/events/steps/".
        """

        data_dump = dict()
        step_data = super().to_dict()

        step_data["old_bs"] = self.RCONNU_old_bs
        step_data["reason"] = self.RCONNU_reason
        step_data["reconnect_plannification"] = self.__reconnect_plannification

        data_dump[time] = step_data

        with open(file_path + self.EVENT_id, 'a') as json_file:
            json.dump(data_dump, json_file)
