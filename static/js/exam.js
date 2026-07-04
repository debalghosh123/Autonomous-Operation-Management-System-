/**
 * Career Lab Consulting - Exam JavaScript
 * Handles question navigation, per-question timer (60 seconds), and submission
 */

let currentQuestion = 1;
let totalQuestions = 25;
let timerInterval = null;
let questionTimeRemaining = 60; // 60 seconds per question
const SECONDS_PER_QUESTION = 60;

function initExam(total, duration) {
    totalQuestions = total;
    setupNavigation();
    startQuestionTimer();
}

/**
 * Start the per-question countdown timer (60 seconds)
 */
function startQuestionTimer() {
    questionTimeRemaining = SECONDS_PER_QUESTION;
    updateTimerDisplay();

    if (timerInterval) {
        clearInterval(timerInterval);
    }

    timerInterval = setInterval(function() {
        questionTimeRemaining--;
        updateTimerDisplay();

        if (questionTimeRemaining <= 0) {
            clearInterval(timerInterval);
            onQuestionTimeout();
        }
    }, 1000);
}

/**
 * Handle when the per-question timer expires
 */
function onQuestionTimeout() {
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
    // Stop camera stream
    if (typeof stopCamera === 'function') {
        stopCamera();
    }
    // Stop eye detection
    if (typeof stopEyeDetection === 'function') {
        stopEyeDetection();
    }
    // Clear timer
    if (timerInterval) {
        clearInterval(timerInterval);
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
            if (answered < totalQuestions) {
                if (!confirm(`You have answered ${answered}/${totalQuestions} questions. Are you sure you want to submit?`)) {
                    return;
                }
            }
            submitExam();
        });
    }
}

function navigateQuestion(index) {
    if (index < 1 || index > totalQuestions) return;

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

    // Reset and restart per-question timer
    startQuestionTimer();
}
