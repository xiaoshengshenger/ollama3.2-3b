<template>
  <header class="border-b border-gray-200 py-3 px-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center">
        <i class="fa fa-comments text-white text-lg"></i>
      </div>
      <h1 class="text-xl font-bold">AI Studio</h1>
    </div>
    <div class="flex items-center gap-3">
      <!-- 激活码按钮 -->
      <button
        class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
        @click="isActivationCodeOpen = true"
      >
        <i class="fa fa-key mr-1"></i>
        <span class="hidden sm:inline">激活码</span>
      </button>
      <!-- 知识库按钮 -->
      <button
        class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
        @click="isKnowledgeBaseOpen = true"
      >
        <i class="fa fa-book mr-1"></i>
        <span class="hidden sm:inline">知识库</span>
      </button>
    </div>

    <!-- 激活码弹窗组件 -->
    <ActivationCodeModal v-model="isActivationCodeOpen" />
    <!-- 知识库弹窗组件 -->
    <KnowledgeBaseModal v-model="isKnowledgeBaseOpen" />

  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import ActivationCodeModal from './ActivationCodeModal.vue';
import KnowledgeBaseModal from './KnowledgeBaseModal.vue';

// 控制各弹窗的显隐状态
const isActivationCodeOpen = ref(false);
const isKnowledgeBaseOpen = ref(false);
</script>