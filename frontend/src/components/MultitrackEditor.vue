<template>
  <div class="multitrack-editor">
    <!-- 主编辑区域 -->
    <div class="editor-container">
      <!-- 上半部分：资源库 + 预览 + 项目信息 -->
      <div class="top-section">
        <!-- 左侧：资源库 -->
        <div class="resource-panel">
          <div class="panel-header">
            <h4>资源库</h4>
            <a-space size="small">
              <a-button size="small" @click="refreshAudioFiles">
                <template #icon><SoundOutlined /></template>
                刷新
              </a-button>
              <a-button size="small" @click="showImportDialog = true">
                <template #icon><ImportOutlined /></template>
                导入
              </a-button>
            </a-space>
          </div>
          <div class="panel-content">
            <div class="resource-tabs">
              <a-tabs default-active-key="audio" size="small">
                <a-tab-pane key="audio" tab="音频文件">
                  <div class="audio-list">
                    <!-- 上传按钮 -->
                    <div class="upload-section">
                      <a-upload
                        :multiple="true"
                        :show-upload-list="false"
                        :before-upload="handleBeforeUpload"
                        accept="audio/*"
                      >
                        <a-button type="primary" size="small" block>
                          <template #icon><UploadOutlined /></template>
                          上传音频
                        </a-button>
                      </a-upload>
                    </div>
                    
                    <!-- 搜索框 -->
                    <div class="search-section">
                      <a-input-search
                        v-model:value="searchKeyword"
                        placeholder="搜索音频..."
                        size="small"
                        @search="handleSearch"
                      />
                    </div>
                    
                    <!-- 音频文件列表 -->
                    <div class="audio-files">
                      <a-spin :spinning="loadingAudioFiles">
                        <div v-if="filteredAudioFiles.length === 0" class="empty-audio">
                          <div class="empty-icon">🎵</div>
                          <div class="empty-text">暂无音频文件</div>
                          <div class="empty-desc">点击上传按钮添加音频文件</div>
                        </div>
                        <div v-else>
                                                     <div 
                             class="audio-item" 
                             v-for="file in filteredAudioFiles" 
                             :key="file.file_id"
                             :draggable="true"
                             @click="selectAudioFile(file)"
                             @dblclick="handleAddAudioToProject(file)"
                             @dragstart="handleDragStart(file, $event)"
                             @dragend="handleDragEnd"
                           >
                            <div class="audio-preview">
                              <!-- 播放按钮 -->
                              <a-button 
                                size="small" 
                                type="text" 
                                @click.stop="playAudioFile(file)"
                                :icon="isPlayingFile(file.file_id) ? h(PauseCircleOutlined) : h(PlayCircleOutlined)"
                              />
                            </div>
                            <div class="audio-info">
                              <div class="audio-name" :title="file.original_name || file.filename">
                                {{ file.original_name || file.filename || '未知文件' }}
                              </div>
                              <div class="audio-meta">
                                <span class="audio-duration">{{ formatDuration(file.duration || 0) }}</span>
                                <span v-if="file.format" class="audio-format">{{ file.format.toUpperCase() }}</span>
                                <span v-else class="audio-format">WAV</span>
                              </div>
                              <div class="audio-hint">
                                双击添加 | 拖拽到音轨
                              </div>
                            </div>
                            <div class="audio-actions">
                              <a-popconfirm
                                title="确定要删除这个音频文件吗？"
                                ok-text="删除"
                                cancel-text="取消"
                                @confirm="handleDeleteAudioFile(file)"
                              >
                                <a-button 
                                  size="small" 
                                  type="text"
                                  danger
                                  @click.stop
                                  :icon="h(DeleteOutlined)"
                                  title="删除文件"
                                />
                              </a-popconfirm>
                            </div>
                          </div>
                        </div>
                      </a-spin>
                    </div>
                  </div>
                </a-tab-pane>
                <a-tab-pane key="effects" tab="音效">
                  <div class="effects-list">
                    <div class="effect-item" v-for="n in 3" :key="n">
                      <div class="effect-icon">🎛️</div>
                      <div class="effect-name">效果 {{ n }}</div>
                    </div>
                  </div>
                </a-tab-pane>
              </a-tabs>
            </div>
          </div>
        </div>

        <!-- 中间：合成效果预览 -->
        <div class="preview-panel">
          <div class="panel-header">
            <h4>合成预览</h4>
          </div>
          <div class="panel-content">
            <div class="preview-area">
              <div class="waveform-display">
                <!-- 波形预览区域 -->
                <div class="waveform-container">
                  <div class="waveform-placeholder">
                    <div class="waveform-icon">📊</div>
                    <div class="waveform-text">音频波形预览</div>
                    <div class="waveform-info">
                      {{ formatTime(currentTime) }} / {{ formatTime(currentProject.project.totalDuration || 0) }}
                    </div>
                  </div>
                </div>
              </div>
              <div class="preview-controls">
                <a-slider 
                  v-model:value="currentTime" 
                  :max="currentProject.project.totalDuration || 1" 
                  :step="0.1"
                  :disabled="!currentProject.project.id"
                  style="flex: 1; margin-right: 12px;"
                />
                <a-space size="small">
                  <a-button size="small" type="primary" @click="togglePlay" :loading="isLoadingPreview" :disabled="!currentProject.project.id">
                    <template #icon>
                      <PlayCircleOutlined v-if="!isPlaying && !isLoadingPreview" />
                      <PauseCircleOutlined v-else-if="isPlaying" />
                    </template>
                    {{ isLoadingPreview ? '准备中' : (isPlaying ? '播放' : '预览') }}
                  </a-button>
                  <a-button size="small" @click="stopPlayback">
                    <template #icon><StopOutlined /></template>
                    停止
                  </a-button>
                </a-space>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：项目信息/音频片段信息 -->
        <div class="project-panel">
          <div class="panel-header">
            <h4>{{ selectedClip ? '音频片段信息' : '项目信息' }}</h4>
            <a-space size="small" v-if="!selectedClip">
              <a-button size="small" @click="showCreateProject = true" type="primary">
                <template #icon><PlusOutlined /></template>
                新建
              </a-button>
              <a-button size="small" @click="showProjectList = true">
                <template #icon><FolderOpenOutlined /></template>
                打开
              </a-button>
              <a-button size="small" @click="saveCurrentProject" :disabled="!currentProject.project.id">
                <template #icon><SaveOutlined /></template>
                保存
              </a-button>
            </a-space>
          </div>
          <div class="panel-content">
            <!-- 音频片段信息 -->
            <div v-if="selectedClip" class="clip-details">
              <div class="project-field">
                <label>片段名称：</label>
                <EditableText 
                  :value="selectedClip.name" 
                  @change="(newName) => updateSelectedClip({ name: newName })"
                  placeholder="音频片段名称"
                />
              </div>
              <div class="project-field">
                <label>音轨类型：</label>
                <span>{{ getTrackTypeLabel(selectedClip.trackType) }}</span>
              </div>
              <div class="project-field">
                <label>开始时间：</label>
                <span>{{ formatTime(selectedClip.startTime) }}</span>
              </div>
              <div class="project-field">
                <label>持续时间：</label>
                <span>{{ formatTime(selectedClip.duration) }}</span>
              </div>
              <div class="project-field">
                <label>音量：</label>
                <a-slider 
                  :value="selectedClip.volume * 100" 
                  :min="0" 
                  :max="200" 
                  :step="1"
                  @change="(value) => updateSelectedClip({ volume: value / 100 })"
                />
                <span>{{ Math.round(selectedClip.volume * 100) }}%</span>
              </div>
              <div class="project-field">
                <label>淡入时间：</label>
                <a-input-number 
                  :value="selectedClip.fadeIn || 0" 
                  :min="0" 
                  :max="selectedClip.duration / 2"
                  :step="0.1"
                  @change="(value) => updateSelectedClip({ fadeIn: value })"
                  addon-after="秒"
                />
              </div>
              <div class="project-field">
                <label>淡出时间：</label>
                <a-input-number 
                  :value="selectedClip.fadeOut || 0" 
                  :min="0" 
                  :max="selectedClip.duration / 2"
                  :step="0.1"
                  @change="(value) => updateSelectedClip({ fadeOut: value })"
                  addon-after="秒"
                />
              </div>
              <div class="project-actions">
                <a-button block @click="clearSelectedClip">
                  取消选择
                </a-button>
              </div>
            </div>
            
            <!-- 项目信息 -->
            <div v-else-if="currentProject.project.id" class="project-details">
              <div class="project-field">
                <label>项目名称：</label>
                <EditableText 
                  :value="currentProject.project.title" 
                  @change="updateProjectTitle"
                  placeholder="项目标题"
                />
              </div>
              <div class="project-field">
                <label>项目描述：</label>
                <EditableText 
                  :value="currentProject.project.description" 
                  @change="updateProjectDescription"
                  placeholder="项目描述"
                />
              </div>
              <div class="project-field">
                <label>作者：</label>
                <span>{{ currentProject.project.author }}</span>
              </div>
              <div class="project-field">
                <label>总时长：</label>
                <span>{{ formatTime(currentProject.project.totalDuration) }}</span>
              </div>
              <div class="project-field">
                <label>采样率：</label>
                <span>{{ currentProject.project.sampleRate }} Hz</span>
              </div>
              <div class="project-field">
                <label>声道数：</label>
                <span>{{ currentProject.project.channels }}</span>
              </div>
              <div class="project-actions">
                <a-button block @click="exportAudio" :disabled="!currentProject.project.id" :loading="exportLoading">
                  <template #icon><ExportOutlined /></template>
                  导出音频
                </a-button>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-else class="project-empty">
              <div class="empty-icon">📁</div>
              <div class="empty-text">暂无项目</div>
              <div class="empty-desc">请创建或打开一个项目</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 下半部分：音轨编辑器 -->
      <div class="bottom-section">
        <div v-if="currentProject.project.id" class="timeline-container">
          <!-- 时间标尺 -->
          <div class="timeline-ruler">
            <!-- 左侧占位区域 -->
            <div class="ruler-left-space"></div>
            <!-- 时间标记区域 -->
            <div class="time-markers">
              <div
                v-for="marker in timeMarkers"
                :key="marker.time"
                class="time-marker"
                :style="{ left: `${(marker.time / viewDuration) * 100}%` }"
              >
                <span class="time-label">{{ formatTime(marker.time) }}</span>
              </div>
            </div>
            <!-- 播放头 -->
            <div 
              class="playhead" 
              :style="{ left: `calc(200px + ${(currentTime / viewDuration) * 100}% - 200px * ${currentTime / viewDuration})` }"
            ></div>
          </div>

          <!-- 音轨列表 -->
          <div class="tracks-container">
            <TrackEditor
              v-for="track in currentProject.tracks"
              :key="track.id"
              :track="track"
              :viewDuration="viewDuration"
              :pixelsPerSecond="pixelsPerSecond"
              :currentTime="currentTime"
              @update-track="updateTrack"
              @update-clip="updateClip"
              @delete-clip="deleteClip"
              @add-clip="addClip"
              @select-exclusive="handleExclusiveSelect"
            />
          </div>
        </div>

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <a-empty description="请创建或打开一个项目开始编辑">
            <a-button type="primary" @click="showCreateProject = true">创建新项目</a-button>
          </a-empty>
        </div>
      </div>
    </div>

    <!-- 创建项目对话框 -->
    <a-modal
      v-model:open="showCreateProject"
      title="创建新项目"
      @ok="createNewProject"
      @cancel="resetCreateForm"
    >
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="项目标题" required>
          <a-input v-model:value="createForm.title" placeholder="输入项目标题" />
        </a-form-item>
        <a-form-item label="项目描述">
          <a-textarea v-model:value="createForm.description" placeholder="项目描述（可选）" :rows="3" />
        </a-form-item>
        <a-form-item label="作者">
          <a-input v-model:value="createForm.author" placeholder="作者名称" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 项目列表对话框 -->
    <a-modal
      v-model:open="showProjectList"
      title="选择项目"
      width="800px"
      :footer="null"
    >
      <ProjectList @select="openProject" @delete="handleDeleteProject" />
    </a-modal>

    <!-- JSON导入对话框 -->
    <a-modal
      v-model:open="showImportDialog"
      title="导入JSON格式"
      width="800px"
      @ok="handleImportJson"
      @cancel="resetImportForm"
    >
      <ImportJsonForm v-model="importForm" />
    </a-modal>

    <!-- 导出进度对话框 -->
    <a-modal
      v-model:open="showExportProgress"
      title="导出进度"
      :footer="exportStatus === 'completed' ? null : undefined"
      :closable="exportStatus !== 'processing'"
      :maskClosable="false"
    >
      <div class="export-progress">
        <a-result
          v-if="exportStatus === 'completed'"
          status="success"
          title="导出完成"
          sub-title="音频文件已成功生成"
        >
          <template #extra>
            <a-button type="primary" @click="downloadExportedFile">下载文件</a-button>
            <a-button @click="showExportProgress = false">关闭</a-button>
          </template>
        </a-result>
        <a-result
          v-else-if="exportStatus === 'failed'"
          status="error"
          title="导出失败"
          :sub-title="exportMessage"
        >
          <template #extra>
            <a-button @click="showExportProgress = false">关闭</a-button>
          </template>
        </a-result>
        <div v-else>
          <a-spin size="large" />
          <p style="margin-top: 16px; text-align: center;">{{ exportMessage || '正在处理音频...' }}</p>
        </div>
      </div>
    </a-modal>


  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, h } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  PlusOutlined,
  FolderOpenOutlined,
  SaveOutlined,
  ImportOutlined,
  ExportOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SoundOutlined,
  UploadOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

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

