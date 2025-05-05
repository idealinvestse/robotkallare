import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on the mode (development, production)
  const env = loadEnv(mode, process.cwd(), '');

  // Extract the base URL for the proxy target, removing the /api/v1 part
  const apiBaseUrl = env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
  const proxyTarget = apiBaseUrl.replace(/\/api\/v1\/?$/, ''); // Get http://localhost:8000

  return {
    plugins: [react()],
    server: {
      proxy: {
        // Proxy /api requests to the backend server
        '/api': {
          target: proxyTarget,
          changeOrigin: true, // Needed for virtual hosted sites
          rewrite: (path) => path.replace(/^\/api/, ''), // Remove /api prefix before sending
          secure: false,      // Allow self-signed certs if backend uses HTTPS locally
          ws: true,           // Proxy websockets if needed
        },
      },
    },
  };
});
