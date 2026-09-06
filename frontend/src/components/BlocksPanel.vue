<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useBlockTypesStore } from '@/stores/blockTypes'

const { t } = useI18n()
const blockTypesStore = useBlockTypesStore()

function onDragStart(event: DragEvent, blockTypeName: string) {
  event.dataTransfer?.setData('application/microbi-block-type', blockTypeName)
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'copy'
  }
}
</script>

<template>
  <aside class="flex flex-col w-52 min-w-52 bg-surface-50 dark:bg-surface-800 border-r border-surface-200 dark:border-surface-700 p-3 gap-2 overflow-y-auto">
    <h2 class="text-sm font-semibold text-surface-600 dark:text-surface-300 uppercase tracking-wide mb-1">
      {{ t('blocks_panel.title') }}
    </h2>
    <p class="text-xs text-surface-400 dark:text-surface-500 mb-2">{{ t('blocks_panel.drag_hint') }}</p>
    <div
      v-for="bt in blockTypesStore.blockTypes"
      :key="bt.name"
      draggable="true"
      class="px-3 py-2 rounded bg-surface-100 dark:bg-surface-700 text-surface-800 dark:text-surface-100 text-sm cursor-grab select-none border border-surface-200 dark:border-surface-600 hover:bg-primary-50 dark:hover:bg-primary-900 transition-colors"
      @dragstart="onDragStart($event, bt.name)"
    >
      {{ bt.name }}
    </div>
  </aside>
</template>
