/**
 * Modal functions
 */
async function addProfile(index){
    popUp(index, null);
}

async function editProfile(index){
    profile = profileList[index]
    popUp(index, profile);
}

async function popUp(index, profile){
    deleteAllRows();

    let modal_h3 = document.getElementById("modal_h3");
    if(profile){
        modal_h3.innerText = "Edit profile";

        // text field with profile name
        let textField = document.getElementById("profile_name");
        textField.setAttribute("placeholder", `${profile["name"]}`);
        textField.setAttribute("defaultValue", `${profile["name"]}`);

        for (let i = 0; i < profile["data"].length; i++) {
            addRow(profile["data"][i]);
        }
    }
    else{
        modal_h3.innerText = "Add new profile";

            // text field with profile name
            let textField = document.getElementById("profile_name");
            textField.setAttribute("placeholder", `Profile ${index}`);
            textField.setAttribute("defaultValue", `Profile ${index}`);

        for (let i = 0; i < 4; i++) {
            addRow(null);
        }
    }

    let modal = document.getElementById("profile_modal");
    modal.style.display = "block";

    let addBtn = document.getElementById('add');
    addBtn.setAttribute("onclick", "addRow()");

    let saveBtn = document.getElementById('save');
    if(profile){
        saveBtn.setAttribute("onclick", "saveUpdatedProfile(" + index + ")");
    }
    else{
        saveBtn.setAttribute("onclick", "saveNewProfile(" + index + ")");
    }


    let span = document.getElementsByClassName("close")[0];
    span.onclick = function() {
        modal.style.display = "none";
    }
}

// function to add a row for a new point
async function addRow(profile_data){
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
            btn.classList.add('modal_delete_button')
            btn.innerHTML = "<img class=\"icon\" src=\"/static/icons/delete.svg\"> Delete"
        }
        else{
            let input = document.createElement("INPUT");
            input.setAttribute("type", "number");
            input.setAttribute("min", "0");

            if(profile_data){
                switch (i) {
                    case 1:
                        input.setAttribute("placeholder", `${profile_data[0]}`);
                        input.setAttribute("max", "900");
                        break;
                    case 2:
                        input.setAttribute("placeholder", `${profile_data[1]}`);
                        input.setAttribute("max", "250");
                        break;
                    case 3:
                        input.setAttribute("placeholder", `${profile_data[2]}`);
                        input.setAttribute("max", "100");
                        break;
                }
            }
            else{
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
            }
            data.appendChild(input);
        }
    }
}

// function to delete a point and its data values in the row
async function deleteRow(index){
    let table = document.getElementById('profile_points')
    table.deleteRow(index - 1);
    for (let i = index-1; i < table.rows.length; ++i) {
        table.rows[i].cells[0].textContent = i+1;
        table.rows[i].cells[4].firstChild.setAttribute("onclick", "deleteRow(" + (i+1) + ")");
    }
}

async function deleteAllRows(){
    let table = document.getElementById('profile_points');
    table.innerHTML = ""
}

// function to save the points as a profile
async function saveNewProfile(index){
    let id = "p" + index;

    enteredProfileData = getEnteredProfileData()
    postNewProfile(id, enteredProfileData["name"], enteredProfileData["data"]);

    let modal = document.getElementById("profile_modal");
    modal.style.display = "none";

    updateProfileList();
}

// function to save the points as a profile
async function saveUpdatedProfile(index){
    profile = profileList[index];

    enteredProfileData = getEnteredProfileData()
    postUpdatedProfile(profile["id"], enteredProfileData["name"], enteredProfileData["data"]);

    let modal = document.getElementById("profile_modal");
    modal.style.display = "none";

    updateProfileList();
}

function getEnteredProfileData(profile){
    let table = document.getElementById("profile_points");
    let textField = document.getElementById("profile_name");

    let name = textField.value != "" ? textField.value : textField.placeholder;
    let data = [];
    for (let i = 0; i < table.rows.length; ++i) {
        time_field = table.rows[i].cells[1].firstChild
        temp_field = table.rows[i].cells[2].firstChild
        power_field = table.rows[i].cells[3].firstChild

        data[i] = [time_field.valueAsNumber || parseFloat(time_field.placeholder),
                   temp_field.valueAsNumber || parseFloat(temp_field.placeholder),
                   power_field.valueAsNumber || parseFloat(power_field.placeholder)];
    }

    return {"name": name, "data": data}
}