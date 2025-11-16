# Progressive Web App (PWA) Implementation

## Overview

Ang JCSGO Church Management System ay may PWA features na para sa mobile at desktop installation.

## Features

### 1. Installable App
- Pwedeng i-install sa mobile at desktop
- Standalone mode para sa native app experience
- Custom splash screen gamit ang app icon at theme color

### 2. Offline Support
- Service Worker para sa caching ng assets
- Offline page kapag walang internet
- Background sync capabilities

### 3. Mobile Responsive
- Optimized para sa lahat ng screen sizes
- Touch-friendly buttons at controls
- Mobile-first navigation

### 4. App-like Experience
- Fullscreen mode (no browser chrome)
- Custom theme colors
- Native app feel

## Files Created

### Static Files
- `static/manifest.json` - Web App Manifest
- `static/service-worker.js` - Service Worker para sa caching
- `static/js/pwa-install.js` - Install prompt handler
- `static/css/mobile.css` - Mobile responsive styles

### Django Files
- `churches/views/pwa_views.py` - PWA views (manifest, service worker, offline)
- `templates/pwa/offline.html` - Offline fallback page

### Updated Files
- `templates/base.html` - Added PWA meta tags at install prompt
- `churches/views/__init__.py` - Export PWA views
- `churches/urls.py` - PWA routes

## How to Use

### Installation on Mobile

1. Open sa mobile browser (Chrome, Safari, Edge)
2. Visit ang site
3. Click ang "Install" button sa popup o
4. Sa browser menu, select "Add to Home Screen" o "Install App"
5. App icon lalabas sa home screen

### Installation on Desktop

1. Open sa browser (Chrome, Edge)
2. Look for install icon sa address bar
3. Click "Install" button
4. App lalabas bilang standalone window

### Offline Mode

1. I-install ang app
2. Open ang app at least once
3. Kapag nawala ang internet, makikita ang offline page
4. Cached pages ay accessible pa rin

## Technical Details

### Service Worker Caching

Naka-cache ang mga sumusunod:
- CSS files (style.css, components)
- JavaScript files (main.js, pwa-install.js)
- Images (JCSGO logo)
- Manifest file

### PWA Meta Tags

```html
<meta name="theme-color" content="#667eea">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="/manifest.json">
```

### Routes

- `/manifest.json` - Web App Manifest
- `/service-worker.js` - Service Worker file
- `/offline/` - Offline fallback page

## Browser Support

### Full Support
- Chrome (Desktop & Mobile)
- Edge (Desktop & Mobile)
- Samsung Internet
- Opera

### Partial Support
- Safari (iOS & macOS) - Limited PWA features
- Firefox - Manifest support only

## Testing

### Local Testing

1. Run development server
```bash
python manage.py runserver
```

2. Open sa Chrome
3. Open DevTools > Application > Manifest
4. Check service worker registration

### Production Testing

1. Deploy sa HTTPS server (required for PWA)
2. Test installation sa different devices
3. Test offline functionality
4. Check Lighthouse PWA score

## Deployment Notes

### Requirements
- HTTPS enabled (mandatory for PWA)
- Service Worker dapat accessible sa root level
- Manifest file dapat valid JSON
- Icons dapat available

### Production Checklist
- [ ] HTTPS configured
- [ ] Service Worker registered
- [ ] Manifest validated
- [ ] Icons accessible
- [ ] Meta tags present
- [ ] Install prompt working
- [ ] Offline page functional

## Troubleshooting

### Service Worker Not Registering
- Check HTTPS enabled
- Check service-worker.js path
- Clear browser cache
- Check DevTools Console for errors

### Install Prompt Not Showing
- Ensure HTTPS
- Check manifest.json valid
- Ensure icons accessible
- Try different browser
- Check install criteria met

### Offline Mode Not Working
- Check Service Worker registered
- Verify caching strategy
- Test network offline simulation
- Check offline.html exists

## Future Enhancements

- Push notifications
- Background sync for form submissions
- Periodic background sync
- Share target API
- Shortcuts to specific features
- Badge API for notifications

