/**
 * Career Lab Consulting - Multi-Signal Proctoring System
 * 
 * Detects when a candidate is distracted using multiple independent signals:
 * 
 * Signal 1: Tab Visibility Change
 *   - document.visibilitychange: detects tab switches (immediate warning)
 * 
 * Signal 2: Window Blur
 *   - window.blur: detects alt-tab, clicking other windows (immediate warning)
 * 
 * Signal 3: Mouse/Pointer Leaving the Browser Window
 *   - document.mouseleave: mouse left the browser
 *   - Warning after 2 seconds sustained outside
 * 
 * Signal 4: Head Pose Estimation (face-api.js)
 *   - Uses 68-point landmarks to estimate head yaw/pitch
 *   - Warning after 2 seconds of head turned away
 *   - Resets after firing so next event can trigger again
 * 
 * ARCHITECTURE: Global cooldown approach
 *   - ONE global cooldown (1.5 seconds between any warnings)
 *   - Every distraction event fires a warning as long as cooldown has elapsed
 *   - No per-signal state flags -- simpler and more reliable
 *   - Navigation grace period suppresses false blur/focus events during question changes
 *   - MAX_WARNINGS = 5 with same UI overlays and 5-second auto-hide
 */

// ========================
// Configuration
// ========================
const MAX_WARNINGS = 5;
const WARNING_COOLDOWN = 1500;      // 1.5 seconds between warnings (prevents double-fire only)
const WARNING_AUTO_HIDE_MS = 5000;  // Auto-hide warning overlay after 5 seconds
const MOUSE_LEAVE_DELAY = 2000;     // 2 seconds before mouse-leave triggers
const HEAD_POSE_DELAY = 2000;       // 2 seconds before head pose triggers
const DETECTION_INTERVAL = 500;     // Head pose check every 500ms
const NAVIGATION_GRACE_MS = 500;    // Suppress blur/focus events for 500ms during navigation

// Head pose thresholds
const YAW_THRESHOLD_LOW = 0.32;
const YAW_THRESHOLD_HIGH = 0.68;
const PITCH_THRESHOLD_LOW = 0.30;
const PITCH_THRESHOLD_HIGH = 0.65;
const FACE_BOX_X_LOW = 0.25;
const FACE_BOX_X_HIGH = 0.75;

// ========================
// State
// ========================
let warningCount = 0;
let lastWarningTime = 0;
let detectionVideo = null;
let eyeDetectionInterval = null;

// Navigation grace period state
let navigationInProgress = false;

// Mouse leave state
let mouseLeaveTimer = null;

// Head pose state
let faceApiLoaded = false;
let landmarksLoaded = false;
let headPoseAwayStartTime = null;

// Debug logging
let debugLogCounter = 0;
const DEBUG_LOG_INTERVAL = 6;

// ========================
// Global Cooldown
// ========================

/**
 * Check if enough time has passed since the last warning
 */
function canShowWarning() {
    return (Date.now() - lastWarningTime) >= WARNING_COOLDOWN;
}

// ========================
// Navigation Grace Period
// ========================

/**
 * Called by exam.js when question navigation occurs.
 * Suppresses blur/focus events for a short grace period to prevent
 * false warnings from DOM focus shifts during navigation.
 */
function onQuestionNavigating() {
    navigationInProgress = true;
    setTimeout(() => { navigationInProgress = false; }, NAVIGATION_GRACE_MS);
}

// ========================
// Initialization
// ========================

/**
 * Initialize multi-signal eye/gaze detection
 * @param {HTMLVideoElement} videoElement - The video element with camera feed
 */
async function initEyeDetection(videoElement) {
    detectionVideo = videoElement;
    
    console.log('[Proctoring] Initializing multi-signal proctoring system...');
    
    // Initialize all signals
    initTabVisibilityDetection();
    initWindowBlurDetection();
    initMouseLeaveDetection();
    await initHeadPoseDetection();
    
    console.log('[Proctoring] All detection signals active');
}

// ========================
// Signal 1: Tab Visibility Change
// ========================

function initTabVisibilityDetection() {
    document.addEventListener('visibilitychange', () => {
        if (navigationInProgress) return;
        if (document.hidden) {
            console.log('[Proctoring] Tab switch detected (visibilitychange)');
            triggerEyeWarning('You switched tabs. Please stay focused on the exam.');
        }
    });

    console.log('[Proctoring] Signal 1 (Tab Visibility) initialized');
}

// ========================
// Signal 2: Window Blur
// ========================

function initWindowBlurDetection() {
    window.addEventListener('blur', () => {
        if (navigationInProgress) return;
        console.log('[Proctoring] Window blur detected');
        triggerEyeWarning('You left the exam window. Please stay focused on the exam.');
    });

    console.log('[Proctoring] Signal 2 (Window Blur) initialized');
}

