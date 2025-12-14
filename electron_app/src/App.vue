<template>
  <div class="flex flex-col h-screen bg-white text-black overflow-hidden">
    <!-- 头部组件 -->
    <Header />

    <!-- 主内容区 -->
    <div class="flex flex-1 overflow-hidden">
      <!-- 左侧列表区 -->
      <aside class="w-64 border-r border-gray-200 bg-white flex-shrink-0 overflow-y-auto">
        <!-- 我的聊天列表 -->
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-xs font-bold uppercase tracking-wider mb-3 text-gray-500">我的聊天</h2>
          <button 
            class="w-full flex items-center gap-2 px-3 py-2.5 bg-gray-100 rounded-lg text-sm font-medium mb-3 hover:bg-gray-200 transition-colors"
            @click="createNewChat"
          >
            <i class="fa fa-plus-circle text-blue-500"></i>
            <span>新对话</span>
          </button>
          <div class="space-y-1">
            <div 
              v-for="item in appStore.chatList" 
              :key="item.key"
              class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm cursor-pointer hover:bg-gray-100 transition-colors"
              :class="{ 'bg-gray-100 font-medium': appStore.currentView === item.key }"
              @click="appStore.switchView(item.key)"
            >
              <i :class="`fa ${item.icon} text-blue-500`"></i>
              <span>{{ item.title }}</span>
            </div>
          </div>
        </div>

        <!-- 历史记录（原我的知识库） -->
        <HistoryList />
      </aside>

      <!-- 右侧功能区（根据currentView渲染对应组件） -->
      <main class="flex-1 overflow-hidden">
        <!-- 聊天视图 -->
        <ChatView v-if="appStore.currentView === 'llmModel'" />
        <!-- 语音生成视图 -->
        <VoiceView v-if="appStore.currentView === 'soulModel'" />
        <!-- 图像生成视图 -->
        <ImageView v-if="appStore.currentView === 'imgModel'" />
        <!-- 视频生成视图 -->
        <VideoView v-if="appStore.currentView === 'vidolModel'" />
      </main>
    </div>

    <!-- 底部组件 -->
    <Footer />
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from './stores/appStore';
import Header from './components/Header.vue';
import Footer from './components/Footer.vue';
import ChatView from './views/ChatView.vue';
import VoiceView from './views/VoiceView.vue';
import ImageView from './views/ImageView.vue';
import VideoView from './views/VideoView.vue';
import HistoryList from './components/HistoryList.vue';

// 初始化Pinia store
const appStore = useAppStore();

// 创建新对话
const createNewChat = () => {
  const newId = Date.now().toString();
  const newHistory = {
    id: newId,
    title: "新对话",
    icon: "fa-comments",
    list: []
  };
  appStore.addHistory(newHistory);
};
</script>

<style scoped>
/* 自定义滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>