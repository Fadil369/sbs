/**
 * SBS Integration Engine - Configuration
 * Environment-based API configuration with CORS support
 */

// Detect environment
const getEnvironment = () => {
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
          return 'development';
    }
    if (window.location.hostname.includes('staging')) {
          return 'staging';
    }
    return 'production';
};

// Environment configuration
const environments = {
    development: {
          apiBaseUrl: 'http://localhost:5000',
          apiTimeout: 30000,
          retryAttempts: 3,
          retryDelay: 1000
    },
    staging: {
          apiBaseUrl: 'https://sbs-api-staging.example.com',
          apiTimeout: 30000,
          retryAttempts: 2,
          retryDelay: 2000
    },
    production: {
          apiBaseUrl: 'https://sbs-api.example.com',
          apiTimeout: 30000,
          retryAttempts: 2,
          retryDelay: 2000
    }
};

// Initialize configuration
const currentEnv = getEnvironment();
const config = environments[currentEnv];

// Export to window object
window.SBS_CONFIG = {
    environment: currentEnv,
    apiBaseUrl: config.apiBaseUrl,
    apiTimeout: config.apiTimeout,
    retryAttempts: config.retryAttempts,
    retryDelay: config.retryDelay,
    // For backwards compatibility
    SBS_API_BASE_URL: config.apiBaseUrl
};

// Also set the old variable name for backwards compatibility
window.SBS_API_BASE_URL = config.apiBaseUrl;

// Log configuration in development
if (currentEnv === 'development') {
    console.log('SBS Configuration loaded:', {
          environment: currentEnv,
          apiBaseUrl: config.apiBaseUrl,
          timestamp: new Date().toISOString()
    });
}
