# Test "link_planifications.py"

from SIMULATOR.src.MOBILE_NODES.users import DynamicUser
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import MacroBS, SmallBS
import SIMULATOR.src.GEOMETRY.link_planifications as lp
import os
os.chdir("/home/jricopal/Documentos/Workspace/PythonSimulator_v6/")

simulation_map = SimulationMap("MAP_TEST", map_configuration="TEST")

antenna_parameters = dict({"height": 1, "n_rx": 6, "gain": 9})
sim_parameters = dict({"type": "simple", "multiconnectivity_mode": "simple"})
traffic_parameters = dict({"model": "generic_demand", "num_demands": 2, "min_time": 2, "max_time": 25, "simulation_time": 20, "min_size": 10, "max_size": 20, "min_duration": 2, "max_duration": 5})
mobility_parameters = dict({"model": "FF", "min_speed": 2, "max_speed": 5, "movement_time": 30, "movement_height": simulation_map.MAP_size})
user = DynamicUser("USER_TEST", mobility_parameters, antenna_parameters, sim_parameters, traffic_parameters, 100)

# * Generate base stations
base_stations = dict()

# MACRO NODEB CONFIGURATION
macro_nodeb_economic_model = None
macro_nodeb_power_model = None
macro_nodeb_total_user_bandwidth = 500
macro_nodeb_bandwidth_plannification = "standard"
macro_nodeb_configuration = dict({"economic_model": macro_nodeb_economic_model, "power_model": macro_nodeb_power_model, "total_user_bandwidth": macro_nodeb_total_user_bandwidth, "bandwidth_plannification": macro_nodeb_bandwidth_plannification})

# MACRO ANTENNA CONFIGURATION (omnidirectional)
macro_antenna_model = "omnidirectional"
macro_antenna_economic_model = None
macro_antenna_power_model = None
macro_antenna_height = 30
macro_antenna_frequency = 2
macro_antenna_tx_power = 28
macro_antenna_ntx = 4
macro_antenna_gain = 12
macro_backhaul_antenna_height = 20
macro_backhaul_antenna_frequency = 21
macro_backhaul_antenna_scanning_range_azimuth = 30
macro_backhaul_antenna_scanning_range_tilt = 20
macro_backhaul_antenna_n_tx = 9
macro_backhaul_antenna_p_tx = 12
macro_backhaul_antenna_gain = 9
macro_backhaul_antenna_bandwidth = 20
macro_backhaul_antenna_parameters = dict({"height": macro_backhaul_antenna_height, "frequency": macro_backhaul_antenna_frequency, "scanning_range_azimuth": macro_backhaul_antenna_scanning_range_azimuth, "scanning_range_tilt": macro_backhaul_antenna_scanning_range_tilt, "n_tx": macro_backhaul_antenna_n_tx, "p_tx": macro_backhaul_antenna_p_tx, "gain": macro_backhaul_antenna_gain, "bandwidth": macro_backhaul_antenna_bandwidth})
macro_antenna_configuration = dict({"antenna_model": macro_antenna_model, "economic_model": macro_antenna_economic_model, "power_model": macro_antenna_power_model, "height": macro_antenna_height, "frequency": macro_antenna_frequency, "tx_power": macro_antenna_tx_power, "ntx": macro_antenna_ntx, "gain": macro_antenna_gain, "backhaul_antennas_parameters": macro_backhaul_antenna_parameters})

# SMALL NODEB CONFIGURATION
small_nodeb_economic_model = None
small_nodeb_power_model = None
small_nodeb_total_user_bandwidth = 750
small_nodeb_bandwidth_plannification = "standard"
small_nodeb_configuration = dict({"economic_model": small_nodeb_economic_model, "power_model": small_nodeb_power_model, "total_user_bandwidth": small_nodeb_total_user_bandwidth, "bandwidth_plannification": small_nodeb_bandwidth_plannification})

# SMALL ANTENNA CONFIGURATION (omnidirectional)
small_antenna_model = "omnidirectional"
small_antenna_economic_model = None
small_antenna_power_model = None
small_antenna_height = 15
small_antenna_frequency = 28
small_antenna_tx_power = 12
small_antenna_ntx = 25
small_antenna_gain = 6
small_backhaul_antenna_height = 15
small_backhaul_antenna_frequency = 21
small_backhaul_antenna_scanning_range_azimuth = 30
small_backhaul_antenna_scanning_range_tilt = 20
small_backhaul_antenna_n_tx = 9
small_backhaul_antenna_p_tx = 12
small_backhaul_antenna_gain = 9
small_backhaul_antenna_bandwidth = 100
small_backhaul_antenna_parameters = dict({"height": small_backhaul_antenna_height, "frequency": small_backhaul_antenna_frequency, "scanning_range_azimuth": small_backhaul_antenna_scanning_range_azimuth, "scanning_range_tilt": small_backhaul_antenna_scanning_range_tilt, "n_tx": small_backhaul_antenna_n_tx, "p_tx": small_backhaul_antenna_p_tx, "gain": small_backhaul_antenna_gain, "bandwidth": macro_backhaul_antenna_bandwidth})
small_antenna_configuration = dict({"antenna_model": small_antenna_model, "economic_model": small_antenna_economic_model, "power_model": small_antenna_power_model, "height": small_antenna_height, "frequency": small_antenna_frequency, "tx_power": small_antenna_tx_power, "ntx": small_antenna_ntx, "gain": small_antenna_gain, "backhaul_antennas_parameters": small_backhaul_antenna_parameters})

# Macro BS
i = 0
for current_point in simulation_map.MAP_device_tessellation["macro"]["points"]:
    current_bs = MacroBS("MACRO_BS_"+str(i+1), current_point, None, None, macro_nodeb_configuration, macro_antenna_configuration, 1000, 1000)
    base_stations[current_bs.BS_id] = current_bs
    i += 1

# Small BS
i = 0
for current_point in simulation_map.MAP_device_tessellation["small"]["points"]:
    current_bs = SmallBS("SMALL_BS_"+str(i+1), "small", current_point, None, None, small_nodeb_configuration, small_antenna_configuration, 1000)
    base_stations[current_bs.BS_id] = current_bs
    i += 1

for current_step in user.DUSER_steps:

    # Update user position
    user.USER_position = current_step.STEP_position
    user.USER_ue.UE_antenna.UEANTENNA_bandwidth = 10
    # link planifications
    best_bs_distance, distances = lp.distance_vector(user, base_stations)
    print("DISTANCE VECTOR PLANIFICATION")
    print(distances)
    print()
    print(best_bs_distance)
    print("-----------------------------")

    best_bs_sinr, sinrs = lp.sinr_schedule_dl(user, base_stations, simulation_map)
    print("SINR PLANIFICATION")
    print(sinrs)
    print()
    print(best_bs_sinr)
    print("-----------------------------")

    best_bs_latency, latencies, sinrs = lp.latency_estimation(user, base_stations, simulation_map, pilot_slot=0.01)
    print("LATENCY PLANIFICATION")
    print(latencies)
    print()
    print(best_bs_latency)
    print("-----------------------------")

    best_bs_capacity, capacities, sinrs = lp.capacity_estimation(user, base_stations, simulation_map)
    print("CAPACITY PLANIFICATION")
    print(capacities)
    print()
    print(best_bs_capacity)
    print("-----------------------------")

