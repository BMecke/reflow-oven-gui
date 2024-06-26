import json
import os
import sys
import time
import webbrowser
import threading

from flask import Flask, request
from flask import render_template

# disable logging
import logging

from DeviceList import DeviceList
from Profiles import Profiles

logging.getLogger("werkzeug").disabled = True

profiles = Profiles()
device_list = DeviceList(profiles)

base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = str(os.path.join(sys._MEIPASS))

app = Flask(__name__,
            static_url_path='/static',
            static_folder=str(os.path.join(base_dir, 'web', 'static')),
            template_folder=str(os.path.join(base_dir, 'web', 'templates')))


@app.route("/")
def index():
    """
    This function is called on an HTTP GET to "/".
    The return corresponds to the HTTP response.

    Returns
    -------
    file "index.html"
        The html content of the main page.

    """
    return render_template('index.html')


@app.route("/reflow_data")
def get_reflow_data():
    """
    This function is called on an HTTP GET to "/reflow_data".
    The return corresponds to the HTTP response.

    Returns
    -------
    dict
        The running time, temperature of the oven and the target temperature of the profile at the current time.
        The returned values are updated in a separate thread and must only be read out here.
    """
    reflow_data = {
        'sensor_temp': device_list.selected_device.temperature,
        'target_temp': profiles.selected_profile.get_target_temperature(device_list.selected_device.runtime),
        'time': device_list.selected_device.runtime,
        'temp_unit': '°C',
        'time_unit': 's'
    }
    return json.dumps(reflow_data)


@app.route("/status")
def get_status():
    """
    This function is called on an HTTP GET to "/status".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json string indicating whether the device is currently running or in the "run out" phase.
    """
    status = {'running': device_list.selected_device.running, 'run_out': device_list.selected_device.run_out}
    return json.dumps(status)


@app.route("/devices")
def get_devices():
    """
    This function is called on an HTTP GET to "/devices".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json string containing the device list.

    """
    return json.dumps([{'id': dev.id, 'name': dev.name, 'selected': dev.selected} for dev in device_list.device_list])


@app.route("/update_device", methods=['POST'])
def update_selected_device():
    """
    This function is called on an HTTP POST to "/update_device".
    This function is called from the frontend to select a new device.
    The device to be selected is passed to the function from the frontend.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()
        device_list.selected_device = json_data['id']
        device_list.selected_device.update_profile(profiles.selected_profile)
        device_list.selected_device.set_profile_on_device(profiles.selected_profile)

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})


@app.route("/profiles")
def get_profiles():
    """
    This function is called on an HTTP GET to "/profiles".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json string containing the profile list.

    """
    return json.dumps([{'id': profile.id, 'name': profile.name, 'data': profile.data, 'selected': profile.selected}
                       for profile in profiles.profile_list])


@app.route("/update_selected_profile", methods=['POST'])
def update_selected_profile():
    """
    This function is called on an HTTP POST to "/update_profile".
    This function is called from the frontend to select a new profile.
    The profile to be selected is passed to the function from the frontend.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()
        profiles.selected_profile = json_data['id']
        device_list.selected_device.update_profile(profiles.selected_profile)
        device_list.selected_device.set_profile_on_device(profiles.selected_profile)
        device_list.selected_device.reset()

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})


@app.route("/new_profile", methods=['POST'])
def new_profile():
    """
    This function is called on an HTTP POST to "/new_profile".
    This function is called from the frontend to add a new profile.
    The profile to add is passed to the function from the frontend.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()
        profiles.add_profile(json_data['id'], json_data['name'], json_data['data'])

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})


@app.route("/update_profile", methods=['POST'])
def update_profile():
    """
    This function is called on an HTTP POST to "/update_profile".
    This function is called from the frontend to update a selected profile.
    The profile to update is passed to the function from the frontend.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()

        profiles.update_profile(json_data['id'], json_data['name'], json_data['data'])

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})

@app.route("/delete_profile", methods=['POST'])
def delete_profile():
    """
    This function is called on an HTTP POST to "/delete_profile".
    This function is called from the frontend to delete a selected profile.
    The profile to delete is passed to the function from the frontend.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()

        profiles.delete_profile(json_data['id'])

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})


@app.route("/update_start_stop", methods=['POST'])
def update_start_stop():
    """
    This function is called on an HTTP POST to "/update_start_stop".
    This function is called from the frontend to start or stop a soldering process.

    The return corresponds to the HTTP response.

    Returns
    -------
        str
            A json string indicating whether all data was received correctly.
    """
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        if device_list.selected_device.running:
            device_list.selected_device.stop()
        else:
            device_list.selected_device.start()

        return json.dumps({'received': True, 'error': None})
    else:
        return json.dumps({'received': False, 'error': 'Content-Type not supported!'})


# Charts
@app.route("/target_temp_points")
def get_target_temp_points():
    """
    This function is called on an HTTP GET to "/target_temp_points".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json array containing all points (time and temperature) for the target temperature chart.

    """
    points = profiles.selected_profile.data
    return json.dumps(points)


@app.route("/measured_temp_points")
def get_measured_temp_points():
    """
    This function is called on an HTTP GET to "/measured_temp_points".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json array containing all points (time and temperature) for the measured temperature chart.

    """
    return json.dumps(device_list.selected_device.measured_points)


@app.route("/measured_temp_point")
def get_measured_temp_point():
    """
    This function is called on an HTTP GET to "/measured_temp_point".
    The return corresponds to the HTTP response.

    Returns
    -------
    str
        A json array containing the last measured point (time and temperature) for the measured temperature chart.

    """
    return json.dumps([device_list.selected_device.runtime, device_list.selected_device.temperature])


def open_website(url, delay):
    time.sleep(delay)
    webbrowser.open(url=url, new=2)


# run the application
if __name__ == "__main__":
    thread = threading.Thread(target=open_website, args=("http://127.0.0.1:5000", 1), daemon=True)
    thread.start()
    app.run(debug=False)