import {
  uploadMultipleAudioFiles,
  listAudioFiles,
  deleteAudioFile
} from '../api/audioFiles'

import EditableText from './common/EditableText.vue'
import TrackEditor from './tracks/TrackEditor.vue'
import ProjectList from './project/ProjectList.vue'
import ImportJsonForm from './import/ImportJsonForm.vue'


// 响应式数据
const currentProject = ref(createEmptyProject())
const showCreateProject = ref(false)
const showProjectList = ref(false)
const showImportDialog = ref(false)
const showExportProgress = ref(false)


// 播放控制
const isPlaying = ref(false)
const currentTime = ref(0)
const isLoadingPreview = ref(false)
let playInterval = null
let previewAudioElement = null  // 专门用于预览播放
let audioFileElement = null     // 专门用于音频文件播放
let currentPreviewFile = null
let currentAudioId = 0          // 当前音频元素的唯一标识符

// 计算当前选中的音频片段
const selectedClip = computed(() => {
  for (const track of currentProject.value.tracks) {
    for (const clip of track.clips) {
      if (clip.selected) {
        return { ...clip, trackType: track.type }
      }
    }
  }
  return null
})

// 视图控制
const viewDuration = ref(60) // 显示的时间范围（秒）
const pixelsPerSecond = computed(() => 800 / viewDuration.value) // 每秒的像素数

