import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 300000,
})

export async function getHealth() {
  const { data } = await api.get('/health')
  return data
}

export async function uploadFiles(files, autoIngest = true) {
  const form = new FormData()
  for (const f of files) {
    form.append('files', f)
  }
  const { data } = await api.post(`/upload?auto_ingest=${autoIngest}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getIngestStatus() {
  const { data } = await api.get('/ingest/status')
  return data
}

export async function triggerIngest() {
  const { data } = await api.post('/ingest')
  return data
}

export async function listFiles() {
  const { data } = await api.get('/files')
  return data
}

export async function chat(message, lookupOidOnline = true) {
  const { data } = await api.post('/chat', {
    message,
    lookup_oid_online: lookupOidOnline,
  })
  return data
}

export function chatStream(message, { onChunk, onSources, onOidLookups, onDone, onError }) {
  const controller = new AbortController()
  fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, lookup_oid_online: true }),
    signal: controller.signal,
  }).then(async (res) => {
    if (!res.ok) {
      onError?.(await res.text())
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const lines = part.split('\n')
        let event = 'message'
        let data = ''
        for (const line of lines) {
          if (line.startsWith('event:')) event = line.slice(6).trim()
          else if (line.startsWith('data:')) data += line.slice(5).trim()
        }
        if (event === 'sources') {
          try { onSources?.(JSON.parse(data)) } catch { onSources?.([]) }
        } else if (event === 'oid_lookups') {
          try { onOidLookups?.(JSON.parse(data)) } catch { /* ignore */ }
        } else if (event === 'error') onError?.(data)
        else if (event === 'done') onDone?.()
        else if (data && data !== '[DONE]') {
          try { onChunk?.(JSON.parse(data)) } catch { onChunk?.(data) }
        }
      }
    }
    onDone?.()
  }).catch((e) => onError?.(e.message))

  return () => controller.abort()
}

export default api