// ========================
// Signal 3: Mouse Leaving Browser
// ========================

function initMouseLeaveDetection() {
    document.addEventListener('mouseleave', () => {
        mouseLeaveTimer = setTimeout(() => {
            console.log('[Proctoring] Mouse left browser window for 2+ seconds');
            triggerEyeWarning('Your cursor left the exam window. Please keep your focus on the exam.');
        }, MOUSE_LEAVE_DELAY);
    });

    document.addEventListener('mouseenter', () => {
        if (mouseLeaveTimer) {
            clearTimeout(mouseLeaveTimer);
            mouseLeaveTimer = null;
        }
    });

    console.log('[Proctoring] Signal 3 (Mouse Leave) initialized');
}

// ========================
// Signal 4: Head Pose Detection
// ========================

async function initHeadPoseDetection() {
    if (typeof faceapi === 'undefined') {
        console.warn('[Proctoring] face-api.js not available - skipping head pose signal');
        return;
    }

    try {
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';

        await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
            faceapi.nets.faceLandmark68TinyNet.loadFromUri(MODEL_URL)
        ]);

        faceApiLoaded = true;
        landmarksLoaded = true;
        console.log('[Proctoring] Signal 4 (Head Pose) initialized with face-api.js landmarks');
    } catch (e) {
        console.warn('[Proctoring] face-api.js model loading failed:', e.message);
        try {
            const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';
            await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
            faceApiLoaded = true;
            landmarksLoaded = false;
            console.log('[Proctoring] Signal 4 (Head Pose) initialized with face box fallback only');
        } catch (e2) {
            console.warn('[Proctoring] face-api.js fully unavailable:', e2.message);
            faceApiLoaded = false;
            landmarksLoaded = false;
        }
    }

    // Start head pose detection loop
    startHeadPoseDetection();
}

function startHeadPoseDetection() {
    headPoseAwayStartTime = null;

    eyeDetectionInterval = setInterval(async () => {
        if (!detectionVideo || detectionVideo.paused || detectionVideo.ended) return;
        if (!faceApiLoaded) return;

        const gazeResult = await detectHeadPose();

        if (gazeResult.lookingAway) {
            if (headPoseAwayStartTime === null) {
                headPoseAwayStartTime = Date.now();
            } else {
                const elapsed = Date.now() - headPoseAwayStartTime;
                if (elapsed >= HEAD_POSE_DELAY) {
                    console.log('[Proctoring] Head pose: looking away for 2+ seconds, direction:', gazeResult.direction);
                    triggerEyeWarning('Head movement detected away from screen. Please face the exam directly.');
                    // Reset so the NEXT time head turns away, it starts fresh
                    headPoseAwayStartTime = null;
                }
            }
        } else {
            // Head returned to facing screen -- reset timer
            headPoseAwayStartTime = null;
        }
    }, DETECTION_INTERVAL);
}

/**
 * Detect head pose using face-api.js landmarks
 */
async function detectHeadPose() {
    if (faceApiLoaded && landmarksLoaded && typeof faceapi !== 'undefined') {
        try {
            const detection = await faceapi
                .detectSingleFace(detectionVideo, new faceapi.TinyFaceDetectorOptions({
                    inputSize: 224,
                    scoreThreshold: 0.4
                }))
                .withFaceLandmarks(true);

            if (!detection) {
                return { lookingAway: true, direction: 'no_face' };
            }

            const positions = detection.landmarks.positions;
            const headPose = calculateHeadPose(positions);

            // Face bounding box position
            const box = detection.detection.box;
            const videoWidth = detectionVideo.videoWidth || detectionVideo.width;
            const faceCenterX = (box.x + box.width / 2) / videoWidth;

            // Debug logging
            debugLogCounter++;
            if (debugLogCounter >= DEBUG_LOG_INTERVAL) {
                console.log(`[Proctoring] HeadPose: yaw=${headPose.yawRatio.toFixed(3)}, pitch=${headPose.pitchRatio.toFixed(3)}, faceX=${faceCenterX.toFixed(3)}`);
                debugLogCounter = 0;
            }

            let lookingAway = false;
            let direction = 'center';

            if (headPose.yawRatio < YAW_THRESHOLD_LOW) {
                lookingAway = true;
                direction = 'turned_right';
            } else if (headPose.yawRatio > YAW_THRESHOLD_HIGH) {
                lookingAway = true;
                direction = 'turned_left';
            }

            if (headPose.pitchRatio < PITCH_THRESHOLD_LOW) {
                lookingAway = true;
                direction = direction === 'center' ? 'looking_up' : direction + '_up';
            } else if (headPose.pitchRatio > PITCH_THRESHOLD_HIGH) {
                lookingAway = true;
                direction = direction === 'center' ? 'looking_down' : direction + '_down';
            }

            if (faceCenterX < FACE_BOX_X_LOW || faceCenterX > FACE_BOX_X_HIGH) {
                lookingAway = true;
                direction = direction === 'center' ? 'off_center' : direction + '_shifted';
            }

            return { lookingAway, direction };
        } catch (e) {
            return { lookingAway: false, direction: null };
        }
    }

    // Fallback: face bounding box only
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

            const lookingAway = faceCenterX < FACE_BOX_X_LOW || faceCenterX > FACE_BOX_X_HIGH ||
                                faceCenterY < 0.15 || faceCenterY > 0.85;

            return { lookingAway, direction: lookingAway ? 'off_center' : 'center' };
        } catch (e) {
            return { lookingAway: false, direction: null };
        }
    }

    return { lookingAway: false, direction: null };
}