// 时间标记
const timeMarkers = computed(() => {
  const markers = []
  const step = viewDuration.value >= 120 ? 10 : viewDuration.value >= 60 ? 5 : 1
  
  for (let time = 0; time <= viewDuration.value; time += step) {
    markers.push({ time })
  }
  return markers
})

// 表单数据
const createForm = reactive({
  title: '',
  description: '',
  author: 'AI-Sound'
})

const importForm = ref({})

// 导出状态
const exportLoading = ref(false)
const exportStatus = ref('')
const exportMessage = ref('')
const currentExportTaskId = ref('')

// 音频文件管理
const audioFiles = ref([])
const loadingAudioFiles = ref(false)
const searchKeyword = ref('')
const selectedAudioFile = ref(null)
const playingFileId = ref(null)

// 拖拽状态
const draggedAudioFile = ref(null)
const isDragging = ref(false)

// 计算属性：过滤后的音频文件
const filteredAudioFiles = computed(() => {
  if (!searchKeyword.value) return audioFiles.value
  
  const keyword = searchKeyword.value.toLowerCase()
  return audioFiles.value.filter(file => 
    (file.original_name || file.filename).toLowerCase().includes(keyword)
  )
})

// 方法定义

// 项目管理
async function createNewProject() {
  if (!createForm.title.trim()) {
    message.error('请输入项目标题')
    return
  }

  try {
    const newProject = createEmptyProject(createForm.title)
    newProject.project.description = createForm.description
    newProject.project.author = createForm.author

    const result = await createProject(newProject)
    if (result.success) {
      currentProject.value = result.data
      showCreateProject.value = false
      resetCreateForm()
      updateViewDuration()
      // 保存到本地存储
      saveCurrentProjectToLocalStorage()
      message.success('项目创建成功')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败')
  }
}

function resetCreateForm() {
  createForm.title = ''
  createForm.description = ''
  createForm.author = 'AI-Sound'
}

async function openProject(projectId) {
  try {
    const result = await loadProject(projectId)
    if (result.success) {
      currentProject.value = result.data
      showProjectList.value = false
      updateViewDuration()
      // 保存到本地存储
      saveCurrentProjectToLocalStorage()
      message.success('项目加载成功')
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  }
}

async function saveCurrentProject() {
  if (!currentProject.value.project.id) return

  try {
    // 更新总时长
    currentProject.value.project.totalDuration = calculateProjectDuration(currentProject.value)
    
    const result = await saveProject(currentProject.value.project.id, currentProject.value)
    if (result.success) {
      message.success('项目保存成功')
    }
  } catch (error) {
    console.error('保存项目失败:', error)
    message.error('保存项目失败')
  }
}

async function handleDeleteProject(projectId) {
  try {
    const result = await deleteProject(projectId)
    if (result.success) {
      message.success('项目删除成功')
      // 如果删除的是当前项目，重置编辑器
      if (currentProject.value.project.id === projectId) {
        currentProject.value = createEmptyProject()
        // 清除本地缓存
        clearProjectCache()
      }
    }
  } catch (error) {
    console.error('删除项目失败:', error)
    message.error('删除项目失败')
  }
}

// 项目信息编辑
function updateProjectTitle(newTitle) {
  currentProject.value.project.title = newTitle
}

function updateProjectDescription(newDescription) {
  currentProject.value.project.description = newDescription
}

// 音轨编辑
function updateTrack(trackId, updates) {
  const track = currentProject.value.tracks.find(t => t.id === trackId)
  if (track) {
    Object.assign(track, updates)
    updateProjectDuration()
  }
}

function updateClip(trackId, clipId, updates) {
  const track = currentProject.value.tracks.find(t => t.id === trackId)
  if (track) {
    const clip = track.clips.find(c => c.id === clipId)
    if (clip) {
      Object.assign(clip, updates)
      updateProjectDuration()
    }
  }
}

function deleteClip(trackId, clipId) {
  const track = currentProject.value.tracks.find(t => t.id === trackId)
  if (track) {
    const index = track.clips.findIndex(c => c.id === clipId)
    if (index !== -1) {
      track.clips.splice(index, 1)
      updateProjectDuration()
    }
  }
}

function addClip(trackId, clipData) {
  const track = currentProject.value.tracks.find(t => t.id === trackId)
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
  }
}

function updateProjectDuration() {
  currentProject.value.project.totalDuration = calculateProjectDuration(currentProject.value)
}

function updateViewDuration() {
  const projectDuration = currentProject.value.project.totalDuration
  if (projectDuration > 0) {
    viewDuration.value = Math.max(60, Math.ceil(projectDuration / 10) * 10)
  }
}

// JSON导入
async function handleImportJson() {
  try {
    // 格式化转换请求数据
    const conversionData = formatConversionData(importForm.value)
    
    const result = await convertToStandardFormat(conversionData)
    if (result.success) {
      currentProject.value = result.data
      showImportDialog.value = false
      updateViewDuration()
      // 保存到本地存储
      saveCurrentProjectToLocalStorage()
      message.success('JSON导入成功')
    }
  } catch (error) {
    console.error('JSON导入失败:', error)
    message.error('JSON导入失败: ' + (error.response?.data?.detail || error.message))
  }
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

function resetImportForm() {
  importForm.value = {}
}

// 项目验证
async function validateCurrentProject() {
  if (!currentProject.value.project.id) return

  try {
    const result = await validateProject(currentProject.value.project.id)
    
    if (result.valid) {
      message.success('项目验证通过')
    } else {
      const errorMsg = result.errors.join(', ')
      const warningMsg = result.warnings.join(', ')
      message.error(`验证失败: ${errorMsg}${warningMsg ? ` 警告: ${warningMsg}` : ''}`)
    }
  } catch (error) {
    console.error('项目验证失败:', error)
    message.error('项目验证失败')
  }
}

// 音频导出
async function exportAudio() {
  if (!currentProject.value.project.id) return

  try {
    exportLoading.value = true
    const result = await exportProject(currentProject.value.project.id)
    
    if (result.success) {
      currentExportTaskId.value = result.export_task_id
      exportStatus.value = 'processing'
      exportMessage.value = result.message
      showExportProgress.value = true
      
      // 开始轮询导出状态
      startExportPolling()
    }
  } catch (error) {
    console.error('导出失败:', error)
    message.error('导出失败')
  } finally {
    exportLoading.value = false
  }
}

function startExportPolling() {
  const pollInterval = setInterval(async () => {
    try {
      const status = await getExportStatus(currentExportTaskId.value)
      exportStatus.value = status.status
      exportMessage.value = status.message
      
      if (status.status === 'completed' || status.status === 'failed') {
        clearInterval(pollInterval)
      }
    } catch (error) {
      console.error('查询导出状态失败:', error)
      clearInterval(pollInterval)
    }
  }, 2000)
}

async function downloadExportedFile() {
  try {
    await downloadExportedAudio(currentExportTaskId.value)
    message.success('文件下载已开始')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

// 播放控制
async function togglePlay() {
  // 如果正在加载，不处理
  if (isLoadingPreview.value) {
    console.log('正在加载预览，忽略播放切换')
    return
  }
  
  if (isPlaying.value) {
    pausePlayback()
  } else {
    // 如果有可用的音频元素且未结束，恢复播放；否则重新开始
    if (previewAudioElement && !previewAudioElement.ended && previewAudioElement.src) {
      resumePlayback()
    } else {
      await startPlayback()
    }
  }
}

async function startPlayback() {
  try {
    // 如果已在加载中，避免重复请求
    if (isLoadingPreview.value) {
      console.log('预览音频正在加载中，跳过重复请求')
      return
    }
    
    isLoadingPreview.value = true
    
    // 检查是否有项目
    if (!currentProject.value.project.id) {
      message.warning('请先创建或加载项目')
      isLoadingPreview.value = false
      return
    }
    
    // 计算预览时长
    const totalDuration = currentProject.value.project.totalDuration || 60  // 默认60秒
    const remainingDuration = totalDuration - currentTime.value
    const previewDuration = Math.min(10.0, Math.max(1.0, remainingDuration))  // 至少1秒，最多10秒
    
    console.log('预览播放参数:', {
      projectId: currentProject.value.project.id,
      currentTime: currentTime.value,
      totalDuration,
      previewDuration
    })
    
    // 生成预览音频
    const previewResult = await generatePreviewAudio(
      currentProject.value.project.id,
      currentTime.value,
      previewDuration
    )
    
    if (!previewResult.success) {
      message.error('生成预览音频失败: ' + (previewResult.message || '未知错误'))
      isLoadingPreview.value = false
      return
    }
    
    console.log('预览音频生成成功:', previewResult)
    
    // 停止当前播放并清理旧的音频元素
    if (previewAudioElement) {
      previewAudioElement.pause()
      previewAudioElement.src = ''
      previewAudioElement = null
    }
    
    // 创建新的音频元素
    currentAudioId++  // 增加音频ID
    const audioId = currentAudioId
    currentPreviewFile = previewResult.data.preview_file
    const audioUrl = getPreviewAudioUrl(currentPreviewFile)
    
    console.log('创建预览音频元素:', {
      audioId: audioId,
      previewFile: currentPreviewFile,
      audioUrl: audioUrl
    })
    
    previewAudioElement = new Audio()
    previewAudioElement.audioId = audioId  // 为音频元素分配ID
    previewAudioElement.crossOrigin = 'anonymous'
    previewAudioElement.preload = 'auto'
    
    // 设置音频事件监听
    previewAudioElement.addEventListener('loadstart', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      console.log('预览音频开始加载')
    })
    
    previewAudioElement.addEventListener('loadeddata', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      console.log('预览音频数据加载完成')
    })
    
    previewAudioElement.addEventListener('loadedmetadata', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      console.log('预览音频元数据加载完成')
    })
    
    previewAudioElement.addEventListener('suspend', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      console.log('预览音频加载暂停')
    })
    
    previewAudioElement.addEventListener('stalled', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      console.log('预览音频加载停滞')
      // 如果加载停滞，重置状态
      if (isLoadingPreview.value) {
        isLoadingPreview.value = false
        message.warning('音频加载停滞，请重试')
      }
    })
    
    previewAudioElement.addEventListener('canplay', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      if (!previewAudioElement) return
      console.log('预览音频可以播放')
      
      // 重置加载状态
      isLoadingPreview.value = false
      isPlaying.value = true
      
      // 尝试播放音频
      const playPromise = previewAudioElement.play()
      
      if (playPromise !== undefined) {
        playPromise.then(() => {
          console.log('预览音频播放成功')
          // 开始更新播放时间
          playInterval = setInterval(() => {
            if (previewAudioElement && !previewAudioElement.paused) {
              currentTime.value = Math.min(
                currentTime.value + 0.1,
                currentProject.value.project.totalDuration || 60
              )
            }
          }, 100)
        }).catch(error => {
          console.error('预览音频播放失败:', error)
          
          if (error.name === 'NotAllowedError') {
            message.warning('浏览器需要用户交互才能播放音频，请再次点击预览按钮')
          } else {
            message.error('音频播放失败: ' + error.message)
          }
          
          // 播放失败时重置状态
          isLoadingPreview.value = false
          isPlaying.value = false
        })
      }
    })
    
    previewAudioElement.addEventListener('ended', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      if (!previewAudioElement) return
      console.log('预览音频播放结束')
      stopPlayback()
    })
    
    previewAudioElement.addEventListener('error', (e) => {
      if (e.target.audioId !== currentAudioId) return  // 只处理当前音频元素的事件
      if (!previewAudioElement) return
      const error = e.target.error
      console.error('预览音频播放错误:', e, error)
      
      let errorMessage = '音频播放失败'
      if (error) {
        switch (error.code) {
          case 1: // MEDIA_ERR_ABORTED
            errorMessage = '音频播放被中止'
            break
          case 2: // MEDIA_ERR_NETWORK
            errorMessage = '网络错误导致音频播放失败'
            break
          case 3: // MEDIA_ERR_DECODE
            errorMessage = '音频解码失败'
            break
          case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
            errorMessage = '音频格式不支持或文件损坏'
            break
          default:
            errorMessage = '音频播放失败: ' + (error.message || '未知错误')
        }
      }
      
      message.error(errorMessage)
      isLoadingPreview.value = false
      isPlaying.value = false
      
      // 清理音频元素但不删除文件（可能还需要重试）
      if (previewAudioElement) {
        previewAudioElement.src = ''
        previewAudioElement.load()
        previewAudioElement = null
      }
    })
    
    // 设置音频源并开始加载
    previewAudioElement.src = audioUrl
    previewAudioElement.load()
    
    // 设置超时保护，如果10秒内没有触发canplay事件，则重置状态
    setTimeout(() => {
      if (isLoadingPreview.value) {
        console.warn('音频加载超时，重置加载状态')
        isLoadingPreview.value = false
        message.warning('音频加载超时，请重试')
      }
    }, 10000)
    
  } catch (error) {
    console.error('启动播放失败:', error)
    message.error('启动播放失败')
    isLoadingPreview.value = false
  }
}

