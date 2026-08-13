// ==========================================
// AA MART - Admin JavaScript
// ==========================================

document.addEventListener('DOMContentLoaded', function () {

    // Sidebar Toggle
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.admin-sidebar');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth <= 768) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            }
        });
    }

    // Image Preview
    document.querySelectorAll('input[type="file"]').forEach(function (input) {
        input.addEventListener('change', function () {
            const preview = this.closest('.form-group').querySelector('.img-preview');
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                }
                reader.readAsDataURL(this.files[0]);
            }
        });
    });

    // Confirm Delete Actions
    document.querySelectorAll('.btn-delete').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Auto-generate Slug
    const nameInput = document.querySelector('input[name="name"]');
    const slugInput = document.querySelector('input[name="slug"]');

    if (nameInput && slugInput) {
        nameInput.addEventListener('input', function () {
            if (!slugInput.dataset.modified) {
                slugInput.value = this.value
                    .toLowerCase()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/[\s_]+/g, '-')
                    .replace(/^-+|-+$/g, '');
            }
        });

        slugInput.addEventListener('input', function () {
            this.dataset.modified = this.value !== '';
        });
    }

    // Data Table Search
    const searchTable = document.getElementById('tableSearch');
    if (searchTable) {
        searchTable.addEventListener('keyup', function () {
            const query = this.value.toLowerCase();
            const table = document.querySelector('.table-admin');
            if (!table) return;

            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(function (row) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // Select All Checkbox
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.addEventListener('change', function () {
            const checkboxes = document.querySelectorAll('.select-item');
            checkboxes.forEach(function (cb) {
                cb.checked = selectAll.checked;
            });
        });
    }

    // Bulk Action
    const bulkAction = document.getElementById('bulkAction');
    if (bulkAction) {
        bulkAction.addEventListener('change', function () {
            if (this.value) {
                if (confirm(`Apply "${this.value}" to selected items?`)) {
                    document.getElementById('bulkForm').submit();
                }
                this.value = '';
            }
        });
    }

    console.log('AA MART Admin - Loaded Successfully');
});
