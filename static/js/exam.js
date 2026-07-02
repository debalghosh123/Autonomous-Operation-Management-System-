/**
 * Career Lab Consulting - Exam JavaScript
 * Handles question navigation, timer, and submission
 */

let currentQuestion = 1;
let totalQuestions = 25;
let timerInterval = null;
let timeRemaining = 0;

function initExam(total, duration) {
    totalQuestions = total;
    timeRemaining = duration * 60;
    startTimer();
    setupNavigation();
}

function startTimer() {
    updateTimerDisplay();
    timerInterval = setInterval(function() {
        timeRemaining--;
        updateTimerDisplay();
        if (timeRemaining <= 0) {
            clearInterval(timerInterval);
            alert('Time is up! Your exam will be submitted automatically.');
            document.getElementById('exam-form').submit();
        }
    }, 1000);
}

function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    const display = document.getElementById('time-display');
    if (display) {
        display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    // Change color when time is running low
    const timer = document.getElementById('timer');
    if (timer && timeRemaining < 300) {
        timer.style.color = '#ff4444';
        timer.style.borderColor = '#ff4444';
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
            const answered = document.querySelectorAll('.dot.answered').length;
            if (answered < totalQuestions) {
                if (!confirm(`You have answered ${answered}/${totalQuestions} questions. Are you sure you want to submit?`)) {
                    e.preventDefault();
                }
            }
        });
    }
}

function navigateQuestion(index) {
    if (index < 1 || index > totalQuestions) return;

    // Hide current
    document.querySelector('.question-card.active').classList.remove('active');
    document.querySelector('.dot.active').classList.remove('active');

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
}
