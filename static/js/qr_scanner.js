/**
 * QR Code Scanner functionality for church attendance
 */

class QRScanner {
    constructor() {
        this.video = null;
        this.canvas = null;
        this.context = null;
        this.stream = null;
        this.isScanning = false;
        this.scanInterval = null;
    }

    init() {
        this.video = document.getElementById('video');
        this.canvas = document.getElementById('canvas');

        if (this.canvas) {
            this.context = this.canvas.getContext('2d');
        }
    }

    async startCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'environment',
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            });

            if (this.video) {
                this.video.srcObject = this.stream;
                this.video.play();
                this.isScanning = true;

                // Start scanning for QR codes
                this.startScanning();

                return true;
            }
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showError('Camera access denied or not available.');
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.video) {
            this.video.srcObject = null;
        }

        this.isScanning = false;

        if (this.scanInterval) {
            clearInterval(this.scanInterval);
            this.scanInterval = null;
        }
    }

    startScanning() {
        if (!this.isScanning) return;

        this.scanInterval = setInterval(() => {
            this.scanFrame();
        }, 100); // Scan every 100ms
    }

    scanFrame() {
        if (!this.video || !this.canvas || !this.context) return;

        if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
            // Draw video frame to canvas
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);

            // Get image data
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);

            // Simple QR code detection (this is a basic implementation)
            // In a real application, you would use a proper QR code library like jsQR
            this.detectQRCode(imageData);
        }
    }

    detectQRCode(imageData) {
        // This is a simplified QR code detection
        // In a real implementation, you would use a library like jsQR
        // For now, we'll just look for patterns that might indicate a QR code

        // Placeholder for actual QR code detection
        // You can integrate jsQR library here:
        // const code = jsQR(imageData.data, imageData.width, imageData.height);
        // if (code) {
        //     this.onQRCodeDetected(code.data);
        // }
    }

    onQRCodeDetected(qrData) {
        if (this.isValidQRCode(qrData)) {
            this.stopCamera();
            this.fillQRInput(qrData);
            this.showSuccess('QR code detected!');
        }
    }

    isValidQRCode(qrData) {
        // Check if the QR code data matches our expected format
        return qrData && qrData.startsWith('CHURCH_ATTENDANCE:');
    }

    fillQRInput(qrData) {
        const qrInput = document.getElementById('qr-scanner-input');
        if (qrInput) {
            qrInput.value = qrData;
            qrInput.focus();
        }
    }

    showSuccess(message) {
        this.showMessage('success', message);
    }

    showError(message) {
        this.showMessage('error', message);
    }

    showMessage(type, message) {
        const messageContainer = document.getElementById('message-container');
        if (!messageContainer) return;

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

        // Remove message after 5 seconds
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// Initialize QR scanner when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    const qrScanner = new QRScanner();
    qrScanner.init();

    // Make scanner available globally
    window.qrScanner = qrScanner;

    // Handle camera button click
    const startCameraBtn = document.getElementById('start-camera');
    if (startCameraBtn) {
        startCameraBtn.addEventListener('click', async function () {
            const success = await qrScanner.startCamera();
            if (success) {
                startCameraBtn.style.display = 'none';
                if (qrScanner.video) {
                    qrScanner.video.style.display = 'block';
                }
            }
        });
    }

    // Handle form submission
    const form = document.getElementById('qr-scan-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();

            const formData = new FormData(form);
            const qrData = formData.get('qr_data');

            if (!qrData || !qrData.trim()) {
                qrScanner.showError('Please scan a QR code or enter the code manually.');
                return;
            }

            if (!qrScanner.isValidQRCode(qrData)) {
                qrScanner.showError('Invalid QR code format. Please scan a valid church attendance QR code.');
                return;
            }

            // Submit form via AJAX
            fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        qrScanner.showSuccess(data.message);
                        form.reset();
                        document.getElementById('qr-scanner-input').focus();

                        // Reload page to show updated attendance list
                        setTimeout(() => {
                            location.reload();
                        }, 2000);
                    } else {
                        qrScanner.showError(data.message);
                    }
                })
                .catch(error => {
                    qrScanner.showError('An error occurred while processing the QR code.');
                    console.error('Error:', error);
                });
        });
    }

    // Auto-focus on QR input
    const qrInput = document.getElementById('qr-scanner-input');
    if (qrInput) {
        qrInput.focus();
    }
});
