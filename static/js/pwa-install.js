let deferredPrompt = null;

window.addEventListener('load', () => {
  registerServiceWorker();
  setupInstallPrompt();
});

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js').catch(() => {});
  }
}

function isStandalone() {
  return window.matchMedia('(display-mode: standalone)').matches
    || window.navigator.standalone === true;
}

function wasDismissed() {
  return localStorage.getItem('pwa-install-dismissed') === 'true';
}

function canOfferInstall() {
  return !isStandalone() && !wasDismissed();
}

function showBar(bar) {
  if (!bar || !canOfferInstall()) return;
  bar.hidden = false;
  bar.classList.add('is-visible');
}

function hideBar(bar) {
  if (!bar) return;
  bar.hidden = true;
  bar.classList.remove('is-visible');
}

async function promptInstall() {
  if (!deferredPrompt) return false;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  return true;
}

function setupInstallPrompt() {
  const bar = document.getElementById('pwa-install-container');
  const installButton = document.getElementById('pwa-install-button');
  const dismissButton = document.getElementById('pwa-dismiss-button');
  const settingsButton = document.getElementById('pwa-install-settings');
  const settingsHint = document.getElementById('pwa-install-settings-hint');

  hideBar(bar);

  if (isStandalone()) {
    if (settingsHint) {
      settingsHint.textContent = 'This app is already installed on this device.';
    }
    return;
  }

  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    deferredPrompt = event;
    if (canOfferInstall()) {
      showBar(bar);
    }
    if (settingsButton) {
      settingsButton.classList.remove('d-none');
    }
    if (settingsHint) {
      settingsHint.classList.add('d-none');
    }
  });

  if (installButton) {
    installButton.addEventListener('click', async () => {
      await promptInstall();
      hideBar(bar);
    });
  }

  if (dismissButton) {
    dismissButton.addEventListener('click', () => {
      localStorage.setItem('pwa-install-dismissed', 'true');
      hideBar(bar);
    });
  }

  if (settingsButton) {
    settingsButton.addEventListener('click', async () => {
      const prompted = await promptInstall();
      if (!prompted) {
        settingsHint.classList.remove('d-none');
        settingsHint.textContent = 'Use your browser menu to add this app to your home screen.';
      }
    });
  }

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    hideBar(bar);
    if (settingsHint) {
      settingsHint.classList.remove('d-none');
      settingsHint.textContent = 'This app is already installed on this device.';
    }
    if (settingsButton) {
      settingsButton.classList.add('d-none');
    }
  });
}
