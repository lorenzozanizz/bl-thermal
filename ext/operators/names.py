""" A file containing all the labels assigned to all operations inside the extension.
Note that the labels are divided by class and file, as to find them easily.

The labels are used around the other folders to avoid spreading "magic strings" and
to prevent dead-link operators which Blender cannot render and have no effect.

When a class requires to draw the corresponding property operator, it can access the
label as Labels.NAME.value

Operation labels which are terminated with _ are internal operations which are more likely
related to auxiliary GUI (e.g. menu drawing, etc...) although the distinction is
admittedly somewhat fuzzy
"""

from enum import Enum

class Labels(Enum):
    """ This class contains label for all operators used for all actions inside the
    extensions. To access an operator's use Labels.NAME.value
    """

    # ------------- Default namespace names ---------------
    # |
    # ( Default operator to open a URL.  )
    OPEN_URL                = "wm.url_open"

    # ------------- Names inside "thermal" (baking family) ---------------
    # |
    # ( Resolves each mesh object's TempInitSpec and bakes it into
    #   a per-vertex float mesh attribute. )
    BAKE_TEMPERATURE        = "thermal.bake_temperature"
    # ( Reserved for the future modal diffusion operator not yet implemented )
    DIFFUSE_TEMPERATURE_     = "thermal.diffuse_temperature"
    # ( Reserved for the future time-evolution operator, not yet implemented )
    EVOLVE_TEMPERATURE_      = "thermal.evolve_temperature"