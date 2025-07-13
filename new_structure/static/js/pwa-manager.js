/**
 * PWA Manager for Hillview School Management System
 * Handles service worker registration, install prompts, and PWA features
 */

class PWAManager {
  constructor() {
    this.deferredPrompt = null;
    this.isInstalled = false;
    this.isOnline = navigator.onLine;
    this.serviceWorkerRegistration = null;
    
    this.init();
  }
  
  async init() {
    console.log('🚀 PWA Manager: Initializing...');
    
    // Check if PWA is already installed
    this.checkInstallStatus();
    
    // Register service worker
    await this.registerServiceWorker();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Setup install prompt
    this.setupInstallPrompt();
    
    // Setup push notifications
    this.setupPushNotifications();
    
    // Setup offline detection
    this.setupOfflineDetection();
    
    console.log('✅ PWA Manager: Initialized successfully');
  }
  
  checkInstallStatus() {
    // Check if running in standalone mode (installed)
    this.isInstalled = window.matchMedia('(display-mode: standalone)').matches ||
                      window.navigator.standalone === true;
    
    if (this.isInstalled) {
      console.log('📱 PWA Manager: App is installed');
      this.hideInstallPrompt();
    }
  }
  
  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/static/sw.js', {
          scope: '/'
        });
        
        console.log('✅ PWA Manager: Service Worker registered successfully');
        
        // Handle service worker updates
        this.serviceWorkerRegistration.addEventListener('updatefound', () => {
          console.log('🔄 PWA Manager: Service Worker update found');
          this.handleServiceWorkerUpdate();
        });
        
        // Check for updates
        this.serviceWorkerRegistration.update();
        
      } catch (error) {
        console.error('❌ PWA Manager: Service Worker registration failed:', error);
      }
    } else {
      console.warn('⚠️ PWA Manager: Service Workers not supported');
    }
  }
  
  setupEventListeners() {
    // Install prompt event
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('📱 PWA Manager: Install prompt available');
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallPrompt();
    });
    
    // App installed event
    window.addEventListener('appinstalled', () => {
      console.log('✅ PWA Manager: App installed successfully');
      this.isInstalled = true;
      this.hideInstallPrompt();
      this.showInstallSuccessMessage();
    });
    
    // Visibility change (app focus/blur)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        this.handleAppFocus();
      }
    });
  }
  
  setupInstallPrompt() {
    // Create install prompt UI
    const installPrompt = document.createElement('div');
    installPrompt.id = 'pwa-install-prompt';
    installPrompt.className = 'pwa-install-prompt hidden';
    installPrompt.innerHTML = `
      <div class="install-prompt-content">
        <div class="install-prompt-icon">
          <i class="fas fa-mobile-alt"></i>
        </div>
        <div class="install-prompt-text">
          <h3>Install Hillview SMS</h3>
          <p>Get quick access and work offline</p>
        </div>
        <div class="install-prompt-actions">
          <button id="install-app-btn" class="btn-install">
            <i class="fas fa-download"></i> Install
          </button>
          <button id="dismiss-install-btn" class="btn-dismiss">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `;
    
    document.body.appendChild(installPrompt);
    
    // Add event listeners
    document.getElementById('install-app-btn').addEventListener('click', () => {
      this.installApp();
    });
    
    document.getElementById('dismiss-install-btn').addEventListener('click', () => {
      this.dismissInstallPrompt();
    });
  }
  
  showInstallPrompt() {
    if (this.isInstalled) return;
    
    const prompt = document.getElementById('pwa-install-prompt');
    if (prompt) {
      prompt.classList.remove('hidden');
      
      // Auto-hide after 10 seconds
      setTimeout(() => {
        this.hideInstallPrompt();
      }, 10000);
    }
  }
  
  hideInstallPrompt() {
    const prompt = document.getElementById('pwa-install-prompt');
    if (prompt) {
      prompt.classList.add('hidden');
    }
  }
  
  async installApp() {
    if (!this.deferredPrompt) {
      console.warn('⚠️ PWA Manager: No install prompt available');
      return;
    }
    
    try {
      // Show the install prompt
      this.deferredPrompt.prompt();
      
      // Wait for user response
      const { outcome } = await this.deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        console.log('✅ PWA Manager: User accepted install');
      } else {
        console.log('❌ PWA Manager: User dismissed install');
      }
      
      // Clear the deferred prompt
      this.deferredPrompt = null;
      this.hideInstallPrompt();
      
    } catch (error) {
      console.error('❌ PWA Manager: Install failed:', error);
    }
  }
  
  dismissInstallPrompt() {
    this.hideInstallPrompt();
    
    // Don't show again for this session
    sessionStorage.setItem('pwa-install-dismissed', 'true');
  }
  
  async setupPushNotifications() {
    if (!('Notification' in window) || !this.serviceWorkerRegistration) {
      console.warn('⚠️ PWA Manager: Push notifications not supported');
      return;
    }
    
    // Check current permission
    let permission = Notification.permission;
    
    if (permission === 'default') {
      // Request permission when user interacts with the app
      this.setupNotificationPermissionRequest();
    } else if (permission === 'granted') {
      console.log('✅ PWA Manager: Notification permission granted');
      await this.subscribeToPushNotifications();
    }
  }
  
  setupNotificationPermissionRequest() {
    // Add click listener to request permission on user interaction
    document.addEventListener('click', async () => {
      if (Notification.permission === 'default') {
        const permission = await Notification.requestPermission();
        
        if (permission === 'granted') {
          console.log('✅ PWA Manager: Notification permission granted');
          await this.subscribeToPushNotifications();
        }
      }
    }, { once: true });
  }
  
  async subscribeToPushNotifications() {
    try {
      // Check if already subscribed
      const existingSubscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
      
      if (existingSubscription) {
        console.log('✅ PWA Manager: Already subscribed to push notifications');
        return;
      }
      
      // Subscribe to push notifications
      const subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.getVapidPublicKey())
      });
      
      // Send subscription to server
      await this.sendSubscriptionToServer(subscription);
      
      console.log('✅ PWA Manager: Subscribed to push notifications');
      
    } catch (error) {
      console.error('❌ PWA Manager: Push subscription failed:', error);
    }
  }
  
  getVapidPublicKey() {
    // This should be your VAPID public key
    // For demo purposes, using a placeholder
    return 'BEl62iUYgUivxIkv69yViEuiBIa40HI80NqIUHI80NqIUHI80NqIUHI80NqIUHI80NqIUHI80NqIUHI80NqIUHI80NqI';
  }
  
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
  
  async sendSubscriptionToServer(subscription) {
    try {
      const response = await fetch('/api/push-subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(subscription)
      });
      
      if (!response.ok) {
        throw new Error('Failed to send subscription to server');
      }
      
    } catch (error) {
      console.error('❌ PWA Manager: Failed to send subscription:', error);
    }
  }
  
  setupOfflineDetection() {
    window.addEventListener('online', () => {
      console.log('🌐 PWA Manager: Back online');
      this.isOnline = true;
      this.hideOfflineIndicator();
      this.syncOfflineData();
    });
    
    window.addEventListener('offline', () => {
      console.log('📴 PWA Manager: Gone offline');
      this.isOnline = false;
      this.showOfflineIndicator();
    });
    
    // Initial check
    if (!this.isOnline) {
      this.showOfflineIndicator();
    }
  }
  
  showOfflineIndicator() {
    let indicator = document.getElementById('offline-indicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'offline-indicator';
      indicator.className = 'offline-indicator';
      indicator.innerHTML = `
        <i class="fas fa-wifi-slash"></i>
        <span>You're offline. Some features may be limited.</span>
      `;
      document.body.appendChild(indicator);
    }
    
    indicator.classList.add('show');
  }
  
  hideOfflineIndicator() {
    const indicator = document.getElementById('offline-indicator');
    if (indicator) {
      indicator.classList.remove('show');
    }
  }
  
  async syncOfflineData() {
    if ('serviceWorker' in navigator && this.serviceWorkerRegistration) {
      try {
        // Trigger background sync
        await this.serviceWorkerRegistration.sync.register('sync-offline-data');
        console.log('🔄 PWA Manager: Background sync registered');
      } catch (error) {
        console.error('❌ PWA Manager: Background sync failed:', error);
      }
    }
  }
  
  handleServiceWorkerUpdate() {
    // Show update available notification
    this.showUpdateAvailableNotification();
  }
  
  showUpdateAvailableNotification() {
    const notification = document.createElement('div');
    notification.className = 'update-notification';
    notification.innerHTML = `
      <div class="update-content">
        <i class="fas fa-sync-alt"></i>
        <span>A new version is available!</span>
        <button id="update-app-btn">Update</button>
        <button id="dismiss-update-btn">Later</button>
      </div>
    `;
    
    document.body.appendChild(notification);
    
    document.getElementById('update-app-btn').addEventListener('click', () => {
      window.location.reload();
    });
    
    document.getElementById('dismiss-update-btn').addEventListener('click', () => {
      notification.remove();
    });
  }
  
  handleAppFocus() {
    // Check for updates when app comes back into focus
    if (this.serviceWorkerRegistration) {
      this.serviceWorkerRegistration.update();
    }
  }
  
  showInstallSuccessMessage() {
    const message = document.createElement('div');
    message.className = 'install-success-message';
    message.innerHTML = `
      <div class="success-content">
        <i class="fas fa-check-circle"></i>
        <span>Hillview SMS installed successfully!</span>
      </div>
    `;
    
    document.body.appendChild(message);
    
    setTimeout(() => {
      message.remove();
    }, 5000);
  }
  
  // Public methods for app integration
  async cacheImportantData(data, key) {
    if ('caches' in window) {
      try {
        const cache = await caches.open('hillview-app-data');
        const response = new Response(JSON.stringify(data));
        await cache.put(key, response);
        console.log(`✅ PWA Manager: Cached data for ${key}`);
      } catch (error) {
        console.error('❌ PWA Manager: Failed to cache data:', error);
      }
    }
  }
  
  async getCachedData(key) {
    if ('caches' in window) {
      try {
        const cache = await caches.open('hillview-app-data');
        const response = await cache.match(key);
        
        if (response) {
          const data = await response.json();
          console.log(`✅ PWA Manager: Retrieved cached data for ${key}`);
          return data;
        }
      } catch (error) {
        console.error('❌ PWA Manager: Failed to get cached data:', error);
      }
    }
    
    return null;
  }
}

// Initialize PWA Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.pwaManager = new PWAManager();
});

// Export for use in other scripts
window.PWAManager = PWAManager;
