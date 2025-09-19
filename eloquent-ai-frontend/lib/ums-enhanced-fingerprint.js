/**
 * Enhanced Browser Fingerprinting for UMS Integration
 *
 * Compatible with existing auth system - enhances browser fingerprinting
 * to work with the existing /api/auth endpoints.
 */

/**
 * Generate comprehensive browser fingerprint
 * @returns {Promise<Object>} Enhanced fingerprint data
 */
async function generateEnhancedFingerprint() {
    const fingerprint = {};

    try {
        // Basic browser information
        fingerprint.userAgent = navigator.userAgent;
        fingerprint.language = navigator.language;
        fingerprint.languages = navigator.languages ? Array.from(navigator.languages) : [];
        fingerprint.platform = navigator.platform;

        // Screen information
        fingerprint.screenResolution = [screen.width, screen.height];
        fingerprint.colorDepth = screen.colorDepth;
        fingerprint.pixelRatio = window.devicePixelRatio || 1;

        // Timezone
        fingerprint.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

        // Hardware information (if available)
        if ('hardwareConcurrency' in navigator) {
            fingerprint.hardwareConcurrency = navigator.hardwareConcurrency;
        }

        if ('deviceMemory' in navigator) {
            fingerprint.deviceMemory = navigator.deviceMemory;
        }

        // Canvas fingerprinting
        fingerprint.canvas = await getCanvasFingerprint();

        // WebGL fingerprinting
        fingerprint.webgl = getWebGLFingerprint();

        // Font detection (simplified)
        fingerprint.fonts = await detectFonts();

        // Plugin information (if available)
        if (navigator.plugins && navigator.plugins.length > 0) {
            fingerprint.plugins = Array.from(navigator.plugins).map(plugin => plugin.name);
        }

        // Additional browser features
        fingerprint.features = {
            localStorage: typeof Storage !== 'undefined',
            sessionStorage: typeof sessionStorage !== 'undefined',
            indexedDB: typeof indexedDB !== 'undefined',
            webWorkers: typeof Worker !== 'undefined',
            webAssembly: typeof WebAssembly !== 'undefined',
            touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0
        };

    } catch (error) {
        console.warn('Error generating enhanced fingerprint:', error);
    }

    return fingerprint;
}

/**
 * Generate canvas fingerprint
 * @returns {Promise<string>} Canvas fingerprint
 */
function getCanvasFingerprint() {
    return new Promise((resolve) => {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = 200;
            canvas.height = 50;

            // Draw fingerprinting pattern
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText('UMS Enhanced Fingerprint 🔍', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('UMS Enhanced Fingerprint 🔍', 4, 17);

            const dataURL = canvas.toDataURL();
            resolve(dataURL);
        } catch (error) {
            resolve('canvas_error');
        }
    });
}

/**
 * Generate WebGL fingerprint
 * @returns {Object} WebGL information
 */
function getWebGLFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

        if (!gl) {
            return { vendor: 'no_webgl', renderer: 'no_webgl' };
        }

        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');

        return {
            vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
            renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
            version: gl.getParameter(gl.VERSION),
            shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION)
        };
    } catch (error) {
        return { vendor: 'webgl_error', renderer: 'webgl_error' };
    }
}

/**
 * Detect available fonts (simplified approach)
 * @returns {Promise<Array>} List of detected fonts
 */
function detectFonts() {
    return new Promise((resolve) => {
        try {
            const baseFonts = ['monospace', 'sans-serif', 'serif'];
            const testFonts = [
                'Arial', 'Helvetica', 'Times New Roman', 'Courier New', 'Verdana',
                'Georgia', 'Palatino', 'Garamond', 'Bookman', 'Trebuchet MS',
                'Impact', 'Comic Sans MS', 'Tahoma', 'Lucida Console'
            ];

            const detectedFonts = [];
            const testString = 'mmmmmmmmmmlli';
            const testSize = '72px';

            // Create test element
            const testElement = document.createElement('div');
            testElement.style.position = 'absolute';
            testElement.style.left = '-9999px';
            testElement.style.fontSize = testSize;
            testElement.innerHTML = testString;
            document.body.appendChild(testElement);

            // Get baseline widths
            const baselineWidths = {};
            baseFonts.forEach(font => {
                testElement.style.fontFamily = font;
                baselineWidths[font] = testElement.offsetWidth;
            });

            // Test each font
            testFonts.forEach(font => {
                baseFonts.forEach(baseFont => {
                    testElement.style.fontFamily = `"${font}", ${baseFont}`;
                    if (testElement.offsetWidth !== baselineWidths[baseFont]) {
                        if (!detectedFonts.includes(font)) {
                            detectedFonts.push(font);
                        }
                    }
                });
            });

            document.body.removeChild(testElement);
            resolve(detectedFonts);
        } catch (error) {
            resolve([]);
        }
    });
}

/**
 * Create enhanced fingerprint data for existing auth endpoints
 * @returns {Promise<Object>} Fingerprint data compatible with existing API
 */
