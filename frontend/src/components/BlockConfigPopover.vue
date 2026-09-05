<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Select from 'primevue/select'
import { isEnumField, isIntegerField } from '@/api/types'
import type { Block, ConfigField } from '@/api/types'
import { updateBlock } from '@/api/programs'
import type { Program } from '@/api/types'

const { t } = useI18n()
const toast = useToast()

const props = defineProps<{
  block: Block
  configFields: ConfigField[]
  programId: string
}>()

const emit = defineEmits<{
  (e: 'updated', program: Program): void
}>()

const localName = ref(props.block.name)
const localConfig = ref<Record<string, unknown>>({ ...props.block.configuration })

watch(
  () => props.block,
  (b) => {
    localName.value = b.name
    localConfig.value = { ...b.configuration }
  },
)

async function onSave() {
  try {
    const program = await updateBlock(
      props.programId,
      props.block.id,
      localName.value,
      localConfig.value,
    )
    emit('updated', program)
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
  }
}
</script>

<template>
  <div class="flex flex-col gap-3 p-1 min-w-48">
    <!-- Name field -->
    <div class="flex flex-col gap-1">
      <label class="text-xs text-surface-500 dark:text-surface-400">{{ t('block_config.name_label') }}</label>
      <InputText v-model="localName" size="small" class="w-full" />
    </div>

    <!-- Dynamic config fields -->
    <div v-for="field in configFields" :key="field.name" class="flex flex-col gap-1">
      <label class="text-xs text-surface-500 dark:text-surface-400 capitalize">{{ field.name }}</label>

      <Select
        v-if="isEnumField(field)"
        v-model="localConfig[field.name]"
        :options="field.choices"
        size="small"
        class="w-full"
      />

      <InputNumber
        v-else-if="isIntegerField(field)"
        v-model="localConfig[field.name] as number"
        :min="field.min ?? undefined"
        :max="field.max ?? undefined"
        :show-buttons="true"
        size="small"
        class="w-full"
      />
    </div>

    <Button :label="t('block_config.save')" size="small" class="mt-1" @click="onSave" />
  </div>
</template>
