/**
 * Career Lab Consulting - Eye Contact Detection
 * Monitors face presence using face-api.js
 * Shows warnings when face is not detected for extended periods
 */

let eyeDetectionInterval = null;
let faceNotDetectedSince = null;
let warningCount = 0;
let faceApiLoaded = false;
let detectionCanvas = null;
let detectionVideo = null;
const FACE_ABSENCE_THRESHOLD = 3000; // 3 seconds
const MAX_WARNINGS = 5;
const DETECTION_INTERVAL = 1000; // Check every 1 second

/**
 * Initialize eye detection with face-api.js
 * @param {HTMLVideoElement} videoElement - The video element with camera feed
 */
async function initEyeDetection(videoElement) {
    detectionVideo = videoElement;

    // Create a hidden canvas for frame analysis
    detectionCanvas = document.createElement('canvas');
    detectionCanvas.width = 160;
    detectionCanvas.height = 120;

    // Try to load face-api.js models
    try {
        if (typeof faceapi !== 'undefined') {
            await faceapi.nets.tinyFaceDetector.loadFromUri('/static/models');
            faceApiLoaded = true;
        }
    } catch (e) {
        console.warn('face-api.js models not available, using fallback detection');
        faceApiLoaded = false;
    }

    // Start periodic detection
    startDetection();
}

/**
 * Start the face detection loop
 */
function startDetection() {
    faceNotDetectedSince = null;
    eyeDetectionInterval = setInterval(async () => {
        if (!detectionVideo || detectionVideo.paused || detectionVideo.ended) return;

        const facePresent = await detectFace();

        if (!facePresent) {
            if (faceNotDetectedSince === null) {
                faceNotDetectedSince = Date.now();
            } else {
                const elapsed = Date.now() - faceNotDetectedSince;
                if (elapsed >= FACE_ABSENCE_THRESHOLD) {
                    triggerEyeWarning();
                    faceNotDetectedSince = Date.now(); // Reset for next warning cycle
                }
            }
        } else {
            faceNotDetectedSince = null;
            hideEyeWarning();
        }
    }, DETECTION_INTERVAL);
}

/**
 * Detect face presence in the video frame
 * Uses face-api.js if available, otherwise uses motion/brightness heuristic
 * @returns {Promise<boolean>} - Whether a face is detected
 */
async function detectFace() {
    if (faceApiLoaded && typeof faceapi !== 'undefined') {
        try {
            const detections = await faceapi.detectAllFaces(
                detectionVideo,
                new faceapi.TinyFaceDetectorOptions({ inputSize: 160, scoreThreshold: 0.3 })
            );
            return detections.length > 0;
        } catch (e) {
            return useFallbackDetection();
        }
    }
    return useFallbackDetection();
}

/**
 * Fallback face detection using pixel analysis
 * Checks for significant visual content in the video frame
 * (skin-tone pixel detection heuristic)
 * @returns {boolean}
 */
function useFallbackDetection() {
    try {
        const ctx = detectionCanvas.getContext('2d');
        ctx.drawImage(detectionVideo, 0, 0, detectionCanvas.width, detectionCanvas.height);
        const imageData = ctx.getImageData(0, 0, detectionCanvas.width, detectionCanvas.height);
        const data = imageData.data;

        let skinPixelCount = 0;
        const totalPixels = data.length / 4;

        // Simple skin-tone detection (works for various skin tones)
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            // Broad skin-tone detection covering multiple skin tones
            if (r > 60 && g > 40 && b > 20 &&
                r > g && r > b &&
                (r - g) > 10 &&
                Math.abs(r - g) < 150) {
                skinPixelCount++;
            }
        }

        // If more than 5% of pixels are skin-tone, face is likely present
        const skinRatio = skinPixelCount / totalPixels;
        return skinRatio > 0.05;
    } catch (e) {
        // If canvas analysis fails, assume face is present (avoid false warnings)
        return true;
    }
}

/**
 * Trigger an eye contact warning
 */
function triggerEyeWarning() {
    warningCount++;

    const warningOverlay = document.getElementById('eye-warning-overlay');
    const warningText = document.getElementById('eye-warning-text');
    const warningCounter = document.getElementById('eye-warning-count');

    if (warningOverlay) {
        warningOverlay.style.display = 'flex';

        if (warningCount >= MAX_WARNINGS) {
            if (warningText) warningText.textContent = 'CRITICAL: Multiple eye contact violations detected! Your exam may be invalidated.';
        } else if (warningCount >= 3) {
            if (warningText) warningText.textContent = 'WARNING: Please maintain eye contact with the screen. Too many violations may terminate your exam.';
        } else {
            if (warningText) warningText.textContent = 'Please look at the screen. Maintain eye contact during the exam.';
        }

        if (warningCounter) warningCounter.textContent = `Warnings: ${warningCount}/${MAX_WARNINGS}`;

        // Auto-hide after 3 seconds
        setTimeout(() => {
            hideEyeWarning();
        }, 3000);
    }

    // Show notification
    showEyeNotification();
}

/**
 * Show a slide-in notification for eye contact warning
 */
function showEyeNotification() {
    let notification = document.getElementById('eye-notification');
    if (notification) {
        notification.textContent = `Eye Contact Warning (${warningCount}/${MAX_WARNINGS})`;
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }
}

/**
 * Hide the eye warning overlay
 */
function hideEyeWarning() {
    const warningOverlay = document.getElementById('eye-warning-overlay');
    if (warningOverlay) {
        warningOverlay.style.display = 'none';
    }
}

/**
 * Stop eye detection monitoring
 */
function stopEyeDetection() {
    if (eyeDetectionInterval) {
        clearInterval(eyeDetectionInterval);
        eyeDetectionInterval = null;
    }
}

/**
 * Get current warning count
 * @returns {number}
 */
function getWarningCount() {
    return warningCount;
}
