# Module 'sorted_keys'
# Created 03/03/2021 (version 6.0)
# Modified 03/03/2021 (version 6.0) - Jose Javier Rico Palomo

from typing import *


def first_element_in_float_tuple(element: tuple):
    """
        Function used as the key of the sorted method that returns the first element of a tuple.

        :param element: tuple of elements.

        :return [float] first_element: the first element of the tuple (in position equal to 0).
    """

    return element[0]
