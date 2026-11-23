import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// Su GitHub Pages il sito vive in /<nome-repo>/: il workflow passa BASE_PATH.
export default defineConfig({
  base: process.env.BASE_PATH ?? '/',
  plugins: [svelte()],
  build: { target: 'es2022', sourcemap: true },
});
