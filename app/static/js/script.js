let trayStates = {};

async function syncTrayStates() {
    const response = await fetch('/api/tray-states');
    const states = await response.json();
    
    Object.entries(states).forEach(([trayId, state]) => {
        const tray = document.getElementById(trayId);
        const cubes = tray.querySelectorAll('.ice-cube');
        
        cubes.forEach((cube, index) => {
            cube.classList.remove('active', 'frozen');
            if (state.active_cubes.includes(index)) {
                cube.classList.add('active');
                if (state.is_frozen) {
                    cube.classList.add('frozen');
                }
            }
        });
        
        const button = document.querySelector(`button[data-tray="${trayId}"]`);
        if (state.is_frozen) {
            button.disabled = true;
            button.textContent = 'Freezing...';
        }
    });
    
    trayStates = states;
}

async function freezeTray(button) {
    const trayId = button.dataset.tray;
    
    try {
        button.disabled = true;
        button.textContent = 'Freezing...';
        
        const response = await fetch('/api/freeze-tray', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ trayId })
        });
        
        if (response.ok) {
            button.textContent = 'Tray Frozen';
            await syncTrayStates();
        } else {
            button.disabled = false;
            button.textContent = `Freeze ${trayId.replace('tray', 'Tray ')}`;
        }
    } catch (error) {
        console.error('Error freezing tray:', error);
        button.disabled = false;
        button.textContent = `Freeze ${trayId.replace('tray', 'Tray ')}`;
    }
}

async function toggleBlock(element) {
    const tray = element.closest('.ice-tray');
    const trayId = tray.id;
    const cubeIndex = Array.from(tray.children).indexOf(element);
    
    // If tray frozen then stop
    if (trayStates[trayId]?.is_frozen) return;
    
    // tray not frozen then toggle cube
    const response = await fetch('/api/toggle-cube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trayId, cubeIndex })
    });
    
    if (response.ok) {
        await syncTrayStates();
    }
}

// Poll for updates every 2 seconds
document.addEventListener('DOMContentLoaded', () => {
    syncTrayStates();
    setInterval(syncTrayStates, 2000);
});