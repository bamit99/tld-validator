// Configuration
const API_BASE_URL = window.location.origin;
const API_KEY_HEADER = 'X-API-Key';

// Global state
let apiKey = localStorage.getItem('tld-api-key') || null;

// Utility functions
function showResult(elementId, message, type = 'success') {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `result ${type}`;
    element.classList.remove('hidden');
}

function hideResult(elementId) {
    const element = document.getElementById(elementId);
    element.classList.add('hidden');
}

function showLoading(buttonId, loading = true) {
    const button = document.getElementById(buttonId);
    button.disabled = loading;
    button.textContent = loading ? 'Loading...' : button.dataset.originalText || button.textContent;
}

// API functions
async function makeRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (apiKey) {
        headers[API_KEY_HEADER] = apiKey;
    }
    
    try {
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message || 'Request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Validation functions
async function validateDomain() {
    const domainInput = document.getElementById('domain-input');
    const domain = domainInput.value.trim();
    
    if (!domain) {
        showResult('validation-result', 'Please enter a domain name', 'error');
        return;
    }
    
    if (!apiKey) {
        showResult('validation-result', 'Please generate an API key first', 'error');
        return;
    }
    
    hideResult('validation-result');
    showLoading('validate-btn', true);
    
    try {
        const result = await makeRequest('/api/validate-tld', {
            method: 'POST',
            body: JSON.stringify({ domain })
        });
        
        const message = result.is_valid 
            ? `Success: ${result.message}` 
            : `Failure: ${result.message}`;
        showResult('validation-result', message, result.is_valid ? 'success' : 'error');
        
    } catch (error) {
        showResult('validation-result', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('validate-btn', false);
    }
}

async function validateTLD() {
    const tldInput = document.getElementById('tld-input');
    const tld = tldInput.value.trim();
    
    if (!tld) {
        showResult('tld-result', 'Please enter a TLD', 'error');
        return;
    }
    
    if (!apiKey) {
        showResult('tld-result', 'Please generate an API key first', 'error');
        return;
    }
    
    hideResult('tld-result');
    showLoading('validate-tld-btn', true);
    
    try {
        const result = await makeRequest('/api/validate-tld', {
            method: 'POST',
            body: JSON.stringify({ tld })
        });
        
        const message = result.is_valid 
            ? `Success: ${result.message}` 
            : `Failure: ${result.message}`;
        showResult('tld-result', message, result.is_valid ? 'success' : 'error');
        
    } catch (error) {
        showResult('tld-result', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('validate-tld-btn', false);
    }
}

// API Key management
async function generateAPIKey() {
    hideResult('api-key-result');
    showLoading('generate-key-btn', true);
    
    try {
        const result = await makeRequest('/api/generate-key', {
            method: 'POST'
        });
        
        apiKey = result.key;
        localStorage.setItem('tld-api-key', apiKey);
        
        showResult('api-key-result', 
            `Generated API Key: ${apiKey}\n\nSave this key! It won't be shown again.`, 
            'success');
        
    } catch (error) {
        showResult('api-key-result', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('generate-key-btn', false);
    }
}

// Cache information
async function refreshCacheInfo() {
    const cacheInfoDiv = document.getElementById('cache-info');
    const button = document.getElementById('refresh-cache-btn');
    
    button.disabled = true;
    button.textContent = 'Refreshing...';
    
    try {
        const info = await makeRequest('/api/cache-info');
        
        if (info.last_updated) {
            const lastUpdated = new Date(info.last_updated);
            const isFresh = info.is_fresh ? 'Fresh' : 'Stale';
            
            cacheInfoDiv.innerHTML = `
                <p><strong>Total TLDs:</strong> ${info.tld_count || 0}</p>
                <p><strong>Last Updated:</strong> ${lastUpdated.toLocaleString()}</p>
                <p><strong>Status:</strong> ${isFresh}</p>
            `;
        } else {
            cacheInfoDiv.innerHTML = '<p>No cache information available</p>';
        }
        
    } catch (error) {
        cacheInfoDiv.innerHTML = `<p>Error loading cache info: ${error.message}</p>`;
    } finally {
        button.disabled = false;
        button.textContent = 'Refresh';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Store original button text
    document.querySelectorAll('button').forEach(button => {
        button.dataset.originalText = button.textContent;
    });
    
    // Load cache info
    refreshCacheInfo();
    
    // Handle Enter key for inputs
    document.getElementById('domain-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') validateDomain();
    });
    
    document.getElementById('tld-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') validateTLD();
    });
    
    // Auto-load API key if available
    if (apiKey) {
        console.log('Using saved API key');
    }
});

// Export functions for global access
window.validateDomain = validateDomain;
window.validateTLD = validateTLD;
window.generateAPIKey = generateAPIKey;
window.refreshCacheInfo = refreshCacheInfo;
