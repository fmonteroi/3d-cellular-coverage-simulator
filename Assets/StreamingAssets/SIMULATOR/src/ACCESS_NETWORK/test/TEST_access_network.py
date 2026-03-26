# TEST "PLOT_backhaul_network.py"

from SIMULATOR.src.ACCESS_NETWORK.access_network import AccessNetwork
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_access_network as PlotAccessNetwork
import matplotlib.pyplot as plt


# * Configure the router parameters
router_parameters = dict()
router_parameters["num_routers"] = 7
router_parameters["min_resources"] = 8000
router_parameters["max_resources"] = 9000
router_parameters["economic_model"] = None
router_parameters["power_model"] = None


# * Create access network with different topologies and configurations
access_network = AccessNetwork("ACCESSNETWORK_TEST_1", topology="path", link_capacity=10000, router_parameters=router_parameters)

print(access_network)
print("-----------------------")

for current_router in access_network.AN_routers.values():
    print(str(current_router)+"\n")

print("-----------------------")

for current_link in access_network.AN_links.values():
    print(str(current_link)+"\n")

PlotAccessNetwork.abstract_access_graph(access_network)
plt.show()
