const CACHE_NAME = 'jcsgo-church-v30';
const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/css/mobile.css',
  '/static/css/components/navbar.css',
  '/static/css/components/sidebar.css',
  '/static/css/components/footer.css',
  '/static/css/components/messages.css',
  '/static/css/pages/dashboard.css',
  '/static/css/pages/church_selection.css',
  '/static/css/pages/church_login.css',
  '/static/css/pages/church_registration.css',
  '/static/css/pages/new_friends.css',
  '/static/css/pages/all_members.css',
  '/static/js/main.js',
  '/static/js/components/main.js',
  '/static/js/pages/new_friends.js',
  '/static/js/pages/all_members.js',
  '/static/image/JCSGO_logo.png',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  const isLogoutPage = url.pathname.includes('/logout/');
  const isAuthPage = url.pathname.includes('/login/') || 
                     url.pathname.includes('/register/') || 
                     url.pathname.includes('/super-admin/login/');
  const isPostRequest = event.request.method === 'POST';
  const isPutRequest = event.request.method === 'PUT';
  const isDeleteRequest = event.request.method === 'DELETE';
  const isPatchRequest = event.request.method === 'PATCH';
  const isApiRequest = url.pathname.includes('/ajax/') || url.pathname.includes('/api/');
  const isNavigationRequest = event.request.mode === 'navigate';
  const isRootPath = url.pathname === '/' || url.pathname === '';
  
  if (isLogoutPage) {
    return;
  }
  
  if (isAuthPage || isPostRequest || isPutRequest || isDeleteRequest || isPatchRequest || isApiRequest) {
    event.respondWith(
      fetch(event.request, {
        credentials: 'include',
        cache: 'no-store'
      })
    );
    return;
  }
  
  if (isNavigationRequest && isRootPath) {
    event.respondWith(
      fetch(event.request).then(response => {
        if (response.status >= 300 && response.status < 400) {
          return response;
        }
        if (response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache);
          });
        }
        return response;
      }).catch(() => {
        return caches.match('/offline/');
      })
    );
    return;
  }
  
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request).then(
          response => {
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            if (response.status >= 300 && response.status < 400) {
              return response;
            }
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });
            return response;
          }
        );
      })
      .catch(() => {
        return caches.match('/offline/');
      })
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

