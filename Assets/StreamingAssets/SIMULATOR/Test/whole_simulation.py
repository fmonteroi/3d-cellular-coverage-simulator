# Test 'whole_simulation.py'

from operator import attrgetter
from SIMULATOR.src.MAP.simulation_map import SimulationMap
from SIMULATOR.src.CELLULAR_NETWORK.base_stations.base_stations import MacroBS, SmallBS
from SIMULATOR.src.PROPAGATION_CHANNEL.propagation_channel import Channel
import SIMULATOR.src.GEOMETRY.geometry_formulas as gf
from SIMULATOR.src.MOBILE_NODES.users import DynamicUser, StaticUser
import SIMULATOR.src.GEOMETRY.link_planifications as lp
import SIMULATOR.Test.jitel_2021_aux_methods as methods
from SIMULATOR.src.LINKS.rf_link import RFLink
from SIMULATOR.src.MODELS.latency_models import LatencyModel
from shapely.geometry import Point, Polygon
import json
import os.path
os.chdir("/home/jricopal/Documentos/Workspace/PythonSimulator_v6/")

# * SIMULATION CONFIGURATION
simulation_time = 60
link_planification = "sinr"  # "capacity_estimation" / "latency_estimation"
macro_user_bandwidth = 300
small_user_bandwidth = 900
num_dynamic_users = 20
num_static_users = 20

# * SIMULATION MAP -> size = 12000, n_macro = 4, n_small = 20
simulation_map = SimulationMap("MAP_0", map_configuration="jitel_2021")
# figure_map = PlotSimulationMap.complete_scenario(simulation_map)
# plt.savefig("/home/jricopal/Escritorio/simulation_map.svg", bbox_inches="tight")

# * CELLULAR NETWORK
base_stations = dict()

# macro nodeb configuration
macro_nodeb_economic_model = None
macro_nodeb_power_model = None
macro_nodeb_total_user_bandwidth = macro_user_bandwidth
macro_nodeb_bandwidth_plannification = "standard"
macro_nodeb_configuration = dict({"economic_model": macro_nodeb_economic_model, "power_model": macro_nodeb_power_model, "total_user_bandwidth": macro_nodeb_total_user_bandwidth, "bandwidth_plannification": macro_nodeb_bandwidth_plannification})

# macro antenna configuration
macro_antenna_model = "omnidirectional"
macro_antenna_economic_model = None
macro_antenna_power_model = None
macro_antenna_height = 40  # ? macro antenna configuration
macro_antenna_frequency = 6  # ? macro antenna configuration
macro_antenna_tx_power = 28  # ? macro antenna configuration
macro_antenna_ntx = 10  # ? macro antenna configuration
macro_antenna_gain = 12  # ? macro antenna configuration
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

# Generate macro cells
i = 0
for current_point in simulation_map.MAP_device_tessellation["macro"]["points"]:
    current_bs = MacroBS("MACRO_BS_"+str(i+1), current_point, None, None, macro_nodeb_configuration, macro_antenna_configuration, 1000, 1000)
    base_stations[current_bs.BS_id] = current_bs
    i += 1

# small nodeb configuration
small_nodeb_economic_model = None
small_nodeb_power_model = None
small_nodeb_total_user_bandwidth = small_user_bandwidth
small_nodeb_bandwidth_plannification = "standard"
small_nodeb_configuration = dict({"economic_model": small_nodeb_economic_model, "power_model": small_nodeb_power_model, "total_user_bandwidth": small_nodeb_total_user_bandwidth, "bandwidth_plannification": small_nodeb_bandwidth_plannification})

# small antenna configuration
small_antenna_model = "omnidirectional"
small_antenna_economic_model = None
small_antenna_power_model = None
small_antenna_height = 15  # ? macro antenna configuration
small_antenna_frequency = 21  # ? macro antenna configuration
small_antenna_tx_power = 12  # ? macro antenna configuration
small_antenna_ntx = 10  # ? macro antenna configuration
small_antenna_gain = 8  # ? macro antenna configuration
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

# Generate small cells
i = 0
for current_point in simulation_map.MAP_device_tessellation["small"]["points"]:
    current_bs = SmallBS("SMALL_BS_"+str(i+1), "small", current_point, None, None, small_nodeb_configuration, small_antenna_configuration, 1000)
    base_stations[current_bs.BS_id] = current_bs
    i += 1

# * USERS
users = dict()
antenna_parameters = dict({"height": 1.7, "n_rx": 4, "gain": 5})  # ? UE configuration
sim_parameters = dict({"type": "simple", "multiconnectivity_mode": "simple"})
traffic_parameters = dict({"model": "generic_demand", "num_demands": 2, "min_time": 2, "max_time": 25, "simulation_time": 20, "min_size": 10, "max_size": 20, "min_duration": 2, "max_duration": 5})
mobility_parameters = dict({"model": "RWP", "min_speed": 2, "max_speed": 5, "movement_time": simulation_time, "movement_height": simulation_map.MAP_size})
latency_model = LatencyModel("LATENCY_MODEL_1", model_parameters=dict({"mu": 70, "beta": 2, "sigma": 1}))

predefined_steps_flag = True  # ! get predefined steps (True) or random walks (False)
if predefined_steps_flag:
    with open("/home/jricopal/Escritorio/user_steps.json") as json_file:
        user_data = json.load(json_file)

for i in range(0, num_dynamic_users):

    if predefined_steps_flag:
        mobility_parameters["predefined_steps"] = user_data["USER_"+str(i+1)]

    current_user = DynamicUser("USER_"+str(i+1), mobility_parameters, antenna_parameters, sim_parameters, traffic_parameters, 10)
    users[current_user.USER_id] = current_user
    methods.connect_user_to_network(current_user.USER_id, users, base_stations, simulation_map, link_planification)  # Connect user when create (in first position)

