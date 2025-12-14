// src/main.js
import { createApp } from 'vue';
import { createPinia } from 'pinia';
// 引入根组件
import App from './App.vue';
// 引入全局样式（Tailwind + 自定义样式）
import './assets/index.css';
// 引入font-awesome图标库
import '@fortawesome/fontawesome-free/css/all.css';

// 创建Vue应用实例
const app = createApp(App);
// 创建Pinia实例（状态管理）
const pinia = createPinia();

// 安装Pinia插件
app.use(pinia);
// 挂载应用到#app节点
app.mount('#app');