document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const activeThemeBadge = document.getElementById('active-theme-name');
    const wallpaperCount = document.getElementById('wallpaper-count');
    const galleryLoading = document.getElementById('gallery-loading');
    const galleryEmpty = document.getElementById('gallery-empty');
    const wallpapersGrid = document.getElementById('wallpapers-grid');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const progressContainer = document.getElementById('upload-progress-container');
    const progressBar = document.getElementById('progress-bar');
    const uploadFilename = document.getElementById('upload-filename');
    const uploadPercentage = document.getElementById('upload-percentage');

    let currentTheme = 'Default';
    let wallpapersList = [];
    let activeWallpaperName = null;

    // Load initial system status
    fetchStatus();

    // Event Listeners for drag-and-drop
    browseBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // Avoid triggering drop-zone click
        fileInput.click();
    });

    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    // Fetch Status from Python Backend
    async function fetchStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Failed to fetch status');
            const data = await response.json();

            currentTheme = data.theme;
            wallpapersList = data.wallpapers || [];
            activeWallpaperName = data.active_wallpaper;

            updateUI();
        } catch (error) {
            console.error('Error fetching status:', error);
            showToast('Could not load wallpapers. Make sure the server is running.', 'error');
        }
    }

    // Update UI elements with fetched data
    function updateUI() {
        activeThemeBadge.textContent = currentTheme;
        wallpaperCount.textContent = `${wallpapersList.length} Wallpaper${wallpapersList.length === 1 ? '' : 's'}`;

        galleryLoading.classList.add('hidden');

        if (wallpapersList.length === 0) {
            galleryEmpty.classList.remove('hidden');
            wallpapersGrid.classList.add('hidden');
        } else {
            galleryEmpty.classList.add('hidden');
            wallpapersGrid.classList.remove('hidden');

            renderGrid();
        }
    }

    // Render the grid of wallpapers
    function renderGrid() {
        wallpapersGrid.innerHTML = '';

        wallpapersList.forEach(filename => {
            const isActive = filename === activeWallpaperName;
            
            const card = document.createElement('div');
            card.className = `wallpaper-card ${isActive ? 'active' : ''}`;
            
            // Image source goes to the local Python API endpoint serving image binary data
            const imgSrc = `/api/wallpaper/${encodeURIComponent(filename)}`;

            card.innerHTML = `
                <div class="card-img-wrapper">
                    ${isActive ? '<span class="active-overlay"><i class="fa-solid fa-circle-check"></i> Active</span>' : ''}
                    <img src="${imgSrc}" class="wallpaper-img" alt="${filename}" loading="lazy">
                    <div class="card-overlay">
                        <span class="card-filename" title="${filename}">${filename}</span>
                        <div class="card-actions">
                            ${!isActive ? `<button class="btn btn-primary btn-set" data-filename="${filename}"><i class="fa-solid fa-check"></i> Set</button>` : ''}
                            <button class="btn btn-action-delete btn-delete" data-filename="${filename}"><i class="fa-regular fa-trash-can"></i> Delete</button>
                        </div>
                    </div>
                </div>
            `;

            // Attach event listeners to card actions
            const setBtn = card.querySelector('.btn-set');
            if (setBtn) {
                setBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    setWallpaper(filename);
                });
            }

            const deleteBtn = card.querySelector('.btn-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteWallpaper(filename);
            });

            wallpapersGrid.appendChild(card);
        });
    }

    // Set Wallpaper action
    async function setWallpaper(filename) {
        showToast(`Applying ${filename}...`, 'success');
        try {
            const response = await fetch('/api/set', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            const result = await response.json();
            if (response.ok && result.status === 'success') {
                showToast(`Wallpaper applied successfully!`, 'success');
                fetchStatus();
            } else {
                throw new Error(result.message || 'Failed to apply wallpaper');
            }
        } catch (error) {
            console.error('Error applying wallpaper:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    // Delete Wallpaper action
    async function deleteWallpaper(filename) {
        if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
            return;
        }

        try {
            const response = await fetch('/api/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filename })
            });

            const result = await response.json();
            if (response.ok && result.status === 'success') {
                showToast(`Deleted ${filename}`, 'success');
                fetchStatus();
            } else {
                throw new Error(result.message || 'Failed to delete');
            }
        } catch (error) {
            console.error('Error deleting wallpaper:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    // File Upload Handler with progress bar tracking
    function handleFileUpload(file) {
        // Validate file type
        if (!file.type.match('image.*')) {
            showToast('Please upload only image files.', 'error');
            return;
        }

        progressContainer.classList.remove('hidden');
        uploadFilename.textContent = file.name;
        progressBar.style.width = '0%';
        uploadPercentage.textContent = '0%';

        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentage = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = `${percentage}%`;
                uploadPercentage.textContent = `${percentage}%`;
            }
        });

        // Track completion
        xhr.addEventListener('load', () => {
            progressContainer.classList.add('hidden');
            if (xhr.status === 200) {
                const result = JSON.parse(xhr.responseText);
                showToast(result.message || 'Upload complete!', 'success');
                fetchStatus();
            } else {
                let msg = 'Upload failed';
                try {
                    const result = JSON.parse(xhr.responseText);
                    msg = result.message || msg;
                } catch(e){}
                showToast(`Error: ${msg}`, 'error');
            }
        });

        // Handle error
        xhr.addEventListener('error', () => {
            progressContainer.classList.add('hidden');
            showToast('Network error occurred during upload.', 'error');
        });

        // Open and send raw binary data
        xhr.open('POST', '/api/upload');
        xhr.setRequestHeader('X-File-Name', encodeURIComponent(file.name));
        xhr.send(file);
    }

    // Toast Notification System
    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'success' 
            ? '<i class="fa-solid fa-circle-check"></i>' 
            : '<i class="fa-solid fa-circle-exclamation"></i>';

        toast.innerHTML = `
            ${icon}
            <span class="toast-message">${message}</span>
        `;

        toastContainer.appendChild(toast);

        // Slide in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Slide out and remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    }
});
