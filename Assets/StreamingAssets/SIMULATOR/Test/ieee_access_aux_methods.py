# Test 'ieee_access_aux_methods.py'

from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.MOBILE_NODES.users import DynamicUser, StaticUser, User
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import MacroBS, SmallBS, BaseStation
from SIMULATOR.src.LINKS.rf_link import RFLink
from SIMULATOR.src.MODELS.latency_models import LatencyModel
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
import SIMULATOR.src.GEOMETRY.link_planifications as lp
from shapely.geometry import Point, Polygon
from typing import *
import json
import random as rd
import sys


def generate_cellular_network(simulation_map: SimulationMap, macro_user_bandwidth: float, small_user_bandwidth: float):

    base_stations = dict()

    # macro nodeb configuration
    macro_nodeb_economic_model = None
    macro_nodeb_power_model = None
    macro_nodeb_total_user_bandwidth = macro_user_bandwidth
    macro_nodeb_bandwidth_plannification = "standard"
    macro_nodeb_configuration = dict({"economic_model": macro_nodeb_economic_model, "power_model": macro_nodeb_power_model, "total_user_bandwidth": macro_nodeb_total_user_bandwidth, "bandwidth_plannification": macro_nodeb_bandwidth_plannification})

    # macro antenna configuration
    macro_antenna_model = "omnidirectional"
    macro_antenna_economic_model = None
    macro_antenna_power_model = None
    macro_antenna_height = 40  # ? macro antenna configuration
    macro_antenna_frequency = 6  # ? macro antenna configuration
    macro_antenna_tx_power = 28  # ? macro antenna configuration
    macro_antenna_ntx = 10  # ? macro antenna configuration
    macro_antenna_gain = 12  # ? macro antenna configuration
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

    # Generate macro cells
    i = 0
    for current_point in simulation_map.MAP_device_tessellation["macro"]["points"]:
        current_bs = MacroBS("MACRO_BS_" + str(i + 1), current_point, None, None, macro_nodeb_configuration, macro_antenna_configuration, 1000, 1000)
        base_stations[current_bs.BS_id] = current_bs
        i += 1

    # small nodeb configuration
    small_nodeb_economic_model = None
    small_nodeb_power_model = None
    small_nodeb_total_user_bandwidth = small_user_bandwidth
    small_nodeb_bandwidth_plannification = "standard"
    small_nodeb_configuration = dict({"economic_model": small_nodeb_economic_model, "power_model": small_nodeb_power_model, "total_user_bandwidth": small_nodeb_total_user_bandwidth, "bandwidth_plannification": small_nodeb_bandwidth_plannification})

    # small antenna configuration
    small_antenna_model = "omnidirectional"
    small_antenna_economic_model = None
    small_antenna_power_model = None
    small_antenna_height = 15  # ? small antenna configuration
    small_antenna_frequency = 21  # ? small antenna configuration
    small_antenna_tx_power = 12  # ? small antenna configuration
    small_antenna_ntx = 16  # ? small antenna configuration
    small_antenna_gain = 8  # ? small antenna configuration
    small_backhaul_antenna_height = 15
    small_backhaul_antenna_frequency = 21
    small_backhaul_antenna_scanning_range_azimuth = 30
    small_backhaul_antenna_scanning_range_tilt = 20
    small_backhaul_antenna_n_tx = 9
    small_backhaul_antenna_p_tx = 12
    small_backhaul_antenna_gain = 9
    small_backhaul_antenna_bandwidth = 100
    small_backhaul_antenna_parameters = dict({"height": small_backhaul_antenna_height, "frequency": small_backhaul_antenna_frequency, "scanning_range_azimuth": small_backhaul_antenna_scanning_range_azimuth, "scanning_range_tilt": small_backhaul_antenna_scanning_range_tilt, "n_tx": small_backhaul_antenna_n_tx, "p_tx": small_backhaul_antenna_p_tx, "gain": small_backhaul_antenna_gain, "bandwidth": small_backhaul_antenna_bandwidth})
    small_antenna_configuration = dict({"antenna_model": small_antenna_model, "economic_model": small_antenna_economic_model, "power_model": small_antenna_power_model, "height": small_antenna_height, "frequency": small_antenna_frequency, "tx_power": small_antenna_tx_power, "ntx": small_antenna_ntx, "gain": small_antenna_gain, "backhaul_antennas_parameters": small_backhaul_antenna_parameters})

    # Generate small cells
    i = 0
    for current_point in simulation_map.MAP_device_tessellation["small"]["points"]:
        current_bs = SmallBS("SMALL_BS_" + str(i + 1), "small", current_point, None, None, small_nodeb_configuration, small_antenna_configuration, 1000)
        base_stations[current_bs.BS_id] = current_bs
        i += 1

    return base_stations


