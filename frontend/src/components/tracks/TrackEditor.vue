<template>
  <div class="track-editor" :style="{ borderLeft: `4px solid ${track.color}` }">
    <!-- 音轨头部控制 -->
    <div class="track-header">
      <div class="track-info">
        <div class="track-title">
          <EditableText 
            :value="track.name" 
            @change="updateTrackName"
            placeholder="音轨名称"
          />
        </div>
        <div class="track-type">{{ getTrackTypeLabel(track.type) }}</div>
      </div>
      
      <div class="track-controls">
        <a-space>
          <!-- 静音/独奏按钮 -->
          <a-button 
            size="small" 
            :type="track.muted ? 'primary' : 'default'"
            @click="toggleMute"
          >
            <template #icon>
              <SoundOutlined v-if="!track.muted" />
              <StopOutlined v-else />
            </template>
          </a-button>
          
          <a-button 
            size="small" 
            :type="track.solo ? 'primary' : 'default'"
            @click="toggleSolo"
          >
            S
          </a-button>
          
          <!-- 音量控制 -->
          <div class="volume-control">
            <SoundOutlined />
            <a-slider 
              v-model:value="trackVolume" 
              :min="0" 
              :max="1" 
              :step="0.1"
              style="width: 80px; margin: 0 8px;"
              @change="updateVolume"
            />
            <span class="volume-label">{{ Math.round(trackVolume * 100) }}%</span>
          </div>
          
          <!-- 添加音频片段 -->
          <a-dropdown>
            <a-button size="small">
              <template #icon><PlusOutlined /></template>
              添加
            </a-button>
            <template #overlay>
              <a-menu @click="handleAddClip">
                <a-menu-item key="upload">上传音频文件</a-menu-item>
                <a-menu-item key="generate">生成空白片段</a-menu-item>
                <a-menu-item key="record">录制音频</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </div>
    </div>
    
    <!-- 音轨时间线 -->
    <div class="track-timeline" ref="timelineRef">
      <!-- 网格背景 -->
      <div class="timeline-grid">
        <div 
          v-for="n in Math.ceil(viewDuration)"
          :key="n"
          class="grid-line"
          :style="{ left: `${(n / viewDuration) * 100}%` }"
        />
      </div>
      
      <!-- 音频片段 -->
      <AudioClipItem
        v-for="clip in track.clips"
        :key="clip.id"
        :clip="clip"
        :track-type="track.type"
        :view-duration="viewDuration"
        :pixels-per-second="pixelsPerSecond"
        @update="updateClip"
        @delete="deleteClip"
        @move="moveClip"
        @resize="resizeClip"
        @select-exclusive="handleExclusiveSelect"
      />
      
      <!-- 播放头 -->
      <div 
        class="track-playhead" 
        :style="{ left: `${(currentTime / viewDuration) * 100}%` }"
      ></div>
      
      <!-- 拖拽区域提示 -->
      <div 
        v-if="isDragOver" 
        class="drop-zone"
        @drop="handleDrop"
        @dragover.prevent
        @dragenter.prevent
        @dragleave="isDragOver = false"
      >
        <CloudUploadOutlined />
        <span>拖拽音频文件到此处</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  SoundOutlined,
  StopOutlined,
  PlusOutlined,
  CloudUploadOutlined
} from '@ant-design/icons-vue'

import EditableText from '../common/EditableText.vue'
import AudioClipItem from './AudioClipItem.vue'
import { uploadMultipleAudioFiles } from '../../api/audioFiles'

