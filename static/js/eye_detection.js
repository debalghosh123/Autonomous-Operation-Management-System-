/**
 * Career Lab Consulting - Multi-Signal Proctoring System
 * 
 * Detects when a candidate is distracted using MULTIPLE independent signals:
 * 
 * Signal 1: Browser Focus Detection (most reliable)
 *   - document.visibilitychange: detects tab switches
 *   - window.blur / window.focus: detects when browser loses focus
 *   - IMMEDIATE warning (no delay) -- these are definitive proof of distraction
 * 
 * Signal 2: Mouse/Pointer Leaving the Exam Area
 *   - document.mouseleave: mouse left the browser window
 *   - Warning after 2 seconds (might be accidental)
 * 
 * Signal 3: WebGazer.js Eye Tracking (actual gaze prediction)
 *   - Uses ML to predict where on screen the user is looking
 *   - If gaze point is OUTSIDE the exam container for 2+ seconds, trigger warning
 *   - This detects subtle eye movements WITHOUT head movement
 * 
 * Signal 4: Head Pose Estimation (supplementary backup)
 *   - Uses face-api.js 68-point landmarks to estimate head yaw/pitch
 *   - Warning after 2 seconds of head turned away
 * 
 * Each signal independently can trigger a warning.
 * One warning per distraction event; resets when the candidate returns focus.
 * MAX_WARNINGS = 5 with same UI overlays and 5-second auto-hide.
 */

// ========================
// Configuration
// ========================
const MAX_WARNINGS = 5;
const GAZE_AWAY_THRESHOLD = 2000;   // 2 seconds for gaze/mouse/head signals
const WARNING_AUTO_HIDE_MS = 5000;  // Auto-hide warning overlay after 5 seconds
const DETECTION_INTERVAL = 500;     // Head pose check every 500ms
const GAZE_RETURN_FRAMES = 3;      // 3 consecutive "at screen" frames (1.5s) to reset head pose

// Head pose thresholds (from previous implementation)
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
let detectionVideo = null;
let eyeDetectionInterval = null;

// Signal 1: Browser focus state
let focusWarningShown = false;

// Signal 2: Mouse leave state
let mouseLeaveTimer = null;
let mouseWarningShown = false;

// Signal 3: WebGazer state
let webgazerActive = false;
let gazeOutsideStartTime = null;
let gazeWarningShown = false;

// Signal 4: Head pose state
let faceApiLoaded = false;
let landmarksLoaded = false;
let headPoseAwayStartTime = null;
let headPoseWarningShown = false;
let headPoseAtScreenFrames = 0;

// Debug logging
let debugLogCounter = 0;
const DEBUG_LOG_INTERVAL = 6;

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
    
    // Initialize all signals in parallel
    initBrowserFocusDetection();
    initMouseLeaveDetection();
    initWebGazer();
    await initHeadPoseDetection();
    
    console.log('[Proctoring] All detection signals active');
}

// ========================
// Signal 1: Browser Focus Detection
// ========================

function initBrowserFocusDetection() {
    // Tab visibility change (tab switch, minimize)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            console.log('[Proctoring] Tab switch detected (visibilitychange)');
            triggerDistraction('tab_switch');
        } else {
            // Returned to tab
            resetFocusState();
        }
    });

    // Window blur (alt-tab, clicking another window)
    window.addEventListener('blur', () => {
        console.log('[Proctoring] Window blur detected');
        triggerDistraction('window_blur');
    });

    // Window focus regained
    window.addEventListener('focus', () => {
        resetFocusState();
    });

    console.log('[Proctoring] Signal 1 (Browser Focus) initialized');
}

function triggerDistraction(source) {
    // IMMEDIATE warning for tab switch / window blur (no delay)
    if (!focusWarningShown) {
        focusWarningShown = true;
        triggerEyeWarning(`Distraction detected: ${source === 'tab_switch' ? 'You switched tabs' : 'You left the exam window'}. Please stay focused on the exam.`);
    }
}

function resetFocusState() {
    focusWarningShown = false;
}

// ========================
// Signal 2: Mouse Leaving Browser
// ========================

