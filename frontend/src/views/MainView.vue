<script setup lang="ts">
import { onMounted } from 'vue'
import MenuBar from '@/components/MenuBar.vue'
import BlocksPanel from '@/components/BlocksPanel.vue'
import ProgramDiagram from '@/components/ProgramDiagram.vue'
import { useBlockTypesStore } from '@/stores/blockTypes'

const blockTypesStore = useBlockTypesStore()

onMounted(() => {
  blockTypesStore.load()
})
</script>

<template>
  <div class="flex flex-col h-screen overflow-hidden bg-surface-0 dark:bg-surface-950 text-surface-900 dark:text-surface-0">
    <MenuBar />
    <div class="flex flex-1 overflow-hidden">
      <BlocksPanel />
      <ProgramDiagram />
    </div>
  </div>
</template>
