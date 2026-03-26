# Class 'BsEvent' (abstract), 'BsStep'
# Created 24/03/2020 (version 4.0)
# Modified 08/03/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.EVENTS.event import Event
from typing import *
import json


class BsEvent(Event):
    """
        Abstract subclass BsEvent. Inheritance of abstract class 'Event'.
        Events that can only be performed by base stations.
        The BS events can be BsStep.

        Attributes
        ----------
        - BSEVENT_bs_id [str]: identifier of the base station which execute this event.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    BSEVENT_bs_id = ""  # Example = "SMALL_BS_5"

    def __str__(self):
        """
            'To-string' method of the abstract subclass 'BsEvent'. Inheritance of abstract class 'Event'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = "  - Base Station: " + self.BSEVENT_bs_id

        return l1 + "\n" + l2

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        event_data = super().to_dict()

        event_data["bs_id"] = self.BSEVENT_bs_id

        return event_data


class BsStep(BsEvent):
    """
        Subclass BsStep. Inheritance of abstract class 'BsEvent'.
        The step is the minimum unit of user movement. The network updates its variables when a base station takes a step.
        At each step, the signal-to-noise level, transmission power, power consumption, etc., will be different, as it will be in a different position and at a different distance from the others base stations.

        Attributes
        ----------
        - BSSTEP_position [tuple of floats]: X and Y position where the step ends.
        - BSSTEP_info [dict]: information on the characteristics of the step.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    BSSTEP_position: Tuple[float, float] = (0.0, 0.0)  # (x,y)
    BSSTEP_info: dict = dict()  # ["speed"], ["distance"], ["consumed_time"]

    def __init__(self, event_id: str, event_time: float, bs_id: str, position: Tuple[float, float], step_info: dict):
        """
            'Init' method of the subclass 'BsStep'. Inheritance of abstract class 'BsEvent'.
            Constructor. Parametrized the object according to the entered parameters.

            :param event_id: step identifier -> Example = "BSSTEP_2".
            :param event_time: time instant at which event occurs (in seconds).
            :param bs_id: identifier of the base station which execute this event -> Example = "SMALL_BS_2".
            :param position: X and Y position where the step ends -> (x,y).
            :param step_info: information on the characteristics of the step.
        """

        self.EVENT_id = event_id  # Super-super class attribute
        self.EVENT_time = event_time  # Super-super class attribute
        self.BSEVENT_bs_id = bs_id  # Superclass attribute
        self.BSSTEP_position = position
        self.BSSTEP_info = step_info

    def __str__(self):
        """
            'To-string' method of the class 'BsStep'. Inheritance of abstract class 'BsEvent'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Position: " + str(self.BSSTEP_position)
        l3 = " - Current speed: " + str(self.BSSTEP_info["speed"]) + " m/s"
        l4 = " - Traveled distance: " + str(self.BSSTEP_info["distance"]) + " m"
        l5 = " - Consumed time: " + str(self.BSSTEP_info["consumed_time"]) + " s"

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/events/bs_steps/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the step events. Defaults to "/SIMULATOR/Results/events/bs_steps/".
        """

        data_dump = dict()
        step_data = super().to_dict()

        step_data["position"] = self.BSSTEP_position
        step_data["speed"] = self.BSSTEP_info["speed"]
        step_data["distance"] = self.BSSTEP_info["distance"]
        step_data["consumed_time"] = self.BSSTEP_info["consumed_time"]

        data_dump[time] = step_data

        with open(file_path + self.EVENT_id, 'a') as json_file:
            json.dump(data_dump, json_file)
