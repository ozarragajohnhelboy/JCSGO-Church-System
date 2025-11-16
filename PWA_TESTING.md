# PWA Testing Guide

## Quick Test Checklist

### 1. Development Testing

```bash
python manage.py runserver
```

Open sa Chrome at check:
- DevTools > Application > Manifest
- DevTools > Application > Service Workers
- DevTools > Lighthouse > Progressive Web App

### 2. Installation Test

Mobile (Android/iOS):
1. Open sa Chrome/Safari
2. Menu > "Add to Home Screen"
3. Verify app icon sa home screen
4. Open app (dapat standalone mode)

Desktop (Chrome/Edge):
1. Look for install icon sa address bar
2. Click "Install"
3. Verify app window opens

### 3. Offline Test

1. Install app
2. Open app
3. DevTools > Network > Offline
4. Refresh page
5. Verify offline page o cached content

### 4. Mobile Responsive Test

Screen sizes:
- 320px (iPhone SE)
- 375px (iPhone standard)
- 414px (iPhone Plus)
- 768px (Tablet)
- 1024px (Desktop)

Check:
- Sidebar toggle working
- Buttons accessible
- Forms usable
- Tables scrollable

## Browser Testing Matrix

### Full PWA Support
- Chrome Android
- Chrome Desktop
- Edge Desktop
- Samsung Internet

### Limited Support
- Safari iOS (basic features)
- Safari macOS (basic features)
- Firefox (manifest only)

## Common Issues

### Service Worker Not Registering

Error: `Service Worker registration failed`

Solutions:
- Check HTTPS enabled
- Verify service-worker.js accessible
- Clear cache: DevTools > Application > Clear storage
- Check console errors

### Manifest Invalid

Error: `Manifest parsing failed`

Solutions:
- Validate JSON syntax
- Check icon paths correct
- Verify start_url valid
- Check manifest.json accessible

### Install Prompt Not Showing

Reasons:
- Not HTTPS
- Already installed
- Dismissed before
- Browser not supported
- Manifest invalid

Solutions:
- Test sa Chrome
- Clear site data
- Check manifest valid
- Use incognito mode

### Offline Page Not Loading

Solutions:
- Verify Service Worker active
- Check cache strategy
- Test offline.html accessible
- Clear Service Worker cache

## DevTools Testing

### Manifest

Application > Manifest
- Name: JCSGO Church Management System
- Short name: JCSGO Church
- Start URL: /
- Display: standalone
- Icons: Present

### Service Worker

Application > Service Workers
- Status: Activated and running
- Update on reload: Optional
- Bypass for network: Optional

### Cache Storage

Application > Cache Storage
- Cache name: jcsgo-church-v1
- Cached files: CSS, JS, images

### Lighthouse

Run: Lighthouse > Progressive Web App
Target score: 90+

Check:
- Installable
- PWA optimized
- Offline capable
- Fast load

## Mobile Testing Commands

### iOS Safari

1. Settings > Safari > Advanced > Web Inspector
2. Connect iPhone sa Mac
3. Safari > Develop > iPhone > Your site
4. Test installation at features

### Android Chrome

1. chrome://inspect sa desktop
2. Connect Android device
3. Enable USB debugging
4. Inspect mobile browser
5. Test PWA features

## Performance Testing

### Metrics

- First Contentful Paint: < 2s
- Largest Contentful Paint: < 2.5s
- Time to Interactive: < 3.8s
- Cumulative Layout Shift: < 0.1

### Tools

```bash
npm install -g lighthouse
lighthouse http://localhost:8000 --view
```

## Production Deployment

### Pre-deployment Checklist

- [ ] HTTPS configured
- [ ] Service Worker accessible
- [ ] Manifest accessible
- [ ] Icons optimized
- [ ] Meta tags present
- [ ] Offline page ready
- [ ] Cache strategy tested

### Post-deployment Verification

1. Visit site sa production URL
2. Test installation sa mobile
3. Test offline functionality
4. Run Lighthouse audit
5. Test on different devices

## Troubleshooting Script

```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations()
    .then(registrations => {
      console.log('Active Service Workers:', registrations.length);
      registrations.forEach(reg => {
        console.log('SW:', reg);
      });
    });
}

caches.keys()
  .then(names => {
    console.log('Caches:', names);
  });
```

## Clear PWA Data

```javascript
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations()
    .then(registrations => {
      registrations.forEach(reg => reg.unregister());
    });
}

caches.keys()
  .then(names => {
    names.forEach(name => caches.delete(name));
  });
```

## Update Service Worker

1. Update version number sa service-worker.js
2. Update CACHE_NAME
3. Deploy
4. Hard refresh (Ctrl+Shift+R)
5. Verify new SW active

## Browser Support Check

```javascript
const features = {
  serviceWorker: 'serviceWorker' in navigator,
  pushManager: 'PushManager' in window,
  notification: 'Notification' in window,
  sync: 'sync' in window,
};

console.log('PWA Features:', features);
```

