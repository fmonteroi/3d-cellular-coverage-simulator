# Test 'ieee_access_simulations.py'

from SIMULATOR.src.MAP.simulation_map import SimulationMap
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_simulation_map as PlotSimulationMap
import SIMULATOR.Test.ieee_access_aux_methods as aux_methods
from operator import attrgetter
import os.path
import json
os.chdir("/home/jricopal/Documentos/Workspace/PythonSimulator_v6/")

# * SIMULATION CONFIGURATION
execution_samples = 35
simulation_time = 60
link_planification = "sinr"  # "latency_estimation" / "capacity_estimation"
bw_algorithm = "standard"
macro_user_bandwidth = 300  # ! Special case (200 MHz channel)
small_user_bandwidth = 900  # ! Special case (200 MHz channel)
num_dynamic_users = 25
bw_requirement_for_dynamic_users = 10  # ! Special case (200 MHz channel)
num_static_users = 0
bw_requirement_for_static_users = 1
random_mobility = False
random_positions = True
directory_path = "/home/jricopal/Escritorio/IEEE_Access_simulations/"
show_figure = False

# * SIMULATION MAP
simulation_map = SimulationMap("MAP_0", map_configuration="resource_management_paper")

# * CELLULAR NETWORK
base_stations = aux_methods.generate_cellular_network(simulation_map, macro_user_bandwidth, small_user_bandwidth)
figure_map, figure_map_axes = PlotSimulationMap.complete_scenario(simulation_map, show_channel_points=False, bs_labels=True, base_stations_dict=base_stations)

results = dict()  # ? Results

# * EXPERIMENTATION
for current_sample in range(0, execution_samples):
    print("**EXECUTION SAMPLE Nº " + str(current_sample))

    # * USERS
    file_path = "/home/jricopal/Escritorio/IEEE_Access_simulations/config/user_steps_sample_" + str(current_sample) + ".json"
    dynamic_users = aux_methods.generate_dynamic_users(num_dynamic_users, simulation_time, simulation_map, bw_requirement_for_dynamic_users, predefined_steps=not random_mobility, directory_path=file_path)
    static_users = aux_methods.generate_static_users(num_static_users, simulation_map, bw_requirement_for_static_users, predefined_position=not random_positions, directory_path=directory_path, offset=len(dynamic_users))
    users = {**dynamic_users, **static_users}

    # * PRESIMULATION
    events = []
    for current_user in users.values():
        if current_user.__class__.__name__ == "DynamicUser":
            [events.append(current_user.DUSER_steps[j]) for j in range(0, len(current_user.DUSER_steps))]  # Add steps from Dynamic users
    events = sorted(events, key=attrgetter('EVENT_time'))

    # * SIMULATION
    # Connect all user to cellular network when the simulation starts
    [aux_methods.connect_user_to_network(current_user_id, users, link_planification, base_stations, simulation_map, 0, "standard") for current_user_id in users.keys()]

    time_results_per_sample = dict()  # ? Results
    for i in range(0, len(events)):
        current_event = events[i]

        best_bs_id = ""
        sinrs = dict()
        current_user = users[current_event.MNEVENT_user_id]

        if current_event.__class__.__name__ == "Step":

            # Get old BS
            old_bs = current_user.USER_ue.UE_sim.get_bs_connected()

            # Update position
            current_user.USER_position = current_event.STEP_position
            user_position = current_user.USER_position

            # Calculate candidate BS
            best_bs_id, sinrs, metrics_values = aux_methods.calculate_candidate_bs(current_user, base_stations, simulation_map, link_planification)

            # Check if handover occurs
            if old_bs != best_bs_id:

                # Disconnect user from old bs and reconnect user to new bs
                bw = aux_methods.reconnect_user(current_user, base_stations, old_bs, best_bs_id, current_event.EVENT_time, bw_algorithm)

            else:

                # Get assigned bandwidth
                bw = base_stations[best_bs_id].BS_node.NODEB_assigned_bandwidth[current_user.USER_id]

            # Update variables
            aux_methods.update_variables(current_user.USER_id, users, base_stations, best_bs_id, sinrs, bw, simulation_map)

            # print("--------------------------")
            # print(" - Event time: " + str(current_event.EVENT_time) + " | USER: " + current_user.USER_id + " | BS: " + current_user.USER_ue.UE_sim.get_bs_connected())
            # print(" * Position: " + str(current_user.USER_position) + " | BW: " + str(current_user.USER_ue.UE_sim.SIM_link.LINK_bandwidth) + " | T: " + str(current_user.USER_ue.UE_sim.SIM_link.LINK_throughput) + " | MaxC: " + str(current_user.USER_ue.UE_sim.SIM_link.LINK_capacity) + " | SINR: " + str(current_user.USER_ue.UE_sim.SIM_link.get_sinr()) + " | L: " + str(current_user.USER_ue.UE_sim.SIM_link.get_propagation_latency()))
            # print(sinrs)
            # print(metrics_values)

            if i == 0:
                x_start, y_start = current_user.USER_position[0], current_user.USER_position[1]
                figure_map_axes.plot(x_start, y_start, marker="x", color="k")

            else:
                x_start, y_start, x_end, y_end = events[i - 1].STEP_position[0], events[i - 1].STEP_position[1], current_user.USER_position[0], current_user.USER_position[1]
                figure_map_axes.plot([x_start, x_end], [y_start, y_end], color="k")
                figure_map_axes.plot(x_start, y_start, marker="x", color="k", markersize=0.5)

            if show_figure:
                figure_map.show()
                print(" - End event. Figure plot.")

            # Update variables from all users
            aux_methods.update_variables_from_all_users(users, base_stations, simulation_map, link_planification, current_user.USER_id)

            # Get results of all users
            user_results_per_time = dict()  # ? Results
            for USER in users.keys():

                metric_results = dict()  # ? Results
                metric_results["capacity"] = users[USER].USER_ue.UE_sim.SIM_link.LINK_capacity
                metric_results["latency"] = users[USER].USER_ue.UE_sim.SIM_link.get_propagation_latency()
                metric_results["position"] = str(users[USER].USER_position)
                metric_results["sinr"] = users[USER].USER_ue.UE_sim.SIM_link.get_sinr()
                metric_results["bandwidth"] = users[USER].USER_ue.UE_sim.SIM_link.LINK_bandwidth
                metric_results["throughput"] = users[USER].USER_ue.UE_sim.SIM_link.LINK_throughput

                user_results_per_time[USER] = metric_results  # ? Results

            time_results_per_sample[current_event.EVENT_time] = user_results_per_time  # ? Results

    results["SAMPLE_"+str(current_sample)] = time_results_per_sample  # ? Results

# "sinr" | "capacity_estimation" | "latency_estimation" | "outweigh_allocation" | "resource_pool"
output_file_name = "sinr"  # ! Change file name
with open(directory_path + "results/results_"+output_file_name + ".json", "w") as output_file:
    json.dump(results, output_file, indent=2, separators=(',', ': '))
