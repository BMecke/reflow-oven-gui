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
 * Modal functions
 */
function popUp(index){
    let modal = document.getElementById("profile_modal");
    modal.style.display = "block";

    let addBtn = document.getElementById('add');
    addBtn.setAttribute("onclick", "addRow()");

    let saveBtn = document.getElementById('save');
    saveBtn.setAttribute("onclick", "save(" + index + ")");

    let span = document.getElementsByClassName("close")[0];
    span.onclick = function() {
        modal.style.display = "none";
    }

    let textField = document.getElementById("profile_name");
    textField.setAttribute("placeholder", `Profile ${index}`);
    textField.setAttribute("defaultValue", `Profile ${index}`);
}

// function to add a row for a new point
function addRow(){
    let table = document.getElementById('profile_points');
    let row = table.insertRow();
    for(let i = 0; i < 5; ++i){
        let data = row.insertCell(i);
        if(i == 0){
            data.textContent = row.rowIndex;
        } else 
        if(i == 4){
            let btn = document.createElement("BUTTON")
            data.appendChild(btn);
            btn.setAttribute("onclick", "deleteRow(" + row.rowIndex + ")");
            btn.innerText = "Delete"
        }
        else{
            let input = document.createElement("INPUT");
            input.setAttribute("type", "number");
            input.setAttribute("min", "0");
            switch (i) {
                case 1:
                    input.setAttribute("placeholder", `${row.rowIndex*30}` );
                    input.setAttribute("max", "900");
                    break;
                case 2:
                    input.setAttribute("placeholder", "25" );
                    input.setAttribute("max", "250");
                    break;
                case 3:
                    input.setAttribute("placeholder", "100" );
                    input.setAttribute("max", "100");
                    break;
            }
            data.appendChild(input);
        }
    }
}

// function to delete a point and its data values in the row
function deleteRow(index){
    let table = document.getElementById('profile_points')
    table.deleteRow(index - 1);
    for (let i = index-1; i < table.rows.length; ++i) {
        table.rows[i].cells[0].textContent = i+1;
        table.rows[i].cells[4].firstChild.setAttribute("onclick", "deleteRow(" + (i+1) + ")");
    }
}

// function to save the points as a profile
function save(profile){
    let table = document.getElementById('profile_points');
    let textField = document.getElementById("profile_name");

    let id = "p" + profile;
    let name = textField.value != "" ? textField.value : textField.defaultValue;
    let data = [];
    for (let i = 0; i < table.rows.length; ++i) {
        data[i] = [table.rows[i].cells[1].firstChild.valueAsNumber || 30*(i+1),
                    table.rows[i].cells[2].firstChild.valueAsNumber || 25,
                    table.rows[i].cells[3].firstChild.valueAsNumber || 100];
    }
    postNewProfile(id, name, data);

    let modal = document.getElementById("profile_modal");
    modal.style.display = "none";

    updateProfileList();
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