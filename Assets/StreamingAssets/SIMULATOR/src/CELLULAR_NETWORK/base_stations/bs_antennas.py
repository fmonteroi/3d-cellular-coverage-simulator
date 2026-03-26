# Class 'BSAntenna'
# Created 20/05/2018 (version 1.0)
# Modified 21/04/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *
from SIMULATOR.src.CODE_UTILS.exceptions import ConfigurationNotFound
from SIMULATOR.src.MODELS.power_models import PowerModel
from SIMULATOR.src.MODELS.economic_models import EconomicModel
from SIMULATOR.src.MATH_UTILS import formulas as f
from SIMULATOR.src.GEOMETRY import geometry_formulas as gf
from SIMULATOR.src.CODE_UTILS import sorted_keys as sk
import json
import sys
import math as m
import scipy.io
import numpy as np


class AntennaBeam:
    """
        Class AntennaBeam.
        It simulates the behaviour of a radiation lobe of a directional antenna.
        The radiation pattern is predefined by a matrix (from 0º to 360º), usually measured in an anechoic chamber.

        Attributes
        ----------
        - BEAM_id [str]: beam identifier.
        - BEAM_width_z [float]: with of the lobe in the Z-axis.
        - BEAM_width_y [float]: with of the lobe in the Y-axis.
        - BEAM_main_azimuth [float]: azimuth angle of the beam that mark its position with respect to the antenna coordinate axis.
        - BEAM_max_range_azimuth [float]: maximum beam range angle.
        - BEAM_min_range_azimuth [float]: minimum beam range angle.
        - BEAM_p_tx [float]: transmitter power of the beam.
        - BEAM_gain [float]: gain of the beam.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - beam_width (class): calculate the beam widths (in Z and Y directions) of an array of antennas.
    """

    BEAM_id: str = ""  # Example = "BEAM_1"
    BEAM_width_z: float = 0.0  # deg
    BEAM_width_y: float = 0.0  # deg
    BEAM_main_azimuth: float = 0.0  # deg
    BEAM_max_range_azimuth: float = 0.0  # deg
    BEAM_min_range_azimuth: float = 0.0  # deg
    BEAM_p_tx: float = 0.0  # dBm
    BEAM_gain: float = 0.0  # dBi

    def __init__(self, beam_id: str, width_z: float, width_y: float, max_range_azimuth: float, min_range_azimuth: float, p_tx: float, gain: float):
        """
            'Init' method of the class 'AntennaBeam'.
            Constructor. Parametrized the object according to the entered parameters.

            :param beam_id: beam identifier -> Example = "BEAM_1".
            :param width_z: with of the lobe in the Z-axis (in degrees).
            :param width_y: with of the lobe in the Y-axis (in degrees).
            :param max_range_azimuth: maximum beam range angle (in degrees).
            :param min_range_azimuth: minimum beam range angle (in degrees).
            :param p_tx: transmitter power of the beam (in dBm).
            :param gain: gain of the beam (in dBi).
        """

        self.BEAM_id = beam_id
        self.BEAM_width_z = width_z
        self.BEAM_width_y = width_y
        self.BEAM_max_range_azimuth = max_range_azimuth
        self.BEAM_min_range_azimuth = min_range_azimuth
        self.BEAM_main_azimuth = self.BEAM_min_range_azimuth + (self.BEAM_max_range_azimuth+self.BEAM_min_range_azimuth/2)
        self.BEAM_p_tx = p_tx
        self.BEAM_gain = gain

    def __str__(self):
        """
            'To-string' method of the class 'AntennaBeam'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.BEAM_id
        l2 = " - Z beam width: " + str(self.BEAM_width_z) + " degrees"
        l3 = " - Y beam width: " + str(self.BEAM_width_y) + " degrees"
        l4 = " - Main azimuth: " + str(self.BEAM_main_azimuth) + " degrees"
        l5 = " - Max scanning range (in azimuth): " + str(self.BEAM_max_range_azimuth) + " degrees"
        l6 = " - Min scanning range (in azimuth): " + str(self.BEAM_min_range_azimuth) + " degrees"
        l7 = " - Transmitter power: " + str(self.BEAM_p_tx) + " dBm"
        l8 = " - Transmitter gain: " + str(self.BEAM_gain) + " dBi"

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6+"\n"+l7+"\n"+l8

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        beam_data = dict()

        beam_data["id"] = self.BEAM_id
        beam_data["width_z"] = self.BEAM_width_z
        beam_data["width_y"] = self.BEAM_width_y
        beam_data["main_azimuth"] = self.BEAM_main_azimuth
        beam_data["max_range_azimuth"] = self.BEAM_max_range_azimuth
        beam_data["min_range_azimuth"] = self.BEAM_min_range_azimuth
        beam_data["p_tx"] = self.BEAM_p_tx
        beam_data["gain"] = self.BEAM_gain

        return beam_data

    @classmethod
    def beam_width(cls, beam_gain: float, efficiency: float, n_tx_x: int, n_tx_y: int):
        """
            Function for calculate the beam widths (in Z and Y directions) of an array of antennas.

            :param beam_gain: gain per beam (in dBi).
            :param efficiency: relation between total power and dissipated power (absolute units).
            :param n_tx_x: number of transmitter in slice 1 (X axis) of a transmitter array (absolute units).
            :param n_tx_y: number of transmitter in slice 2 (Y axis) of a transmitter array (absolute units).

            :return [float] theta_z_deg: beam width in Z axis at 3dB (degrees).
            :return [float] theta_y_deg: beam width in Y axis at 3dB (degrees).
        """

        r_theta = n_tx_x / n_tx_y  # relation between beam width angles z and y (absolute units)

        gain_units = f.to_units(beam_gain)  # mW

        d = gain_units / efficiency  # Directivity = gain_units = efficiency * d

        theta_z_rad = m.sqrt((4 * m.pi) / (d * r_theta))  # d = 4*m.pi / theta_z_rad*theta_y_rad
        theta_y_rad = theta_z_rad * r_theta  # radians

        theta_z_deg = theta_z_rad * (180 / m.pi)  # radians to degrees
        theta_y_deg = theta_y_rad * (180 / m.pi)  # radians to degrees

        return theta_z_deg, theta_y_deg


class AntennaPanel:
    """
        Class AntennaPanel.
        It simulates the behaviour of a panel (or sub-panel) of a directive antenna, consisting of an array of radiators generating different beams.

        Attributes
        ----------
        - PANEL_id [str]: panel identifier.
        - PANEL_beams [list of objects (SIMULATOR.AntennaBeam)]: beams formed by the panel.
        - PANEL_ntx [int]: number of transmitter elements (mimo antennas).
        - PANEL_main_azimuth [float]: azimuth angle of the panel that mark its position with respect to the antenna coordinate axis.
        - PANEL_max_range [float]: maximum panel range angle.
        - PANEL_min_range [float]: minimum panel range angle.
        - PANEL_scanning_range_azimuth [float]: maximum angled path in which the radiation pattern can move in the azimuth axis.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
    """

    PANEL_id: str = ""  # Example = "SUBPANEL_1"
    PANEL_beams: List[AntennaBeam] = []  # [BEAM_1, BEAM_2]
    PANEL_ntx: int = 0  # absolute units
    PANEL_main_azimuth: float = 0.0  # deg
    PANEL_max_range_azimuth: float = 0.0  # deg
    PANEL_min_range_azimuth: float = 0.0  # deg
    PANEL_scanning_range_azimuth: float = 0.0  # deg

    def __init__(self, panel_id: str, n_tx: int, max_range_azimuth: float, min_range_azimuth: float, scanning_range_azimuth: float, beams: dict):
        """
            'Init' method of the class 'AntennaPanel'.
            Constructor. Parametrized the object according to the entered parameters.

            :param panel_id: panel identifier -> Example = "SUBPANEL_1".
            :param n_tx: number of transmitter elements (mimo antennas).
            :param max_range_azimuth: maximum panel range angle (in degrees).
            :param min_range_azimuth: minimum panel range angle (in degrees).
            :param beams: beams object to be created in the "init" panel method.
            :param scanning_range_azimuth: maximum angled path in which the radiation pattern can move in the azimuth axis.
        """

        self.PANEL_id = panel_id
        self.PANEL_ntx = n_tx
        self.PANEL_max_range_azimuth = max_range_azimuth
        self.PANEL_min_range_azimuth = min_range_azimuth
        self.PANEL_scanning_range_azimuth = scanning_range_azimuth

        self.PANEL_main_azimuth = self.PANEL_min_range_azimuth + (self.PANEL_scanning_range_azimuth / 2)
        self.PANEL_main_azimuth = self.PANEL_main_azimuth if self.PANEL_main_azimuth < 360 else self.PANEL_main_azimuth - 360

        self.PANEL_beams = []
        for BEAM in beams.values():
            self.PANEL_beams.append(BEAM)

    def __str__(self):
        """
            'To-string' method of the class 'AntennaPanel'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.PANEL_id
        l2 = " - Number of transmitter antennas: " + str(self.PANEL_ntx)
        l3 = " - Max scanning range (in azimuth): " + str(self.PANEL_max_range_azimuth) + " degrees"
        l4 = " - Min scanning range (in azimuth): " + str(self.PANEL_min_range_azimuth) + " degrees"
        l5 = " - Total scanning range (in azimuth): " + str(self.PANEL_scanning_range_azimuth) + " degrees"

        beams_ids = ""
        for i in range(0, len(self.PANEL_beams)):
            beams_ids += self.PANEL_beams[i].BEAM_id + ", "

        l6 = " - Beams: " + beams_ids

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        panel_data = dict()
        beams_data = dict()

        panel_data["id"] = self.PANEL_id
        panel_data["n_tx"] = self.PANEL_ntx
        panel_data["max_range_azimuth"] = self.PANEL_max_range_azimuth
        panel_data["min_range_azimuth"] = self.PANEL_min_range_azimuth
        panel_data["scanning_range_azimuth"] = self.PANEL_scanning_range_azimuth

        for i in range(0, len(self.PANEL_beams)):
            beams_data[self.PANEL_beams[i].BEAM_id] = self.PANEL_beams[i].to_dict()

        panel_data["beams"] = beams_data

        return panel_data


