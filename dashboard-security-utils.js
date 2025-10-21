/**
 * R2D2 Dashboard Security Utilities
 *
 * Comprehensive security library for XSS prevention, CSRF protection,
 * authentication management, and memory leak prevention.
 *
 * @author Web Development Specialist
 * @date 2025-10-20
 * @version 1.0.0
 */

// ============================================================================
// 1. XSS PREVENTION
// ============================================================================

/**
 * Sanitize HTML by escaping dangerous characters
 * Prevents XSS attacks by converting HTML special characters to entities
 *
 * @param {string} str - Unsanitized string that may contain HTML
 * @returns {string} - Sanitized string safe for innerHTML
 *
 * @example
 * sanitizeHTML("<script>alert('xss')</script>")
 * // Returns: "&lt;script&gt;alert('xss')&lt;/script&gt;"
 */
function sanitizeHTML(str) {
    if (typeof str !== 'string') return '';

    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
        '/': '&#x2F;'
    };

    return str.replace(/[&<>"'/]/g, (char) => map[char]);
}

/**
 * Safely set text content without HTML interpretation
 * Recommended for all user-generated content display
 *
 * @param {HTMLElement} element - Target DOM element
 * @param {string} text - Text content to display
 * @returns {boolean} - Success status
 */
function setTextContent(element, text) {
    if (!element) {
        console.warn('setTextContent: Element is null or undefined');
        return false;
    }

    element.textContent = String(text);
    return true;
}

/**
 * Set HTML content with automatic sanitization
 * Use only when HTML rendering is absolutely necessary
 *
 * @param {HTMLElement} element - Target DOM element
 * @param {string} html - HTML content to sanitize and display
 * @returns {boolean} - Success status
 */
function setHTMLContent(element, html) {
    if (!element) {
        console.warn('setHTMLContent: Element is null or undefined');
        return false;
    }

    element.innerHTML = sanitizeHTML(html);
    return true;
}

/**
 * Create safe DOM element with sanitized attributes
 *
 * @param {string} tagName - HTML tag name
 * @param {Object} attributes - Element attributes (will be sanitized)
 * @param {string} textContent - Text content (safe, not HTML)
 * @returns {HTMLElement} - Created element
 */
function createSafeElement(tagName, attributes = {}, textContent = '') {
    const element = document.createElement(tagName);

    // Set sanitized attributes
    Object.keys(attributes).forEach(key => {
        const value = attributes[key];
        if (key === 'style' && typeof value === 'object') {
            Object.assign(element.style, value);
        } else if (key.startsWith('data-')) {
            element.setAttribute(key, sanitizeHTML(String(value)));
        } else if (key === 'className' || key === 'class') {
            element.className = sanitizeHTML(String(value));
        } else {
            element[key] = sanitizeHTML(String(value));
        }
    });

    // Set text content safely
    if (textContent) {
        element.textContent = textContent;
    }

    return element;
}

// ============================================================================
// 2. CSRF PROTECTION
// ============================================================================

/**
 * CSRF Token Manager
 * Generates and manages CSRF tokens for form and API protection
 */
class CSRFTokenManager {
    constructor() {
        this.token = this.generateToken();
        this.tokenKey = 'r2d2_csrf_token';
        this.loadOrGenerateToken();
    }

    /**
     * Generate cryptographically secure CSRF token
     * @returns {string} - Generated token
     */
    generateToken() {
        // Use crypto.getRandomValues for secure random generation
        if (window.crypto && window.crypto.getRandomValues) {
            const array = new Uint8Array(32);
            window.crypto.getRandomValues(array);
            return 'csrf_' + Array.from(array, byte =>
                byte.toString(16).padStart(2, '0')
            ).join('');
        }

        // Fallback for older browsers
        return 'csrf_' + Math.random().toString(36).substr(2, 16) +
               Date.now().toString(36);
    }

    /**
     * Load existing token from sessionStorage or generate new one
     */
    loadOrGenerateToken() {
        try {
            const stored = sessionStorage.getItem(this.tokenKey);
            if (stored && stored.startsWith('csrf_')) {
                this.token = stored;
            } else {
                this.token = this.generateToken();
                sessionStorage.setItem(this.tokenKey, this.token);
            }
        } catch (e) {
            console.warn('sessionStorage unavailable, using in-memory token');
            this.token = this.generateToken();
        }
    }

    /**
     * Get current CSRF token
     * @returns {string} - Current token
     */
    getToken() {
        return this.token;
    }

    /**
     * Refresh CSRF token (call after successful request)
     * @returns {string} - New token
     */
    refreshToken() {
        this.token = this.generateToken();
        try {
            sessionStorage.setItem(this.tokenKey, this.token);
        } catch (e) {
            console.warn('Could not store new CSRF token');
        }
        return this.token;
    }

    /**
     * Validate CSRF token from server response
     * @param {string} serverToken - Token from server
     * @returns {boolean} - Valid or not
     */
    validateToken(serverToken) {
        return serverToken === this.token;
    }
}

// ============================================================================
// 3. AUTHENTICATION MANAGEMENT
// ============================================================================

/**
 * Authentication Header Manager
 * Manages authentication tokens and headers for API requests
 */
class AuthHeaderManager {
    constructor(authToken = null) {
        this.authToken = authToken;
        this.tokenKey = 'r2d2_auth_token';
        this.tokenExpiryKey = 'r2d2_auth_expiry';

        // Try to load token from storage if not provided
        if (!this.authToken) {
            this.loadToken();
        }
    }

    /**
     * Load authentication token from localStorage
     */
    loadToken() {
        try {
            this.authToken = localStorage.getItem(this.tokenKey);

            // Check if token is expired
            const expiry = localStorage.getItem(this.tokenExpiryKey);
            if (expiry && Date.now() > parseInt(expiry)) {
                console.warn('Auth token expired');
                this.clearToken();
            }
        } catch (e) {
            console.warn('Could not load auth token from storage');
        }
    }

    /**
     * Set authentication token
     * @param {string} token - Authentication token
     * @param {number} expiryMs - Token expiry in milliseconds (optional)
     */
    setToken(token, expiryMs = null) {
        this.authToken = token;

        try {
            localStorage.setItem(this.tokenKey, token);

            if (expiryMs) {
                const expiryTime = Date.now() + expiryMs;
                localStorage.setItem(this.tokenExpiryKey, expiryTime.toString());
            }
        } catch (e) {
            console.warn('Could not store auth token');
        }
    }

    /**
     * Clear authentication token
     */
    clearToken() {
        this.authToken = null;
        try {
            localStorage.removeItem(this.tokenKey);
            localStorage.removeItem(this.tokenExpiryKey);
        } catch (e) {
            console.warn('Could not clear auth token from storage');
        }
    }

    /**
     * Get authentication token
     * @returns {string|null} - Current token or null
     */
    getToken() {
        return this.authToken;
    }

    /**
     * Check if user is authenticated
     * @returns {boolean} - True if authenticated
     */
    isAuthenticated() {
        return !!this.authToken;
    }

    /**
     * Get complete headers object with auth and CSRF
     * @param {Object} additionalHeaders - Additional headers to include
     * @returns {Object} - Complete headers object
     */
    getHeaders(additionalHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...additionalHeaders
        };

        // Add auth header if token exists
        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        // Add CSRF token if manager exists
        if (typeof csrfManager !== 'undefined') {
            headers['X-CSRF-Token'] = csrfManager.getToken();
        }

        return headers;
    }
}

