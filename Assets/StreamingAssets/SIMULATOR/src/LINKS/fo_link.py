# Class 'FOLink'
# Created 03/03/2020 (version 3.0)
# Modified 02/02/2021 (version 6.0) - Jose Javier Rico Palomo

import configparser
import os
import math as m
import sys
from SIMULATOR.src.LINKS.link import Link
from typing import *
import json


class FOLink(Link):
    """
        Subclass FOLink. Inheritance of class 'Link'.
        It simulates the behavior of a link between two devices though a fiber optic technology.

        Attributes
        ----------
        - FOLINK_distance [float] (private): distance of the fibre optic cable.
        - FOLINK_model [str] (private): fibre optic link pattern.
        - __system_margin [float] (private): power margin of the fibre optic link.
        - __attenuation [float] (private): fibre line attenuation as a function of distance. It is given by the operating window.
        - __n_splices [int] (private): number of intermediate devices.
        - __splice_loss [float] (private): losses introduced by the intermediate devices.
        - __window [str] (private): fibre line operating window.
        - __t_mod [float] (private): intermodal dispersion time in multimode fibre.
        - __t_cd [float] (private): chromatic dispersion time.
        - __t_pmd [float] (private): polarisation mode dispersion time.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __get_model_parameters (private): it collects the parameters of the link according to the model chosen when creating the object.
        - calculate_losses: it calculates the link losses based on characteristic parameter of the model.
        - calculate_rx_power: it calculates the link budget of the link. The receiver power is function of transmitter power, losses and sensibility of the receiver.
        - calculate_rise_time: it calculates the rise time (propagation latency in optic fiber) of the link.
    """

    FOLINK_distance: float = 0.0  # m
    FOLINK_model: str = ""  # "DIGITAL_MONOMODE" / "DIGITAL_MULTIMODE"
    __system_margin: float = 0.0  # dB
    __attenuation: float = 0.0  # dB/m
    __n_splices: int = 0  # absolute units
    __splice_loss: float = 0.0  # dB
    __window: str = ""  # "FIRST", "SECOND", "THIRD"
    __t_mod: float = 0.0  # s
    __t_cd: float = 0.0  # s
    __t_pmd: float = 0.0  # s

    def __init__(self, link_id: str, source_id: str, peer_id: str, link_type: str, capacity: float, assigned_bandwidth: float, link_distance: float, window: str, fo_model: str, system_margin=0.0, active_connections: List[str] = None, model_parameters: dict = None, config_file_path: str = "SIMULATOR/Configuration/model_config/optic_fiber/", tx_rx_rise_time=11e-8):
        """
            'Init' method of the subclass 'FOLink'. Inheritance of class 'Link'.
            Constructor. Parametrized the object according to the entered parameters.

            :param link_id: link identifier -> Example = "FOLINK_1".
            :param source_id: origin device identifier of the link -> Example = "ROUTER_7".
            :param peer_id: destination device identifier of the link -> Example = "BS_2".
            :param link_type: type of link depending on the network it is on -> "ue" / "fronthaul" / "backhaul".
            :param capacity: maximum capacity on the link at the time it was created (in Mbps).
            :param assigned_bandwidth: assigned bandwidth to the link (in MHz).
            :param link_distance: distance of the fiber optic link (in meters).
            :param window: power margin of the fibre optic link -> "DIGITAL_MONOMODE" / "DIGITAL_MULTIMODE".
            :param fo_model: fibre line operating window -> "FIRST", "SECOND", "THIRD".
            :param* system_margin: power margin of the fibre optic link (in dB). Defaults to 0.
            :param* active_connections: identifier of the active connections in the link -> Example = ["CONN_1", "CONN_2"]. Defaults to None.
            :param* model_parameters: predefined parameters for configuring the optic fiber. Defaults to None.
            :param* config_file_path: path to the folder containing the configuration file of the optic fiber models. Defaults to "SIMULATOR/Configuration/model_config/optic_fiber".
            :param* tx_rx_rise_time: rise time of the receiver and transmitter device (in seconds). Defaults to 11ns.
        """

        try:
            fo_parameters = self.__get_model_parameters(config_file_path) if model_parameters is None else model_parameters

        except FileExistsError as e:  # Catch exception if occurs (if configuration file doesnt exist)
            print(e)
            sys.exit(3)

        self.__attenuation = fo_parameters["attenuation"]
        self.__n_splices = m.ceil(self.FOLINK_distance / fo_parameters["distance_per_splice"])
        self.__splice_loss = fo_parameters["splice_loss"]
        self.__t_mod = fo_parameters["t_mod"]
        self.__t_cd = fo_parameters["t_cd"]
        self.__t_pmd = fo_parameters["t_pmd"]

        fo_latency = self.calculate_rise_time(tx_rx_rise_time, tx_rx_rise_time) + (link_distance/300000000)

        super().__init__(link_id, source_id, peer_id, link_type, assigned_bandwidth, capacity=capacity, latency=fo_latency, active_connections=active_connections)
        self.FOLINK_distance = link_distance
        self.__window = window
        self.FOLINK_model = fo_model
        self.__system_margin = system_margin

    def __str__(self):
        """
            'To-string' method of the subclass 'FOLink'. Inheritance of class 'Link'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Distance: " + str(self.FOLINK_distance) + " m."
        l3 = " - Model: " + self.FOLINK_model + "."
        l4 = " - System margin: " + str(self.__system_margin) + " dB."
        l5 = " - Attenuation: " + str(self.__attenuation) + " dB/km."
        l6 = " - Number of splices: " + str(self.__n_splices) + "."
        l7 = " - Operation window: " + self.__window + "."
        l8 = " - Inter-modal dispersion time: " + str(self.__t_mod) + " s."
        l9 = " - Chromatic dispersion time: " + str(self.__t_cd) + " s."
        l10 = " - Polarization mode dispersion time: " + str(self.__t_pmd) + " s."

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7 + "\n" + l8 + "\n" + l9 + "\n" + l10

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the links. Defaults to "/SIMULATOR/Results/".
        """

        sub_path = ""
        data_dump = dict()
        link_data = super().to_dict()

        link_data["distance"] = self.FOLINK_distance
        link_data["model"] = self.FOLINK_model
        link_data["system_margin"] = self.__system_margin
        link_data["attenuation"] = self.__attenuation
        link_data["n_splices"] = self.__n_splices
        link_data["splice_loss"] = self.__splice_loss
        link_data["window"] = self.__window
        link_data["t_mod"] = self.__t_mod
        link_data["t_cd"] = self.__t_cd
        link_data["t_pmd"] = self.__t_pmd

        data_dump[time] = link_data

        if self.LINK_type == "backhaul":
            sub_path = "/cellular_network/backhaul/links/"
        elif self.LINK_type == "fronthaul":
            sub_path = "/access_network/fronthaul/links/"
        elif self.LINK_type == "ue":
            sub_path = "/users/user_equipment/links/"

        with open(file_path + sub_path + self.LINK_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __get_model_parameters(self, file_path: str):
        """
            It collects the parameters of the link according to the model chosen when creating the object.

            :param file_path: path to the folder containing the configuration file of the optic fiber models.

            :return [dict] parameters: parameters for configuring the optic fiber.

            :raise FileNotFoundError: occurs when the file you want to access does not exist.
        """

        parameters = dict()

        file_name = "FO_" + self.FOLINK_model  # Example = "FO_DIGITAL_MONOMODE".

        # Open the file in read by tokens mode
        config_file = configparser.ConfigParser()

        if os.path.isfile(file_path + file_name):  # Check if file exist
            config_file.read(file_path + file_name)
        else:  # If doest exist, raise and exception
            raise FileNotFoundError(file_path + file_name)

        # Read and collect the parameters
        parameters["attenuation"] = float(config_file[self.__window + "_WINDOW"]['alpha'])
        parameters["distance_per_splice"] = float(config_file[self.__window + "_WINDOW"]['distance_per_splice'])
        parameters["splice_loss"] = float(config_file[self.__window + "_WINDOW"]['splice_loss'])
        parameters["t_mod"] = float(config_file[self.__window + "_WINDOW"]['t_mod'])
        parameters["t_cd"] = float(config_file[self.__window + "_WINDOW"]['t_cd'])
        parameters["t_pmd"] = float(config_file[self.__window + "_WINDOW"]['t_pmd'])

        return parameters

    def calculate_losses(self, connector_loss: float):
        """
            It calculates the link losses based on characteristic parameter of the model.

            :param connector_loss: losses of the SCP fiber connector (in dB).

            :return [float] losses: total losses of the fiber line (in dB).
        """

        attenuation_losses = self.__attenuation*(self.FOLINK_distance/1000)
        total_splices_losses = self.__n_splices * self.__splice_loss
        other_losses = 0  # No defined

        losses = 2*connector_loss + attenuation_losses + total_splices_losses + other_losses + self.__system_margin

        return losses

    def calculate_rx_power(self, p_tx: float, connector_loss: float, rx_sensitivity: float):
        """
            It calculates the link budget of the link. The receiver power is function of transmitter power, losses and sensibility of the receiver.

            :param p_tx: transmitter power (in dBm).
            :param connector_loss: losses of the SCP fiber connector (in dB).
            :param rx_sensitivity: minimum sensibility of the receiver or gain (in dB).

            :return [float] p_rx: detected power in the link receiver (in dBm).
        """

        p_rx = p_tx + rx_sensitivity + self.calculate_losses(connector_loss)

        return p_rx

    def calculate_rise_time(self, t_tx: float, t_rx: float):
        """
            It calculates the rise time (propagation latency in optic fiber) of the link.
            Determine the dispersion limitation in a optic fiber link.

            :param  t_tx: consumed time by the transmitter (in seconds).
            :param  t_rx: consumed time by the receiver (in seconds).

            :return [float] t_sys: consumed time for the signal propagation in a optic fiber link (in seconds).
        """
        
        t_sys = m.sqrt(t_tx**2 + self.__t_mod**2 + self.__t_cd**2 + self.__t_pmd**2 + t_rx**2)

        return t_sys
