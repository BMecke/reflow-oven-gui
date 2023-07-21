import time
import random

from Device import Device
from Profile import Profile


class Simulator(Device):
    """
    This class implements a simulated soldering oven.
    It is used to test various functions.


    Attributes
    ----------
    number_of_simulators: int
        Indicates how many simulator objects have already been created.
        This is important so that the IDs of the individual objects are different.
    id: str
        The ID of the simulator object. This is incremented with each object created.
    name: str
        The Name of the device.
    profile: SimProfile()
        The soldering profiles are managed here.
    room_temperature: float
        The simulated room-temperature
    temperature: float
        The current temperature of the device.
        This is continuously updated in a separate thread.

    Methods
    -------
    reset()
        Reset the device.
    get_temperature()
        Get the current temperature from the connected device.
    set_profile_on_device()
        Here the profile is transferred to the currently selected soldering device.
    """

    number_of_simulators = 1

    def __init__(self, profile):
        super().__init__(profile)
        self.id = "simulator_" + str(self.__class__.number_of_simulators)
        self.name = "Simulator " + str(self.__class__.number_of_simulators)
        self.__class__.number_of_simulators += 1

        self.room_temperature = 21
        self.temperature = self.room_temperature

        self._run_thread.start()

    def reset(self):
        """
        Reset the device.
        """
        super().reset()
        self.temperature = self.room_temperature

    def stop_device(self):
        """
        Since this is a simulator, nothing needs to be done here.
        """
        pass

    def start_device(self):
        """
        Since this is a simulator, nothing needs to be done here.
        """
        pass

    def get_temperature(self):
        """
        Here the temperature of the currently selected simulator device is measured.

        Returns
        -------
        float
            The current simulated temperature.
        """
        sleep_time = 3
        target_temp = self.profile.get_target_temperature(self.runtime + sleep_time)
        time.sleep(sleep_time)
        if self.running:
            if target_temp > self.temperature:
                return self.temperature + random.randint(5, 6)
            elif self.temperature > target_temp and self.temperature > self.room_temperature + 2:
                return self.temperature - random.randint(1, 2)
            else:
                return self.room_temperature
        else:
            if self.temperature > self.room_temperature + 2:
                return self.temperature - random.randint(1, 2)
            else:
                return self.room_temperature

    def set_profile_on_device(self, data_points):
        """
        Here the profile is transferred to the currently selected soldering device.
        Since this is a simulator, nothing needs to be done here.

        Parameters
        ----------
        data_points: list
            The data points to be set.
        """
        pass
