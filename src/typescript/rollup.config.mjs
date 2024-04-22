import esbuild from 'rollup-plugin-esbuild';
import { nodeResolve } from '@rollup/plugin-node-resolve';

export default [
  {
    input: `index.ts`,
    plugins: [esbuild({ minify: true }), nodeResolve()],
    output: [
      {
        file: `../python/schorle/assets/js/index.js`,
        format: 'esm',
        sourcemap: false
      }
    ]
  },
  {
    input: `mainWorker.ts`,
    plugins: [esbuild({ minify: true }), nodeResolve()],
    output: [
      {
        file: `../python/schorle/assets/js/workers/mainWorker.js`,
        format: 'esm',
        sourcemap: false
      }
    ]
  }
];