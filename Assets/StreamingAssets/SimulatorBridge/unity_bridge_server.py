"""Runs a local TCP bridge between Unity and the original simulator."""

import argparse
import configparser
import json
import math
import os
import socket
import sys
import types

# Caches the last created channel
CACHED_CHANNEL = None


def parse_args():
    """Parses the command line arguments sent by Unity.

    Returns:
        Parsed arguments with the TCP port and simulator root path.
    """
    parser = argparse.ArgumentParser(description="Unity to simulator TCP bridge.")
    parser.add_argument("--port", type=int, required=True, help="Local TCP port.")
    parser.add_argument("--sim-root", required=True, help="Absolute path to the simulator root.")
    return parser.parse_args()


def install_simulator_package(sim_root: str):
    """Registers the simulator root as the SIMULATOR package.

    Args:
        sim_root: Absolute path to the original simulator root folder.
    """
    sim_root = os.path.abspath(sim_root)

    if "SIMULATOR" in sys.modules:
        return

    simulator_package = types.ModuleType("SIMULATOR")
    simulator_package.__path__ = [sim_root]
    sys.modules["SIMULATOR"] = simulator_package


def get_model_parameters(
    sim_root: str,
    scenario: str,
    environment_type: str,
    losses_model: str,
    disable_shadowing: bool
):
    """Reads the channel parameters from the simulator config files.

    Args:
        sim_root: Absolute path to the original simulator root folder.
        scenario: Propagation scenario selected in Unity.
        environment_type: Environment type selected in Unity.
        losses_model: Path loss model selected in Unity.
        disable_shadowing: True when shadowing must be forced to zero.

    Returns:
        Dictionary with the model parameters required by the original channel,
        or None when the selected model does not need a config file.
    """
    if losses_model == "FSPL":
        return None

    config_path = os.path.join(sim_root, "Configuration", "model_config", "channels", f"SCENARIO_{scenario}_{environment_type}")

    parser = configparser.ConfigParser()

    if not parser.read(config_path):
        raise FileNotFoundError(f"Channel configuration not found: {config_path}")

    if losses_model not in parser:
        raise ValueError(f"Loss model '{losses_model}' is not configured in {config_path}")

    parameters = {"losses_model": losses_model}

    if losses_model == "ABG":
        parameters["alpha"] = parser[losses_model]["alpha"]
        parameters["beta"] = parser[losses_model]["beta"]
        parameters["gamma"] = parser[losses_model]["gamma"]
        if disable_shadowing:
            # Disables shadowing by forcing the factor to zero
            parameters["shadow_factor"] = "0"
        else:
            # Uses the configured shadowing factor
            parameters["shadow_factor"] = parser[losses_model]["shadow_factor"]
    else:
        raise ValueError(f"Loss model '{losses_model}' is not supported by this bridge.")

    return parameters


def get_channel(request: dict, sim_root: str):
    """Gets the current channel, reusing the last one if possible.

    Args:
        request: Unity request containing scenario, environment and loss model.
        sim_root: Absolute path to the original simulator root folder.

    Returns:
        Original simulator Channel instance used for propagation calculations.
    """
    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    global CACHED_CHANNEL

    # Reuses the channel if it was already created
    if CACHED_CHANNEL is not None:
        return CACHED_CHANNEL

    model_parameters = get_model_parameters(
        sim_root=sim_root,
        scenario=request["scenario"],
        environment_type=request["environmentType"],
        losses_model=request["lossesModel"],
        disable_shadowing=request["disableShadowing"]
    )

    config_dir = (os.path.join(sim_root, "Configuration", "model_config", "channels") + os.sep)

    # Creates the channel only once
    channel = Channel(
        channel_id="CHANNEL_1",
        scenario=request["scenario"],
        environment=request["environmentType"],
        losses_model=request["lossesModel"],
        model_parameters=model_parameters,
        config_file_path=config_dir
    )

    CACHED_CHANNEL = channel
    return channel


def receive_json_request(connection: socket.socket):
    """Reads one JSON request line from Unity.

    Args:
        connection: TCP socket connected to Unity.

    Returns:
        Request dictionary decoded from UTF-8 JSON.
    """
    data = bytearray()

    while True:
        chunk = connection.recv(65536)

        if not chunk:
            break

        newline_index = chunk.find(b"\n")

        if newline_index >= 0:
            data.extend(chunk[:newline_index])
            break

        data.extend(chunk)

    if not data:
        raise RuntimeError("Unity sent an empty request.")

    return json.loads(data.decode("utf-8"))


def send_json_response(connection: socket.socket, response: dict):
    """Sends one JSON response line to Unity.

    Args:
        connection: TCP socket connected to Unity.
        response: Response dictionary that will be encoded as JSON.
    """
    message = json.dumps(response, separators=(",", ":")) + "\n"
    connection.sendall(message.encode("utf-8"))


def build_error_response(error_message: str):
    """Builds a standard error response.

    Args:
        error_message: Error text that Unity will display or log.

    Returns:
        Response dictionary with empty result lists.
    """
    return {"error": error_message, "results": [], "receiverResults": []}


