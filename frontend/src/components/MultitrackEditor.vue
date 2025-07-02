<template>
  <div class="multitrack-editor">
    <!-- 主编辑区域 -->
    <div class="editor-container">
      <!-- 上半部分：资源库 + 预览 + 项目信息 -->
      <div class="top-section">
        <!-- 资源库面板 -->
        <ResourcePanel
          :audio-files="audioFiles"
          :loading="loadingAudioFiles"
          :search-keyword="searchKeyword"
          :playing-file-id="playingFileId"
          :active-tab="activeAudioTab"
          @refresh="refreshAudioFiles"
          @tab-change="activeAudioTab = $event"
          @upload="handleBeforeUpload"
          @search="handleSearch"
          @select-file="selectAudioFile"
          @play-file="playAudioFile"
          @delete-file="handleDeleteAudioFile"
          @add-to-project="handleAddAudioToProject"
          @drag-start="handleDragStart"
          @drag-end="handleDragEnd"
        />

        <!-- 预览面板 -->
        <PreviewPanel
          :current-time="currentTime"
          :total-duration="currentProject.project.totalDuration || 0"
          :is-playing="isPlaying"
          :is-loading="isLoadingPreview"
          :has-project="!!currentProject.project.id"
          @toggle-play="togglePlay"
          @stop="stopPlayback"
          @time-change="currentTime = $event"
        />

        <!-- 项目信息面板 -->
        <ProjectInfoPanel
          :project="currentProject.project"
          :selected-clip="selectedClip"
          :has-project="!!currentProject.project.id"
          :export-loading="exportLoading"
          @create-project="showCreateProject = true"
          @open-project="showProjectList = true"
          @save-project="saveCurrentProject"
          @export-project="exportCurrentProject"
          @update-project="updateProjectInfo"
          @update-clip="updateSelectedClip"
          @clear-selection="clearSelectedClip"
        />
      </div>

      <!-- 下半部分：音轨编辑器 -->
      <div class="bottom-section">
        <TimelineEditor
          v-if="currentProject.project.id"
          ref="timelineEditor"
          :tracks="currentProject.tracks"
          :current-time="currentTime"
          :zoom-level="zoomLevel"
          :view-duration="viewDuration"
          :pixels-per-second="pixelsPerSecond"
          :timeline-width="timelineWidth"
          :total-duration="currentProject.project.totalDuration || 60"
          :min-zoom="minZoom"
          :max-zoom="maxZoom"
          @zoom-change="handleZoomChange"
          @timeline-scroll="handleTimelineScroll"
          @update-track="updateTrack"
          @update-clip="updateClip"
          @delete-clip="deleteClip"
          @add-clip="addClip"
          @select-exclusive="handleExclusiveSelect"
        />

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <a-empty description="请创建或打开一个项目开始编辑">
            <a-button type="primary" @click="showCreateProject = true">创建新项目</a-button>
          </a-empty>
        </div>
      </div>
    </div>

    <!-- 对话框组件 -->
    <ProjectCreateForm
      :open="showCreateProject"
      @update:open="showCreateProject = $event"
      @success="handleProjectCreated"
    />

    <ProjectList
      :open="showProjectList"
      @update:open="showProjectList = $event"
      @select="handleProjectSelected"
    />

    <ImportJsonForm
      :open="showImportDialog"
      @update:open="showImportDialog = $event"
      @success="handleImportSuccess"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { h } from 'vue'

// 导入子组件
import ResourcePanel from './panels/ResourcePanel.vue'
import PreviewPanel from './panels/PreviewPanel.vue'
import ProjectInfoPanel from './panels/ProjectInfoPanel.vue'
import TimelineEditor from './panels/TimelineEditor.vue'
import ProjectCreateForm from './dialogs/ProjectCreateForm.vue'
import ProjectList from './dialogs/ProjectList.vue'
import ImportJsonForm from './dialogs/ImportJsonForm.vue'
import EditableText from './common/EditableText.vue'

// 导入API服务
import { uploadMultipleAudioFiles, uploadAudioFile, listAudioFiles, deleteAudioFile } from '../api/audioFiles'
import { 
  createProject,
  loadProject,
  saveProject,
  listProjects,
  deleteProject,
  convertToStandardFormat,
  validateProject,
  exportProject,
  getExportStatus,
  downloadExportedAudio,
  generatePreviewAudio,
  getPreviewAudioUrl,
  deletePreviewFile,
  createEmptyProject,
  calculateProjectDuration,
  formatTime,
  generateId
} from '../api/multitrackProject'

