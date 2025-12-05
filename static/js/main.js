// Header is always visible - no hide functionality needed
// Main JavaScript file for Rezidenzia Faeldo Resort & Café
// Handles client-side interactions and UI enhancements

document.addEventListener('DOMContentLoaded', function () {
    // Initialize all functionality
    initializeFormValidation();
    initializeUIEnhancements();
    initializeInteractiveElements();
    initializeCartFunctionality();
    initializeOrderTracking();
});

// Form validation enhancements
function initializeFormValidation() {
    // Enhanced form validation for checkout
    const checkoutForm = document.getElementById('checkoutForm');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function (e) {
            if (!validateCheckoutForm()) {
                e.preventDefault();
            }
        });
    }

    // Enhanced form validation for reservations
    const reservationForm = document.getElementById('reservationForm');
    if (reservationForm) {
        reservationForm.addEventListener('submit', function (e) {
            if (!validateReservationForm()) {
                e.preventDefault();
            }
        });
    }

    // Real-time validation feedback
    const inputs = document.querySelectorAll('input[required], select[required], textarea[required]');
    inputs.forEach(input => {
        input.addEventListener('blur', function () {
            validateField(this);
        });

        input.addEventListener('input', function () {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

// Validate individual form fields
function validateField(field) {
    const isValid = field.checkValidity();

    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        hideFieldError(field);
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-valid');
        showFieldError(field, getValidationMessage(field));
    }

    return isValid;
}

// Show field-specific error messages
function showFieldError(field, message) {
    hideFieldError(field); // Remove existing error

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;

    field.parentNode.appendChild(errorDiv);
}

// Hide field error messages
function hideFieldError(field) {
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

// Get custom validation messages
function getValidationMessage(field) {
    if (field.validity.valueMissing) {
        return `${getFieldLabel(field)} is required.`;
    }
    if (field.validity.typeMismatch) {
        if (field.type === 'email') {
            return 'Please enter a valid email address.';
        }
        if (field.type === 'tel') {
            return 'Please enter a valid phone number.';
        }
    }
    if (field.validity.patternMismatch) {
        return 'Please match the required format.';
    }
    return field.validationMessage;
}

// Get field label for error messages
function getFieldLabel(field) {
    const label = document.querySelector(`label[for="${field.id}"]`);
    return label ? label.textContent.replace('*', '').trim() : 'This field';
}

// Validate checkout form
function validateCheckoutForm() {
    const form = document.getElementById('checkoutForm');
    if (!form) return true;

    let isValid = true;

    // Check required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    // Validate order type specific requirements
    const orderType = document.querySelector('input[name="order_type"]:checked').value;
    const addressField = document.getElementById('address');

    if (orderType === 'delivery' && (!addressField.value || addressField.value.trim().length < 10)) {
        showFieldError(addressField, 'Please provide a complete delivery address (at least 10 characters).');
        addressField.classList.add('is-invalid');
        isValid = false;
    }

    return isValid;
}

// Validate reservation form
function validateReservationForm() {
    const form = document.getElementById('reservationForm');
    if (!form) return true;

    let isValid = true;

    // Validate date is in the future
    const dateField = document.getElementById('reservation_date');
    if (dateField && dateField.value) {
        const selectedDate = new Date(dateField.value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            showFieldError(dateField, 'Please select a future date.');
            dateField.classList.add('is-invalid');
            isValid = false;
        }
    }

    // Validate large party handling
    const peopleField = document.getElementById('number_of_people');
    if (peopleField && peopleField.value === '13+') {
        showAlert('For parties of 13+ people, please call us directly at +1 (555) 123-4567 to make your reservation.', 'info');
        isValid = false;
    }

    return isValid;
}

// UI Enhancement functions
function initializeUIEnhancements() {
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId && targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Loading states for form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Processing...';
                submitBtn.disabled = true;

                // Re-enable button after 10 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 10000);
            }
        });
    });
}

// Interactive elements
function initializeInteractiveElements() {
    // Tooltips initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Confirm dialogs for destructive actions
    const dangerButtons = document.querySelectorAll('.btn-danger, .delete-product-btn');
    dangerButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            if (!this.dataset.confirmed) {
                e.preventDefault();
                if (confirm('Are you sure you want to perform this action? This cannot be undone.')) {
                    this.dataset.confirmed = 'true';
                    this.click();
                }
            }
        });
    });

    // Auto-focus first input in modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function () {
            const firstInput = this.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    });

    // Clear modal forms when closed
    modals.forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function () {
            const form = this.querySelector('form');
            if (form) {
                form.reset();
                // Remove validation classes
                const validatedFields = form.querySelectorAll('.is-valid, .is-invalid');
                validatedFields.forEach(field => {
                    field.classList.remove('is-valid', 'is-invalid');
                });
                // Remove error messages
                const errorMessages = form.querySelectorAll('.invalid-feedback');
                errorMessages.forEach(error => error.remove());
            }
        });
    });
}

