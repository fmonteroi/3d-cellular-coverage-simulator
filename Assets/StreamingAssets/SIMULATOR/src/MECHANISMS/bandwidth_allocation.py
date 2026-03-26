# Module 'bandwidth_allocation'
# Created 24/02/2021 (version 6.0)
# Modified 24/02/2021 (version 6.0) - Jose Javier Rico Palomo


from typing import *
from SIMULATOR.src.CODE_UTILS.exceptions import UserOutOfBandwidth, LowPriorityUser


def standard_allocation(current_user_id: str, total_bandwidth: float, old_users_assigment_dict: Dict[str, float]):
    """
        Reallocate the allocated bandwidth to users on an equal planning basis (all users should receive the same bandwidth).

        :param current_user_id: candidate user identifier -> Example: "USER_1".
        :param total_bandwidth: total bandwidth available to the base station (in MHz).
        :param old_users_assigment_dict: dict of connected users and their allocated bandwidth before reallocation (copy).

        :return [dict] new_users_assigment_dict: dict of connected users and their allocated bandwidth with reallocation.
    """

    new_users_assigment_dict = dict()

    # Calculate the dedicated bandwidth to each user
    bw_per_user = total_bandwidth / (len(old_users_assigment_dict) + 1)

    # Add new user
    new_users_assigment_dict[current_user_id] = bw_per_user

    # Add old users
    for USER in old_users_assigment_dict.keys():
        new_users_assigment_dict[USER] = bw_per_user

    return new_users_assigment_dict


def simple_priority_allocation(current_user_id: str, available_bandwidth: float, priority: int, requirement: float, connected_users: Dict[str, int], users_assigment_dict: Dict[str, float]):
    """
        Reallocate the allocated bandwidth to users on an priority planning basis.
        Each user of strictly lower priority gives up bandwidth in proportion (the lower the priority, the more it contributes).

        :param current_user_id: candidate user identifier -> Example: "USER_1".
        :param available_bandwidth: total bandwidth available to the base station (in MHz).
        :param priority: priority that the user has in the network according to its type (absolute units).
        :param requirement: bandwidth needed by the user (in MHz).
        :param connected_users: identifier of the users connected to the BS and its priority.
        :param users_assigment_dict: users connected to the base station and their allocated bandwidth (copy).

        :return [dict] users_assigment_dict: dict of connected users and their allocated bandwidth with reallocation.

        :raise LowPriorityUser: occurs when the user does not have sufficient priority to connect to the base station according to the chosen plannification.
        :raise UserOutOfBandwidth: occurs when another user has run out of available bandwidth due to the evaluated users connection.
    """

    aux_priority_dict = dict()
    bw_assigned_to_user = 0

    # Calculate the bandwidth required by the candidate user
    necessary_bandwidth = requirement - available_bandwidth

    # Find out which are the lowest priority users.
    for USER in users_assigment_dict.keys():
        if priority > connected_users[USER]:
            aux_priority_dict[USER] = connected_users[USER]

    if len(aux_priority_dict) < 1:  # If there are no lower-priority users, raise an exception
        raise LowPriorityUser(current_user_id)

    # Calculate the inverse summation of the priorities (for the priority factor)
    sum_inv_p_i = 0
    for PRIORITY in aux_priority_dict.values():
        sum_inv_p_i += 1 / PRIORITY

    # Calculate the amount of bandwidth to be given up by each lower priority user, depending on the priority factor of each user.
    # The priority factor is the percentage of each users assignment as a function of its priority in relation to the total priority (inverse weighted average). The lower the priority, the higher the factor.
    for USER in aux_priority_dict.keys():
        priority_factor = 1 / (aux_priority_dict[USER]*sum_inv_p_i)  # f(P,N,n) = 1 / Pn*sum_i(1/Pi)
        unallocated_bandwidth = necessary_bandwidth * priority_factor
        bw_assigned_to_user += unallocated_bandwidth

        # Subtract, from the user being evaluated, the bandwidth that it gives up (if it does not go to zero).
        if users_assigment_dict[USER] - unallocated_bandwidth > 0:
            users_assigment_dict[USER] = users_assigment_dict[USER] - unallocated_bandwidth

        else:  # raise an exception when a user has out of bandwidth due to another user bs connection
            raise UserOutOfBandwidth(list(USER))

    # Adds the candidate user to the dictionary and assigns bandwidth to it
    users_assigment_dict[current_user_id] = bw_assigned_to_user + available_bandwidth

    return users_assigment_dict