def generate_dynamic_users(num_users: int, simulation_time: float, simulation_map: SimulationMap, bw_requirement: float, predefined_steps=False, directory_path="/home/jricopal/Escritorio/", offset: int = 0):

    dynamic_users = dict()

    antenna_parameters = dict({"height": 1.7, "n_rx": 4, "gain": 5})  # ? UE configuration
    sim_parameters = dict({"type": "simple", "multiconnectivity_mode": "simple"})
    traffic_parameters = dict({"model": "generic_demand", "num_demands": 2, "min_time": 2, "max_time": 25, "simulation_time": 20, "min_size": 10, "max_size": 20, "min_duration": 2, "max_duration": 5})
    mobility_parameters = dict({"model": "RWP", "min_speed": 1000, "max_speed": 2000, "movement_time": simulation_time, "movement_height": simulation_map.MAP_size})

    if predefined_steps:
        with open(directory_path) as json_file:
            user_data = json.load(json_file)

    for i in range(0, num_users):

        if predefined_steps:
            mobility_parameters["predefined_steps"] = user_data["USER_"+str(i+1+offset)]

        if i < 10:  # URLLC
            user_type = 3
            bw_requirement = bw_requirement

        elif 10 <= i < 30:  # mMTC
            user_type = 2
            bw_requirement = 1

        else:  # eMBB
            user_type = 1
            bw_requirement = bw_requirement

        current_user = DynamicUser("USER_"+str(i+1+offset), mobility_parameters, antenna_parameters, sim_parameters, traffic_parameters, bw_requirement, priority=user_type)
        dynamic_users[current_user.USER_id] = current_user

    return dynamic_users


def generate_static_users(num_users: int, simulation_map: SimulationMap, bw_requirement: float, predefined_position=False, directory_path="/home/jricopal/Escritorio/", offset: int = 0):

    static_users = dict()

    antenna_parameters = dict({"height": 1.7, "n_rx": 4, "gain": 5})  # ? UE configuration
    sim_parameters = dict({"type": "simple", "multiconnectivity_mode": "simple"})
    traffic_parameters = dict({"model": "generic_demand", "num_demands": 2, "min_time": 2, "max_time": 25, "simulation_time": 20, "min_size": 10, "max_size": 20, "min_duration": 2, "max_duration": 5})

    if predefined_position:
        with open(directory_path+"config/user_positions.json") as json_file:
            user_data = json.load(json_file)

    for i in range(0, num_users):

        if predefined_position:
            current_user = StaticUser("USER_"+str(i+1+offset), "sensor", antenna_parameters, sim_parameters, traffic_parameters, bw_requirement, position=user_data["USER_"+str(i+1+offset)])  # ! Bandwidth requirements

        else:
            current_user = StaticUser("USER_" + str(i+1+offset), "sensor", antenna_parameters, sim_parameters, traffic_parameters, bw_requirement, map_size=simulation_map.MAP_size)  # ! Bandwidth requirements

        static_users[current_user.USER_id] = current_user

    return static_users


def calculate_candidate_bs(current_user: User, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, link_planification: str):

    metric_values = dict()

    if link_planification == "sinr":
        best_bs_id, sinrs = lp.sinr_schedule_dl(current_user, base_stations, simulation_map, threshold=100)

    elif link_planification == "capacity_estimation":
        best_bs_id, capacities, sinrs = lp.capacity_estimation(current_user, base_stations, simulation_map)
        metric_values = capacities

    elif link_planification == "latency_estimation":
        best_bs_id, latencies, sinrs = lp.latency_estimation(current_user, base_stations, simulation_map, pilot_slot=0.01)
        metric_values = latencies

    else:
        print("ERROR in link planification")
        sys.exit(4)

    return best_bs_id, sinrs, metric_values


def reconnect_user(current_user: User, base_stations: Dict[str, BaseStation], old_bs: str, new_bs: str, event_time: float, bw_algorithm: str):

    # Disconnect user from old bs
    base_stations[old_bs].disconnect_user(current_user.USER_id)

    # Connect user to new bs
    bw = base_stations[new_bs].connect_user(current_user.USER_id, current_user.USER_priority, current_user.USER_ue.UE_antenna.UEANTENNA_bandwidth, event_time, bw_algorithm)

    return bw