function initMouseLeaveDetection() {
    document.addEventListener('mouseleave', () => {
        if (!mouseWarningShown) {
            mouseLeaveTimer = setTimeout(() => {
                if (!mouseWarningShown) {
                    mouseWarningShown = true;
                    console.log('[Proctoring] Mouse left browser window for 2+ seconds');
                    triggerEyeWarning('Your cursor left the exam window. Please keep your focus on the exam.');
                }
            }, GAZE_AWAY_THRESHOLD);
        }
    });

    document.addEventListener('mouseenter', () => {
        if (mouseLeaveTimer) {
            clearTimeout(mouseLeaveTimer);
            mouseLeaveTimer = null;
        }
        mouseWarningShown = false;
    });

    console.log('[Proctoring] Signal 2 (Mouse Leave) initialized');
}

// ========================
// Signal 3: WebGazer.js Eye Tracking
// ========================

function initWebGazer() {
    if (typeof webgazer === 'undefined') {
        console.warn('[Proctoring] WebGazer.js not available - skipping gaze tracking signal');
        return;
    }

    try {
        webgazer.setGazeListener((data, timestamp) => {
            if (!data) return;

            // Get exam container bounds
            const examContainer = document.getElementById('exam-form');
            if (!examContainer) return;

            const rect = examContainer.getBoundingClientRect();
            
            // Add some margin around the exam area (50px buffer for accuracy tolerance)
            const margin = 50;
            const isLookingAtExam = (
                data.x >= (rect.left - margin) &&
                data.x <= (rect.right + margin) &&
                data.y >= (rect.top - margin) &&
                data.y <= (rect.bottom + margin)
            );

            if (!isLookingAtExam) {
                // Gaze is outside exam area
                if (gazeOutsideStartTime === null) {
                    gazeOutsideStartTime = Date.now();
                } else if (!gazeWarningShown) {
                    const elapsed = Date.now() - gazeOutsideStartTime;
                    if (elapsed >= GAZE_AWAY_THRESHOLD) {
                        gazeWarningShown = true;
                        console.log('[Proctoring] WebGazer: gaze outside exam area for 2+ seconds');
                        triggerEyeWarning('Your eyes appear to be looking away from the exam questions. Please maintain focus.');
                    }
                }
            } else {
                // Gaze returned to exam area
                gazeOutsideStartTime = null;
                gazeWarningShown = false;
            }
        }).begin();

        // Hide WebGazer's built-in UI (we have our own camera preview)
        webgazer.showPredictionPoints(false);
        webgazer.showVideo(false);
        webgazer.showFaceOverlay(false);
        webgazer.showFaceFeedbackBox(false);
        
        webgazerActive = true;
        console.log('[Proctoring] Signal 3 (WebGazer Eye Tracking) initialized');
    } catch (e) {
        console.warn('[Proctoring] WebGazer initialization failed:', e.message);
        webgazerActive = false;
    }
}

// ========================
// Signal 4: Head Pose Detection (Backup)
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
        // Try just face detector without landmarks
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
    headPoseWarningShown = false;
    headPoseAtScreenFrames = 0;

    eyeDetectionInterval = setInterval(async () => {
        if (!detectionVideo || detectionVideo.paused || detectionVideo.ended) return;
        if (!faceApiLoaded) return;

        const gazeResult = await detectHeadPose();

        if (gazeResult.lookingAway) {
            headPoseAtScreenFrames = 0;

            if (headPoseAwayStartTime === null) {
                headPoseAwayStartTime = Date.now();
            } else if (!headPoseWarningShown) {
                const elapsed = Date.now() - headPoseAwayStartTime;
                if (elapsed >= GAZE_AWAY_THRESHOLD) {
                    headPoseWarningShown = true;
                    console.log('[Proctoring] Head pose: looking away for 2+ seconds, direction:', gazeResult.direction);
                    triggerEyeWarning('Head movement detected away from screen. Please face the exam directly.');
                }
            }
        } else {
            headPoseAtScreenFrames++;
            if (headPoseAtScreenFrames >= GAZE_RETURN_FRAMES) {
                headPoseAwayStartTime = null;
                headPoseWarningShown = false;
            }
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
 * Trigger an eye/gaze warning with a specific message
 * @param {string} message - Custom warning message for the specific signal
 */
function triggerEyeWarning(message) {
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

    // Stop WebGazer
    if (webgazerActive && typeof webgazer !== 'undefined') {
        try {
            webgazer.end();
        } catch (e) {
            console.warn('[Proctoring] Error stopping WebGazer:', e.message);
        }
        webgazerActive = false;
    }
}

/**
 * Get current warning count
 * @returns {number}
 */
function getWarningCount() {
    return warningCount;
}
