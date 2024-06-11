import esbuild from 'rollup-plugin-esbuild';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import gzipPlugin from 'rollup-plugin-gzip';
import terser from '@rollup/plugin-terser';


export default [
  {
    input: `index.ts`,
    plugins: [esbuild({ minify: true }), nodeResolve()],
    output: {
      file: `../python/schorle/assets/js/index.js`,
      format: 'esm',
      sourcemap: false
    }
  },
  {
    plugins: [
      terser(),
      gzipPlugin({
        fileName: '.gz'
      })],
    input: `../python/schorle/assets/js/index.js`,
    output: {
      file: `../python/schorle/assets/js/index.min.js`,
      format: 'esm',
      sourcemap: false
    }

  },
  {
    input: `mainWorker.ts`,
    plugins: [esbuild({ minify: true }), nodeResolve()],
    output: {
      file: `../python/schorle/assets/js/workers/mainWorker.js`,
      format: 'esm',
      sourcemap: false
    }

  }
];