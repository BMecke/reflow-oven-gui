import json
import logging
import threading
import time

import serial
import os

from Device import Device

logger = logging.getLogger('V3_PRO')
logging.basicConfig(format='%(levelname)s - %(name)s | %(asctime)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)


def check_if_device_is_v3_pro_device(port):
    test_dev = V3ProSerialConnection(port)
    if test_dev.check_serial_connection():
        return True
    else:
        return False


class V3Pro(Device):
    """
    This class implements an V3 Pro reflow controller from Beta Layout.

    Attributes
    ----------
    number_of_v3_pro_devices: int
        Indicates how many V3 Pro objects have already been created.
        This is important so that the IDs of the individual objects are different.
    id: str
        The ID of the V3 Pro object. This is incremented with each object created.
    name: str
        The Name of the device.

    Methods
    -------
    start_device()
        Start the soldering process on the device.
    stop_device()
        Stop the soldering process on the device.
    device_finished()
        Stop the device when the follow up time is zero.
    get_temperature()
        Get the current temperature from the connected device.
    set_profile_on_device()
        Here the profile is transferred to the currently selected soldering device.
    """
    number_of_v3_pro_devices = 1

    def __init__(self, profile, port):
        super().__init__(profile)
        self.id = "v3pro_" + str(self.__class__.number_of_v3_pro_devices)
        self.name = "V3 PRO " + str(self.__class__.number_of_v3_pro_devices)
        self.__class__.number_of_v3_pro_devices += 1
        self._run_thread_started = False
        self._v3_pro_serial_connection = V3ProSerialConnection(port)

    def start_device(self):
        """
        Before the soldering process is started, all settings from the device are written to a JSON file.
        After that the settings are overwritten within the device so that this software works with the device.
        Then, the soldering is started.
        """
        self._v3_pro_serial_connection.save_initial_controller_settings()
        self._v3_pro_serial_connection.controller_init()
        self.set_profile_on_device(self.profile)
        self._run_thread = threading.Thread(target=self._run)
        self._run_thread.start()
        self._v3_pro_serial_connection.start()

    def stop_device(self):
        """
        Stop the soldering process.
        """
        self._v3_pro_serial_connection.stop()

    def device_finished(self):
        """
        Stop the device when the follow up time is zero
        After the device is stopped, the initial settings on the device are restored.
        """
        self._thread_should_run = False
        self._v3_pro_serial_connection.stop()
        self._v3_pro_serial_connection.write_back_initial_controller_settings()

    def get_temperature(self):
        """
        Here the temperature of the currently selected V3 Pro device is measured.

        Returns
        -------
        float
            The current simulated temperature.
        """
        time.sleep(2)
        return self._v3_pro_serial_connection.temperature

    def set_profile_on_device(self, profile):
        """
        Here the profile is transferred to the currently selected soldering device.

        Parameters
        ----------
        profile: list
            The profile to be set.
        """
        # only write the profile, when the initial data of the device is saved
        if self.running or self.run_out:
            # The V3 Pro Controller only supports 4 solder phases (preheat, soak, reflow, dwell).
            # If more phases are passed, a warning is to be displayed
            if len(profile.data) > 4:
                logger.warning('More than 4 data points were transferred. Only the first 4 points are used.')
            self._v3_pro_serial_connection.preheat_time = profile.data[0][0]
            self._v3_pro_serial_connection.preheat_temp = profile.data[0][1]
            self._v3_pro_serial_connection.preheat_pwr = profile.data[0][2]

            self._v3_pro_serial_connection.soak_time = profile.data[1][0] - profile.data[0][0]
            self._v3_pro_serial_connection.soak_temp = profile.data[1][1]
            self._v3_pro_serial_connection.soak_pwr= profile.data[1][2]

            self._v3_pro_serial_connection.reflow_time = profile.data[2][0] - profile.data[1][0]
            self._v3_pro_serial_connection.reflow_temp = profile.data[2][1]
            self._v3_pro_serial_connection.reflow_pwr = profile.data[2][2]

            self._v3_pro_serial_connection.dwell_time = profile.data[3][0] - profile.data[2][0]
            self._v3_pro_serial_connection.dwell_temp = profile.data[3][1]
            self._v3_pro_serial_connection.dwell_pwr = profile.data[3][2]
            logger.info('Profile written to device')


class V3ProSerialConnection:
    """
    This class manages the communication with the device via the serial interface (UART).
    Here settings and values can be read from the device and written to the device.

    Attributes
    ----------
    ser: Serial()
        The serial connection to the V3 PRO controller

    Methods
    -------
    save_initial_controller_settings()
        Saves the settings that are originally on the device to a JSON file.
    write_back_initial_controller_settings()
        Write back the initial settings to the device.
    controller_init()
        Initialize the reflow controller.
    check_serial_connection()
        Test if the computer is connected to the correct reflow controller.
    """

    def __init__(self, port=None):
        """
        Initializes all variables where the settings of the reflow controller are stored with None.
        Additionally, a serial connection to the device is established if a port is specified when creating the object.

        Attributes
        ----------
        port: str
            The port of the reflow controller which to connect to.
        """
        self._dev_access = threading.Lock()

        # The currently set settings are temporarily stored in this variables
        # so that they do not have to be read from the device each time.
        self._memory_slot = None
        self._temp_unit = None
        self._trace = None
        self._temp_trace = None
        self._debug = None
        self._background_light = None

        self._preheat_temp = None
        self._preheat_time = None
        self._preheat_pwr = None
        self._soak_temp = None
        self._soak_time = None
        self._soak_pwr = None
        self._reflow_temp = None
        self._reflow_time = None
        self._reflow_pwr = None
        self._dwell_temp = None
        self._dwell_time = None
        self._dwell_pwr = None
        self._auto_extend = None

        # Dict to save the settings that are saved on the device at the start of the program
        # These settings are written back to the device when the program is terminated.
        self._initial_settings = {
            'memory_slot': None,
            'temp_unit': None,
            'trace': None,
            'temp_trace': None,
            'debug': None,
            'background_light': None,
            'preheat_temp': None,
            'preheat_time': None,
            'preheat_pwr': None,
            'soak_temp': None,
            'soak_time': None,
            'soak_pwr': None,
            'reflow_temp': None,
            'reflow_time': None,
            'reflow_pwr': None,
            'dwell_temp': None,
            'dwell_time': None,
            'dwell_pwr': None,
            'auto_extend': None
        }

        # number of attempts to send a command to the controller via UART
        self._number_of_trials = 5

        self.ser = None
        if port:
            self._serial_init(port)

    def __del__(self):
        if self.ser:
            self.write_back_initial_controller_settings()

    def _serial_init(self, com_port):
        """
        Initialize the serial device.
        For this first all superfluous lines are read from the UART buffer, and it is tested whether a reflow controller
        of the type V3-Pro from Beta Layout is connected.
        The properties are described in the users guide of the reflow controller (baud: 9600, 8N1).

        Attributes
        ----------
        com_port: int
            The serial port from which to read the data.
        """

        ser = serial.Serial(
            port=com_port,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=1,
            bytesize=8,
            timeout=0.5
        )
        self.ser = ser

        # skip unnecessary lines
        self._dev_access.acquire()
        while True:
            rawline = self._read_line()
            if len(rawline) == 0:
                break
        self._dev_access.release()

        connected = self.check_serial_connection()
        if not connected:
            raise ConnectionError('Could not connect to reflow controller.')

        logger.info('Serial connection initialized.')

    def save_initial_controller_settings(self):
        """
        Saves the settings that are originally on the device to a JSON file.
        However, the file is only overwritten if the previous program run was terminated properly.
        Otherwise, the settings from the file will be used.
        """
        with open(os.path.join('storage', 'v3_pro_initial_settings.json'), 'r') as json_file:
            try:
                file_data = json.load(json_file)
                # The data was written back cleanly to the device in the last program run.
                # This means that the settings on the device are the correct ones
                # and the file can be overwritten with the device settings.
                if file_data['old_settings_written_back_without_errors']:
                    self._initial_settings = self._get_initial_controller_settings()
                    data = {'old_settings_written_back_without_errors': False,
                            'data': self._initial_settings}
                # The data was not written back cleanly to the device in the last program run.
                # Therefore, the previously saved settings are used again
                else:
                    self._initial_settings = file_data['data']
                    data = {'old_settings_written_back_without_errors': False,
                            'data': self._initial_settings}
            # the File is empty
            except json.decoder.JSONDecodeError:
                self._initial_settings = self._get_initial_controller_settings()
                data = {'old_settings_written_back_without_errors': False,
                        'data': self._initial_settings}

        with open(os.path.join('storage', 'v3_pro_initial_settings.json'), 'w') as json_file:
            # write data to json_file
            json.dump(data, json_file)

        logger.info('Initial settings saved.')

    def _get_initial_controller_settings(self):
        """
        Get the settings that are stored on the device and save them in a dict.
        """
        initial_settings = {
                            # memory_slot must be executed first so that the settings are fetched for the correct slot
                            'memory_slot': self.memory_slot,

                            'temp_unit': self.temp_unit,
                            'trace': self.trace,
                            'temp_trace': self.temp_trace,
                            'debug': self.debug,
                            'background_light': self.background_light,
                            'preheat_temp': self.preheat_temp,
                            'preheat_time': self.preheat_time,
                            'preheat_pwr': self.preheat_pwr,
                            'soak_temp': self.soak_temp,
                            'soak_time': self.soak_time,
                            'soak_pwr': self.soak_pwr,
                            'reflow_temp': self.reflow_temp,
                            'reflow_time': self.reflow_time,
                            'reflow_pwr': self.reflow_pwr,
                            'dwell_temp': self.dwell_time,
                            'dwell_time': self.dwell_time,
                            'dwell_pwr': self.dwell_pwr,
                            'auto_extend': self.auto_extend
        }
        return initial_settings

    def write_back_initial_controller_settings(self):
        """
        Write back the initial settings to the device.
        """
        self.temp_unit = self._initial_settings['temp_unit']
        self.trace = self._initial_settings['trace']
        self.temp_trace = self._initial_settings['temp_trace']
        self.debug = self._initial_settings['debug']
        self.background_light = self._initial_settings['background_light']
        self.preheat_temp = self._initial_settings['preheat_temp']
        self.preheat_time = self._initial_settings['preheat_time']
        self.preheat_pwr = self._initial_settings['preheat_pwr']
        self.soak_temp = self._initial_settings['soak_temp']
        self.soak_time = self._initial_settings['soak_time']
        self.soak_pwr = self._initial_settings['soak_pwr']
        self.reflow_temp = self._initial_settings['reflow_temp']
        self.reflow_time = self._initial_settings['reflow_time']
        self.reflow_pwr = self._initial_settings['reflow_pwr']
        self.dwell_temp = self._initial_settings['dwell_temp']
        self.dwell_time = self._initial_settings['dwell_time']
        self.dwell_pwr = self._initial_settings['dwell_pwr']
        self.auto_extend = self._initial_settings['auto_extend']
        # Must be executed last so that the settings are set for the correct slot
        self.memory_slot = self._initial_settings['memory_slot']

        data = {'old_settings_written_back_without_errors': True,
                'data': self._initial_settings}
        with open(os.path.join('storage', 'v3_pro_initial_settings.json'), 'w') as json_file:
            # write data to json_file
            json.dump(data, json_file)

        logger.info('Initial settings written back to the device.')

    def controller_init(self):
        """
        Initialize the reflow controller.
        The settings of the device are set so that the device can work with this software
        """
        self.memory_slot = 4
        self.temp_unit = 'C'
        self.trace = 'OFF'
        self.temp_trace = 'OFF'
        self.debug = 'OFF'
        self.background_light = 0
        self.auto_extend = 'OFF'

        logger.info('Reflow controller initialized.')

    def _read_line(self):
        return self.ser.readline().decode().strip()

    def _write_command(self, value):
        self._dev_access.acquire()
        try:
            self.ser.write(bytes(str(value) + '\r', 'utf-8'))
        except AttributeError:
            self._dev_access.release()
            raise ConnectionError('Could not write command to reflow controller.')

        response_lines = []
        command_unsuccessful = False
        while True:
            rawline = self._read_line()
            # check if the controller returns an error (# Command >[...]< not found)
            if 'not found' in rawline or '# Command >' in rawline:
                command_unsuccessful = True
            if len(rawline) == 0:
                break
            response_lines.append(rawline)
        if command_unsuccessful:
            self._dev_access.release()
            raise ConnectionError('Could not write command to reflow controller.')
        self._dev_access.release()
        return response_lines

    def check_serial_connection(self):
        """
        Test if the computer is connected to the correct reflow controller.
        """
        # check if device is connected
        for i in range(self._number_of_trials):
            try:
                response = self._write_command('doStop')
                for line in response:
                    if 'Stop' in line:
                        return True
            except (ConnectionError, ValueError):
                pass
        return False

    @property
    def port(self):
        return self.ser.port

    @port.setter
    def port(self, value):
        if self.ser and self.ser.isOpen():
            self.ser.close()
        self._serial_init(value)

    @property
    def temperature(self):
        for i in range(self._number_of_trials):
            try:
                # get temperature slot
                response = self._write_command('tempshow')

                # if the temperature is below 100°, there is a whitespace between the + and the number (e.g., '+ 99 C')
                parts = response[1].split(' ')
                if parts[0] == '+':
                    temp = int(parts[1])
                else:
                    temp = int(parts[0].replace('+', ''))
                if 0 <= temp <= 490:
                    return temp
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read temperature')

    def start(self):
        for i in range(self._number_of_trials):
            try:
                # try to start device
                response = self._write_command('doStart')
                if 'Start' in response[1]:
                    return
                else:
                    raise ValueError
            except (ConnectionError, ValueError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not start reflow controller')

    def stop(self):
        for i in range(self._number_of_trials):
            try:
                # try to start device
                response = self._write_command('doStop')
                if 'Stop' in response[1]:
                    return
                else:
                    raise ValueError
            except (ConnectionError, ValueError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not stop reflow controller')

    @property
    def memory_slot(self):
        if self._memory_slot:
            return self._memory_slot
        else:
            for i in range(self._number_of_trials):
                try:
                    # get memory slot
                    response = self._write_command('settings')
                    mem_slot = int(response[1].strip('settings '))
                    if 0 <= mem_slot <= 4:
                        self._memory_slot = mem_slot
                        return self._memory_slot
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not read memory slot')

    @memory_slot.setter
    def memory_slot(self, value):
        if value > 4:
            logger.warning('The entered value is greater than the last memory location of the device. '
                           'The Value has been changed to memory slot 4.')
            value = 4

        if value is not self._memory_slot:
            self._memory_slot = None
            for i in range(self._number_of_trials):
                try:
                    # set memory slot
                    response = self._write_command('settings ' + str(value))
                    mem_slot = int(response[1].strip('settings '))
                    if mem_slot == value:
                        self._memory_slot = mem_slot
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write memory slot.')

    @property
    def temp_unit(self):
        if self._temp_unit:
            return self._temp_unit
        for i in range(self._number_of_trials):
            try:
                # get memory slot
                response = self._write_command('tempUnit')
                temp_unit = response[1].strip('tempUnit ')
                if temp_unit == 'C' or temp_unit == 'F':
                    self._temp_unit = temp_unit
                    return self._temp_unit
                else:
                    raise ValueError
            except (ConnectionError, ValueError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read temperature unit.')

    @temp_unit.setter
    def temp_unit(self, value):
        if value is not self._temp_unit:
            self._temp_unit = None
            for i in range(self._number_of_trials):
                try:
                    # set temperature unit
                    response = self._write_command('tempUnit ' + value)
                    temp_unit = response[1].strip('tempUnit ')
                    if temp_unit == value:
                        self._temp_unit = temp_unit
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write temperature unit.')

    @property
    def trace(self):
        if self._trace:
            return self._trace
        for i in range(self._number_of_trials):
            try:
                # get trace setting
                response = self._write_command('trace')
                trace = response[1].strip('trace ')
                if trace == 'OFF' or trace == 'ON':
                    self._trace = trace
                    return self._trace
                else:
                    raise ValueError
            except (ConnectionError, ValueError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read trace setting.')

    @trace.setter
    def trace(self, value):
        if value == 0:
            value = 'OFF'
        elif value == 1:
            value = 'ON'
        elif isinstance(value, str):
            value = value.upper()

        if value is not self._trace:
            self._trace = None
            for i in range(self._number_of_trials):
                try:
                    # set trace setting
                    if value == 'ON':
                        response = self._write_command('trace 1')
                    elif value == 'OFF':
                        response = self._write_command('trace 0')
                    else:
                        logger.warning('The entered value is wrong. Use "ON" or "OFF" in trace function.')
                        break
                    trace = response[1].strip('trace ')

                    if trace == value:
                        self._trace = trace
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write trace setting.')

    @property
    def temp_trace(self):
        if self._temp_trace:
            return self._temp_trace
        for i in range(self._number_of_trials):
            try:
                # get temp trace setting
                response = self._write_command('temptrace')
                temp_trace = response[1].split(' ')[2]
                if temp_trace == 'OFF' or temp_trace == 'ON':
                    self._temp_trace = temp_trace
                    return self._temp_trace
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read temptrace setting.')

    @temp_trace.setter
    def temp_trace(self, value):
        if value == 0:
            value = 'OFF'
        elif value == 1:
            value = 'ON'
        elif isinstance(value, str):
            value = value.upper()

        if value is not self._temp_trace:
            self._temp_trace = None
            for i in range(self._number_of_trials):
                try:
                    # set temp trace setting
                    if value == 'ON':
                        response = self._write_command('temptrace 1')
                    elif value == 'OFF':
                        response = self._write_command('temptrace 0')
                    else:
                        logger.warning('The entered value is wrong. Use "ON" or "OFF" in temp_trace function.')
                        break
                    temp_trace = response[1].split(' ')[2]

                    if temp_trace == value:
                        self._temp_trace = temp_trace
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError, IndexError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write temptrace setting.')

    @property
    def debug(self):
        if self._debug:
            return self._debug
        for i in range(self._number_of_trials):
            try:
                # get debug setting
                response = self._write_command('debug')
                debug = response[1].strip('debug ')
                if debug == 'OFF' or debug == 'ON':
                    self._debug = debug
                    return self._debug
                else:
                    raise ValueError
            except (ConnectionError, ValueError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read temptrace setting.')

    @debug.setter
    def debug(self, value):
        if value == 0:
            value = 'OFF'
        elif value == 1:
            value = 'ON'
        elif isinstance(value, str):
            value = value.upper()

        if value is not self._debug:
            self._debug = None
            for i in range(self._number_of_trials):
                try:
                    # set debug setting
                    if value == 'ON':
                        response = self._write_command('debug 1')
                    elif value == 'OFF':
                        response = self._write_command('debug 0')
                    else:
                        logger.warning('The entered value is wrong. Use "ON" or "OFF" in debug function.')
                        break
                    debug = response[1].strip('debug ')

                    if debug == value:
                        self._debug = debug
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write debug setting.')

    @property
    def background_light(self):
        if self._background_light:
            return self._background_light
        else:
            for i in range(self._number_of_trials):
                try:
                    # get memory slot
                    response = self._write_command('bLight')
                    background_light = int(response[1].strip('bLight '))
                    if 0 <= background_light <= 10:
                        self._background_light = background_light
                        return self._background_light
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not read background light brightness.')

    @background_light.setter
    def background_light(self, value):
        if value > 10:
            logger.warning('The entered background light brightnesss is greater than the highest possible value. '
                           'The Value has been changed to 10.')
            value = 10

        if value is not self._background_light:
            self._background_light = None
            for i in range(self._number_of_trials):
                try:
                    # set memory slot
                    response = self._write_command('bLight ' + str(value))
                    background_light = int(response[1].strip('bLight '))
                    if background_light == value:
                        self._background_light = background_light
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write background light brightness.')

    def _get_solder_temp(self, soldering_phase):
        for i in range(self._number_of_trials):
            try:
                # get temperature of the soldering phase
                response = self._write_command(soldering_phase + 'temp')
                # split string on single or double whitespaces
                response = response[1].split()
                temp = int(response[1])
                if 0 <= temp <= 254 and self.temp_unit == 'C':
                    return temp
                elif 32 <= temp <= 490 and self.temp_unit == 'F':
                    return temp
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not read {soldering_phase} temperature')

    def _set_solder_temp(self, soldering_phase, value):
        if ((value < 0 or value > 254) and self.temp_unit == 'C') or \
                ((value < 32 or value > 490) and self.temp_unit == 'F'):
            logger.warning(f'The entered {soldering_phase} temperature is greater or lower than the highest/lowest '
                           f'possible value.')
            return

        for i in range(self._number_of_trials):
            try:
                # set solder temp
                response = self._write_command(soldering_phase + 'temp ' + str(value))
                # split string on single or double whitespaces
                response = response[1].split()
                temp = int(response[1])
                if temp == value:
                    return temp
                    break
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not write {soldering_phase} temperature')

    @property
    def preheat_temp(self):
        if self._preheat_temp:
            return self._preheat_temp
        else:
            self._preheat_temp = self._get_solder_temp('pht')
            return self._preheat_temp

    @preheat_temp.setter
    def preheat_temp(self, value):
        if value is not self._preheat_temp:
            self._preheat_temp = None
            self._set_solder_temp('pht', value)
            self._preheat_temp = value

    @property
    def soak_temp(self):
        if self._soak_temp:
            return self._soak_temp
        else:
            self._soak_temp = self._get_solder_temp('soak')
            return self._soak_temp

    @soak_temp.setter
    def soak_temp(self, value):
        if value is not self._soak_temp:
            self._soak_temp = None
            self._set_solder_temp('soak', value)
            self._soak_temp = value

    @property
    def reflow_temp(self):
        if self._reflow_temp:
            return self._reflow_temp
        else:
            self._reflow_temp = self._get_solder_temp('reflow')
            return self._reflow_temp

    @reflow_temp.setter
    def reflow_temp(self, value):
        if value is not self._reflow_temp:
            self._reflow_temp = None
            self._set_solder_temp('reflow', value)
            self._reflow_temp = value

    @property
    def dwell_temp(self):
        if self._dwell_temp:
            return self._dwell_temp
        else:
            self._dwell_temp = self._get_solder_temp('dwell')
            return self._dwell_temp

    @dwell_temp.setter
    def dwell_temp(self, value):
        if value is not self._dwell_temp:
            self._dwell_temp = None
            self._set_solder_temp('dwell', value)
            self._dwell_temp = value

    def _get_solder_time(self, soldering_phase):
        for i in range(self._number_of_trials):
            try:
                # get temperature of the soldering phase
                response = self._write_command(soldering_phase + 'time')
                # split string on single or double whitespaces and remove 'Seconds'-String from number
                response = (response[1].split())[1]
                response = response[:response.find('S')]
                solder_time = int(response)
                if 0 <= solder_time <= 65534:
                    return solder_time
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not read {soldering_phase} time')

    def _set_solder_time(self, soldering_phase, value):
        if value < 0 or value > 65534:
            logger.warning(f'The entered {soldering_phase} time is greater or lower '
                           f'than the highest/lowest possible value.')
            return

        for i in range(self._number_of_trials):
            try:
                # set solder time
                response = self._write_command(soldering_phase + 'time ' + str(value))
                # split string on single or double whitespaces and remove 'Seconds'-String from number
                response = (response[1].split())[1]
                response = response[:response.find('S')]
                solder_time = int(response)
                if solder_time == value:
                    return solder_time
                    break
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not write {soldering_phase} time')

    @property
    def preheat_time(self):
        if self._preheat_time:
            return self._preheat_time
        else:
            self._preheat_time = self._get_solder_time('pht')
            return self._preheat_time

    @preheat_time.setter
    def preheat_time(self, value):
        if value is not self._preheat_time:
            self._preheat_time = None
            self._set_solder_time('pht', value)
            self._preheat_time = value

    @property
    def soak_time(self):
        if self._soak_time:
            return self._soak_time
        else:
            self._soak_time = self._get_solder_time('soak')
            return self._soak_time

    @soak_time.setter
    def soak_time(self, value):
        if value is not self._soak_time:
            self._soak_time = None
            self._set_solder_time('soak', value)
            self._soak_time = value

    @property
    def reflow_time(self):
        if self._reflow_time:
            return self._reflow_time
        else:
            self._reflow_time = self._get_solder_time('reflow')
            return self._preheat_time

    @reflow_time.setter
    def reflow_time(self, value):
        if value is not self._reflow_time:
            self._reflow_time = None
            self._set_solder_time('reflow', value)
            self._reflow_time = value

    @property
    def dwell_time(self):
        if self._dwell_time:
            return self._dwell_time
        else:
            self._dwell_time = self._get_solder_time('dwell')
            return self._dwell_time

    @dwell_time.setter
    def dwell_time(self, value):
        if value is not self._dwell_time:
            self._dwell_time = None
            self._set_solder_time('dwell', value)
            self._dwell_time = value

    def _get_solder_pwr(self, soldering_phase):
        for i in range(self._number_of_trials):
            try:
                # get temperature of the soldering phase
                response = self._write_command(soldering_phase + 'pwr')
                # split string on single or double whitespaces and remove '%'-Character from number
                response = (response[1].split())[1]
                response = response.replace('%', '')
                solder_pwr = int(response)
                if 0 <= solder_pwr <= 100:
                    return solder_pwr
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not read {soldering_phase} power')

    def _set_solder_pwr(self, soldering_phase, value):
        if value < 0 or value > 100:
            logger.warning(f'The entered {soldering_phase} power is greater or lower '
                           f'than the highest/lowest possible value.')
            return

        for i in range(self._number_of_trials):
            try:
                # set solder time
                response = self._write_command(soldering_phase + 'pwr ' + str(value))
                # split string on single or double whitespaces and remove '%'-Character from number
                response = (response[1].split())[1]
                response = response.replace('%', '')
                solder_pwr = int(response)
                if solder_pwr == value:
                    return solder_pwr
                    break
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError(f'Could not write {soldering_phase} power')

    @property
    def preheat_pwr(self):
        if self._preheat_pwr:
            return self._preheat_pwr
        else:
            self._preheat_pwr = self._get_solder_pwr('pht')
            return self._preheat_pwr

    @preheat_pwr.setter
    def preheat_pwr(self, value):
        if value is not self._preheat_pwr:
            self._preheat_pwr = None
            self._set_solder_pwr('pht', value)
            self._preheat_pwr = value

    @property
    def soak_pwr(self):
        if self._soak_pwr:
            return self._soak_pwr
        else:
            self._soak_pwr = self._get_solder_pwr('soak')
            return self._soak_pwr

    @soak_pwr.setter
    def soak_pwr(self, value):
        if value is not self._soak_pwr:
            self._soak_pwr = None
            self._set_solder_pwr('soak', value)
            self._soak_pwr = value

    @property
    def reflow_pwr(self):
        if self._reflow_pwr:
            return self._reflow_pwr
        else:
            self._reflow_pwr = self._get_solder_pwr('reflow')
            return self._reflow_pwr

    @reflow_pwr.setter
    def reflow_pwr(self, value):
        if value is not self._reflow_pwr:
            self._reflow_pwr = None
            self._set_solder_pwr('reflow', value)
            self._reflow_pwr = value

    @property
    def dwell_pwr(self):
        if self._dwell_pwr:
            return self._dwell_pwr
        else:
            self._dwell_pwr = self._get_solder_pwr('dwell')
            return self._dwell_pwr

    @dwell_pwr.setter
    def dwell_pwr(self, value):
        if value is not self._dwell_pwr:
            self._dwell_pwr = None
            self._set_solder_pwr('dwell', value)
            self._dwell_pwr = value

    @property
    def auto_extend(self):
        if self._auto_extend:
            return self._auto_extend
        for i in range(self._number_of_trials):
            try:
                # get auto extend setting
                response = self._write_command('autoextend')
                auto_extend = response[1].split(' ')[1]
                if auto_extend == 'OFF' or auto_extend == 'ON':
                    self._auto_extend = auto_extend
                    return self._auto_extend
                else:
                    raise ValueError
            except (ConnectionError, ValueError, IndexError):
                if i == self._number_of_trials - 1:
                    raise ConnectionError('Could not read autoextend setting.')

    @auto_extend.setter
    def auto_extend(self, value):
        if value == 0:
            value = 'OFF'
        elif value == 1:
            value = 'ON'
        elif isinstance(value, str):
            value = value.upper()

        if value is not self._auto_extend:
            self._auto_extend = None
            for i in range(self._number_of_trials):
                try:
                    # set auto extend setting
                    if value == 'ON':
                        response = self._write_command('autoextend 1')
                    elif value == 'OFF':
                        response = self._write_command('autoextend 0')
                    else:
                        logger.warning('The entered value is wrong. Use "ON" or "OFF" in auto_extend function.')
                        break
                    auto_extend = response[1].split(' ')[1]

                    if auto_extend == value:
                        self._auto_extend = auto_extend
                        break
                    else:
                        raise ValueError
                except (ConnectionError, ValueError, IndexError):
                    if i == self._number_of_trials - 1:
                        raise ConnectionError('Could not write autoextend setting.')
