async function getDeviceList(){
    let devices = await getData("/devices");
    deviceList = devices;
    return devices
}

async function getProfileList(){
    let profiles = await getData("/profiles");
    profileList = profiles;
    return profiles
}

function replaceSensorTemp(temp){
    let td = document.getElementById('sensor_temp');
    td.innerHTML = temp;
}

function replaceTargetTemp(temp){
    let td = document.getElementById('target_temp');
    td.innerHTML = temp;
}

function replaceTime(temp){
    let td = document.getElementById('time');
    td.innerHTML = temp;
}

async function getData(path){
  let host = window.location.protocol + "//" + window.location.host;
  let url = host + path
  let response = await fetch(url);
  let data = await response.json();
  return await data;
}

// https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch
async function postJSON(path, data) {
  let host = window.location.protocol + "//" + window.location.host;
  let url = host + path
  try {
    const response = await fetch(url, {
      method: "POST", // or 'PUT'
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();
    //console.log("Success:", result);
  } catch (error) {
    //console.error("Error:", error);
  }
}

// https://stackoverflow.com/questions/16096872/how-to-sort-2-dimensional-array-by-column-value
function sortFunction(a, b) {
    if (a[0] === b[0]) {
        return 0;
    }
    else {
        return (a[0] < b[0]) ? -1 : 1;
    }
}
