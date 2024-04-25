import esbuild from 'rollup-plugin-esbuild';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import { uglify } from "rollup-plugin-uglify";

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
    plugins: [uglify()],
    input: `../python/schorle/assets/js/index.js`,
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