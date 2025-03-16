document.addEventListener('DOMContentLoaded', function() {
    console.log('Analytics JS loaded');
    // Initialize with data from template
    const analyticsData = JSON.parse(document.getElementById('initialData').textContent);
    updateDashboard(analyticsData);
    updateTable(analyticsData.fans);
    
    // Update periodically
    setInterval(updateAnalytics, 10000);
});

async function updateAnalytics() {
    try {
        const response = await fetch('/api/analytics');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Analytics data received:', data);
        updateDashboard(data);
        updateTable(data.fans);
    } catch (error) {
        console.error('Error fetching analytics:', error);
    }
}

function updateDashboard(data) {
    document.getElementById('totalRuntime').textContent = `${data.totalRuntime}h`;
    document.getElementById('activeFans').textContent = data.activeFans;
    document.getElementById('efficiency').textContent = `${data.efficiency}%`;
}

function updateTable(fans) {
    const tbody = document.getElementById('fanUsageTable');
    tbody.innerHTML = '';

    fans.forEach(fan => {
        const statusClass = fan.status.toLowerCase() === 'on' ? 'status-active' : 'status-inactive';
        const row = `
            <tr>
                <td>${fan.room}</td>
                <td><span class="status-badge ${statusClass}">${fan.status}</span></td>
                <td>${fan.runtimeToday}h</td>
                <td>${fan.lastActive}</td>
                <td>${fan.co2Reduced} ppm</td>
            </tr>
        `;
        tbody.innerHTML += row;
    });
}