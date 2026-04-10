document.addEventListener('DOMContentLoaded', async () => {
    // Attempt to auto-fill the URL from the active tab
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs[0]) {
            const currentUrl = tabs[0].url;
            if (currentUrl.includes('youtube.com') || currentUrl.includes('youtu.be') || currentUrl.includes('instagram.com/reel')) {
                document.getElementById('url').value = currentUrl;
            }
        }
    });

    const pitchInput = document.getElementById('pitch');
    document.getElementById('pitch-down').addEventListener('click', () => {
        let val = parseInt(pitchInput.value || 0);
        if (val > -12) pitchInput.value = val - 1;
    });
    
    document.getElementById('pitch-up').addEventListener('click', () => {
        let val = parseInt(pitchInput.value || 0);
        if (val < 12) pitchInput.value = val + 1;
    });

    document.getElementById('process-btn').addEventListener('click', async () => {
        const url = document.getElementById('url').value.trim();
        const pitch = parseInt(pitchInput.value || 0);

        if (!url) {
            updateStatus('Please enter a valid URL', 'error');
            return;
        }

        setLoading(true);
        updateStatus('Connecting to backend...', 'info');

        try {
            // Initiate the request to the local backend
            // To prevent hanging on long tasks (Spleeter can take minutes), we assume the connection stays open.
            const response = await fetch('http://localhost:8000/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, pitch_shift: pitch })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Server error: ${response.status}`);
            }

            updateStatus('Processing complete. Downloading...', 'info');
            
            const blob = await response.blob();
            const downloadUrl = URL.createObjectURL(blob);
            
            // Try extracting original filename from Content-Disposition header
            let filename = 'karaoke_track.mp3';
            const disposition = response.headers.get('Content-Disposition');
            if (disposition && disposition.indexOf('attachment') !== -1) {
                const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                const matches = filenameRegex.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            chrome.downloads.download({
                url: downloadUrl,
                filename: filename
            }, (downloadId) => {
                 if(chrome.runtime.lastError) {
                     updateStatus('Download failed: ' + chrome.runtime.lastError.message, 'error');
                 } else {
                     updateStatus('Success! Track downloaded.', 'success');
                 }
            });

        } catch (error) {
            // Check if it's a fetch connection error
            if (error.message === 'Failed to fetch') {
                 updateStatus('Cannot connect to standard backend (is it running?)', 'error');
            } else {
                 updateStatus(`Error: ${error.message}`, 'error');
            }
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        const processBtn = document.getElementById('process-btn');
        const btnText = processBtn.querySelector('.btn-text');
        const loader = document.getElementById('loader');
        
        if (isLoading) {
            processBtn.disabled = true;
            btnText.style.display = 'none';
            loader.style.display = 'block';
        } else {
            processBtn.disabled = false;
            btnText.style.display = 'block';
            loader.style.display = 'none';
        }
    }

    function updateStatus(message, type) {
        const statusText = document.getElementById('status-text');
        statusText.textContent = message;
        statusText.className = `status-${type}`;
    }
});
