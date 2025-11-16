let deferredPrompt;
let installButton;

window.addEventListener('load', () => {
  registerServiceWorker();
  setupInstallPrompt();
});

function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('Service Worker registered');
      })
      .catch(error => {
        console.log('Service Worker registration failed');
      });
  }
}

function setupInstallPrompt() {
  const installContainer = document.getElementById('pwa-install-container');
  installButton = document.getElementById('pwa-install-button');
  const dismissButton = document.getElementById('pwa-dismiss-button');

  if (!installContainer || !installButton) return;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installContainer.style.display = 'block';
  });

  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('PWA installed');
    }
    
    deferredPrompt = null;
    installContainer.style.display = 'none';
  });

  if (dismissButton) {
    dismissButton.addEventListener('click', () => {
      installContainer.style.display = 'none';
      localStorage.setItem('pwa-install-dismissed', 'true');
    });
  }

  window.addEventListener('appinstalled', () => {
    console.log('PWA installed successfully');
    installContainer.style.display = 'none';
  });

  if (localStorage.getItem('pwa-install-dismissed') === 'true') {
    installContainer.style.display = 'none';
  }
}

