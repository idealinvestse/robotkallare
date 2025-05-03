/**
 * Optimized static file references for GDial
 * This module provides a more efficient way to handle static file references
 */

// Base path for static assets - centralized configuration
const STATIC_BASE_PATH = '/ringbot/static';

// Helper function to generate complete URLs to static assets
function staticPath(assetPath) {
  // Remove leading slash if present to avoid double slashes
  if (assetPath.startsWith('/')) {
    assetPath = assetPath.substring(1);
  }
  return `${STATIC_BASE_PATH}/${assetPath}`;
}

// Helper function to load CSS files dynamically
function loadStylesheet(path) {
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = staticPath(path);
  document.head.appendChild(link);
}

// Helper function to load JavaScript files dynamically
function loadScript(path, async = false, defer = false) {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = staticPath(path);
    script.async = async;
    script.defer = defer;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

// Helper function to create navigation links with proper paths
function createNavLink(href, text, iconSvg) {
  // If href is a relative path and doesn't start with /ringbot, add the prefix
  if (href.startsWith('/') && !href.startsWith('/ringbot/')) {
    href = `/ringbot${href}`;
  } else if (!href.startsWith('/') && !href.startsWith('http')) {
    href = `${STATIC_BASE_PATH}/${href}`;
  }
  
  const link = document.createElement('a');
  link.href = href;
  link.className = 'header-link';
  
  if (iconSvg) {
    link.innerHTML = iconSvg;
  }
  
  const span = document.createElement('span');
  span.textContent = text;
  link.appendChild(span);
  
  return link;
}

// Export the utility functions
window.gdial = {
  staticPath,
  loadStylesheet,
  loadScript,
  createNavLink,
  STATIC_BASE_PATH
};