// Cart functionality enhancements
function initializeCartFunctionality() {
    // Update cart badge animation
    const cartBadge = document.querySelector('.navbar .badge');
    if (cartBadge) {
        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                if (mutation.type === 'childList') {
                    cartBadge.style.animation = 'none';
                    setTimeout(() => {
                        cartBadge.style.animation = 'cartBounce 0.5s ease';
                    }, 10);
                }
            });
        });

        observer.observe(cartBadge, { childList: true });
    }

    // Quantity controls in cart
    const qtyControls = document.querySelectorAll('.qty-decrease, .qty-increase');
    qtyControls.forEach(button => {
        button.addEventListener('click', function () {
            const input = button.classList.contains('qty-decrease')
                ? button.nextElementSibling
                : button.previousElementSibling;

            const currentValue = parseInt(input.value);
            const min = parseInt(input.min) || 1;
            const max = parseInt(input.max) || 10;

            if (button.classList.contains('qty-decrease') && currentValue > min) {
                input.value = currentValue - 1;
            } else if (button.classList.contains('qty-increase') && currentValue < max) {
                input.value = currentValue + 1;
            }

            // Trigger change event for real-time updates
            input.dispatchEvent(new Event('change'));
        });
    });

    // Real-time cart total updates
    const cartForm = document.querySelector('#cart form');
    if (cartForm) {
        const quantityInputs = cartForm.querySelectorAll('input[name="quantity"]');
        quantityInputs.forEach(input => {
            input.addEventListener('change', function () {
                updateCartTotals();
            });
        });
    }
}

// Update cart totals in real-time
function updateCartTotals() {
    const cartItems = document.querySelectorAll('.cart-item');
    let subtotal = 0;

    cartItems.forEach(item => {
        const price = parseFloat(item.dataset.price);
        const quantity = parseInt(item.querySelector('input[name="quantity"]').value);
        const itemTotal = price * quantity;

        const subtotalElement = item.querySelector('.item-subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = `$${itemTotal.toFixed(2)}`;
        }

        subtotal += itemTotal;
    });

    // Update totals in summary
    const subtotalElement = document.querySelector('.cart-subtotal');
    const taxElement = document.querySelector('.cart-tax');
    const totalElement = document.querySelector('.cart-total');

    if (subtotalElement) subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
    if (taxElement) {
        const tax = subtotal * 0.085;
        taxElement.textContent = `$${tax.toFixed(2)}`;
    }
    if (totalElement) {
        const total = subtotal * 1.085;
        totalElement.textContent = `$${total.toFixed(2)}`;
    }
}

// Order tracking enhancements
function initializeOrderTracking() {
    // Auto-refresh functionality for active orders
    const orderStatus = document.querySelector('.badge');
    if (orderStatus && isActiveOrderStatus(orderStatus.textContent)) {
        // Refresh every 30 seconds for active orders
        setTimeout(() => {
            location.reload();
        }, 30000);
    }

    // Progress step animations
    const progressSteps = document.querySelectorAll('.progress-step');
    progressSteps.forEach((step, index) => {
        setTimeout(() => {
            step.style.opacity = '0';
            step.style.transform = 'translateY(20px)';
            step.style.transition = 'all 0.5s ease';

            setTimeout(() => {
                step.style.opacity = '1';
                step.style.transform = 'translateY(0)';
            }, 50);
        }, index * 200);
    });
}

// Check if order status is active (needs tracking)
function isActiveOrderStatus(status) {
    const activeStatuses = ['pending', 'preparing', 'ready', 'out-for-delivery'];
    return activeStatuses.includes(status.toLowerCase().replace(' ', '-'));
}

// Utility function to show custom alerts
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container') || document.body;
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show mt-3`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.insertAdjacentElement('afterbegin', alertElement);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

// Utility function to format currency
function formatCurrency(amount) {
    return '₱' + parseFloat(amount).toFixed(2);
}

// Utility function to debounce events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Handle network errors gracefully
window.addEventListener('online', function () {
    showAlert('Connection restored!', 'success');
});

window.addEventListener('offline', function () {
    showAlert('You are currently offline. Some features may not work properly.', 'warning');
});

// Handle form submission errors
window.addEventListener('error', function (e) {
    console.error('JavaScript error:', e.error);

    // Show user-friendly error message for form-related errors
    if (e.error && e.error.stack && e.error.stack.includes('form')) {
        showAlert('Something went wrong with the form submission. Please try again.', 'danger');
    }
});

// Export utility functions for potential use by other scripts
window.ResortCafe = {
    showAlert,
    formatCurrency,
    debounce,
    validateField,
    updateCartTotals
};