def update_variables(current_user_id: str, users: Dict[str, User], base_stations: Dict[str, BaseStation], bs_connected: str, sinrs: Dict[str, float], assigned_bandwidth: float, simulation_map: SimulationMap):

    # user attributes
    sinr = sinrs[bs_connected]
    n_rx = users[current_user_id].USER_ue.UE_antenna.UEANTENNA_nrx
    latency_model = LatencyModel("LATENCY_MODEL_1", model_parameters=dict({"mu": 70, "beta": 2, "sigma": 1}))
    user_position = users[current_user_id].USER_position
    user_height = users[current_user_id].USER_ue.UE_antenna.UEANTENNA_height

    # bs attributes
    target_bs = base_stations[bs_connected]
    bs_position = target_bs.BS_position
    bs_height = target_bs.BS_antenna.ANTENNA_height
    tx_power = target_bs.BS_antenna.get_tx_power(user_position, bs_position, rx_height=user_height, tx_height=bs_height)
    n_tx = target_bs.BS_antenna.get_ntx(user_position, bs_position, rx_height=user_height, tx_height=bs_height)
    distance = gf.euclidean_distance(bs_position, user_position, elevation_rx=user_height, elevation_tx=bs_height)
    frequency = target_bs.BS_antenna.get_frequency(user_position, bs_position, rx_height=user_height, tx_height=bs_height)

    # channel attributes
    path_loss = -1
    for current_channel in simulation_map.MAP_channel_tessellation.keys():
        if Polygon(simulation_map.MAP_channel_tessellation[current_channel]["polygon"][0]).contains(Point(user_position)):
            path_loss = simulation_map.MAP_channel_tessellation[current_channel]["channel"].path_loss(distance, frequency)
    weighted_channels = Channel.weight_channels(user_position, bs_position, simulation_map, rx_height=user_height, tx_height=bs_height)

    # Create user link
    link_id = "UE_LINK_" + users[current_user_id].USER_id.split("_")[1]

    if users[current_user_id].USER_priority == 3:  # URLLC
        throughput = rd.uniform(40, 100)  # ! High throughput

    elif users[current_user_id].USER_priority == 2:  # mMTC
        throughput = rd.uniform(10, 80)  # ! High throughput

    elif users[current_user_id].USER_priority == 1:  # eMBB
        throughput = rd.uniform(100, 400)  # ! High throughput

    link = RFLink(link_id, "ue", latency_model, bs_connected, n_tx, tx_power, users[current_user_id].USER_id, n_rx, assigned_bandwidth, 0.01, weighted_channels, path_loss, sinr, throughput=throughput)
    users[current_user_id].USER_ue.UE_sim.SIM_link = link
    users[current_user_id].USER_ue.UE_antenna.UEANTENNA_bandwidth = assigned_bandwidth


def update_variables_from_all_users(users: Dict[str, User], base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, link_planification: str, last_evaluated_user_id: str):

    for current_user in users.values():

        if current_user.USER_id != last_evaluated_user_id:

            connected_bs = current_user.USER_ue.UE_sim.get_bs_connected()
            best_bs_id, sinrs, metric_values = calculate_candidate_bs(current_user, base_stations, simulation_map, link_planification)
            assigned_bandwidth = current_user.USER_ue.UE_sim.SIM_link.LINK_bandwidth
            update_variables(current_user.USER_id, users, base_stations, connected_bs, sinrs, assigned_bandwidth, simulation_map)


def connect_user_to_network(current_user_id: str, users: Dict[str, User], link_planification: str, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, current_simulation_time: float, bandwidth_allocation_algorithm: str):

    # Calculate candidate BS
    best_bs_id, sinrs, metrics_values = calculate_candidate_bs(users[current_user_id], base_stations, simulation_map, link_planification)

    # Connect user to BS
    bw = base_stations[best_bs_id].connect_user(current_user_id, users[current_user_id].USER_priority, users[current_user_id].USER_ue.UE_antenna.UEANTENNA_bandwidth, current_simulation_time, bandwidth_allocation_algorithm)

    # Update user and cellular network variables
    update_variables(current_user_id, users, base_stations, best_bs_id, sinrs, bw, simulation_map)
