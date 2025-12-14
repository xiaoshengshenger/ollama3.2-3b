<template>
  <div class="mb-8">
    <h2 class="text-xs font-bold text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-2">
      <span class="cute-dot"></span>
      <span>我的聊天</span>
    </h2>
    <button class="w-full btn-secondary text-left mb-4 text-sm">
      <i class="fa fa-plus-circle text-xs mr-2 text-accent"></i>
      <span class="font-bold">新对话 ✨</span>
    </button>
    <div class="space-y-3">
      <div 
        v-for="item in chatList" 
        :key="item.key"
        class="card"
        :class="{ 'border-primary/50 bg-primary/5': currentView === item.key }"
        @click="handleChatItemClick(item.key)"
      >
        <div class="flex items-center gap-2 mb-2">
          <i :class="`fa ${item.icon} text-primary text-lg`"></i>
          <p class="text-sm font-bold truncate">{{ item.title }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

import { useAppStore } from '../stores/appStore';
import { storeToRefs } from 'pinia';

const appStore = useAppStore();
const { chatList,currentView } = storeToRefs(appStore);

const handleChatItemClick = (key: string) => {
  appStore.switchView(key);
};
</script>