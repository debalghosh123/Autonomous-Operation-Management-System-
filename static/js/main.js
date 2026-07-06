/**
 * Career Lab Consulting - Main JavaScript
 * Python Evaluation System
 */

/**
 * Show a custom styled modal dialog.
 * @param {Object} options - Modal configuration
 * @param {string} options.title - Modal title
 * @param {string} options.message - Modal message
 * @param {string} [options.type] - 'info' | 'warning' | 'error' | 'success'
 * @param {boolean} [options.showCancel] - Whether to show cancel button (true for confirm, false for alert)
 * @param {string} [options.confirmText] - Text for confirm button
 * @param {string} [options.cancelText] - Text for cancel button
 * @returns {Promise<boolean>} Resolves true if confirmed, false if cancelled
 */
function showModal(options) {
    return new Promise(function(resolve) {
        var overlay = document.getElementById('custom-modal-overlay');
        var titleEl = document.getElementById('modal-title');
        var messageEl = document.getElementById('modal-message');
        var iconEl = document.getElementById('modal-icon');
        var confirmBtn = document.getElementById('modal-confirm');
        var cancelBtn = document.getElementById('modal-cancel');

        // Set content
        titleEl.textContent = options.title || 'Confirm';
        messageEl.textContent = options.message || '';

        // Set icon based on type
        var iconClass = 'fas fa-info-circle';
        var iconTypeClass = '';
        switch (options.type) {
            case 'warning':
                iconClass = 'fas fa-exclamation-triangle';
                iconTypeClass = 'modal-icon-warning';
                break;
            case 'error':
                iconClass = 'fas fa-times-circle';
                iconTypeClass = 'modal-icon-error';
                break;
            case 'success':
                iconClass = 'fas fa-check-circle';
                iconTypeClass = 'modal-icon-success';
                break;
            default:
                iconClass = 'fas fa-info-circle';
                iconTypeClass = '';
        }
        iconEl.innerHTML = '<i class="' + iconClass + '"></i>';
        iconEl.className = 'modal-icon' + (iconTypeClass ? ' ' + iconTypeClass : '');

        // Configure buttons
        confirmBtn.textContent = options.confirmText || 'OK';
        if (options.showCancel === false) {
            cancelBtn.style.display = 'none';
        } else {
            cancelBtn.style.display = '';
            cancelBtn.textContent = options.cancelText || 'Cancel';
        }

        // Show modal
        overlay.style.display = 'flex';

        // Clean up previous listeners
        var newConfirm = confirmBtn.cloneNode(true);
        var newCancel = cancelBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
        cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);

        function closeModal(result) {
            overlay.style.display = 'none';
            resolve(result);
        }

        newConfirm.addEventListener('click', function() { closeModal(true); });
        newCancel.addEventListener('click', function() { closeModal(false); });

        // Close on overlay click (outside the modal)
        overlay.addEventListener('click', function handler(e) {
            if (e.target === overlay) {
                overlay.removeEventListener('click', handler);
                closeModal(false);
            }
        });

        // Close on Escape key
        function escHandler(e) {
            if (e.key === 'Escape') {
                document.removeEventListener('keydown', escHandler);
                closeModal(false);
            }
        }
        document.addEventListener('keydown', escHandler);
    });
}

/**
 * Custom confirm dialog (replacement for native confirm())
 * @param {string} message - The confirmation message
 * @param {string} [title] - Optional title
 * @returns {Promise<boolean>}
 */
function showConfirm(message, title) {
    return showModal({
        title: title || 'Please Confirm',
        message: message,
        type: 'warning',
        showCancel: true,
        confirmText: 'Yes, Proceed',
        cancelText: 'Cancel'
    });
}

/**
 * Custom alert dialog (replacement for native alert())
 * @param {string} message - The alert message
 * @param {string} [title] - Optional title
 * @param {string} [type] - 'info' | 'warning' | 'error' | 'success'
 * @returns {Promise<boolean>}
 */
function showAlert(message, title, type) {
    return showModal({
        title: title || 'Notice',
        message: message,
        type: type || 'info',
        showCancel: false,
        confirmText: 'OK'
    });
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Career Lab Consulting - Python Evaluation System Loaded');

    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href && href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Add loading state to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn && !btn.classList.contains('no-loading')) {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    });
});
