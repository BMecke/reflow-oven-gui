// updated the displayed reflow data (sensor temp, target temp, time)
async function updateReflowData(){
    let data = await getData("/reflow_data");
    replaceSensorTemp(data["sensor_temp"] + data["temp_unit"]);
    replaceTargetTemp(data["target_temp"] + data["temp_unit"]);
    replaceTime(data["time"] + data["time_unit"]);
}

// updated the displayed actions (On or Off)
async function updateStatus(){
    let data = await getData("/status");
    let button = document.getElementById('start_stop');
    if(data["running"] === true){
        deviceRunning = true;
        button.innerHTML = "Stop";
    }
    else {
        deviceRunning = false;
        button.innerHTML = "Start";
    }
    button.setAttribute("onclick", "postStartStop()");
    deviceRunOut = data["run_out"]
}

// updated the displayed device list
async function updateDeviceList(){
    let devices = await getDeviceList();
    let div = document.getElementById('device_list');
    // remove all children
    div.textContent = "";

    for (let i = 0; i < devices.length; i++) {
        let link = document.createElement("a");
        link.textContent = devices[i]["name"];
        link.href = "javascript:void(0);";
        link.setAttribute("onclick", "postDevice(" + i + ")");
        if(devices[i]['selected'])
            link.style.color =  "#009374";
        div.appendChild(link);
    }
}

// updated the displayed profile list
async function updateProfileList(){
    let profiles = await getProfileList();
    let div = document.getElementById('profile_list');
    // remove all children
    div.textContent = "";

    for (let i = 0; i < profiles.length; i++) {
        let link = document.createElement("a");
        link.textContent = profiles[i]['name'];
        link.href = "javascript:void(0);";
        link.setAttribute("onclick", "postProfile(" + i + ")");
        if(profiles[i]['selected'])
            link.style.color =  "#009374";
        div.appendChild(link);
    }
    let link = document.createElement("a");
    link.textContent = "New Profile";
    link.href = "javascript:void(0);";
    link.setAttribute("onclick", "popUp(" + (profiles.length + 1) + ")");
    div.appendChild(link);
}

/**
 * Chart functions
 */
async function updateTargetTempPoints(){
    let points = await getData("/target_temp_points");
    setTargetTempInChart(points);
}

async function updateMeasuredTempPoints(){
    let points = await getData("/measured_temp_points");
    points.sort(sortFunction);
    setMeasuredTempInChart(points);
    lastUpdatedPoint = points.at(-1);
}


async function updateLastMeasuredTempPoint(){
    let point = await getData("/measured_temp_point");
    if(lastUpdatedPoint[0] != point[0]){
        lastUpdatedPoint = point;
        addMeasuredTempPointInChart(point);
    }
}