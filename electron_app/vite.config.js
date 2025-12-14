import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,        // 和 main.js 中 loadURL 的端口一致
    host: '127.0.0.1', // 避免 localhost 解析异常
    cors: true,        // 解决 PrivateGPT API 跨域问题
    open: false        // 不自动打开浏览器
  },
  build: {
    outDir: 'dist',    // 打包到当前目录的 dist 文件夹
    emptyOutDir: true
  }
});