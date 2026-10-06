/* LOAD STATS */
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('kpi-total').textContent = data.total.toLocaleString();
        document.getElementById('kpi-normal').textContent = data.normal.toLocaleString();
        document.getElementById('kpi-anomalies').textContent = data.anomalies.toLocaleString();
        document.getElementById('kpi-average').textContent = data.average + ' kW';
    } catch (err) {
        console.error('Error loading stats:', err);
    }
}

/* MAIN TIME SERIES CHART */
async function loadMainChart() {
    try {
        const res = await fetch('/api/timeseries');
        const data = await res.json();

        const times = data.map(d => d.time);
        const values = data.map(d => d.value);
        const anomalyTimes = data.filter(d => d.status === 'Anomaly').map(d => d.time);
        const anomalyValues = data.filter(d => d.status === 'Anomaly').map(d => d.value);

        const trace1 = {
            x: times,
            y: values,
            type: 'scatter',
            mode: 'lines',
            name: 'Consumption',
            line: { color: '#00d4ff', width: 1 },
            opacity: 0.6
        };

        const trace2 = {
            x: anomalyTimes,
            y: anomalyValues,
            type: 'scatter',
            mode: 'markers',
            name: 'Anomaly',
            marker: { color: '#ff4757', size: 6 }
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(255,255,255,0.02)',
            font: { color: '#8892b0' },
            xaxis: {
                gridcolor: 'rgba(0,212,255,0.08)',
                title: 'Date & Time',
                zeroline: false
            },
            yaxis: {
                gridcolor: 'rgba(0,212,255,0.08)',
                title: 'Power (kW)',
                zeroline: false
            },
            margin: { t: 20, b: 50, l: 60, r: 20 },
            height: 450,
            legend: {
                orientation: 'h',
                y: 1.08,
                font: { color: '#e0e0e0' }
            },
            hovermode: 'x unified',
            hoverlabel: {
                bgcolor: '#1a1a3a',
                bordercolor: '#00d4ff',
                font: {
                    color: '#ffffff',
                    size: 13,
                    family: 'Inter, sans-serif'
                }
            }
        };

        document.getElementById('main-chart').innerHTML = '';
        Plotly.newPlot('main-chart', [trace1, trace2], layout, { responsive: true });
    } catch (err) {
        console.error('Error loading main chart:', err);
        document.getElementById('main-chart').innerHTML =
            '<div class="loader">Failed to load chart</div>';
    }
}

/* HOURLY PATTERN CHART */
async function loadHourlyChart() {
    try {
        const res = await fetch('/api/hourly-pattern');
        const data = await res.json();

        const trace = {
            x: data.map(d => d.hour),
            y: data.map(d => d.value),
            type: 'bar',
            marker: {
                color: data.map(d => d.value),
                colorscale: [
                    [0, '#1a1a3a'],
                    [0.5, '#00d4ff'],
                    [1, '#7b2ff7']
                ],
                line: { width: 0 }
            },
            hovertemplate: 'Hour: %{x}<br>Avg: %{y:.3f} kW<extra></extra>'
        };

        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(255,255,255,0.02)',
            font: { color: '#8892b0' },
            xaxis: {
                title: 'Hour of Day',
                gridcolor: 'rgba(0,212,255,0.08)',
                zeroline: false
            },
            yaxis: {
                title: 'Avg Power (kW)',
                gridcolor: 'rgba(0,212,255,0.08)',
                zeroline: false
            },
            margin: { t: 15, b: 45, l: 55, r: 20 },
            height: 320,
            showlegend: false,
            hoverlabel: {
                bgcolor: '#1a1a3a',
                bordercolor: '#00d4ff',
                font: {
                    color: '#ffffff',
                    size: 13,
                    family: 'Inter, sans-serif'
                }
            }
        };

        document.getElementById('hourly-chart').innerHTML = '';
        Plotly.newPlot('hourly-chart', [trace], layout, { responsive: true });
    } catch (err) {
        console.error('Error loading hourly chart:', err);
        document.getElementById('hourly-chart').innerHTML =
            '<div class="loader">Failed to load</div>';
    }
}

/* DISTRIBUTION CHART */
async function loadDistChart() {
    try {
        const res = await fetch('/api/distribution');
        const data = await res.json();

        const trace1 = {
            x: data.normal,
            type: 'histogram',
            name: 'Normal',
            marker: { color: '#2ed573' },
            opacity: 0.7,
            nbinsx: 40
        };

        const trace2 = {
            x: data.anomaly,
            type: 'histogram',
            name: 'Anomaly',
            marker: { color: '#ff4757' },
            opacity: 0.8,
            nbinsx: 40
        };

        const layout = {
            barmode: 'overlay',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(255,255,255,0.02)',
            font: { color: '#8892b0' },
            xaxis: {
                title: 'Power (kW)',
                gridcolor: 'rgba(0,212,255,0.08)',
                zeroline: false
            },
            yaxis: {
                title: 'Frequency',
                gridcolor: 'rgba(0,212,255,0.08)',
                zeroline: false
            },
            margin: { t: 15, b: 45, l: 55, r: 20 },
            height: 320,
            legend: {
                orientation: 'h',
                y: 1.12,
                font: { color: '#e0e0e0' }
            },
            hoverlabel: {
                bgcolor: '#1a1a3a',
                bordercolor: '#00d4ff',
                font: {
                    color: '#ffffff',
                    size: 13,
                    family: 'Inter, sans-serif'
                }
            }
        };

        document.getElementById('dist-chart').innerHTML = '';
        Plotly.newPlot('dist-chart', [trace1, trace2], layout, { responsive: true });
    } catch (err) {
        console.error('Error loading distribution chart:', err);
        document.getElementById('dist-chart').innerHTML =
            '<div class="loader">Failed to load</div>';
    }
}

/* SEND MESSAGE */
async function sendMessage() {
    const input = document.getElementById('user-input');
    const question = input.value.trim();
    if (!question) return;

    addMessage('user', question);
    input.value = '';

    try {
        const res = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        const data = await res.json();
        setTimeout(() => addMessage('bot', data.answer), 250);
    } catch (err) {
        console.error('Error asking question:', err);
        addMessage('bot', 'Sorry, something went wrong. Please try again.');
    }
}

/* ADD MESSAGE */
function addMessage(role, text) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `
        <div class="avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="text">${text}</div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

/* EVENT LISTENERS */
document.getElementById('send-btn').addEventListener('click', sendMessage);

document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

/* INIT */
window.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadMainChart();
    loadHourlyChart();
    loadDistChart();
});