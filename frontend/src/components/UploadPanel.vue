<template>
  <el-card shadow="hover">
    <template #header>
      <span>上传分析文件</span>
    </template>

    <el-upload
      drag
      multiple
      :auto-upload="false"
      :file-list="fileList"
      :on-change="onChange"
      :on-remove="onRemove"
      accept=".mib,.my,.smi,.snmpwalk,.walk,.txt,.out,.log"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        拖拽或点击上传 <em>MIB</em> / <em>snmpwalk</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 .mib .snmpwalk .walk .txt，单文件最大 20MB。上传后自动解析 OID 并构建索引。
        </div>
      </template>
    </el-upload>

    <div class="actions">
      <el-button type="primary" :loading="uploading" @click="doUpload">
        上传并分析
      </el-button>
      <el-button :loading="ingestStatus.status === 'running'" @click="reIngest">
        重建索引
      </el-button>
    </div>

    <el-alert
      v-if="ingestStatus.message"
      :title="ingestStatus.message"
      :type="alertType"
      :closable="false"
      show-icon
      class="ingest-alert"
    />
  </el-card>
</template>

<script setup>
import { computed, ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { triggerIngest, uploadFiles } from '../api/client.js'

const props = defineProps({
  ingestStatus: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['uploaded', 'refresh-status'])

const fileList = ref([])
const rawFiles = ref([])
const uploading = ref(false)

const alertType = computed(() => {
  const t = { done: 'success', running: 'info', error: 'error' }
  return t[props.ingestStatus.status] || 'info'
})

function onChange(file, list) {
  fileList.value = list
  rawFiles.value = list.map((f) => f.raw).filter(Boolean)
}

function onRemove(file, list) {
  fileList.value = list
  rawFiles.value = list.map((f) => f.raw).filter(Boolean)
}

async function doUpload() {
  if (!rawFiles.value.length) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  try {
    const res = await uploadFiles(rawFiles.value)
    ElMessage.success(res.message)
    fileList.value = []
    rawFiles.value = []
    emit('uploaded')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || e.message)
  } finally {
    uploading.value = false
  }
}

async function reIngest() {
  try {
    await triggerIngest()
    emit('refresh-status')
    ElMessage.info('索引重建已启动')
  } catch (e) {
    ElMessage.error(e.message)
  }
}
</script>

<style scoped>
.actions { margin-top: 16px; display: flex; gap: 8px; }
.ingest-alert { margin-top: 12px; }
</style>
