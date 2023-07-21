import time
from threading import Thread
import logging

logger = logging.getLogger('Device')
logging.basicConfig(format='%(levelname)s - %(name)s | %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

class Device:
    """
    In this class the different soldering devices are managed.
    The device classes of the different soldering devices inherit from this class.


    Attributes
    ----------
    temperature: float
        The current temperature of the device.
        This is continuously updated in a separate thread.
    profile: Profile()
        The soldering profiles are managed here.
    running: bool
        Indicates whether the oven is soldering.
    follow_up_time: int
        Specifies how long the chart should continue to update after the soldering process has been stopped
    run_out: bool
        True as long as the follow-up time is greater than 0 and the device is not running.
    selected: bool
        Specifies whether this device should send its status to the web page.
    target_temperature: float
        The temperature that the oven should currently have according to the profile.
    runtime: int
        Indicates how long the soldering program is already running.
    measured_points: list
        All points measured since the start (time and temperature) are stored here.
        This is important to be able to display all points when reloading the web page.


    Methods
    -------
    reset()
        Reset the device.
    start()
        Start the soldering process.
    start_device()
        Here the soldering process on the currently selected soldering device is started.
    stop()
        Stop the soldering process.
    stop_device()
        Here the soldering process on the currently selected soldering device is stopped.
    run()
        The run function of the threading class.
    get_temperature()
        Get the current temperature from the connected device.
    update_profile()
        Update the current profile.
    set_profile_on_device()
        Here the profile is transferred to the currently selected soldering device.
        This function must be implemented in the subclass of the device.
    """

    def __init__(self, profile):
        self._start_time = 0
        self._run_thread = Thread(target=self._run)

        self.temperature = 0
        self.profile = profile
        self.running = False
        self.follow_up_time = 30
        self.run_out = False
        self.selected = False
        self.target_temperature = 0
        # Runtime in seconds
        self.runtime = 0
        self.measured_points = []

    def reset(self):
        """
        Reset the device.
        """
        self.temperature = 0
        self._start_time = 0

        self.running = False
        # True as long as the follow-up time is greater than 0 and the device is not running
        self.run_out = False
        self.target_temperature = 0
        # Runtime in seconds
        self.runtime = 0
        self.measured_points = []

    def start(self):
        """
        Start the soldering process.
        In this function the function "start_device()" is called, which must be implemented in the child classes
        """
        self.measured_points = []
        self._start_time = time.time()
        self.running = True
        self.run_out = False
        self.start_device()

    def start_device(self):
        """
        Here the soldering process on the currently selected soldering device is started.
        Therefore, it must be adapted to the device and implemented new in each device class.
        """
        raise NotImplementedError

    def stop(self):
        """
        Stop the soldering process.
        In this function the function "stop_device()" is called, which must be implemented in the child classes
        """
        self.running = False
        self.run_out = True

    def stop_device(self):
        """
        Here the soldering process on the currently selected soldering device is stopped.
        Therefore, it must be adapted to the device and implemented new in each device class.
        """
        raise NotImplementedError

    def _run(self):
        """
        The run function of the threading class.

        In this function, the temperature of the connected device is permanently read out.
        For this purpose, the function "get_temperature()" must be implemented for each device in the subclass.
        Also, the start time is updated here.
        """
        follow_up_time = self.follow_up_time
        time_stamp = 0
        last_time_stamp = 0
        last_temperature = 0
        while True:
            self.temperature = self.get_temperature()
            if self.running or self.run_out:
                time_stamp = time.time()
                self.runtime = round(time_stamp - self._start_time)
                # If the runtime is already greater than 0 at this point, add an element with
                if len(self.measured_points) == 0 and self.runtime > 0:
                    self.measured_points.append((0, last_temperature))
                self.measured_points.append((self.runtime, self.temperature))
            else:
                self.runtime = 0

            if self.run_out and follow_up_time > 0:
                follow_up_time -= (time_stamp - last_time_stamp)
            elif self.run_out and follow_up_time <= 0:
                self.run_out = False
                self.running = False
                follow_up_time = self.follow_up_time
                self.stop_device()

            if self.runtime >= self.profile.duration and self.running:
                self.running = False
                self.run_out = True

            last_time_stamp = time_stamp
            last_temperature = self.temperature

    def get_temperature(self):
        """
        Here the temperature of the currently selected soldering device is measured.
        Therefore, this function must be implemented new in each device class.

        Returns
        -------
        float
            The current temperature.
        """
        raise NotImplementedError

    def update_profile(self, profile):
        """
        Update the current profile.
        """
        self.profile = profile

    def set_profile_on_device(self, profile):
        """
        Here the profile is transferred to the currently selected soldering device.
        This function must be implemented in the subclass of the device.

        Parameters
        ----------
        profile: list
            The profile to be set.
        """
        raise NotImplementedError

