# Class 'latency_model' (abstract)
# Created 19/10/2020 (version 5.0)
# Modified 09/03/2021 (version 6.0) - Jose Javier Rico Palomo

import sys
import configparser
import os
import math as m
from scipy.special import erf
import random as rd
import SIMULATOR.src.MATH_UTILS.formulas as f


class LatencyModel:
    """
        Class 'LatencyModel'.
        It models link latency, i.e, the time it takes for connections to get from the sender to the receiver.
        This time is used as a penalty in simulations (the higher the latency, the poorer the link quality).

        Attributes
        ----------
        - LM_id [str]: latency model identifier.
        - __model (private) [str]: mathematical model of latency.
        - __mu (private) [float]: server response time (nodeb of base station).
        - __beta (private) [float]: beta (absolute units).
        - __sigma (private) [float]: standard deviation (absolute units).

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - __get_model_parameters (private): it collects the parameters of the scenario according to the model chosen when creating the object.
        - get_latency: it calculates the latency by the 3-times model.
        - get_propagation_latency: it calculates only the propagation latency by the 3-times model.
    """

    LM_id: str = ""  # Example = "LATENCYMODEL_1"
    __model: str = ""  # "3_times"
    __mu: float = 0.0  # absolute units
    __beta: float = 0.0  # absolute units
    __sigma: float = 0.0  # absolute units

    def __init__(self, model_id: str, model: str = "3_times", model_parameters: dict = None, config_file_path: str = "SIMULATOR/Configuration/model_config/latency/"):
        """
            'Init' method of the class 'LatencyModel'.
            Constructor. Parametrized the object according to the entered parameters.

            :param model_id: latency model identifier -> Example = "LATENCYMODEL_1".
            :param* model: mathematical model of latency -> "3_times". Defaults to "3_times".
            :param* model_parameters: predefined parameters for configuring the latency model. Defaults to None.
            :param* config_file_path: path to the folder containing the configuration file of the latency models. Defaults to "SIMULATOR/Configuration/model_config/latency/".

            :except FileExistsError: THE PROGRAM WILL EXIT IF 'FILE EXIST ERROR' EXCEPTIONS OCCURS (file in 'SIMULATOR/Configuration/model_config/latency/').
        """

        self.LM_id = model_id
        self.__model = model

        try:
            model_parameters = self.__get_model_parameters(config_file_path) if model_parameters is None else model_parameters
            self.__mu = model_parameters["mu"]
            self.__beta = model_parameters["beta"]
            self.__sigma = model_parameters["sigma"]

        except FileExistsError as e:  # Catch exception if occurs (if configuration file doesnt exist)
            print(e)
            sys.exit(3)

    def __str__(self):
        """
            'To-string' method of the class 'LatencyModel'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.LM_id
        l2 = " - Model: " + self.__model
        l3 = " - Response server time: " + str(self.__mu)
        l4 = " - Beta: " + str(self.__beta)
        l5 = " - Standard deviation: " + str(self.__sigma)

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        latency_data = dict()

        latency_data["model"] = self.__model
        latency_data["mu"] = self.__mu
        latency_data["beta"] = self.__beta
        latency_data["sigma"] = self.__sigma

        return latency_data

    def __get_model_parameters(self, file_path: str):
        """
            It collects the parameters of the latency model according to the parameters chosen when creating the object.

            :param file_path: path to the folder containing the configuration file of the latency models.

            :return [dict] parameters: parameters for configuring the latency model.

            :raise FileNotFoundError: occurs when the file you want to access does not exist.
        """

        parameters = dict()

        file_name = "latency_models"

        # Open the file in read by tokens mode
        config_file = configparser.ConfigParser()

        if os.path.isfile(file_path + file_name):  # Check if file exist
            config_file.read(file_path + file_name)
        else:  # If doest exist, raise and exception
            raise FileNotFoundError(file_path + file_name)

        # Read and collect the parameters
        parameters["mu"] = float(config_file[self.__model]["mu"])
        parameters["beta"] = float(config_file[self.__model]["beta"])
        parameters["sigma"] = float(config_file[self.__model]["sigma"])

        return parameters

    def get_latency(self, t_slot: float, tx_power: float, bandwidth: float, path_loss: float):
        """
            It calculates the latency by the 3-times model.
            [REF] D. A. Chekired, M. A. Togou, L. Khoukhi and A. Ksentini, "5G-Slicing-Enabled Scalable SDN Core Network: Toward an Ultra-Low Latency of Autonomous Driving Service," in IEEE Journal on Selected Areas in Communications, vol. 37, no. 8, pp. 1769-1782, Aug. 2019.

            :param t_slot: slot time defined by 5G standard (in seconds).
            :param tx_power: transmission power (in dBm).
            :param bandwidth: assigned bandwidth to link (in MHz).
            :param path_loss: link path losses (in dB).

            :return [float] lat_3times: latency of the link by 3-times model (in seconds).
        """

        # Propagation latency
        t_prop = self.get_propagation_latency(t_slot, tx_power, bandwidth, path_loss)

        # Processing (handling) time
        t_hand = 1 / (self.__mu * (1 - self.__beta))

        # Queue (tail) waiting time
        t_tail = self.__beta / (self.__mu * (1 - self.__beta))

        lat_3times = t_prop + t_hand + t_tail

        return lat_3times

    def get_propagation_latency(self, t_slot: float, tx_power: float, bandwidth: float, path_loss: float, lambda_blockers_max: float = 0.9, e_t_mean: float = 0.01):
        """
            It calculates only the propagation latency by the 3-times model.
            [REF] D. A. Chekired, M. A. Togou, L. Khoukhi and A. Ksentini, "5G-Slicing-Enabled Scalable SDN Core Network: Toward an Ultra-Low Latency of Autonomous Driving Service," in IEEE Journal on Selected Areas in Communications, vol. 37, no. 8, pp. 1769-1782, Aug. 2019.
            [REF] M. Gapeyenko et al., "On the Temporal Effects of Mobile Blockers in Urban Millimeter-Wave Cellular Scenarios," in IEEE Transactions on Vehicular Technology, vol. 66, no. 11, pp. 10124-10138, Nov. 2017, doi: 10.1109/TVT.2017.2754543.

            :param t_slot: slot time defined by 5G standard (in seconds).
            :param tx_power: transmission power (in dBm).
            :param bandwidth: assigned bandwidth to link (in MHz).
            :param path_loss: link path losses (in dB).
            :param* lambda_blockers_max: lambda parameter of mobile blockers (try between 0.1 and 0.9). Defaults to 0.9.
            :param* e_t_mean: medium blocking time (it is not known where it comes from). Defaults to 0.01.

            :return [float] t_prop: propagation latency of the link by 3-times model (in seconds).
        """

        threshold = 90
        lambda_blockers = rd.uniform(0.1, lambda_blockers_max)

        # Mobile blockers
        e_w = 1 / lambda_blockers
        e_u = e_w * (m.exp(lambda_blockers * e_t_mean) - 1)

        # LOS and NLOS time of the link
        e_t_los = e_w / (e_w + e_u)
        e_t_nlos = e_u / (e_w + e_u)

        # Distribution blocking time
        e_tv = (e_t_los * e_t_nlos) / (e_t_los - e_t_nlos)

        noise = -174 + 10 * m.log10(bandwidth * 1000000)  # tau_o * BW

        # Simplified link budget
        delta = tx_power + noise - path_loss + threshold
        delta = f.to_units(delta)

        # Service probability
        p_acc = (1 / 2) * (1 + erf(delta / m.sqrt(2 * self.__sigma)))  # erf: error function

        # Propagation latency
        t_prop = (t_slot - e_tv) / p_acc

        return t_prop
