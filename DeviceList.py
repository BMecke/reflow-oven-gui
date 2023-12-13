import threading

from USBDeviceDaemon import USBDeviceDaemon

from devices.Simulator import Simulator
from devices.V3_Pro import V3Pro, check_if_device_is_v3_pro_device


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
        self._profiles = profiles

        # initialize device list with a simulated device (and set it as the currently selected one)
        self.device_list = [Simulator(self._profiles.selected_profile)]
        self.device_list[0].selected = True

        # this list contains the currently connected and compatible serial devices (real hardware, no simulators)
        # each element is a dict with a "port" and an actual "device" key
        self._hardware_device_list = []

        # instantiate USBDeviceDaemon and block until initialization is complete
        self._is_device_list_initialized = threading.Event()
        self._is_device_list_initialized.clear()
        self._usb_daemon = USBDeviceDaemon(
            self._on_added_devices, self._on_removed_devices, self._on_device_initialization
        )
        self._is_device_list_initialized.wait()

    def _on_added_devices(self, port_list):
        """
        TODO: Add docstring
        """
        for port in port_list:
            if check_if_device_is_v3_pro_device(port):
                print("True")
                self._hardware_device_list.append({
                    'port': port,
                    'device': V3Pro(self._profiles.selected_profile, port)
                })

    def _on_removed_devices(self, port_list):
        """
        TODO: Add docstring
        """
        for port in port_list:
            for device in self._hardware_device_list:
                if port == device['port']:
                    self._hardware_device_list.remove(device)
                    break

    def _on_device_initialization(self):
        """
        Adds all device entries from the pure hardware device list to the overall device list.

        Unblocks the "__init__" method afterward.
        """
        for device in self._hardware_device_list:
            self.device_list.append(device['device'])
        self._is_device_list_initialized.set()

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
