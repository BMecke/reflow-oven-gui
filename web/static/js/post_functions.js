// post message when start/stop button is clicked
function postStartStop(){
    // clear chart on start
    if(!deviceRunning){
        clearTargetTempInChart();
        clearMeasuredTempInChart();
        chartLength = 0;
    }
    postJSON("/update_start_stop", "");

    // The following lines ensure that the chart always starts at 0 and not sometimes randomly at 1
    // ToDo: improve the following lines
    lastUpdatedPoint = [-1, -1];
    update();
    updateLastMeasuredTempPoint();
}

function postDevice(deviceIndex){
    postJSON("/update_device", deviceList[deviceIndex]);
}

function postProfile(profileIndex){
    postJSON("/update_profile", profileList[profileIndex]);
    clearTargetTempInChart();
    clearMeasuredTempInChart();
    chartLength = 0;
}

function postNewProfile(id, name, data){
    postJSON("/new_profile", {id, name, data});
    //console.log(JSON.stringify({id, name, data}));
}