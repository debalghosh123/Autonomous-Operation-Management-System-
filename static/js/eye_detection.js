/**
 * Career Lab Consulting - Eye Gaze Detection
 * Monitors gaze direction using face-api.js 68-point face landmarks.
 * Detects when the candidate's eyes look away from the screen (questions panel).
 * Only triggers warnings when gaze is off-center, NOT when face is simply present.
 */

let eyeDetectionInterval = null;
let gazeAwayStartTime = null;
let warningCount = 0;
let faceApiLoaded = false;
let landmarksLoaded = false;
let detectionVideo = null;
let warningShownForCurrentDistraction = false; // Prevents repeated warnings for a single distraction event
const GAZE_AWAY_THRESHOLD = 2000; // 2 seconds of looking away before warning (brief threshold to avoid flickers)
const MAX_WARNINGS = 5;
const DETECTION_INTERVAL = 500; // Check every 500ms for smoother detection

// Gaze thresholds - how far off-center the gaze must be to count as "looking away"
// These are ratios (0 = looking fully left/up, 0.5 = center, 1 = fully right/down)
const GAZE_HORIZONTAL_THRESHOLD = 0.28; // If horizontal ratio < 0.28 or > 0.72, looking away
const GAZE_VERTICAL_THRESHOLD = 0.25;   // If vertical ratio < 0.25 or > 0.75, looking away

/**
 * Initialize eye gaze detection with face-api.js landmarks
 * @param {HTMLVideoElement} videoElement - The video element with camera feed
 */
async function initEyeDetection(videoElement) {
    detectionVideo = videoElement;

    // Try to load face-api.js models from CDN
    try {
        if (typeof faceapi !== 'undefined') {
            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';

            // Load both TinyFaceDetector and face landmarks model
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL)
            ]);

            faceApiLoaded = true;
            landmarksLoaded = true;
            console.log('face-api.js TinyFaceDetector + FaceLandmark68TinyNet loaded successfully');
        }
    } catch (e) {
        console.warn('face-api.js landmark models not available:', e.message);
        // Try loading just face detector as fallback
        try {
            if (typeof faceapi !== 'undefined') {
                const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';
                await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
                faceApiLoaded = true;
                landmarksLoaded = false;
                console.log('face-api.js TinyFaceDetector loaded (without landmarks)');
            }
        } catch (e2) {
            console.warn('face-api.js not available at all, gaze detection disabled:', e2.message);
            faceApiLoaded = false;
            landmarksLoaded = false;
        }
    }

    // Start periodic detection
    startDetection();
}

/**
 * Start the gaze detection loop
 *
 * State machine:
 *   LOOKING_AT_SCREEN -> gaze leaves screen -> start timer (GAZE_AWAY_DETECTED)
 *   GAZE_AWAY_DETECTED -> threshold elapsed -> trigger ONE warning (WARNING_SHOWN)
 *   WARNING_SHOWN -> still looking away -> DO NOTHING (no repeated warnings)
 *   WARNING_SHOWN / GAZE_AWAY_DETECTED -> gaze returns -> reset to LOOKING_AT_SCREEN
 */
function startDetection() {
    gazeAwayStartTime = null;
    warningShownForCurrentDistraction = false;
    eyeDetectionInterval = setInterval(async () => {
        if (!detectionVideo || detectionVideo.paused || detectionVideo.ended) return;

        const gazeResult = await detectGaze();

        if (gazeResult.lookingAway) {
            // Eyes are looking away from the screen
            if (gazeAwayStartTime === null) {
                gazeAwayStartTime = Date.now();
            } else if (!warningShownForCurrentDistraction) {
                // Only trigger a warning if we haven't already shown one for this distraction
                const elapsed = Date.now() - gazeAwayStartTime;
                if (elapsed >= GAZE_AWAY_THRESHOLD) {
                    triggerEyeWarning();
                    warningShownForCurrentDistraction = true; // Mark: warning shown, do not repeat
                }
            }
            // If warningShownForCurrentDistraction is true and still looking away, do nothing
        } else {
            // Eyes are back on screen - reset state for the next distraction event
            gazeAwayStartTime = null;
            warningShownForCurrentDistraction = false;
        }
    }, DETECTION_INTERVAL);
}

/**
 * Detect gaze direction using face-api.js landmarks
 * Returns whether the candidate is looking away from the screen
 * @returns {Promise<{lookingAway: boolean, direction: string|null}>}
 */