function pausePlayback() {
  isPlaying.value = false
  if (previewAudioElement) {
    previewAudioElement.pause()
  }
  if (playInterval) {
    clearInterval(playInterval)
    playInterval = null
  }
}

function resumePlayback() {
  if (!previewAudioElement) return
  
  console.log('恢复播放预览音频')
  isPlaying.value = true
  
  const playPromise = previewAudioElement.play()
  
  if (playPromise !== undefined) {
    playPromise.then(() => {
      console.log('预览音频恢复播放成功')
      // 开始更新播放时间
      playInterval = setInterval(() => {
        if (previewAudioElement && !previewAudioElement.paused) {
          currentTime.value = Math.min(
            currentTime.value + 0.1,
            currentProject.value.project.totalDuration || 60
          )
        }
      }, 100)
    }).catch(error => {
      console.error('预览音频恢复播放失败:', error)
      isPlaying.value = false
      
      if (error.name === 'NotAllowedError') {
        message.warning('浏览器需要用户交互才能播放音频，请再次点击预览按钮')
      } else {
        message.error('音频播放失败: ' + error.message)
      }
    })
  }
}

async function stopPlayback() {
  isPlaying.value = false
  currentTime.value = 0
  
  if (previewAudioElement) {
    previewAudioElement.pause()
    previewAudioElement.currentTime = 0
    previewAudioElement.src = ''
    previewAudioElement.load()
    previewAudioElement = null
  }
  
  if (playInterval) {
    clearInterval(playInterval)
    playInterval = null
  }
  
  // 删除临时预览文件
  if (currentPreviewFile) {
    try {
      // 添加preview_前缀，因为后端生成的文件名是preview_{uuid}.wav
      const previewFileName = `preview_${currentPreviewFile}.wav`
      const result = await deletePreviewFile(previewFileName)
      if (result.success) {
        console.log('预览文件已删除:', previewFileName)
      } else {
        console.warn('删除预览文件失败:', result.error)
      }
    } catch (error) {
      console.error('删除预览文件出错:', error)
    }
  }
  
  currentPreviewFile = null
}

