# Module 'link_planifications'
# Created 06/03/2020 (version 3.0)
# Modified 16/05/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *
import operator
from SIMULATOR.src.MOBILE_NODES.users import User
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
import SIMULATOR.src.MATH_UTILS.formulas as f
import SIMULATOR.src.PROPAGATION_CHANNEL.channel_estimation as ce


def distance_vector(rx_device: User, base_stations: Dict[str, BaseStation]):
    """
        Link schedule based on distance vector. The candidate bs shall be the one with the shortest distance to the receiver.

        :param rx_device: user who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.

        :return [str] nearest_bs_id: identifier of the nearest bs.
        :return [dict] distances: base station identifier and its distances to the receiver.
    """

    distances = dict()
    nearest_bs_id = ""

    # Calculates the distance between receiver and each base stations and store
    for BS in base_stations.keys():
        current_distance = gf.euclidean_distance(base_stations[BS].BS_position, rx_device.USER_position, elevation_tx=base_stations[BS].BS_antenna.ANTENNA_height, elevation_rx=rx_device.USER_ue.UE_antenna.UEANTENNA_height)
        distances[base_stations[BS].BS_id] = current_distance

    # Calculate the shortest distance
    aux_distance = next(iter(distances.values()))
    for BS in distances.keys():
        if distances[BS] < aux_distance:
            nearest_bs_id = BS
            aux_distance = distances[BS]

    return nearest_bs_id, distances


def sinr_schedule_dl(rx_device: User, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, threshold: float = -9):
    """
        Link schedule based on SINR (for downlink scenarios). The candidate bs shall be the one with the high SINR to the receiver.

        :param rx_device: user who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.
        :param simulation_map: map generated for the simulation.
        :param* threshold: the minimum number of SINRs that a base station must have with the receiver to be a candidate (in dBm). Defaults to -9.

        :return [str] best_bs_id: identifier of the bs with high SINR.
        :return [dict] sinrs: base station identifier and its sinrs to the receiver.
    """

    sinrs = dict()
    aux_signals = dict()

    # Calculates the signal level received for all base stations
    for BS in base_stations.keys():

        # Calculates weighted losses
        current_weighted_channels = Channel.weight_channels(base_stations[BS].BS_position, rx_device.USER_position, simulation_map, tx_height=base_stations[BS].BS_antenna.ANTENNA_height, rx_height=rx_device.USER_ue.UE_antenna.UEANTENNA_height)
        current_weighted_losses = Channel.weight_losses(current_weighted_channels, base_stations[BS].BS_antenna.get_frequency(rx_device.USER_position, base_stations[BS].BS_position), simulation_map)

        # Calculate rx signal
        tx_power = base_stations[BS].BS_antenna.get_tx_power(rx_device.USER_position, base_stations[BS].BS_position, rx_height=rx_device.USER_ue.UE_antenna.UEANTENNA_height, tx_height=base_stations[BS].BS_antenna.ANTENNA_height)
        tx_gain = base_stations[BS].BS_antenna.get_gain(rx_device.USER_position, base_stations[BS].BS_position, rx_height=rx_device.USER_ue.UE_antenna.UEANTENNA_height, tx_height=base_stations[BS].BS_antenna.ANTENNA_height)
        signal_in_dbm = Channel.link_budget(tx_power, tx_gain, rx_device.USER_ue.UE_antenna.UEANTENNA_gain, current_weighted_losses)
        signal_in_units = f.to_units(signal_in_dbm)

        # Add previous calculated rx signal to the data structure
        aux_signals[BS] = signal_in_units

    # Calculates the SINR from the receiver to all base stations
    for BS in base_stations.keys():

        aux_interferences = []

        for S in aux_signals.keys():

            if S != BS and base_stations[BS].BS_antenna.get_frequency(rx_device.USER_position, base_stations[BS].BS_position) == base_stations[S].BS_antenna.get_frequency(rx_device.USER_position, base_stations[BS].BS_position):
                aux_interferences.append(aux_signals[S])

        aux_bandwidth = base_stations[BS].BS_node.get_total_bandwidth() / (len(base_stations[BS].BS_node.NODEB_users)+1)
        received_sinr = Channel.sinr(aux_signals[BS], aux_bandwidth, sum(aux_interferences))
        sinrs[BS] = received_sinr

    # Check whether the base station to which it was previously connected meets the threshold requirement
    bs_previously_connected = rx_device.USER_ue.UE_sim.get_bs_connected()

    if bs_previously_connected in sinrs and sinrs[bs_previously_connected] > threshold:
        best_bs_id = bs_previously_connected

    else:  # Calculates the highest SINR

        best_bs_id = next(iter(sinrs.keys()))
        aux_sinr = sinrs[best_bs_id]

        for BS in sinrs.keys():
            if sinrs[BS] >= aux_sinr:
                best_bs_id = BS
                aux_sinr = sinrs[BS]

    return best_bs_id, sinrs


