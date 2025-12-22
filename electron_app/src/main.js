// src/main.js
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import '@fortawesome/fontawesome-free/css/all.css';
// v4.x 版本需导入 createPersistedState 函数（而非直接导入插件）
import { createPersistedState } from 'pinia-plugin-persistedstate';

const app = createApp(App);
const pinia = createPinia();

// 2. 注册插件到 Pinia
pinia.use(createPersistedState());

app.use(pinia);
app.mount('#app');