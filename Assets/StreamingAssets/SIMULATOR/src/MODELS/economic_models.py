# Class 'EconomicModel' (abstract), class 'BsEconomicModel'
# Created 07/06/2018 (version 1.0)
# Modified 24/02/2020 (version 6.0) - Jose Javier Rico Palomo

import json
from typing import *


class EconomicModel:
    """
        Abstract class EconomicModel.
        It models the economic cost of cellular network devices.
        The model can be BsEconomicModel.

        Attributes
        ----------
        - EM_id [str]: economic model identifier.
        - EM_total_capex [float]: total capital expenditures of the device.
        - EM_total_opex [float]: total operational expenditures of the device.
        - CAPEX_deploy [float]: deployment costs of the device.
        - CAPEX_equipment [float]: equipment costs of the device.
        - OPEX_kwh_cost [float]: kilowatts per hour cost.
        - OPEX_oam [float]: operational, administration and maintenance cost of the device.
        - OPEX_rent [float]: rental site cost of the device.

        Methods
        -------
        - __str__: information for output by file or by screen of results.
        - to_dict: it creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        - total_costs (class method): it calculates the economic cost of whole network (capex and opex).
    """

    EM_id: str = ""  # Example = "ECONOMICMODEL_1"
    EM_total_capex: float = 0.0  # €
    EM_total_opex: float = 0.0  # €/year
    CAPEX_deploy: float = 0.0  # €
    CAPEX_equipment: float = 0.0  # €
    OPEX_kwh_cost: float = 0.0  # €
    OPEX_oam: float = 0.0  # €/year
    OPEX_rent: float = 0.0  # €/year

    def __str__(self):
        """
            'To-string' method of the abstract class 'EconomicModel'.
            Information for output by file or by screen of results.
        """

        l1 = " - id: " + self.EM_id
        l2 = " - Initial deployment cost: " + str(self.CAPEX_deploy) + " €"
        l3 = " - Equipment cost: " + str(self.CAPEX_equipment) + " €"
        l4 = " - Operational, administration and maintenance cost per year: " + str(self.OPEX_oam) + " €/year"
        l5 = " - Site rental cost per year: " + str(self.OPEX_rent) + " €/year"
        l6 = " - Kilowatts per hour cost: " + str(self.OPEX_kwh_cost) + " €"
        l7 = " - Total capital expenditures (CAPEX): " + str(self.EM_total_capex) + " €"
        l8 = " - Total operational expenditures (OPEX): " + str(self.EM_total_opex) + " €"

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6 + "\n" + l7 + "\n" + l8

    def to_dict(self):
        """
            It creates a dictionary with the values of the object to be used by the subclass to dump the values into a json file.
        """

        economic_model_data = dict()

        economic_model_data["deploy"] = str(self.CAPEX_deploy)
        economic_model_data["equipment"] = str(self.CAPEX_equipment)
        economic_model_data["kwh_cost"] = str(self.OPEX_kwh_cost)
        economic_model_data["oam"] = str(self.OPEX_oam)
        economic_model_data["rent"] = str(self.OPEX_rent)
        economic_model_data["total_capex"] = str(self.EM_total_capex)
        economic_model_data["total_opex"] = str(self.EM_total_opex)

        return economic_model_data

    @classmethod
    def total_costs(cls, bs_costs: dict, backhaul_costs: dict, fronthaul_costs: dict, access_network_costs: dict):
        """
            It calculates the economic cost of whole network (capex and opex).

            :param bs_costs: economic cost of base stations -> [BS_id]["capex"], [BS_id]["opex"]
            :param backhaul_costs: economic cost of backhaul network -> ["capex"], ["opex"]
            :param fronthaul_costs: economic cost of fronthaul network -> ["capex"], ["opex"]
            :param access_network_costs: economic cost of access network -> ["network_capex"], ["network_opex"], [Router_id]["capex"], [Router_id]["opex"]

            :return [float] total_capex: total capital expenditures of the network (in €).
            :return [float] total_opex: total operational expenditures of the network (in €/year).
        """

        total_capex = 0.0
        total_opex = 0.0

        # Base Stations costs
        for BS in bs_costs.keys():
            total_capex += bs_costs[BS]["capex"]
            total_opex += bs_costs[BS]["opex"]

        # Backhaul costs
        total_capex += backhaul_costs["capex"]
        total_opex += backhaul_costs["opex"]

        # Fronthaul costs
        total_capex += fronthaul_costs["capex"]
        total_opex += fronthaul_costs["opex"]

        # Access network costs
        total_capex += access_network_costs["network_capex"]
        total_opex += access_network_costs["network_opex"]

        for ROUTER in access_network_costs["routers"].keys():
            total_capex += access_network_costs["routers"][ROUTER]["capex"]
            total_opex += access_network_costs["routers"][ROUTER]["opex"]

        return total_capex, total_opex