def build_empty_success_response():
    """Builds an empty success response.

    Returns:
        Response dictionary without errors and without simulation results.
    """
    return {"error": "", "results": [], "receiverResults": []}


def calculate_distance(
    tx_x: float, tx_y: float, tx_z: float, rx_x: float, rx_y: float, rx_z: float
):
    """Calculates the 3D distance between transmitter and receiver.

    Args:
        tx_x: Transmitter X position in Unity world meters.
        tx_y: Transmitter Y position in Unity world meters.
        tx_z: Transmitter Z position in Unity world meters.
        rx_x: Receiver X position in Unity world meters.
        rx_y: Receiver Y position in Unity world meters.
        rx_z: Receiver Z position in Unity world meters.

    Returns:
        Distance between transmitter and receiver in meters.
    """
    dx = rx_x - tx_x
    dy = rx_y - tx_y
    dz = rx_z - tx_z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def read_common_link_data(request: dict):
    """Extracts the common values shared by all link calculations.

    Args:
        request: Unity request containing transmitter and propagation values.

    Returns:
        Dictionary with shared link values using simulator units.
    """
    return {
        "tx_x": float(request["transmitterX"]),
        "tx_y": float(request["transmitterY"]),
        "tx_z": float(request["transmitterZ"]),
        "tx_power_dbm": float(request["txPowerDbm"]),
        "rx_gain_dbi": float(request["rxGainDbi"]),
        "frequency_ghz": float(request["frequencyGHz"]),
        "minimum_distance": max(float(request["minimumDistanceMeters"]), 0.001),
        "bandwidth_mhz": max(float(request["bandwidthMHz"]), 0.001)
    }


def calculate_basic_link_metrics(
    channel,
    common_data: dict,
    rx_x: float,
    rx_y: float,
    rx_z: float,
    tx_gain_dbi: float,
    building_collisions: int,
    building_loss_db: float
):
    """Calculates the basic metrics of one transmitter-receiver link.

    Args:
        channel: Original simulator Channel instance.
        common_data: Shared link values from read_common_link_data.
        rx_x: Receiver X position in Unity world meters.
        rx_y: Receiver Y position in Unity world meters.
        rx_z: Receiver Z position in Unity world meters.
        tx_gain_dbi: Transmitter antenna gain for this direction in dBi.
        building_collisions: Number of building collisions detected by Unity.
        building_loss_db: Extra propagation loss caused by buildings in dB.

    Returns:
        Dictionary with distance, path loss, building loss and received power.
    """
    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    # Computes 3D distance
    distance = calculate_distance(common_data["tx_x"], common_data["tx_y"], common_data["tx_z"], rx_x, rx_y, rx_z)

    # Clamps the minimum valid distance
    distance = max(distance, common_data["minimum_distance"])

    # Computes base channel loss
    base_path_loss_db = channel.path_loss(distance, common_data["frequency_ghz"])

    # Adds extra building loss
    path_loss_db = base_path_loss_db + building_loss_db

    # Computes received power
    prx_dbm = Channel.link_budget(
        tx_power=common_data["tx_power_dbm"],
        tx_gain=tx_gain_dbi,
        rx_gain=common_data["rx_gain_dbi"],
        path_losses=path_loss_db
    )

    return {
        "buildingCollisions": building_collisions,
        "buildingLossDb": building_loss_db,
        "distanceMeters": distance,
        "basePathLossDb": base_path_loss_db,
        "pathLossDb": path_loss_db,
        "prxDbm": prx_dbm
    }


def calculate_mobile_link_metrics(
    channel,
    common_data: dict,
    rx_x: float,
    rx_y: float,
    rx_z: float,
    tx_gain_dbi: float,
    building_collisions: int,
    building_loss_db: float,
    bandwidth_mhz: float
):
    """Calculates the live metrics of one mobile receiver link.

    Args:
        channel: Original simulator Channel instance.
        common_data: Shared link values with the receiver gain already applied.
        rx_x: Receiver X position in Unity world meters.
        rx_y: Receiver Y position in Unity world meters.
        rx_z: Receiver Z position in Unity world meters.
        tx_gain_dbi: Transmitter antenna gain for this direction in dBi.
        building_collisions: Number of building collisions detected by Unity.
        building_loss_db: Extra propagation loss caused by buildings in dB.
        bandwidth_mhz: Channel bandwidth used by the SNR calculation in MHz.

    Returns:
        Dictionary with basic link metrics plus SNR in dB.
    """
    basic_metrics = calculate_basic_link_metrics(
        channel=channel,
        common_data=common_data,
        rx_x=rx_x,
        rx_y=rx_y,
        rx_z=rx_z,
        tx_gain_dbi=tx_gain_dbi,
        building_collisions=building_collisions,
        building_loss_db=building_loss_db
    )

    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
    import SIMULATOR.src.MATH_UTILS.formulas as f

    # Converts received power from dBm to mW
    rx_power_mw = f.to_units(basic_metrics["prxDbm"])

    # Computes SNR as SINR without external interference
    snr_db = Channel.sinr(
        rx_power=rx_power_mw,
        bandwidth=bandwidth_mhz,
        interferences=0.0
    )

    basic_metrics["snrDb"] = snr_db
    return basic_metrics


