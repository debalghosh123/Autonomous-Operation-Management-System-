/**
 * Career Lab Consulting - Proctoring System
 * ULTRA-SIMPLE: Uses ONLY browser focus events.
 * Every single alt-tab/tab-switch = one warning. Period.
 */

var warningCount = 0;
var MAX_WARNINGS = 5;
var warningVisible = false;

function initEyeDetection(videoElement) {
    console.log('[PROCTORING] System initialized');
    
    // visibilitychange - fires when user switches tabs
    document.addEventListener('visibilitychange', function() {
        console.log('[PROCTORING] visibilitychange, hidden=' + document.hidden);
        if (document.hidden) {
            showProctoringWarning('You switched away from the exam tab!');
        }
    });
    
    // blur - fires when window loses focus (alt-tab, click outside)
    window.addEventListener('blur', function() {
        console.log('[PROCTORING] window blur');
        if (!warningVisible) {
            showProctoringWarning('You left the exam window!');
        }
    });
}

function showProctoringWarning(message) {
    if (warningCount >= MAX_WARNINGS) return;
    if (warningVisible) return;
    
    warningCount++;
    warningVisible = true;
    console.log('[PROCTORING] WARNING #' + warningCount + ': ' + message);
    
    var overlay = document.getElementById('eye-warning-overlay');
    var textEl = document.getElementById('eye-warning-text');
    var counterEl = document.getElementById('eye-warning-count');
    
    if (overlay) {
        overlay.style.display = 'flex';
    }
    if (textEl) {
        if (warningCount >= MAX_WARNINGS) {
            textEl.textContent = 'CRITICAL: Too many violations! Your exam may be invalidated.';
        } else {
            textEl.textContent = message + ' Please maintain focus on the exam.';
        }
    }
    if (counterEl) {
        counterEl.textContent = 'Warnings: ' + warningCount + '/' + MAX_WARNINGS;
    }
    
    // Notification
    var notification = document.getElementById('eye-notification');
    if (notification) {
        notification.textContent = 'Warning ' + warningCount + '/' + MAX_WARNINGS;
        notification.classList.add('show');
        setTimeout(function() {
            notification.classList.remove('show');
        }, 4000);
    }
    
    // Auto-hide after 5 seconds, then allow next warning
    setTimeout(function() {
        warningVisible = false;
        if (overlay) {
            overlay.style.display = 'none';
        }
        console.log('[PROCTORING] Ready for next warning');
    }, 5000);
}

function triggerEyeWarning(message) {
    showProctoringWarning(message || 'Focus violation detected!');
}

function hideEyeWarning() {
    var overlay = document.getElementById('eye-warning-overlay');
    if (overlay) overlay.style.display = 'none';
}

function stopEyeDetection() {
    console.log('[PROCTORING] Stopped');
}

function getWarningCount() {
    return warningCount;
}

function onQuestionNavigating() {
    // No-op: question navigation should NOT affect proctoring
}
