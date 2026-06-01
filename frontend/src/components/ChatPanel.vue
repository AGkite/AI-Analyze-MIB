<template>
  <div class="chat-panel">
    <div ref="scrollRef" class="messages">
      <div v-if="!messages.length" class="welcome">
        <h2>开始分析</h2>
        <p>上传企业 MIB 与 snmpwalk 后，可在此提问，例如：</p>
        <ul>
          <li>解析 walk 中的 cpuUsage 对应哪个 OID？</li>
          <li>1.3.6.1.4.1.99999.1.1.0 是什么含义？</li>
          <li>对比 MIB 与 walk 结果是否一致？</li>
        </ul>
      </div>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['msg', msg.role]"
      >
        <div class="bubble">
          <div v-if="msg.role === 'assistant'" class="md" v-html="renderMd(msg.content)" />
          <div v-else>{{ msg.content }}</div>
          <span v-if="msg.streaming" class="cursor">▌</span>
        </div>

        <div v-if="msg.oidLookups?.length" class="meta oid-meta">
          <el-collapse>
            <el-collapse-item title="OID 联网解析" name="oid">
              <div v-for="o in msg.oidLookups" :key="o.oid" class="oid-row">
                <el-tag size="small" :type="sourceTag(o.source)">{{ o.source }}</el-tag>
                <code>{{ o.oid }}</code>
                <span>{{ o.name || '—' }}</span>
                <p class="desc">{{ o.description }}</p>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>

        <div v-if="msg.sources?.length" class="meta">
          <span class="label">参考来源：</span>
          <el-tag v-for="s in msg.sources" :key="s" size="small" type="info">{{ s }}</el-tag>
        </div>
      </div>
    </div>

    <div class="input-bar">
      <el-input
        v-model="input"
        type="textarea"
        :rows="2"
        placeholder="输入问题…（含 OID 时将自动联网查询）"
        :disabled="loading"
        @keydown.enter.exact.prevent="submit"
      />
      <el-button type="primary" :loading="loading" @click="submit">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['send'])

const input = ref('')
const scrollRef = ref(null)

function renderMd(text) {
  if (!text) return ''
  return marked.parse(text, { breaks: true })
}

function sourceTag(source) {
  const m = { common: 'success', observium: 'primary', web_search: 'warning', unknown: 'info' }
  return m[source] || 'info'
}

function submit() {
  const t = input.value.trim()
  if (!t) return
  emit('send', t)
  input.value = ''
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  },
  { deep: true },
)
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: calc(100vh - 120px); min-height: 480px; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.welcome { color: #606266; max-width: 520px; }
.welcome h2 { margin-top: 0; color: #303133; }
.welcome ul { padding-left: 20px; line-height: 1.8; }
.msg { margin-bottom: 20px; }
.msg.user { display: flex; justify-content: flex-end; }
.msg.user .bubble {
  background: #409eff;
  color: #fff;
  border-radius: 12px 12px 4px 12px;
  max-width: 75%;
}
.msg.assistant .bubble {
  background: #f4f4f5;
  border-radius: 12px 12px 12px 4px;
  max-width: 90%;
}
.bubble { padding: 12px 16px; line-height: 1.6; }
.bubble :deep(pre) { background: #1e1e1e; color: #eee; padding: 8px; border-radius: 6px; overflow-x: auto; }
.cursor { animation: blink 1s infinite; }
@keyframes blink { 50% { opacity: 0; } }
.meta { margin-top: 8px; font-size: 12px; }
.meta .label { color: #909399; margin-right: 8px; }
.meta .el-tag { margin-right: 4px; margin-bottom: 4px; }
.oid-row { margin-bottom: 10px; font-size: 13px; }
.oid-row code { margin: 0 8px; background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }
.oid-row .desc { margin: 4px 0 0; color: #606266; }
.input-bar {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #ebeef5;
  background: #fafafa;
}
.input-bar .el-textarea { flex: 1; }
</style>