def partial_outweigh_priority_allocation(current_user_id: str, available_bandwidth: float, priority: int, requirement: float, connected_users: Dict[str, int], users_assigment_dict: Dict[str, float]):
    """
        Reallocate the allocated bandwidth to users on an partial outweigh priority planning basis.
        Each user of same or lower priority gives up bandwidth in proportion (the lower the priority, the more it contributes).
        Similar to low priority but the users evaluated may have the same priority, and not necessarily higher.

        :param current_user_id: candidate user identifier -> Example: "USER_1".
        :param available_bandwidth: total bandwidth available to the base station (in MHz).
        :param priority: priority that the user has in the network according to its type (absolute units).
        :param requirement: bandwidth needed by the user (in MHz).
        :param connected_users: identifier of the users connected to the BS and its priority.
        :param users_assigment_dict: users connected to the base station and their allocated bandwidth (copy).

        :return [dict] users_assigment_dict: dict of connected users and their allocated bandwidth with reallocation.

        :raise LowPriorityUser: occurs when the user does not have sufficient priority to connect to the base station according to the chosen plannification.
        :raise UserOutOfBandwidth: occurs when another user has run out of available bandwidth due to the evaluated users connection.
    """

    aux_priority_dict = dict()
    bw_assigned_to_user = 0

    # Calculate the bandwidth required by the candidate user
    necessary_bandwidth = requirement - available_bandwidth

    # Find out which are the lowest or equal priority users.
    for USER in users_assigment_dict.keys():
        if priority >= connected_users[USER]:
            aux_priority_dict[USER] = connected_users[USER]

    if len(aux_priority_dict) < 1:  # If there are no lower or equal-priority users, raise an exception
        raise LowPriorityUser(current_user_id)

    # Calculate the inverse summation of the priorities (for the priority factor)
    sum_inv_p_i = 0
    for PRIORITY in aux_priority_dict.values():
        sum_inv_p_i += 1 / PRIORITY

    # Calculate the amount of bandwidth to be given up by each lower priority user, depending on the priority factor of each user.
    # The priority factor is the percentage of each users assignment as a function of its priority in relation to the total priority (inverse weighted average). The lower the priority, the higher the factor.
    for USER in aux_priority_dict.keys():
        priority_factor = 1 / (aux_priority_dict[USER]*sum_inv_p_i)
        unallocated_bandwidth = necessary_bandwidth * priority_factor  # f(P,N,n) = 1 / Pn*sum_i(1/Pi)
        bw_assigned_to_user += unallocated_bandwidth

        # Subtract, from the user being evaluated, the bandwidth that it gives up (if it does not go to zero).
        if users_assigment_dict[USER] - unallocated_bandwidth > 0:
            users_assigment_dict[USER] = users_assigment_dict[USER] - unallocated_bandwidth

        else:  # raise an exception when a user has out of bandwidth due to another user bs connection
            raise UserOutOfBandwidth(list(USER))

    # Adds the candidate user to the dictionary and assigns bandwidth to it
    users_assigment_dict[current_user_id] = bw_assigned_to_user + available_bandwidth

    return users_assigment_dict


def total_outweigh_priority_allocation(current_user_id: str, available_bandwidth: float, priority: int, requirement: float, connected_users: Dict[str, int], users_assigment_dict: Dict[str, float]):
    """
        Reallocate the allocated bandwidth to users on an total outweigh priority planning basis.
        Each user gives up bandwidth in proportion (the lower the priority, the more it contributes).
        Similar to "partial_outweigh_priority_allocation" but evaluates all users, independent of its priority.

        :param current_user_id: candidate user identifier -> Example: "USER_1".
        :param available_bandwidth: total bandwidth available to the base station (in MHz).
        :param priority: priority that the user has in the network according to its type (absolute units).
        :param requirement: bandwidth needed by the user (in MHz).
        :param connected_users: identifier of the users connected to the BS and its priority.
        :param users_assigment_dict: users connected to the base station and their allocated bandwidth (copy).

        :return [dict] users_assigment_dict: dict of connected users and their allocated bandwidth with reallocation.

        :raise LowPriorityUser: occurs when the user does not have sufficient priority to connect to the base station according to the chosen plannification.
        :raise UserOutOfBandwidth: occurs when another user has run out of available bandwidth due to the evaluated users connection.
    """

    aux_priority = 0
    bw_assigned_to_user = 0

    # Calculate the bandwidth required by the candidate user
    necessary_bandwidth = requirement - available_bandwidth

    # Find out which are the lowest or equal priority users.
    for USER in users_assigment_dict.keys():
        if priority >= connected_users[USER]:
            aux_priority += 1

    if aux_priority < 1:  # If there are no lower or equal-priority users, raise an exception
        raise LowPriorityUser(current_user_id)

    # Calculate the inverse summation of the priorities (for the priority factor)
    sum_inv_p_i = 0
    for PRIORITY in users_assigment_dict.values():
        sum_inv_p_i += 1 / PRIORITY

    # Calculate the amount of bandwidth to be given up by any user (independent of its priority), depending on the priority factor of each user.
    # The priority factor is the percentage of each users assignment as a function of its priority in relation to the total priority (inverse weighted average). The lower the priority, the higher the factor.
    for USER in users_assigment_dict.keys():
        priority_factor = 1 / (users_assigment_dict[USER]*sum_inv_p_i)
        unallocated_bandwidth = necessary_bandwidth * priority_factor  # f(P,N,n) = 1 / Pn*sum_i(1/Pi)
        bw_assigned_to_user += unallocated_bandwidth

        # Subtract, from the user being evaluated, the bandwidth that it gives up (if it does not go to zero).
        if users_assigment_dict[USER] - unallocated_bandwidth > 0:
            users_assigment_dict[USER] = users_assigment_dict[USER] - unallocated_bandwidth

        else:  # raise an exception when a user has out of bandwidth due to another user bs connection
            raise UserOutOfBandwidth(list(USER))

    # Adds the candidate user to the dictionary and assigns bandwidth to it
    users_assigment_dict[current_user_id] = bw_assigned_to_user + available_bandwidth

    return users_assigment_dict


