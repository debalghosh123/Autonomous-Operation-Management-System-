/**
 * Career Lab Consulting - Proctoring System
 * ULTRA-SIMPLE: Uses ONLY browser focus events.
 * Every single alt-tab/tab-switch = one warning. Period.
 * After MAX_WARNINGS violations, the exam is auto-terminated.
 */

var warningCount = 0;
var MAX_WARNINGS = 4;
var warningVisible = false;
var examTerminated = false;

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
    if (examTerminated) return;
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
            textEl.textContent = 'EXAM TERMINATED: Too many violations! Your exam has been automatically cancelled.';
        } else {
            textEl.textContent = message + ' Please maintain focus on the exam. (' + warningCount + '/' + MAX_WARNINGS + ' warnings)';
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
    
    // Check if max warnings reached - auto-terminate the exam
    if (warningCount >= MAX_WARNINGS) {
        examTerminated = true;
        console.log('[PROCTORING] MAX WARNINGS REACHED - AUTO-TERMINATING EXAM');
        // Set the terminated flag in the form
        var terminatedFlag = document.getElementById('terminated-flag');
        if (terminatedFlag) {
            terminatedFlag.value = '1';
        }
        // Auto-submit after a brief delay so candidate sees the termination message
        setTimeout(function() {
            if (typeof submitExam === 'function') {
                submitExam();
            } else {
                document.getElementById('exam-form').submit();
            }
        }, 2000);
        return;
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