// 项目持久化
function saveCurrentProjectToLocalStorage() {
  if (currentProject.value.project.id) {
    localStorage.setItem('sound-edit-current-project-id', currentProject.value.project.id)
    localStorage.setItem('sound-edit-current-project-data', JSON.stringify(currentProject.value))
    console.log('项目已自动保存到本地缓存:', currentProject.value.project.title)
  }
}

function clearProjectCache() {
  localStorage.removeItem('sound-edit-current-project-id')
  localStorage.removeItem('sound-edit-current-project-data')
  message.info('本地项目缓存已清除')
}

async function loadProjectFromLocalStorage() {
  try {
    const savedProjectId = localStorage.getItem('sound-edit-current-project-id')
    const savedProjectData = localStorage.getItem('sound-edit-current-project-data')
    
    if (savedProjectId && savedProjectData) {
      // 尝试从服务器加载最新的项目数据
      try {
        const serverProject = await loadProject(savedProjectId)
        if (serverProject.success) {
          currentProject.value = serverProject.data
          message.success('已恢复项目: ' + currentProject.value.project.title)
          return
        }
      } catch (error) {
        console.warn('从服务器加载项目失败，使用本地缓存:', error)
      }
      
      // 如果服务器加载失败，使用本地缓存
      const localProject = JSON.parse(savedProjectData)
      currentProject.value = localProject
      message.info('已恢复本地项目: ' + currentProject.value.project.title)
    }
  } catch (error) {
    console.error('恢复项目失败:', error)
  }
}