// ============================================================================
// 4. SECURE FETCH WRAPPER
// ============================================================================

/**
 * Secure fetch wrapper with automatic auth, CSRF, and error handling
 *
 * @param {string} url - Request URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Response|null>} - Response or null on error
 */
async function secureFetch(url, options = {}) {
    try {
        // Get auth manager instance
        const authMgr = typeof authManager !== 'undefined' ? authManager : null;

        if (!authMgr || !authMgr.isAuthenticated()) {
            console.error('secureFetch: Not authenticated');

            // Trigger authentication flow if handler exists
            if (typeof handleAuthenticationRequired === 'function') {
                handleAuthenticationRequired();
            }

            return null;
        }

        // Merge headers with auth and CSRF
        const headers = authMgr.getHeaders(options.headers || {});

        // Perform fetch with secure headers
        const response = await fetch(url, {
            ...options,
            headers
        });

        // Handle authentication errors
        if (response.status === 401) {
            console.error('secureFetch: Authentication failed (401)');
            authMgr.clearToken();

            if (typeof handleAuthenticationRequired === 'function') {
                handleAuthenticationRequired();
            }

            return null;
        }

        // Handle forbidden errors
        if (response.status === 403) {
            console.error('secureFetch: Forbidden (403) - Invalid CSRF token?');

            // Refresh CSRF token and retry once
            if (typeof csrfManager !== 'undefined') {
                csrfManager.refreshToken();
            }

            return null;
        }

        return response;

    } catch (error) {
        console.error('secureFetch: Network error:', error.message);

        // Trigger connection error handler if exists
        if (typeof handleNetworkError === 'function') {
            handleNetworkError(error);
        }

        return null;
    }
}

// ============================================================================
// 5. MEMORY LEAK PREVENTION
// ============================================================================

/**
 * Managed Interval with automatic cleanup
 * Prevents memory leaks from forgotten intervals
 */
