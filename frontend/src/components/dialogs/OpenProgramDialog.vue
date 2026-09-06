<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import type { Program } from '@/api/types'
import { getPrograms } from '@/api/programs'

const { t } = useI18n()

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', program: Program): void
}>()

const programs = ref<Program[]>([])
const selected = ref<Program | null>(null)

watch(
  () => props.visible,
  async (v) => {
    if (v) {
      programs.value = await getPrograms()
      selected.value = null
    }
  },
)

function onConfirm() {
  if (!selected.value) return
  emit('confirm', selected.value)
  emit('update:visible', false)
}

function onCancel() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    :modal="true"
    :closable="false"
    :draggable="false"
    class="w-96"
    @update:visible="emit('update:visible', $event)"
  >
    <template #header>
      <span class="font-semibold text-lg w-full text-center">{{ t('dialog.open_program.title') }}</span>
    </template>
    <div class="flex flex-col gap-1 mb-4 min-h-24">
      <p v-if="programs.length === 0" class="text-surface-500 text-sm">
        {{ t('dialog.open_program.no_programs') }}
      </p>
      <div
        v-for="prog in programs"
        :key="prog.id"
        class="px-3 py-2 rounded cursor-pointer transition-colors"
        :class="selected?.id === prog.id ? 'bg-primary text-primary-contrast' : 'hover:bg-surface-100 dark:hover:bg-surface-700'"
        @click="selected = prog"
      >
        {{ prog.name }}
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <Button :label="t('dialog.open_program.cancel')" severity="secondary" @click="onCancel" />
        <Button :label="t('dialog.open_program.confirm')" :disabled="!selected" @click="onConfirm" />
      </div>
    </template>
  </Dialog>
</template>
