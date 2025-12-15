<template>
  <!-- 弹窗遮罩层 -->
  <div v-if="modelValue" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click="closeModal">
    <!-- 弹窗内容区（阻止事件冒泡） -->
    <div class="bg-white rounded-lg w-full max-w-md p-6 shadow-lg" @click.stop>
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-800">激活码验证</h3>
        <button class="text-gray-500 hover:text-gray-700" @click="closeModal">
          <i class="fa fa-times"></i>
        </button>
      </div>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">输入激活码</label>
          <input
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="请输入您的激活码"
          />
        </div>
        <div class="flex justify-end space-x-3 pt-2">
          <button
            class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
            @click="closeModal"
          >
            取消
          </button>
          <button
            class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            验证激活
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">

// 定义props，接收父组件的显隐状态
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

// 定义emit，向父组件发送状态更新事件
const emit = defineEmits(['update:modelValue']);

// 关闭弹窗的方法
const closeModal = () => {
  emit('update:modelValue', false);
};
</script>