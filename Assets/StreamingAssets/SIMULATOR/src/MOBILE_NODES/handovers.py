# Class 'Handover' (abstract), 'Lvl2Handover'
# Created 11/02/2021 (version 6.0)
# Modified 11/02/2021 (version 6.0) - Jose Javier Rico Palomo

import json
from typing import *


class Handover:
    """
        Abstract class Handover.
        It captures the handover process of a mobile node from one device to another.
        Handover can be level 2 (between base stations) or level 3 (between routers).

        Attributes
        ----------
        - HANDOVER_id [str]: handover identifier.
        - HANDOVER_time [float]: time instant at which handover occurs.
        - HANDOVER_user_id [str]: identifier of the user executing the handover.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    HANDOVER_id: str = ""  # Example = "HANDOVER_1"
    HANDOVER_time: float = 0.0  # s
    HANDOVER_user_id: str = ""  # Example = "USER_9"

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        handover_data = dict()

        handover_data["time"] = self.HANDOVER_time
        handover_data["user_id"] = self.HANDOVER_user_id

        return handover_data

    def __str__(self):
        """
            'To-string' method of the abstract class 'Handover'.
            Information for output by file or by screen of results.
        """

        l1 = " - id " + self.HANDOVER_id
        l2 = " - Time: " + str(self.HANDOVER_time) + " s"
        l3 = " - User: " + self.HANDOVER_user_id

        return l1+"\n"+l2+"\n"+l3


class HandoverLvl2(Handover):
    """
        Subclass HandoverLvl2. Inheritance of abstract class 'Handover'.
        It collects the handover process of a user between one cell and another (base station).

        Attributes
        ----------
        - HANDLVL2_new_bs_id [str]: base station identifier from which the user is to disconnect.
        - HANDLVL2_old_bs_id [str]: base station identifier to which the user is to connect to.
        - HANDLVL2_position [tuple of floats]: X and Y position at which the handover occurs.
        - __step_id [str]: step identifier triggering handover execution.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    HANDLVL2_new_bs_id: str = ""  # Example = "BS_4"
    HANDLVL2_old_bs_id: str = ""  # Example = "BS_7"
    HANDLVL2_position: Tuple[float, float] = (0.0, 0.0)  # (x,y)
    __step_id: str = ""  # Example = "STEP_4"

    def __init__(self, handover_id: str, time: float, user_id: str, old_bs: str, new_bs: str, position: Tuple[float, float], step_id: str):
        """
            'Init' method of the subclass 'HandoverLvL2'. Inheritance of abstract class 'Handover'.
            Constructor. Parametrized the object according to the entered parameters.

            :param handover_id: handover identifier -> Example = "HANDOVER_1".
            :param time: time instant at which handover occurs (in seconds).
            :param user_id: identifier of the user executing the handover -> Example = "USER_9".
            :param old_bs: base station identifier from which the user is to disconnect -> Example = "BS_4".
            :param new_bs: base station identifier to which the user is to connect to -> Example = "BS_7".
            :param position: X and Y position at which the handover occurs -> (x,y).
            :param step_id: step identifier triggering handover execution -> Example = "STEP_4".
        """

        self.HANDOVER_id = handover_id
        self.HANDOVER_time = time
        self.HANDOVER_user_id = user_id
        self.HANDLVL2_new_bs_id = new_bs
        self.HANDLVL2_old_bs_id = old_bs
        self.HANDLVL2_position = position
        self.__step_id = step_id

    def __str__(self):
        """
            'To-string' method of the subclass 'HandoverLvl2'. Inheritance of abstract class 'Handover'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Old BS: " + self.HANDLVL2_old_bs_id
        l3 = " - New BS: " + self.HANDLVL2_new_bs_id
        l4 = " - Position: " + str(self.HANDLVL2_position)
        l5 = " - Step id: " + self.__step_id

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/handovers/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/users/handovers/".
        """

        data_dump = dict()
        handover_data = super().to_dict()

        handover_data["new_bs"] = self.HANDLVL2_new_bs_id
        handover_data["old_bs"] = self.HANDLVL2_old_bs_id
        handover_data["position"] = str(self.HANDLVL2_position)
        handover_data["step"] = self.__step_id

        data_dump[time] = handover_data

        with open(file_path + "/" + self.HANDOVER_user_id + "/" + self.HANDOVER_id, 'a') as json_file:
            json.dump(data_dump, json_file)