async function createEnhancedFingerprintData() {
    const fingerprint = await generateEnhancedFingerprint();

    // Return in format expected by existing auth endpoints
    return {
        browser_fingerprint: JSON.stringify(fingerprint), // For the existing field
        device_info: {
            browser: getBrowserName(fingerprint.userAgent),
            os: getOSName(fingerprint.userAgent),
            device_type: getDeviceType(fingerprint.userAgent),
            screen_resolution: fingerprint.screenResolution ?
                `${fingerprint.screenResolution[0]}x${fingerprint.screenResolution[1]}` : null,
            timezone: fingerprint.timezone,
            language: fingerprint.language,
            hardware_concurrency: fingerprint.hardwareConcurrency,
            device_memory: fingerprint.deviceMemory
        },
        // Raw fingerprint for UMS enhanced processing
        raw_fingerprint_data: fingerprint
    };
}

/**
 * Extract browser name from user agent
 * @param {string} userAgent - User agent string
 * @returns {string} Browser name
 */
function getBrowserName(userAgent) {
    if (!userAgent) return 'Unknown';

    if (userAgent.includes('Chrome') && !userAgent.includes('Edge')) return 'Chrome';
    if (userAgent.includes('Firefox')) return 'Firefox';
    if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) return 'Safari';
    if (userAgent.includes('Edge')) return 'Edge';
    if (userAgent.includes('Opera')) return 'Opera';
    return 'Unknown';
}

/**
 * Extract OS name from user agent
 * @param {string} userAgent - User agent string
 * @returns {string} OS name
 */
function getOSName(userAgent) {
    if (!userAgent) return 'Unknown';

    if (userAgent.includes('Windows')) return 'Windows';
    if (userAgent.includes('Mac OS') || userAgent.includes('macOS')) return 'macOS';
    if (userAgent.includes('Linux') && !userAgent.includes('Android')) return 'Linux';
    if (userAgent.includes('Android')) return 'Android';
    if (userAgent.includes('iPhone') || userAgent.includes('iPad')) return 'iOS';
    return 'Unknown';
}

/**
 * Determine device type from user agent
 * @param {string} userAgent - User agent string
 * @returns {string} Device type
 */
function getDeviceType(userAgent) {
    if (!userAgent) return 'desktop';

    if (/Mobile|Android/.test(userAgent)) return 'mobile';
    if (/Tablet|iPad/.test(userAgent)) return 'tablet';
    return 'desktop';
}

/**
 * Enhanced initialization for anonymous users
 * Compatible with existing /api/auth/anonymous endpoint
 * @returns {Promise<Object>} Enhanced authentication result
 */
async function initializeEnhancedAnonymousAuth() {
    try {
        const fingerprintData = await createEnhancedFingerprintData();

        // Call existing endpoint with enhanced data
        const response = await fetch('/api/auth/anonymous', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: generateDeviceId(),
                ...fingerprintData
            })
        });

        if (!response.ok) {
            throw new Error(`Authentication failed: ${response.status}`);
        }

        const authResult = await response.json();

        // Store token if provided
        if (authResult.token) {
            localStorage.setItem('auth_token', authResult.token);
        }

        return {
            ...authResult,
            recognition_method: authResult.user?.is_anonymous === false ? 'fingerprint_recognized' : 'new_anonymous',
            fingerprint_confidence: calculateFingerprintConfidence(fingerprintData.raw_fingerprint_data)
        };

    } catch (error) {
        console.error('Enhanced anonymous auth failed:', error);
        throw error;
    }
}

/**
 * Generate device ID for fallback recognition
 * @returns {string} Device ID
 */
function generateDeviceId() {
    // Try to get existing device ID from localStorage
    let deviceId = localStorage.getItem('device_id');

    if (!deviceId) {
        // Generate new device ID
        deviceId = 'dev_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now().toString(36);
        localStorage.setItem('device_id', deviceId);
    }

    return deviceId;
}

/**
 * Calculate fingerprint confidence score
 * @param {Object} fingerprint - Raw fingerprint data
 * @returns {number} Confidence score (0-100)
 */
function calculateFingerprintConfidence(fingerprint) {
    let score = 0;

    if (fingerprint.userAgent) score += 10;
    if (fingerprint.language) score += 5;
    if (fingerprint.screenResolution) score += 15;
    if (fingerprint.timezone) score += 10;
    if (fingerprint.hardwareConcurrency) score += 10;
    if (fingerprint.deviceMemory) score += 10;
    if (fingerprint.canvas && fingerprint.canvas !== 'canvas_error') score += 20;
    if (fingerprint.webgl && fingerprint.webgl.vendor !== 'webgl_error') score += 15;
    if (fingerprint.fonts && fingerprint.fonts.length > 0) score += Math.min(fingerprint.fonts.length / 2, 10);

    return Math.min(score, 100);
}

// Export functions for use in the application
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    module.exports = {
        generateEnhancedFingerprint,
        createEnhancedFingerprintData,
        initializeEnhancedAnonymousAuth,
        generateDeviceId,
        calculateFingerprintConfidence
    };
} else {
    // Browser environment
    window.UMSEnhanced = {
        generateEnhancedFingerprint,
        createEnhancedFingerprintData,
        initializeEnhancedAnonymousAuth,
        generateDeviceId,
        calculateFingerprintConfidence
    };
}