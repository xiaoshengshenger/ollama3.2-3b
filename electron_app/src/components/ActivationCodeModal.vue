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
            v-model="activationCode" 
            :class="{ 'border-red-500': hasError }" 
          />
          <!-- 错误提示 -->
          <p v-if="hasError" class="mt-1 text-sm text-red-500">{{ errorMessage }}</p>
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
            @click="validateActivationCode"  
            :disabled="isVerifying"  
          >
            <span v-if="!isVerifying">验证激活</span>
            <span v-else>验证中...</span> 
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import useCode from '../hook/useCode';
import { useAppStore } from '../stores/appStore';
const appStore = useAppStore();

const { validateCode } = useCode();

// 定义props，接收父组件的显隐状态
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
});

// 定义emit，向父组件发送状态更新事件
const emit = defineEmits(['update:modelValue', 'validateSuccess']); // 新增验证成功的emit

// 关闭弹窗的方法
const closeModal = () => {
  activationCode.value = '';
  emit('update:modelValue', false);
};

// 激活码相关响应式数据
const activationCode = ref(''); // 绑定输入框的激活码
const hasError = ref(false); // 是否显示错误提示
const errorMessage = ref(''); // 错误提示文本
const isVerifying = ref(false); // 是否正在验证

// 激活码校验方法
const validateActivationCode = async () => {
  // 1. 清空之前的错误状态
  hasError.value = false;
  errorMessage.value = '';

  // 2. 前端基础校验
  if (!activationCode.value.trim()) {
    hasError.value = true;
    errorMessage.value = '请输入激活码';
    return;
  }

  // 3. 标记为验证中状态
  isVerifying.value = true;

  try {
    // 4. 模拟向后端发送校验请求（替换为你的真实接口）
    // 这里只是示例，你需要替换成实际的接口调用
    const result = await validateCode(activationCode.value);

    // 5. 处理校验结果
    if (result.is_valid) {
      // 验证成功：关闭弹窗并通知父组件
      appStore.updateCode(activationCode.value); // 更新store中的激活码
      closeModal();
      // 可添加成功提示（如Toast）
      alert('激活成功');
    } else {
      // 验证失败：显示错误信息
      hasError.value = true;
      errorMessage.value = "激活失败";
    }
  } catch (error) {
    // 6. 捕获请求异常
    hasError.value = true;
    errorMessage.value = '激活失败，请稍后重试';
    console.error('激活码验证失败:', error);
  } finally {
    // 7. 重置验证中状态
    isVerifying.value = false;
  }
};
</script>