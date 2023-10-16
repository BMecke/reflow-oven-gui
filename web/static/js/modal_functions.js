/**
 * Modal functions
 */
async function popUp(index){
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
async function addRow(){
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
async function deleteRow(index){
    let table = document.getElementById('profile_points')
    table.deleteRow(index - 1);
    for (let i = index-1; i < table.rows.length; ++i) {
        table.rows[i].cells[0].textContent = i+1;
        table.rows[i].cells[4].firstChild.setAttribute("onclick", "deleteRow(" + (i+1) + ")");
    }
}

// function to save the points as a profile
async function save(profile){
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