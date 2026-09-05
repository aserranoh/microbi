<script setup lang="ts">
import { computed, h, markRaw, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import {
  VueFlow,
  useVueFlow,
  type Node,
  type Edge,
  type Connection as VFConnection,
  type EdgeMouseEvent,
} from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import BlockNode from '@/components/BlockNode.vue'
import { useProgramStore } from '@/stores/program'
import { addBlock, connectBlocks, removeConnection } from '@/api/programs'
import type { Program } from '@/api/types'

const { t } = useI18n()
const toast = useToast()
const programStore = useProgramStore()
const { project } = useVueFlow()

const nodeTypes = { block: markRaw(BlockNode) }

// Convert program blocks/connections to VueFlow nodes/edges
const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])

function programToFlow(program: Program) {
  nodes.value = program.blocks.map((block) => ({
    id: block.id,
    type: 'block',
    position: block.position,
    data: {
      block,
      programId: program.id,
      onUpdated: handleProgramUpdate,
    },
  }))

  edges.value = program.connections.map((conn) => ({
    id: conn.id,
    source: conn.source.block_id,
    sourceHandle: `${conn.source.block_id}__${conn.source.port_name}`,
    target: conn.target.block_id,
    targetHandle: `${conn.target.block_id}__${conn.target.port_name}`,
  }))
}

watch(
  () => programStore.currentProgram,
  (program) => {
    if (program) programToFlow(program)
    else {
      nodes.value = []
      edges.value = []
    }
  },
  { immediate: true },
)

function handleProgramUpdate(program: Program) {
  programStore.setProgram(program)
}

// Drop handler: insert block
async function onDrop(event: DragEvent) {
  if (!programStore.currentProgram) {
    toast.add({ severity: 'warn', summary: t('toast.error_title'), detail: t('toast.no_program_open'), life: 3000 })
    return
  }

  const blockTypeName = event.dataTransfer?.getData('application/microbi-block-type')
  if (!blockTypeName) return

  // Convert screen coordinates to flow coordinates
  const flowWrapper = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = project({
    x: event.clientX - flowWrapper.left,
    y: event.clientY - flowWrapper.top,
  })

  try {
    const program = await addBlock(programStore.currentProgram.id, blockTypeName, position)
    programStore.setProgram(program)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.block_add_failed', { detail }), life: 4000 })
  }
}

function onDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'copy'
}

// Connect handler
async function onConnect(connection: VFConnection) {
  if (!programStore.currentProgram) return

  // Parse handle IDs: format is "{blockId}__{portName}"
  const parseHandle = (handleId: string) => {
    const sep = handleId.lastIndexOf('__')
    return { blockId: handleId.slice(0, sep), portName: handleId.slice(sep + 2) }
  }

  if (!connection.sourceHandle || !connection.targetHandle) return
  const src = parseHandle(connection.sourceHandle)
  const tgt = parseHandle(connection.targetHandle)

  try {
    const program = await connectBlocks(
      programStore.currentProgram.id,
      src.blockId,
      src.portName,
      tgt.blockId,
      tgt.portName,
    )
    programStore.setProgram(program)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.connection_failed', { detail }), life: 4000 })
  }
}

// Remove edge on click
async function onEdgeClick({ edge }: EdgeMouseEvent) {
  if (!programStore.currentProgram) return
  try {
    const program = await removeConnection(programStore.currentProgram.id, edge.id)
    programStore.setProgram(program)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
  }
}

// Sync node position back to backend on drag end (optimistic — position update via updateBlock could be added later)
// For now we just keep nodes in sync with the store state via watch.
</script>

<template>
  <div
    class="flex-1 relative bg-surface-100 dark:bg-surface-900"
    @drop.prevent="onDrop"
    @dragover="onDragOver"
  >
    <div
      v-if="!programStore.currentProgram"
      class="absolute inset-0 flex items-center justify-center text-surface-400 dark:text-surface-500 text-sm select-none"
    >
      {{ t('diagram.no_program') }}
    </div>

    <VueFlow
      v-else
      v-model:nodes="nodes"
      v-model:edges="edges"
      :node-types="nodeTypes"
      fit-view-on-init
      class="w-full h-full"
      @connect="onConnect"
      @edge-click="onEdgeClick"
    />
  </div>
</template>
