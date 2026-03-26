# TEST "PLOT_backhaul_network.py"

import SIMULATOR.src.CELLULAR_NETWORK.test.TEST_base_station as testBs
from SIMULATOR.src.CELLULAR_NETWORK.backhaul.backhaul_network import BackhaulNetwork
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.MODELS.latency_models import LatencyModel
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_backhaul_network as PlotBackhaul
import matplotlib.pyplot as plt
import os
os.chdir("/home/jricopal/Documentos/Workspace/PythonSimulator_v6/")

# * Create base stations dict
base_stations = dict()
base_stations[testBs.bs_1.BS_id] = testBs.bs_1
base_stations[testBs.bs_2.BS_id] = testBs.bs_2
base_stations[testBs.bs_3.BS_id] = testBs.bs_3
base_stations[testBs.bs_4.BS_id] = testBs.bs_4
base_stations[testBs.bs_5.BS_id] = testBs.bs_5
base_stations[testBs.bs_6.BS_id] = testBs.bs_6
base_stations[testBs.bs_7.BS_id] = testBs.bs_7

# * Create simulation map
simulation_map = SimulationMap("MAP_0", map_configuration="TEST")
# ? Test hexagonal, test materns and thomas point process, test 1 macro BS, test 1 small BS

# * Create backhaul network
latency_model_parameters = dict({"mu": 1, "beta": 2, "sigma": 3000000})
latency_model = LatencyModel("LATENCY_MODEL_1", model_parameters=latency_model_parameters)

link_parameters = dict()
link_parameters["sinr_threshold"] = 3
link_parameters["latency_model"] = latency_model
link_parameters["t_slot"] = 5

backhaul_network = BackhaulNetwork("BACKHAUL_NETWORK_0", base_stations, link_parameters, simulation_map, topology="random", link_technology="RF")
print(str(backhaul_network)+"\n")

for current_bs in base_stations.keys():
    print(current_bs)
    print(base_stations[current_bs].BS_backhaul_block)
    print("--------------------------------------------")

PlotBackhaul.abstract_backhaul_graph(backhaul_network, base_stations)
plt.show()
