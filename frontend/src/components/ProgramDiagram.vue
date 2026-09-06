<script setup lang="ts">
import { markRaw, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import {
  VueFlow,
  useVueFlow,
  type Node,
  type Edge,
  type Connection as VFConnection,
  type NodeDragEvent,
} from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import BlockNode from '@/components/BlockNode.vue'
import { useProgramStore } from '@/stores/program'
import { addBlock, connectBlocks, deleteBlock, removeConnection, updateBlock } from '@/api/programs'
import type { Program } from '@/api/types'

const { t } = useI18n()
const toast = useToast()
const programStore = useProgramStore()
const { project } = useVueFlow()
const vueFlow = useVueFlow()

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const nodeTypes = { block: markRaw(BlockNode) } as any
const nodes = ref<Node[]>([])
const edges = ref<Edge[]>([])

// Shared ref so only one block's config popover can be open at a time
const openPopoverId = ref<string | null>(null)
function onPopoverOpen(id: string | null) { openPopoverId.value = id }

function buildEdges(program: Program): Edge[] {
  return program.connections.map((conn) => ({
    id: conn.id,
    source: conn.source.block_id,
    sourceHandle: `${conn.source.block_id}__${conn.source.port_name}`,
    target: conn.target.block_id,
    targetHandle: `${conn.target.block_id}__${conn.target.port_name}`,
  }))
}

function programToFlow(program: Program) {
  nodes.value = program.blocks.map((block) => ({
    id: block.id,
    type: 'block',
    position: block.position,
    data: {
      block,
      programId: program.id,
      onUpdated: handleBlockUpdate,
      // Getter avoids Ref auto-unwrap when VueFlow processes node data
      getOpenPopoverId: () => openPopoverId.value,
      onPopoverOpen,
    },
  })) as Node[]
  edges.value = buildEdges(program)
}

watch(
  () => programStore.currentProgram,
  async (program) => {
    if (program) {
      programToFlow(program)
    } else {
      nodes.value = []
      edges.value = []
    }
  },
  { immediate: true },
)

// Update block data in VueFlow without rebuilding the whole diagram.
// This preserves component instances (open popovers stay open).
function handleBlockUpdate(program: Program) {
  for (const block of program.blocks) {
    const node = nodes.value.find((n) => n.id === block.id)
    if (node) {
      // Spread preserves openPopoverId and onPopoverOpen in data
      node.data = { ...node.data, block }
    }
  }
  edges.value = buildEdges(program)
  // Directly mutate store (avoids triggering the watch above)
  if (programStore.currentProgram) {
    programStore.currentProgram.blocks = program.blocks
    programStore.currentProgram.connections = program.connections
  }
}

// Drop: add block at cursor position
async function onDrop(event: DragEvent) {
  if (!programStore.currentProgram) {
    toast.add({ severity: 'warn', summary: t('toast.error_title'), detail: t('toast.no_program_open'), life: 3000 })
    return
  }
  const blockTypeName = event.dataTransfer?.getData('application/microbi-block-type')
  if (!blockTypeName) return

  const flowWrapper = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const position = project({ x: event.clientX - flowWrapper.left, y: event.clientY - flowWrapper.top })

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

// Connect two handles
async function onConnect(connection: VFConnection) {
  if (!programStore.currentProgram) return

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

// Sync block position to backend when drag ends
async function onNodeDragStop({ node }: NodeDragEvent) {
  if (!programStore.currentProgram) return
  try {
    await updateBlock(
      programStore.currentProgram.id,
      node.id,
      undefined,
      undefined,
      node.position,
    )
    // Silently update position in store without triggering diagram rebuild
    const block = programStore.currentProgram.blocks.find((b) => b.id === node.id)
    if (block) block.position = node.position
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
  }
}

// Delete selected nodes/edges when DEL key is pressed
async function onKeyDown(event: KeyboardEvent) {
  if (event.key !== 'Delete') return
  const tag = (event.target as HTMLElement)?.tagName?.toLowerCase()
  if (tag === 'input' || tag === 'textarea') return
  if ((event.target as HTMLElement)?.isContentEditable) return
  if (!programStore.currentProgram) return

  // getSelectedNodes/getSelectedEdges are ComputedRefs despite the type saying GraphNode[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const toDeleteNodes = [...((vueFlow as any).getSelectedNodes?.value ?? [])] as Array<{ id: string }>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const toDeleteEdges = [...((vueFlow as any).getSelectedEdges?.value ?? [])] as Array<{ id: string }>

  for (const node of toDeleteNodes) {
    try {
      await deleteBlock(programStore.currentProgram.id, node.id)
      nodes.value = nodes.value.filter((n) => n.id !== node.id)
      edges.value = edges.value.filter((e) => e.source !== node.id && e.target !== node.id)
      if (programStore.currentProgram) {
        programStore.currentProgram.blocks = programStore.currentProgram.blocks.filter((b) => b.id !== node.id)
        programStore.currentProgram.connections = programStore.currentProgram.connections.filter(
          (c) => c.source.block_id !== node.id && c.target.block_id !== node.id,
        )
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
      toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
    }
  }

  for (const edge of toDeleteEdges) {
    try {
      const program = await removeConnection(programStore.currentProgram.id, edge.id)
      edges.value = edges.value.filter((e) => e.id !== edge.id)
      if (programStore.currentProgram) {
        programStore.currentProgram.connections = program.connections
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
      toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
    }
  }
}

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))
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
      :delete-key-code="null"
      :default-viewport="{ zoom: 1 }"
      class="w-full h-full"
      @connect="onConnect"
      @node-drag-stop="onNodeDragStop"
    />
  </div>
</template>