def mixed_distance_sinr_dl(rx_device: User, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, threshold: float = -9, number_of_near_bs: float = 5):
    """
        Link schedule based on SINR (for downlink scenarios) but only evaluate the nearest bs.
        The candidate bs shall be the one with the high SINR to the receiver (as long as it is close to the receiver).

        :param rx_device: user who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.
        :param simulation_map: map generated for the simulation.
        :param* threshold: the minimum number of SINRs that a base station must have with the receiver to be a candidate (in dBm). Defaults to -9.
        :param* number_of_near_bs: number of bss to be evaluated (the closest ones). Defaults to 5.

        :return [str] best_bs_id: identifier of the bs with high SINR.
        :return [dict] sinrs: base station identifier and its sinrs to the receiver.
    """

    near_base_stations = dict()

    # Obtain the distances to receiver to all BSs
    _, distances = distance_vector(rx_device, base_stations)

    # Sort the distances from smallest to largest (reverse=False)
    distances_sort = sorted(distances.items(), key=operator.itemgetter(1), reverse=False)

    # Get the "number_of_near_bs" near BSs and store in a aux dict
    aux_nearest_bs = list(distances_sort)[:number_of_near_bs]
    [near_base_stations.update({aux_nearest_bs[i][0]: base_stations[aux_nearest_bs[i][0]]}) for i in range(0, len(aux_nearest_bs))]

    # Obtain the sinrs of the near BSs
    best_bs_id, sinrs = sinr_schedule_dl(rx_device, near_base_stations, simulation_map, threshold=threshold)

    return best_bs_id, sinrs


def sinr_schedule_backhaul(candidate_bs: BaseStation, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap):
    """
        Link schedule based on SINR (for backhaul connections). The candidate bs shall be the one with the high SINR to the receiver.
        Its evaluate the sinr with a generic bs backhaul antenna.

        :param candidate_bs: base station who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.
        :param simulation_map: map generated for the simulation.

        :return [str] best_bs_id: identifier of the bs with high SINR.
        :return [dict] sinrs: base station identifier and its sinrs to the receiver.
    """

    sinrs = dict()
    aux_signals = dict()

    # Calculates the signal level received for all base stations
    for BS in base_stations.keys():

        if BS != candidate_bs.BS_id:

            # Calculates weighted losses
            current_weighted_channels = Channel.weight_channels(base_stations[BS].BS_position, candidate_bs.BS_position, simulation_map, tx_height=base_stations[BS].BS_backhaul_block.BB_antenna_parameters["height"], rx_height=candidate_bs.BS_backhaul_block.BB_antenna_parameters["height"])
            current_weighted_losses = Channel.weight_losses(current_weighted_channels, candidate_bs.BS_backhaul_block.BB_antenna_parameters["frequency"], simulation_map)

            # Calculate rx signal
            tx_power = base_stations[BS].BS_backhaul_block.BB_antenna_parameters["p_tx"]
            tx_gain = base_stations[BS].BS_backhaul_block.BB_antenna_parameters["gain"]
            signal_in_dbm = Channel.link_budget(tx_power, tx_gain, candidate_bs.BS_backhaul_block.BB_antenna_parameters["gain"], current_weighted_losses)
            signal_in_units = f.to_units(signal_in_dbm)

            # Add previous calculated rx signal to the data structure
            aux_signals[BS] = signal_in_units

    # Calculates the SINR from the receiver to all base stations
    for BS in base_stations.keys():

        if BS != candidate_bs.BS_id:  # does not evaluate herself

            aux_interferences = []

            for S in aux_signals.keys():

                if S != BS and base_stations[BS].BS_backhaul_block.BB_antenna_parameters["frequency"] == base_stations[S].BS_backhaul_block.BB_antenna_parameters["frequency"]:
                    aux_interferences.append(aux_signals[S])

            aux_bandwidth = base_stations[BS].BS_backhaul_block.get_max_backhaul_bandwidth() / (len(base_stations[BS].BS_backhaul_block.BB_antennas) + 1)
            received_sinr = Channel.sinr(aux_signals[BS], aux_bandwidth, sum(aux_interferences))
            sinrs[BS] = received_sinr

    best_bs_id = next(iter(sinrs.keys()))
    aux_sinr = sinrs[best_bs_id]

    for BS in sinrs.keys():
        if sinrs[BS] >= aux_sinr:
            best_bs_id = BS
            aux_sinr = sinrs[BS]

    return best_bs_id, sinrs


