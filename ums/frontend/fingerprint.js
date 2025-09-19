/**
 * Browser Fingerprinting Utility for UMS
 *
 * This module provides client-side browser fingerprinting capabilities
 * for user recognition in the User Management Services.
 */

/**
 * Generate a comprehensive browser fingerprint
 * @returns {Promise<Object>} Fingerprint data object
 */
export async function generateFingerprint() {
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
        console.warn('Error generating fingerprint:', error);
    }

    return fingerprint;
}

/**
 * Generate canvas fingerprint
 * @returns {Promise<string>} Canvas fingerprint hash
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
            ctx.fillText('Hello, world! 🌍', 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText('Hello, world! 🌍', 4, 17);

            // Get canvas data
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
 * Create session data object for UMS API
 * @returns {Promise<Object>} Session creation object
 */
export async function createSessionData() {
    const fingerprint = await generateFingerprint();

    return {
        fingerprint: {
            components: fingerprint,
            browser_name: getBrowserName(fingerprint.userAgent),
            os_name: getOSName(fingerprint.userAgent),
            device_type: getDeviceType(fingerprint.userAgent),
            screen_resolution: fingerprint.screenResolution ?
                `${fingerprint.screenResolution[0]}x${fingerprint.screenResolution[1]}` : null,
            timezone: fingerprint.timezone,
            language: fingerprint.language
        },
        device_info: {
            screen_width: fingerprint.screenResolution ? fingerprint.screenResolution[0] : null,
            screen_height: fingerprint.screenResolution ? fingerprint.screenResolution[1] : null,
            pixel_ratio: fingerprint.pixelRatio,
            hardware_concurrency: fingerprint.hardwareConcurrency,
            device_memory: fingerprint.deviceMemory,
            touch_support: fingerprint.features?.touchSupport || false
        }
    };
}

/**
 * Extract browser name from user agent
 * @param {string} userAgent - User agent string
 * @returns {string} Browser name
 */
function getBrowserName(userAgent) {
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
    if (/Mobile|Android/.test(userAgent)) return 'mobile';
    if (/Tablet|iPad/.test(userAgent)) return 'tablet';
    return 'desktop';
}

/**
 * Store session token in local storage
 * @param {string} token - Session token
 */
export function storeSessionToken(token) {
    try {
        localStorage.setItem('ums_session_token', token);
    } catch (error) {
        console.warn('Could not store session token:', error);
    }
}

/**
 * Retrieve session token from local storage
 * @returns {string|null} Session token or null
 */
export function getSessionToken() {
    try {
        return localStorage.getItem('ums_session_token');
    } catch (error) {
        console.warn('Could not retrieve session token:', error);
        return null;
    }
}

/**
 * Clear session token from local storage
 */
export function clearSessionToken() {
    try {
        localStorage.removeItem('ums_session_token');
    } catch (error) {
        console.warn('Could not clear session token:', error);
    }
}