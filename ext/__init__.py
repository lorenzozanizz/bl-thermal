""" Thermal
GitHub: https://github.com/lorenzozanizz/bl-thermal

Version: 1.0.0
Blender: 4.x
License: MIT
"""

bl_info = {
    "name": "Thermal",
    "author": "lorenzozanizz",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "Sidebar > Randomizer",
    "description": "An extension to synthetically generate thermal imaging data in Blender",
    "category": "Physics",
}


import sys


# Do not register the BPY module if we are testing
if sys.modules['pytest'] is  None:

    from .thermal_core import properties as simulation_properties
    from .ui import properties as data_properties

    from .ui import classes as ui_classes

    registration_classes = (
        *ui_classes
    )

    # Construct a dictionary with all properties declarations across all modules
    properties = {}
    for properties_set in (simulation_properties, data_properties):
        properties.update(properties_set)


def register():
    """ Register the classes and properties for the GUI extension
    """
    # Register all the required classes
    for cls in registration_classes:
        # bpy.utils.register_class(cls)
        pass

    # Define all the attributes for the GUI
    for prop_name, prop_value in properties.items():
        # setattr(bpy.types.Scene, prop_name, prop_value)
        pass


def unregister():
    """ Unregister the classes and properties for the GUI extension
    """

    # Delete all registered properties in the environment
    for prop in properties:
        # delattr(bpy.types.Scene, prop)
        pass

    # Unregister all previously registered classes
    for cls in reversed(registration_classes):
        pass
        # bpy.utils.unregister_class(cls)

    # UniqueLogger.cleanup()
    # unregister_handlers()
