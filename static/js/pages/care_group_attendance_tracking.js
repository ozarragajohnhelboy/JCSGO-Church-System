document.addEventListener('DOMContentLoaded', function () {
    const dateInput = document.getElementById('attendance_date');
    if (dateInput) {
        dateInput.addEventListener('change', function () {
            if (this.value) {
                window.location.search = '?date=' + encodeURIComponent(this.value);
            }
        });
    }

    const form = document.getElementById('care-group-attendance-form');
    if (!form) {
        return;
    }

    const careGroupBoxes = form.querySelectorAll('.js-care-group-present');
    const sundayBoxes = form.querySelectorAll('.js-sunday-present');
    const actions = form.querySelector('.form-actions');
    if (!actions || (careGroupBoxes.length === 0 && sundayBoxes.length === 0)) {
        return;
    }

    function addToggle(label, boxes) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline-primary btn-sm';
        button.textContent = label;
        button.addEventListener('click', function () {
            const shouldCheck = Array.from(boxes).some(function (box) {
                return !box.checked;
            });
            boxes.forEach(function (box) {
                box.checked = shouldCheck;
            });
        });
        actions.insertBefore(button, actions.firstChild);
    }

    if (sundayBoxes.length) {
        addToggle('Toggle Sunday', sundayBoxes);
    }
    if (careGroupBoxes.length) {
        addToggle('Toggle Care Group', careGroupBoxes);
    }
});
