# Module 'traffic_generation'
# Created 20/07/2020 (version 5.0)
# Modified 15/02/2021 (version 6.0) - Jose Javier Rico Palomo


from SIMULATOR.src.CODE_UTILS.exceptions import ConditionalParameterIsDefault, ConfigurationNotFound
from SIMULATOR.src.MODELS import traffic_models as tm
import numpy as np


def generate_traffic(traffic_model: str, time: float, rate: float = 0.0, min_size: float = 0.0, max_size: float = 0.0, min_duration: float = 0.0, max_duration: float = 0.0, time_between_packets: float = 0.0, fps: float = 0.0):
    """
        Its generates the traffic demands (whit structure) depending of  introduced traffic model and parameters.

        :param traffic_model: selected traffic model.
        :param time: time interval in which the demands are generated (in seconds).
        :param* rate: parameter representing the number of times the phenomenon is expected to occur over a given interval. Only positive values (absolute units). Defaults to 0.
        :param* min_size: minimum demand size to calculate the actual size between a maximum and a minimum (in bits). Defaults to 0.
        :param* max_size: maximum demand size to calculate the actual size between a maximum and a minimum (in bits). Defaults to 0.
        :param* min_duration: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds). Defaults to 0.
        :param* max_duration: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds). Defaults to 0.
        :param* time_between_packets: interval time between packets for each demand (in seconds). Defaults to 0.
        :param* fps: frames per second you want the video to operate at. Defaults to 0.

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).

        :raise ConfigurationNotFound: occurs when the configuration entered by parameters is not implemented in the simulator.
        :raise ConditionalParameterIsDefault: occurs when the conditional parameters have default values (if the default configuration is not configured).
    """

    if traffic_model == "poisson":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_size is generate_traffic.__defaults__[1]:
            raise ConditionalParameterIsDefault("min_size")

        if max_size is generate_traffic.__defaults__[2]:
            raise ConditionalParameterIsDefault("max_size")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")
        
        return tm.poisson_traffic(time, rate, min_duration, max_duration, min_size, max_size)
        
    elif traffic_model == "ftp":

        # Check if conditional parameters have the default value
        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")
        
        return tm.ftp_traffic(time, min_duration, max_duration)
        
    elif traffic_model == "web_browsing":
        return tm.web_browsing_traffic(time)

    elif traffic_model == "video_streaming_3gpp":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")
        
        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.video_streaming_3gpp_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "gaming_3gpp_uplink":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.uplink_gaming_3gpp_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "gaming_3gpp_downlink":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.downlink_gaming_3gpp_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "video_streaming_mpg4":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.video_vbr_mpeg4_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "gaming_wow_uplink":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.uplink_gaming_wow_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "gaming_wow_downlink":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        return tm.downlink_gaming_wow_traffic(time, rate, min_duration, max_duration)

    elif traffic_model == "gaming_configurable_uplink":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_size is generate_traffic.__defaults__[1]:
            raise ConditionalParameterIsDefault("min_size")

        if max_size is generate_traffic.__defaults__[2]:
            raise ConditionalParameterIsDefault("max_size")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        if time_between_packets is generate_traffic.__defaults__[5]:
            raise ConditionalParameterIsDefault("time_between_packets")

        return tm.uplink_gaming_configurable_traffic(time, rate, min_duration, max_duration, min_size, max_size, time_between_packets)

    elif traffic_model == "video_streaming_configurable":

        # Check if conditional parameters have the default value
        if rate is generate_traffic.__defaults__[0]:
            raise ConditionalParameterIsDefault("rate")

        if min_size is generate_traffic.__defaults__[1]:
            raise ConditionalParameterIsDefault("min_size")

        if max_size is generate_traffic.__defaults__[2]:
            raise ConditionalParameterIsDefault("max_size")

        if min_duration is generate_traffic.__defaults__[3]:
            raise ConditionalParameterIsDefault("min_duration")

        if max_duration is generate_traffic.__defaults__[4]:
            raise ConditionalParameterIsDefault("max_duration")

        if fps is generate_traffic.__defaults__[6]:
            raise ConditionalParameterIsDefault("fps")

        return tm.video_configurable_traffic(time, rate, min_duration, max_duration, min_size, max_size, fps)

    else:
        ConfigurationNotFound("traffic_model")


def generic_demand(num_demands: int, min_time: float, max_time: float, simulation_time: float, min_size: float, max_size: float, min_duration: float, max_duration: float):
    """
        It generates a generic parametrized demand.

        :param num_demands: amount of demands to be generated.
        :param min_time: minimum value of time interval in which the demands are generated (in seconds).
        :param max_time: maximum value of time interval in which the demands are generated (in seconds).
        :param simulation_time: total simulation time (in seconds).
        :param min_duration: minimum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param max_duration: maximum duration of demands to calculate the actual duration between a maximum and a minimum (in seconds).
        :param min_size: minimum demand size to calculate the actual size between a maximum and a minimum (in bits).
        :param max_size: maximum demand size to calculate the actual size between a maximum and a minimum (in bits).

        :return [list of float] arrival_times: arrival time for each demand (in seconds).
        :return [list of float] demand_sizes: size, or necessary capacity, for each demand (in Mbps).
        :return [list of float] demand_durations: duration, or active time, for each demand (in seconds).
    """

    arrival_times = []  # seconds
    demand_sizes = []  # bits
    demand_durations = []  # seconds

    for _ in range(0, num_demands):

        max_time = simulation_time if max_time == 0 or max_time > simulation_time else max_time

        current_arrival_time = np.random.uniform(min_time, max_time)
        arrival_times.append(current_arrival_time)

        current_demand_size = np.random.uniform(min_size, max_size)
        demand_sizes.append(current_demand_size)

        current_demand_duration = np.random.uniform(min_duration, max_duration)
        demand_durations.append(current_demand_duration)

    return arrival_times, demand_sizes, demand_durations
