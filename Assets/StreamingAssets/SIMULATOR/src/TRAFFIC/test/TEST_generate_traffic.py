# Test "generate_traffic.py"

import SIMULATOR.src.TRAFFIC.traffic_generation as tg
import SIMULATOR.src.CODE_UTILS.Plots.PLOT_traffic as plotTraffic
import matplotlib.pyplot as plt


simulation_time = 100

# poisson
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("poisson", simulation_time, rate=0.1, min_size=10000, max_size=20000, min_duration=3, max_duration=10)
demands_poisson = [arrival_times, demand_sizes, demand_durations]

# ftp
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("ftp", simulation_time, min_duration=3, max_duration=10)
demands_ftp = [arrival_times, demand_sizes, demand_durations]

# web_browsing
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("web_browsing", simulation_time)
demands_web = [arrival_times, demand_sizes, demand_durations]

# video_streaming_3gpp
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("video_streaming_3gpp", simulation_time, rate=0.5, min_duration=20, max_duration=30)
demands_video_3gpp = [arrival_times, demand_sizes, demand_durations]

# gaming_3gpp_uplink
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("gaming_3gpp_uplink", simulation_time, rate=0.2, min_duration=10, max_duration=20)
demands_gaming_ul = [arrival_times, demand_sizes, demand_durations]

# gaming_3gpp_downlink
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("gaming_3gpp_downlink", simulation_time, rate=0.2, min_duration=10, max_duration=20)
demands_gaming_dl = [arrival_times, demand_sizes, demand_durations]

# video_streaming_mpg4
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("video_streaming_mpg4", simulation_time, rate=4, min_duration=2, max_duration=30)
demands_video_mpg4 = [arrival_times, demand_sizes, demand_durations]

# gaming_wow_uplink
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("gaming_wow_uplink", simulation_time, rate=0.04, min_duration=10, max_duration=20)
demands_wow_ul = [arrival_times, demand_sizes, demand_durations]

# gaming_wow_downlink
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("gaming_wow_downlink", simulation_time, rate=0.04, min_duration=10, max_duration=20)
demands_wow_dl = [arrival_times, demand_sizes, demand_durations]

# gaming_configurable_uplink
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("gaming_configurable_uplink", simulation_time, rate=2, min_size=200, max_size=300, min_duration=3, max_duration=10, time_between_packets=0.01)
demands_configurable_gaming = [arrival_times, demand_sizes, demand_durations]

# video_streaming_configurable
arrival_times, demand_sizes, demand_durations = tg.generate_traffic("video_streaming_configurable", simulation_time, rate=0.02, min_size=100, max_size=200, min_duration=1, max_duration=10, fps=60)
demands_configurable_video = [arrival_times, demand_sizes, demand_durations]

# ----------------------------------------------------------------------------- #
# plotTraffic.demand("poisson", demands_poisson, simulation_time)
# plotTraffic.demand("ftp", demands_ftp, simulation_time)
# plotTraffic.demand("web_browsing", demands_web, simulation_time)
# plotTraffic.demand("video_streaming_3gpp", demands_video_3gpp, simulation_time)
# plotTraffic.demand("gaming_3gpp_uplink", demands_gaming_ul, simulation_time)
# plotTraffic.demand("gaming_3gpp_downlink", demands_gaming_dl, simulation_time)
# plotTraffic.demand("video_streaming_mpg4", demands_video_mpg4, simulation_time)
# plotTraffic.demand("gaming_wow_uplink", demands_wow_ul, simulation_time)
# plotTraffic.demand("gaming_wow_downlink", demands_wow_dl, simulation_time)
# plotTraffic.demand("gaming_configurable_uplink", demands_configurable_gaming, simulation_time)
plotTraffic.demand("video_streaming_configurable", demands_configurable_video, simulation_time)

plt.show()
