async function handleFanControl(room, isOn) {
    try {
        const formData = new FormData();
        formData.append('room', room);
        formData.append('fan_control', isOn ? 'on' : 'off');

        const response = await fetch('/dashboard', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        });

        const data = await response.json();
        handleFanControlResponse(data, room, isOn);
    } catch (error) {
        handleFanControlError(error, room, isOn);
    }
}

function handleFanControlResponse(data, room, isOn) {
    if (data.success) {
        updateFanStatus(room, isOn);
        window.notifications.show(`Fan in ${room} ${isOn ? 'turned on' : 'turned off'}`, 'success');
    } else {
        console.error('Failed to update fan status');
        revertFanSwitch(room, !isOn);
        window.notifications.show('Failed to update fan status', 'error');
    }
}

function handleFanControlError(error, room, isOn) {
    console.error('Error:', error);
    revertFanSwitch(room, !isOn);
}

function updateFanStatus(room, isOn) {
    const statusElement = document.getElementById(`status-${room}`);
    const newStatus = isOn ? 'ON' : 'OFF';
    statusElement.innerText = newStatus;
    statusElement.className = isOn ? 'fan-status-on' : 'fan-status-off';
}

function revertFanSwitch(room, state) {
    document.getElementById(`switch-${room}`).checked = state;
}

function updateCO2Levels() {
    fetch('/api/get_co2_levels')
        .then(response => response.json())
        .then(data => updateCO2Display(data))
        .catch(error => console.error("Error fetching CO₂ levels:", error));
}

function updateCO2Display(data) {
    data.forEach(room => {
        let co2Element = document.getElementById(`co2-${room.roomGroupName}`);
        if (co2Element) {
            updateCO2Element(co2Element, room.co2);
        }
    });
}

function updateCO2Element(element, co2Level) {
    element.innerText = co2Level + " ppm";
    element.className = getCO2Class(co2Level);
}

function getCO2Class(co2Level) {
    if (co2Level < 1000) return "co2-box co2-low";
    if (co2Level < 1500) return "co2-box co2-medium";
    if (co2Level < 2000) return "co2-box co2-high";
    return "co2-box co2-critical";
}

function updateFanStatusPeriodically() {
    fetch('/api/fan_status')
        .then(response => response.json())
        .then(data => updateFanDisplays(data))
        .catch(error => console.error("Error fetching fan status:", error));
}

function updateFanDisplays(data) {
    data.forEach(fan => {
        let statusElement = document.getElementById(`status-${fan.room}`);
        let switchElement = document.getElementById(`switch-${fan.room}`);
        
        if (statusElement && switchElement) {
            updateFanDisplayElements(statusElement, switchElement, fan.status);
        }
    });
}

function updateFanDisplayElements(statusElement, switchElement, newStatus) {
    let currentStatus = statusElement.innerText.trim();
    if (currentStatus !== newStatus) {
        statusElement.innerText = newStatus;
        statusElement.className = (newStatus === "ON") ? "fan-status-on" : "fan-status-off";
        switchElement.checked = newStatus === "ON";
    }
}

async function removeFan(room) {
    try {
        const response = await fetch('/dashboard', {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: createRemoveFanFormData(room)
        });
        
        const data = await response.json();
        handleRemoveFanResponse(data, room);
    } catch (error) {
        console.error('Error:', error);
    }
}

function createRemoveFanFormData(room) {
    const formData = new FormData();
    formData.append('room', room);
    formData.append('remove_fan', 'true');
    return formData;
}

function handleRemoveFanResponse(data, room) {
    if (data.success) {
        document.querySelector(`#switch-${room}`).closest('.card').remove();
        updateAvailableRooms();
        window.notifications.show(`Fan removed from ${room}`, 'success');
    } else {
        console.error(data.error || 'Failed to remove fan');
        window.notifications.show(data.error || 'Failed to remove fan', 'error');
    }
}

async function updateAvailableRooms() {
    try {
        const response = await fetch('/api/available_rooms');
        const availableRooms = await response.json();
        updateRoomSelect(availableRooms);
    } catch (error) {
        console.error("Error updating available rooms:", error);
    }
}

function updateRoomSelect(availableRooms) {
    const select = document.getElementById("room");
    select.innerHTML = "";
    availableRooms.forEach(room => {
        const option = document.createElement("option");
        option.value = room;
        option.textContent = room;
        select.appendChild(option);
    });
}

async function handleAssignFan(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/dashboard', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            // First fetch the current CO2 level for the room
            const co2Response = await fetch('/api/get_co2_levels');
            const co2Data = await co2Response.json();
            const roomCO2 = co2Data.find(room => room.roomGroupName === data.fan.room)?.co2 || 0;
            
            // Get the appropriate CO2 class
            const co2Class = getCO2Class(roomCO2);
            
            // Create and add the new fan card with the current CO2 level
            const cardContainer = document.querySelector('.card-container');
            const newCardHTML = `
                <div class="card">
                    <div class="card-header">
                        <div style="display: flex; align-items: center;">
                            <span>Room:</span>
                            <a href="/room_graph/${data.fan.room}">${data.fan.room}</a>
                        </div>
                        <div>
                            <span>Status:</span>
                            <span id="status-${data.fan.room}" class="fan-status-off">OFF</span>
                        </div>
                    </div>
                    
                    <div class="card-main">
                        <p>CO₂ Level</p>
                        <span id="co2-${data.fan.room}" class="co2-box ${co2Class}">
                            ${roomCO2} ppm
                        </span>
                    </div>
                    
                    <div class="card-footer">
                        <form onsubmit="return false;" style="display: flex; width: 100%; align-items: center; gap: 1rem;">
                            <div style="flex: 1">
                                <label class="switch">
                                    <input type="checkbox"
                                           id="switch-${data.fan.room}"
                                           onchange="handleFanControl('${data.fan.room}', this.checked)">
                                    <span class="slider"></span>
                                </label>
                            </div>
                            <div>
                                <button type="button"
                                        onclick="removeFan('${data.fan.room}')"
                                        class="btn-secondary">Remove</button>
                            </div>
                        </form>
                    </div>
                </div>
            `;
            cardContainer.insertAdjacentHTML('beforeend', newCardHTML);
            
            // Update available rooms dropdown
            updateAvailableRooms();
            
            // Reset the form
            form.reset();
            window.notifications.show(`Fan successfully assigned to ${data.fan.room}`, 'success');
        } else {
            console.error(data.error || 'Failed to assign fan');
            window.notifications.show(data.error || 'Failed to assign fan', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        window.notifications.show('Error assigning fan', 'error');
    }
}

function initializePolling() {
    setInterval(updateCO2Levels, 10000);
    setInterval(updateFanStatusPeriodically, 1000);
    updateCO2Levels();
    updateFanStatusPeriodically();
}

window.handleFanControl = handleFanControl;
window.removeFan = removeFan;
window.handleAssignFan = handleAssignFan;

document.addEventListener('DOMContentLoaded', initializePolling);