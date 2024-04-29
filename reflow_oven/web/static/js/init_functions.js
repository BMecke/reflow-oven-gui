var deviceList = new Array();
var profileList = new Array();
var deviceRunning = false;
var deviceRunOut = false;
var chartLength = 0;
var lastUpdatedPoint = [-1, -1];


function update(){
    updateProfileList();
    updateDeviceList();
    updateReflowData();
    updateStatus();
    updateTargetTempPoints();
}
update();
updateMeasuredTempPoints();

// periodically call update functions
var intervalId = setInterval(function() {
    update();
    if(deviceRunning || deviceRunOut){
        updateLastMeasuredTempPoint();
    }
    else {
        lastUpdatedPoint = [-1, -1];
    }
    //updateMeasuredTempPoints();
}, 1000);
