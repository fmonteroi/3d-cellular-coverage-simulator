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
    """Parse the command line arguments sent by Unity."""
    parser = argparse.ArgumentParser(description="Unity to simulator TCP bridge.")
    parser.add_argument("--port", type=int, required=True, help="Local TCP port.")
    parser.add_argument(
        "--sim-root", required=True, help="Absolute path to the simulator root."
    )
    return parser.parse_args()


def install_simulator_package(sim_root: str):
    """Register the simulator root as the SIMULATOR package."""
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
    disable_shadowing: bool,
):
    """Read the channel parameters from the simulator config files."""
    if losses_model == "FSPL":
        return None

    config_path = os.path.join(
        sim_root,
        "Configuration",
        "model_config",
        "channels",
        f"SCENARIO_{scenario}_{environment_type}",
    )

    parser = configparser.ConfigParser()

    if not parser.read(config_path):
        raise FileNotFoundError(f"Channel configuration not found: {config_path}")

    if losses_model not in parser:
        raise ValueError(
            f"Loss model '{losses_model}' is not configured in {config_path}"
        )

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
        raise ValueError(
            f"Loss model '{losses_model}' is not supported by this bridge."
        )

    return parameters


def get_channel(request: dict, sim_root: str):
    """Get the current channel, reusing the last one if possible."""
    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    global CACHED_CHANNEL

    # Reuse channel if was already created
    if CACHED_CHANNEL is not None:
        return CACHED_CHANNEL
    
    model_parameters = get_model_parameters(
        sim_root=sim_root,
        scenario=request["scenario"],
        environment_type=request["environmentType"],
        losses_model=request["lossesModel"],
        disable_shadowing=request["disableShadowing"],
    )

    config_dir = (
        os.path.join(sim_root, "Configuration", "model_config", "channels") + os.sep
    )

    # Create the channel only once
    channel = Channel(
        channel_id="CHANNEL_1",
        scenario=request["scenario"],
        environment=request["environmentType"],
        losses_model=request["lossesModel"],
        model_parameters=model_parameters,
        config_file_path=config_dir,
    )

    CACHED_CHANNEL = channel
    return channel


def receive_json_request(connection: socket.socket):
    """Read one JSON request line from Unity."""
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


def send_json_response(connection: socket.socket, payload: dict):
    """Send one JSON response line to Unity."""
    message = json.dumps(payload, separators=(",", ":")) + "\n"
    connection.sendall(message.encode("utf-8"))


def build_error_response(error_message: str):
    """Build a standard error response."""
    return {"error": error_message, "results": [], "receiverResults": []}


def build_empty_success_response():
    """Build an empty success response."""
    return {"error": "", "results": [], "receiverResults": []}


def calculate_distance(
    tx_x: float, tx_y: float, tx_z: float, rx_x: float, rx_y: float, rx_z: float
):
    """Calculate the 3D distance between transmitter and receiver."""
    dx = rx_x - tx_x
    dy = rx_y - tx_y
    dz = rx_z - tx_z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def calculate_propagation_latency_ms(distance_meters: float):
    """Calculate propagation latency from the traveled distance."""
    speed_of_light_mps = 299792458.0
    return (distance_meters / speed_of_light_mps) * 1000.0


def read_common_request_data(request: dict):
    """Extract the common values shared by all link calculations."""
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
    building_loss_db: float,
):
    """Calculate the basic metrics of one transmitter-receiver link."""
    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    # Compute 3D distance
    distance = calculate_distance(
        common_data["tx_x"],
        common_data["tx_y"],
        common_data["tx_z"],
        rx_x,
        rx_y,
        rx_z,
    )

    # Clamp the minimum valid distance
    distance = max(distance, common_data["minimum_distance"])

    # Compute base channel loss
    base_path_loss_db = channel.path_loss(distance, common_data["frequency_ghz"])

    # Add extra building loss
    path_loss_db = base_path_loss_db + building_loss_db

    # Compute received power
    prx_dbm = Channel.link_budget(
        tx_power=common_data["tx_power_dbm"],
        tx_gain=tx_gain_dbi,
        rx_gain=common_data["rx_gain_dbi"],
        path_losses=path_loss_db,
    )

    return {
        "buildingCollisions": building_collisions,
        "buildingLossDb": building_loss_db,
        "distanceMeters": distance,
        "basePathLossDb": base_path_loss_db,
        "pathLossDb": path_loss_db,
        "prxDbm": prx_dbm,
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
    bandwidth_mhz: float,
):
    """Calculate the live metrics of one mobile receiver link."""
    basic_metrics = calculate_basic_link_metrics(
        channel=channel,
        common_data=common_data,
        rx_x=rx_x,
        rx_y=rx_y,
        rx_z=rx_z,
        tx_gain_dbi=tx_gain_dbi,
        building_collisions=building_collisions,
        building_loss_db=building_loss_db,
    )

    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
    import SIMULATOR.src.MATH_UTILS.formulas as f

    # Compute propagation latency
    propagation_latency_ms = calculate_propagation_latency_ms(
        basic_metrics["distanceMeters"]
    )

    # Convert received power from dBm to mW
    rx_power_mw = f.to_units(basic_metrics["prxDbm"])

    # Compute SNR as SINR without external interference
    snr_db = Channel.sinr(
        rx_power=rx_power_mw,
        bandwidth=bandwidth_mhz,
        interferences=0.0,
    )

    basic_metrics["propagationLatencyMs"] = propagation_latency_ms
    basic_metrics["snrDb"] = snr_db
    return basic_metrics




def simulate_grid(request: dict, sim_root: str):
    """Calculate metrics for all grid voxels."""
    channel = get_channel(request, sim_root)
    common_data = read_common_request_data(request)

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
            building_loss_db=float(voxel.get("buildingLossDb", 0.0)),
        )

        results.append(
            {
                "index": int(voxel["index"]),
                "buildingCollisions": metrics["buildingCollisions"],
                "buildingLossDb": metrics["buildingLossDb"],
                "distanceMeters": metrics["distanceMeters"],
                "pathLossDb": metrics["pathLossDb"],
                "prxDbm": metrics["prxDbm"],
            }
        )

    return {"error": "", "results": results, "receiverResults": []}


def simulate_mobile_receivers(request: dict, sim_root: str):
    """Calculate live metrics for all mobile receivers."""
    channel = get_channel(request, sim_root)
    common_data = read_common_request_data(request)

    receiver_results = []

    for receiver in request["receivers"]:
        metrics = calculate_mobile_link_metrics(
            channel=channel,
            common_data=common_data,
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
                "snrDb": metrics["snrDb"],
                "propagationLatencyMs": metrics["propagationLatencyMs"],
            }
        )

    return {"error": "", "results": [], "receiverResults": receiver_results}


def process_request(request: dict, sim_root: str):
    """Route the request to the correct simulation path."""
    request_type = request.get("requestType", "grid")

    if request_type == "shutdown":
        return build_empty_success_response(), True

    if request_type == "grid":
        return simulate_grid(request, sim_root), False

    if request_type == "mobile_receivers":
        return simulate_mobile_receivers(request, sim_root), False

    return build_error_response(f"Unsupported requestType: {request_type}"), False


def main():
    """Run a persistent local TCP bridge."""
    args = parse_args()

    # Register the simulator package once
    install_simulator_package(args.sim_root)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Configures the TCP server
        # Allows to reuse the same port immediately after restarting the bridge
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