def discard_priority_allocation(current_user_id: str, available_bandwidth: float, priority: int, requirement: float, connected_users: Dict[str, int], users_assigment_dict: Dict[str, float]):
    """
        Reallocate the allocated bandwidth to users on an discard priority planning basis.
        Each user of strictly lower priority gives up bandwidth in but lower priority users may run out of bandwidth and be dropped from the base station (the lower the priority, the more it contributes).
        Similar to "simple_priority" but may discard users who run out of bandwidth.

        :param current_user_id: candidate user identifier -> Example: "USER_1".
        :param available_bandwidth: total bandwidth available to the base station (in MHz).
        :param priority: priority that the user has in the network according to its type (absolute units).
        :param requirement: bandwidth needed by the user (in MHz).
        :param connected_users: identifier of the users connected to the BS and its priority.
        :param users_assigment_dict: users connected to the base station and their allocated bandwidth (copy).

        :return [dict] users_assigment_dict: dict of connected users and their allocated bandwidth with reallocation.

        :raise LowPriorityUser: occurs when the user does not have sufficient priority to connect to the base station according to the chosen plannification.
        :raise UserOutOfBandwidth: occurs when another user has run out of available bandwidth due to the evaluated users connection.
    """

    aux_priority_dict = dict()
    users_out_of_bw = []
    bw_assigned_to_user = 0

    # Calculate the bandwidth required by the candidate user
    necessary_bandwidth = requirement - available_bandwidth

    # Find out which are the lowest priority users.
    for USER in users_assigment_dict.keys():
        if priority > connected_users[USER]:
            aux_priority_dict[USER] = connected_users[USER]

    if len(aux_priority_dict) < 1:  # If there are no lower-priority users, raise an exception
        raise LowPriorityUser(current_user_id)

    # Calculate the amount of bandwidth to be given up by each lower priority user, depending on the priority factor of each user.
    # The priority factor is the percentage of each users assignment as a function of its priority in relation to the total priority (inverse weighted average). The lower the priority, the higher the factor.
    for USER in connected_users.keys():

        # Evaluate only lower-priority users
        if USER in aux_priority_dict:

            # Calculate the inverse summation of the priorities (for the priority factor)
            sum_inv_p_i = 0
            for PRIORITY in aux_priority_dict.values():
                sum_inv_p_i += 1 / PRIORITY

            priority_factor = 1 / (aux_priority_dict[USER]*sum_inv_p_i)
            unallocated_bandwidth = necessary_bandwidth * priority_factor  # f(P,N,n) = 1 / Pn*sum_i(1/Pi)

            # Subtract, from the user being evaluated, the bandwidth that it gives up (if it does not go to zero).
            if users_assigment_dict[USER] - unallocated_bandwidth > 0:
                users_assigment_dict[USER] = users_assigment_dict[USER] - unallocated_bandwidth
                bw_assigned_to_user += unallocated_bandwidth

            else:  # If a user has to give up all of his bandwidth
                bw_assigned_to_user += users_assigment_dict[USER]  # only added the bandwidth that it can provide
                necessary_bandwidth = necessary_bandwidth - bw_assigned_to_user  # the required bandwidth is updated
                del aux_priority_dict[USER]  # The user who has run out of bandwidth is removed from the auxiliary priority dictionary (so that it is not evaluated more times)
                del users_assigment_dict[USER]  # The user who has run out of bandwidth is removed from the bandwidth dictionary allocated to users
                users_out_of_bw.append(USER)  # The user is added to the list of users without bandwidth to be removed from the base station

    # if, when all the users have been evaluated, there are any users who have run out of bandwidth, raise an exception
    if len(users_out_of_bw) > 0:
        raise UserOutOfBandwidth(users_out_of_bw, new_dict_allocated_bw_to_users=users_assigment_dict)

    return users_assigment_dict
