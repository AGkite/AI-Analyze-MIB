<template>
  <ul v-if="items.length" class="file-list">
    <li v-for="item in items" :key="item.path">
      <span class="name">{{ item.name }}</span>
      <span class="size">{{ formatSize(item.size) }}</span>
    </li>
  </ul>
  <el-empty v-else description="暂无文件" :image-size="48" />
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
})

function formatSize(n) {
  if (!n) return ''
  if (n < 1024) return `${n} B`
  return `${(n / 1024).toFixed(1)} KB`
}
</script>

<style scoped>
.file-list { list-style: none; padding: 0; margin: 0; }
.file-list li {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #eee;
  font-size: 13px;
}
.name { color: #303133; word-break: break-all; }
.size { color: #909399; flex-shrink: 0; margin-left: 8px; }
</style>
