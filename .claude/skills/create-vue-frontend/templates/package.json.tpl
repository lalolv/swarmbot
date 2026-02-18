{
  "name": "{package_name}",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "preview": "vite preview",
    "typecheck": "vue-tsc --noEmit"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "pinia": "^2.3.1",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.4",
    "@tailwindcss/vite": "^4.1.8",
    "tailwindcss": "^4.1.8",
    "typescript": "~5.8.3",
    "vue-tsc": "^2.2.10",
    "vite": "^6.3.5"
  }
}
