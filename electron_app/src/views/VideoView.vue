<template>
  <div class="p-6 h-full flex flex-col">
    <div class="max-w-2xl mx-auto w-full">
      <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
        <i class="fa fa-film text-blue-500"></i>
        <span>视频生成</span>
      </h2>

      <div class="border border-gray-200 rounded-lg p-4 mb-6">
        <label class="block text-sm font-medium mb-2">视频描述</label>
        <textarea 
          class="w-full border border-gray-200 rounded-lg p-3 min-h-[120px] focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 resize-none text-sm"
          v-model="prompt"
          placeholder="请输入视频的描述内容（如：一只小鸟从天空飞过，落在树枝上，背景是森林）..."
        ></textarea>
      </div>

      <div class="grid grid-cols-3 gap-4 mb-6">
        <div>
          <label class="block text-sm font-medium mb-2">视频风格</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="style"
          >
            <option value="animation">动画</option>
            <option value="realistic">真人实拍</option>
            <option value="3d">3D建模</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">视频时长</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="duration"
          >
            <option value="5">5秒</option>
            <option value="10">10秒</option>
            <option value="15">15秒</option>
            <option value="30">30秒</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium mb-2">分辨率</label>
          <select 
            class="w-full border border-gray-200 rounded-lg p-3 focus:outline-none focus:border-blue-300 focus:ring-1 focus:ring-blue-300 text-sm"
            v-model="resolution"
          >
            <option value="720p">720P</option>
            <option value="1080p">1080P</option>
            <option value="4k">4K</option>
          </select>
        </div>
      </div>

      <div class="flex justify-center">
        <button 
          class="bg-blue-500 text-white px-6 py-3 rounded-lg text-sm font-medium hover:bg-blue-600 transition-colors flex items-center gap-2"
          @click="generateVideo"
          :disabled="!prompt.trim()"
        >
          <i class="fa fa-play-circle"></i>
          <span>生成视频</span>
        </button>
      </div>

      <!-- 生成结果展示 -->
      <div v-if="videoUrl" class="mt-6 text-center">
        <p class="text-sm font-medium mb-2">生成结果</p>
        <video controls class="w-full rounded-lg shadow-md mx-auto">
          <source :src="videoUrl" type="video/mp4">
          您的浏览器不支持视频播放
        </video>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import axios from 'axios';

// 视频描述
const prompt = ref('');
// 视频风格
const style = ref('animation');
// 视频时长
const duration = ref('5');
// 分辨率
const resolution = ref('720p');
// 生成的视频URL
const videoUrl = ref('');

// 生成视频
const generateVideo = async () => {
  try {
    // 模拟API请求（实际项目中替换为真实接口）
    const response = await axios.post('/api/video/generate', {
      prompt: prompt.value,
      style: style.value,
      duration: duration.value,
      resolution: resolution.value
    });

    // 模拟返回视频URL
    videoUrl.value = response.data.videoUrl || 'https://example.com/video.mp4';
  } catch (error) {
    console.error('生成视频失败:', error);
    alert('生成视频失败，请重试！');
  }
};
</script>