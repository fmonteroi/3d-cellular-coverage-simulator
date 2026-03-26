# Class 'User', class 'StaticUser', class 'DynamicUser'
# Created 25/05/2018 (version 1.0)
# Modified 10/02/2021 (version 6.0) - Jose Javier Rico Palomo

import sys
from typing import *
from SIMULATOR.src.MOBILE_NODES.user_equipment import UserEquipment
from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
from SIMULATOR.src.EVENTS.mn_event import Step
from SIMULATOR.src.MODELS import mobility_models
from SIMULATOR.src.GEOMETRY import geometry_formulas as gf
import random as rd
import json


class User:
    """
        Abstract class NetworkDevice.
        Simulates the behaviour of a user inside an simulation scenario.
        The user can be Static or Dynamic.

        Attributes
        ----------
        - USER_id [str]: user identifier.
        - USER_position [tuple of floats]: current X and Y position of the users (related to the simulation scenario).
        - USER_ue [object (SIMULATOR.UserEquipment)]: mobile terminal of the user.
        - USER_priority [int]: priority that the user has in the network, depending on the traffic model or parameterization.
        - __traffic_model [str]: traffic model selected by parameter.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    USER_id: str = ""  # Example = "USER_1".
    USER_position: Tuple[float, float] = (0.0, 0.0)  # (x,y)
    USER_ue: UserEquipment = None
    USER_priority: int = 0  # absolute units
    __traffic_model: str = ""  # traffic model in "TRAFFIC/traffic_models.py" / "random"

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        network_device_data = dict()

        network_device_data["position"] = self.USER_position
        network_device_data["ue"] = self.USER_ue.UE_id
        network_device_data["priority"] = self.USER_priority
        network_device_data["traffic_model"] = self.__traffic_model

        return network_device_data

    def __str__(self):
        """
            'To-string' method of the abstract class 'User'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.USER_id
        l2 = " - Position: " + str(self.USER_position)
        l3 = " - User equipment: " + self.USER_ue.UE_id
        l4 = " - Priority: " + str(self.USER_priority)
        l5 = " - Traffic model: " + self.__traffic_model

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5