// 监听项目变化，自动保存到本地存储
watch(currentProject, (newProject) => {
  if (newProject.project.id) {
    saveCurrentProjectToLocalStorage()
  }
}, { deep: true })

// 全局键盘事件处理
function handleKeyDown(event) {
  // 检查是否在输入框中
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return
  }
  
  switch (event.key) {
    case ' ':
      // 空格键：播放/暂停
      if (currentProject.value.project.id) {
        togglePlay()
        event.preventDefault()
      }
      break
    case 'Delete':
    case 'Backspace':
      handleDeleteSelectedClips()
      event.preventDefault()
      break
    case 'Escape':
      clearAllSelections()
      event.preventDefault()
      break
  }
}

function handleGlobalClick(event) {
  // 如果点击的不是音频片段相关元素，清除所有选中状态
  if (!event.target.closest('.audio-clip') && !event.target.closest('.ant-modal')) {
    clearAllSelections()
  }
}

function handleDeleteSelectedClips() {
  const selectedClips = []
  
  // 收集所有选中的音频片段
  currentProject.value.tracks.forEach(track => {
    track.clips.forEach(clip => {
      if (clip.selected) {
        selectedClips.push({ trackId: track.id, clipId: clip.id, clipName: clip.name })
      }
    })
  })
  
  if (selectedClips.length === 0) {
    message.info('请先选择要删除的音频片段')
    return
  }
  
  // 显示确认对话框
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除 ${selectedClips.length} 个音频片段吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk() {
      selectedClips.forEach(({ trackId, clipId }) => {
        deleteClip(trackId, clipId)
      })
      message.success(`已删除 ${selectedClips.length} 个音频片段`)
    }
  })
}

function clearAllSelections() {
  currentProject.value.tracks.forEach(track => {
    track.clips.forEach(clip => {
      if (clip.selected) {
        clip.selected = false
      }
    })
  })
}

function handleExclusiveSelect(trackId, clipId) {
  // 清除所有音频片段的选中状态
  currentProject.value.tracks.forEach(track => {
    track.clips.forEach(clip => {
      clip.selected = false
    })
  })
  
  // 选中指定的音频片段
  const track = currentProject.value.tracks.find(t => t.id === trackId)
  if (track) {
    const clip = track.clips.find(c => c.id === clipId)
    if (clip) {
      clip.selected = true
    }
  }
}

// 更新选中的音频片段
function updateSelectedClip(updates) {
  if (!selectedClip.value) return
  
  // 找到对应的音轨和片段并更新
  for (const track of currentProject.value.tracks) {
    for (const clip of track.clips) {
      if (clip.selected) {
        Object.assign(clip, updates)
        break
      }
    }
  }
}

// 清除选中状态
function clearSelectedClip() {
  currentProject.value.tracks.forEach(track => {
    track.clips.forEach(clip => {
      clip.selected = false
    })
  })
}

// 生命周期
onMounted(async () => {
  // 恢复之前的项目
  await loadProjectFromLocalStorage()
  // 加载音频文件列表
  await loadAudioFiles()
  
  // 添加全局键盘事件监听
  document.addEventListener('keydown', handleKeyDown)
  // 添加全局点击事件监听
  document.addEventListener('click', handleGlobalClick)
})

onUnmounted(() => {
  // 清理播放相关资源
  if (playInterval) {
    clearInterval(playInterval)
  }
  if (previewAudioElement) {
    previewAudioElement.pause()
    previewAudioElement = null
  }
  if (audioFileElement) {
    audioFileElement.pause()
    audioFileElement = null
  }
  
  // 移除全局键盘事件监听
  document.removeEventListener('keydown', handleKeyDown)
  // 移除全局点击事件监听  
  document.removeEventListener('click', handleGlobalClick)
})

