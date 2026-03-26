# Test "bs_antennas.py"

from SIMULATOR.src.CELLULAR_NETWORK.base_stations.bs_antennas import OmnidirectionalAntenna, DirectionalAntenna, TriSectorAntenna

test_rx_position = (25, 25)
test_rx_height = 1.5
test_tx_position = (100, 100)

# * Test omnidirectional antenna
omnidirectional_antenna = OmnidirectionalAntenna("ANTENNA_TEST_1", "MACRO", None, None, 30, 4, 2, 12, 18, 200)
# print(omnidirectional_antenna.__str__())

# * Test directional antenna
n_panels = 1
n_tx_per_panel = 9
beams_per_panel = 2
p_tx_per_beam = 21
gain_per_beam = 12
beam_z_width = 20
beam_y_width = 20

beams_configuration = dict({"beams_per_panel": beams_per_panel, "p_tx_per_beam": p_tx_per_beam, "gain_per_beam": gain_per_beam, "z_width": beam_z_width, "y_width": beam_y_width})
subpanel_configuration = dict({"n_panels": n_panels, "n_tx_per_panel": n_tx_per_panel, "beams_configuration": beams_configuration})

directional_antenna = DirectionalAntenna("ANTENNA_TEST_2", "SMALL", None, None, 12, 34, 400, 30, 120, 10, 20, subpanel_configuration, "/home/jricopal/Escritorio/Mgain_34GHz_360.mat")

# print(directional_antenna.__str__())
# print("--------")
# print(directional_antenna.DIRANTENNA_subpanels[0].__str__())
# print("--------")
# print(directional_antenna.DIRANTENNA_subpanels[0].PANEL_beams[1].__str__())

# current_tx_power = directional_antenna.get_tx_power(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=directional_antenna.ANTENNA_height)
# print(" - Current TX power: " + str(current_tx_power) + " dBm")

# current_frequency = directional_antenna.get_frequency(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=directional_antenna.ANTENNA_height)
# print(" - Current frequency: " + str(current_frequency) + " GHz")

# current_n_tx = directional_antenna.get_ntx(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=directional_antenna.ANTENNA_height)
# print(" - Current number mimo antennas: " + str(current_n_tx))

# current_gain = directional_antenna.get_gain(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=directional_antenna.ANTENNA_height)
# print(" - Current gain: " + str(current_gain) + " dBi")

# * Test trisector antenna
panel_configuration = dict()
sector_1_configuration = dict()
sector_1_configuration["p_tx"] = 12
sector_1_configuration["gain"] = 9
sector_1_configuration["n_tx"] = 4
panel_configuration["sector_1"] = sector_1_configuration
sector_2_configuration = dict()
sector_2_configuration["p_tx"] = 12
sector_2_configuration["gain"] = 9
sector_2_configuration["n_tx"] = 4
panel_configuration["sector_2"] = sector_2_configuration
sector_3_configuration = dict()
sector_3_configuration["p_tx"] = 12
sector_3_configuration["gain"] = 9
sector_3_configuration["n_tx"] = 4
panel_configuration["sector_3"] = sector_3_configuration

trisector_antenna = TriSectorAntenna("ANTENNA_TEST_3", "MACRO", None, None, 12, 2, 400, "/home/jricopal/Escritorio/Mgain_34GHz_360.mat", panel_configuration)

current_tx_power = trisector_antenna.get_tx_power(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=trisector_antenna.ANTENNA_height)
print(" - Current TX power: " + str(current_tx_power) + " dBm")

current_frequency = trisector_antenna.get_frequency(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=trisector_antenna.ANTENNA_height)
print(" - Current frequency: " + str(current_frequency) + " GHz")

current_n_tx = trisector_antenna.get_ntx(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=trisector_antenna.ANTENNA_height)
print(" - Current number mimo antennas: " + str(current_n_tx))

current_gain = trisector_antenna.get_gain(test_rx_position, test_tx_position, rx_height=test_rx_height, tx_height=trisector_antenna.ANTENNA_height)
print(" - Current gain: " + str(current_gain) + " dBi")

# TODO: test radiation patterns
# TODO: test plot

# * Test 'to_json' method
omnidirectional_antenna.to_json(1, file_path="/home/jricopal/Escritorio/")
directional_antenna.to_json(1, file_path="/home/jricopal/Escritorio/")
trisector_antenna.to_json(1, file_path="/home/jricopal/Escritorio/")

