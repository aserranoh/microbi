<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import Button from 'primevue/button'
import Popover from 'primevue/popover'
import BlockConfigPopover from '@/components/BlockConfigPopover.vue'
import { useBlockTypesStore } from '@/stores/blockTypes'
import type { Block, Program } from '@/api/types'

const props = defineProps<{
  data: {
    block: Block
    programId: string
    onUpdated: (program: Program) => void
    getOpenPopoverId: () => string | null
    onPopoverOpen: (id: string | null) => void
  }
}>()

const blockTypesStore = useBlockTypesStore()
const popoverRef = ref<InstanceType<typeof Popover> | null>(null)

const blockType = computed(() => blockTypesStore.getByName(props.data.block.block_type))

const inputPorts = computed(() => blockType.value?.ports.filter((p) => p.direction === 'input') ?? [])
const outputPorts = computed(() => blockType.value?.ports.filter((p) => p.direction === 'output') ?? [])
const configFields = computed(() => blockType.value?.configuration ?? [])
const maxPorts = computed(() => Math.max(inputPorts.value.length, outputPorts.value.length, 1))

// Layout constants (px)
const HANDLE_SIZE = 12
const HEADER_H = 32  // h-8
const NAME_H = 20    // h-5
const PORT_H = 24    // h-6
const PAD_BOTTOM = 8

const containerHeight = computed(() => HEADER_H + NAME_H + maxPorts.value * PORT_H + PAD_BOTTOM)

function portCenterY(index: number): number {
  return HEADER_H + NAME_H + index * PORT_H + PORT_H / 2
}

function inputHandleStyle(index: number) {
  return {
    top: `${portCenterY(index)}px`,
    left: '0px',
    width: `${HANDLE_SIZE}px`,
    height: `${HANDLE_SIZE}px`,
    borderRadius: '2px',
    transform: 'translateY(-50%)',
    background: 'var(--p-surface-400)',
  }
}

function outputHandleStyle(index: number) {
  return {
    top: `${portCenterY(index)}px`,
    right: '0px',
    left: 'auto',
    width: `${HANDLE_SIZE}px`,
    height: `${HANDLE_SIZE}px`,
    borderRadius: '2px',
    transform: 'translateY(-50%)',
    background: 'var(--p-primary-color)',
  }
}

// Close this popover when another block's popover becomes active
watch(
  () => props.data.getOpenPopoverId(),
  (id) => {
    if (id !== props.data.block.id) {
      popoverRef.value?.hide()
    }
  },
)

function togglePopover(event: MouseEvent) {
  const alreadyOpen = props.data.getOpenPopoverId() === props.data.block.id
  if (alreadyOpen) {
    popoverRef.value?.hide()
    props.data.onPopoverOpen(null)
  } else {
    props.data.onPopoverOpen(props.data.block.id)
    popoverRef.value?.show(event)
  }
}
</script>

<template>
  <!-- Outer container: full node area including handle margins -->
  <div class="relative" :style="{ width: '240px', height: `${containerHeight}px` }">
    <!-- Visible block box, inset by HANDLE_SIZE on each side -->
    <div
      class="absolute inset-y-0 bg-surface-0 dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-md shadow-md overflow-hidden"
      :style="{ left: `${HANDLE_SIZE}px`, right: `${HANDLE_SIZE}px` }"
    >
      <!-- Header: edit button in normal flow, title absolutely centered across full width -->
      <div
        class="relative flex items-center px-2 bg-primary-100 dark:bg-primary-900 border-b border-surface-200 dark:border-surface-600"
        :style="{ height: `${HEADER_H}px` }"
      >
        <span class="absolute inset-x-0 text-center text-xs italic text-primary-700 dark:text-primary-200 truncate px-6 pointer-events-none">
          {{ data.block.block_type }}
        </span>
        <Button
          icon="pi pi-pencil"
          size="small"
          text
          rounded
          severity="secondary"
          class="!p-0 !w-5 !h-5 ml-auto relative z-10"
          @click.stop="togglePopover"
        />
      </div>

      <!-- Block name centered -->
      <div
        class="flex items-center justify-center px-2"
        :style="{ height: `${NAME_H}px` }"
      >
        <span class="text-xs text-surface-500 dark:text-surface-400 font-mono truncate">
          {{ data.block.name }}
        </span>
      </div>

      <!-- Port name rows -->
      <div
        v-for="i in maxPorts"
        :key="i"
        class="flex items-center justify-between px-2"
        :style="{ height: `${PORT_H}px` }"
      >
        <span class="text-xs text-surface-600 dark:text-surface-300 truncate">
          {{ inputPorts[i - 1]?.name ?? '' }}
        </span>
        <span class="text-xs text-surface-600 dark:text-surface-300 truncate">
          {{ outputPorts[i - 1]?.name ?? '' }}
        </span>
      </div>
    </div>

    <!-- Input handles (positioned outside the left edge of the block box) -->
    <Handle
      v-for="(port, i) in inputPorts"
      :key="`in-${port.name}`"
      :id="`${data.block.id}__${port.name}`"
      type="target"
      :position="Position.Left"
      :style="inputHandleStyle(i)"
    />

    <!-- Output handles (positioned outside the right edge of the block box) -->
    <Handle
      v-for="(port, i) in outputPorts"
      :key="`out-${port.name}`"
      :id="`${data.block.id}__${port.name}`"
      type="source"
      :position="Position.Right"
      :style="outputHandleStyle(i)"
    />
  </div>

  <Popover ref="popoverRef" :pt="{ content: { class: 'p-2' } }">
    <BlockConfigPopover
      :block="data.block"
      :config-fields="configFields"
      :program-id="data.programId"
      @updated="(p) => data.onUpdated(p)"
    />
  </Popover>
</template>

