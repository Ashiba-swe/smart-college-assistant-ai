// Smart College Assistant AI - Main Application Utilities
document.addEventListener('DOMContentLoaded', function () {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Copy to clipboard helper function
function copyToClipboard(elementId, btnElement) {
    const textToCopy = document.getElementById(elementId) ? document.getElementById(elementId).innerText : elementId;
    navigator.clipboard.writeText(textToCopy).then(function() {
        if (btnElement) {
            const originalHtml = btnElement.innerHTML;
            btnElement.innerHTML = '<i class="bi bi-check2"></i> Copied!';
            setTimeout(function() {
                btnElement.innerHTML = originalHtml;
            }, 2000);
        }
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
    });
}