// 添加音频文件到项目
function handleAddAudioToProject(audioFile) {
  // 找到合适的音轨
  let targetTrack = null
  
  // 根据文件类型选择默认音轨
  if (audioFile.original_name) {
    const name = audioFile.original_name.toLowerCase()
    if (name.includes('dialogue') || name.includes('voice') || name.includes('speech')) {
      targetTrack = currentProject.value.tracks.find(t => t.type === 'dialogue')
    } else if (name.includes('background') || name.includes('music') || name.includes('bgm')) {
      targetTrack = currentProject.value.tracks.find(t => t.type === 'background')
    } else if (name.includes('environment') || name.includes('effect') || name.includes('ambient')) {
      targetTrack = currentProject.value.tracks.find(t => t.type === 'environment')
    }
  }
  
  // 如果没有找到合适的音轨，使用第一个音轨
  if (!targetTrack && currentProject.value.tracks.length > 0) {
    targetTrack = currentProject.value.tracks[0]
  }
  
  if (targetTrack) {
    const fileName = audioFile.original_name || audioFile.filename || '音频片段'
    const clipData = {
      name: fileName.replace(/\.[^/.]+$/, ''),
      filePath: audioFile.file_id,
      startTime: findNextAvailableTimeInTrack(targetTrack),
      duration: audioFile.duration || 3.0
    }
    
    addClip(targetTrack.id, clipData)
    showAudioManager.value = false
    message.success(`已添加到 ${getTrackTypeLabel(targetTrack.type)} 音轨`)
  } else {
    message.warning('请先创建音轨')
  }
}

function findNextAvailableTimeInTrack(track) {
  if (track.clips.length === 0) {
    return 0
  }
  
  // 找到最后一个片段的结束时间
  const lastClip = track.clips.reduce((latest, clip) => {
    const endTime = clip.startTime + clip.duration
    return endTime > latest ? endTime : latest
  }, 0)
  
  return lastClip + 0.5 // 添加0.5秒间隙
}

function getTrackTypeLabel(type) {
  const labels = {
    dialogue: '角色对话',
    environment: '环境音效',
    background: '背景音乐'
  }
  return labels[type] || type
}

// 音频文件管理方法
async function loadAudioFiles() {
  try {
    loadingAudioFiles.value = true
    const result = await listAudioFiles()
    if (result.success) {
      audioFiles.value = result.data
    }
  } catch (error) {
    console.error('加载音频文件失败:', error)
    message.error('加载音频文件失败')
  } finally {
    loadingAudioFiles.value = false
  }
}

async function handleBeforeUpload(file) {
  try {
    const result = await uploadMultipleAudioFiles([file])
    if (result.success && result.data[0].upload_success) {
      message.success(`${file.name} 上传成功`)
      await loadAudioFiles() // 重新加载文件列表
    } else {
      message.error(`${file.name} 上传失败`)
    }
  } catch (error) {
    console.error('上传失败:', error)
    message.error(`${file.name} 上传失败`)
  }
  return false // 阻止默认上传行为
}

function handleSearch(value) {
  searchKeyword.value = value
}

function selectAudioFile(file) {
  selectedAudioFile.value = file
}

// 删除音频文件
async function handleDeleteAudioFile(file) {
  try {
    // 停止播放（如果正在播放这个文件）
    if (playingFileId.value === file.file_id) {
      if (audioFileElement) {
        audioFileElement.pause()
        audioFileElement = null
      }
      playingFileId.value = null
    }
    
    const result = await deleteAudioFile(file.file_id)
    if (result.success) {
      message.success('音频文件删除成功')
      await loadAudioFiles() // 重新加载文件列表
    } else {
      message.error('删除失败: ' + (result.message || '未知错误'))
    }
  } catch (error) {
    console.error('删除音频文件失败:', error)
    message.error('删除音频文件失败')
  }
}

function playAudioFile(file) {
  if (playingFileId.value === file.file_id) {
    // 停止播放
    if (audioFileElement) {
      audioFileElement.pause()
      audioFileElement = null
    }
    playingFileId.value = null
  } else {
    // 停止其他正在播放的音频文件
    if (audioFileElement) {
      audioFileElement.pause()
      audioFileElement = null
    }
    
    // 开始播放新文件
    try {
      const audioUrl = `http://localhost:8000/api/v1/audio-files/download/${file.file_id}`
      console.log('播放音频文件:', audioUrl)
      
      audioFileElement = new Audio(audioUrl)
      audioFileElement.crossOrigin = 'anonymous'
      
      audioFileElement.onloadstart = () => {
        console.log('开始加载音频文件')
      }
      
      audioFileElement.oncanplay = () => {
        console.log('音频可以播放')
        audioFileElement.play().then(() => {
          console.log('音频播放开始')
          playingFileId.value = file.file_id
        }).catch(error => {
          console.error('播放失败:', error)
          message.error('音频播放失败')
          playingFileId.value = null
          audioFileElement = null
        })
      }
      
      audioFileElement.onended = () => {
        console.log('音频播放结束')
        playingFileId.value = null
        audioFileElement = null
      }
      
      audioFileElement.onerror = (error) => {
        console.error('音频加载错误:', error)
        message.error('音频文件加载失败')
        playingFileId.value = null
        audioFileElement = null
      }
      
      // 开始加载
      audioFileElement.load()
      
    } catch (error) {
      console.error('创建音频元素失败:', error)
      message.error('音频播放失败')
      playingFileId.value = null
      audioFileElement = null
    }
  }
}

function isPlayingFile(fileId) {
  return playingFileId.value === fileId
}

function formatDuration(seconds) {
  if (!seconds) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

function refreshAudioFiles() {
  loadAudioFiles()
}

// 拖拽相关方法
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
}

function handleDragEnd(event) {
  isDragging.value = false
  draggedAudioFile.value = null
  
  // 移除拖拽样式
  event.target.classList.remove('dragging')
}
</script>

<style scoped>
.multitrack-editor {
  background: #1a1a1a;
  height: 100vh;
  display: flex;
  flex-direction: column;
  color: #fff;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a1a;
}

/* 上半部分：三栏布局 */
.top-section {
  height: calc(50% - 8px);
  display: flex;
  gap: 16px;
  padding: 16px;
}

.resource-panel, .preview-panel, .project-panel {
  background: #2a2a2a;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  border: 1px solid #333;
}