const props = defineProps({
  track: {
    type: Object,
    required: true
  },
  viewDuration: {
    type: Number,
    default: 60
  },
  pixelsPerSecond: {
    type: Number,
    default: 10
  },
  currentTime: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['update-track', 'update-clip', 'delete-clip', 'add-clip', 'select-exclusive'])

const timelineRef = ref(null)
const isDragOver = ref(false)
const trackVolume = ref(props.track.volume)

// 计算属性
const trackTypeLabels = {
  dialogue: '角色对话',
  environment: '环境音效', 
  background: '背景音乐'
}

function getTrackTypeLabel(type) {
  return trackTypeLabels[type] || type
}

// 监听音量变化
watch(() => props.track.volume, (newVolume) => {
  trackVolume.value = newVolume
})

// 音轨控制方法
function updateTrackName(newName) {
  emit('update-track', props.track.id, { name: newName })
}

function toggleMute() {
  emit('update-track', props.track.id, { muted: !props.track.muted })
}

function toggleSolo() {
  emit('update-track', props.track.id, { solo: !props.track.solo })
}

function updateVolume(volume) {
  emit('update-track', props.track.id, { volume })
}

// 音频片段操作
function updateClip(clipId, updates) {
  emit('update-clip', props.track.id, clipId, updates)
}

function deleteClip(clipId) {
  emit('delete-clip', props.track.id, clipId)
}

function moveClip(clipId, newStartTime) {
  // 确保不会移动到负时间
  const startTime = Math.max(0, newStartTime)
  emit('update-clip', props.track.id, clipId, { startTime })
}

function resizeClip(clipId, newDuration) {
  // 确保持续时间为正数
  const duration = Math.max(0.1, newDuration)
  emit('update-clip', props.track.id, clipId, { duration })
}

function handleExclusiveSelect(clipId) {
  // 向上传递事件，让多轨编辑器处理全局选中状态
  emit('select-exclusive', props.track.id, clipId)
}

// 添加音频片段
function handleAddClip({ key }) {
  switch (key) {
    case 'upload':
      // 触发文件上传
      openFileDialog()
      break
    case 'generate':
      // 生成空白片段
      generateBlankClip()
      break
    case 'record':
      // 开始录制
      startRecording()
      break
  }
}

function openFileDialog() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'audio/*'
  input.multiple = true
  
  input.onchange = (event) => {
    const files = Array.from(event.target.files)
    handleFileUpload(files)
  }
  
  input.click()
}

async function handleFileUpload(files) {
  try {
    message.loading('正在上传音频文件...', 0)
    
    const result = await uploadMultipleAudioFiles(files)
    
    message.destroy()
    
    if (result.success) {
      let successCount = 0
      
      result.data.forEach((uploadResult, index) => {
        if (uploadResult.upload_success) {
          const clipData = {
            name: uploadResult.original_name.replace(/\.[^/.]+$/, ''),
            filePath: uploadResult.file_path,
            startTime: findNextAvailableTime() + successCount * 0.5,
            duration: uploadResult.duration || 3.0
          }
          
          emit('add-clip', props.track.id, clipData)
          successCount++
        }
      })
      
      if (successCount > 0) {
        message.success(`成功添加 ${successCount} 个音频片段`)
      }
      
      const failedCount = files.length - successCount
      if (failedCount > 0) {
        message.warning(`${failedCount} 个文件上传失败`)
      }
    }
  } catch (error) {
    message.destroy()
    console.error('文件上传失败:', error)
    message.error('文件上传失败')
  }
}

function generateBlankClip() {
  const clipData = {
    name: '空白片段',
    filePath: '',
    startTime: findNextAvailableTime(),
    duration: 3.0
  }
  
  emit('add-clip', props.track.id, clipData)
}

function startRecording() {
  message.info('录制功能暂未实现')
  // TODO: 实现录制功能
}

function findNextAvailableTime() {
  if (props.track.clips.length === 0) {
    return 0
  }
  
  // 找到最后一个片段的结束时间
  const lastClip = props.track.clips.reduce((latest, clip) => {
    const endTime = clip.startTime + clip.duration
    return endTime > latest ? endTime : latest
  }, 0)
  
  return lastClip + 0.5 // 添加0.5秒间隙
}

