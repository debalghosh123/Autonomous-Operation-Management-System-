/**
 * Career Lab Consulting - Head Pose Gaze Detection
 * Monitors gaze direction using head pose estimation from face-api.js 68-point landmarks.
 * 
 * WHY HEAD POSE:
 * The 68-point face landmark model provides eye CONTOUR outlines (the shape of the eye opening),
 * NOT the iris/pupil center. The centroid of 6 eye contour points is always approximately the
 * geometric center of the eye opening regardless of where the person is actually looking.
 * Instead, we use head rotation (yaw/pitch) estimated from key facial landmarks as a proxy
 * for gaze direction -- when someone looks away from a screen, their head typically turns too.
 *
 * KEY LANDMARKS USED:
 * - Point 30: Nose tip
 * - Point 8: Chin
 * - Point 36: Left eye outer corner
 * - Point 45: Right eye outer corner
 * - Point 48: Left mouth corner
 * - Point 54: Right mouth corner
 */

let eyeDetectionInterval = null;
let gazeAwayStartTime = null;
let warningCount = 0;
let faceApiLoaded = false;
let landmarksLoaded = false;
let detectionVideo = null;
let warningShownForCurrentDistraction = false;
let gazeAtScreenFrames = 0;
let debugLogCounter = 0;

const GAZE_AWAY_THRESHOLD = 2000; // 2 seconds of looking away before warning
const MAX_WARNINGS = 5;
const DETECTION_INTERVAL = 500; // Check every 500ms
const GAZE_RETURN_FRAMES_REQUIRED = 3; // 3 consecutive "at screen" frames (1.5s) before resetting
const DEBUG_LOG_INTERVAL = 6; // Log debug info every 6 frames (3 seconds at 500ms interval)

// Head pose thresholds for "looking away"
const YAW_THRESHOLD_LOW = 0.32;   // Head turned right (nose closer to right eye)
const YAW_THRESHOLD_HIGH = 0.68;  // Head turned left (nose closer to left eye)
const PITCH_THRESHOLD_LOW = 0.30; // Head tilted up (nose higher relative to face height)
const PITCH_THRESHOLD_HIGH = 0.65; // Head tilted down (nose lower relative to face height)

// Face bounding box position thresholds (face shifted far in frame)
const FACE_BOX_X_LOW = 0.25;
const FACE_BOX_X_HIGH = 0.75;

/**
 * Initialize eye/gaze detection with face-api.js landmarks
 * @param {HTMLVideoElement} videoElement - The video element with camera feed
 */
