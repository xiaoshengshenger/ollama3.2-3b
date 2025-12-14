<template>
  <aside class="w-[280px] border-r border-primary/10 bg-white/50 p-4 hidden md:block overflow-y-auto scrollbar-hide">
    <ChatList />
    <HistoryList />
  </aside>
</template>

<script setup lang="ts">
import ChatList from './ChatList.vue';
import HistoryList from './HistoryList.vue';
</script>