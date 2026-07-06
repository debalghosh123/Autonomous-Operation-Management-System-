/**
 * Career Lab Consulting - Voice Mode
 * Web Speech API integration for accessibility
 */

let recognition = null;
let isListening = false;

document.addEventListener('DOMContentLoaded', function() {
    const voiceBtn = document.getElementById('voice-btn');
    const voiceOverlay = document.getElementById('voice-overlay');
    const voiceClose = document.getElementById('voice-close');
    const voiceFeedback = document.getElementById('voice-feedback');
    const voiceStatus = document.getElementById('voice-status');

    if (voiceBtn) {
        voiceBtn.addEventListener('click', function() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                toggleVoiceMode();
            } else {
                showAlert(
                    'Voice mode is not supported in your browser. Please use Chrome or Edge for voice commands.',
                    'Browser Not Supported',
                    'warning'
                );
            }
        });
    }

    if (voiceClose) {
        voiceClose.addEventListener('click', function() {
            stopVoiceMode();
        });
    }
});

function toggleVoiceMode() {
    const overlay = document.getElementById('voice-overlay');
    if (isListening) {
        stopVoiceMode();
    } else {
        overlay.style.display = 'flex';
        startVoiceMode();
    }
}

function startVoiceMode() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = function() {
        isListening = true;
        document.getElementById('voice-status').textContent = 'Listening... Speak a command.';
    };

    recognition.onresult = function(event) {
        const command = event.results[event.results.length - 1][0].transcript.trim();
        processVoiceInput(command);
    };

    recognition.onerror = function(event) {
        document.getElementById('voice-feedback').textContent = 'Error: ' + event.error;
    };

    recognition.onend = function() {
        if (isListening) {
            recognition.start(); // Restart if still in voice mode
        }
    };

    recognition.start();
}

function stopVoiceMode() {
    isListening = false;
    if (recognition) {
        recognition.stop();
    }
    document.getElementById('voice-overlay').style.display = 'none';
}

async function processVoiceInput(command) {
    const feedback = document.getElementById('voice-feedback');
    feedback.textContent = `Command: "${command}"`;

    try {
        const response = await fetch('/api/voice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });
        const data = await response.json();

        feedback.textContent = data.message;

        // Execute action
        switch (data.action) {
            case 'next_question':
                navigateQuestion(currentQuestion + 1);
                break;
            case 'previous_question':
                navigateQuestion(currentQuestion - 1);
                break;
            case 'select_answer':
                selectAnswer(data.answer);
                break;
            case 'submit_exam':
                showConfirm('Submit your exam?', 'Confirm Submission').then(function(confirmed) {
                    if (confirmed) {
                        document.getElementById('exam-form').submit();
                    }
                });
                break;
            case 'show_time':
                feedback.textContent = `Time remaining: ${document.getElementById('time-display').textContent}`;
                break;
        }

        // Speak response
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(data.message);
            utterance.rate = 1.0;
            speechSynthesis.speak(utterance);
        }
    } catch (error) {
        feedback.textContent = 'Error processing command. Please try again.';
    }
}

function selectAnswer(option) {
    const activeCard = document.querySelector('.question-card.active');
    if (activeCard) {
        const radio = activeCard.querySelector(`input[value="${option}"]`);
        if (radio) {
            radio.checked = true;
            radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}