// ========== 响应式数据 ==========
// 音频文件相关
const audioFiles = ref([])
const loadingAudioFiles = ref(false)
const searchKeyword = ref('')
const activeAudioTab = ref('dialogue')
const playingFileId = ref(null)

// 项目相关
const currentProject = reactive(createEmptyProject())

// 播放控制
const currentTime = ref(0)
const isPlaying = ref(false)
const isLoadingPreview = ref(false)

// 选择状态 
const selectedClip = computed(() => {
  for (const track of currentProject.tracks) {
    for (const clip of track.clips) {
      if (clip.selected) {
        return { ...clip, trackType: track.type }
      }
    }
  }
  return null
})

// 时间轴相关
const zoomLevel = ref(1)
const viewDuration = computed(() => 60 / zoomLevel.value)
const pixelsPerSecond = computed(() => 50 * zoomLevel.value)
const timelineWidth = computed(() => Math.max(3000, (currentProject.project.totalDuration || 60) * pixelsPerSecond.value))
const minZoom = ref(0.25)
const maxZoom = ref(8)

// 对话框显示状态
const showCreateProject = ref(false)
const showProjectList = ref(false)
const showImportDialog = ref(false)
const exportLoading = ref(false)

// 音频播放相关
let currentAudio = null
let currentAudioId = null

// 拖拽状态
const draggedAudioFile = ref(null)
const isDragging = ref(false)

// ========== 计算属性 ==========
const filteredDialogueFiles = computed(() => 
  filterFilesByKeyword(audioFiles.value.filter(file => file.category === 'dialogue' || !file.category))
)

const filteredEnvironmentFiles = computed(() => 
  filterFilesByKeyword(audioFiles.value.filter(file => file.category === 'environment'))
)

const filteredThemeFiles = computed(() => 
  filterFilesByKeyword(audioFiles.value.filter(file => file.category === 'theme'))
)

// ========== 方法定义 ==========

// 根据关键词过滤文件
function filterFilesByKeyword(files) {
  if (!searchKeyword.value) return files
  
  const keyword = searchKeyword.value.toLowerCase()
  return files.filter(file => 
    (file.original_name || file.filename).toLowerCase().includes(keyword)
  )
}

// 音频文件管理
async function refreshAudioFiles() {
  loadingAudioFiles.value = true
  try {
         const response = await listAudioFiles()
    if (response.success) {
      audioFiles.value = response.data
    } else {
      message.error('获取音频文件列表失败')
    }
  } catch (error) {
    console.error('获取音频文件失败:', error)
    message.error('获取音频文件失败')
  } finally {
    loadingAudioFiles.value = false
  }
}

// 搜索处理
function handleSearch(keyword) {
  searchKeyword.value = keyword
}

// 文件上传
async function handleBeforeUpload(file, category) {
  try {
    const response = await uploadAudioFile(file, category)
    if (response.success) {
      message.success('文件上传成功')
      refreshAudioFiles()
    } else {
      message.error('文件上传失败')
    }
  } catch (error) {
    console.error('文件上传失败:', error)
    message.error('文件上传失败')
  }
  return false
}

// 文件选择
function selectAudioFile(file) {
  console.log('选择音频文件:', file)
}

// 文件播放
function playAudioFile(file) {
  if (isPlayingFile(file.file_id)) {
    stopAudioPlayback()
  } else {
    playFileAudio(file)
  }
}

function isPlayingFile(fileId) {
  return playingFileId.value === fileId
}

async function playFileAudio(file) {
  try {
    stopAudioPlayback()
    
    playingFileId.value = file.file_id
    
    // 创建音频元素
    currentAudio = new Audio()
    currentAudioId = Date.now().toString()
    currentAudio.audioId = currentAudioId
    
    // 设置音频源
    const fileUrl = `/api/v1/audio-files/${file.file_id}/file`
    currentAudio.src = fileUrl
    currentAudio.crossOrigin = 'anonymous'
    
    // 事件监听器
    const checkAudioId = (e) => e.target.audioId === currentAudioId
    
    currentAudio.addEventListener('ended', (e) => {
      if (!checkAudioId(e)) return
      stopAudioPlayback()
    })
    
    currentAudio.addEventListener('error', (e) => {
      if (!checkAudioId(e)) return
      console.error('音频播放错误:', e)
      stopAudioPlayback()
      message.error('音频播放失败')
    })
    
    await currentAudio.play()
  } catch (error) {
    console.error('播放音频失败:', error)
    stopAudioPlayback()
    message.error('播放音频失败')
  }
}

