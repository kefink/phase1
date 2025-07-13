/**
 * Hillview School Management System - Service Worker
 * Provides offline functionality, caching, and push notifications
 */

const CACHE_NAME = 'hillview-sms-v1.0.0';
const OFFLINE_URL = '/offline';
const API_CACHE_NAME = 'hillview-api-v1.0.0';
const STATIC_CACHE_NAME = 'hillview-static-v1.0.0';

// Files to cache immediately on install
const CORE_CACHE_FILES = [
  '/',
  '/offline',
  '/static/css/mobile_responsive_dashboard.css',
  '/static/css/style.css',
  '/static/js/script.js',
  '/static/js/pwa-manager.js',
  '/static/manifest.json',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-512x512.png'
];

// Routes to cache for offline access
const OFFLINE_ROUTES = [
  '/classteacher/dashboard',
  '/parent/dashboard',
  '/classteacher/analytics',
  '/teacher/dashboard',
  '/headteacher/dashboard'
];

// API endpoints to cache
const CACHEABLE_API_ROUTES = [
  '/api/analytics/',
  '/api/mobile-performance/',
  '/classteacher/get_',
  '/parent/get_'
];

// Install event - cache core files
self.addEventListener('install', event => {
  console.log('🔧 Service Worker: Installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache core files
      caches.open(STATIC_CACHE_NAME).then(cache => {
        console.log('📦 Service Worker: Caching core files');
        return cache.addAll(CORE_CACHE_FILES);
      }),
      
      // Cache offline routes
      caches.open(CACHE_NAME).then(cache => {
        console.log('📦 Service Worker: Caching offline routes');
        return Promise.all(
          OFFLINE_ROUTES.map(url => {
            return fetch(url).then(response => {
              if (response.ok) {
                return cache.put(url, response);
              }
            }).catch(err => {
              console.warn(`Failed to cache ${url}:`, err);
            });
          })
        );
      })
    ]).then(() => {
      console.log('✅ Service Worker: Installation complete');
      // Skip waiting to activate immediately
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker: Activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== CACHE_NAME && 
                cacheName !== API_CACHE_NAME && 
                cacheName !== STATIC_CACHE_NAME) {
              console.log('🗑️ Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control of all clients
      self.clients.claim()
    ]).then(() => {
      console.log('✅ Service Worker: Activation complete');
    })
  );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests and external URLs
  if (request.method !== 'GET' || !url.origin.includes(self.location.origin)) {
    return;
  }
  
  // Handle different types of requests
  if (isStaticAsset(url.pathname)) {
    event.respondWith(handleStaticAsset(request));
  } else if (isAPIRequest(url.pathname)) {
    event.respondWith(handleAPIRequest(request));
  } else if (isPageRequest(url.pathname)) {
    event.respondWith(handlePageRequest(request));
  }
});

// Check if request is for static asset
function isStaticAsset(pathname) {
  return pathname.startsWith('/static/') || 
         pathname.endsWith('.css') || 
         pathname.endsWith('.js') || 
         pathname.endsWith('.png') || 
         pathname.endsWith('.jpg') || 
         pathname.endsWith('.ico') ||
         pathname === '/manifest.json';
}

// Check if request is for API
function isAPIRequest(pathname) {
  return pathname.startsWith('/api/') || 
         CACHEABLE_API_ROUTES.some(route => pathname.startsWith(route));
}

// Check if request is for a page
function isPageRequest(pathname) {
  return !pathname.startsWith('/static/') && 
         !pathname.startsWith('/api/') &&
         !pathname.includes('.');
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
  try {
    const cache = await caches.open(STATIC_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      // Return cached version and update in background
      updateCacheInBackground(request, cache);
      return cachedResponse;
    }
    
    // Fetch and cache
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
    
  } catch (error) {
    console.warn('Static asset fetch failed:', error);
    // Return cached version if available
    const cache = await caches.open(STATIC_CACHE_NAME);
    return await cache.match(request) || new Response('Asset not available offline');
  }
}

