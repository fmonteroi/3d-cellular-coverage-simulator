# TEST "base_stations.py"

from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import MacroBS, SmallBS

# * Create base stations with different configurations

# MACRO NODEB CONFIGURATION
macro_nodeb_economic_model = None
macro_nodeb_power_model = None
macro_nodeb_total_user_bandwidth = 500
macro_nodeb_bandwidth_plannification = "standard"
macro_nodeb_configuration = dict({"economic_model": macro_nodeb_economic_model, "power_model": macro_nodeb_power_model, "total_user_bandwidth": macro_nodeb_total_user_bandwidth, "bandwidth_plannification": macro_nodeb_bandwidth_plannification})

# MACRO ANTENNA CONFIGURATION (omnidirectional)
macro_antenna_model = "omnidirectional"
macro_antenna_economic_model = None
macro_antenna_power_model = None
macro_antenna_height = 30
macro_antenna_frequency = 2
macro_antenna_tx_power = 28
macro_antenna_ntx = 4
macro_antenna_gain = 12
macro_backhaul_antenna_height = 20
macro_backhaul_antenna_frequency = 21
macro_backhaul_antenna_scanning_range_azimuth = 30
macro_backhaul_antenna_scanning_range_tilt = 20
macro_backhaul_antenna_n_tx = 9
macro_backhaul_antenna_p_tx = 12
macro_backhaul_antenna_gain = 9
macro_backhaul_antenna_bandwidth = 20
macro_backhaul_antenna_parameters = dict({"height": macro_backhaul_antenna_height, "frequency": macro_backhaul_antenna_frequency, "scanning_range_azimuth": macro_backhaul_antenna_scanning_range_azimuth, "scanning_range_tilt": macro_backhaul_antenna_scanning_range_tilt, "n_tx": macro_backhaul_antenna_n_tx, "p_tx": macro_backhaul_antenna_p_tx, "gain": macro_backhaul_antenna_gain, "bandwidth": macro_backhaul_antenna_bandwidth})
macro_antenna_configuration = dict({"antenna_model": macro_antenna_model, "economic_model": macro_antenna_economic_model, "power_model": macro_antenna_power_model, "height": macro_antenna_height, "frequency": macro_antenna_frequency, "tx_power": macro_antenna_tx_power, "ntx": macro_antenna_ntx, "gain": macro_antenna_gain, "backhaul_antennas_parameters": macro_backhaul_antenna_parameters})

# SMALL NODEB CONFIGURATION
small_nodeb_economic_model = None
small_nodeb_power_model = None
small_nodeb_total_user_bandwidth = 750
small_nodeb_bandwidth_plannification = "standard"
small_nodeb_configuration = dict({"economic_model": small_nodeb_economic_model, "power_model": small_nodeb_power_model, "total_user_bandwidth": small_nodeb_total_user_bandwidth, "bandwidth_plannification": small_nodeb_bandwidth_plannification})

# SMALL ANTENNA CONFIGURATION (omnidirectional)
small_antenna_model = "omnidirectional"
small_antenna_economic_model = None
small_antenna_power_model = None
small_antenna_height = 15
small_antenna_frequency = 28
small_antenna_tx_power = 12
small_antenna_ntx = 25
small_antenna_gain = 6
small_backhaul_antenna_height = 15
small_backhaul_antenna_frequency = 21
small_backhaul_antenna_scanning_range_azimuth = 30
small_backhaul_antenna_scanning_range_tilt = 20
small_backhaul_antenna_n_tx = 9
small_backhaul_antenna_p_tx = 12
small_backhaul_antenna_gain = 9
small_backhaul_antenna_bandwidth = 100
small_backhaul_antenna_parameters = dict({"height": small_backhaul_antenna_height, "frequency": small_backhaul_antenna_frequency, "scanning_range_azimuth": small_backhaul_antenna_scanning_range_azimuth, "scanning_range_tilt": small_backhaul_antenna_scanning_range_tilt, "n_tx": small_backhaul_antenna_n_tx, "p_tx": small_backhaul_antenna_p_tx, "gain": small_backhaul_antenna_gain, "bandwidth": macro_backhaul_antenna_bandwidth})
small_antenna_configuration = dict({"antenna_model": small_antenna_model, "economic_model": small_antenna_economic_model, "power_model": small_antenna_power_model, "height": small_antenna_height, "frequency": small_antenna_frequency, "tx_power": small_antenna_tx_power, "ntx": small_antenna_ntx, "gain": small_antenna_gain, "backhaul_antennas_parameters": small_backhaul_antenna_parameters})

