<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Button from 'primevue/button'
import { getMcus } from '@/api/compiler'

const { t } = useI18n()

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', name: string, mcu: string): void
}>()

const name = ref('')
const mcus = ref<string[]>([])
const selectedMcu = ref<string | null>(null)

watch(
  () => props.visible,
  async (visible) => {
    if (!visible) return
    mcus.value = await getMcus()
    if (mcus.value.length > 0) selectedMcu.value = mcus.value[0] ?? null
  },
)

function onConfirm() {
  if (!name.value.trim() || !selectedMcu.value) return
  emit('confirm', name.value.trim(), selectedMcu.value)
  name.value = ''
  emit('update:visible', false)
}

function onCancel() {
  name.value = ''
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    :modal="true"
    :closable="false"
    :draggable="false"
    class="w-80"
    @update:visible="emit('update:visible', $event)"
  >
    <template #header>
      <span class="font-semibold text-lg w-full text-center">{{ t('dialog.new_program.title') }}</span>
    </template>
    <div class="flex flex-col gap-3 mb-4">
      <div class="flex flex-col gap-1">
        <label class="text-xs text-surface-500">{{ t('dialog.new_program.name_label') }}</label>
        <InputText
          v-model="name"
          :placeholder="t('dialog.new_program.name_placeholder')"
          autofocus
          @keyup.enter="onConfirm"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs text-surface-500">{{ t('dialog.new_program.mcu_label') }}</label>
        <Select
          v-model="selectedMcu"
          :options="mcus"
          :placeholder="t('dialog.new_program.mcu_placeholder')"
          class="w-full"
        />
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <Button :label="t('dialog.new_program.cancel')" severity="secondary" @click="onCancel" />
        <Button
          :label="t('dialog.new_program.confirm')"
          :disabled="!name.trim() || !selectedMcu"
          @click="onConfirm"
        />
      </div>
    </template>
  </Dialog>
</template>