async function initEyeDetection(videoElement) {
    detectionVideo = videoElement;

    // Try to load face-api.js models from CDN
    try {
        if (typeof faceapi !== 'undefined') {
            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';

            // Load TinyFaceDetector and face landmarks model
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL)
            ]);

            faceApiLoaded = true;
            landmarksLoaded = true;
            console.log('[EyeDetection] face-api.js TinyFaceDetector + FaceLandmark68TinyNet loaded successfully');
            console.log('[EyeDetection] Using HEAD POSE estimation for gaze detection');
        }
    } catch (e) {
        console.warn('[EyeDetection] Landmark models not available:', e.message);
        // Try loading just face detector as fallback
        try {
            if (typeof faceapi !== 'undefined') {
                const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';
                await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
                faceApiLoaded = true;
                landmarksLoaded = false;
                console.log('[EyeDetection] TinyFaceDetector loaded (without landmarks, using face-box fallback)');
            }
        } catch (e2) {
            console.warn('[EyeDetection] face-api.js not available, gaze detection disabled:', e2.message);
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
 * State machine with hysteresis:
 *   LOOKING_AT_SCREEN -> gaze leaves screen -> start timer, reset gazeAtScreenFrames
 *   GAZE_AWAY_DETECTED -> threshold elapsed -> trigger ONE warning
 *   WARNING_SHOWN -> still looking away -> DO NOTHING (no repeated warnings)
 *   WARNING_SHOWN / GAZE_AWAY_DETECTED -> gaze returns for 3+ consecutive frames -> reset
 */
function startDetection() {
    gazeAwayStartTime = null;
    warningShownForCurrentDistraction = false;
    gazeAtScreenFrames = 0;
    debugLogCounter = 0;

    eyeDetectionInterval = setInterval(async () => {
        if (!detectionVideo || detectionVideo.paused || detectionVideo.ended) return;

        const gazeResult = await detectGaze();

        if (gazeResult.lookingAway) {
            // Candidate is looking away from the screen
            gazeAtScreenFrames = 0;

            if (gazeAwayStartTime === null) {
                gazeAwayStartTime = Date.now();
            } else if (!warningShownForCurrentDistraction) {
                const elapsed = Date.now() - gazeAwayStartTime;
                if (elapsed >= GAZE_AWAY_THRESHOLD) {
                    triggerEyeWarning();
                    warningShownForCurrentDistraction = true;
                }
            }
            // If warningShownForCurrentDistraction is true and still looking away, do nothing
        } else {
            // Candidate appears to be looking at screen
            gazeAtScreenFrames++;

            // Only reset distraction state after sustained looking-at-screen (hysteresis)
            if (gazeAtScreenFrames >= GAZE_RETURN_FRAMES_REQUIRED) {
                gazeAwayStartTime = null;
                warningShownForCurrentDistraction = false;
            }
        }
    }, DETECTION_INTERVAL);
}

/**
 * Detect gaze direction using head pose estimation from face landmarks.
 * Falls back to face bounding box position if landmarks are not available.
 * @returns {Promise<{lookingAway: boolean, direction: string|null}>}
 */
async function detectGaze() {
    // PRIMARY: Head pose estimation using 68-point landmarks
    if (faceApiLoaded && landmarksLoaded && typeof faceapi !== 'undefined') {
        try {
            const detection = await faceapi
                .detectSingleFace(detectionVideo, new faceapi.TinyFaceDetectorOptions({
                    inputSize: 224,
                    scoreThreshold: 0.4
                }))
                .withFaceLandmarks(true); // true = use tiny model

            if (!detection) {
                // No face detected - face may be turned too far or out of frame
                return { lookingAway: true, direction: 'no_face' };
            }

            // Get all 68 landmark positions
            const landmarks = detection.landmarks;
            const positions = landmarks.positions;

            // Calculate head pose (yaw and pitch)
            const headPose = calculateHeadPose(positions);

            // SECONDARY: Check face bounding box position in frame
            const box = detection.detection.box;
            const videoWidth = detectionVideo.videoWidth || detectionVideo.width;
            const videoHeight = detectionVideo.videoHeight || detectionVideo.height;
            const faceCenterX = (box.x + box.width / 2) / videoWidth;

            // Debug logging every few seconds
            debugLogCounter++;
            if (debugLogCounter >= DEBUG_LOG_INTERVAL) {
                console.log(`[EyeDetection] yawRatio=${headPose.yawRatio.toFixed(3)}, pitchRatio=${headPose.pitchRatio.toFixed(3)}, faceCenterX=${faceCenterX.toFixed(3)}`);
                debugLogCounter = 0;
            }

            // Determine if looking away
            let lookingAway = false;
            let direction = 'center';

            // Check yaw (left-right head rotation)
            if (headPose.yawRatio < YAW_THRESHOLD_LOW) {
                lookingAway = true;
                direction = 'turned_right';
            } else if (headPose.yawRatio > YAW_THRESHOLD_HIGH) {
                lookingAway = true;
                direction = 'turned_left';
            }

            // Check pitch (up-down head tilt)
            if (headPose.pitchRatio < PITCH_THRESHOLD_LOW) {
                lookingAway = true;
                direction = direction === 'center' ? 'looking_up' : direction + '_up';
            } else if (headPose.pitchRatio > PITCH_THRESHOLD_HIGH) {
                lookingAway = true;
                direction = direction === 'center' ? 'looking_down' : direction + '_down';
            }

            // Check face position in frame (head physically shifted)
            if (faceCenterX < FACE_BOX_X_LOW || faceCenterX > FACE_BOX_X_HIGH) {
                lookingAway = true;
                direction = direction === 'center' ? 'off_center' : direction + '_shifted';
            }

            return { lookingAway, direction };
        } catch (e) {
            console.warn('[EyeDetection] Head pose detection error:', e.message);
            // On error, don't penalize the candidate
            return { lookingAway: false, direction: null };
        }
    }

    // FALLBACK: Face bounding box position only (no landmarks available)
    if (faceApiLoaded && typeof faceapi !== 'undefined') {
        try {
            const detection = await faceapi.detectSingleFace(
                detectionVideo,
                new faceapi.TinyFaceDetectorOptions({ inputSize: 160, scoreThreshold: 0.3 })
            );

            if (!detection) {
                return { lookingAway: true, direction: 'no_face' };
            }

            const box = detection.box;
            const videoWidth = detectionVideo.videoWidth || detectionVideo.width;
            const videoHeight = detectionVideo.videoHeight || detectionVideo.height;

            const faceCenterX = (box.x + box.width / 2) / videoWidth;
            const faceCenterY = (box.y + box.height / 2) / videoHeight;

            // Debug logging
            debugLogCounter++;
            if (debugLogCounter >= DEBUG_LOG_INTERVAL) {
                console.log(`[EyeDetection] fallback mode - faceCenterX=${faceCenterX.toFixed(3)}, faceCenterY=${faceCenterY.toFixed(3)}`);
                debugLogCounter = 0;
            }

            // Face significantly off-center means the person has moved/turned away
            const lookingAway = faceCenterX < FACE_BOX_X_LOW || faceCenterX > FACE_BOX_X_HIGH ||
                                faceCenterY < 0.15 || faceCenterY > 0.85;

            return { lookingAway, direction: lookingAway ? 'off_center' : 'center' };
        } catch (e) {
            return { lookingAway: false, direction: null };
        }
    }

    // No detection available at all - don't penalize
    return { lookingAway: false, direction: null };
}

/**
 * Calculate head pose (yaw and pitch) from 68-point face landmarks.
 *
 * YAW (left-right head rotation):
 *   Compare distances from nose tip to each eye corner.
 *   If face is turned left, nose is closer to left eye corner, farther from right.
 *   If face is turned right, nose is closer to right eye corner, farther from left.
 *   Ratio: 0.5 = facing forward, <0.32 = turned right, >0.68 = turned left.
 *
 * PITCH (up-down head tilt):
 *   Use nose tip position relative to the eye-line and chin.
 *   The nose normally sits at about 40-60% of the way between eye-line and chin.
 *   Looking down: nose appears lower (ratio > 0.65).
 *   Looking up: nose appears higher (ratio < 0.30).
 *
 * @param {Array} positions - Array of 68 landmark point objects with .x and .y
 * @returns {{yawRatio: number, pitchRatio: number}}
 */
function calculateHeadPose(positions) {
    // Key landmarks
    const noseTip = positions[30];
    const chin = positions[8];
    const leftEyeOuterCorner = positions[36];
    const rightEyeOuterCorner = positions[45];

    // --- YAW ESTIMATION ---
    // Distance from nose tip to each eye outer corner (horizontal distance)
    const leftDist = Math.abs(noseTip.x - leftEyeOuterCorner.x);
    const rightDist = Math.abs(noseTip.x - rightEyeOuterCorner.x);

    // Ratio: 0.5 means nose is equidistant from both eyes (facing forward)
    // < 0.5 means nose is closer to left eye (turned right in the image)
    // > 0.5 means nose is closer to right eye (turned left in the image)
    let yawRatio = 0.5;
    if (leftDist + rightDist > 0) {
        yawRatio = leftDist / (leftDist + rightDist);
    }

    // --- PITCH ESTIMATION ---
    // Eye line Y is the average Y of both eye outer corners
    const eyeLineY = (leftEyeOuterCorner.y + rightEyeOuterCorner.y) / 2;
    const chinY = chin.y;
    const noseY = noseTip.y;

    // Face height from eye-line to chin
    const faceHeight = chinY - eyeLineY;

    // Where the nose sits relative to the eye-line to chin range
    // Normal forward-facing: approximately 0.4-0.6
    // Looking down: nose lower, ratio > 0.65
    // Looking up: nose higher, ratio < 0.30
    let pitchRatio = 0.5;
    if (faceHeight > 0) {
        pitchRatio = (noseY - eyeLineY) / faceHeight;
        // Clamp to reasonable range
        pitchRatio = Math.max(0, Math.min(1, pitchRatio));
    }

    return { yawRatio, pitchRatio };
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