function stopAudioPlayback() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio.src = ''
    currentAudio = null
  }
  currentAudioId = null
  playingFileId.value = null
}

// 文件删除
async function handleDeleteAudioFile(file) {
  try {
    const response = await deleteAudioFile(file.file_id)
    if (response.success) {
      message.success('文件删除成功')
      refreshAudioFiles()
    } else {
      message.error('文件删除失败')
    }
  } catch (error) {
    console.error('文件删除失败:', error)
    message.error('文件删除失败')
  }
}

// 添加到项目
function handleAddAudioToProject(file) {
  console.log('添加音频到项目:', file)
  // TODO: 实现添加到项目的逻辑
}

// 拖拽处理
function handleDragStart(file, event) {
  draggedAudioFile.value = file
  isDragging.value = true
  
  // 设置拖拽数据
  event.dataTransfer.setData('application/json', JSON.stringify({
    type: 'audio-file',
    file: file
  }))
  
  // 设置拖拽效果
  event.dataTransfer.effectAllowed = 'copy'
  
  // 添加拖拽样式
  event.target.classList.add('dragging')
  
  console.log('开始拖拽音频文件:', file.original_name || file.filename)
}

function handleDragEnd(event) {
  isDragging.value = false
  draggedAudioFile.value = null
  
  // 移除拖拽样式
  event.target.classList.remove('dragging')
  
  console.log('拖拽结束')
}

// 预览播放控制
async function togglePlay() {
  if (isPlaying.value) {
    await pausePreview()
  } else {
    await playPreview()
  }
}

async function playPreview() {
  if (!currentProject.project.id) return
  
  try {
    isLoadingPreview.value = true
    
         const response = await generatePreviewAudio(currentProject.project.id, currentTime.value, 60)
    if (response.success) {
      // 播放预览文件
      await playPreviewAudio(response.data.preview_file)
    } else {
      message.error('生成预览失败')
    }
  } catch (error) {
    console.error('播放预览失败:', error)
    message.error('播放预览失败')
  } finally {
    isLoadingPreview.value = false
  }
}

async function playPreviewAudio(previewFile) {
  try {
    stopPreviewAudio()
    
    currentAudio = new Audio()
    currentAudioId = Date.now().toString()
    currentAudio.audioId = currentAudioId
    
    currentAudio.src = `/api/v1/preview/${previewFile}`
    
    const checkAudioId = (e) => e.target.audioId === currentAudioId
    
    currentAudio.addEventListener('canplay', (e) => {
      if (!checkAudioId(e)) return
      isLoadingPreview.value = false
    })
    
    currentAudio.addEventListener('timeupdate', (e) => {
      if (!checkAudioId(e)) return
      currentTime.value = e.target.currentTime
    })
    
    currentAudio.addEventListener('ended', (e) => {
      if (!checkAudioId(e)) return
      stopPlayback()
    })
    
    currentAudio.addEventListener('error', (e) => {
      if (!checkAudioId(e)) return
      console.error('预览播放错误:', e)
      stopPlayback()
      message.error('预览播放失败')
    })
    
    await currentAudio.play()
    isPlaying.value = true
  } catch (error) {
    console.error('播放预览音频失败:', error)
    isLoadingPreview.value = false
    message.error('播放预览失败')
  }
}

async function pausePreview() {
  if (currentAudio) {
    currentAudio.pause()
    isPlaying.value = false
  }
}

async function stopPlayback() {
  stopPreviewAudio()
  currentTime.value = 0
  
  // 删除预览文件
  if (currentAudio?.src) {
    const previewFile = currentAudio.src.split('/').pop()
    if (previewFile.startsWith('preview_')) {
      try {
        await deletePreviewFile(previewFile)
      } catch (error) {
        console.error('删除预览文件失败:', error)
      }
    }
  }
}

