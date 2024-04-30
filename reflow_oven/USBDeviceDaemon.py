import threading
import queue
import time

from sys import platform
if platform == 'linux':
    import pyudev
elif platform == 'win32':
    import wmi
    import pythoncom

import serial.tools.list_ports


class USBDeviceDaemon:
    """
    Monitors USB ports for devices being plugged in and out.
    Whenever such a USB event occurs, the list of currently connected serial devices is updated.
    """
    def __init__(self, plug_in_event, plug_out_event, init_complete):
        """
        Monitors USB ports for devices being plugged in and out.
        Whenever such a USB event occurs, the list of currently connected serial devices is updated.

        Parameters
        ----------
        plug_in_event: function
            The function to call when serial devices have been plugged in to USB.
            Receives the corresponding port names as a list.

        plug_out_event: function
            The function to call when serial devices have been plugged out from USB.
            Receives the corresponding port names as a list.

        init_complete: function
            The function to call after the USBDeviceDaemon has been fully initialized
            and all serial devices that were connected via USB during the initialization have been processed.
            This function is only called once.

        Returns
        -------
        USBDeviceDaemon
            A USBDeviceDaemon object.
        """
        # the callback functions invoked when serial devices are inserted/removed via USB
        self._add_event = plug_in_event
        self._remove_event = plug_out_event

        # the callback function invoked after the USBDeviceDaemon is initialized and the first event has been processed
        # (and a flag to determine, whether the function has already been invoked)
        self._device_initialized = init_complete
        self._is_device_initialized = False

        # a list containing the ports of all currently connected serial devices
        self._active_ports = []

        # a queue for USB events
        # (event = a USB device was plugged in/out)
        self._event_queue = queue.Queue()

        # initialize the list of currently connected serial devices
        self._event_queue.put(item='usb_device', block=False)

        # a thread that continuously processes all events in the USB event queue
        self._event_handler_thread = threading.Thread(target=self._event_handler, daemon=True)
        self._event_handler_thread.start()

        # start monitoring for USB events
        # (each event will invoke the respective "event_reaction" function)
        if platform == 'linux':
            self._context = pyudev.Context()
            self._monitor = pyudev.Monitor.from_netlink(self._context)
            self._monitor.filter_by(subsystem='usb')
            self._observer = pyudev.MonitorObserver(self._monitor, self._pyudev_event_reaction)
            self._observer.start()
        elif platform == 'win32':
            self._observer = threading.Thread(target=self._wmi_init_n_event_reaction, daemon=True)
            self._observer.start()

    def _pyudev_event_reaction(self, action, device):
        """
        Enqueues an event into the USB event queue.

        Parameters
        ----------
        action: str
            The kind of event that occurred.
            Examples are "bind", "unbind", etc.

        device: pyudev.Device
            The device object that the action was performed on.
            Provides several properties to access device information such as its vendor, USB path, etc.
        """
        self._event_queue.put(item=device.properties['DEVTYPE'], block=False)

    def _wmi_init_n_event_reaction(self):
        """
        Monitors the Windows USB controller for operations (plug in/out) on devices.

        Every operation is enqueued into the USB event queue.
        """
        pythoncom.CoInitialize()
        self._context = wmi.WMI()
        self._monitor = self._context.Win32_USBControllerDevice.watch_for("operation")

        while True:
            # wait for a new operation issued by the Windows USB controller
            self._monitor()

            # enqueue an event into the USB event queue
            self._event_queue.put(item='usb_device', block=False)

    def _device_initialization_complete(self):
        """
        When called for the first time, this function invokes a callback function.

        The invoked callback function will assume that the USBDeviceDaemon has been fully initialized
        and all serial devices that were connected via USB during the initialization have been processed.
        """
        if not self._is_device_initialized:
            self._is_device_initialized = True
            self._device_initialized()

    def _event_handler(self):
        """
        Continuously processes all events in the USB event queue.

        If serial devices are added/removed, the corresponding callback function is invoked with
        a list of the connected/disconnected ports' names.
        """
        while True:
            # get the next event in the USB event queue
            new_event = self._event_queue.get()

            # filter by device type "USB device"
            if new_event == 'usb_device':

                # leave time for proper initialization
                time.sleep(0.5)

                # the new list of all currently connected serial devices
                new_ports = [comport[0] for comport in serial.tools.list_ports.comports()]

                removed_ports = []
                added_ports = []

                # remove all the serial devices that have been registered but are not connected anymore
                for port in self._active_ports:
                    if port not in new_ports:
                        self._active_ports.remove(port)
                        removed_ports.append(port)

                # add all the new serial devices that have not been registered yet
                for port in new_ports:
                    if port not in self._active_ports:
                        self._active_ports.append(port)
                        added_ports.append(port)

                # invoke callback for removed serial devices (with the corresponding port names)
                if removed_ports:
                    self._remove_event(removed_ports)

                # invoke callback for added serial devices (with the corresponding port names)
                if added_ports:
                    self._add_event(added_ports)

            # event in the USB event queue successfully processed
            self._event_queue.task_done()
            self._device_initialization_complete()
