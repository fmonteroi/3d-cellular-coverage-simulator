# Module 'Traffic_models'
# Created 30/03/2020 (version 4.0)
# Modified 12/02/2021 (version 6.0) - Jose Javier Rico Palomo

# [REF] Jorge Navarro-Ortiz et al., "A Survey on 5G Usage Scenarios and Traffic Models", IEEE COMMUNICATIONS SURVEYS & TUTORIALS, VOL. XX, NO. X, XXX, XXXX
# [REF] X. Wang, T. Kwon, Y. Choi, M. Chen and Y. Zhang, "Characterizing the gaming traffic of World of Warcraft: From game scenarios to network access technologies," in IEEE Network, vol. 26, no. 1, pp. 27-34, January-February 2012.
# [REF] S. Nosheen and J. Y. Khan, "High Throughput and QoE Fairness Algorithms for HD Video Transmission over IEEE802.11ac Networks," 2020 International Conference on Computing, Networking and Communications (ICNC), Big Island, HI, USA, 2020, pp. 84-89.


from SIMULATOR.src.MATH_UTILS import distributions as d
import numpy as np
from scipy.stats import bernoulli


def poisson_traffic(time: float, rate: float, duration_min: float, duration_max: float, size_min: float, size_max: float):
    """
        Generic traffic model based on Poisson distribution.
        - File Size: no specified (random value between min and max).
        - Reading time:  exponential distribution (with a parametrized rate).
        - Duration: no specified (random value between min and max).

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param size_min: minimum demand size to calculate the actual size between a maximum and a minimum (in bits).
        :param size_max: maximum demand size to calculate the actual size between a maximum and a minimum (in bits).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i-1] + d.exponential(rate)
        arrival_times.append(current_arrival_time)

        # Calculate the size, in bites, randomly (between MIN and MAX)
        current_demand_size = np.random.randint(size_min, high=size_max)
        demand_sizes.append(current_demand_size)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration/1000)  # Mbps

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def ftp_traffic(time: float, duration_min: float, duration_max: float):
    """
        FTP 3GPP Traffic Model. TSG-RAN1#48 (Appendix B).
        - File Size: truncated lognormal distribution (Max 5MBytes, x>0, sigma=0.35, mu=14.45)
        - Reading time: exponential distribution (lambda=0.006)
        - Duration: no specified (random between min and max values).

        :param time: time interval in which the demands are generated (in seconds).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped.
        current_arrival_time = d.exponential(0.006) if i == 0 else arrival_times[i - 1] + d.exponential(0.006) + demand_durations[i-1]
        arrival_times.append(current_arrival_time)

        # Size (in bits)
        current_demand_size = d.truncated_log_normal(14.45, 0.35, 100, 50000)  # 5000000
        demand_sizes.append(current_demand_size)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration/1000)  # Mbps

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def web_browsing_traffic(time: float):
    """
        Web browsing 3GPP Traffic Model. TSG-RAN1#48 (Appendix B).
        - Main object size: truncated lognormal distribution (min 100bytes, max 2 Mbytes, sigma=1.37, mu=8.37)
        - Embedded object size: truncated lognormal distribution (min 50bytes, max 2 Mbytes, sigma=2.36, mu=6.17)
        - Embedded object per page: truncated pareto distribution (alpha=1.1, k=2, m=55). Subtract k for the random value to obtain Nd.
        - Reading time: exponential distribution (lambda=0.033)
        - Parsing time: exponential distribution (lambda=7.69)

        :param time: time interval in which the demands are generated (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution
        current_arrival_time = d.exponential(0.033) if i == 0 else arrival_times[i - 1] + d.exponential(0.033)
        arrival_times.append(current_arrival_time)

        # Size (caution whit bits and bytes)
        s_m = d.truncated_log_normal(8.37, 1.37, 100, 200)  # Principal object size (bytes) -> 2000000
        n_d = round(d.truncated_pareto(1.1, 2, 53) - 2)  # The number of embedded objects in the website to be transmitted must be integer (round)

        s_e = []
        for j in range(0, n_d):  # Iterate the embedded objects
            embedded_object_size = d.truncated_log_normal(6.17, 2.36, 50, 200)  # Size of the embedded object inside the website -> 2000000
            s_e.append(embedded_object_size)

        current_demand_size = s_m + sum(s_e)  # Total size of the page = size of the main object + size of all embedded objects (bytes)
        demand_sizes.append(current_demand_size*8)  # Transform to bits

        # Duration (seconds)
        t_p = []
        for j in range(0, n_d):  # Iterate the embedded objects
            t_p.append(d.exponential(7.69))  # Read time between embedded objects

        current_demand_duration = sum(t_p)
        demand_durations.append(current_demand_duration/1000)  # Mbps

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def video_streaming_3gpp_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        Video Streaming 3GPP Traffic Model. TSG-RAN1#48 (Appendix B).
        - Inter-arrival time between frames: deterministic 100ms (based on 10 frame per seconds).
        - Packets per frame: deterministic 8 packets per frame.
        - Packets size: truncated pareto distribution (alpha=1.2, k=20bytes, m=250bytes).
        - Inter-arrival time between packets in a frame: truncated pareto distribution (alpha=1.1, k=2.5ms, m=12.5ms).

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        burst_time = 0
        frame_arrivals = []
        frame_sizes = []
        frame_durations = []

        j = 0
        while burst_time <= demand_durations[i]:

            frame_arrivals.append(arrival_times[i]) if j == 0 else frame_arrivals.append(frame_arrivals[j - 1] + frame_durations[j - 1] + 0.1)  # 100ms inter arrival time between frames

            packet_sizes = []
            packet_arrivals = []

            for k in range(0, 8):  # 8 packets per frame
                packet_arrivals.append(frame_arrivals[j]) if k == 0 else packet_arrivals.append(packet_arrivals[k-1] + d.truncated_pareto(1.1, 0.0025, 0.0125))  # Packet arrival times
                packet_sizes.append(d.truncated_pareto(1.2, 20, 250))  # Packet size (in bytes)

            frame_sizes.append(sum(packet_sizes))  # Frame size (bytes) = packet size (bytes) * 8 packets per frame
            frame_durations.append(packet_arrivals[-1])  # The frame duration will be the last packet arrival time
            burst_time = frame_arrivals[j] + frame_durations[j]

            j += 1

        current_demand_size = sum(frame_sizes)  # The video size is the total size of all the frames (in bytes)
        demand_sizes.append((current_demand_size*8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def uplink_gaming_3gpp_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        UL gaming 3GPP Traffic Model. TSG-RAN1#48 (Appendix B).
        - Initial packet arrival: uniform distribution (a=0, b=40ms)
        - Packet arrival: deterministic 40ms
        - Packet size: largest extreme value distribution (a=45bytes, b=5.7bytes) -> Fisher-Tippett

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(np.random.uniform(0, 0.4)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j - 1] + 0.4)  # From the first package, the others arrive spaced 40 ms apart.
            packet_sizes.append(d.fisher_tippett(45, 5.7) + 2)  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The game session size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def downlink_gaming_3gpp_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        DL gaming 3GPP Traffic Model. TSG-RAN1#48 (Appendix B).
        - Initial packet arrival: uniform distribution (a=0, b=40ms)
        - Packet arrival: largest extreme value distribution (a=55ms, b=6ms) -> Fisher-Tippett
        - Packet size: largest extreme value distribution (a=120bytes, b=36bytes). 2 bytes UDP header -> Fisher-Tippett

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(np.random.uniform(0, 0.4)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j - 1] + d.fisher_tippett(0.055, 0.006))  # From the first package, the others arrive spaced by distribution apart.
            packet_sizes.append(d.fisher_tippett(120, 36) + 2)  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The game session size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def video_vbr_mpeg4_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        VBR MPEG-4 Coder video traffic model.
        [REF] S. Nosheen and J. Y. Khan, "High Throughput and QoE Fairness Algorithms for HD Video Transmission over IEEE802.11ac Networks," 2020 International Conference on Computing, Networking and Communications (ICNC), Big Island, HI, USA, 2020, pp. 84-89.
        - Arrival time -> exponential
        - min burst size = 900 bytes
        - max burst size = 1500 bytes
        - burst rate = 10 packets / s
        - Duration -> random between minimum and maximum

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes)
        sub_rate = 10  # packets per second
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(d.exponential(sub_rate)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j-1] + d.exponential(sub_rate))
            packet_sizes.append(np.random.uniform(90, 150))  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The video size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def uplink_gaming_wow_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        Uplink gaming traffic for World of Warcraft (for downtown game scenarios).
        [REF] X. Wang, T. Kwon, Y. Choi, M. Chen and Y. Zhang, "Characterizing the gaming traffic of World of Warcraft: From game scenarios to network access technologies," in IEEE Network, vol. 26, no. 1, pp. 27-34, January-February 2012.
        - Weibull distribution -> packet size (scale=22.709, shape=1.578), inter arrival time (scale=0.042, shape=0.367)
        - Probability of Max size packet = 0

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(d.weibull(0.042, 0.367)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j - 1] + d.weibull(0.042, 0.367))  # From the first package, the others arrive spaced by distribution apart.
            packet_sizes.append(d.weibull(22.709, 1.578))  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The game session size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def downlink_gaming_wow_traffic(time: float, rate: float, duration_min: float, duration_max: float):
    """
        Downlink gaming traffic for World of Warcraft (for downtown game scenarios).
        [REF] X. Wang, T. Kwon, Y. Choi, M. Chen and Y. Zhang, "Characterizing the gaming traffic of World of Warcraft: From game scenarios to network access technologies," in IEEE Network, vol. 26, no. 1, pp. 27-34, January-February 2012.
        - Weibull distribution -> packet size (scale=430.263, shape=1.007), inter arrival time (scale=0.050, shape=0.492)
        - Probability of Max size packet = 0.35, M = 1460 bytes

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(d.weibull(0.050, 0.492)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j - 1] + d.weibull(0.050, 0.492))  # From the first package, the others arrive spaced by distribution apart.
            packet_sizes.append(d.weibull(430.263, 1.007)) if bernoulli.rvs(0.35) == 0 else packet_sizes.append(1460/8)  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The game session size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def uplink_gaming_configurable_traffic(time: float, rate: float, duration_min: float, duration_max: float, size_min: float, size_max: float, time_between_packets: float):
    """
        Configurable uplink gaming traffic based on 3GPP UL gaming model.
        - Initial packet arrival: uniform distribution (a=0, b=40ms)
        - Packet arrival: deterministic 40ms
        - Packet size: largest extreme value distribution (not defined yet) -> Fisher-Tippett

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param size_min: minimum demand size to calculate the actual size between a maximum and a minimum (in Megabits).
        :param size_max: maximum demand size to calculate the actual size between a maximum and a minimum (in Megabits).
        :param time_between_packets: interval time between packets for each demand (in seconds).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes): it is necessary to calculate how many frames are inside the video
        packet_arrival_times = []
        packet_sizes = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            packet_arrival_times.append(np.random.uniform(0, time_between_packets)) if j == 0 else packet_arrival_times.append(packet_arrival_times[j - 1] + time_between_packets)  # From the first package, the others arrive spaced by distribution apart.
            packet_sizes.append(d.fisher_tippett(size_min / 8, size_max / 8))  # Packet size (in bytes)

            burst_time = packet_arrival_times[j]
            j += 1

        current_demand_size = sum(packet_sizes)  # The game session size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to Megabits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations


def video_configurable_traffic(time: float, rate: float, duration_min: float, duration_max: float, size_min: float, size_max: float, fps: float = 60):
    """
        Configurable video streaming.
        - Time between frames -> 1/fps

        :param time: time interval in which the demands are generated (in seconds).
        :param rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units).
        :param duration_min: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param duration_max: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param size_min: minimum demand size to calculate the actual size between a maximum and a minimum (in Megabits).
        :param size_max: maximum demand size to calculate the actual size between a maximum and a minimum (in Megabits).
        :param* fps: frames per second you want the video to operate at. Defaults to 60.

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds
    aux_time = 0  # seconds

    i = 0
    while aux_time <= time:

        # Arrival times follow an exponential distribution. The time is incremental and demands cannot be overlapped
        current_arrival_time = d.exponential(rate) if i == 0 else arrival_times[i - 1] + d.exponential(rate) + demand_durations[i - 1]
        arrival_times.append(current_arrival_time)

        # Calculate the duration randomly (between MIN and MAX seconds)
        current_demand_duration = np.random.uniform(duration_min, duration_max)
        demand_durations.append(current_demand_duration)

        # Size (caution with bits and bytes)
        frame_arrival_times = []
        frame_sizes = []
        frame_durations = []
        burst_time = 0

        j = 0
        while burst_time <= demand_durations[i]:  # The time is incremental

            frame_arrival_times.append(arrival_times[i]) if j == 0 else frame_arrival_times.append(frame_arrival_times[j - 1] + frame_durations[j - 1] + (1 / fps))  # 1/fps ms inter arrival time between frames

            packets_sizes = []
            packets_arrivals = []

            for k in range(0, 8):  # 8 packets per frame
                packets_arrivals.append(frame_arrival_times[j]) if k == 0 else packets_arrivals.append(packets_arrivals[k - 1] + d.truncated_pareto(1.1, 0.0025, 0.0026))  # Packet arrival times
                packets_sizes.append(d.truncated_pareto(1.2, size_min*100, size_max*100))

            frame_sizes.append(sum(packets_sizes))  # Frame size (bytes) = packet size (bytes) * 8 packets per frame
            frame_durations.append(packets_arrivals[-1])  # The frame duration will be the last packet arrival time

            burst_time = frame_arrival_times[j]
            j += 1

        current_demand_size = sum(frame_sizes)  # The video size is the total size of all the packets (in bytes)
        demand_sizes.append((current_demand_size * 8)/1000)  # Transform to bits

        aux_time = arrival_times[i]
        i += 1

    return arrival_times, demand_sizes, demand_durations
