# Class 'SimulationMap'
# Created 14/03/2018 (version 1.0)
# Modified 29/01/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
import SIMULATOR.src.GEOMETRY.point_process as pp
import SIMULATOR.src.GEOMETRY.tessellations as tessellations
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
import SIMULATOR.src.MAP.predefined_scenarios as pred_scenario
import random
import json


class SimulationMap:
    """
        Class 'SimulationMap'.
        It models the behaviour of the simulation scenario.
        IT creates the scenario where all the elements of the simulation will be placed.
        It creates and distributes the propagation channel and generates the necessary points and tessellations for the cellular network.

         Attributes
        ----------
        - MAP_id [str]: simulation map identifier.
        - MAP_size [float]: size of one of the sides of the simulation map, taking into account square maps (in meters).
        - MAP_device_tessellation [dict of dicts]: tessellations of the cellular network.
        - MAP_channel_tesselation [dict of dicts]: tessellation of the propagation channels.
        - __device_tessellation_parameters (private) [dict of dicts]: parameters for the generation of the scenario points and tessellation process.
        - __channel_tessellation_parameters (private) [dict]: parameters of the point process which creates the tessellation of the propagation channel.
        - __configuration (private) [str]: predefined configuration of the simulation map.
        - __channel_voronoi_2d (private) [list]: structure returned by the generation of the voronoi diagram of the channels (its necessary to draw the regions).

        Methods
        -------
        - __init__: constructor. It parametrises the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __generate_map (private): it generates the simulation map, distributes the propagation channels and generates the necessary geometry (points and tessellations) for the generations of cells and base stations.
        - __ generate_channel_tessellation (private): it generates the geometry (points and tessellation) necessary for the generation of the different scenarios and propagation channels.
        - __distribute_propagation_channels (private): it distributes the scenarios available for the simulation according to probability and creates the channels.
        - get_channel_voronoi_2d: it returns the private attribute "channel_voronoi_2d".
    """

    MAP_id: str = ""  # Example: "MAP_1"
    MAP_size: float = 0.0  # m
    MAP_device_tessellation: dict = dict()  # ["macro"]["points"], ["small"]["points], ["macro"]["polygons"], ["small"]["polygons"]
    MAP_channel_tessellation: dict = dict()  # ["CHANNEL_1"]["point"], ["CHANNEL_1"]["polygon"], ["CHANNEL_1"][Channel], ["CHANNEL_2"]["point"], ["CHANNEL_2"]["polygon"], ["CHANNEL_2"][Channel], ...
    __device_tessellation_parameters: dict = dict()  # ["macro"/"small"] + ["tessellation"], ["pp"], ["alpha"], ["beta"], ["sigma/radius"], ["number_of_points"], ["hex_radius"]
    __channel_tessellation_parameters: dict = dict()  # ["pp"], ["alpha"], ["radius"], ["number_of_points"], ["distribution_method"], ["losses_model"]
    __configuration: str = ""  # "TEST" / "configuration_test_adp5g_scenario" / "jitel_2021" / "resource_management_paper"
    __channel_voronoi_2d: list = None  # [regions, vertices]

    def __init__(self, map_id: str, map_configuration="None", map_size: float = 0, bs_levels: int = 2, device_parameters: dict = None, channel_parameters: dict = None):
        """
            'Init' method of the class 'SimulationMap'.
            Constructor. It parametrises the object according to the entered parameters.

            :param map_id: simulation map identifier -> Example: "MAP_1".
            :param* map_configuration: predefined configuration of the simulation map -> "". Defaults to "None". # * Add possible configurations
            :param* map_size: size of one of the sides of the simulation map, taking into account square maps (in meters). Defaults to 0.
            :param* bs_levels: number of levels of the cellular networks (macro, small, micro, pico and femto). Defaults to 2 (macro and small).
            :param* device_parameters: parameters for the generation of the scenario points and tessellation process. Defaults to None.
            :param* channel_parameters: parameters of the point process which creates the tessellation of the propagation channel. Defaults to None.

            :raise ConditionalParameterIsDefault: occurs when the conditional parameters have default values (if the default configuration is not configured).
            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        self.MAP_id = map_id
        self.__configuration = map_configuration

        # * Add as many configurations as implemented in "predefined_maps"
        if self.__configuration == "configuration_test_adp5g_scenario":

            predefined_configuration = pred_scenario.configuration_test_adp5g_scenario()
            self.MAP_size = predefined_configuration["map_size"]
            self.MAP_device_tessellation = predefined_configuration["device_tessellation"]
            self.MAP_channel_tessellation = predefined_configuration["channel_tessellation"]
            self.__device_tessellation_parameters = predefined_configuration["device_parameters"]
            self.__channel_tessellation_parameters = predefined_configuration["channel_parameters"]
            self.__channel_voronoi_2d = predefined_configuration["channel_voronoi_2d"]

        elif self.__configuration == "TEST":

            predefined_configuration = pred_scenario.configuration_test()
            self.MAP_size = predefined_configuration["map_size"]
            self.MAP_device_tessellation = predefined_configuration["device_tessellation"]
            self.MAP_channel_tessellation = predefined_configuration["channel_tessellation"]
            self.__device_tessellation_parameters = predefined_configuration["device_parameters"]
            self.__channel_tessellation_parameters = predefined_configuration["channel_parameters"]
            self.__channel_voronoi_2d = predefined_configuration["channel_voronoi_2d"]

        elif self.__configuration == "jitel_2021":

            predefined_configuration = pred_scenario.configuration_jitel_2021()
            self.MAP_size = predefined_configuration["map_size"]
            self.MAP_device_tessellation = predefined_configuration["device_tessellation"]
            self.MAP_channel_tessellation = predefined_configuration["channel_tessellation"]
            self.__device_tessellation_parameters = predefined_configuration["device_parameters"]
            self.__channel_tessellation_parameters = predefined_configuration["channel_parameters"]
            self.__channel_voronoi_2d = predefined_configuration["channel_voronoi_2d"]

        elif self.__configuration == "resource_management_paper":

            predefined_configuration = pred_scenario.configuration_resource_management_paper()
            self.MAP_size = predefined_configuration["map_size"]
            self.MAP_device_tessellation = predefined_configuration["device_tessellation"]
            self.MAP_channel_tessellation = predefined_configuration["channel_tessellation"]
            self.__device_tessellation_parameters = predefined_configuration["device_parameters"]
            self.__channel_tessellation_parameters = predefined_configuration["channel_parameters"]
            self.__channel_voronoi_2d = predefined_configuration["channel_voronoi_2d"]

        elif self.__configuration == "None":  # No predefined configuration selected (check if conditional parameters are parametrized before generating the scenario)

            # Check if conditional parameters have the default value (if not, raise an exception)
            if map_size is SimulationMap.__init__.__defaults__[1]:  # Conditional argument in the position 1
                raise ConditionalParameterIsDefault("map_size")

            if device_parameters is SimulationMap.__init__.__defaults__[2]:  # Conditional argument in the position 2
                raise ConditionalParameterIsDefault("device_parameters")

            if channel_parameters is SimulationMap.__init__.__defaults__[3]:  # Conditional argument in the position 3
                raise ConditionalParameterIsDefault("channel_parameters")

            # If all the conditional parameters are added by configuration, generate the map
            self.MAP_size = map_size
            self.__device_tessellation_parameters = device_parameters
            self.__channel_tessellation_parameters = channel_parameters

            self.MAP_channel_tessellation, self.MAP_device_tessellation = self.__generate_map(bs_levels)

        else:  # If configuration entered by parameters is not implemented in the simulator, raise an exception.
            raise ConfigurationNotFound(self.__configuration)

    def __str__(self):
        """
            'To-string' method of the class 'SimulationMap'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.MAP_id
        l2 = " - Predefined configuration: " + self.__configuration
        l3 = " - Size: " + str(self.MAP_size)

        return l1+"\n"+l2+"\n"+l3

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/simulation_map/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the simulation_map. Defaults to "/SIMULATOR/Results/simulation_map/".
        """

        data_dump = dict()
        simulation_map_data = dict()

        simulation_map_data["size"] = self.MAP_size
        simulation_map_data["device_tessellation_parameters"] = self.__device_tessellation_parameters
        simulation_map_data["channel_tessellation_parameters"] = self.__channel_tessellation_parameters
        simulation_map_data["configuration"] = self.__configuration
        simulation_map_data["device_tessellation"] = self.MAP_device_tessellation
        simulation_map_data["channel_tessellation"] = self.MAP_channel_tessellation

        data_dump[time] = simulation_map_data

        with open(file_path+self.MAP_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __generate_map(self, bs_levels: int):
        """
            It generates the simulation map, distributes the propagation channels and generates the necessary geometry (points and tessellations) for the generations of cells and base stations.

            :param bs_levels: number of levels of the cellular networks (macro, small, micro, pico and femto).

            :return [dict] channel_tessellation: structured tessellation of propagation channels across the simulation map.
            :return [dict] device_tessellations: structured tessellation of different levels of cells.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        device_tessellation = dict()

        # It generates the channel tessellation and creates the propagation channels
        channel_tesselation = self.__generate_channel_tessellation()

        # Generate points and tessellations of base stations (depending on the number of levels)

        if bs_levels == 2:  # MACRO AND SMALL CELLS

            macro_tessellations = self.__device_tessellation_parameters["macro"]
            small_tessellations = self.__device_tessellation_parameters["small"]

            if macro_tessellations["tessellation"] == "voronoi" and small_tessellations["tessellation"] == "voronoi":

                if macro_tessellations["pp"] == "MPP" or macro_tessellations["pp"] == "TPP":
                    generated_points = pp.point_process(macro_tessellations["pp"], self.MAP_size, alpha=macro_tessellations["alpha"], beta=macro_tessellations["beta"], sigma=macro_tessellations["sigma/radius"], number_of_points=macro_tessellations["number_of_points"])
                    macro_points = [generated_points[0]]
                    small_points = [generated_points[1]]

                else:
                    macro_points = pp.point_process(macro_tessellations["pp"], self.MAP_size, alpha=macro_tessellations["alpha"], beta=macro_tessellations["beta"], sigma=macro_tessellations["sigma/radius"], number_of_points=macro_tessellations["number_of_points"])
                    small_points = pp.point_process(small_tessellations["pp"], self.MAP_size, alpha=small_tessellations["alpha"], beta=small_tessellations["beta"], sigma=small_tessellations["sigma/radius"], number_of_points=small_tessellations["number_of_points"])

                macro_polygons = tessellations.generate_tessellations(macro_tessellations["tessellation"], points=macro_points)
                small_polygons = tessellations.generate_tessellations(small_tessellations["tessellation"], points=small_points)

            elif macro_tessellations["tessellation"] == "hexagonal" and small_tessellations["tessellation"] == "voronoi":
                macro_points, small_points, macro_polygons, small_polygons = tessellations.hexagon_voronoi(macro_tessellations["hex_radius"], self.MAP_size, small_tessellations["sigma/radius"], alpha=small_tessellations["alpha"], points_per_hexagon=small_tessellations["number_of_points"])
                macro_points = [macro_points]
                small_points = [small_points]

            elif macro_tessellations["tessellation"] == "hexagonal" and small_tessellations["tessellations"] == "hexagonal":
                macro_points, macro_polygons = tessellations.generate_tessellations(macro_tessellations["tessellation"], size=self.MAP_size, hexagon_radius=macro_tessellations["hex_radius"])
                small_points, small_polygons = tessellations.generate_tessellations(small_tessellations["tessellation"], size=self.MAP_size, hexagon_radius=small_tessellations["hex_radius"])

            else:
                raise ConfigurationNotFound("tessellations")

            macro_device_tesselation = dict()
            macro_device_tesselation["points"] = macro_points
            macro_device_tesselation["polygons"] = macro_polygons
            device_tessellation["macro"] = macro_device_tesselation

            small_device_tessellation = dict()
            small_device_tessellation["points"] = small_points
            small_device_tessellation["polygons"] = small_polygons
            device_tessellation["small"] = small_device_tessellation

        return channel_tesselation, device_tessellation

    def __generate_channel_tessellation(self):
        """
            It generates the geometry (points and tessellation) necessary for the generation of the different scenarios and propagation channels.

            :return [dict] channel_tessellation: structured tessellation of propagation channels across the simulation map.

            :raise ValueError: occurs when entered value is not correct.
            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        # It generates point for channels
        if self.__channel_tessellation_parameters["pp"] == "CR" or self.__channel_tessellation_parameters["pp"] == "PPP" or self.__channel_tessellation_parameters["pp"] == "BPP" or self.__channel_tessellation_parameters["pp"] == "HCPP":
            channel_points = pp.point_process(self.__channel_tessellation_parameters["pp"], self.MAP_size, alpha=self.__channel_tessellation_parameters["alpha"], sigma=self.__channel_tessellation_parameters["radius"], number_of_points=self.__channel_tessellation_parameters["number_of_points"])
        else:
            raise ConfigurationNotFound(self.__channel_tessellation_parameters["pp"])

        # If channel_points are a two-position array, it means that the point process used for generate the channel points is not valid
        if len(channel_points) > 1:
            raise ValueError

        channel_points = channel_points[0]

        # Channel tessellations
        voronoi_diagram, self.__channel_voronoi_2d = tessellations.generate_tessellations("finite_voronoi", points=channel_points, size=self.MAP_size)

        # Distributing propagation channels
        distributed_channels = self.__distribute_propagation_channels(len(channel_points), self.__channel_tessellation_parameters["distribution_method"], self.__channel_tessellation_parameters["losses_model"])

        # Create channel tessellation structure
        channel_tessellation = pred_scenario.structured_diagram(channel_points, distributed_channels, self.__channel_voronoi_2d)

        return channel_tessellation

    @staticmethod
    def __distribute_propagation_channels(number_of_channels: int, distribution_method: str, losses_model: str):
        """
            It distributes the scenarios available for the simulation according to probability and creates the channels.

            :param number_of_channels: number of channels to be distributed.
            :param distribution_method: method for distributing scenarios across the map
            :param losses_model: losses model used for the simulations.

            :return [list of objects (SIMULATOR.Channel)]: propagation channels generated according to the scenarios distributed over the map.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        channels = []

        for i in range(0, number_of_channels):

            # Choose an environment and line of sight randomly
            if distribution_method == "random":
                current_channel_id = random.choice(['UMa LOS', 'Umi LOS', 'Indoor LOS', 'UMa NLOS', 'Umi NLOS', 'Indoor NLOS'])

            # All the environments are the same
            elif distribution_method in ('UMa LOS', 'Umi LOS', 'Indoor LOS', 'UMa NLOS', 'Umi NLOS', 'Indoor NLOS'):
                current_channel_id = distribution_method

            else:
                raise ConfigurationNotFound("distribution_method")

            # It creates the channels
            c = Channel("CHANNEL_" + str(i + 1), current_channel_id.split(" ")[0], current_channel_id.split(" ")[1], losses_model)
            channels.append(c)

        return channels

    def get_channel_voronoi_2d(self):
        """
            It returns the private attribute "channel_voronoi_2d".

            :return [list]: structure returned by the generation of the voronoi diagram of the channels (its necessary to draw the regions).
        """

        return self.__channel_voronoi_2d
