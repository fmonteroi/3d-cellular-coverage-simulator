import configparser
import os
import statistics
import sys


def get_model_parameters(sim_root,scenario,environment,disable_shadowing,):
    config_path = os.path.join(sim_root,"Configuration","model_config","channels","SCENARIO_" + scenario + "_" + environment)

    config_file = configparser.ConfigParser()

    if not config_file.read(config_path):
        raise FileNotFoundError("Configuration file not found: " + config_path)

    parameters = {
        "losses_model": "ABG",
        "alpha": config_file["ABG"]["alpha"],
        "beta": config_file["ABG"]["beta"],
        "gamma": config_file["ABG"]["gamma"],
        "shadow_factor": config_file["ABG"]["shadow_factor"]
    }

    if disable_shadowing:
        parameters["shadow_factor"] = "0"

    return parameters


def main():
    # Test values
    tx_power_dbm = 30.0
    tx_gain_dbi = 14.19512
    rx_gain_dbi = 0.0
    distance_meters = 0.9526258
    frequency_ghz = 1.785
    scenario = "Umi"
    environment = "LOS"
    number_of_tests = 10000

    streaming_assets = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sim_root = os.path.join(streaming_assets, "SIMULATOR")

    # Allows Python to import the original simulator package
    sys.path.insert(0, streaming_assets)

    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    config_dir = os.path.join(sim_root,"Configuration","model_config","channels") + os.sep

    # Calculate once without shadowing.
    parameters_without_shadowing = get_model_parameters(sim_root,scenario,environment,True)

    channel_without_shadowing = Channel(
        channel_id="TEST_WITHOUT_SHADOWING",
        scenario=scenario,
        environment=environment,
        losses_model="ABG",
        model_parameters=parameters_without_shadowing,
        config_file_path=config_dir
    )

    path_loss_without_shadowing = channel_without_shadowing.path_loss(distance_meters,frequency_ghz)

    received_power_without_shadowing = Channel.link_budget(tx_power=tx_power_dbm,tx_gain=tx_gain_dbi,rx_gain=rx_gain_dbi,path_losses=path_loss_without_shadowing)

    # Calculate 100 times using the original shadowing
    channel_with_shadowing = Channel(
        channel_id="TEST_WITH_SHADOWING",
        scenario=scenario,
        environment=environment,
        losses_model="ABG",
        config_file_path=config_dir
    )

    path_loss_results = []
    received_power_results = []

    for i in range(number_of_tests):
        path_loss = channel_with_shadowing.path_loss(distance_meters,frequency_ghz)

        received_power = Channel.link_budget(tx_power=tx_power_dbm,tx_gain=tx_gain_dbi,rx_gain=rx_gain_dbi,path_losses=path_loss)

        path_loss_results.append(path_loss)
        received_power_results.append(received_power)

    print("--- Input data ---")
    print("Tx power:", tx_power_dbm, "dBm")
    print("Tx gain:", tx_gain_dbi, "dBi")
    print("Rx gain:", rx_gain_dbi, "dBi")
    print("Distance:", distance_meters, "m")
    print("Frequency:", frequency_ghz, "GHz")

    print()
    print("--- Without shadowing ---")
    print("Path loss:", path_loss_without_shadowing, "dB")
    print("Received power:", received_power_without_shadowing, "dBm")

    print()
    print("--- With shadowing:", number_of_tests, "tests ---")
    print("Average path loss:", statistics.mean(path_loss_results), "dB")
    print("Average received power:", statistics.mean(received_power_results), "dBm")
    print("Minimum received power:", min(received_power_results), "dBm")
    print("Maximum received power:", max(received_power_results), "dBm")
    print("Standard deviation:", statistics.stdev(received_power_results), "dB")


if __name__ == "__main__":
    main()