""" Temperature unit conversion utilities.

"""

from enum import Enum

class TempUnit(Enum):
    """ Display unit a user may enter/see temperatures in.
    Internal storage is always Kelvin, see module docstring.
    """
    KELVIN = "Kelvin"
    CELSIUS = "Celsius"
    FAHRENHEIT = "Fahrenheit"

class Conversions:
    """

    """

    @staticmethod
    def to_kelvin(value: float, unit: TempUnit) -> float:
        """ Convert unit to kelvin """
        if unit is TempUnit.KELVIN:
            return value
        if unit is TempUnit.CELSIUS:
            return value + 273.15
        if unit is TempUnit.FAHRENHEIT:
            return (value - 32.0) * (5.0 / 9.0) + 273.15
        raise ValueError(f"Unknown TempUnit: {unit}")

    @staticmethod
    def from_kelvin(value_k: float, unit: TempUnit) -> float:
        """ Convert Kalvin to unit """
        if unit is TempUnit.KELVIN:
            return value_k
        if unit is TempUnit.CELSIUS:
            return value_k - 273.15
        if unit is TempUnit.FAHRENHEIT:
            return (value_k - 273.15) * (9.0 / 5.0) + 32.0
        raise ValueError(f"Unknown TempUnit: {unit}")

    @staticmethod
    def is_physically_valid_kelvin(value_k: float) -> bool:
        """ Trivial check for Kelvin """
        return value_k >= 0.0