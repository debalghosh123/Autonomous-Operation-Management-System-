/**
 * Career Lab Consulting - Voice Mode (Complete Rewrite)
 * Persistent speech recognition with client-side command processing.
 * No API calls needed - all commands handled locally for instant response.
 */

(function() {
    'use strict';

    // State
    let recognition = null;
    let isListening = false;
    let isVoiceActivated = false;
    let consecutiveErrors = 0;
    let restartTimeout = null;
    let retryTimeout = null;
    const MAX_CONSECUTIVE_ERRORS = 5;
    const RESTART_DELAY = 500;
    const ERROR_RESTART_DELAY = 1000;
    const BACKOFF_RETRY_DELAY = 3000;

    // DOM references (populated on DOMContentLoaded)
    let voiceBtn = null;
    let voiceOverlay = null;
    let voiceClose = null;
    let voiceFeedback = null;
    let voiceStatus = null;
    let voiceIndicator = null;
    let voiceLastCommand = null;
    let voiceActionTaken = null;

    // Command patterns for client-side matching
    const COMMANDS = {
        next: /\b(next|skip|forward|move forward|go forward|next question)\b/i,
        previous: /\b(previous|prev|back|go back|last|before)\b/i,
        selectA: /\b(select a|option a|answer a|choose a)\b/i,
        selectB: /\b(select b|option b|answer b|choose b)\b/i,
        selectC: /\b(select c|option c|answer c|choose c)\b/i,
        selectD: /\b(select d|option d|answer d|choose d)\b/i,
        singleA: /^a$/i,
        singleB: /^b$/i,
        singleC: /^c$/i,
        singleD: /^d$/i,
        submit: /\b(submit|finish|done|end|end exam|submit exam|finish exam)\b/i,
        time: /\b(time|how much time|timer|time left|time remaining|how long)\b/i,
        read: /\b(read|read question|read it|read aloud|read the question|read out)\b/i,
        help: /\b(help|commands|what can i say|what commands)\b/i
    };

    document.addEventListener('DOMContentLoaded', function() {
        voiceBtn = document.getElementById('voice-btn');
        voiceOverlay = document.getElementById('voice-overlay');
        voiceClose = document.getElementById('voice-close');
        voiceFeedback = document.getElementById('voice-feedback');
        voiceStatus = document.getElementById('voice-status');
        voiceIndicator = document.getElementById('voice-indicator');
        voiceLastCommand = document.getElementById('voice-last-command');
        voiceActionTaken = document.getElementById('voice-action-taken');

        if (voiceBtn) {
            voiceBtn.addEventListener('click', function() {
                if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
                    showVoiceAlert('Voice mode is not supported in your browser. Please use Chrome or Edge.');
                    return;
                }
                toggleVoiceOverlay();
            });
        }

        if (voiceClose) {
            voiceClose.addEventListener('click', function() {
                closeOverlay();
            });
        }
    });

    /**
     * Toggle the voice overlay panel (listening persists after close)
     */
    function toggleVoiceOverlay() {
        if (!isVoiceActivated) {
            // First activation - start listening and show overlay
            isVoiceActivated = true;
            showOverlay();
            startListening();
            showVoiceIndicator();
        } else if (voiceOverlay && voiceOverlay.style.display === 'flex') {
            // Overlay is visible - close it (keep listening)
            closeOverlay();
        } else {
            // Overlay is hidden - show it again
            showOverlay();
        }
    }

    function showOverlay() {
        if (voiceOverlay) {
            voiceOverlay.style.display = 'flex';
        }
    }

    function closeOverlay() {
        if (voiceOverlay) {
            voiceOverlay.style.display = 'none';
        }
        // Voice continues listening in background
    }

    /**
     * Show/hide voice indicator in exam header
     */
    function showVoiceIndicator() {
        if (voiceIndicator) {
            voiceIndicator.style.display = 'inline-flex';
        }
    }

    function hideVoiceIndicator() {
        if (voiceIndicator) {
            voiceIndicator.style.display = 'none';
        }
    }

    /**
     * Start speech recognition with persistent listening
     */
    function startListening() {
        if (recognition) {
            try { recognition.abort(); } catch(e) {}
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return;

        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        recognition.maxAlternatives = 1;

        recognition.onstart = function() {
            isListening = true;
            consecutiveErrors = 0;
            updateStatus('Listening... Speak a command.');
            updateIndicatorState('listening');
        };

        recognition.onresult = function(event) {
            consecutiveErrors = 0;
            const lastResult = event.results[event.results.length - 1];
            if (lastResult.isFinal) {
                const transcript = lastResult[0].transcript.trim();
                if (transcript) {
                    processCommand(transcript);
                }
            }
        };

        recognition.onerror = function(event) {
            // 'no-speech' and 'aborted' are normal - not real errors
            if (event.error === 'no-speech' || event.error === 'aborted') {
                return;
            }

            consecutiveErrors++;
            console.warn('[Voice] Recognition error:', event.error, '(count:', consecutiveErrors, ')');

            if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
                updateStatus('Microphone issue detected. Retrying...');
                updateIndicatorState('error');
                // Back off to 3-second retry
                clearTimeout(retryTimeout);
                retryTimeout = setTimeout(function() {
                    if (isVoiceActivated) {
                        restartRecognition();
                    }
                }, BACKOFF_RETRY_DELAY);
            } else {
                updateStatus('Recovering... (' + event.error + ')');
                // Normal error restart with 1s delay
                clearTimeout(restartTimeout);
                restartTimeout = setTimeout(function() {
                    if (isVoiceActivated) {
                        restartRecognition();
                    }
                }, ERROR_RESTART_DELAY);
            }
        };

        recognition.onend = function() {
            isListening = false;
            // Always restart if voice is activated (500ms delay prevents rapid loops)
            if (isVoiceActivated) {
                clearTimeout(restartTimeout);
                restartTimeout = setTimeout(function() {
                    if (isVoiceActivated) {
                        restartRecognition();
                    }
                }, RESTART_DELAY);
            }
        };

        try {
            recognition.start();
        } catch(e) {
            console.warn('[Voice] Failed to start recognition:', e);
            // Retry after delay
            clearTimeout(restartTimeout);
            restartTimeout = setTimeout(function() {
                if (isVoiceActivated) {
                    restartRecognition();
                }
            }, ERROR_RESTART_DELAY);
        }
    }

    /**
     * Restart recognition safely
     */
    function restartRecognition() {
        if (!isVoiceActivated) return;
        if (recognition) {
            try { recognition.abort(); } catch(e) {}
        }
        startListening();
    }

    /**
     * Stop voice mode completely
     */
    function stopVoiceMode() {
        isVoiceActivated = false;
        isListening = false;
        clearTimeout(restartTimeout);
        clearTimeout(retryTimeout);
        if (recognition) {
            try { recognition.abort(); } catch(e) {}
            recognition = null;
        }
        hideVoiceIndicator();
        closeOverlay();
        updateIndicatorState('off');
    }

    /**
     * Process a voice command entirely client-side
     */
    function processCommand(transcript) {
        const command = transcript.toLowerCase().trim();
        updateLastCommand(transcript);

        // Match commands in priority order
        if (COMMANDS.next.test(command)) {
            executeNext();
        } else if (COMMANDS.previous.test(command)) {
            executePrevious();
        } else if (COMMANDS.selectA.test(command) || COMMANDS.singleA.test(command)) {
            executeSelect('A');
        } else if (COMMANDS.selectB.test(command) || COMMANDS.singleB.test(command)) {
            executeSelect('B');
        } else if (COMMANDS.selectC.test(command) || COMMANDS.singleC.test(command)) {
            executeSelect('C');
        } else if (COMMANDS.selectD.test(command) || COMMANDS.singleD.test(command)) {
            executeSelect('D');
        } else if (COMMANDS.submit.test(command)) {
            executeSubmit();
        } else if (COMMANDS.time.test(command)) {
            executeTime();
        } else if (COMMANDS.read.test(command)) {
            executeReadQuestion();
        } else if (COMMANDS.help.test(command)) {
            executeHelp();
        } else {
            updateActionTaken('Command not recognized: "' + transcript + '"');
            speak('Sorry, I did not understand that. Say help for available commands.');
        }
    }

    // --- Command Executors ---

    function executeNext() {
        if (typeof currentQuestion !== 'undefined' && typeof totalQuestions !== 'undefined') {
            if (currentQuestion < totalQuestions) {
                var target = currentQuestion + 1;
                navigateQuestion(target);
                var msg = 'Moving to question ' + target;
                updateActionTaken(msg);
                speak(msg);
            } else {
                var msg2 = 'Already on the last question';
                updateActionTaken(msg2);
                speak(msg2);
            }
        }
    }

    function executePrevious() {
        if (typeof currentQuestion !== 'undefined') {
            if (currentQuestion > 1) {
                var target = currentQuestion - 1;
                navigateQuestion(target);
                var msg = 'Moving to question ' + target;
                updateActionTaken(msg);
                speak(msg);
            } else {
                var msg2 = 'Already on the first question';
                updateActionTaken(msg2);
                speak(msg2);
            }
        }
    }

    function executeSelect(option) {
        var activeCard = document.querySelector('.question-card.active');
        if (activeCard) {
            var radio = activeCard.querySelector('input[value="' + option + '"]');
            if (radio) {
                radio.checked = true;
                radio.dispatchEvent(new Event('change', { bubbles: true }));
                var msg = 'Selected option ' + option;
                updateActionTaken(msg);
                speak(msg);
            } else {
                var msg2 = 'Option ' + option + ' not found';
                updateActionTaken(msg2);
                speak(msg2);
            }
        }
    }

    function executeSubmit() {
        updateActionTaken('Submitting exam...');
        speak('Submitting your exam.');

        // Use showConfirm if available, otherwise native confirm
        if (typeof showConfirm === 'function') {
            showConfirm('Submit your exam?', 'Confirm Submission').then(function(confirmed) {
                if (confirmed) {
                    if (typeof submitExam === 'function') {
                        submitExam();
                    } else {
                        document.getElementById('exam-form').submit();
                    }
                }
            });
        } else {
            if (confirm('Submit your exam?')) {
                if (typeof submitExam === 'function') {
                    submitExam();
                } else {
                    document.getElementById('exam-form').submit();
                }
            }
        }
    }

    function executeTime() {
        var display = document.getElementById('time-display');
        if (display) {
            var timeText = display.textContent;
            var msg = 'Time remaining: ' + timeText;
            updateActionTaken(msg);
            speak(msg);
        } else {
            speak('Timer not available.');
        }
    }

    function executeReadQuestion() {
        var activeCard = document.querySelector('.question-card.active');
        if (!activeCard) {
            speak('No active question found.');
            return;
        }

        var questionText = activeCard.querySelector('.question-text');
        var options = activeCard.querySelectorAll('.option-text');

        var textToRead = '';
        if (questionText) {
            textToRead = questionText.textContent.trim();
        }

        if (options.length > 0) {
            var labels = ['A', 'B', 'C', 'D'];
            textToRead += '. Options: ';
            options.forEach(function(opt, index) {
                if (index < labels.length) {
                    textToRead += labels[index] + ': ' + opt.textContent.trim() + '. ';
                }
            });
        }

        updateActionTaken('Reading question aloud');
        speak(textToRead);
    }

    function executeHelp() {
        var helpText = 'Available commands: ' +
            'Say next or skip to go forward. ' +
            'Say previous or back to go back. ' +
            'Say A, B, C, or D to select an answer. ' +
            'Say select A, select B, select C, or select D. ' +
            'Say submit or finish to end the exam. ' +
            'Say time to hear remaining time. ' +
            'Say read to hear the current question. ' +
            'Say help to hear these commands again.';
        updateActionTaken('Listing available commands');
        speak(helpText);
    }

    // --- Text-to-Speech ---

    function speak(text) {
        if (!('speechSynthesis' in window)) return;
        // Cancel any current speech
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        utterance.lang = 'en-US';
        window.speechSynthesis.speak(utterance);
    }

    // --- UI Updates ---

    function updateStatus(text) {
        if (voiceStatus) {
            voiceStatus.textContent = text;
        }
    }

    function updateLastCommand(text) {
        if (voiceFeedback) {
            voiceFeedback.textContent = 'Heard: "' + text + '"';
        }
        if (voiceLastCommand) {
            voiceLastCommand.textContent = '"' + text + '"';
        }
    }

    function updateActionTaken(text) {
        if (voiceActionTaken) {
            voiceActionTaken.textContent = text;
        }
        // Also update the overlay feedback
        if (voiceFeedback) {
            voiceFeedback.innerHTML = '<span class="voice-heard">Heard: "' + (voiceLastCommand ? voiceLastCommand.textContent : '') + '"</span><br><span class="voice-action">' + text + '</span>';
        }
    }

    function updateIndicatorState(state) {
        if (!voiceIndicator) return;
        voiceIndicator.classList.remove('voice-indicator-listening', 'voice-indicator-error');
        if (state === 'listening') {
            voiceIndicator.classList.add('voice-indicator-listening');
        } else if (state === 'error') {
            voiceIndicator.classList.add('voice-indicator-error');
        }
    }

    function showVoiceAlert(message) {
        if (typeof showAlert === 'function') {
            showAlert(message, 'Voice Mode', 'warning');
        } else {
            alert(message);
        }
    }

    // Expose stopVoiceMode globally for cleanup
    window.stopVoiceMode = stopVoiceMode;

})();
