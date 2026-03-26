# Module 'PLOT_traffic'
# Created 17/05/2021 (version 6.0)
# Modified 17/05/2021 (version 6.0) - Jose Javier Rico Palomo

import matplotlib.pyplot as plt


def demand(traffic_model: str, demands: list, simulation_time: float):

    # plt.figure()

    min_x_plot = 0
    max_x_plot = simulation_time
    min_y_plot = 0
    max_y_plot = 1000
    fig, ax = plt.subplots()

    plt.axis([min_x_plot, max_x_plot, min_y_plot, max_y_plot])

    arrival_times = demands[0]
    demand_sizes = demands[1]
    demand_durations = demands[2]

    for i in range(0, len(arrival_times)):

        t_i = arrival_times[i]
        d = demand_durations[i]
        t_f = t_i + d
        s = demand_sizes[i]

        x_values = [min_x_plot, t_i - 0.01, t_i, t_f, t_f + 0.01, max_x_plot]
        y_values = [0, 0, s, s, 0, 0]  # Mbps

        plt.plot(x_values, y_values, linewidth=0.5, label="Conn " + str(i))
        ax.fill(x_values, y_values, alpha=0.1)

    plt.title(traffic_model)
    plt.legend()
