from abc import abstractmethod, ABCMeta

from bpy.types import Panel


class UISection(metaclass=ABCMeta):
    pass

class BakeSection(UISection):
    """

    """
    pass


class SpecSection(UISection):
    """

    """
    pass


class RenderSection(UISection):
    pass



class CentralPanel(UISection):
    pass



class MainPanel(Panel):
    pass

class InfoPanel(Panel):
    pass