.resource-panel {
  flex: 3;
}

.preview-panel {
  flex: 4;
}

.project-panel {
  flex: 3;
}

/* 面板头部 */
.panel-header {
  padding: 12px 16px;
  background: #333;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.panel-header h4 {
  margin: 0;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

/* 面板内容 */
.panel-content {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

/* 资源库样式 */
.resource-tabs :deep(.ant-tabs-nav) {
  margin: 0;
}

.resource-tabs :deep(.ant-tabs-tab) {
  color: #ccc;
}

.resource-tabs :deep(.ant-tabs-tab-active) {
  color: #1890ff;
}

.resource-tabs :deep(.ant-tabs-content-holder) {
  padding-top: 16px;
}

.audio-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.upload-section {
  margin-bottom: 16px;
}

.search-section {
  margin-bottom: 16px;
}

.audio-files {
  flex: 1;
  overflow: auto;
}

.empty-audio {
  text-align: center;
  padding: 32px 16px;
  color: #666;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 14px;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 12px;
  color: #999;
}

.audio-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #3a3a3a;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
  border: 1px solid transparent;
}

.audio-item:hover {
  background: #404040;
  border-color: #555;
}

.audio-item:last-child {
  margin-bottom: 0;
}

.audio-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
  border-color: #52c41a;
  background: #1f2f1f;
}

.audio-item:hover {
  background: #404040;
  border-color: #555;
}

.audio-item:active {
  transform: scale(0.98);
}

.audio-preview {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #555;
  border-radius: 4px;
  margin-right: 12px;
}

.audio-info {
  flex: 1;
  min-width: 0;
}

.audio-name {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-meta {
  display: flex;
  gap: 8px;
  align-items: center;
}

.audio-duration, .audio-format {
  font-size: 11px;
  color: #999;
}

.audio-format {
  background: #555;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.audio-actions {
  margin-left: 8px;
}

.audio-actions .ant-btn-text.ant-btn-dangerous {
  color: #ff7875;
  opacity: 0.7;
  transition: all 0.2s;
}

.audio-actions .ant-btn-text.ant-btn-dangerous:hover {
  opacity: 1;
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.effect-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #3a3a3a;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.effect-item:hover {
  background: #404040;
}

.audio-preview, .effect-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #555;
  border-radius: 4px;
}

.audio-info {
  flex: 1;
}

.audio-name, .effect-name {
  color: #fff;
  font-size: 14px;
  margin-bottom: 4px;
}

.audio-duration {
  color: #999;
  font-size: 12px;
}

.audio-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.audio-format {
  background: #555;
  color: #ccc;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: 500;
}

.audio-hint {
  color: #666;
  font-size: 11px;
  font-style: italic;
  opacity: 0;
  transition: opacity 0.2s;
}

.audio-item:hover .audio-hint {
  opacity: 1;
}

/* 预览区域样式 */
.preview-area {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.waveform-display {
  flex: 1;
  background: #1e1e1e;
  border-radius: 6px;
  margin-bottom: 16px;
}

.waveform-container {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.waveform-placeholder {
  text-align: center;
  color: #666;
}

.waveform-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.waveform-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.waveform-info {
  font-size: 14px;
  color: #999;
}

.preview-controls {
  display: flex;
  align-items: center;
}

.preview-controls :deep(.ant-slider) {
  flex: 1;
}

.preview-controls :deep(.ant-slider-rail) {
  background: #444;
}

.preview-controls :deep(.ant-slider-track) {
  background: #1890ff;
}

.preview-controls :deep(.ant-slider-handle) {
  border-color: #1890ff;
}

/* 项目信息样式 */
.project-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-field label {
  color: #999;
  font-size: 12px;
  font-weight: 500;
}

.project-field span {
  color: #fff;
  font-size: 14px;
}

.project-actions {
  margin-top: 16px;
}

.project-empty {
  text-align: center;
  color: #666;
  padding: 32px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #999;
}

/* 下半部分：音轨编辑器 */
.bottom-section {
  height: calc(50% - 8px);
  display: flex;
  flex-direction: column;
  padding: 16px;
  padding-top: 0;
}

.timeline-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-radius: 8px;
  border: 1px solid #333;
  overflow: hidden;
}

.timeline-ruler {
  height: 40px;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  position: relative;
  display: flex;
}

.ruler-left-space {
  width: 200px;
  background: #333;
  border-right: 1px solid #444;
}

.time-markers {
  position: relative;
  height: 100%;
  flex: 1;
}

.time-marker {
  position: absolute;
  top: 0;
  height: 100%;
  border-left: 1px solid #444;
  padding-left: 4px;
  display: flex;
  align-items: center;
}

.time-label {
  font-size: 12px;
  color: #999;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4d4f;
  z-index: 10;
  pointer-events: none;
  transition: left 0.1s ease;
}

.playhead::before {
  content: '';
  position: absolute;
  top: -6px;
  left: -6px;
  width: 14px;
  height: 14px;
  background: #ff4d4f;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.tracks-container {
  flex: 1;
  min-height: 200px;
  overflow: auto;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-state :deep(.ant-empty-description) {
  color: #666;
}

/* 自定义按钮样式 */
:deep(.ant-btn-sm) {
  border-radius: 4px;
  font-size: 12px;
}

:deep(.ant-btn-primary) {
  background: #1890ff;
  border-color: #1890ff;
}

:deep(.ant-btn-primary:hover) {
  background: #40a9ff;
  border-color: #40a9ff;
}

/* 自定义模态框样式 */
:deep(.ant-modal-content) {
  background: #2a2a2a;
  color: #fff;
}

:deep(.ant-modal-header) {
  background: #333;
  border-bottom: 1px solid #444;
}

:deep(.ant-modal-title) {
  color: #fff;
}

:deep(.ant-modal-close-x) {
  color: #999;
}

:deep(.ant-modal-close-x:hover) {
  color: #fff;
}

.export-progress {
  text-align: center;
  padding: 20px;
}
</style> 