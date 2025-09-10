document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('qr-scan-form');
    const manualForm = document.getElementById('manual-attendance-form');
    const messageContainer = document.getElementById('message-container');
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const debugCameraBtn = document.getElementById('debug-camera');

    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');
    const scannerStatus = document.getElementById('scanner-status');
    const debugInfo = document.getElementById('debug-info');

    let stream = null;
    let isScanning = false;
    const eventSelect = document.getElementById('event-select');
    const hiddenAttendanceType = document.getElementById('hidden-attendance-type');

    if (eventSelect) {
        eventSelect.addEventListener('change', function () {
            const value = this.value;
            if (value) {
                hiddenAttendanceType.value = value;
                updateScannerStatus(`Event selected: ${this.options[this.selectedIndex].text}. You can start the scanner.`, 'info');
            }
        });
    }

    let scanInterval = null;
    let debugInterval = null;
    let isProcessing = false;

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (isProcessing) return;
        isProcessing = true;

        const now = new Date();
        const clientDate = now.toISOString().split('T')[0];
        const clientTime = now.toTimeString().split(' ')[0];

        const formData = new FormData(form);
        formData.append('client_date', clientDate);
        formData.append('client_time', clientTime);

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('success', data.message);

                    if (data.user && data.user.is_new_friend && data.user.timer_status) {
                        const timerInfo = document.createElement('div');
                        timerInfo.className = 'alert alert-info mt-2';
                        timerInfo.innerHTML = `
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>New Friend Status:</strong> ${data.user.timer_status}${data.user.timer_status == 1 ? 'st' : data.user.timer_status == 2 ? 'nd' : data.user.timer_status == 3 ? 'rd' : 'th'} Timer
                    `;
                        document.querySelector('.scanner-container').appendChild(timerInfo);
                    }

                    updateScannerStatus('Attendance recorded! Scanning for next QR code...', 'success');
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    if (data.message && data.message.toLowerCase() === 'qr is already scanned') {
                        showMessage('error', 'qr is already scanned');
                        updateScannerStatus('qr is already scanned', 'error');
                    } else {
                        showMessage('error', data.message);
                        updateScannerStatus('Error: ' + data.message, 'error');
                    }
                }
            })
            .catch(error => {
                showMessage('error', 'An error occurred while processing the QR code.');
                updateScannerStatus('Error processing QR code', 'error');
            })
            .finally(() => {
                isProcessing = false;
            });
    });

    manualForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const now = new Date();
        const clientDate = now.toISOString().split('T')[0];
        const clientTime = now.toTimeString().split(' ')[0];

        const formData = new FormData(manualForm);
        formData.append('client_date', clientDate);
        formData.append('client_time', clientTime);

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('success', data.message);

                    if (data.user && data.user.is_new_friend && data.user.timer_status) {
                        const timerInfo = document.createElement('div');
                        timerInfo.className = 'alert alert-info mt-2';
                        timerInfo.innerHTML = `
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>New Friend Status:</strong> ${data.user.timer_status}${data.user.timer_status == 1 ? 'st' : data.user.timer_status == 2 ? 'nd' : data.user.timer_status == 3 ? 'rd' : 'th'} Timer
                    `;
                        document.querySelector('.scanner-container').appendChild(timerInfo);
                    }

                    manualForm.reset();
                    setTimeout(() => {
                        location.reload();
                    }, 2000);
                } else {
                    showMessage('error', data.message);
                }
            })
            .catch(error => {
                showMessage('error', 'An error occurred while recording manual attendance.');
            });
    });

    function showMessage(type, message) {
        const alertClass = type === 'success' ? 'success-alert' : 'error-alert';
        const icon = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';

        const messageDiv = document.createElement('div');
        messageDiv.className = alertClass;
        messageDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="${icon} me-2"></i>
                <span>${message}</span>
            </div>
        `;

        messageContainer.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    startCameraBtn.addEventListener('click', async function () {
        if (!eventSelect || !eventSelect.value) {
            showMessage('error', 'Please select a church event before starting the scanner.');
            updateScannerStatus('Please select a church event first.', 'error');
            return;
        }
        try {
            if (typeof jsQR === 'undefined') {
                showMessage('error', 'QR code library not loaded. Please refresh the page.');
                return;
            }

            let constraints = {
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280, min: 640 },
                    height: { ideal: 720, min: 480 },
                    frameRate: { ideal: 30, max: 60 }
                }
            };

            try {
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                console.log('Camera access successful with environment facing mode');
            } catch (err) {
                console.log('Environment camera failed, trying user facing mode:', err);
                constraints = {
                    video: {
                        facingMode: 'user',
                        width: { ideal: 1280, min: 640 },
                        height: { ideal: 720, min: 480 },
                        frameRate: { ideal: 30, max: 60 }
                    }
                };

                try {
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    console.log('Camera access successful with user facing mode');
                } catch (err2) {
                    console.log('User camera failed, trying basic constraints:', err2);
                    constraints = {
                        video: {
                            width: { ideal: 1280, min: 640 },
                            height: { ideal: 720, min: 480 }
                        }
                    };
                    stream = await navigator.mediaDevices.getUserMedia(constraints);
                    console.log('Camera access successful with basic constraints');
                }
            }

            video.srcObject = stream;
            video.style.display = 'block';
            startCameraBtn.style.display = 'none';
            stopCameraBtn.style.display = 'inline-block';
            debugCameraBtn.style.display = 'inline-block';

            video.onloadedmetadata = function () {
                video.play();
                isScanning = true;
                startQRScanning();
                updateScannerStatus(`Camera active - Event: ${eventSelect.options[eventSelect.selectedIndex].text}. Point at QR code to record attendance.`, 'scanning');
                updateDebugInfo();
                showMessage('success', 'Automatic scanner started! Point at QR codes to record attendance instantly.');
            };

        } catch (err) {
            console.error('Camera error:', err);
            let errorMessage = 'Camera access denied or not available.';

            if (err.name === 'NotAllowedError') {
                errorMessage = 'Camera access denied. Please allow camera access and try again.';
            } else if (err.name === 'NotFoundError') {
                errorMessage = 'No camera found on this device.';
            } else if (err.name === 'NotSupportedError') {
                errorMessage = 'Camera not supported on this device.';
            }

            showMessage('error', errorMessage);
            updateScannerStatus('Camera error: ' + errorMessage, 'error');
        }
    });

    stopCameraBtn.addEventListener('click', function () {
        stopScanning();
        showMessage('success', 'Camera stopped.');
    });

    debugCameraBtn.addEventListener('click', function () {
        if (debugInfo.style.display === 'none') {
            debugInfo.style.display = 'block';
            updateDebugInfo();
            debugInterval = setInterval(updateDebugInfo, 1000);
        } else {
            debugInfo.style.display = 'none';
            if (debugInterval) {
                clearInterval(debugInterval);
                debugInterval = null;
            }
        }
    });

    function startQRScanning() {
        if (!isScanning) return;

        console.log('Starting QR scanning...');
        let scanCount = 0;

        scanInterval = setInterval(() => {
            if (video.readyState === video.HAVE_ENOUGH_DATA && video.videoWidth > 0 && video.videoHeight > 0 && !isProcessing) {
                try {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;

                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);

                    scanCount++;
                    if (scanCount % 50 === 0) {
                        console.log(`QR Scanning... (${scanCount} scans completed)`);
                    }

                    const code = jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: "attemptBoth",
                        greyScaleWeights: {
                            red: 0.2126,
                            green: 0.7152,
                            blue: 0.0722,
                        }
                    });

                    if (code && code.data) {
                        console.log('QR Code detected:', code.data);

                        if (code.data.startsWith('CHURCH_ATTENDANCE:')) {
                            console.log('Valid church attendance QR code detected!');
                            isScanning = false;
                            updateScannerStatus('QR Code detected! Recording attendance...', 'processing');

                            document.getElementById('hidden-qr-data').value = code.data;
                            form.dispatchEvent(new Event('submit'));

                            setTimeout(() => {
                                if (!isProcessing) {
                                    isScanning = true;
                                    updateScannerStatus('Camera active - Point at QR code to automatically record attendance', 'scanning');
                                }
                            }, 3000);
                        } else {
                            console.log('Invalid QR code format:', code.data);
                            updateScannerStatus('Invalid QR code detected - Please scan a church attendance QR code', 'error');
                        }
                    }
                } catch (error) {
                    console.error('QR scanning error:', error);
                }
            } else {
                if (scanCount % 100 === 0) {
                    console.log('QR Scanning conditions not met:', {
                        videoReadyState: video.readyState,
                        videoWidth: video.videoWidth,
                        videoHeight: video.videoHeight,
                        isProcessing: isProcessing
                    });
                }
            }
        }, 200);
    }

    function stopScanning() {
        isScanning = false;
        if (scanInterval) {
            clearInterval(scanInterval);
            scanInterval = null;
        }

        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }

        video.style.display = 'none';
        startCameraBtn.style.display = 'inline-block';
        stopCameraBtn.style.display = 'none';
        debugCameraBtn.style.display = 'none';
        debugInfo.style.display = 'none';
        updateScannerStatus('Scanner stopped', 'stopped');
    }

    function updateScannerStatus(message, type) {
        if (scannerStatus) {
            scannerStatus.innerHTML = `<i class="fas fa-info-circle"></i> ${message}`;

            scannerStatus.className = 'text-white-50';
            if (type === 'success') {
                scannerStatus.className = 'text-success';
            } else if (type === 'error') {
                scannerStatus.className = 'text-warning';
            } else if (type === 'processing') {
                scannerStatus.className = 'text-info';
            } else if (type === 'scanning') {
                scannerStatus.className = 'text-white-50';
            } else if (type === 'stopped') {
                scannerStatus.className = 'text-muted';
            }
        }
    }

    function updateDebugInfo() {
        if (debugInfo) {
            const videoInfo = document.getElementById('video-info');
            const canvasInfo = document.getElementById('canvas-info');
            const scanInfo = document.getElementById('scan-info');

            if (videoInfo) {
                const readyState = ['HAVE_NOTHING', 'HAVE_METADATA', 'HAVE_CURRENT_DATA', 'HAVE_FUTURE_DATA', 'HAVE_ENOUGH_DATA'][video.readyState];
                videoInfo.textContent = video.readyState >= 2 ?
                    `Ready (${video.videoWidth}x${video.videoHeight}) - ${readyState}` : `Not ready - ${readyState}`;
            }

            if (canvasInfo) {
                canvasInfo.textContent = canvas.width > 0 ?
                    `Ready (${canvas.width}x${canvas.height})` : 'Not ready';
            }

            if (scanInfo) {
                scanInfo.textContent = isScanning ? 'Active' : 'Inactive';
            }

            const streamInfo = document.getElementById('stream-info');
            if (streamInfo) {
                streamInfo.textContent = stream ? (stream.active ? 'Active' : 'Inactive') : 'None';
            }

            console.log('Debug Info:', {
                videoReadyState: video.readyState,
                videoWidth: video.videoWidth,
                videoHeight: video.videoHeight,
                canvasWidth: canvas.width,
                canvasHeight: canvas.height,
                isScanning: isScanning,
                streamActive: stream ? stream.active : false
            });
        }
    }

    window.addEventListener('beforeunload', function () {
        stopScanning();
    });
});
