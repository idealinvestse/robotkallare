/**
 * GDial Translation System - Optimized Version
 * Centralized translation management for multilingual support
 */

// Set default language if not already set in localStorage
const DEFAULT_LANGUAGE = 'sv';
let currentLanguage = localStorage.getItem('gdial_language') || DEFAULT_LANGUAGE;
document.documentElement.lang = currentLanguage;

// Store translations with lazy loading
const translationCache = {
  sv: null,
  en: null
};

// Helper function to get translations (lazy loaded)
async function getTranslations(lang) {
  if (translationCache[lang]) {
    return translationCache[lang];
  }
  
  try {
    // Path to translation file
    const path = `/ringbot/static/translations_${lang}.js`;
    
    // Dynamic import for translations
    if (!window[`translations_${lang}`]) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = path;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    
    // Store in cache
    translationCache[lang] = window[`translations_${lang}`] || {};
    return translationCache[lang];
  } catch (err) {
    console.error(`Failed to load translations for ${lang}:`, err);
    return {};
  }
}

/**
 * Get translation for a key
 * @param {string} key - Translation key
 * @param {string} [defaultText=null] - Default text if translation not found
 * @returns {string} - Translated text or default/key
 */
async function translate(key, defaultText = null) {
  // Get translations for current language
  const translations = await getTranslations(currentLanguage);
  
  // Return translation if exists
  if (translations && translations[key]) {
    return translations[key];
  }
  
  // Return default text or key
  return defaultText || key;
}

/**
 * Synchronous version for direct use in templates
 * Note: Should only be used after translations are loaded
 */
function __(key, lang = null, defaultText = null) {
  const langToUse = lang || currentLanguage;
  const translations = window[`translations_${langToUse}`] || {};
  
  if (translations[key]) {
    return translations[key];
  }
  
  return defaultText || key;
}

/**
 * Change the UI language
 * @param {string} lang - Language code ('sv' or 'en')
 */
async function setLanguage(lang) {
  if (lang !== 'sv' && lang !== 'en') {
    console.error('Unsupported language:', lang);
    return;
  }
  
  // Update language setting
  currentLanguage = lang;
  document.documentElement.lang = lang;
  localStorage.setItem('gdial_language', lang);
  
  // Make sure translations are loaded
  await getTranslations(lang);
  
  // Update all elements with data-i18n attribute
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = __(key);
  });
  
  // Update placeholder attributes
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    el.placeholder = __(key);
  });
  
  // Update title
  if (document.getElementById('page-title')) {
    document.getElementById('page-title').textContent = __('pageTitle');
  }
  
  // Update header
  if (document.getElementById('header-title')) {
    document.getElementById('header-title').textContent = __('headerTitle');
  }
  
  // Update status
  if (document.getElementById('system-status')) {
    document.getElementById('system-status').textContent = __('systemReady');
  }
  
  // Update language selector
  const languageSelect = document.getElementById('language-select');
  if (languageSelect) {
    languageSelect.value = lang;
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  // Load translations for current language
  await getTranslations(currentLanguage);
  
  // Apply translations to page
  await setLanguage(currentLanguage);
  
  // Set up language selector
  const languageSelect = document.getElementById('language-select');
  if (languageSelect) {
    languageSelect.value = currentLanguage;
    
    languageSelect.addEventListener('change', (event) => {
      setLanguage(event.target.value);
    });
  }
});

// Export translation functions
window.__ = __;
window.setLanguage = setLanguage;
window.translate = translate;