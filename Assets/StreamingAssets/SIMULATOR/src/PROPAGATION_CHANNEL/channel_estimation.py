# Module 'channel_estimation'
# Created 21/04/2021 (version 6.0)
# Modified 21/04/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
from SIMULATOR.src.MOBILE_NODES.users import User
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
import math as m
import random as rd
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
import SIMULATOR.src.MATH_UTILS.formulas as f
from scipy.special import erf


def latency_estimation(current_user: User, target_bs: BaseStation, t_slot: float = 1):
    """
        Calculate theoretical propagation latency by estimating link budget and bandwidth without allocation planning.

        :param current_user: user who estimates the channel.
        :param target_bs: base station to which the channel is estimated.
        :param* t_slot: duration of the transmission pilot slot (in ms). Defaults to 1.

        :return [float] estimated_propagation_latency: estimated theoretical propagation latency (in seconds).
    """

    threshold = 90
    estimated_lambda_blockers = rd.uniform(0.1, 0.9)
    estimated_e_t_mean = 0.01
    e_w = 1 / estimated_lambda_blockers
    e_u = e_w * (m.exp(estimated_lambda_blockers * estimated_e_t_mean) - 1)
    e_t_los = e_w / (e_w + e_u)
    e_t_nlos = e_u / (e_w + e_u)
    e_tv = (e_t_los * e_t_nlos) / (e_t_los - e_t_nlos)

    rx_position = current_user.USER_position
    rx_height = current_user.USER_ue.UE_antenna.UEANTENNA_height
    tx_power = target_bs.BS_antenna.get_tx_power(rx_position, target_bs.BS_position, rx_height=rx_height, tx_height=target_bs.BS_antenna.ANTENNA_height)

    estimated_bandwidth = current_user.USER_ue.UE_antenna.UEANTENNA_bandwidth
    estimated_noise = -174 + 10 * m.log10(estimated_bandwidth * 1000000)

    distance = gf.euclidean_distance(rx_position, target_bs.BS_position, elevation_tx=target_bs.BS_antenna.ANTENNA_height, elevation_rx=rx_height)
    estimated_frequency = target_bs.BS_antenna.ANTENNA_frequency
    estimated_path_loss = 20 * m.log10((4 * m.pi * estimated_frequency * distance * 1000000000) / 3e8)

    estimated_delta = tx_power + estimated_noise - estimated_path_loss + threshold
    estimated_delta = f.to_units(estimated_delta)

    sigma = 1
    p_acc = (1 / 2) * (1 + erf(estimated_delta / m.sqrt(2 * sigma)))  # erf: error function
    estimated_propagation_latency = (t_slot - e_tv) / p_acc

    return estimated_propagation_latency


def capacity_estimation(current_user: User, target_bs: BaseStation, sinr: float):
    """
        Calculate theoretical capacity by estimating spectral efficiency and bandwidth without allocation planning.

        :param current_user: user who estimates the channel.
        :param target_bs: base station to which the channel is estimated.
        :param sinr: estimated signal-to-interference-plus-noise-ratio from receiver to transmitter (in dBm).

        :return [float] estimated_capacity: estimated maximum theoretical capacity (in Mbps).
    """

    rx_position = current_user.USER_position
    rx_height = current_user.USER_ue.UE_antenna.UEANTENNA_height
    n_rx = current_user.USER_ue.UE_antenna.UEANTENNA_nrx
    n_tx = target_bs.BS_antenna.get_ntx(rx_position, target_bs.BS_position, rx_height=rx_height, tx_height=target_bs.BS_antenna.ANTENNA_height)

    theoretical_capacity = Channel.spectral_efficiency_mimo(n_tx, n_rx, sinr)
    estimated_bandwidth = current_user.USER_ue.UE_antenna.UEANTENNA_bandwidth

    estimated_capacity = theoretical_capacity * estimated_bandwidth

    return estimated_capacity
