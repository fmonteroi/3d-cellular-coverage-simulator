import argparse
import configparser
import json
import math
import os
import socket
import sys
import types


def parse_args():
    """Parse the command line arguments sent by Unity."""
    parser = argparse.ArgumentParser(description="Unity to simulator TCP bridge.")
    parser.add_argument("--port", type=int, required=True, help="Local TCP port.")
    parser.add_argument(
        "--sim-root", required=True, help="Absolute path to the simulator root."
    )
    return parser.parse_args()


def install_simulator_package(sim_root: str):
    """Register the simulator root as the SIMULATOR package.

    This allows Python to import modules seeing SIMULATOR as a valid package.
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
        parameters["shadow_factor"] = ("0" if disable_shadowing else parser[losses_model]["shadow_factor"])
    else:
        raise ValueError(
            f"Loss model '{losses_model}' is not supported by this bridge."
        )

    return parameters


def receive_json_request(connection: socket.socket):
    """Read one JSON request line from Unity."""
    data = bytearray()

    while True:
        # Read up to 64KB
        chunk = connection.recv(65536)

        # If chunk is empty
        if not chunk:
            break

        # Check if the chunk contains a newline character, which indicates the end of the JSON message
        newline_index = chunk.find(b"\n")

        # If a newline is found, append only the part of the chunk up to the newline and stop reading further
        if newline_index >= 0:
            data.extend(chunk[:newline_index])
            break

        # Otherwise, append the entire chunk and continue reading
        data.extend(chunk)

    if not data:
        raise RuntimeError("Unity sent an empty request.")

    return json.loads(data.decode("utf-8"))


def send_json_response(connection: socket.socket, payload: dict):
    """Send one JSON response line to Unity."""
    # Converts Python dictionary to a JSON
    message = json.dumps(payload, separators=(",", ":")) + "\n"
    # Send the JSON message as bytes
    connection.sendall(message.encode("utf-8"))


def calculate_distance(
    tx_x: float, tx_y: float, tx_z: float, rx_x: float, rx_y: float, rx_z: float
):
    """Calculate the 3D distance between transmitter and receiver."""
    dx = rx_x - tx_x
    dy = rx_y - tx_y
    dz = rx_z - tx_z
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def simulate(request: dict, sim_root: str):
    """Calculate path loss and received power for all voxel centers."""
    # The import is realized here to ensure the SIMULATOR package is already registered
    from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel

    # Load channel parameters
    model_parameters = get_model_parameters(
        sim_root=sim_root,
        scenario=request["scenario"],
        environment_type=request["environmentType"],
        losses_model=request["lossesModel"],
        disable_shadowing=request["disableShadowing"],
    )

    # Builds the path to the channel directory
    config_dir = (
        os.path.join(sim_root, "Configuration", "model_config", "channels") + os.sep
    )

    # Initializes propagation channel
    channel = Channel(
        channel_id="CHANNEL_1",
        scenario=request["scenario"],
        environment=request["environmentType"],
        losses_model=request["lossesModel"],
        model_parameters=model_parameters,
        config_file_path=config_dir,
    )

    # Read parameters from the request

    # Transmitter position
    tx_x = float(request["transmitterX"])
    tx_y = float(request["transmitterY"])
    tx_z = float(request["transmitterZ"])

    # Transmitter power, receiver gain and frequency
    tx_power_dbm = float(request["txPowerDbm"])
    rx_gain_dbi = float(request["rxGainDbi"])
    frequency_ghz = float(request["frequencyGHz"])
    minimum_distance = max(float(request["minimumDistanceMeters"]), 0.001)

    # Results list
    results = []

    for voxel in request["voxels"]:
        # Calculate the distance between the transmitter and the voxel center
        distance = calculate_distance(
            tx_x,
            tx_y,
            tx_z,
            float(voxel["x"]),
            float(voxel["y"]),
            float(voxel["z"]),
        )

        # Ensure the distance is not below the minimum distance
        distance = max(distance, minimum_distance)

        # Calculates path loss
        base_path_loss_db = channel.path_loss(distance, frequency_ghz)
        
        # Adds the extra loss caused by crossed buildings
        building_loss_db = float(voxel.get("buildingLossDb", 0.0))
        path_loss_db = base_path_loss_db + building_loss_db

        # Calculates received power in dBm
        prx_dbm = Channel.link_budget(
            tx_power=tx_power_dbm,
            tx_gain=float(voxel["txGainDbi"]),
            rx_gain=rx_gain_dbi,
            path_losses=path_loss_db,
        )

        # Append the result for this voxel
        results.append(
            {
                "index": int(voxel["index"]),
                "buildingCollisions": int(voxel.get("buildingCollisions", 0)),
                "buildingLossDb": building_loss_db,
                "distanceMeters": distance,
                "pathLossDb": path_loss_db,
                "prxDbm": prx_dbm,
            }
        )

    return {"error": "", "results": results}


def main():
    """Run a one-shot local TCP bridge."""
    # Receives the port and simulator root path from Unity
    args = parse_args()

    # Registers the SIMULATOR package to allow importing simulator modules
    install_simulator_package(args.sim_root)

    # Creates a TCP socket
    # With: automatically close the server socket when done
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        # Socket configuration
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("127.0.0.1", args.port))
        server.listen(1)
        server.settimeout(30.0)

        # Notify Unity that the bridge is ready to accept one connection
        print(f"Bridge listening on 127.0.0.1:{args.port}", flush=True)

        # Accepts Unity's connection
        connection, _ = server.accept()

        # Processes the request and send the response
        with connection:
            connection.settimeout(30.0)
            try:
                request = receive_json_request(connection)
                response = simulate(request, args.sim_root)
            except Exception as ex:
                response = {"error": str(ex), "results": []}

            print(f"Response sent to Unity", flush=True)
            send_json_response(connection, response)


if __name__ == "__main__":
    main()
