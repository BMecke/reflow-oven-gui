import logging

logger = logging.getLogger('Profile')
logging.basicConfig(format='%(levelname)s - %(name)s | %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


class Profile:
    """
    In this class the different soldering profiles are managed.
    The profile classes of the different devices inherit from this class.

    Attributes
    ----------
    id: str
        The ID of the profile.
    name: str
        The Name of the profile.

    Methods
    -------
    data: list
        A list containing the data points (time and temperature) of the profile.
    get_target_temperature(seconds)
        Returns the setpoint temperature at a specified location.
        The selected location is passed in seconds.
    """

    def __init__(self, profile_id, name, data):
        self._data = []

        self.id = profile_id
        self.name = name
        self.data = data
        self.selected = False
        self.duration = float(max([t for (t, y, p) in self.data]))

    @property
    def data(self):
        # ToDo: time and temperature or time, temperature and power?
        """
        A list containing the data points (time and temperature) of the profile.
        This list is sorted automatically.

        Returns
        -------
        list
            The sorted list containing the data points (time and temperature) of the profile.
        """
        return self._data

    @data.setter
    def data(self, data_points):
        """

        Parameters
        ----------
        data_points: list
            The list containing the data points (time and temperature) of the profile.
            This list is sorted automatically.
        """
        data_points.sort(key=lambda tup: tup[0])
        self._data = data_points

    def get_target_temperature(self, second):
        """
        Returns the setpoint temperature at a specified location.
        The selected location is passed in seconds.

        Parameters
        ----------
        second: float
            The time from which the temperature is to be determined

        Returns
        -------
        float
            The target temperature at the selected time.
        """
        try:
            (prev_point, next_point) = self._get_surrounding_points(second)
            if prev_point != next_point:
                gradient = float(next_point[1] - prev_point[1]) / float(next_point[0] - prev_point[0])
                temp = gradient * (second - prev_point[0]) + prev_point[1]
                return round(temp, 2)
            else:
                return round(float(prev_point[1]), 2)
        except TypeError:
            # logger.warning('A too high temperature is requested')
            return round(float(self.data[-1][1]), 2)

    def _get_surrounding_points(self, second):
        """
        Get the points to the right and left of the desired second.
        This can then be used to determine the temperature value of the desired second.
        If the entered second is too large, None is returned.
        If the desired number matches exactly a point in the array, this value is returned for both points.

        Parameters
        ----------
        second: float
            The second from which the points on the right and left are searched for
        """

        if second > self.duration:
            return None
        else:
            for i in range(len(self.data)):
                if second == self.data[i][0]:
                    prev_point = self.data[i]
                    next_point = self.data[i]
                    return prev_point, next_point
                # second 0, no previous point
                elif second < self.data[i][0] and i == 0:
                    prev_point = (0, 0)
                    next_point = self.data[i]
                    return prev_point, next_point
                # get the points to the left and right of the current value
                elif second < self.data[i][0]:
                    prev_point = self.data[i - 1]
                    next_point = self.data[i]
                    return prev_point, next_point
