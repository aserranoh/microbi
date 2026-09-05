<script setup lang="ts">
import { computed, ref } from 'vue'
import { Handle, Position } from '@vue-flow/core'
import Button from 'primevue/button'
import Popover from 'primevue/popover'
import BlockConfigPopover from '@/components/BlockConfigPopover.vue'
import { useProgramStore } from '@/stores/program'
import type { Block, Program } from '@/api/types'

const props = defineProps<{
  data: {
    block: Block
    programId: string
    onUpdated: (program: Program) => void
  }
}>()

const programStore = useProgramStore()
const popoverRef = ref<InstanceType<typeof Popover> | null>(null)

const blockType = computed(() => programStore.getBlockType(props.data.block.block_type))

const inputPorts = computed(() =>
  blockType.value?.ports.filter((p) => p.direction === 'input') ?? [],
)
const outputPorts = computed(() =>
  blockType.value?.ports.filter((p) => p.direction === 'output') ?? [],
)

const configFields = computed(() => blockType.value?.configuration ?? [])

const maxPorts = computed(() => Math.max(inputPorts.value.length, outputPorts.value.length, 1))
const nodeHeight = computed(() => 56 + maxPorts.value * 28)

function togglePopover(event: MouseEvent) {
  popoverRef.value?.toggle(event)
}
</script>

<template>
  <div
    class="relative bg-surface-0 dark:bg-surface-800 border border-surface-300 dark:border-surface-600 rounded-lg shadow-md overflow-visible"
    :style="{ minWidth: '180px', height: nodeHeight + 'px' }"
  >
    <!-- Header -->
    <div class="flex items-center justify-between px-2 py-1 bg-primary-100 dark:bg-primary-900 rounded-t-lg border-b border-surface-300 dark:border-surface-600">
      <span class="text-xs font-semibold text-primary-700 dark:text-primary-200 truncate">
        {{ data.block.block_type }}
      </span>
      <Button
        icon="pi pi-pencil"
        size="small"
        text
        rounded
        severity="secondary"
        class="!p-0 !w-5 !h-5"
        @click="togglePopover"
      />
    </div>

    <!-- Block name -->
    <div class="px-2 pt-1 pb-0">
      <span class="text-xs text-surface-500 dark:text-surface-400 font-mono">{{ data.block.name }}</span>
    </div>

    <!-- Ports row -->
    <div class="absolute inset-x-0 bottom-0 top-11 flex">
      <!-- Input ports (left) -->
      <div class="flex flex-col justify-around flex-1 pl-2 py-1">
        <div
          v-for="port in inputPorts"
          :key="port.name"
          class="relative flex items-center"
          style="height: 24px"
        >
          <Handle
            :id="`${data.block.id}__${port.name}`"
            type="target"
            :position="Position.Left"
            class="!static !transform-none !relative !w-3 !h-3 !rounded-full !bg-surface-400 dark:!bg-surface-500 !border-2 !border-surface-0 dark:!border-surface-800"
          />
          <span class="ml-1 text-xs text-surface-600 dark:text-surface-300 truncate">{{ port.name }}</span>
        </div>
      </div>

      <!-- Output ports (right) -->
      <div class="flex flex-col justify-around flex-1 pr-2 py-1 items-end">
        <div
          v-for="port in outputPorts"
          :key="port.name"
          class="relative flex items-center"
          style="height: 24px"
        >
          <span class="mr-1 text-xs text-surface-600 dark:text-surface-300 truncate">{{ port.name }}</span>
          <Handle
            :id="`${data.block.id}__${port.name}`"
            type="source"
            :position="Position.Right"
            class="!static !transform-none !relative !w-3 !h-3 !rounded-full !bg-primary-400 !border-2 !border-surface-0 dark:!border-surface-800"
          />
        </div>
      </div>
    </div>
  </div>

  <Popover ref="popoverRef">
    <BlockConfigPopover
      :block="data.block"
      :config-fields="configFields"
      :program-id="data.programId"
      @updated="(p) => { popoverRef?.hide(); data.onUpdated(p) }"
    />
  </Popover>
</template>
