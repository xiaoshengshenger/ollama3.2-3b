<template>
  <div class="p-6 h-full flex flex-col">
    <div class="max-w-2xl mx-auto w-full">
      <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
        <i class="fa fa-picture-o text-blue-500"></i>
        <span>图像生成</span>
      </h2>

      <div class="border border-gray-200 rounded-lg p-4 mb-6">
        <label class="block text-sm font-medium mb-2">图像描述</label>
        <textarea 
          class="w-full border border-gray-200 rounded-lg p-3 min-h-[120px] focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 resize-none text-sm"
          v-model="prompt"
          placeholder="请输入图像的描述内容（如：一只可爱的卡通猫，坐在草地上，蓝天白云）..."
        ></textarea>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label class="block text-sm font-medium mb-2">图像风格</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="style"
          >
            <option value="cartoon">卡通风格</option>
            <option value="realistic">现实主义</option>
            <option value="abstract">抽象艺术</option>
            <option value="anime">动漫风格</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">图像尺寸</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="size"
          >
            <option value="512x512">512×512</option>
            <option value="768x768">768×768</option>
            <option value="1024x1024">1024×1024</option>
          </select>
        </div>
      </div>

      <div class="flex justify-center">
        <button 
          class="bg-blue-500 text-white px-6 py-3 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
          @click="generateImage"
          :disabled="!prompt.trim()"
        >
          <i class="fa fa-magic"></i>
          <span>生成图像</span>
        </button>
      </div>

      <!-- 生成结果展示 -->
      <div v-if="imageUrl" class="mt-6 text-center">
        <p class="text-sm font-medium mb-2">生成结果</p>
        <img :src="imageUrl" alt="生成的图像" class="rounded-lg shadow-md max-w-full h-auto mx-auto">
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

// 图像描述
const prompt = ref('');
// 图像风格
const style = ref('cartoon');
// 图像尺寸
const size = ref('512x512');
// 生成的图像URL
const imageUrl = ref('');

// 生成图像
const generateImage = async () => {
  try {
    // 模拟API请求（实际项目中替换为真实接口）
    const response = await axios.post('/api/image/generate', {
      prompt: prompt.value,
      style: style.value,
      size: size.value
    });

    // 模拟返回图像URL
    imageUrl.value = response.data.imageUrl || 'https://example.com/image.jpg';
  } catch (error) {
    console.error('生成图像失败:', error);
    alert('生成图像失败，请重试！');
  }
};
</script>