class ManagedInterval {
    constructor(callback, interval, name = 'unnamed') {
        this.callback = callback;
        this.interval = interval;
        this.name = name;
        this.intervalId = null;
        this.isActive = false;
    }

    /**
     * Start the interval
     */
    start() {
        if (this.isActive) {
            console.warn(`ManagedInterval "${this.name}" already running`);
            return;
        }

        this.intervalId = setInterval(this.callback, this.interval);
        this.isActive = true;
        console.log(`ManagedInterval "${this.name}" started (${this.interval}ms)`);
    }

    /**
     * Stop the interval
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            this.isActive = false;
            console.log(`ManagedInterval "${this.name}" stopped`);
        }
    }

    /**
     * Check if interval is running
     * @returns {boolean}
     */
    isRunning() {
        return this.isActive;
    }

    /**
     * Restart the interval
     */
    restart() {
        this.stop();
        this.start();
    }
}

/**
 * Managed Timeout with automatic cleanup
 */
class ManagedTimeout {
    constructor(callback, delay, name = 'unnamed') {
        this.callback = callback;
        this.delay = delay;
        this.name = name;
        this.timeoutId = null;
        this.isActive = false;
    }

    /**
     * Start the timeout
     */
    start() {
        if (this.isActive) {
            console.warn(`ManagedTimeout "${this.name}" already scheduled`);
            return;
        }

        this.timeoutId = setTimeout(() => {
            this.isActive = false;
            this.callback();
        }, this.delay);
        this.isActive = true;
    }

    /**
     * Cancel the timeout
     */
    cancel() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
            this.isActive = false;
        }
    }

    /**
     * Check if timeout is scheduled
     * @returns {boolean}
     */
    isScheduled() {
        return this.isActive;
    }
}

/**
 * Image Cache with automatic cleanup
 * Prevents memory leaks from accumulated base64 images
 */
class ImageCache {
    constructor(maxSize = 5) {
        this.images = [];
        this.maxSize = maxSize;
        this.totalSize = 0; // Track approximate memory usage
    }

    /**
     * Add image to cache with automatic cleanup of old images
     * @param {string} imageData - Base64 image data
     */
    addImage(imageData) {
        // Estimate size (base64 is ~1.33x original size)
        const size = imageData.length;

        this.images.push({
            data: imageData,
            timestamp: Date.now(),
            size: size
        });

        this.totalSize += size;

        // Remove oldest if exceeding max size
        while (this.images.length > this.maxSize) {
            const removed = this.images.shift();
            this.totalSize -= removed.size;
        }
    }

    /**
     * Get latest image
     * @returns {string|null} - Latest image data or null
     */
    getLatest() {
        return this.images.length > 0 ?
            this.images[this.images.length - 1].data : null;
    }

    /**
     * Get image by index (0 = oldest, -1 = newest)
     * @param {number} index - Image index
     * @returns {string|null} - Image data or null
     */
    getImage(index) {
        if (index < 0) {
            index = this.images.length + index;
        }
        return this.images[index] ? this.images[index].data : null;
    }

    /**
     * Clear all images
     */
    clear() {
        this.images = [];
        this.totalSize = 0;
    }

    /**
     * Get cache size
     * @returns {number} - Number of images in cache
     */
    size() {
        return this.images.length;
    }

    /**
     * Get approximate memory usage in bytes
     * @returns {number} - Approximate bytes used
     */
    memoryUsage() {
        return this.totalSize;
    }
}

/**
 * Toast Notification Manager with automatic cleanup
 * Prevents DOM bloat from accumulated toast elements
 */
class ToastManager {
    constructor() {
        this.toastElement = null;
        this.timeoutId = null;
        this.toastQueue = [];
        this.isShowing = false;
    }

    /**
     * Show toast notification
     * @param {string} message - Message to display
     * @param {string} type - Toast type: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Display duration in milliseconds
     */
    show(message, type = 'success', duration = 3000) {
        // Queue toast if one is already showing
        if (this.isShowing) {
            this.toastQueue.push({ message, type, duration });
            return;
        }

        this.isShowing = true;

        // Clear existing timeout
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }

        // Create or reuse toast element
        if (!this.toastElement) {
            this.toastElement = document.createElement('div');
            this.toastElement.className = 'toast-notification';
            this.toastElement.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                padding: 15px 20px;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                z-index: 9999;
                max-width: 400px;
                opacity: 0;
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(this.toastElement);
        }

        // Set message and type
        this.toastElement.textContent = message;
        this.toastElement.className = `toast-notification toast-${type}`;

        // Set type-specific styling
        const typeColors = {
            success: '#10b981',
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };
        this.toastElement.style.background = typeColors[type] || typeColors.info;

