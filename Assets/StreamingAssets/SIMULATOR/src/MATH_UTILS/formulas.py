# Module 'formulas'
# Created 18/02/2020 (version 3.0)
# Modified 20/01/2021 (version 6.0) - Jose Javier Rico Palomo

import math as m
from SIMULATOR.src.CODE_UTILS.exceptions import InvalidNegativeValue


def to_db(x_units: float):
    """
        Function for switching from decimal units to decibels.

        :param x_units: units to convert (in decimal units).

        :return [float] x_db: decibels equivalent to the input (in dB).

        :raise InvalidNegativeValue: occurs when negative values are not accepted.
    """

    if x_units < 0:
        raise InvalidNegativeValue(x_units)

    x_db = 10*m.log10(x_units)

    return x_db


def to_units(x_db: float):
    """
        Function for switching from decibels to decimal units.

        :param x_db: decibels to convert (in dB).

        :return [float] x_units: decimal units equivalents to the input (in decimal units).
    """

    x_units = 10**(x_db/10)

    return x_units
