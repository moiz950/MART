// ==========================================
// AA MART - Main JavaScript
// ==========================================

document.addEventListener('DOMContentLoaded', function () {

    // Back to Top Button
    const backToTop = document.getElementById('backToTop');
    if (backToTop) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 300) {
                backToTop.classList.add('show');
            } else {
                backToTop.classList.remove('show');
            }
        });

        backToTop.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Sticky Header
    const header = document.getElementById('mainHeader');
    if (header) {
        window.addEventListener('scroll', function () {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // Auto-hide Flash Messages
    const alerts = document.querySelectorAll('.flash-alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.remove('show');
            setTimeout(function () {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Product Image Zoom
    const mainImage = document.getElementById('mainProductImage');
    if (mainImage) {
        mainImage.addEventListener('mousemove', function (e) {
            const rect = this.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width * 100;
            const y = (e.clientY - rect.top) / rect.height * 100;
            this.style.transformOrigin = `${x}% ${y}%`;
            this.style.transform = 'scale(1.5)';
        });

        mainImage.addEventListener('mouseleave', function () {
            this.style.transform = 'scale(1)';
        });
    }

    // Quantity Input Validation
    document.querySelectorAll('.quantity-selector input').forEach(function (input) {
        input.addEventListener('change', function () {
            let val = parseInt(this.value);
            const min = parseInt(this.min) || 1;
            const max = parseInt(this.max) || 99;
            if (isNaN(val) || val < min) this.value = min;
            if (val > max) this.value = max;
        });
    });

    // Rating Stars Interaction
    document.querySelectorAll('.rating-input i').forEach(function (star) {
        star.addEventListener('click', function () {
            const rating = this.dataset.rating;
            const container = this.closest('.rating-input');
            container.querySelectorAll('i').forEach(function (s, index) {
                if (index < rating) {
                    s.classList.remove('far');
                    s.classList.add('fas');
                } else {
                    s.classList.remove('fas');
                    s.classList.add('far');
                }
            });
            container.querySelector('input[type="hidden"]').value = rating;
        });
    });

    // Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href !== '#') {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });

    // Add to Cart Animation
    document.querySelectorAll('.btn-add-cart').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            const form = this.closest('form');
            if (form) return; // Let form submit naturally

            this.innerHTML = '<i class="fas fa-check me-2"></i>Added!';
            this.classList.add('btn-success');
            setTimeout(() => {
                this.innerHTML = '<i class="fas fa-shopping-cart me-2"></i>Add to Cart';
                this.classList.remove('btn-success');
            }, 2000);
        });
    });

    // Countdown Timer for Flash Sales
    document.querySelectorAll('.countdown-timer').forEach(function (timer) {
        const endDate = new Date(timer.dataset.end).getTime();

        function updateCountdown() {
            const now = new Date().getTime();
            const distance = endDate - now;

            if (distance < 0) {
                timer.innerHTML = 'Sale Ended';
                return;
            }

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            timer.querySelector('.days').textContent = String(days).padStart(2, '0');
            timer.querySelector('.hours').textContent = String(hours).padStart(2, '0');
            timer.querySelector('.minutes').textContent = String(minutes).padStart(2, '0');
            timer.querySelector('.seconds').textContent = String(seconds).padStart(2, '0');
        }

        updateCountdown();
        setInterval(updateCountdown, 1000);
    });

    // Live Search Suggestions
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            if (query.length < 2) {
                document.querySelector('.search-suggestions')?.remove();
                return;
            }

            searchTimeout = setTimeout(() => {
                fetch(`/search/suggestions?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        // Handle suggestions display
                    });
            }, 500);
        });
    }

    // Payment Method Selection
    document.querySelectorAll('input[name="payment_method"]').forEach(function (input) {
        input.addEventListener('change', function () {
            document.querySelectorAll('.payment-option').forEach(function (opt) {
                opt.classList.remove('active');
            });
            this.closest('.payment-option').classList.add('active');
        });
    });

    // Address Selection
    document.querySelectorAll('input[name="shipping_address"]').forEach(function (input) {
        input.addEventListener('change', function () {
            document.querySelectorAll('.address-card').forEach(function (card) {
                card.classList.remove('selected');
            });
            this.closest('.address-card').classList.add('selected');
        });
    });

    console.log('AA MART - Loaded Successfully');
});