function stopPreviewAudio() {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio.src = ''
    currentAudio = null
  }
  currentAudioId = null
  isPlaying.value = false
  isLoadingPreview.value = false
}

// 项目管理
function handleUpdateProject(updates) {
  Object.assign(currentProject.project, updates)
}

function updateProjectTitle(newTitle) {
  currentProject.project.title = newTitle
}

function updateProjectDescription(newDescription) {
  currentProject.project.description = newDescription
}





// 片段管理  
function updateSelectedClip(updates) {
  const clip = selectedClip.value
  if (!clip) return
  
  // 在所有音轨中找到对应的片段并更新
  for (const track of currentProject.tracks) {
    const targetClip = track.clips.find(c => c.id === clip.id)
    if (targetClip) {
      Object.assign(targetClip, updates)
      updateProjectDuration()
      autoSaveProject()
      break
    }
  }
}



function getTrackTypeLabel(type) {
  const labels = {
    dialogue: '角色对话',
    environment: '环境音效',
    background: '背景音乐'
  }
  return labels[type] || type
}

// 时间轴控制
function handleZoomChange(newZoom) {
  zoomLevel.value = newZoom
}

function handleTimelineScroll(scrollLeft) {
  // 同步时间轴滚动
}

// 音轨和片段管理
function updateTrack(trackId, updates) {
  const track = currentProject.tracks.find(t => t.id === trackId)
  if (track) {
    Object.assign(track, updates)
    updateProjectDuration()
  }
}

function updateClip(trackId, clipId, updates) {
  const track = currentProject.tracks.find(t => t.id === trackId)
  if (track) {
    const clip = track.clips.find(c => c.id === clipId)
    if (clip) {
      Object.assign(clip, updates)
      updateProjectDuration()
      autoSaveProject()
    }
  }
}

function deleteClip(trackId, clipId) {
  const track = currentProject.tracks.find(t => t.id === trackId)
  if (track) {
    const index = track.clips.findIndex(c => c.id === clipId)
    if (index !== -1) {
      track.clips.splice(index, 1)
      updateProjectDuration()
      autoSaveProject()
    }
  }
}

function addClip(trackId, clipData) {
  const track = currentProject.tracks.find(t => t.id === trackId)
  if (track) {
    const newClip = {
      id: generateId('clip'),
      name: clipData.name || '新音频片段',
      filePath: clipData.filePath || '',
      startTime: clipData.startTime || 0,
      duration: clipData.duration || 3,
      volume: 1.0,
      fadeIn: 0.1,
      fadeOut: 0.1,
      playbackRate: 1.0,
      loop: false,
      character: null,
      text: null,
      metadata: {}
    }
    track.clips.push(newClip)
    updateProjectDuration()
    autoSaveProject()
  }
}

function updateProjectDuration() {
  currentProject.project.totalDuration = calculateProjectDuration(currentProject)
}

// 自动保存项目到服务器（防抖处理）
let autoSaveTimer = null
function autoSaveProject() {
  const projectId = currentProject.project?.id
  
  // 确保项目ID是有效的字符串
  if (!projectId || typeof projectId !== 'string' || projectId.trim() === '') {
    console.log('跳过自动保存：项目ID无效', projectId)
    return
  }
  
  // 清除之前的定时器
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer)
  }

  // 设置延迟保存，避免频繁请求
  autoSaveTimer = setTimeout(async () => {
    try {
      console.log('正在自动保存项目，ID:', projectId)
      const result = await saveProject(projectId, currentProject)
      if (result.success) {
        console.log('项目已自动保存到服务器:', currentProject.project.title)
      } else {
        console.warn('自动保存失败:', result.message)
      }
    } catch (error) {
      console.warn('自动保存项目失败:', error)
      // 如果是422错误，说明项目可能还没有创建，或者ID有问题
      if (error.response?.status === 422) {
        console.log('项目可能需要先保存到服务器才能自动保存')
      }
    }
  }, 1000) // 1秒延迟
}

function handleExclusiveSelect(trackId, clipId) {
  // 清除所有音频片段的选中状态
  currentProject.tracks.forEach(track => {
    track.clips.forEach(clip => {
      clip.selected = false
    })
  })
  
  // 选中指定的音频片段
  const track = currentProject.tracks.find(t => t.id === trackId)
  if (track) {
    const clip = track.clips.find(c => c.id === clipId)
    if (clip) {
      clip.selected = true
    }
  }
}

