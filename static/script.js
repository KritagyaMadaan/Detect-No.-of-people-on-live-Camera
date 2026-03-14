document.addEventListener('DOMContentLoaded', () => {
    // Tab Navigation
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const topNav = document.getElementById('top-nav');
    const secondaryNav = document.getElementById('secondary-nav');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.dataset.target;
            
            // Update active nav styling
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');
            
            // Change visible tab
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`tab-${target}`).classList.add('active');

            // Header Management
            if (target === 'monitor') {
                topNav.style.display = 'flex';
                secondaryNav.style.display = 'none';
            } else if (target === 'history') {
                topNav.style.display = 'none';
                secondaryNav.style.display = 'flex';
                secondaryNav.querySelector('.secondary-title').textContent = 'Detection History';
                secondaryNav.querySelector('.cal-btn').style.display = 'block';
                secondaryNav.querySelector('.save-btn').style.display = 'none';
            } else if (target === 'settings') {
                topNav.style.display = 'none';
                secondaryNav.style.display = 'flex';
                secondaryNav.querySelector('.secondary-title').textContent = 'Configuration';
                secondaryNav.querySelector('.cal-btn').style.display = 'none';
                secondaryNav.querySelector('.save-btn').style.display = 'block';
            } else {
                topNav.style.display = 'none';
                secondaryNav.style.display = 'flex';
                secondaryNav.querySelector('.secondary-title').textContent = 'Account';
            }
        });
    });

    // API Poll Interval
    setInterval(fetchState, 1000);

    // Initial load
    fetchState();

    // Elements
    const limitUp = document.getElementById('limit-up');
    const limitDown = document.getElementById('limit-down');
    const limitInput = document.getElementById('limit-input');
    const toggleCameraBtn = document.getElementById('toggle-camera-btn');
    const cameraBtnText = document.getElementById('camera-btn-text');
    const liveCameraWrapper = document.getElementById('live-camera-wrapper');
    const videoStream = document.getElementById('video-stream');
    const sensitivitySlider = document.getElementById('sensitivity-slider');

    let isCameraActive = false;
    let occupancyLimit = 50;

    // Toggle Camera API
    toggleCameraBtn.addEventListener('click', () => {
        const newStatus = !isCameraActive;
        fetch('/api/toggle_camera', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ active: newStatus })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                isCameraActive = data.camera_active;
                updateCameraUI();
            }
        });
    });

    function updateCameraUI() {
        if (isCameraActive) {
            cameraBtnText.textContent = "Stop Camera";
            toggleCameraBtn.classList.replace('btn-primary', 'btn-danger');
            if (toggleCameraBtn.classList.contains('btn-primary')) toggleCameraBtn.style.backgroundColor = '#d32f2f'; // fallback inline
            liveCameraWrapper.style.display = 'block';
            videoStream.src = `/video_feed?t=${new Date().getTime()}`; // force reload stream
        } else {
            cameraBtnText.textContent = "Start Camera";
            toggleCameraBtn.classList.replace('btn-danger', 'btn-primary');
            toggleCameraBtn.style.backgroundColor = '';
            liveCameraWrapper.style.display = 'none';
            videoStream.src = '';
        }
    }

    // Settings logic
    limitUp.addEventListener('click', () => {
        limitInput.value = parseInt(limitInput.value) + 5;
        updateSettings();
    });
    limitDown.addEventListener('click', () => {
        if (limitInput.value > 5) {
            limitInput.value = parseInt(limitInput.value) - 5;
            updateSettings();
        }
    });
    limitInput.addEventListener('change', updateSettings);
    sensitivitySlider.addEventListener('change', updateSettings);

    function updateSettings() {
        occupancyLimit = parseInt(limitInput.value);
        fetch('/api/update_settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                limit: occupancyLimit,
                sensitivity: parseInt(sensitivitySlider.value)
            })
        });
    }

    // Secondary Nav Actions
    secondaryNav.querySelector('.save-btn').addEventListener('click', (e) => {
        e.preventDefault();
        // Go back to monitor
        document.querySelector('[data-target="monitor"]').click();
    });
    secondaryNav.querySelector('.back-btn').addEventListener('click', () => {
        document.querySelector('[data-target="monitor"]').click();
    });


    // Main Loop Fetch Model State
    function fetchState() {
        fetch('/api/state')
        .then(res => res.json())
        .then(data => {
            // Check Camera Status Consistency
            if (data.camera_active !== isCameraActive) {
                isCameraActive = data.camera_active;
                updateCameraUI();
            }

            occupancyLimit = data.limit;
            const currentCount = data.current_count;

            // Update DOM Elements for Monitor Page
            document.getElementById('count-present').textContent = currentCount;
            document.getElementById('count-limit').textContent = occupancyLimit;
            document.getElementById('peak-today').textContent = data.peak_today;

            // AR View Elements
            document.getElementById('ar-big-count').textContent = currentCount;
            document.getElementById('ar-entries').textContent = data.total_entries + "/hr";
            document.getElementById('ar-limit').textContent = occupancyLimit;

            // Limit Inputs
            if (document.activeElement !== limitInput) {
                limitInput.value = occupancyLimit;
            }

            // Occupancy Ring Update
            const percentage = Math.min(Math.round((currentCount / occupancyLimit) * 100), 100);
            document.getElementById('occupancy-percentage').textContent = percentage + "%";
            
            // Handle Ring stroke dasharray
            // Max is 100
            const ring = document.getElementById('occupancy-ring');
            ring.setAttribute('stroke-dasharray', `${percentage}, 100`);

            // Color of ring Based on percentage
            const svgChart = document.querySelector('.circular-chart');
            if (percentage >= 90) {
                svgChart.style.stroke = '#E53935'; // Red alert
                ring.style.stroke = '#E53935';
            } else if (percentage >= 70) {
                svgChart.style.stroke = '#FB8C00'; // Warning orange
                ring.style.stroke = '#FB8C00';
            } else {
                svgChart.style.stroke = ''; // Defaults back to CSS
                ring.style.stroke = '';
            }

            // Sync History Tab only sometimes
            renderHistory(data.history);
        })
        .catch(err => console.log('Error fetching state:', err));
    }


    function renderHistory(historyData) {
        const container = document.getElementById('history-cards');
        if (container.children.length === historyData.length) return; // naive check to avoid re-rendering layout repeatedly
        
        container.innerHTML = '';
        historyData.forEach(item => {
            // Generate dummy mini bar chart dynamically
            let barHtml = '';
            for(let i=0; i<8; i++) {
                const height = 20 + Math.random() * 40;
                barHtml += `<div class="bar" style="height: ${height}%;"></div>`;
            }

            const card = document.createElement('div');
            card.className = 'card history-card';
            card.innerHTML = `
                <div class="history-card-header">
                    <div class="history-icon-wrapper">
                        <div class="history-icon"><i class="fa-regular fa-clock"></i></div>
                        <div>
                            <div class="history-date">${item.date}</div>
                            <div class="history-time">${item.time}</div>
                        </div>
                    </div>
                    <div class="history-stats">
                        <div class="history-total">${item.total}</div>
                        <span class="history-label">Total Visits</span>
                    </div>
                </div>
                <div class="history-bar-chart">
                    ${barHtml}
                </div>
                <div class="history-footer mt-2 pl-3 pb-1 border-top" style="border-top:1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                    Peak occupancy  <strong style="color:white; margin-left:10px;">${item.peak} People</strong>
                </div>
            `;
            container.appendChild(card);
        });
    }
});
