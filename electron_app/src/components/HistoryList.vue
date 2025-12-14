<template>
  <div class="w-full bg-white text-black">
    <!-- 分割线 -->
    <div class="h-[1px] bg-gray-200 ml-[20px] mr-[20px]"></div>
    <!-- 历史记录标题 -->
    <div class="ml-[5px] mt-[10px] text-sm text-gray-500 font-medium">历史记录</div>

    <!-- 历史记录列表：简化层级，统一样式控制 -->
    <div class="ml-[5px] mt-[5px] mr-[5px]">
      <div
        v-for="item in historyList"
        :key="item.id"
        class="flex items-center justify-between gap-2 h-[35px] mt-[5px] px-[5px] rounded-lg cursor-pointer transition-colors duration-200 hover:bg-gray-200"
        :class="{
          // 选中样式：用浅蓝背景（更明显），也可改用 bg-gray-200 加深灰色
          'bg-gray-200': appStore.currentHistoryId === item.id,
        }"
        @click="handleHistoryItemClick(item.id)"
      >
        <!-- 左侧：文档图标 + 标题 -->
        <div class="flex items-center gap-2 flex-1 min-w-0">
          <i class="fa fa-file text-blue-500 text-base"></i>
          <p class="text-sm font-medium text-black truncate">
            {{ item.title }}
          </p>
        </div>
        <!-- 右侧：三个点图标（单独处理冒泡和样式） -->
        <i 
          class="fa fa-ellipsis-v text-gray-400 text-base more-icon cursor-pointer transition-colors"
          @click.stop="handleMoreClick(item.id)"
        ></i>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '../stores/appStore';
import { storeToRefs } from 'pinia';

// 初始化 Pinia store
const appStore = useAppStore();
const { historyList } = storeToRefs(appStore);

// 处理历史记录项点击事件
const handleHistoryItemClick = (id: string) => {
  appStore.setCurrentHistoryId(id);
};

// 处理更多操作点击
const handleMoreClick = (id: string) => {
  console.log('更多操作，历史记录ID：', id);
};
</script>

<style scoped>
/* 可选：自定义滚动条（若列表过长） */
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