        // Show toast
        requestAnimationFrame(() => {
            this.toastElement.style.opacity = '1';
        });

        // Auto-hide after duration
        this.timeoutId = setTimeout(() => {
            this.hide();
        }, duration);
    }

    /**
     * Hide current toast
     */
    hide() {
        if (!this.toastElement) return;

        this.toastElement.style.opacity = '0';

        setTimeout(() => {
            this.isShowing = false;

            // Show next toast in queue
            if (this.toastQueue.length > 0) {
                const next = this.toastQueue.shift();
                this.show(next.message, next.type, next.duration);
            }
        }, 300);
    }

    /**
     * Complete cleanup - remove from DOM
     */
    cleanup() {
        this.hide();

        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }

        if (this.toastElement && this.toastElement.parentNode) {
            this.toastElement.parentNode.removeChild(this.toastElement);
            this.toastElement = null;
        }

        this.toastQueue = [];
        this.isShowing = false;
    }
}

/**
 * Resource Manager - Centralized cleanup for all managed resources
 */
class ResourceManager {
    constructor() {
        this.intervals = new Map();
        this.timeouts = new Map();
        this.imageCaches = new Map();
        this.toastManagers = new Map();
        this.websockets = new Map();
    }

    /**
     * Register a managed interval
     */
    registerInterval(name, interval) {
        this.intervals.set(name, interval);
    }

    /**
     * Register a managed timeout
     */
    registerTimeout(name, timeout) {
        this.timeouts.set(name, timeout);
    }

    /**
     * Register an image cache
     */
    registerImageCache(name, cache) {
        this.imageCaches.set(name, cache);
    }

    /**
     * Register a toast manager
     */
    registerToastManager(name, manager) {
        this.toastManagers.set(name, manager);
    }

    /**
     * Register a WebSocket
     */
    registerWebSocket(name, websocket) {
        this.websockets.set(name, websocket);
    }

    /**
     * Cleanup all resources
     */
    cleanupAll() {
        console.log('ResourceManager: Cleaning up all resources...');

        // Stop all intervals
        this.intervals.forEach((interval, name) => {
            console.log(`  Stopping interval: ${name}`);
            interval.stop();
        });
        this.intervals.clear();

        // Cancel all timeouts
        this.timeouts.forEach((timeout, name) => {
            console.log(`  Canceling timeout: ${name}`);
            timeout.cancel();
        });
        this.timeouts.clear();

        // Clear all image caches
        this.imageCaches.forEach((cache, name) => {
            console.log(`  Clearing image cache: ${name}`);
            cache.clear();
        });
        this.imageCaches.clear();

        // Cleanup all toast managers
        this.toastManagers.forEach((manager, name) => {
            console.log(`  Cleaning up toast manager: ${name}`);
            manager.cleanup();
        });
        this.toastManagers.clear();

        // Close all WebSockets
        this.websockets.forEach((ws, name) => {
            console.log(`  Closing WebSocket: ${name}`);
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        });
        this.websockets.clear();

        console.log('ResourceManager: Cleanup complete');
    }
}

// ============================================================================
// 6. GLOBAL INSTANCES AND INITIALIZATION
// ============================================================================

// Create global instances
const csrfManager = new CSRFTokenManager();
const toastManager = new ToastManager();
const resourceManager = new ResourceManager();

// Auth manager will be initialized by dashboard with token
let authManager = null;

/**
 * Initialize authentication manager
 * Call this from dashboard after obtaining auth token
 *
 * @param {string} token - Authentication token
 * @param {number} expiryMs - Token expiry in milliseconds
 */
function initializeAuth(token, expiryMs = null) {
    authManager = new AuthHeaderManager(token);
    if (expiryMs) {
        authManager.setToken(token, expiryMs);
    }
    console.log('Authentication manager initialized');
}

/**
 * Global cleanup on page unload
 * Prevents memory leaks when navigating away
 */
window.addEventListener('beforeunload', () => {
    console.log('Page unloading - cleaning up resources...');
    resourceManager.cleanupAll();
});

// ============================================================================
// 7. EXPORT FOR MODULE SYSTEMS
// ============================================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // XSS Prevention
        sanitizeHTML,
        setTextContent,
        setHTMLContent,
        createSafeElement,

        // CSRF Protection
        CSRFTokenManager,

        // Authentication
        AuthHeaderManager,
        initializeAuth,

        // Secure Fetch
        secureFetch,

        // Memory Management
        ManagedInterval,
        ManagedTimeout,
        ImageCache,
        ToastManager,
        ResourceManager,

        // Global Instances
        csrfManager,
        toastManager,
        resourceManager
    };
}

console.log('✓ R2D2 Dashboard Security Utilities v1.0.0 loaded');
