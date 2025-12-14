<template>
  <div class="p-6 h-full flex flex-col">
    <div class="max-w-2xl mx-auto w-full">
      <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
        <i class="fa fa-microphone text-blue-500"></i>
        <span>语音生成</span>
      </h2>

      <div class="border border-gray-200 rounded-lg p-4 mb-6">
        <label class="block text-sm font-medium mb-2">输入文本</label>
        <textarea 
          class="w-full border border-gray-200 rounded-lg p-3 min-h-[120px] focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 resize-none text-sm"
          v-model="textContent"
          placeholder="请输入要转换为语音的文本内容..."
        ></textarea>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-6">
        <div>
          <label class="block text-sm font-medium mb-2">语音类型</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="voiceType"
          >
            <option value="female">甜美女生</option>
            <option value="male">阳光男生</option>
            <option value="child">卡通童声</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">语速</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="speed"
          >
            <option value="slow">慢速</option>
            <option value="normal">正常</option>
            <option value="fast">快速</option>
          </select>
        </div>
      </div>

      <div class="flex justify-center">
        <button 
          class="bg-blue-500 text-white px-6 py-3 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
          @click="generateVoice"
          :disabled="!textContent.trim()"
        >
          <i class="fa fa-play"></i>
          <span>生成语音</span>
        </button>
      </div>

      <!-- 生成结果展示 -->
      <div v-if="voiceUrl" class="mt-6 text-center">
        <p class="text-sm font-medium mb-2">生成结果</p>
        <audio controls class="w-full">
          <source :src="voiceUrl" type="audio/mp3">
          您的浏览器不支持音频播放
        </audio>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

// 文本内容
const textContent = ref('');
// 语音类型
const voiceType = ref('female');
// 语速
const speed = ref('normal');
// 生成的语音URL
const voiceUrl = ref('');

// 生成语音
const generateVoice = async () => {
  try {
    // 模拟API请求（实际项目中替换为真实接口）
    const response = await axios.post('/api/voice/generate', {
      text: textContent.value,
      voiceType: voiceType.value,
      speed: speed.value
    });

    // 模拟返回语音URL
    voiceUrl.value = response.data.voiceUrl || 'https://example.com/voice.mp3';
  } catch (error) {
    console.error('生成语音失败:', error);
    alert('生成语音失败，请重试！');
  }
};
</script>