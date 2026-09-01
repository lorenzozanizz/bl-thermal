""" A module containing definition and resources for several physical constants
which enter when computing sensor models, emittance and emission from the
raw temperature map imposed on the scene as an initial state.
"""

# ------------------------ Physical constants ------------------------

# SECOND RADIATION CONSTANT
# https://physics.nist.gov/cgi-bin/cuu/CCValue?c22ndrc|ShowFirst=Browse
# Second radiation constant c2 = h*c/k, in metre-Kelvin
SECOND_RADIATION_CONSTANT_MK = 1.4387768775e-2

# Temperatures at or below this are clamped before entering any transfer.
# Guards the 1/T division and keeps exp(B/T) from overflowing to inf.
# Simulation would fail for temperatures this low anyway. This avoid numerical
# issues in cases of bad input.
MIN_TRANSFER_TEMPERATURE_K = 1.0