def simulate_grid(request: dict, sim_root: str):
    """Calculates metrics for all grid voxels.

    Args:
        request: Unity grid request containing voxel positions and gains.
        sim_root: Absolute path to the original simulator root folder.

    Returns:
        Response dictionary with one result entry per voxel.
    """
    channel = get_channel(request, sim_root)
    common_data = read_common_link_data(request)

    results = []

    for voxel in request["voxels"]:
        metrics = calculate_basic_link_metrics(
            channel=channel,
            common_data=common_data,
            rx_x=float(voxel["x"]),
            rx_y=float(voxel["y"]),
            rx_z=float(voxel["z"]),
            tx_gain_dbi=float(voxel["txGainDbi"]),
            building_collisions=int(voxel.get("buildingCollisions", 0)),
            building_loss_db=float(voxel.get("buildingLossDb", 0.0))
        )

        results.append(
            {
                "index": int(voxel["index"]),
                "buildingCollisions": metrics["buildingCollisions"],
                "buildingLossDb": metrics["buildingLossDb"],
                "distanceMeters": metrics["distanceMeters"],
                "pathLossDb": metrics["pathLossDb"],
                "prxDbm": metrics["prxDbm"]
            }
        )

    return {"error": "", "results": results, "receiverResults": []}


def simulate_mobile_receivers(request: dict, sim_root: str):
    """Calculates live metrics for all mobile receivers.

    Args:
        request: Unity request containing all mobile receiver positions.
        sim_root: Absolute path to the original simulator root folder.

    Returns:
        Response dictionary with one result entry per mobile receiver.
    """
    channel = get_channel(request, sim_root)
    common_data = read_common_link_data(request)

    receiver_results = []

    for receiver in request["receivers"]:
        # Adds the specific receiver gain for mobile receivers
        receiver_link_data = common_data.copy()
        receiver_link_data["rx_gain_dbi"] = float(
            receiver.get("rxGainDbi", common_data["rx_gain_dbi"])
        )

        metrics = calculate_mobile_link_metrics(
            channel=channel,
            common_data=receiver_link_data,
            rx_x=float(receiver["x"]),
            rx_y=float(receiver["y"]),
            rx_z=float(receiver["z"]),
            tx_gain_dbi=float(receiver["txGainDbi"]),
            building_collisions=int(receiver.get("buildingCollisions", 0)),
            building_loss_db=float(receiver.get("buildingLossDb", 0.0)),
            bandwidth_mhz=common_data["bandwidth_mhz"]
        )

        receiver_results.append(
            {
                "id": str(receiver["id"]),
                "txGainDbi": float(receiver["txGainDbi"]),
                "buildingCollisions": metrics["buildingCollisions"],
                "buildingLossDb": metrics["buildingLossDb"],
                "distanceMeters": metrics["distanceMeters"],
                "basePathLossDb": metrics["basePathLossDb"],
                "pathLossDb": metrics["pathLossDb"],
                "prxDbm": metrics["prxDbm"],
                "snrDb": metrics["snrDb"]
            }
        )

    return {"error": "", "results": [], "receiverResults": receiver_results}


def process_request(request: dict, sim_root: str):
    """Routes the request to the correct simulation path.

    Args:
        request: Unity request containing the requestType field.
        sim_root: Absolute path to the original simulator root folder.

    Returns:
        Tuple with the response dictionary and the shutdown flag.
    """
    request_type = request.get("requestType", "grid")

    if request_type == "shutdown":
        return build_empty_success_response(), True

    if request_type == "grid":
        return simulate_grid(request, sim_root), False

    if request_type == "mobile_receivers":
        return simulate_mobile_receivers(request, sim_root), False

    return build_error_response(f"Unsupported requestType: {request_type}"), False


def main():
    """Runs a persistent local TCP bridge.

    The server listens on localhost, receives one JSON request per connection,
    sends one JSON response, and stops only when Unity sends shutdown.
    """
    args = parse_args()

    # Registers the simulator package once
    install_simulator_package(args.sim_root)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Configures the TCP server
        # Allows reusing the same port immediately after restarting the bridge
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", args.port))
        server.listen(8)
        server.settimeout(None)

        print(f"Bridge listening on 127.0.0.1:{args.port}", flush=True)

        while True:
            connection, _ = server.accept()
            with connection:
                connection.settimeout(30.0)

                try:
                    request = receive_json_request(connection)
                    response, should_stop = process_request(request, args.sim_root)
                except Exception as ex:
                    response = build_error_response(str(ex))
                    should_stop = False

                send_json_response(connection, response)

                if should_stop:
                    print("Bridge shutdown requested", flush=True)
                    break


if __name__ == "__main__":
    main()
