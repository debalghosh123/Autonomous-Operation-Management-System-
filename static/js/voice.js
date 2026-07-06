/**
 * Career Lab Consulting - Keyboard Shortcuts Handler
 * Listens for keydown events to navigate exam questions and select options.
 * Shortcuts:
 *   ArrowRight  - navigate to next question
 *   ArrowLeft   - navigate to previous question
 *   A/B/C/D or 1/2/3/4 - select option
 *   Enter       - submit exam
 *   ?           - toggle shortcuts guide
 */

(function() {
    'use strict';

    let shortcutsGuideVisible = false;
    let toastTimeout = null;

    document.addEventListener('DOMContentLoaded', function() {
        const shortcutsBtn = document.getElementById('shortcuts-btn');
        const shortcutsGuide = document.getElementById('shortcuts-guide');
        const shortcutsGuideClose = document.getElementById('shortcuts-guide-close');

        if (shortcutsBtn) {
            shortcutsBtn.addEventListener('click', function() {
                toggleShortcutsGuide();
            });
        }

        if (shortcutsGuideClose) {
            shortcutsGuideClose.addEventListener('click', function() {
                hideShortcutsGuide();
            });
        }

        // Close guide when clicking overlay background
        if (shortcutsGuide) {
            shortcutsGuide.addEventListener('click', function(e) {
                if (e.target === shortcutsGuide) {
                    hideShortcutsGuide();
                }
            });
        }

        // Listen for keyboard shortcuts
        document.addEventListener('keydown', handleKeydown);
    });

    /**
     * Main keydown handler
     */
    function handleKeydown(e) {
        // Ignore if user is typing in an input or textarea
        var tag = e.target.tagName.toLowerCase();
        if (tag === 'input' || tag === 'textarea' || tag === 'select') {
            return;
        }

        var key = e.key;

        switch (key) {
            case 'ArrowRight':
                e.preventDefault();
                navigateNext();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                navigatePrevious();
                break;
            case 'a':
            case 'A':
                e.preventDefault();
                selectOption('A');
                break;
            case 'b':
            case 'B':
                e.preventDefault();
                selectOption('B');
                break;
            case 'c':
            case 'C':
                e.preventDefault();
                selectOption('C');
                break;
            case 'd':
            case 'D':
                e.preventDefault();
                selectOption('D');
                break;
            case '1':
                e.preventDefault();
                selectOption('A');
                break;
            case '2':
                e.preventDefault();
                selectOption('B');
                break;
            case '3':
                e.preventDefault();
                selectOption('C');
                break;
            case '4':
                e.preventDefault();
                selectOption('D');
                break;
            case 'Enter':
                e.preventDefault();
                submitExamShortcut();
                break;
            case '?':
                e.preventDefault();
                toggleShortcutsGuide();
                break;
        }
    }

    /**
     * Navigate to next question
     */
    function navigateNext() {
        if (typeof currentQuestion !== 'undefined' && typeof totalQuestions !== 'undefined') {
            if (currentQuestion < totalQuestions) {
                navigateQuestion(currentQuestion + 1);
                showToast('Question ' + (currentQuestion) + ' of ' + totalQuestions);
            } else {
                showToast('Already on the last question');
            }
        }
    }

    /**
     * Navigate to previous question
     */
    function navigatePrevious() {
        if (typeof currentQuestion !== 'undefined') {
            if (currentQuestion > 1) {
                navigateQuestion(currentQuestion - 1);
                showToast('Question ' + (currentQuestion) + ' of ' + totalQuestions);
            } else {
                showToast('Already on the first question');
            }
        }
    }

    /**
     * Select an option on the current question
     */
    function selectOption(option) {
        var activeCard = document.querySelector('.question-card.active');
        if (activeCard) {
            var radio = activeCard.querySelector('input[value="' + option + '"]');
            if (radio) {
                radio.checked = true;
                radio.dispatchEvent(new Event('change', { bubbles: true }));
                showToast('Selected option ' + option);
            }
        }
    }

    /**
     * Submit exam via keyboard shortcut
     */
    function submitExamShortcut() {
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

    /**
     * Toggle the shortcuts guide overlay
     */
    function toggleShortcutsGuide() {
        if (shortcutsGuideVisible) {
            hideShortcutsGuide();
        } else {
            showShortcutsGuide();
        }
    }

    function showShortcutsGuide() {
        var guide = document.getElementById('shortcuts-guide');
        if (guide) {
            guide.style.display = 'flex';
            shortcutsGuideVisible = true;
        }
    }

    function hideShortcutsGuide() {
        var guide = document.getElementById('shortcuts-guide');
        if (guide) {
            guide.style.display = 'none';
            shortcutsGuideVisible = false;
        }
    }

    /**
     * Show a feedback toast notification
     */
    function showToast(message) {
        var toast = document.getElementById('shortcuts-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'shortcuts-toast';
            toast.className = 'shortcuts-toast';
            document.body.appendChild(toast);
        }

        toast.textContent = message;
        toast.classList.add('show');

        if (toastTimeout) {
            clearTimeout(toastTimeout);
        }
        toastTimeout = setTimeout(function() {
            toast.classList.remove('show');
        }, 1500);
    }

    // Expose for cleanup if needed
    window.stopVoiceMode = function() {};

})();