def capacity_estimation(rx_device: User, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap):
    """
        Link schedule based on channel estimation (for downlink scenarios).
        The candidate bs shall be the one with the high available theoretical capacity to the receiver.

        :param rx_device: user who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.
        :param simulation_map: map generated for the simulation.

        :return [str] best_bs_id: identifier of the bs with high available theoretical capacity.
        :return [dict] capacities: base station identifier and its available capacities to the receiver.
        :return [dict] sinrs: base station identifier and its sinrs to the receiver.
    """

    capacities = dict()

    best_bs_id_sinr, sinrs = sinr_schedule_dl(rx_device, base_stations, simulation_map, threshold=1000)

    # Calculates the estimated capacity for all base stations
    for BS in base_stations.keys():
        capacities[BS] = ce.capacity_estimation(rx_device, base_stations[BS], sinrs[BS])

    # Calculates the highest capacity
    best_bs_id = next(iter(capacities.keys()))
    aux_capacity = capacities[best_bs_id]

    for BS in capacities.keys():
        if capacities[BS] >= aux_capacity:
            best_bs_id = BS
            aux_capacity = capacities[BS]

    return best_bs_id, capacities, sinrs


def latency_estimation(rx_device: User, base_stations: Dict[str, BaseStation], simulation_map: SimulationMap, pilot_slot: float = 1):
    """
        Link schedule based on propagation latency estimation (for downlink scenarios).
        The candidate bs shall be the one with the low propagation latency to the receiver.

        :param rx_device: user who will be the receiver of the link.
        :param base_stations: base stations generated for the simulation.
        :param simulation_map: map generated for the simulation.
        :param* pilot_slot: duration of the transmission pilot slot (in ms). Defaults to 1.

        :return [str] best_bs_id: identifier of the bs with low propagation latency to the receiver.
        :return [dict] latencies: base station identifier and its propagation latencies to the receiver.
        :return [dict] sinrs: base station identifier and its sinrs to the receiver.
    """

    latencies = dict()

    best_bs_id_sinr, sinrs = sinr_schedule_dl(rx_device, base_stations, simulation_map, threshold=1000)

    # Calculates the estimated propagation latency for all base stations
    for BS in base_stations.keys():
        latencies[BS] = ce.latency_estimation(rx_device, base_stations[BS], t_slot=pilot_slot)

    # Calculates the highest capacity
    best_bs_id = next(iter(latencies.keys()))
    aux_latency = latencies[best_bs_id]

    for BS in latencies.keys():
        if latencies[BS] <= aux_latency:
            best_bs_id = BS
            aux_latency = latencies[BS]

    return best_bs_id, latencies, sinrs
