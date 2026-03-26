# TEST "simulation_map.py"

from SIMULATOR.src.MAP.simulation_map import SimulationMap
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_simulation_map as PlotMap
import matplotlib.pyplot as plt
import os
os.chdir("/home/jricopal/Documentos/Workspace/PythonSimulator_v6/")

channel_parameters = dict()
channel_parameters["pp"] = "PPP"
channel_parameters["alpha"] = 10
channel_parameters["radius"] = 0
channel_parameters["number_of_points"] = 0
channel_parameters["distribution_method"] = "random"  # 'UMa LOS', 'Umi LOS', 'Indoor LOS', 'UMa NLOS', 'Umi NLOS', 'Indoor NLOS'
channel_parameters["losses_model"] = "ABG"

macro_device_parameters = dict()
macro_device_parameters["tessellation"] = "hexagonal"  # voronoi
macro_device_parameters["pp"] = "PPP"
macro_device_parameters["alpha"] = 5  # ! test different densities
macro_device_parameters["beta"] = 10  # ! test different densities
macro_device_parameters["sigma/radius"] = 2  # ! test different densities
macro_device_parameters["number_of_points"] = 0  # ! test different densities
macro_device_parameters["hex_radius"] = 100  # ! test different densities

small_device_parameters = dict()
small_device_parameters["tessellation"] = "voronoi"  # hexagonal
small_device_parameters["pp"] = "PPP"
small_device_parameters["alpha"] = 2  # ! test different densities
small_device_parameters["beta"] = 0  # ! test different densities
small_device_parameters["sigma/radius"] = 30  # ! test different densities
small_device_parameters["number_of_points"] = 0  # ! test different densities
small_device_parameters["hex_radius"] = 20  # ! test different densities

device_parameters = dict({"macro": macro_device_parameters, "small": small_device_parameters})
bs_levels = 2

simulation_map = SimulationMap("TEST_MAP_1", map_size=1000, bs_levels=bs_levels, device_parameters=device_parameters, channel_parameters=channel_parameters)

# print(simulation_map.MAP_device_tessellation)
# print("-------------------------------------")
# print(simulation_map.MAP_channel_tessellation)

PlotMap.complete_scenario(simulation_map)
# plt.show()