class BsEconomicModel(EconomicModel):
    """
        Subclass BsEconomicModel. Inheritance of abstract class 'EconomicModel'.
        It models the economic cost of a Base Station.

        Attributes
        ----------
        - BSEM_bs_id [float]: base station identifier.
        - BSEM_deployment_cost [float]: deployment costs of the base station.
        - BSEM_equipment_cost [float]: equipment costs of the base station.
        - BSEM_site_rent_cost [float]: operational, administration and maintenance cost of the base station.
        - BSEM_oam_cost [float]: rental site cost of the base station.

        Methods
        -------
        - __init__: Constructor. Parametrized the object according to the entered parameters.
        - __str__: information for output by file or by screen of results.
        - to_json: it dumps (in a json file) the values of the class attributes at each time instant.
        - calculate_capex: it calculates the capital expenditures of base station.
        - calculate_opex: it calculates the operational expenditures of base station.
    """

    BSEM_bs_id: str = ""  # Example = "MACRO_BS_2".
    BSEM_deployment_cost: float = 0.0  # €
    BSEM_equipment_cost: float = 0.0  # €
    BSEM_site_rent_cost: float = 0.0  # €/year
    BSEM_oam_cost: float = 0.0  # €/year

    def __init__(self, model_id: str, bs_id: str, deployment_cost: float, equipment_cost: float, oam_cost: float, rent_cost: float, kwh_cost: float, economic_models: Dict[str, EconomicModel]):
        """
            'Init' method of the subclass 'BsEconomicModel'. Inheritance of abstract class 'EconomicModel'.
            Constructor. Parametrized the object according to the entered parameters.

            :param model_id: economic model identifier -> Example = "ECONOMICMODEL_1".
            :param bs_id: base station identifier -> Example = "MACRO_BS_2".
            :param deployment_cost: deployment costs of the base station (in  €).
            :param equipment_cost: equipment costs of the base station (in  €).
            :param oam_cost: operational, administration and maintenance cost of the base station (in  €/year).
            :param rent_cost: rental site cost of the base station (in  €/year).
            :param kwh_cost: kilowatts per hour cost (in €).
            :param economic_models: economic models of all devices that composes the base station -> keys device_names values economic_models.
        """

        self.EM_id = model_id
        self.BSEM_bs_id = bs_id
        self.BSEM_deployment_cost = deployment_cost
        self.BSEM_equipment_cost = equipment_cost
        self.BSEM_site_rent_cost = rent_cost
        self.BSEM_oam_cost = oam_cost
        self.OPEX_kwh_cost = kwh_cost

        self.CAPEX_deploy = self.BSEM_deployment_cost
        self.CAPEX_equipment = self.BSEM_equipment_cost
        self.OPEX_oam = self.BSEM_site_rent_cost
        self.OPEX_rent = self.BSEM_oam_cost

        # sum all the costs of the devices that make up the base station
        for EM in economic_models.keys():
            self.CAPEX_deploy += economic_models[EM].CAPEX_deploy
            self.CAPEX_equipment += economic_models[EM].CAPEX_equipment
            self.OPEX_oam += economic_models[EM].OPEX_oam
            self.OPEX_rent += economic_models[EM].OPEX_rent

    def __str__(self):
        """
            'To-string' method of the abstract subclass 'BsEconomicModel'. Inheritance of abstract class 'EconomicModel'.
            Information for output by file or by screen of results.
        """

        l1 = super().__str__()
        l2 = " - BS id: " + self.BSEM_bs_id
        l3 = " - BS deployment cost: " + str(self.BSEM_deployment_cost) + " €"
        l4 = " - BS equipment cost: " + str(self.BSEM_equipment_cost) + " €"
        l5 = " - BS oam cost per year: " + str(self.BSEM_oam_cost) + " €/year"
        l6 = " - BS site rental cost per year: " + str(self.BSEM_site_rent_cost) + " €/year"

        return l1 + "\n" + l2 + "\n" + l3 + "\n" + l4 + "\n" + l5 + "\n" + l6

    def to_json(self, time: float, file_path: str = "/SIMULATOR/Results/SIMULATOR/Results/cellular_networks/base_stations/"):
        """
            It dumps (in a json file) the values of the class attributes at each time instant.

            :param time: time instant (in seconds).
            :param* file_path: path to the folder containing the results files of the links. Defaults to "/SIMULATOR/Results/".
        """

        data_dump = dict()
        economic_model_data = super().to_dict()

        economic_model_data["bs_id"] = self.BSEM_bs_id
        economic_model_data["bs_deploy"] = str(self.BSEM_deployment_cost)
        economic_model_data["bs_equipment"] = str(self.BSEM_equipment_cost)
        economic_model_data["bs_oam"] = str(self.BSEM_oam_cost)
        economic_model_data["bs_rent"] = str(self.BSEM_site_rent_cost)

        data_dump[time] = economic_model_data

        with open(file_path + self.BSEM_bs_id + "/" + self.EM_id, 'a') as json_file:
            json.dump(data_dump, json_file)

    def calculate_capex(self):
        """
            It calculates the capital expenditures of base station.

            :return [float] capex: capital expenditures of base station (in €).
        """

        capex = self.BSEM_deployment_cost + self.BSEM_equipment_cost
        self.EM_total_capex = capex

        return capex

    def calculate_opex(self, consumed_power: float, simulation_time: float):
        """
            It calculates the operational expenditures of base station.

            :param consumed_power: total consumed power for BS in the simulation (in Kw).
            :param simulation_time: total simulation time (in seconds).

            :return [float] opex: operational expenditures of base station (in € per year).
        """

        consumed_power_per_day = (24 * 3600 * consumed_power) / simulation_time

        opex = self.BSEM_oam_cost + self.BSEM_site_rent_cost + (consumed_power_per_day*self.OPEX_kwh_cost*365*24)
        self.EM_total_opex = opex

        return opex