// 拖拽处理
function handleDrop(event) {
  event.preventDefault()
  isDragOver.value = false
  
  // 获取时间线的位置信息
  const timelineRect = timelineRef.value.getBoundingClientRect()
  const dropX = event.clientX - timelineRect.left
  const dropTime = (dropX / timelineRect.width) * props.viewDuration
  
  // 尝试获取拖拽的音频文件数据
  try {
    const dragData = event.dataTransfer.getData('application/json')
    if (dragData) {
      const data = JSON.parse(dragData)
      if (data.type === 'audio-file') {
        // 处理从资源库拖拽的音频文件
        handleAudioFileDrop(data.file, Math.max(0, dropTime))
        return
      }
    }
  } catch (error) {
    console.warn('解析拖拽数据失败:', error)
  }
  
  // 处理从外部拖拽的文件
  const files = Array.from(event.dataTransfer.files)
  const audioFiles = files.filter(file => file.type.startsWith('audio/'))
  
  if (audioFiles.length > 0) {
    handleFileUpload(audioFiles)
  } else {
    message.warning('请拖拽音频文件')
  }
}

// 处理从资源库拖拽的音频文件
function handleAudioFileDrop(audioFile, startTime) {
  const fileName = audioFile.original_name || audioFile.filename || '音频片段'
  const clipData = {
    name: fileName.replace(/\.[^/.]+$/, ''),
    filePath: audioFile.file_id,
    startTime: startTime,
    duration: audioFile.duration || 3.0
  }
  
  emit('add-clip', props.track.id, clipData)
  message.success(`已添加音频文件到 ${getTrackTypeLabel(props.track.type)} 音轨`)
}

// 监听拖拽事件
function setupDragListeners() {
  const timeline = timelineRef.value
  if (!timeline) return
  
  timeline.addEventListener('dragenter', (e) => {
    e.preventDefault()
    isDragOver.value = true
  })
  
  timeline.addEventListener('dragleave', (e) => {
    e.preventDefault()
    // 只有当拖拽离开整个容器时才隐藏提示
    if (!timeline.contains(e.relatedTarget)) {
      isDragOver.value = false
    }
  })
}

// 生命周期
import { onMounted } from 'vue'

onMounted(() => {
  setupDragListeners()
})
</script>

<style scoped>
.track-editor {
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  min-height: 80px;
}

.track-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #333;
  border-bottom: 1px solid #444;
}

.track-info {
  flex: 1;
}

.track-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
  color: #fff;
}

.track-type {
  font-size: 12px;
  color: #999;
}

.track-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 4px;
}

.volume-label {
  font-size: 12px;
  color: #999;
  min-width: 35px;
}

.track-timeline {
  position: relative;
  height: 60px;
  background: #1e1e1e;
  overflow: hidden;
}

.timeline-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.grid-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #444;
}

.track-playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4d4f;
  z-index: 15;
  pointer-events: none;
  transition: left 0.1s ease;
}

.drop-zone {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(24, 144, 255, 0.2);
  border: 2px dashed #1890ff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #1890ff;
  font-size: 14px;
  z-index: 10;
}

.drop-zone span {
  margin-top: 8px;
}

/* 自定义滑块样式 */
:deep(.ant-slider) {
  margin: 0;
  width: 60px;
}

:deep(.ant-slider-rail) {
  background: #444;
}

:deep(.ant-slider-track) {
  background: #1890ff;
}

:deep(.ant-slider-handle) {
  border-color: #1890ff;
  background: #1890ff;
}

:deep(.ant-slider-handle:hover) {
  border-color: #40a9ff;
}

/* 自定义按钮样式 */
:deep(.ant-btn) {
  border-color: #444;
  background: #333;
  color: #ccc;
}

:deep(.ant-btn:hover) {
  border-color: #555;
  background: #404040;
  color: #fff;
}

:deep(.ant-btn-primary) {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

:deep(.ant-btn-primary:hover) {
  background: #40a9ff;
  border-color: #40a9ff;
}
</style> 