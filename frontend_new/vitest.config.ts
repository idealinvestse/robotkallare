/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true, // Optional: makes vitest globals like describe, it, expect available without import
    environment: 'jsdom', // Set the test environment to jsdom
  },
});