class BSAntenna:
    """
        Abstract class BSAntenna.
        It simulates the behaviour of an generic antenna located in a base station. It is used for channel and radio link calculation.
        The antenna can be 'directional' or 'omnidirectional'.

        Attributes
        ----------
        - ANTENNA_id [str]: antenna identifier.
        - ANTENNA_type [str]: type of the base station which the antenna is located.
        - ANTENNA_economic_model [object (SIMULATOR.EconomicModel)]: economic cost model of the device. Used to calculate the total costs of the device.
        - ANTENNA_power_model [object (SIMULATOR.PowerModel)]: power consumption model of the device. Used to calculate the total consumed power of the device.
        - ANTENNA_height [float]: tilt of the antenna.
        - ANTENNA_bandwidth [float]: bandwidth allocated by the base station for the antenna link.
        - ANTENNA_frequency [float]: operational frequency.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - get_rx_power (interface): it calculates the RX power of a receiver depending of antenna type (omnidirectional, directional or others).
    """

    ANTENNA_id: str = ""  # Example = "ANTENNA_1".
    ANTENNA_type: str = ""  # "MACRO" / "SMALL"
    ANTENNA_economic_model: EconomicModel = None
    ANTENNA_power_model: PowerModel = None
    ANTENNA_height: float = 0.0  # m
    ANTENNA_bandwidth: float = 0.0  # MHz
    ANTENNA_frequency: float = 0.0  # GHz

    def __str__(self):
        """
            'To-string' method of the abstract class 'BSAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.ANTENNA_id
        l2 = " - Type: " + self.ANTENNA_type
        l3 = " - Economic model: None" if self.ANTENNA_economic_model is None else " - Economic model: " + self.ANTENNA_economic_model.EM_id
        l4 = " - Power model: None" if self.ANTENNA_power_model is None else " - Power model: " + self.ANTENNA_power_model.PM_id
        l5 = " - Height: " + str(self.ANTENNA_height) + " m."
        l6 = " - Assigned bandwidth: " + str(self.ANTENNA_bandwidth) + " MHz."
        l7 = " - Frequency: " + str(self.ANTENNA_frequency) + " GHz."

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        antenna_data = dict()

        antenna_data["type"] = self.ANTENNA_type
        antenna_data["economic_model"] = "None" if self.ANTENNA_economic_model is None else self.ANTENNA_economic_model.EM_id
        antenna_data["power_model"] = "None" if self.ANTENNA_power_model is None else self.ANTENNA_power_model.PM_id
        antenna_data["height"] = self.ANTENNA_height
        antenna_data["bandwidth"] = self.ANTENNA_bandwidth
        antenna_data["frequency"] = self.ANTENNA_frequency

        return antenna_data

    def get_tx_power(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Interface of TX power function for Antennas.
            It calculates the equivalent transmission power for the calculation of the RX power at the receiver depending of antenna type (omnidirectional, directional or others).

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.


            :return tx_power: transmitter power depending of antenna type (in dBm).
        """

        return 0

    def get_gain(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Interface of gain function for Antennas.
            It calculates the equivalent transmission gain for the calculation of the RX power at the receiver depending of antenna type (omnidirectional, directional or others).

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return gain: transmission gain depending of antenna type (in dBi).
        """

        return 0

    def get_ntx(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Interface of ntx function for Antennas.
            It calculates the the number of mimo transmitting antennas corresponding to each TX-RX link depending of antenna type (omnidirectional, directional or others).

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return ntx: number of mimo transmitting antennas  depending of antenna type (absolute units).
        """

        return 0

    def get_frequency(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Interface of frequency function for Antennas.
            It calculates the antenna frequency corresponding to each TX-RX link depending of antenna type (omnidirectional, directional or others).

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return frequency: antenna frequency (in GHz).
        """

        return 0


class OmnidirectionalAntenna(BSAntenna):
    """
        Subclass OmnidirectionalAntenna. Inheritance of abstract class BSAntenna.
        The antenna radiate the same to all sides.

        Attributes
        ----------
        - OMNIANTENNA_ntx [float]: number of transmitter elements (mimo antennas).
        - OMNIANTENNA_gain [float]: gain of the antenna.
        - OMNIANTENNA_tx_power [int]: transmitter power of the antenna.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - get_tx_power: characterisation of the tx power of an omnidirectional antenna.
        - get_gain: characterisation of the gain of an omnidirectional antenna.
        - get_ntx: characterisation of the number of transmitter of an omnidirectional antenna.
        - get_frequency: characterisation of the frequency of an omnidirectional antenna.
    """

    OMNIANTENNA_ntx: int = 0  # absolute units
    OMNIANTENNA_gain: float = 0.0  # dBi
    OMNIANTENNA_tx_power: float = 0.0  # dBm

    def __init__(self, antenna_id: str, antenna_type: str, economic_model: Union[None, EconomicModel], power_model: Union[None, PowerModel], height: float, n_tx: int, frequency: float, gain: float, tx_power: float, bandwidth: float):
        """
            'Init' method of the subclass 'OmnidirectionalAntenna'. Inheritance of abstract class 'BSAntenna'.
            Constructor. Parametrized the object according to the entered parameters.

            :param antenna_id: antenna identifier -> Example = "ANTENNA_1".
            :param antenna_type: type of the base station which the antenna is located -> "MACRO" / "SMALL".
            :param economic_model: economic cost model of the device. 'None' if do not want to evaluate.
            :param power_model: power consumption model of the device. 'None' if do not want to evaluate.
            :param height: elevation of the antenna (in meters).
            :param n_tx: number of transmitter elements (mimo antennas).
            :param frequency: operational frequency (in GHz).
            :param gain: gain of the antenna (in dBi).
            :param tx_power: transmitter power of the antenna (in dBm).
            :param bandwidth: bandwidth allocated by the base station for the antenna link (in MHz).
        """

        self.ANTENNA_id = antenna_id  # Superclass attribute
        self.ANTENNA_type = antenna_type  # Superclass attribute
        self.ANTENNA_economic_model = economic_model  # Superclass attribute
        self.ANTENNA_power_model = power_model  # Superclass attribute
        self.ANTENNA_height = height  # Superclass attribute
        self.ANTENNA_bandwidth = bandwidth  # Superclass attribute
        self.ANTENNA_frequency = frequency  # Superclass attribute
        self.OMNIANTENNA_ntx = n_tx
        self.OMNIANTENNA_gain = gain
        self.OMNIANTENNA_tx_power = tx_power

    def __str__(self):
        """
            'To-string' method of the subclass 'OmnidirectionalAntenna'. Inheritance of abstract class 'BSAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Number of transmitter mimo antennas: " + str(self.OMNIANTENNA_ntx)
        l3 = " - gain: " + str(self.OMNIANTENNA_gain) + " dBi"
        l4 = " - tx_power: " + str(self.OMNIANTENNA_tx_power) + " dBm"

        return l1+"\n"+l2+"\n"+l3+"\n"+l4

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_networks/antennas/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_networks/antennas/".
        """

        data_dump = dict()
        antenna_data = super().to_dict()

        antenna_data["ntx"] = self.OMNIANTENNA_ntx
        antenna_data["gain"] = self.OMNIANTENNA_gain
        antenna_data["tx_power"] = self.OMNIANTENNA_tx_power

        data_dump[time] = antenna_data

        with open(file_path + self.ANTENNA_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def get_tx_power(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_tx_power for BSAntenna.
            Characterisation of the transmit power of an omnidirectional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return tx_power: transmitter power depending of antenna type (in dBm).
        """

        return self.OMNIANTENNA_tx_power

    def get_gain(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_gain for BSAntenna.
            Characterisation of the transmit gain of an omnidirectional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return gain: transmission gain depending of antenna type (in dBi).
        """

        return self.OMNIANTENNA_gain

    def get_ntx(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_ntx for BSAntenna.
            Characterisation of the number of transmitter mimo antennas of an omnidirectional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return ntx: number of mimo transmitting antennas  depending of antenna type (absolute units).
        """

        return self.OMNIANTENNA_ntx

    def get_frequency(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_frequency for BSAntenna.
            Characterisation of the frequency of an omnidirectional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return frequency: antenna frequency (in GHz).
        """

        return self.ANTENNA_frequency


class DirectionalAntenna(BSAntenna):
    """
        Subclass DirectionalAntenna. Inheritance of abstract class BSAntenna.
        The radiation from the antenna follows a directed pattern, and does not radiate the same to all sides.
        It composes from a single or many subpanels.

        Attributes
        ----------
        - DIRANTENNA_main_azimuth [float]: main direction of antenna orientation (in azimuth).
        - DIRANTENNA_scanning_range_azimuth [float]: maximum angled path in which the radiation pattern can move in the azimuth axis.
        - DIRANTENNA_main_tilt [float]: main direction of antenna orientation (in tilt).
        - DIRANTENNA_scanning_range_tilt [float]: maximum angled path in which the radiation pattern can move in the tilt axis.
        - DIRANTENNA_subpanels [list of objects (SIMULATOR.AntennaPanel)]: panels composing the antenna.
        - DIRANTENNA_radiation_pattern [matrix]: matrix of values containing the correspondence between the radiation pattern of the directive antenna and a hypothetical omnidirectional pattern.
        - __radiation_pattern_name [str]: name of the radiation pattern used.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - get_tx_power: characterisation of the tx power of an directional antenna (depending of RX and TX position).
        - get_gain: characterisation of the gain of an directional antenna (depending of RX and TX position).
        - get_ntx: characterisation of the number of transmitter of an directional antenna (depending of RX and TX position).
        - get_frequency: characterisation of the frequency of an directional antenna.
        - __get_radiation_pattern (private): it extracts the radiation pattern of an antenna from a .mat file.
    """

    DIRANTENNA_main_azimuth: float = 0.0  # deg
    DIRANTENNA_scanning_range_azimuth: float = 0.0  # deg
    DIRANTENNA_main_tilt: float = 0.0  # deg
    DIRANTENNA_scanning_range_tilt: float = 0.0  # deg
    DIRANTENNA_subpanels: List[AntennaPanel] = []  # [SUBPANEL_1, SUBPANEL_2]
    DIRANTENNA_radiation_pattern: np.array = None  # Matrix values of matlab file
    __radiation_pattern_name: str = ""  # Example: "MGain_34GHz_360"

    def __init__(self, antenna_id: str, antenna_type: str, economic_model: Union[None, EconomicModel], power_model: Union[None, PowerModel], height: float, frequency: float, bandwidth: float, azimuth: float, scanning_range_azimuth: float, tilt: float, scanning_range_tilt: float, subpanel_configuration: dict, radiation_pattern_file: str):
        """
            'Init' method of the subclass 'DirectionalAntenna'. Inheritance of abstract class 'BSAntenna'.
            Constructor. Parametrized the object according to the entered parameters.

            :param antenna_id: antenna identifier -> Example = "ANTENNA_1".
            :param antenna_type: type of the base station which the antenna is located -> "MACRO" / "SMALL".
            :param economic_model: economic cost model of the device. 'None' if do not want to evaluate.
            :param power_model: power consumption model of the device. 'None' if do not want to evaluate.
            :param height: elevation of the antenna (in meters).
            :param frequency: operational frequency (in GHz).
            :param bandwidth: bandwidth allocated by the base station for the antenna link (in MHz).
            :param azimuth: main direction of antenna orientation (in azimuth).
            :param scanning_range_azimuth: maximum angled path in which the radiation pattern can move in the azimuth axis (in degrees).
            :param tilt: main direction of antenna orientation (in tilt).
            :param scanning_range_tilt: maximum angled path in which the radiation pattern can move in the tilt axis (in degrees).
            :param subpanel_configuration: configuration of the subpanels.
            :param radiation_pattern_file: path to .mat file that describes the radiation pattern of the antenna.

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        self.ANTENNA_id = antenna_id  # Superclass attribute
        self.ANTENNA_type = antenna_type  # Superclass attribute
        self.ANTENNA_economic_model = economic_model  # Superclass attribute
        self.ANTENNA_power_model = power_model  # Superclass attribute
        self.ANTENNA_height = height  # Superclass attribute
        self.ANTENNA_bandwidth = bandwidth  # Superclass attribute
        self.ANTENNA_frequency = frequency  # Superclass attribute

        self.DIRANTENNA_main_azimuth = azimuth
        self.DIRANTENNA_scanning_range_azimuth = scanning_range_azimuth
        self.DIRANTENNA_main_tilt = tilt
        self.DIRANTENNA_scanning_range_tilt = scanning_range_tilt
        self.__radiation_pattern_name = radiation_pattern_file.split("/")[-1].replace(".mat", "")
        self.DIRANTENNA_radiation_pattern = self.__get_radiation_pattern(radiation_pattern_file)
        self.DIRANTENNA_subpanels = []

        n_panels = subpanel_configuration["n_panels"]
        n_tx_per_panel = subpanel_configuration["n_tx_per_panel"]
        beams_configuration = subpanel_configuration["beams_configuration"]

        if n_panels < 1:
            raise ConfigurationNotFound("n_panels")

        elif beams_configuration["beams_per_panel"] < 1:
            raise ConfigurationNotFound("beams_per_panel")

        else:
            self.generate_panels(n_panels, n_tx_per_panel, beams_configuration)

    def __str__(self):
        """
            'To-string' method of the subclass 'DirectionalAntenna'. Inheritance of abstract class 'BSAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Main azimuth: " + str(self.DIRANTENNA_main_azimuth) + " degrees"
        l3 = " - Scanning range in azimuth: " + str(self.DIRANTENNA_scanning_range_azimuth) + " degrees"
        l4 = " - Main tilt: " + str(self.DIRANTENNA_main_tilt) + " degrees"
        l5 = " - Scanning range in tilt: " + str(self.DIRANTENNA_scanning_range_tilt) + " degrees"
        l6 = " - Radiation pattern: " + self.__radiation_pattern_name

        panels_ids = ""
        for i in range(0, len(self.DIRANTENNA_subpanels)):
            panels_ids += self.DIRANTENNA_subpanels[i].PANEL_id + ", "

        l7 = " - Panels: " + panels_ids

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6+"\n"+l7

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        antenna_data = super().to_dict()
        panel_data = dict()

        antenna_data["main_azimuth"] = self.DIRANTENNA_main_azimuth
        antenna_data["scanning_range_azimuth"] = self.DIRANTENNA_scanning_range_azimuth
        antenna_data["scanning_range_tilt"] = self.DIRANTENNA_scanning_range_tilt
        antenna_data["main_tilt"] = self.DIRANTENNA_main_tilt
        antenna_data["radiation_pattern_name"] = self.__radiation_pattern_name
        # antenna_data["radiation_pattern"] = str(list(self.DIRANTENNA_radiation_pattern))

        for i in range(0, len(self.DIRANTENNA_subpanels)):
            panel_data[self.DIRANTENNA_subpanels[i].PANEL_id] = self.DIRANTENNA_subpanels[i].to_dict()

        # noinspection PyTypeChecker
        antenna_data["subpanels"] = panel_data

        return antenna_data

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_networks/antennas/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_networks/antennas/".
        """

        data_dump = dict()
        antenna_data = self.to_dict()

        data_dump[time] = antenna_data

        with open(file_path + self.ANTENNA_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def __get_radiation_pattern(self, file_path):
        """
            It extracts the radiation pattern of an antenna from a .mat file.

            :param file_path: path to .mat file that describes the radiation pattern of the antenna.

            :return [ndarray] radiation_pattern: NxM array with the information describing the radiation pattern (attenuation values as a function of angle)
        """

        radiation_pattern = scipy.io.loadmat(file_path)

        return radiation_pattern[self.__radiation_pattern_name]

    def get_tx_power(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_tx_power for BSAntenna.
            Characterisation of the transmit power of an directional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.


            :return tx_power: transmitter power depending of antenna type (in dBm).
        """

        # Find out which panel range the user is in (calculate the distances to each beam main azimuth)
        aux_distances = []
        for i in range(0, len(self.DIRANTENNA_subpanels)):
            for j in range(0, len(self.DIRANTENNA_subpanels[i].PANEL_beams)):

                # For a hypotenuse equal to 1
                current_azimuth_point = (m.cos(self.DIRANTENNA_subpanels[i].PANEL_beams[j].BEAM_main_azimuth), m.sin(self.DIRANTENNA_subpanels[i].PANEL_beams[j].BEAM_main_azimuth))

                try:
                    current_distance_to_azimuth_point = gf.euclidean_distance(rx_position, current_azimuth_point)

                except ValueError as e:
                    print(e)
                    sys.exit(1)

                aux_distances.append((current_distance_to_azimuth_point, i, j))

        panel_beam_selected = sorted(aux_distances, key=sk.first_element_in_float_tuple)[0]
        panel_tx_power = self.DIRANTENNA_subpanels[panel_beam_selected[1]].PANEL_beams[panel_beam_selected[2]].BEAM_p_tx

        return panel_tx_power

    def get_gain(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_gain for BSAntenna.
            Characterisation of the transmit gain of an directional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return gain: transmission gain depending of antenna type (in dBi).
        """

        try:
            incident_angles = gf.calculate_incident_angle(rx_position, tx_position, rx_height=rx_height, tx_height=tx_height)

        except ValueError as e:  # Catch exception if occurs (quadrant of a receiver point not found)
            print(e)
            sys.exit(1)

        attenuation_factor = self.DIRANTENNA_radiation_pattern[incident_angles[0], incident_angles[1]]

        # Find out which panel range the user is in (calculate the distances to each beam main azimuth)
        aux_distances = []
        for i in range(0, len(self.DIRANTENNA_subpanels)):
            for j in range(0, len(self.DIRANTENNA_subpanels[i].PANEL_beams)):

                # For a hypotenuse equal to 1
                current_azimuth_point = (m.cos(self.DIRANTENNA_subpanels[i].PANEL_beams[j].BEAM_main_azimuth), m.sin(self.DIRANTENNA_subpanels[i].PANEL_beams[j].BEAM_main_azimuth))
                current_distance_to_azimuth_point = gf.euclidean_distance(rx_position, current_azimuth_point)
                aux_distances.append((current_distance_to_azimuth_point, i, j))

        panel_beam_selected = sorted(aux_distances, key=sk.first_element_in_float_tuple)[0]
        panel_gain = self.DIRANTENNA_subpanels[panel_beam_selected[1]].PANEL_beams[panel_beam_selected[2]].BEAM_gain

        return panel_gain * attenuation_factor

    def get_ntx(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_ntx for BSAntenna.
            Characterisation of the number of transmitter mimo antennas of an directional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return ntx: number of mimo transmitting antennas depending of antenna type (absolute units).
        """

        n_tx = 0

        if len(self.DIRANTENNA_subpanels) == 1:
            n_tx = self.DIRANTENNA_subpanels[0].PANEL_ntx

        elif len(self.DIRANTENNA_subpanels) > 1:

            aux_distances = []
            for i in range(0, len(self.DIRANTENNA_subpanels)):

                # For a hypotenuse equal to 1
                current_azimuth_point = (m.cos(m.radians(self.DIRANTENNA_subpanels[i].PANEL_main_azimuth)), m.sin(m.radians(self.DIRANTENNA_subpanels[i].PANEL_main_azimuth)))
                current_distance_to_azimuth_point = gf.euclidean_distance(rx_position, current_azimuth_point)
                aux_distances.append((current_distance_to_azimuth_point, i))

            panel_selected = sorted(aux_distances, key=sk.first_element_in_float_tuple)[0]
            n_tx = self.DIRANTENNA_subpanels[panel_selected[1]].PANEL_ntx

        return n_tx

    def get_frequency(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_frequency for BSAntenna.
            Characterisation of the frequency of an directional antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return frequency: antenna frequency (in GHz).
        """

        return self.ANTENNA_frequency

    def generate_panels(self, n_panels: int, n_tx_per_panel: int, beams_configuration: dict):
        """
            It generates the panels according to the tilt and azimuth angulation they should have in relation to the antenna angulation.

            :param n_panels: number of panels per antenna.
            :param n_tx_per_panel: number of transmitter elements (mimo antennas) per panel.
            :param beams_configuration: configuration of the beams.
        """

        # Configuration of the beams
        n_beams_per_panel = beams_configuration["beams_per_panel"]
        p_tx_per_beam = beams_configuration["p_tx_per_beam"]
        gain_per_beam = beams_configuration["gain_per_beam"]
        beam_z_width = beams_configuration["z_width"]
        beam_y_width = beams_configuration["y_width"]

        aux_scanning_range = self.DIRANTENNA_main_azimuth + (self.DIRANTENNA_scanning_range_azimuth / 2)
        max_antenna_scanning_range = aux_scanning_range if aux_scanning_range < 360 else aux_scanning_range - 360

        # aux_scanning_range = self.DIRANTENNA_main_azimuth - (self.DIRANTENNA_scanning_range_azimuth / 2)
        # min_antenna_scanning_range = aux_scanning_range if aux_scanning_range >= 0 else aux_scanning_range + 360

        panel_range = self.DIRANTENNA_scanning_range_azimuth / n_panels
        beam_range = panel_range / n_beams_per_panel

        # Generation of the panels
        panel_offset = 0
        for i in range(0, n_panels):
            max_panel_range = max_antenna_scanning_range - panel_offset
            min_panel_range = max_panel_range - panel_range

            # Generation of the beams
            beam_offset = 0
            beams = dict()
            for j in range(0, n_beams_per_panel):
                max_beam_range = max_panel_range - beam_offset
                min_beam_range = max_beam_range - beam_range

                beams["BEAM_"+str(j+1)] = AntennaBeam("BEAM_"+str(j+1), beam_z_width, beam_y_width, max_beam_range, min_beam_range, p_tx_per_beam, gain_per_beam)

                beam_offset += beam_range

            current_panel = AntennaPanel("PANEL_" + str(i + 1), n_tx_per_panel, max_panel_range, min_panel_range, panel_range, beams)
            self.DIRANTENNA_subpanels.append(current_panel)

            panel_offset += panel_range


class AntennaRss5921(DirectionalAntenna):
    """
        Subclass AntennaRss5921. Inheritance of abstract class DirectionalAntenna.
        Directional patch antenna consisting of 4 sub-panels with 3 modes of operation (2, 4 and 8 beams respectively).
        Used in the '5G pilot' project for autonomous vehicle simulations.
        The characteristics have been obtained from the datasheet provided by the manufacturer.

        Attributes
        ----------
        - RSS5921_mode [str]: antenna operating mode (2, 4 or 8 beams).
        - RSS5921_efficiency [float]: ratio between the power radiated by an antenna and the power delivered to the antenna.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
    """

    RSS5921_mode: str = ""  # "CFG1" / "CFG2" / "CFG5"
    RSS5921_efficiency: float = 0.0  # absolute units

    def __init__(self, antenna_id: str, antenna_type: str, height: float, frequency: float, bandwidth: float, azimuth: float, tilt: float, efficiency: float = 0.8, mode: str = "CFG1"):
        """
            'Init' method of the subclass 'DirectionalAntenna'. Inheritance of abstract class 'BSAntenna'.
            Constructor. Parametrized the object according to the entered parameters.

            :param antenna_id: antenna identifier -> Example = "ANTENNA_1".
            :param antenna_type: type of the base station which the antenna is located -> "MACRO" / "SMALL".
            :param height: elevation of the antenna (in meters).
            :param frequency: operational frequency (in GHz).
            :param bandwidth: bandwidth allocated by the base station for the antenna link (in MHz).
            :param azimuth: main direction of antenna orientation (in azimuth).
            :param tilt: main direction of antenna orientation (in tilt).
            :param* efficiency: ratio between the power radiated by an antenna and the power delivered to the antenna (absolute units). Defaults to 0.8.
            :param* mode: antenna operating mode -> "CFG1" / "CFG2" / "CFG5". Defaults to "CFG1".

            :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        """

        self.RSS5921_mode = mode
        self.RSS5921_efficiency = efficiency

        if 26.50 > frequency > 29.50:  # operational frequency of the antenna RSS5921
            raise ConfigurationNotFound("RSS5921_frequency")

        scanning_range_azimuth = 120  # degrees
        scanning_range_tilt = 30  # degrees

        economic_model = None  # ? update RSS5921 economic_model when model are deploy
        power_model = None  # ? update RSS5921 power_model when model are deploy

        subpanel_configuration = dict()
        beams_configuration = dict()

        if self.RSS5921_mode == "CFG1":
            subpanel_configuration["n_panels"] = 1
            n_tx_per_panel_slice_1 = 24
            n_tx_per_panel_slice_2 = 16
            subpanel_configuration["n_tx_per_panel"] = n_tx_per_panel_slice_1*n_tx_per_panel_slice_2  # 384 (24x16)
            beams_configuration["beams_per_panel"] = 2
            beams_configuration["p_tx_per_beam"] = 28  # dBm
            beams_configuration["gain_per_beam"] = 31  # dBi
            z_width, y_width = AntennaBeam.beam_width(beams_configuration["gain_per_beam"], self.RSS5921_efficiency, n_tx_per_panel_slice_1, n_tx_per_panel_slice_2)
            beams_configuration["z_width"] = z_width  # degrees (considering 0.8 efficiency)
            beams_configuration["y_width"] = y_width  # degrees (considering 0.8 efficiency)
            subpanel_configuration["beams_configuration"] = beams_configuration

        elif self.RSS5921_mode == "CFG2":
            subpanel_configuration["n_panels"] = 2
            subpanel_configuration["n_tx_per_panel"] = 192  # 24x8
            beams_configuration["beams_per_panel"] = 2
            beams_configuration["p_tx_per_beam"] = 25  # dBm
            beams_configuration["gain_per_beam"] = 28  # dBm
            beams_configuration["z_width"] = 4.69  # degrees (considering 0.8 efficiency)
            beams_configuration["y_width"] = 7.03  # degrees (considering 0.8 efficiency)
            subpanel_configuration["beams_configuration"] = beams_configuration

        elif self.RSS5921_mode == "CFG5":
            subpanel_configuration["n_panels"] = 4
            subpanel_configuration["n_tx_per_panel"] = 96  # 24x4
            beams_configuration["beams_per_panel"] = 2
            beams_configuration["p_tx_per_beam"] = 22  # dBm
            beams_configuration["gain_per_beam"] = 25  # dBm
            beams_configuration["z_width"] = 4.69  # degrees (considering 0.8 efficiency)
            beams_configuration["y_width"] = 7.03  # degrees (considering 0.8 efficiency)
            subpanel_configuration["beams_configuration"] = beams_configuration

        else:
            raise ConfigurationNotFound("RSS5921_mode")

        radiation_pattern_file = ""  # ? add .m file path

        super().__init__(antenna_id, antenna_type, economic_model, power_model, height, frequency, bandwidth, azimuth, scanning_range_azimuth, tilt, scanning_range_tilt, subpanel_configuration, radiation_pattern_file)

    def __str__(self):
        """
            'To-string' method of the subclass 'AntennaRss5921'. Inheritance of abstract class 'DirectionalAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Operating mode: " + str(self.RSS5921_mode)
        l3 = " - Efficiency: " + str(self.RSS5921_efficiency)

        return l1 + "\n" + l2 + "\n" + l3

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_networks/antennas/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_networks/antennas/".
        """

        data_dump = dict()
        antenna_data = super().to_dict()

        antenna_data["mode"] = self.RSS5921_mode
        antenna_data["efficiency"] = self.RSS5921_efficiency

        data_dump[time] = antenna_data

        with open(file_path + self.ANTENNA_id, 'a') as json_file:
            json.dump(data_dump, json_file)


class TriSectorAntenna(BSAntenna):
    """
        Class TriSectorAntenna. Inheritance of abstract class 'BSAntenna'.
        Structure that allocate 3 directional antennas, rotated 120 degrees in azimuth to each other.

        Attributes
        ----------
        - SECTORX_carrier_frequency [float]: sector carrier frequency.
        - SECTORX_main_azimuth [float]: main direction of sector orientation (in azimuth).
        - SECTORX_scanning_range_azimuth [float]: maximum angled path in which the radiation pattern can move in the azimuth axis (for each sector).
        - SECTORX_main_tilt [float]: main direction of sector orientation (in tilt).
        - SECTORX_scanning_range_tilt [float]: maximum angled path in which the radiation pattern can move in the tilt axis (for each sector).
        - SECTORX_panel [Object (SIMULATOR.AntennaPanel)]: panel composing the sector.
        - SECTORX_radiation_pattern [np.array]: matrix of values containing the correspondence between the radiation pattern of the sector and a hypothetical omnidirectional pattern.
        - __sectorX_radiation_pattern_name [str]: name of the radiation pattern used for the sector.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - get_tx_power: characterisation of the tx power of an trisector antenna (depending of RX and TX position).
        - get_gain: characterisation of the gain of an trisector antenna (depending of RX and TX position).
        - get_ntx: characterisation of the number of transmitter of an trisector antenna (depending of RX and TX position).
        - get_frequency: characterisation of the frequency of an trisector antenna.
        - find_incident_sector: calculate, as a function of the incident vector, the sector to be radiated to the receiver.
        - __get_radiation_pattern (private): it extracts the radiation pattern of an antenna from a .mat file.
    """

    # Sector 1 attributes
    SECTOR1_carrier_frequency: float = 0.0
    SECTOR1_main_azimuth: float = 0.0
    SECTOR1_scanning_range_azimuth: float = 0.0
    SECTOR1_main_tilt: float = 0.0
    SECTOR1_scanning_range_tilt: float = 0.0
    SECTOR1_panel: AntennaPanel = None
    SECTOR1_radiation_pattern: np.array = None
    __sector1_radiation_pattern_name: str = ""

    # Sector 2 attributes
    SECTOR2_carrier_frequency: float = 0.0
    SECTOR2_main_azimuth: float = 0.0
    SECTOR2_scanning_range_azimuth: float = 0.0
    SECTOR2_main_tilt: float = 0.0
    SECTOR2_scanning_range_tilt: float = 0.0
    SECTOR2_panel: AntennaPanel = None
    SECTOR2_radiation_pattern: np.array = None
    __sector2_radiation_pattern_name: str = ""

    # Sector 3 attributes
    SECTOR3_carrier_frequency: float = 0.0
    SECTOR3_main_azimuth: float = 0.0
    SECTOR3_scanning_range_azimuth: float = 0.0
    SECTOR3_main_tilt: float = 0.0
    SECTOR3_scanning_range_tilt: float = 0.0
    SECTOR3_panel: AntennaPanel = None
    SECTOR3_radiation_pattern: np.array = None
    __sector3_radiation_pattern_name: str = ""

    def __init__(self, antenna_id: str, antenna_type: str, economic_model: Union[EconomicModel, None], power_model: Union[PowerModel, None], height: float, frequency: float, bw: float, radiation_pattern_file: str, panel_configuration: dict):

        # Antenna attributes
        self.ANTENNA_id = antenna_id
        self.ANTENNA_type = antenna_type
        self.ANTENNA_economic_model = economic_model
        self.ANTENNA_power_model = power_model
        self.ANTENNA_height = height
        self.ANTENNA_bandwidth = bw
        self.ANTENNA_frequency = frequency

        # Sector 1 attributes
        self.SECTOR1_carrier_frequency = self.ANTENNA_frequency
        self.SECTOR1_main_azimuth = 90
        self.SECTOR1_scanning_range_azimuth = 120
        self.SECTOR1_main_tilt = 0
        self.SECTOR1_scanning_range_tilt = 0
        sector_1_beam = AntennaBeam("PANEL1_BEAM", 0, 120, 150, 30, panel_configuration["sector_1"]["p_tx"], panel_configuration["sector_1"]["gain"])
        sector_1_beams = dict({sector_1_beam.BEAM_id: sector_1_beam})
        self.SECTOR1_panel = AntennaPanel("TRISECTOR_PANEL_1", panel_configuration["sector_1"]["n_tx"], 150, 30, self.SECTOR1_scanning_range_azimuth, sector_1_beams)
        self.__sector1_radiation_pattern_name = radiation_pattern_file.split("/")[-1].replace(".mat", "")
        self.SECTOR1_radiation_pattern = self.__get_radiation_pattern(radiation_pattern_file, self.__sector1_radiation_pattern_name)

        # Sector 2 attributes
        self.SECTOR2_carrier_frequency = self.ANTENNA_frequency + 0.01
        self.SECTOR2_main_azimuth = 210
        self.SECTOR2_scanning_range_azimuth = 120
        self.SECTOR2_main_tilt = 0
        self.SECTOR2_scanning_range_tilt = 0
        sector_2_beam = AntennaBeam("PANEL2_BEAM", 0, 120, 270, 150, panel_configuration["sector_2"]["p_tx"], panel_configuration["sector_2"]["gain"])
        sector_2_beams = dict({sector_2_beam.BEAM_id: sector_2_beam})
        self.SECTOR2_panel = AntennaPanel("TRISECTOR_PANEL_2", panel_configuration["sector_2"]["n_tx"], 270, 150, self.SECTOR2_scanning_range_azimuth, sector_2_beams)
        self.__sector2_radiation_pattern_name = radiation_pattern_file.split("/")[-1].replace(".mat", "")
        self.SECTOR2_radiation_pattern = self.__get_radiation_pattern(radiation_pattern_file, self.__sector2_radiation_pattern_name)

        # Sector 3 attributes
        self.SECTOR3_carrier_frequency = self.ANTENNA_frequency - 0.01
        self.SECTOR3_main_azimuth = 330
        self.SECTOR3_scanning_range_azimuth = 120
        self.SECTOR3_main_tilt = 0
        self.SECTOR3_scanning_range_tilt = 0
        sector_3_beam = AntennaBeam("PANEL3_BEAM", 0, 120, 30, 270, panel_configuration["sector_3"]["p_tx"], panel_configuration["sector_3"]["gain"])
        sector_3_beams = dict({sector_3_beam.BEAM_id: sector_3_beam})
        self.SECTOR3_panel = AntennaPanel("TRISECTOR_PANEL_3", panel_configuration["sector_3"]["n_tx"], 30, 270, self.SECTOR2_scanning_range_azimuth, sector_3_beams)
        self.__sector3_radiation_pattern_name = radiation_pattern_file.split("/")[-1].replace(".mat", "")
        self.SECTOR3_radiation_pattern = self.__get_radiation_pattern(radiation_pattern_file, self.__sector3_radiation_pattern_name)

    def __str__(self):
        """
            'To-string' method of the subclass 'TriSectorAntenna'. Inheritance of abstract class 'BSAntenna'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()  # Superclass information
        l2 = " - Sector 1 carrier frequency: " + str(self.SECTOR1_carrier_frequency) + " GHz"
        l3 = " - Sector 1 main azimuth: " + str(self.SECTOR1_main_azimuth) + " degrees"
        l4 = " - Sector 1 scanning range in azimuth: " + str(self.SECTOR1_scanning_range_azimuth) + " degrees"
        l5 = " - Sector 1 main tilt: " + str(self.SECTOR1_main_tilt) + " degrees"
        l6 = " - Sector 1 scanning range in tilt: " + str(self.SECTOR1_scanning_range_tilt) + " degrees"
        l7 = " - Sector 1 radiation pattern: " + self.__sector1_radiation_pattern_name
        l8 = " - Sector 1 antenna panel: " + self.SECTOR1_panel.PANEL_id
        l9 = " - Sector 2 carrier frequency: " + str(self.SECTOR2_carrier_frequency) + " GHz"
        l10 = " - Sector 2 main azimuth: " + str(self.SECTOR2_main_azimuth) + " degrees"
        l11 = " - Sector 2 scanning range in azimuth: " + str(self.SECTOR2_scanning_range_azimuth) + " degrees"
        l12 = " - Sector 2 main tilt: " + str(self.SECTOR2_main_tilt) + " degrees"
        l13 = " - Sector 2 scanning range in tilt: " + str(self.SECTOR2_scanning_range_tilt) + " degrees"
        l14 = " - Sector 2 radiation pattern: " + self.__sector2_radiation_pattern_name
        l15 = " - Sector 2 antenna panel: " + self.SECTOR2_panel.PANEL_id
        l16 = " - Sector 3 carrier frequency: " + str(self.SECTOR3_carrier_frequency) + " GHz"
        l17 = " - Sector 3 main azimuth: " + str(self.SECTOR3_main_azimuth) + " degrees"
        l18 = " - Sector 3 scanning range in azimuth: " + str(self.SECTOR3_scanning_range_azimuth) + " degrees"
        l19 = " - Sector 3 main tilt: " + str(self.SECTOR3_main_tilt) + " degrees"
        l20 = " - Sector 3 scanning range in tilt: " + str(self.SECTOR3_scanning_range_tilt) + " degrees"
        l21 = " - Sector 3 radiation pattern: " + self.__sector3_radiation_pattern_name
        l22 = " - Sector 3 antenna panel: " + self.SECTOR3_panel.PANEL_id

        return l1+"\n"+l2+"\n"+l3+"\n"+l4+"\n"+l5+"\n"+l6+"\n"+l7+"\n"+l8+"\n"+l9+"\n"+l10+"\n"+l11+"\n"+l12+"\n"+l13+"\n"+l14+"\n"+l15+"\n"+l16+"\n"+l17+"\n"+l18+"\n"+l19+"\n"+l20+"\n"+l21+"\n"+l22

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        antenna_data = super().to_dict()

        antenna_data["SECTOR1_carrier_frequency"] = self.SECTOR1_carrier_frequency
        antenna_data["SECTOR1_main_azimuth"] = self.SECTOR1_main_azimuth
        antenna_data["SECTOR1_scanning_range_azimuth"] = self.SECTOR1_scanning_range_azimuth
        antenna_data["SECTOR1_main_tilt"] = self.SECTOR1_main_tilt
        antenna_data["SECTOR1_scanning_range_tilt"] = self.SECTOR1_scanning_range_tilt
        antenna_data["SECTOR1_panel"] = self.SECTOR1_panel.PANEL_id
        # antenna_data["SECTOR1_radiation_pattern"] = str(list(self.SECTOR1_radiation_pattern))
        antenna_data["SECTOR2_carrier_frequency"] = self.SECTOR2_carrier_frequency
        antenna_data["SECTOR2_main_azimuth"] = self.SECTOR2_main_azimuth
        antenna_data["SECTOR2_scanning_range_azimuth"] = self.SECTOR2_scanning_range_azimuth
        antenna_data["SECTOR2_main_tilt"] = self.SECTOR2_main_tilt
        antenna_data["SECTOR2_scanning_range_tilt"] = self.SECTOR2_scanning_range_tilt
        antenna_data["SECTOR2_panel"] = self.SECTOR2_panel.PANEL_id
        # antenna_data["SECTOR2_radiation_pattern"] = str(list(self.SECTOR2_radiation_pattern))
        antenna_data["SECTOR3_carrier_frequency"] = self.SECTOR3_carrier_frequency
        antenna_data["SECTOR3_main_azimuth"] = self.SECTOR3_main_azimuth
        antenna_data["SECTOR3_scanning_range_azimuth"] = self.SECTOR3_scanning_range_azimuth
        antenna_data["SECTOR3_main_tilt"] = self.SECTOR3_main_tilt
        antenna_data["SECTOR3_scanning_range_tilt"] = self.SECTOR3_scanning_range_tilt
        antenna_data["SECTOR3_panel"] = self.SECTOR3_panel.PANEL_id
        # antenna_data["SECTOR3_radiation_pattern"] = str(list(self.SECTOR3_radiation_pattern))

        return antenna_data

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/cellular_networks/antennas/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the network devices. Defaults to "/SIMULATOR/Results/cellular_networks/antennas/".
        """

        data_dump = dict()
        antenna_data = self.to_dict()

        data_dump[time] = antenna_data

        with open(file_path + self.ANTENNA_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def get_tx_power(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_tx_power for BSAntenna.
            Characterisation of the TX power of an trisector antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return tx_power: transmitter power depending of antenna type (in dBm).
        """

        current_tx_power = 0

        sector_selected = self.find_incident_sector(rx_position)

        if sector_selected == "SECTOR_1":
            current_tx_power = self.SECTOR1_panel.PANEL_beams[0].BEAM_p_tx

        elif sector_selected == "SECTOR_2":
            current_tx_power = self.SECTOR2_panel.PANEL_beams[0].BEAM_p_tx

        elif sector_selected == "SECTOR_3":
            current_tx_power = self.SECTOR3_panel.PANEL_beams[0].BEAM_p_tx

        return current_tx_power

    def get_gain(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_gain for BSAntenna.
            Characterisation of the gain of an trisector antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return gain: transmission gain depending of antenna type (in dBi).
        """

        current_gain = 0

        sector_selected = self.find_incident_sector(rx_position)

        if sector_selected == "SECTOR_1":
            current_gain = self.SECTOR1_panel.PANEL_beams[0].BEAM_gain

        elif sector_selected == "SECTOR_2":
            current_gain = self.SECTOR2_panel.PANEL_beams[0].BEAM_gain

        elif sector_selected == "SECTOR_3":
            current_gain = self.SECTOR3_panel.PANEL_beams[0].BEAM_gain

        return current_gain

    def get_ntx(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_ntx for BSAntenna.
            Characterisation of the number of transmitter mimo antennas of an trisector antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return ntx: number of mimo transmitting antennas  depending of antenna type (absolute units).
        """

        current_n_tx = 0

        sector_selected = self.find_incident_sector(rx_position)

        if sector_selected == "SECTOR_1":
            current_n_tx = self.SECTOR1_panel.PANEL_ntx

        elif sector_selected == "SECTOR_2":
            current_n_tx = self.SECTOR2_panel.PANEL_ntx

        elif sector_selected == "SECTOR_3":
            current_n_tx = self.SECTOR3_panel.PANEL_ntx

        return current_n_tx

    def get_frequency(self, rx_position: Tuple[float, float], tx_position: Tuple[float, float], rx_height: float = 0.0, tx_height: float = 0.0):
        """
            Override interface method get_frequency for BSAntenna.
            Characterisation of the frequency of an trisector antenna.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).
            :param tx_position: X and Y coordinates of the receiver or the second position -> (x,y).
            :param* rx_height: height of the transmitter (in meters). Defaults to 0.
            :param* tx_height: height of the receiver (in meters). Defaults to 0.

            :return frequency: antenna frequency (in GHz).
        """

        current_frequency = 0

        sector_selected = self.find_incident_sector(rx_position)

        if sector_selected == "SECTOR_1":
            current_frequency = self.SECTOR1_carrier_frequency

        elif sector_selected == "SECTOR_2":
            current_frequency = self.SECTOR2_carrier_frequency

        elif sector_selected == "SECTOR_3":
            current_frequency = self.SECTOR3_carrier_frequency

        return current_frequency

    def find_incident_sector(self, rx_position: Tuple[float, float]):
        """
            Calculate, as a function of the incident vector, the sector to be radiated to the receiver.

            :param rx_position: X and Y coordinates of the transmitter or the first position -> (x,y).

            :return [str] sector_selected: incident sector identifier.
        """

        aux_azimuths = dict({"SECTOR_1": self.SECTOR1_main_azimuth, "SECTOR_2": self.SECTOR2_main_azimuth, "SECTOR_3": self.SECTOR3_main_azimuth})
        aux_distances = []
        for current_sector in aux_azimuths.keys():

            # For a hypotenuse equal to 1
            current_azimuth_point = (m.cos(aux_azimuths[current_sector]), m.sin(aux_azimuths[current_sector]))
            current_distance_to_azimuth_point = gf.euclidean_distance(rx_position, current_azimuth_point)
            aux_distances.append((current_distance_to_azimuth_point, current_sector))

        sector_selected = sorted(aux_distances, key=sk.first_element_in_float_tuple)[0]
        sector_selected = sector_selected[1]

        return sector_selected

    @staticmethod
    def __get_radiation_pattern(file_path: str, radiation_pattern_name: str):
        """
            It extracts the radiation pattern of an antenna from a .mat file.

            :param file_path: path to .mat file that describes the radiation pattern of the antenna.

            :return [ndarray] radiation_pattern: NxM array with the information describing the radiation pattern (attenuation values as a function of angle)
        """

        radiation_pattern = scipy.io.loadmat(file_path)

        return radiation_pattern[radiation_pattern_name]
