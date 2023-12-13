from devices.Simulator import Simulator
from devices.V3_Pro import V3Pro


class DeviceList:
    """
    This class contains all connected soldering devices that can be switched between.

    Attributes
    ----------
    device_list: list
        A list with all connected devices.

    Methods
    -------
        device_list: list
            A list with name and ID of all connected devices.
        selected_device: dict
            Name, ID and selection status of the currently selected device.
       """
    def __init__(self, profiles):
        self.device_list = [Simulator(profiles.selected_profile)]#, V3Pro(profiles.selected_profile, '/dev/ttyUSB0')]
        self.device_list[0].selected = True

    @property
    def selected_device(self):
        """
        Returns
        -------
        dict
            The currently selected device.
        """
        return next((dev for dev in self.device_list if dev.selected is True), None)

    @selected_device.setter
    def selected_device(self, dev_id):
        self.selected_device.selected = False
        new_selected_device = next((dev for dev in self.device_list if dev.id == dev_id), None)
        if new_selected_device:
            new_selected_device.selected = True
