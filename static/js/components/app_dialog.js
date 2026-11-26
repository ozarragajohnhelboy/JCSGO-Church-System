(function () {
    function dialogElements() {
        const root = document.getElementById('appDialog');
        if (!root) {
            return null;
        }
        return {
            root: root,
            title: document.getElementById('appDialogTitle'),
            message: document.getElementById('appDialogMessage'),
            confirmBtn: document.getElementById('appDialogConfirm'),
            cancelBtn: document.getElementById('appDialogCancel'),
            content: root.querySelector('.app-dialog'),
        };
    }

    function showDialog(options) {
        const els = dialogElements();
        if (!els || typeof bootstrap === 'undefined') {
            if (options.mode === 'confirm') {
                return Promise.resolve(window.confirm(options.message));
            }
            window.alert(options.message);
            return Promise.resolve(true);
        }

        const settings = options || {};
        els.title.textContent = settings.title || 'Notice';
        els.message.textContent = settings.message || '';
        els.confirmBtn.textContent = settings.confirmLabel || 'OK';
        els.cancelBtn.textContent = settings.cancelLabel || 'Cancel';
        els.cancelBtn.classList.toggle('d-none', settings.mode === 'alert');
        els.content.classList.toggle('app-dialog--danger', Boolean(settings.danger));
        els.confirmBtn.classList.toggle('btn-danger', Boolean(settings.danger));
        els.confirmBtn.classList.toggle('btn-primary', !settings.danger);

        const modal = bootstrap.Modal.getOrCreateInstance(els.root);
        return new Promise(function (resolve) {
            let settled = false;

            function finish(result) {
                if (settled) {
                    return;
                }
                settled = true;
                els.confirmBtn.removeEventListener('click', onConfirm);
                els.root.removeEventListener('hidden.bs.modal', onHidden);
                resolve(result);
            }

            function onConfirm() {
                finish(true);
                modal.hide();
            }

            function onHidden() {
                finish(false);
            }

            els.confirmBtn.addEventListener('click', onConfirm);
            els.root.addEventListener('hidden.bs.modal', onHidden, { once: true });
            modal.show();
        });
    }

    window.appConfirm = function (message, options) {
        const settings = options || {};
        return showDialog({
            mode: 'confirm',
            title: settings.title || 'Please confirm',
            message: message,
            confirmLabel: settings.confirmLabel || 'Confirm',
            cancelLabel: settings.cancelLabel || 'Cancel',
            danger: settings.danger,
        });
    };

    window.showSuccess = window.showSuccess || function (message) {
        return window.appAlert(message, { title: 'Success' });
    };

    window.showError = window.showError || function (message) {
        return window.appAlert(message, { title: 'Error', danger: true });
    };

    window.appAlert = function (message, options) {
        const settings = options || {};
        return showDialog({
            mode: 'alert',
            title: settings.title || 'Notice',
            message: message,
            confirmLabel: settings.confirmLabel || 'OK',
            danger: settings.danger,
        });
    };

    document.addEventListener('submit', function (event) {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }
        const message = form.getAttribute('data-confirm');
        if (!message || form.dataset.confirmed === '1') {
            return;
        }
        event.preventDefault();
        window.appConfirm(message, {
            title: form.getAttribute('data-confirm-title') || 'Please confirm',
            confirmLabel: form.getAttribute('data-confirm-label') || 'Confirm',
            cancelLabel: form.getAttribute('data-confirm-cancel') || 'Cancel',
            danger: form.getAttribute('data-confirm-danger') === '1',
        }).then(function (ok) {
            if (!ok) {
                return;
            }
            form.dataset.confirmed = '1';
            form.submit();
        });
    });
})();
