/**
 * Career Lab Consulting - Camera Management
 * Handles webcam lifecycle: init, stop, state tracking
 */

let cameraStream = null;
let cameraActive = false;

/**
 * Initialize the camera and attach to a video element
 * @param {HTMLVideoElement} videoElement - The video element to display the feed
 * @returns {Promise<boolean>} - Whether camera was successfully started
 */
async function initCamera(videoElement) {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoElement.srcObject = cameraStream;
        await videoElement.play();
        cameraActive = true;

        // Monitor if camera stream is interrupted
        cameraStream.getVideoTracks().forEach(track => {
            track.onended = function() {
                cameraActive = false;
                showCameraWarning('Camera has been disabled! Please re-enable your camera to continue the exam.');
            };
            track.onmute = function() {
                cameraActive = false;
                showCameraWarning('Camera has been muted! Please ensure your camera is active.');
            };
            track.onunmute = function() {
                cameraActive = true;
                hideCameraWarning();
            };
        });

        return true;
    } catch (error) {
        console.error('Camera initialization failed:', error);
        cameraActive = false;
        return false;
    }
}

/**
 * Stop the camera stream and release resources
 */
function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
        cameraActive = false;
    }
}

/**
 * Check if camera is currently active
 * @returns {boolean}
 */
function isCameraActive() {
    return cameraActive && cameraStream !== null;
}

/**
 * Show camera warning overlay
 * @param {string} message - Warning message to display
 */
function showCameraWarning(message) {
    let overlay = document.getElementById('camera-warning-overlay');
    if (overlay) {
        const msgEl = overlay.querySelector('.camera-warning-text');
        if (msgEl) msgEl.textContent = message;
        overlay.style.display = 'flex';
    }
}

/**
 * Hide camera warning overlay
 */
function hideCameraWarning() {
    let overlay = document.getElementById('camera-warning-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}
