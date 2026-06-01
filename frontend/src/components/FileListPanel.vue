<template>
  <el-card shadow="hover">
    <template #header>
      <div class="head">
        <span>知识库文件</span>
        <el-button link type="primary" @click="$emit('refresh')">刷新</el-button>
      </div>
    </template>

    <el-collapse>
      <el-collapse-item title="MIB 文件" name="mib">
        <FileRows :items="files.mib || []" />
      </el-collapse-item>
      <el-collapse-item title="Snmpwalk" name="walk">
        <FileRows :items="files.snmpwalk || []" />
      </el-collapse-item>
      <el-collapse-item title="OID 解析报告" name="gen">
        <FileRows :items="files.generated || []" />
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script setup>
import FileRows from './FileRows.vue'

defineProps({
  files: { type: Object, default: () => ({}) },
})
defineEmits(['refresh'])
</script>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: center; }
</style>
