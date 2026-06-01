<template>
  <div class="app">
    <header class="header">
      <div class="brand">
        <el-icon :size="28"><Connection /></el-icon>
        <div>
          <h1>AI-Analyze-MIB</h1>
          <p>企业 MIB / snmpwalk 智能分析</p>
        </div>
      </div>
      <div class="status-tags">
        <el-tag :type="health.minimax_configured ? 'success' : 'danger'" size="small">
          LLM {{ health.minimax_configured ? '已配置' : '未配置' }}
        </el-tag>
        <el-tag :type="health.vectorstore_ready ? 'success' : 'warning'" size="small">
          索引 {{ health.vectorstore_ready ? '就绪' : '未构建' }}
        </el-tag>
        <el-tag size="small" :type="ingestTagType">{{ ingestLabel }}</el-tag>
      </div>
    </header>

    <el-container class="main">
      <el-aside width="360px" class="aside">
        <UploadPanel
          :ingest-status="ingestStatus"
          @uploaded="onUploaded"
          @refresh-status="pollIngest"
        />
        <FileListPanel :files="fileList" @refresh="loadFiles" />
      </el-aside>

      <el-main class="chat-main">
        <ChatPanel
          :loading="chatLoading"
          :messages="messages"
          @send="onSend"
        />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import UploadPanel from './components/UploadPanel.vue'
import FileListPanel from './components/FileListPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import {
  chatStream,
  getHealth,
  getIngestStatus,
  listFiles,
} from './api/client.js'

const health = ref({ minimax_configured: false, vectorstore_ready: false })
const ingestStatus = ref({ status: 'idle', message: '' })
const fileList = ref({ mib: [], snmpwalk: [], generated: [] })
const messages = ref([])
const chatLoading = ref(false)
let pollTimer = null

const ingestLabel = computed(() => {
  const m = {
    idle: '索引: 空闲',
    queued: '索引: 排队',
    running: '索引: 构建中',
    done: '索引: 完成',
    error: '索引: 失败',
  }
  return m[ingestStatus.value.status] || ingestStatus.value.message
})

const ingestTagType = computed(() => {
  const t = { done: 'success', running: 'warning', error: 'danger', queued: 'info' }
  return t[ingestStatus.value.status] || 'info'
})

async function refreshHealth() {
  try {
    health.value = await getHealth()
  } catch {
    health.value = { minimax_configured: false, vectorstore_ready: false }
  }
}

async function pollIngest() {
  try {
    ingestStatus.value = await getIngestStatus()
    if (ingestStatus.value.status === 'done') {
      await refreshHealth()
      await loadFiles()
    }
  } catch { /* ignore */ }
}

async function loadFiles() {
  try {
    fileList.value = await listFiles()
  } catch { /* ignore */ }
}

function onUploaded() {
  pollIngest()
  loadFiles()
  if (!pollTimer) {
    pollTimer = setInterval(pollIngest, 2000)
  }
}

async function onSend(text) {
  if (!text.trim() || chatLoading.value) return

  messages.value.push({ role: 'user', content: text })
  const assistantMsg = {
    role: 'assistant',
    content: '',
    sources: [],
    oidLookups: [],
    streaming: true,
  }
  messages.value.push(assistantMsg)
  chatLoading.value = true

  chatStream(text, {
    onChunk: (chunk) => {
      assistantMsg.content += chunk
    },
    onSources: (sources) => {
      assistantMsg.sources = Array.isArray(sources) ? sources : []
    },
    onOidLookups: (lookups) => {
      assistantMsg.oidLookups = lookups || []
    },
    onError: (err) => {
      assistantMsg.content = `请求失败: ${err}`
      assistantMsg.streaming = false
      chatLoading.value = false
      ElMessage.error(String(err))
    },
    onDone: () => {
      assistantMsg.streaming = false
      chatLoading.value = false
    },
  })
}

onMounted(async () => {
  await refreshHealth()
  await pollIngest()
  await loadFiles()
  pollTimer = setInterval(pollIngest, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style>
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f0f2f5;
}
.app { min-height: 100vh; display: flex; flex-direction: column; }
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%);
  color: #fff;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand h1 { margin: 0; font-size: 1.25rem; }
.brand p { margin: 4px 0 0; opacity: 0.85; font-size: 0.85rem; }
.status-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.main { flex: 1; padding: 16px; gap: 16px; }
.aside { display: flex; flex-direction: column; gap: 16px; }
.chat-main {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  padding: 0 !important;
  overflow: hidden;
}
</style>
