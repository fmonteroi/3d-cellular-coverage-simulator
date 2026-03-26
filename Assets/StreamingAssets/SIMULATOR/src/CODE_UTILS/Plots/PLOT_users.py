# Module 'PLOT_users'
# Created 06/05/2021 (version 6.0)
# Modified 06/05/2021 (version 6.0) - Jose Javier Rico Palomo

from SIMULATOR.src.MOBILE_NODES.users import DynamicUser
from SIMULATOR.src.MAP.simulation_map import SimulationMap
import matplotlib.pyplot as plt


def single_user_movement(user: DynamicUser):

    plt.figure()

    last_position = user.DUSER_steps[0].STEP_position

    for i in range(0, len(user.DUSER_steps)):

        current_position = user.DUSER_steps[i].STEP_position
        plt.plot(current_position[0], current_position[1], 'kx')

        if i > 0:
            plt.plot([last_position[0], current_position[0]], [last_position[1], current_position[1]], linestyle='dashed', color='k')
            last_position = current_position
