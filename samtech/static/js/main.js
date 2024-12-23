// Enable Bootstrap tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // File input validation
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            var fileName = e.target.files[0].name;
            var fileSize = e.target.files[0].size;
            var maxSize = 100 * 1024 * 1024; // 100MB

            if (fileSize > maxSize) {
                alert('File size must be less than 100MB');
                e.target.value = '';
            }
        });
    });

    // Password strength indicator
    var passwordInput = document.querySelector('input[type="password"]');
    if (passwordInput) {
        passwordInput.addEventListener('input', function(e) {
            var password = e.target.value;
            var strength = 0;
            
            if (password.length >= 8) strength++;
            if (password.match(/[a-z]/)) strength++;
            if (password.match(/[A-Z]/)) strength++;
            if (password.match(/[0-9]/)) strength++;
            if (password.match(/[^a-zA-Z0-9]/)) strength++;

            var feedback = '';
            switch(strength) {
                case 0:
                case 1:
                    feedback = 'Weak';
                    break;
                case 2:
                case 3:
                    feedback = 'Medium';
                    break;
                case 4:
                case 5:
                    feedback = 'Strong';
                    break;
            }

            var feedbackElement = document.getElementById('password-strength');
            if (!feedbackElement) {
                feedbackElement = document.createElement('div');
                feedbackElement.id = 'password-strength';
                feedbackElement.className = 'form-text';
                passwordInput.parentNode.appendChild(feedbackElement);
            }
            feedbackElement.textContent = 'Password strength: ' + feedback;
        });
    }
});
