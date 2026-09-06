<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'

const { t } = useI18n()

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
  (e: 'confirm', name: string): void
}>()

const name = ref('')

function onConfirm() {
  if (!name.value.trim()) return
  emit('confirm', name.value.trim())
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
    <div class="flex flex-col gap-1 mb-4">
      <label class="text-xs text-surface-500">{{ t('dialog.new_program.name_label') }}</label>
      <InputText
        v-model="name"
        :placeholder="t('dialog.new_program.name_placeholder')"
        autofocus
        @keyup.enter="onConfirm"
      />
    </div>
    <template #footer>
      <div class="flex justify-end gap-2">
        <Button :label="t('dialog.new_program.cancel')" severity="secondary" @click="onCancel" />
        <Button :label="t('dialog.new_program.confirm')" :disabled="!name.trim()" @click="onConfirm" />
      </div>
    </template>
  </Dialog>
</template>
