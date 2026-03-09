// FILE: rollup.config.js
import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import copy from 'rollup-plugin-copy';

export default {
  input: {
    'background': 'src/background.js',
    'content': 'src/content.js',
    'auth': 'src/auth.js',
    'popup/popup': 'src/popup/popup.js',
    'reader/reader': 'src/reader/reader.js',
    'sidebar/script': 'src/sidebar/script.js',
    'sidebar/coins': 'src/sidebar/coins.js',
    'sidebar/manage_prompts': 'src/sidebar/manage_prompts.js',
    'offscreen_parser': 'src/offscreen_parser.js',
    'reader/book_viewer': 'src/reader/book_viewer.js', // *** AGGIUNTO ***
    'reader/player': 'src/reader/player.js'
  },
  output: {
    dir: 'dist',
    format: 'esm',
    chunkFileNames: 'chunks/[name]-[hash].js',
    sourcemap: true
  },
  plugins: [
    resolve({ browser: true }),
    commonjs(),
    copy({
      targets: [
        { src: 'src/manifest.json', dest: 'dist' },
        { src: 'src/rules.json', dest: 'dist' },
        { src: 'src/*.html', dest: 'dist' },
        { src: 'src/css', dest: 'dist' },
        { src: 'src/icons/**/*', dest: 'dist/icons' },
        { src: 'public/libs', dest: 'dist' },
        { src: 'src/popup/*.html', dest: 'dist/popup' },
        { src: 'src/popup/*.css', dest: 'dist/popup' },
        { src: 'src/reader/*.html', dest: 'dist/reader' },
        { src: 'src/reader/player.html', dest: 'dist/reader' },
        { src: 'src/reader/*.css', dest: 'dist/reader' },
        { src: 'src/sidebar/*.html', dest: 'dist/sidebar' },
        { src: 'src/sidebar/*.css', dest: 'dist/sidebar' }
      ],
      flatten: false
    })
  ]
};