/**
 * Calculate head pose (yaw and pitch) from 68-point landmarks.
 * 
 * YAW: Compare distances from nose tip to each eye corner.
 *   Ratio 0.5 = facing forward, <0.32 = turned right, >0.68 = turned left
 * 
 * PITCH: Nose tip position relative to eye-line and chin.
 *   Normal: 0.4-0.6, Looking down: >0.65, Looking up: <0.30
 */
function calculateHeadPose(positions) {
    const noseTip = positions[30];
    const chin = positions[8];
    const leftEyeOuter = positions[36];
    const rightEyeOuter = positions[45];

    // Yaw
    const leftDist = Math.abs(noseTip.x - leftEyeOuter.x);
    const rightDist = Math.abs(noseTip.x - rightEyeOuter.x);
    let yawRatio = 0.5;
    if (leftDist + rightDist > 0) {
        yawRatio = leftDist / (leftDist + rightDist);
    }

    // Pitch
    const eyeLineY = (leftEyeOuter.y + rightEyeOuter.y) / 2;
    const faceHeight = chin.y - eyeLineY;
    let pitchRatio = 0.5;
    if (faceHeight > 0) {
        pitchRatio = Math.max(0, Math.min(1, (noseTip.y - eyeLineY) / faceHeight));
    }

    return { yawRatio, pitchRatio };
}

// ========================
// Warning System (shared by all signals)
// ========================

/**
 * Trigger a proctoring warning with a specific message.
 * Uses a global cooldown to prevent spamming -- only one warning per 6 seconds.
 * @param {string} message - Custom warning message for the specific signal
 */
function triggerEyeWarning(message) {
    if (!canShowWarning()) return;  // Still in cooldown
    if (warningCount >= MAX_WARNINGS) return;  // Max reached

    lastWarningTime = Date.now();
    warningCount++;

    const warningOverlay = document.getElementById('eye-warning-overlay');
    const warningText = document.getElementById('eye-warning-text');
    const warningCounter = document.getElementById('eye-warning-count');

    if (warningOverlay) {
        warningOverlay.style.display = 'flex';

        if (warningCount >= MAX_WARNINGS) {
            if (warningText) warningText.textContent = 'CRITICAL: Multiple violations detected! Your exam may be invalidated.';
        } else if (warningCount >= 3) {
            if (warningText) warningText.textContent = message || 'WARNING: Please keep your focus on the exam. Too many violations may terminate your exam.';
        } else {
            if (warningText) warningText.textContent = message || 'Please maintain focus on the exam questions.';
        }

        if (warningCounter) warningCounter.textContent = `Warnings: ${warningCount}/${MAX_WARNINGS}`;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            hideEyeWarning();
        }, WARNING_AUTO_HIDE_MS);
    }

    // Show notification
    showEyeNotification();
}

/**
 * Show a slide-in notification for warning
 */
function showEyeNotification() {
    const notification = document.getElementById('eye-notification');
    if (notification) {
        notification.textContent = `Proctoring Warning (${warningCount}/${MAX_WARNINGS})`;
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

// ========================
// Cleanup
// ========================

/**
 * Stop all detection monitoring
 */
function stopEyeDetection() {
    // Stop head pose interval
    if (eyeDetectionInterval) {
        clearInterval(eyeDetectionInterval);
        eyeDetectionInterval = null;
    }

    // Stop mouse leave timer
    if (mouseLeaveTimer) {
        clearTimeout(mouseLeaveTimer);
        mouseLeaveTimer = null;
    }
}

/**
 * Get current warning count
 * @returns {number}
 */
function getWarningCount() {
    return warningCount;
}