user_id_offset = len(users)
for i in range(0, num_static_users):
    current_user = StaticUser("USER_"+str(i+1+user_id_offset), "sensor", antenna_parameters, sim_parameters, traffic_parameters, 10, map_size=simulation_map.MAP_size)
    users[current_user.USER_id] = current_user
    methods.connect_user_to_network(current_user.USER_id, users, base_stations, simulation_map, link_planification)  # Connect user when create (in static position)

# * PRESIMULATION
events = []
for current_user in users.values():
    if current_user.__class__.__name__ == "DynamicUser":
        [events.append(current_user.DUSER_steps[j]) for j in range(0, len(current_user.DUSER_steps))]  # Add steps from Dynamic users
events = sorted(events, key=attrgetter('EVENT_time'))

# * SIMULATION
results = []
results_times = []
for i in range(0, len(events)):
    current_event = events[i]

    best_bs_id = ""
    sinrs = dict()
    current_user = users[current_event.MNEVENT_user_id]

    if current_event.__class__.__name__ == "Step" and current_event.EVENT_time < simulation_time:

        old_bs = current_user.USER_ue.UE_sim.get_bs_connected()

        # Update position
        current_user.USER_position = current_event.STEP_position
        user_position = current_user.USER_position

        # Calculate candidate BS
        if link_planification == "sinr":
            best_bs_id, sinrs = lp.sinr_schedule_dl(current_user, base_stations, simulation_map, threshold=100)

        elif link_planification == "capacity_estimation":
            best_bs_id, capacities, sinrs = lp.capacity_estimation(current_user, base_stations, simulation_map)

        elif link_planification == "latency_estimation":
            best_bs_id, capacities, sinrs = lp.latency_estimation(current_user, base_stations, simulation_map, pilot_slot=0.01)

        if old_bs != best_bs_id:

            # Disconnect user from old bs
            base_stations[old_bs].disconnect_user(current_user.USER_id)

            # Connect user to new bs
            bw = base_stations[best_bs_id].connect_user(current_user.USER_id, current_user.USER_priority, 10, 0, "standard")

        else:
            bw = base_stations[best_bs_id].BS_node.NODEB_assigned_bandwidth[current_user.USER_id]

        # Update variables
        current_sinr = sinrs[best_bs_id]
        n_rx = current_user.USER_ue.UE_antenna.UEANTENNA_nrx
        user_height = current_user.USER_ue.UE_antenna.UEANTENNA_height
        bs_position = base_stations[best_bs_id].BS_position
        bs_height = base_stations[best_bs_id].BS_antenna.ANTENNA_height
        tx_power = base_stations[best_bs_id].BS_antenna.get_tx_power(user_position, bs_position, rx_height=user_height, tx_height=bs_height)
        n_tx = base_stations[best_bs_id].BS_antenna.get_ntx(user_position, bs_position, rx_height=user_height, tx_height=bs_height)
        distance = gf.euclidean_distance(bs_position, user_position, elevation_rx=user_height, elevation_tx=bs_height)
        frequency = base_stations[best_bs_id].BS_antenna.get_frequency(user_position, bs_position, rx_height=user_height, tx_height=bs_height)

        path_loss = -1
        for current_channel in simulation_map.MAP_channel_tessellation.keys():
            if Polygon(simulation_map.MAP_channel_tessellation[current_channel]["polygon"][0]).contains(Point(user_position)):
                path_loss = simulation_map.MAP_channel_tessellation[current_channel]["channel"].path_loss(distance, frequency)
        weighted_channels = Channel.weight_channels(user_position, bs_position, simulation_map, rx_height=user_height, tx_height=bs_height)

        # Create user link
        link_id = "UE_LINK_" + current_user.USER_id.split("_")[1]
        link = RFLink("UE_LINK_" + current_user.USER_id.split("_")[1], "ue", latency_model, best_bs_id, n_tx, tx_power, current_user.USER_id, n_rx, bw, 0.01, weighted_channels, path_loss, current_sinr)
        current_user.USER_ue.UE_sim.SIM_link = link
        current_user.USER_ue.UE_antenna.UEANTENNA_bandwidth = bw
        current_capacity = current_user.USER_ue.UE_sim.SIM_link.LINK_capacity
        current_path_loss = current_user.USER_ue.UE_sim.SIM_link.get_path_loss()
        current_bw = current_user.USER_ue.UE_sim.SIM_link.LINK_bandwidth
        current_bs_connected = current_user.USER_ue.UE_sim.SIM_link.LINK_peer
        current_sinr = current_user.USER_ue.UE_sim.SIM_link.get_sinr()
        current_position = current_user.USER_position
        current_latency = current_user.USER_ue.UE_sim.SIM_link.get_propagation_latency()

        if current_bw != 10:
            print("\n")
            print(" >>>>>>> FATAL PROBLEM! <<<<<<< ")
            print("*EVENT TIME: " + str(current_event.EVENT_time))
            print(current_user.USER_id + " | C: " + str(current_capacity) + " | P: " + str(current_path_loss) + " | B: " + str(current_bw))
            print(current_user.USER_id + " | POS: " + str(current_position) + " | BS: " + current_bs_connected + " | SINR: " + str(current_sinr))
            print(base_stations[current_bs_connected].BS_node.NODEB_assigned_bandwidth)
            print(" >>>>>>>>>>>> **** <<<<<<<<<<<< ")
            print("\n")

        for USER in users.keys():
            user_capacity = users[USER].USER_ue.UE_sim.SIM_link.LINK_capacity
            user_latency = users[USER].USER_ue.UE_sim.SIM_link.get_propagation_latency()

            results.append([USER, user_capacity, user_latency])
        results_times.append(current_event.EVENT_time)
