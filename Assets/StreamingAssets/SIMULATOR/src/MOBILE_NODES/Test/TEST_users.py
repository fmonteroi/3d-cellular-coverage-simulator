# Test "users.py" and "user_equipment.py"

from SIMULATOR.src.MOBILE_NODES.users import StaticUser, DynamicUser
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_users as PlotUsers
import matplotlib.pyplot as plt

# * Test static user
user_1_priority = 5
user_2_priority = 6

antenna_parameters = dict()
antenna_parameters["height"] = 1.5
antenna_parameters["n_rx"] = 6
antenna_parameters["gain"] = 9

sim_parameters = dict()
sim_parameters["type"] = "simple"
sim_parameters["multiconnectivity_mode"] = "simple"

traffic_parameters = dict()
traffic_parameters["model"] = "generic_demand"
traffic_parameters["num_demands"] = 2
traffic_parameters["min_time"] = 2
traffic_parameters["max_time"] = 25
traffic_parameters["simulation_time"] = 20
traffic_parameters["min_size"] = 10
traffic_parameters["max_size"] = 20
traffic_parameters["min_duration"] = 2
traffic_parameters["max_duration"] = 5

mobility_parameters = dict()
mobility_parameters["model"] = "FF"
mobility_parameters["min_speed"] = 2
mobility_parameters["max_speed"] = 5
mobility_parameters["movement_time"] = 30  # simulation_time
mobility_parameters["movement_height"] = 25  # map_size
# mobility_parameters["predefined_steps"] =

static_user = StaticUser("TEST_USER_1", "smarthome", antenna_parameters, sim_parameters, traffic_parameters, 0, priority=user_1_priority, position=(21, 21))
dynamic_user = DynamicUser("TEST_USER_2", mobility_parameters, antenna_parameters, sim_parameters, traffic_parameters, 0, priority=user_2_priority)

print(dynamic_user.__str__())
print(dynamic_user.DUSER_steps[0].__str__())

PlotUsers.single_user_movement(dynamic_user)
# plt.show()
