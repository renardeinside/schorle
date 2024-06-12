import { defineConfig } from 'vite';
import viteCompression from 'vite-plugin-compression';

export default defineConfig({
  plugins: [viteCompression()],
  build: {
    outDir: '../python/schorle/assets/js/',
    chunkSizeWarningLimit: 10000,
    emptyOutDir: true,
    minify: 'terser',
    rollupOptions: {
      input: {
        'index.min': 'index.ts',
        'workers/mainWorker': 'mainWorker.ts'
      },
      output: {
        entryFileNames: '[name].js'
      }
    }
  }
});
