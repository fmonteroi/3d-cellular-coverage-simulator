# Module 'link_generation'
# Created 27/04/2021 (version 6.0)
# Modified 03/05/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.LINKS.rf_link import RFLink
from SIMULATOR.src.LINKS.fo_link import FOLink
from SIMULATOR.src.LINKS.link import Link
import random as rd
import SIMULATOR.src.GEOMETRY.link_planifications as lp
from SIMULATOR.src.ACCESS_NETWORK.network_device import Router
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.MOBILE_NODES.users import User
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import BaseStation
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound
from typing import *


def generate_links(link_id: str, device_source: Union[Router, User, BaseStation], device_peer: Union[Router, User, BaseStation], link_type: str, technology: str, simulation_map: SimulationMap = None, link_parameters: dict = None, base_stations: Dict[str, BaseStation] = None):
    """
        It generates a link given the source and destination devices and some parameters.

        :param link_id: link identifier -> Example = "LINK_1".
        :param device_source: origin device object of the link -> Example = "UE_7".
        :param device_peer: destination device object of the link -> Example = "BS_2".
        :param link_type: type of link depending on the network it is on -> "ue" / "fronthaul" / "backhaul".
        :param technology: technology used in the link -> "ue" / "fronthaul" / "backhaul".
        :param* simulation_map: generated map por the simulation. Defaults to None.
        :param* link_parameters: link configuration. The dictionary values and keys must be different depending on the link to be created. Defaults to None.
        :param* base_stations: base stations generated for the simulations.

        :return [Object (SIMULATOR.Link)]: generated link.

        :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
    """

    # Select source id (depending on the object that arrives by parameter)
    if device_source.__class__.__name__ == "Router":
        source_id = device_source.ND_id
        rx_position = 0
    elif device_source.__class__.__name__ in ["MacroBS", "SmallBS"]:
        source_id = device_source.BS_id
        rx_position = device_source.BS_position
    elif device_source.__class__.__name__ == "UserEquipment":
        source_id = device_source.USER_id
        rx_position = device_source.USER_position
    else:  # If class name is unknown, raise an exception
        raise ConfigurationNotFound(device_source.__class__.__name__)

    # Select peer id (depending on the object that arrives by parameter)
    if device_peer.__class__.__name__ == "Router":
        peer_id = device_peer.ND_id
        tx_position = 0
    elif device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
        peer_id = device_peer.BS_id
        tx_position = device_peer.BS_position
    elif device_peer.__class__.__name__ == "UserEquipment":
        peer_id = device_peer.USER_id
        tx_position = device_peer.USER_position
    else:  # If class name is unknown, raise an exception
        raise ConfigurationNotFound(device_peer.__class__.__name__)

    if technology == "EMPTY":
        link = Link(link_id, source_id, peer_id, link_type, link_parameters["capacity"], 0)

    elif technology == "RF":

        # Select source parameters
        if device_source.__class__.__name__ in ["MacroBS", "SmallBS"]:
            n_rx = device_source.BS_antenna.get_ntx(rx_position, tx_position)
            tx_height = device_source.BS_antenna.ANTENNA_height
            frequency = device_source.BS_antenna.get_frequency(rx_position, tx_position)
        elif device_source.__class__.__name__ == "UserEquipment":
            n_rx = device_source.USER_ue.UE_antenna.UEANTENNA_nrx
            tx_height = device_source.USER_ue.UE_antenna.UEANTENNA_height
            frequency = 0  # * device_source.USER_ue.UE_antenna.UEANTENNA_frequency
        else:  # If class name is unknown, raise an exception
            raise ConfigurationNotFound(device_source.__class__.__name__)

        # Select peer parameters
        if device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
            n_tx = device_peer.BS_antenna.get_ntx(rx_position, tx_position)
            tx_power = device_peer.BS_antenna.get_tx_power(rx_position, tx_position)
            rx_height = device_source.BS_antenna.ANTENNA_height
        elif device_peer.__class__.__name__ == "UserEquipment":
            n_tx = device_peer.USER_ue.UE_antenna.UEANTENNA_nrx
            tx_power = 0  # * tx_power = device_peer.USER_ue.UE_antenna.UEANTENNA_tx_power
            rx_height = device_source.USER_ue.UE_antenna.UEANTENNA_height
        else:  # If class name is unknown, raise an exception
            raise ConfigurationNotFound(device_peer.__class__.__name__)

        if device_source.__class__.__name__ in ["MacroBS", "SmallBS"] and device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
            bandwidth = -1
            for current_antenna in device_source.BS_backhaul_block.BB_links.keys():
                if device_source.BS_backhaul_block.BB_links[current_antenna] == link_id:
                    bandwidth = device_source.BS_backhaul_block.BB_assigned_bandwidth[current_antenna]
        elif device_source.__class__.__name__ in ["MacroBS", "SmallBS"] and device_peer.__class__.__name__ == "UserEquipment":
            bandwidth = device_source.BS_node.NODEB_assigned_bandwidth[device_peer.USER_id]
        elif device_source.__class__.__name__ == "UserEquipment" and device_peer.__class__.__name__ == "UserEquipment":
            bandwidth = device_source.USER_ue.UE_antenna.UEANTENNA_bandwidth
        elif device_source.__class__.__name__ == "UserEquipment" and device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
            bandwidth = device_source.USER_ue.UE_antenna.UEANTENNA_bandwidth
        else:  # If class name is unknown, raise an exception
            raise ConfigurationNotFound("device_source.__class__.__name__ or device_peer.__class__.__name__")

        current_weighted_channels = Channel.weight_channels(tx_position, rx_position, simulation_map, tx_height=tx_height, rx_height=rx_height)
        current_losses = Channel.weight_losses(current_weighted_channels, frequency, simulation_map)

        if device_source.__class__.__name__ in ["MacroBS", "SmallBS"] and device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
            best_bs_id, sinrs = lp.sinr_schedule_backhaul(device_source, base_stations, simulation_map)
            current_sinr = sinrs[device_peer.BS_id]

        elif device_source.__class__.__name__ == "UserEquipment" and device_peer.__class__.__name__ in ["MacroBS", "SmallBS"]:
            best_bs_id, sinrs = lp.sinr_schedule_dl(device_peer, base_stations, simulation_map, threshold=link_parameters["sinr_threshold"])
            current_sinr = sinrs[device_peer.USER_id]

        else:  # If class name is unknown, raise an exception
            raise ConfigurationNotFound("device_source.__class__.__name__ or device_peer.__class__.__name__")

        link = RFLink(link_id, link_type, link_parameters["latency_model"], source_id, n_tx, tx_power, peer_id, n_rx, bandwidth, link_parameters["t_slot"], current_weighted_channels, current_losses, current_sinr)

    elif technology == "FO":
        distance = rd.randint(link_parameters["FO"]["min_distance"], link_parameters["FO"]["max_distance"])  # Calculate random resources (from min to max)
        link = FOLink(link_id, source_id, peer_id, link_type, link_parameters["FO"]["capacity"], link_parameters["FO"]["bandwidth"], distance, link_parameters["FO"]["window"], link_parameters["FO"]["model"], system_margin=link_parameters["FO"]["system_margin"])

    else:
        raise ConfigurationNotFound("technology")

    return link
