import esbuild from 'rollup-plugin-esbuild';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import { uglify } from 'rollup-plugin-uglify';
import { brotliCompress } from 'zlib';
import { promisify } from 'util';
import gzipPlugin from 'rollup-plugin-gzip';

const brotliPromise = promisify(brotliCompress);

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
      uglify(),
      gzipPlugin({
        customCompression: content => brotliPromise(Buffer.from(content)),
        fileName: '.br'
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