function clearSelectedClip() {
  currentProject.tracks.forEach(track => {
    track.clips.forEach(clip => {
      clip.selected = false
    })
  })
}

// 对话框事件处理
async function handleProjectCreated(projectData) {
  try {
    const newProject = createEmptyProject(projectData.title)
    newProject.project.description = projectData.description
    newProject.project.author = projectData.author

    const result = await createProject(newProject)
    if (result.success) {
      Object.assign(currentProject, result.data)
      message.success('项目创建成功')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败')
  }
}

async function handleProjectSelected(projectId) {
  try {
    const result = await loadProject(projectId)
    if (result.success) {
      Object.assign(currentProject, result.data)
      message.success('项目加载成功')
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  }
}

async function handleImportSuccess(importData) {
  try {
    // 格式化转换请求数据
    const conversionData = formatConversionData(importData)
    
    const result = await convertToStandardFormat(conversionData)
    if (result.success) {
      Object.assign(currentProject, result.data)
      message.success('JSON导入成功')
    }
  } catch (error) {
    console.error('JSON导入失败:', error)
    message.error('JSON导入失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 手动保存项目
async function saveCurrentProject() {
  const projectId = currentProject.project?.id
  
  if (!projectId || typeof projectId !== 'string' || projectId.trim() === '') {
    message.error('无效的项目，请先创建项目')
    return
  }

  try {
    // 更新总时长
    currentProject.project.totalDuration = calculateProjectDuration(currentProject)
    
    const result = await saveProject(projectId, currentProject)
    if (result.success) {
      message.success('项目保存成功')
    } else {
      message.error('项目保存失败: ' + (result.message || '未知错误'))
    }
  } catch (error) {
    console.error('保存项目失败:', error)
    if (error.response?.status === 422) {
      message.error('项目数据格式错误，请检查项目配置')
    } else {
      message.error('保存项目失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

// 导出项目
async function exportCurrentProject() {
  const projectId = currentProject.project?.id
  
  if (!projectId || typeof projectId !== 'string' || projectId.trim() === '') {
    message.error('无效的项目，请先创建并保存项目')
    return
  }

  try {
    exportLoading.value = true
    
    const result = await exportProject(projectId)
    if (result.success) {
      message.success('项目导出完成，请查看下载文件')
      // 这里可以触发下载或显示下载链接
      if (result.downloadUrl) {
        window.open(result.downloadUrl, '_blank')
      }
    } else {
      message.error('项目导出失败: ' + (result.message || '未知错误'))
    }
  } catch (error) {
    console.error('导出项目失败:', error)
    message.error('导出项目失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    exportLoading.value = false
  }
}

// 更新项目信息
function updateProjectInfo(updates) {
  Object.assign(currentProject.project, updates)
  // 触发自动保存
  autoSaveProject()
}

// 格式化转换数据
function formatConversionData(importData) {
  const conversionRequest = {
    dialogueData: {},
    environmentData: null,
    backgroundMusic: null,
    projectInfo: null
  }
  
  if (importData.type === 'dialogue' && importData.data) {
    conversionRequest.dialogueData = importData.data
    conversionRequest.projectInfo = {
      title: importData.data.title || '导入的项目',
      description: importData.data.description || '',
      author: 'AI-Sound'
    }
  }
  
  return conversionRequest
}

// 格式化工具函数
function formatDuration(seconds) {
  return formatTime(seconds)
}

// 键盘事件处理
function handleKeyDown(event) {
  if (event.code === 'Space' && !event.target.matches('input, textarea')) {
    event.preventDefault()
    togglePlay()
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  refreshAudioFiles()
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  stopAudioPlayback()
  stopPreviewAudio()
  document.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.multitrack-editor {
  height: 100vh;
  background: #1a1a1a;
  color: #fff;
  overflow: hidden;
}

.editor-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.top-section {
  display: flex;
  gap: 12px;
  padding: 12px;
  height: 300px;
  min-height: 300px;
  background: #222;
}

.bottom-section {
  flex: 1;
  padding: 0 12px 12px;
  overflow: hidden;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #1e1e1e;
  border-radius: 8px;
  border: 1px solid #333;
}

.empty-state :deep(.ant-empty) {
  color: #999;
}
</style>