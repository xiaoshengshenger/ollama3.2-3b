<template>
  <header class="border-b border-gray-200 py-3 px-4 flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center">
        <i class="fa fa-comments text-white text-lg"></i>
      </div>
      <h1 class="text-xl font-bold">AI Studio</h1>
    </div>
    <div class="flex items-center gap-3">
      <button class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
        <i class="fa fa-upload"></i>
      </button>
      <button class="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
        <i class="fa fa-cog"></i>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts"></script>