class StaticUser(User):
    """
        Subclass StaticUser. Inheritance of abstract class 'User'.
        It simulates the behaviour of a static receiver, which has the same functionalities as the dynamic receiver but cannot change its position.

        Attributes
        ----------
        - SUSER_type [str]: device characterization.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    SUSER_type: str = ""  # "sensor" / "smart home"

    def __init__(self, user_id: str, user_type: str, antenna_parameters: dict, sim_parameters: dict, traffic_parameters: dict, assigned_bandwidth: float, priority: int = 0, position: Tuple[float, float] = (0, 0), map_size: float = 0.0):
        """
            'Init' method of the subclass 'StaticUser'. Inheritance of abstract class 'User'.
            Constructor. Parametrized the object according to the entered parameters.

            :param user_id: user identifier -> Example: "USER_1".
            :param user_type: device characterization -> "sensor" / "smart home".
            :param antenna_parameters: configuration of the terminal antenna.
            :param sim_parameters: configuration of the terminal sim card.
            :param traffic_parameters: configuration of the traffic model.
            :param assigned_bandwidth: bandwidth allocated by the base station for the UE antenna link (in MHz).
            :param* priority: priority that the user has in the network, depending on the traffic model or parameterization (absolute units). Defaults to 0.
            :param* position: current X and Y position of the users (related to the simulation scenario -> (x,y). Defaults to (0,0).
            :param* map_size: size of the simulation map. Defaults to 0.

            :raise ConditionalParameterIsDefault: occurs when the conditional parameters have default values (if the default configuration is not configured).
        """

        self.USER_id = user_id  # Superclass attribute
        self.SUSER_type = user_type
        self.__traffic_model = traffic_parameters["model"]  # Superclass attribute
        self.USER_ue = UserEquipment("UE_1", antenna_parameters, sim_parameters, traffic_parameters, assigned_bandwidth, self.USER_id)  # Superclass attribute
        self.USER_priority = priority  # Superclass attribute

        if position is StaticUser.__init__.__defaults__[1]:

            if map_size is StaticUser.__init__.__defaults__[2]:
                raise ConditionalParameterIsDefault("map_size")
            else:  # Select a random position inside the simulation map margins
                self.USER_position = (rd.random()*map_size, rd.random()*map_size)

        else:
            self.USER_position = position  # Superclass attribute

    def __str__(self):
        """
            'To-string' method of the subclass 'StaticUser'. Inheritance of abstract class 'User'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - User type: " + self.SUSER_type

        return l1 + "\n" + l2

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the users. Defaults to "/SIMULATOR/Results/users/".
        """

        data_dump = dict()
        user_data = super().to_dict()

        user_data["user_type"] = self.SUSER_type

        data_dump[time] = user_data

        with open(file_path + self.USER_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class DynamicUser(User):
    """
        Subclass DynamicUser. Inheritance of abstract class 'User'.
        It simulates the behaviour of a dynamic receiver, which change its position according to a mobility model.

        Attributes
        ----------
        - DUSER_steps [list of objects (SIMULATOR.Step)]: steps generated by the user (events).
        - __mobility_parameters (private) [dict]: parameters of the mobility model used for generate Steps.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_mobility (private): it generates the movement (steps objects) that the user will follow through during the simulation.
    """

    DUSER_steps: List[Step] = []  # Example = [Step_1, Step_2]
    __mobility_parameters: dict = dict()  # ["model"], ["min_speed"], ["max_speed"], ["predefined_steps"], ["movement_time"], ["movement_height"]

    def __init__(self, user_id: str, mobility_parameters: dict, antenna_parameters: dict, sim_parameters: dict, traffic_parameters: dict, assigned_bandwidth: float, priority: int = 0):
        """
            'Init' method of the subclass 'DynamicUser'. Inheritance of abstract class 'User'.
            Constructor. Parametrized the object according to the entered parameters.

            :param user_id: user identifier -> Example: "USER_1".
            :param mobility_parameters: configuration of the mobility models.
            :param antenna_parameters: configuration of the terminal antenna.
            :param sim_parameters: configuration of the terminal sim card.
            :param traffic_parameters: configuration of the traffic model.
            :param assigned_bandwidth: bandwidth allocated by the base station for the UE antenna link (in MHz).
            :param priority: priority that the user has in the network, depending on the traffic model or parameterization (absolute units). Defaults to 0.

            :except ConfigurationNotFound: THE PROGRAM WILL EXIT IF 'CONFIGURATION NOT FOUND' EXCEPTIONS OCCURS (parameter "mobility_model").
        """

        self.USER_id = user_id  # Superclass attribute
        self.__traffic_model = traffic_parameters["model"]  # Superclass attribute
        self.__mobility_parameters = mobility_parameters
        self.USER_ue = UserEquipment("UE_1", antenna_parameters, sim_parameters, traffic_parameters, assigned_bandwidth, self.USER_id)  # Superclass attribute
        self.USER_priority = priority  # Superclass attribute

        try:
            self.DUSER_steps = self.__generate_mobility()

        except ConfigurationNotFound as e:  # Catch exception if occurs (parameter "mobility_model")
            print(e)
            sys.exit(2)

    def __str__(self):
        """
            'To-string' method of the subclass 'DynamicUser'. Inheritance of abstract class 'User'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Mobility model: " + self.__mobility_parameters["model"] if "model" in self.__mobility_parameters else " - Mobility model: None"

        steps_str = ""
        for i in range(0, len(self.DUSER_steps)):
            steps_str += self.DUSER_steps[i].EVENT_id + ", "
        l3 = " - Steps: " + steps_str

        return l1 + "\n" + l2 + "\n" + l3

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/users/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the users. Defaults to "/SIMULATOR/Results/users/".
        """

        data_dump = dict()
        user_data = super().to_dict()

        user_data["mobility_model"] = self.__mobility_parameters["model"] if "model" in self.__mobility_parameters else "None"

        if len(self.DUSER_steps) == 0:
            user_data["steps"] = "None"

        else:
            steps = dict()

            for i in range(0, len(self.DUSER_steps)):
                steps = steps[self.DUSER_steps[i].EVENT_id] = self.DUSER_steps[i].to_dict()

            user_data["steps"] = steps

        data_dump[time] = user_data

        with open(file_path + self.USER_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_mobility(self):
        """
            It generates the movement (steps objects) that the user will follow through during the simulation.

            :return [list of objects] user_steps: generated steps by dynamic user.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        user_steps = []
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
                    self.USER_position = first_position
                    first_step = Step("STEP_"+str(i-1), time, self.USER_id, first_position, first_step_info)
                    user_steps.append(first_step)
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

                        s = Step("STEP_" + str(i-1), time, self.USER_id, current_position, step_info)
                        user_steps.append(s)

                        last_position = current_position

                    else:
                        break

        else:

            current_step_time = 0

            steps_positions = self.__mobility_parameters["predefined_steps"]
            self.USER_position = steps_positions[0]

            for i in range(0, len(steps_positions)):

                step_info = dict()
                step_info["speed"] = self.__mobility_parameters["min_speed"] + (rd.random()*(self.__mobility_parameters["max_speed"]-self.__mobility_parameters["min_speed"]))
                step_info["distance"] = gf.euclidean_distance(steps_positions[i-1], steps_positions[i]) if i > 0 else 0
                step_info["consumed_time"] = step_info["distance"] / step_info["speed"]  # v = e / t -> t = e / v

                # current_step_time += step_info["consumed_time"]
                current_step_time = i

                current_step = Step("STEP_"+str(i+1), current_step_time, self.USER_id, steps_positions[i], step_info)
                user_steps.append(current_step)

        return user_steps
