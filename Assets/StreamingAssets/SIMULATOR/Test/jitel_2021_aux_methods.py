# Test 'jitel_2021_aux_methods'

from typing import *
import sys
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
from SIMULATOR.src.MOBILE_NODES.users import User
from SIMULATOR.src.MODELS.latency_models import LatencyModel
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
from SIMULATOR.src.LINKS.rf_link import RFLink
import SIMULATOR.src.GEOMETRY.link_planifications as lp
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
from shapely.geometry import Point, Polygon


def connect_user_to_network(current_user: str, users: Dict[str, User], base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, link_planification: str):

    # Calculate candidate BS
    if link_planification == "sinr":
        best_bs_id, sinrs = lp.sinr_schedule_dl(users[current_user], base_stations, simulation_map, threshold=100)

    elif link_planification == "capacity_estimation":
        best_bs_id, capacities, sinrs = lp.capacity_estimation(users[current_user], base_stations, simulation_map)

    elif link_planification == "latency_estimation":
        best_bs_id, capacities, sinrs = lp.latency_estimation(users[current_user], base_stations, simulation_map, pilot_slot=0.01)

    else:
        print("ERROR -> link planification")
        sys.exit(4)

    # Connect user to BS
    bw = base_stations[best_bs_id].connect_user(users[current_user].USER_id, users[current_user].USER_priority, 10, 0, "standard")

    # user attributes
    sinr = sinrs[best_bs_id]
    n_rx = users[current_user].USER_ue.UE_antenna.UEANTENNA_nrx
    latency_model = LatencyModel("LATENCY_MODEL_1", model_parameters=dict({"mu": 70, "beta": 2, "sigma": 1}))
    user_position = users[current_user].USER_position
    user_height = users[current_user].USER_ue.UE_antenna.UEANTENNA_height

    # bs attributes
    target_bs = base_stations[best_bs_id]
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
    link_id = "UE_LINK_" + users[current_user].USER_id.split("_")[1]
    link = RFLink(link_id, "ue", latency_model, best_bs_id, n_tx, tx_power, users[current_user].USER_id, n_rx, bw, 0.01, weighted_channels, path_loss, sinr)
    users[current_user].USER_ue.UE_sim.SIM_link = link
    users[current_user].USER_ue.UE_antenna.UEANTENNA_bandwidth = bw
