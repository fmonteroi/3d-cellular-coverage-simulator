# Class 'RFLink'
# Created 03/03/2020 (version 3.0)
# Modified 02/02/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.LINKS.link import Link
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
from SIMULATOR.src.MODELS.latency_models import LatencyModel
from typing import *
import json


class RFLink(Link):
    """
        Subclass RFLink. Inheritance of class 'Link'.
        It simulates the behavior of a link between two devices though a radio frequency technology.

        Attributes
        ----------
        - RFLINK_weighted_channels [list of tuples of objects (SIMULATOR.Channel) and floats]: channels through which the link passes and distances (in meters) travelled on each channel.
        - RFLINK_latency_model [object (SIMULATOR.LatencyModel)]: latency model of the link.
        - __sinr [float]: signal-to-interference-plus-noise-ratio level of the link.
        - __path_losses [float]: free space losses in the channel.
        - __spectral_efficiency [float]: theoretical mean capacity of the link.
        - __propagation_latency [float]: propagation latency of the link.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - calculate_capacity: it calculates the channel capacity the link capacity according to the appropriate model.
        - get_path_loss: it returns the existing free space losses in the RF link.
        - get_sinr: it returns the existing signal-to-interference-plus-noise-ratio in the RF link.
        - get_propagation_latency: it returns the existing propagation latency in the RF link.
    """

    RFLINK_weighted_channels: List[Tuple[str, float]] = []  # [(CHANNEL_1, d1), (CHANNEL_2, d2), ...]
    RFLINK_latency_model: LatencyModel = None
    __sinr: float = 0.0  # dBm
    __path_losses: float = 0.0  # dB
    __spectral_efficiency: float = 0.0  # bps/Hz
    __propagation_latency: float = 0.0  # ms

    def __init__(self, link_id: str, link_type: str, latency_model: LatencyModel, tx_id: str, n_tx: int, tx_power: float, rx_id: str, n_rx: int, assigned_bandwidth: float, t_slot: float, weighted_channels: list, losses: float, sinr: float, throughput: float = 0.0, active_connections: List[str] = None):
        """
            'Init' method of the subclass 'RFLink'. Inheritance of class 'Link'.
            Constructor. Parametrized the object according to the entered parameters.

            :param link_id: link identifier -> Example = "LINK_1".
            :param link_type: type of link depending on the network it is on -> "ue" / "fronthaul" / "backhaul" / "layer3".
            :param tx_id: transmitter device identifier -> Example = "SMALL_BS_4".
            :param n_tx: number of transmitter antennas (mimo).
            :param tx_power: transmitter power (in dBm).
            :param rx_id: receiver device identifier -> Example = "UE_9".
            :param n_rx: number of receiver antennas (mimo).
            :param assigned_bandwidth: assigned bandwidth to the link (in MHz).
            :param t_slot: slot time defined by 5G standard (in seconds).
            :param weighted_channels: weighted channels between the transmitter and receiver -> keys channels_id and values distance.
            :param losses: free space losses of the link (in dB).
            :param sinr: signal-to-interference-plus-noise-ratio level of the link (in dBm).
            :param* throughput: capacity consumed by data passing through the link (in Mbps). Defaults to 0.
            :param* active_connections: identifier of the active connections in the link -> Example = ["CONN_1", "CONN_2"]. Defaults to None.
        """

        self.RFLINK_latency_model = latency_model
        self.RFLINK_weighted_channels = weighted_channels
        self.__path_losses = losses
        self.__sinr = sinr
        self.__spectral_efficiency = Channel.spectral_efficiency_mimo(n_tx, n_rx, self.__sinr) if n_tx > 1 and n_rx > 1 else 0

        link_capacity = self.calculate_capacity(assigned_bandwidth, self.__sinr, self.__spectral_efficiency)
        link_latency = self.RFLINK_latency_model.get_latency(t_slot, tx_power, assigned_bandwidth, self.__path_losses)
        self.__propagation_latency = self.RFLINK_latency_model.get_propagation_latency(t_slot, tx_power, assigned_bandwidth, self.__path_losses)

        super().__init__(link_id, rx_id, tx_id, link_type, assigned_bandwidth, throughput=throughput, capacity=link_capacity, latency=link_latency, active_connections=active_connections)

    def __str__(self):
        """
            'To-string' method of the subclass 'RFLink'. Inheritance of class 'Link'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - Latency model: " + self.RFLINK_latency_model.LM_id
        l3 = " - SINR: " + str(self.__sinr) + " dBm"
        l4 = " - Path losses: " + str(self.__path_losses) + " dB"
        l5 = " - Spectral efficiency: " + str(self.__spectral_efficiency) + " bps/Hz"
        l6 = " - Weighted channels: " + str(self.RFLINK_weighted_channels)

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the links. Defaults to "/SIMULATOR/Results/".
        """

        sub_path = ""
        data_dump = dict()
        link_data = super().to_dict()

        link_data["latency_model"] = self.RFLINK_latency_model.LM_id
        link_data["sinr"] = self.__sinr
        link_data["path_loss"] = self.__path_losses
        link_data["spectral_efficiency"] = self.__spectral_efficiency
        link_data["weighted_channels"] = str(self.RFLINK_weighted_channels)

        data_dump[time] = link_data

        if self.LINK_type == "backhaul":
            sub_path = "/cellular_network/backhaul/links/"
        elif self.LINK_type == "fronthaul":
            sub_path = "/access_network/fronthaul/links/"
        elif self.LINK_type == "ue":
            sub_path = "/users/user_equipment/links/"
        elif self.LINK_type == "layer3":
            sub_path = "/access_network/links/"

        with open(file_path + sub_path + self.LINK_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def get_path_loss(self):
        """
            Returns the existing free space losses in the RF link.

            :return [float] path_losses: path loss (in dB).
        """

        return self.__path_losses

    def get_sinr(self):
        """
            Returns the existing signal-to-interference-plus-noise-ratio in the RF link.

            :return [float] SINR: signal-to-interference-plus-noise-ratio (in dBm).
        """

        return self.__sinr

    def get_propagation_latency(self):
        """
            Returns the existing propagation latency in the RF link.

            :return [float] latency: propagation latency (in ms).
        """

        return self.__propagation_latency

    @staticmethod
    def calculate_capacity(bandwidth: float, sinr: float, spectral_efficiency: float):
        """
            It calculates the channel capacity the link capacity according to the appropriate model.
            If both antennas have only 1 transmitter, the Shannon formula shall be used for the capacity calculation (spectral efficiency equal to 1).
            If either antenna has more than 1 transmitter, the mimo antenna formula shall be used for the capacity calculation (spectral efficiency bigger than 1).

            :param bandwidth: assigned bandwidth to the link (in MHz).
            :param sinr: signal-to-interference-plus-noise-ratio level of the link (in dB).
            :param spectral_efficiency: theoretical mean capacity of the link (in bps/Hz).

            :return [float] capacity: maximum capacity supported by the link (in Mbps).
        """

        capacity = 0

        if spectral_efficiency == 1:
            capacity = Channel.capacity_shannon(sinr, bandwidth)

        elif spectral_efficiency > 1:
            capacity = spectral_efficiency * bandwidth  # data rate

        return capacity
