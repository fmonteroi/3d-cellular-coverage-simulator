# Class 'BS_PowerModel' (abstract), class 'AggregatedPowerConsumption'
# Created 06/04/2020 (version 4.0)
# Modified 10/03/2021 (version 6.0) - Jose Javier Rico Palomo

import configparser
import os
import sys
import json
from SIMULATOR.src.MATH_UTILS import formulas as f


class PowerModel:
    """
        Abstract class PowerModel.
        It models the power consumption of cellular network devices.
        The model can be BsPowerModel.

        Attributes
        ----------
        - PM_id [str]: power model identifier.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - energy_consumed (class method): it calculates the energy consumed by the network or a device in the simulation.
    """

    PM_id: str = ""  # Example = "POWERMODEL_1"

    def __str__(self):
        """
            'To-string' method of the abstract class 'PowerModel'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.PM_id

        return l1

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        power_model_data = dict()

        power_model_data["id"] = self.PM_id

        return power_model_data

    @classmethod
    def energy_consumed(cls, power_consumption: float, simulation_time: float):
        """
            It calculates the energy consumed by the network or a device in the simulation.

            :param power_consumption: power consumed by the network or device (in Kw).
            :param simulation_time: total simulation time (in seconds)

            :return [float] energy: energy consumed in the simulation (in Kwh)
        """

        energy = power_consumption / (simulation_time/3600)

        return energy


class BsPowerModel(PowerModel):
    """
        Abstract subclass BsPowerModel. Inheritance of abstract class 'PowerModel'.
        It models the power consumption of a base stations, load depending.
        The model can be E3F or AggregatedPowerConsumption.

        Attributes
        ----------
        - BSPM_bs_id [str]: base station identifier.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - energy_efficiency (class method): it calculates the energy efficiency KPI of the cellular network.
    """

    BSPM_bs_id: str = ""  # Example = "SMALL_BS_7"

    def __str__(self):
        """
            'To-string' method of the abstract subclass 'BsPowerModel'. Inheritance of abstract class 'PowerModel'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - BS id: " + self.BSPM_bs_id

        return l1 + "\n" + l2

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        power_model_data = super().to_dict()

        power_model_data["bs_id"] = self.BSPM_bs_id

        return power_model_data

    @classmethod
    def energy_efficiency(cls, datarate: float, power_consumption: float):
        """
            It calculates the energy efficiency KPI of the cellular network.
            The number of bits of information that can be reliably transmitted though the communication channel per energy unit.
            [REF] E. Björnson and E. G. Larsson, "How Energy-Efficient Can a Wireless Communication System Become?," 2018 52nd Asilomar Conference on Signals, Systems, and Computers, Pacific Grove, CA, USA, 2018, pp. 1252-1256

            :param datarate: capacity that has been circulated on the network or device (in Mbps).
            :param power_consumption: power consumed by the network or device (in Kw).

            :return [float] ee: energy efficiency taking into account load and consumption (in bits/joule).
        """

        ee = datarate*1000000 / power_consumption*1000

        return ee


class AggregatedPowerConsumption(BsPowerModel):
    """
        Subclass AggregatedPowerConsumption. Inheritance of abstract subclass 'BsPowerModel'.
        It simulates the Aggregated power consumption model of a BS, which takes into account the the load of the BS.

        Attributes
        ----------
        - APC_alpha: power transmission efficiency due to an RF amplifier and supply losses.
        - APC_beta: power dissipated due to signal processing.
        - APC_delta: dynamic power consumption per data unit constant.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - __get_model_parameters (private): it collects the parameters of the power consumption model according to the bs type.
        - power_consumption: it calculates the consumed power of the base station taking into account the load and the properties of the model.
    """

    APC_alpha: float = 0.0  # absolute units
    APC_beta: float = 0.0  # w
    APC_delta: float = 0.0  # w/Mbps

    def __init__(self, power_model_id: str, bs_id: str, config_file_path: str = "SIMULATOR/Configuration/model_config/power_models/"):
        """
            'Init' method of the subclass 'AggregatedPowerConsumption'. Inheritance of abstract class 'BsPowerModel'.
            Constructor. Parametrized the object according to the entered parameters.

            :param power_model_id: power consumption model identifier -> Example = "POWERMODEL_1".
            :param bs_id: base station identifier -> Example = "MACRO_BS_7".
            :param* config_file_path: path to the folder containing the configuration file of the power consumption model. Defaults to "SIMULATOR/Configuration/model_config/power_models/".
        """

        self.PM_id = power_model_id
        self.BSPM_bs_id = bs_id

        try:
            model_parameters = self.__get_model_parameters(config_file_path)

        except FileExistsError as e:  # Catch exception if occurs (if configuration file doesnt exist)
            print(e)
            sys.exit(3)

        self.APC_alpha = model_parameters["alpha"]
        self.APC_beta = model_parameters["beta"]
        self.APC_delta = model_parameters["delta"]

    def __str__(self):
        """
            'To-string' method of the subclass 'AggregatedPowerConsumption'. Inheritance of class 'BsPowerModel'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Power transmission efficiency due to an RF amplifier and supply losses (alpha): " + str(self.APC_alpha)
        l3 = " - Power dissipated due to signal processing (beta): " + str(self.APC_beta) + " watts"
        l4 = " - Dynamic power consumption per data unit constant (delta): " + str(self.APC_delta) + " w/Mbps."

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/SIMULATOR/Results/cellular_networks/base_stations/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the links. Defaults to "/SIMULATOR/Results/".
        """

        data_dump = dict()
        link_data = super().to_dict()

        link_data["alpha"] = str(self.APC_alpha)
        link_data["beta"] = str(self.APC_beta)
        link_data["delta"] = str(self.APC_delta)

        data_dump[time] = link_data

        with open(file_path + self.BSPM_bs_id + "/" + self.PM_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __get_model_parameters(self, file_path: str):
        """
            It collects the parameters of the power consumption model according to the bs type.

            :param file_path: path to the folder containing the configuration file of the power consumption model.

            :return [dict] parameters: parameters for configuring the power consumption model.

            :raise FileNotFoundError: occurs when the file you want to access does not exist.
        """

        parameters = dict()

        file_name = "aggregated_power_consumption_model"

        # Open the file in read by tokens mode
        config_file = configparser.ConfigParser()

        if os.path.isfile(file_path + file_name):  # Check if file exist
            config_file.read(file_path + file_name)
        else:  # If doest exist, raise and exception
            raise FileNotFoundError(file_path + file_name)

        # Read and collect the parameters
        parameters["alpha"] = float(config_file[self.BSPM_bs_id.split("_")[0]+"_CELL"]['alpha'])
        parameters["beta"] = float(config_file[self.BSPM_bs_id.split("_")[0]+"_CELL"]['beta'])
        parameters["delta"] = float(config_file[self.BSPM_bs_id.split("_")[0]+"_CELL"]['delta'])

        return parameters

    def power_consumption(self, tx_power: float, load: float, ro: float = 0.0):
        """
            It calculates the consumed power of the base station taking into account the load and the properties of the model.

            :param tx_power: transmitter power of the base station (in dBm).
            :param load: capacity consumed by the base station (in Mbps).
            :param ro: power consumption of a fibre optic SCP transceiver (watts).

            :return [float] power_consumed: consumed power of the base station (watts).
        """

        tx_power_units = f.to_units(tx_power)
        # ? import statistics as st
        # ? mean_load = st.mean(list(load))  # average load of the entire simulation

        power_consumed = self.APC_alpha*tx_power_units + self.APC_beta + self.APC_delta*load + ro

        return power_consumed

