/**
 * Career Lab Consulting - Exam JavaScript
 * Handles question navigation, per-question timer (60 seconds), and submission
 */

let currentQuestion = 1;
let totalQuestions = 25;
let timerInterval = null;
let questionTimeRemaining = 60; // 60 seconds per question
const SECONDS_PER_QUESTION = 60;

// Track per-question remaining time (array indexed by question number, 1-based)
let questionTimers = [];

function initExam(total, duration) {
    totalQuestions = total;
    // Initialize per-question timers (all start at 60 seconds)
    questionTimers = new Array(totalQuestions + 1).fill(SECONDS_PER_QUESTION);
    setupNavigation();
    startQuestionTimer();
}

/**
 * Start the per-question countdown timer (resumes from saved time)
 */
function startQuestionTimer() {
    // Restore saved time for this question
    questionTimeRemaining = questionTimers[currentQuestion] || SECONDS_PER_QUESTION;
    updateTimerDisplay();

    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timerInterval = setInterval(function() {
        questionTimeRemaining--;
        questionTimers[currentQuestion] = questionTimeRemaining;
        updateTimerDisplay();

        if (questionTimeRemaining <= 0) {
            clearInterval(timerInterval);
            onQuestionTimeout();
        }
    }, 1000);
}

/**
 * Save the current question's remaining time before navigating away
 */
function saveCurrentQuestionTime() {
    if (currentQuestion >= 1 && currentQuestion <= totalQuestions) {
        questionTimers[currentQuestion] = questionTimeRemaining;
    }
}

/**
 * Handle when the per-question timer expires
 */
function onQuestionTimeout() {
    // Notify proctoring system before auto-advance to suppress false blur events
    if (typeof onQuestionNavigating === 'function') {
        onQuestionNavigating();
    }

    if (currentQuestion < totalQuestions) {
        // Auto-advance to next question
        navigateQuestion(currentQuestion + 1);
    } else {
        // Last question - auto-submit the exam
        submitExam();
    }
}

/**
 * Submit the exam form and stop camera
 */
function submitExam() {
    // Stop camera stream (wrapped in try/catch to prevent blocking form submission)
    try {
        if (typeof stopCamera === 'function') {
            stopCamera();
        }
    } catch (e) {
        console.warn('[Exam] Error stopping camera:', e);
    }
    // Stop eye detection (wrapped in try/catch to prevent blocking form submission)
    try {
        if (typeof stopEyeDetection === 'function') {
            stopEyeDetection();
        }
    } catch (e) {
        console.warn('[Exam] Error stopping eye detection:', e);
    }
    // Clear timer
    if (timerInterval) {
        clearInterval(timerInterval);
    }
    // Show processing overlay
    var overlay = document.getElementById('processing-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
    }
    document.getElementById('exam-form').submit();
}

function updateTimerDisplay() {
    const minutes = Math.floor(questionTimeRemaining / 60);
    const seconds = questionTimeRemaining % 60;
    const display = document.getElementById('time-display');
    if (display) {
        display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    // Change color when time is running low (less than 10 seconds)
    const timer = document.getElementById('timer');
    if (timer) {
        if (questionTimeRemaining <= 10) {
            timer.classList.add('timer-critical');
            timer.classList.remove('timer-warning');
        } else if (questionTimeRemaining <= 20) {
            timer.classList.add('timer-warning');
            timer.classList.remove('timer-critical');
        } else {
            timer.classList.remove('timer-warning');
            timer.classList.remove('timer-critical');
        }
    }
}

function setupNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    if (prevBtn) {
        prevBtn.addEventListener('click', function() {
            navigateQuestion(currentQuestion - 1);
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', function() {
            navigateQuestion(currentQuestion + 1);
        });
    }

    // Dot navigation
    document.querySelectorAll('.dot').forEach(dot => {
        dot.addEventListener('click', function() {
            navigateQuestion(parseInt(this.dataset.index));
        });
    });

    // Track answered questions
    document.querySelectorAll('input[type="radio"]').forEach(input => {
        input.addEventListener('change', function() {
            const questionCard = this.closest('.question-card');
            const index = questionCard.dataset.index;
            const dot = document.querySelector(`.dot[data-index="${index}"]`);
            if (dot) {
                dot.classList.add('answered');
            }
        });
    });

    // Confirm before submit
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const answered = document.querySelectorAll('.dot.answered').length;
            var message;
            if (answered < totalQuestions) {
                message = 'You have answered ' + answered + '/' + totalQuestions + ' questions. Are you sure you want to submit?';
            } else {
                message = 'You have answered all questions. Ready to submit your exam?';
            }

            // Guard: if showConfirm is not available, fall back to native confirm()
            if (typeof showConfirm === 'function') {
                showConfirm(message, 'Submit Exam').then(function(confirmed) {
                    if (confirmed) {
                        submitExam();
                    }
                });
            } else {
                // Fallback to native confirm if modal system is unavailable
                if (confirm(message)) {
                    submitExam();
                }
            }
        });
    }
}

function navigateQuestion(index) {
    if (index < 1 || index > totalQuestions) return;

    // Notify proctoring system that navigation is happening to suppress false blur events
    if (typeof onQuestionNavigating === 'function') {
        onQuestionNavigating();
    }

    // Save current question's remaining time before navigating away
    saveCurrentQuestionTime();

    // Clear the current timer
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    // Hide current
    const activeCard = document.querySelector('.question-card.active');
    const activeDot = document.querySelector('.dot.active');
    if (activeCard) activeCard.classList.remove('active');
    if (activeDot) activeDot.classList.remove('active');

    // Show target
    const targetCard = document.getElementById(`question-${index}`);
    if (targetCard) {
        targetCard.classList.add('active');
    }

    const targetDot = document.querySelector(`.dot[data-index="${index}"]`);
    if (targetDot) {
        targetDot.classList.add('active');
    }

    currentQuestion = index;

    // Update counter
    document.getElementById('current-q').textContent = currentQuestion;

    // Update button states
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    if (prevBtn) prevBtn.disabled = (currentQuestion === 1);
    if (nextBtn) nextBtn.disabled = (currentQuestion === totalQuestions);

    // Start timer with saved remaining time for this question
    startQuestionTimer();
}