async function detectGaze() {
    // If we have landmarks model, use gaze direction detection
    if (faceApiLoaded && landmarksLoaded && typeof faceapi !== 'undefined') {
        try {
            const detection = await faceapi
                .detectSingleFace(detectionVideo, new faceapi.TinyFaceDetectorOptions({
                    inputSize: 224,
                    scoreThreshold: 0.4
                }))
                .withFaceLandmarks(true); // true = use tiny model

            if (!detection) {
                // No face detected - could be looking far away or face out of frame
                // Treat as looking away only if it persists (handled by threshold timer)
                return { lookingAway: true, direction: 'no_face' };
            }

            // Extract eye landmarks from the 68-point model
            const landmarks = detection.landmarks;
            const positions = landmarks.positions;

            // Left eye: points 36-41
            const leftEye = positions.slice(36, 42);
            // Right eye: points 42-47
            const rightEye = positions.slice(42, 48);

            // Calculate gaze direction for each eye
            const leftGaze = calculateEyeGaze(leftEye);
            const rightGaze = calculateEyeGaze(rightEye);

            // Average the gaze of both eyes
            const avgHorizontalRatio = (leftGaze.horizontalRatio + rightGaze.horizontalRatio) / 2;
            const avgVerticalRatio = (leftGaze.verticalRatio + rightGaze.verticalRatio) / 2;

            // Determine if looking away from center
            let lookingAway = false;
            let direction = 'center';

            if (avgHorizontalRatio < GAZE_HORIZONTAL_THRESHOLD) {
                lookingAway = true;
                direction = 'left';
            } else if (avgHorizontalRatio > (1 - GAZE_HORIZONTAL_THRESHOLD)) {
                lookingAway = true;
                direction = 'right';
            }

            if (avgVerticalRatio < GAZE_VERTICAL_THRESHOLD) {
                lookingAway = true;
                direction = direction === 'center' ? 'up' : direction + '_up';
            } else if (avgVerticalRatio > (1 - GAZE_VERTICAL_THRESHOLD)) {
                lookingAway = true;
                direction = direction === 'center' ? 'down' : direction + '_down';
            }

            return { lookingAway, direction };
        } catch (e) {
            console.warn('Gaze detection error:', e.message);
            // On error, don't penalize the candidate
            return { lookingAway: false, direction: null };
        }
    }

    // Fallback: if only face detector is available (no landmarks)
    if (faceApiLoaded && typeof faceapi !== 'undefined') {
        try {
            const detection = await faceapi.detectSingleFace(
                detectionVideo,
                new faceapi.TinyFaceDetectorOptions({ inputSize: 160, scoreThreshold: 0.3 })
            );

            if (!detection) {
                return { lookingAway: true, direction: 'no_face' };
            }

            // Without landmarks, we can use face box position relative to video center
            // If the face box is significantly off-center, the person may be looking away
            const box = detection.box;
            const videoWidth = detectionVideo.videoWidth || detectionVideo.width;
            const videoHeight = detectionVideo.videoHeight || detectionVideo.height;

            const faceCenterX = box.x + box.width / 2;
            const faceCenterY = box.y + box.height / 2;

            const normalizedX = faceCenterX / videoWidth;
            const normalizedY = faceCenterY / videoHeight;

            // Face is present and roughly centered - assume looking at screen
            // Only flag as looking away if face is drastically off-center
            const lookingAway = normalizedX < 0.2 || normalizedX > 0.8 ||
                                normalizedY < 0.15 || normalizedY > 0.85;

            return { lookingAway, direction: lookingAway ? 'off_center' : 'center' };
        } catch (e) {
            return { lookingAway: false, direction: null };
        }
    }

    // No detection available at all - don't penalize
    return { lookingAway: false, direction: null };
}

/**
 * Calculate gaze direction for a single eye based on landmark positions
 * Uses the position of the eye center (approximating iris) relative to eye boundaries
 *
 * Eye landmarks (6 points per eye):
 * - Point 0: left corner (outer)
 * - Point 1: top-left
 * - Point 2: top-right
 * - Point 3: right corner (inner)
 * - Point 4: bottom-right
 * - Point 5: bottom-left
 *
 * The iris/pupil center is estimated as the centroid of the eye region.
 * Gaze is determined by where this center sits relative to the eye boundaries.
 *
 * @param {Array} eyePoints - Array of 6 landmark points for one eye
 * @returns {{horizontalRatio: number, verticalRatio: number}}
 */
function calculateEyeGaze(eyePoints) {
    // Get eye boundary extremes
    const leftCorner = eyePoints[0];  // Outer corner
    const rightCorner = eyePoints[3]; // Inner corner

    // Top boundary (average of top points)
    const topY = (eyePoints[1].y + eyePoints[2].y) / 2;
    // Bottom boundary (average of bottom points)
    const bottomY = (eyePoints[4].y + eyePoints[5].y) / 2;

    // Eye center (centroid of all 6 points) - approximates iris center
    // The centroid of the visible eye region shifts toward where the iris is looking
    const eyeCenterX = eyePoints.reduce((sum, p) => sum + p.x, 0) / eyePoints.length;
    const eyeCenterY = eyePoints.reduce((sum, p) => sum + p.y, 0) / eyePoints.length;

    // Calculate horizontal ratio: 0 = looking fully left, 0.5 = center, 1 = fully right
    const eyeWidth = rightCorner.x - leftCorner.x;
    let horizontalRatio = 0.5; // default center
    if (eyeWidth > 0) {
        horizontalRatio = (eyeCenterX - leftCorner.x) / eyeWidth;
        // Clamp to [0, 1]
        horizontalRatio = Math.max(0, Math.min(1, horizontalRatio));
    }

    // Calculate vertical ratio: 0 = looking up, 0.5 = center, 1 = looking down
    const eyeHeight = bottomY - topY;
    let verticalRatio = 0.5; // default center
    if (eyeHeight > 0) {
        verticalRatio = (eyeCenterY - topY) / eyeHeight;
        // Clamp to [0, 1]
        verticalRatio = Math.max(0, Math.min(1, verticalRatio));
    }

    return { horizontalRatio, verticalRatio };
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
            if (warningText) warningText.textContent = 'CRITICAL: Multiple gaze violations detected! Your exam may be invalidated.';
        } else if (warningCount >= 3) {
            if (warningText) warningText.textContent = 'WARNING: Please keep your eyes on the screen. Too many violations may terminate your exam.';
        } else {
            if (warningText) warningText.textContent = 'Please look at the screen. Maintain eye contact with the questions during the exam.';
        }

        if (warningCounter) warningCounter.textContent = `Warnings: ${warningCount}/${MAX_WARNINGS}`;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideEyeWarning();
        }, 5000);
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