// Handle API requests with network-first strategy
async function handleAPIRequest(request) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      // Cache successful API responses
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.warn('API request failed, trying cache:', error);
    
    // Try to return cached version
    const cache = await caches.open(API_CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline API response
    return new Response(JSON.stringify({
      error: 'Offline',
      message: 'This data is not available offline',
      cached: false
    }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Handle page requests with network-first strategy
async function handlePageRequest(request) {
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      // Cache successful page responses
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
    
  } catch (error) {
    console.warn('Page request failed, trying cache:', error);
    
    // Try to return cached version
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page
    return await caches.match(OFFLINE_URL) || 
           new Response('Page not available offline', { status: 503 });
  }
}

// Update cache in background
async function updateCacheInBackground(request, cache) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      await cache.put(request, response);
    }
  } catch (error) {
    console.warn('Background cache update failed:', error);
  }
}

// Background sync for offline actions
self.addEventListener('sync', event => {
  console.log('🔄 Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'upload-marks') {
    event.waitUntil(syncUploadMarks());
  } else if (event.tag === 'sync-reports') {
    event.waitUntil(syncReports());
  } else if (event.tag === 'sync-analytics') {
    event.waitUntil(syncAnalytics());
  }
});

// Push notification handler
self.addEventListener('push', event => {
  console.log('📱 Service Worker: Push notification received');
  
  let notificationData = {
    title: 'Hillview School',
    body: 'You have a new notification',
    icon: '/static/images/icons/icon-192x192.png',
    badge: '/static/images/icons/icon-72x72.png',
    tag: 'hillview-notification',
    requireInteraction: false,
    actions: [
      {
        action: 'view',
        title: 'View',
        icon: '/static/images/icons/view-action.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/static/images/icons/dismiss-action.png'
      }
    ]
  };
  
  if (event.data) {
    try {
      const data = event.data.json();
      notificationData = { ...notificationData, ...data };
    } catch (error) {
      console.warn('Failed to parse push data:', error);
      notificationData.body = event.data.text() || notificationData.body;
    }
  }
  
  event.waitUntil(
    self.registration.showNotification(notificationData.title, notificationData)
  );
});

// Notification click handler
self.addEventListener('notificationclick', event => {
  console.log('🔔 Service Worker: Notification clicked');
  
  event.notification.close();
  
  const action = event.action;
  const notificationData = event.notification.data || {};
  
  if (action === 'dismiss') {
    return;
  }
  
  // Default action or 'view' action
  let urlToOpen = notificationData.url || '/';
  
  if (action === 'view' && notificationData.viewUrl) {
    urlToOpen = notificationData.viewUrl;
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // Check if there's already a window/tab open with the target URL
      for (const client of clientList) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Open new window/tab
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Sync functions for offline actions
async function syncUploadMarks() {
  try {
    console.log('📊 Service Worker: Syncing uploaded marks...');
    
    // Get pending uploads from IndexedDB
    const pendingUploads = await getPendingUploads('marks');
    
    for (const upload of pendingUploads) {
      try {
        const response = await fetch('/classteacher/upload_marks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(upload.data)
        });
        
        if (response.ok) {
          await removePendingUpload('marks', upload.id);
          console.log('✅ Marks upload synced successfully');
        }
      } catch (error) {
        console.warn('Failed to sync marks upload:', error);
      }
    }
  } catch (error) {
    console.error('Sync upload marks failed:', error);
  }
}

async function syncReports() {
  try {
    console.log('📄 Service Worker: Syncing reports...');
    // Implementation for syncing reports
  } catch (error) {
    console.error('Sync reports failed:', error);
  }
}

async function syncAnalytics() {
  try {
    console.log('📈 Service Worker: Syncing analytics...');
    // Implementation for syncing analytics
  } catch (error) {
    console.error('Sync analytics failed:', error);
  }
}

// Helper functions for IndexedDB operations
async function getPendingUploads(type) {
  // Implementation for getting pending uploads from IndexedDB
  return [];
}

async function removePendingUpload(type, id) {
  // Implementation for removing pending upload from IndexedDB
}

console.log('🚀 Hillview SMS Service Worker loaded successfully');