# Create base stations
bs_1 = MacroBS("MACRO_BS_1", (25, 25), None, None, macro_nodeb_configuration, macro_antenna_configuration, 1000, 1000)
bs_2 = MacroBS("MACRO_BS_2", (70, 100), None, None, macro_nodeb_configuration, macro_antenna_configuration, 1000, 1000)
bs_3 = SmallBS("SMALL_BS_1", "MICRO", (10, 10), None, None, small_nodeb_configuration, small_antenna_configuration, 400)
bs_4 = SmallBS("SMALL_BS_2", "MICRO", (60, 50), None, None, small_nodeb_configuration, small_antenna_configuration, 400)
bs_5 = SmallBS("SMALL_BS_3", "MICRO", (5, 23), None, None, small_nodeb_configuration, small_antenna_configuration, 400)
bs_6 = SmallBS("SMALL_BS_4", "MICRO", (24, 75), None, None, small_nodeb_configuration, small_antenna_configuration, 400)
bs_7 = SmallBS("SMALL_BS_5", "MICRO", (100, 1), None, None, small_nodeb_configuration, small_antenna_configuration, 400)

print(bs_1.__str__())
print("-------------")
print(bs_1.BS_cell.__str__())
print("-------------")
print(bs_1.BS_node.__str__())
print("-------------")
print(bs_1.BS_antenna.__str__())
print("-------------")
print(bs_1.BS_backhaul_block.__str__())
print("-------------")
print(bs_1.MBS_fronthaul_block.__str__())
print("\n")
print(bs_2.__str__())
print("-------------")
print(bs_2.BS_cell.__str__())
print("-------------")
print(bs_2.BS_node.__str__())
print("-------------")
print(bs_2.BS_antenna.__str__())
print("-------------")
print(bs_2.BS_backhaul_block.__str__())
print("-------------")
print(bs_2.MBS_fronthaul_block.__str__())
print("\n")
print(bs_3.__str__())
print("-------------")
print(bs_3.BS_cell.__str__())
print("-------------")
print(bs_3.BS_node.__str__())
print("-------------")
print(bs_3.BS_antenna.__str__())
print("-------------")
print(bs_3.BS_backhaul_block.__str__())
print("\n")
print(bs_4.__str__())
print("-------------")
print(bs_4.BS_cell.__str__())
print("-------------")
print(bs_4.BS_node.__str__())
print("-------------")
print(bs_4.BS_antenna.__str__())
print("-------------")
print(bs_4.BS_backhaul_block.__str__())
print("\n")
print(bs_5.__str__())
print("-------------")
print(bs_5.BS_cell.__str__())
print("-------------")
print(bs_5.BS_node.__str__())
print("-------------")
print(bs_5.BS_antenna.__str__())
print("-------------")
print(bs_5.BS_backhaul_block.__str__())
print("\n")
print(bs_6.__str__())
print("-------------")
print(bs_6.BS_cell.__str__())
print("-------------")
print(bs_6.BS_node.__str__())
print("-------------")
print(bs_6.BS_antenna.__str__())
print("-------------")
print(bs_6.BS_backhaul_block.__str__())
print("\n")
print(bs_7.__str__())
print("-------------")
print(bs_7.BS_cell.__str__())
print("-------------")
print(bs_7.BS_node.__str__())
print("-------------")
print(bs_7.BS_antenna.__str__())
print("-------------")
print(bs_7.BS_backhaul_block.__str__())
print("\n")
