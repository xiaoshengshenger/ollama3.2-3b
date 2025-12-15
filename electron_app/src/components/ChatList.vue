<template>
  <div class="ml-[10px] mt-[10px] mb-[10px]">
    <div class="space-y-1">
      <div 
        v-for="item in chatList" 
        :key="item.key"
        class="flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm cursor-pointer hover:bg-gray-200 transition-colors"
        :class="{ 'bg-gray-100 font-medium': currentView === item.key }"
        @click="handleChatItemClick(item.key)"
      >
        <i :class="`fa ${item.icon} text-blue-500`"></i>
        <span>{{ item.title }}</span>
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