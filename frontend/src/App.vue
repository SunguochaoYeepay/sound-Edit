<template>
  <div id="app">
    <a-layout>
      <a-layout-header>
        <h1 style="color: #fff;">Sound-Edit 多轨音频编辑器</h1>
      </a-layout-header>
      <a-layout-content style="padding: 0; min-height: 80vh;">
        <MultitrackEditor />
      </a-layout-content>
    </a-layout>
  </div>
</template>

<script setup>
import MultitrackEditor from './components/MultitrackEditor.vue'
</script>

<style>
#app {
  min-height: 100vh;
  background: #f0f2f5;
}
</style>
