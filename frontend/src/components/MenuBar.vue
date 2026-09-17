<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Menubar from 'primevue/menubar'
import Button from 'primevue/button'
import Select from 'primevue/select'
import type { MenuItem } from 'primevue/menuitem'
import NewProgramDialog from '@/components/dialogs/NewProgramDialog.vue'
import OpenProgramDialog from '@/components/dialogs/OpenProgramDialog.vue'
import DownloadDialog from '@/components/dialogs/DownloadDialog.vue'
import { useProgramStore } from '@/stores/program'
import { createProgram, deleteProgram, updateProgram, buildProgram } from '@/api/programs'
import { getMcus } from '@/api/compiler'
import type { Program } from '@/api/types'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const programStore = useProgramStore()

const isDark = ref(document.documentElement.classList.contains('dark'))
const showNewDialog = ref(false)
const showOpenDialog = ref(false)
const showDownloadDialog = ref(false)
const downloadHex = ref('')
const downloadMcu = ref('')

const mcus = ref<string[]>([])
const selectedMcu = ref<string | null>(null)

getMcus().then((list) => {
  mcus.value = list
})

watch(
  () => programStore.currentProgram?.mcu,
  (mcu) => {
    selectedMcu.value = mcu ?? null
  },
  { immediate: true },
)

async function onMcuChange(mcu: string) {
  if (!programStore.currentProgram || mcu === programStore.currentProgram.mcu) return
  try {
    const updated = await updateProgram(programStore.currentProgram.id, { mcu })
    programStore.setProgram(updated)
  } catch {
    // revert selector to current program mcu on error
    selectedMcu.value = programStore.currentProgram.mcu
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.mcu_update_failed'), life: 3000 })
  }
}

function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
}

// menuItems must be computed so that `disabled` reacts to programStore changes
const menuItems = computed<MenuItem[]>(() => [
  {
    label: t('menu.programs'),
    items: [
      { label: t('menu.programs_new'), icon: 'pi pi-plus', command: () => { showNewDialog.value = true } },
      { label: t('menu.programs_open'), icon: 'pi pi-folder-open', command: () => { showOpenDialog.value = true } },
      {
        label: t('menu.programs_delete'),
        icon: 'pi pi-trash',
        disabled: !programStore.currentProgram,
        command: () => {
          if (!programStore.currentProgram) return
          confirm.require({
            header: t('confirm.delete_program_header'),
            message: t('confirm.delete_program_message', { name: programStore.currentProgram.name }),
            acceptLabel: t('confirm.yes'),
            rejectLabel: t('confirm.no'),
            accept: async () => {
              try {
                await deleteProgram(programStore.currentProgram!.id)
                programStore.setProgram(null)
                toast.add({ severity: 'success', summary: t('toast.success_title'), detail: t('toast.program_deleted'), life: 3000 })
              } catch {
                toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.error_title'), life: 3000 })
              }
            },
          })
        },
      },
    ],
  },
  {
    label: t('menu.project'),
    items: [
      {
        label: t('menu.project_download'),
        icon: 'pi pi-download',
        disabled: !programStore.currentProgram,
        command: async () => {
          if (!programStore.currentProgram) {
            toast.add({ severity: 'warn', summary: t('toast.error_title'), detail: t('toast.no_program_open'), life: 3000 })
            return
          }
          try {
            const result = await buildProgram(programStore.currentProgram.id)
            programStore.setProgram(result.program)
            if (result.errors.length > 0) {
              const detail = result.errors.map((e) => `${e.block_name}: ${e.error_message}`).join('\n')
              toast.add({ severity: 'error', summary: t('toast.build_error'), detail, life: 8000 })
              return
            }
            const hexArtifact = result.program.artifacts.find((a) => a.type === 'hex')
            if (!hexArtifact) {
              toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.no_hex_artifact'), life: 4000 })
              return
            }
            downloadHex.value = hexArtifact.contents
            downloadMcu.value = result.program.mcu
            showDownloadDialog.value = true
          } catch {
            toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.build_failed'), life: 3000 })
          }
        },
      },
    ],
  },
])

async function onNewProgram(name: string, mcu: string) {
  try {
    const program = await createProgram(name, mcu)
    programStore.setProgram(program)
    toast.add({ severity: 'success', summary: t('toast.success_title'), detail: t('toast.program_created', { name }), life: 3000 })
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? t('toast.error_title')
    toast.add({ severity: 'error', summary: t('toast.error_title'), detail, life: 4000 })
  }
}

async function onOpenProgram(program: Program) {
  programStore.setProgram(program)
  toast.add({ severity: 'success', summary: t('toast.success_title'), detail: t('toast.program_opened', { name: program.name }), life: 3000 })
}
</script>

<template>
  <!--
    border-none alone doesn't work because PrimeVue's unlayered CSS (cssLayer:false)
    outranks Tailwind utilities (which are in @layer utilities). We use pt.root to
    apply an inline style instead, which has highest CSS specificity.
  -->
  <div class="flex items-center border-b border-surface-200 dark:border-surface-700 px-2 bg-surface-0 dark:bg-surface-900 select-none">
    <Menubar
      :model="menuItems"
      :pt="{ root: { style: 'border: none; box-shadow: none; background: transparent; padding: 0;' } }"
    />
    <Select
      v-if="programStore.currentProgram"
      v-model="selectedMcu"
      :options="mcus"
      size="small"
      class="ml-1"
      :pt="{ root: { style: 'min-width: 8rem;' } }"
      @change="onMcuChange(selectedMcu!)"
    />
    <div class="flex-1" />
    <Button
      :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
      rounded
      text
      severity="secondary"
      :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
      @click="toggleDark"
    />
  </div>

  <NewProgramDialog v-model:visible="showNewDialog" @confirm="onNewProgram" />
  <OpenProgramDialog v-model:visible="showOpenDialog" @confirm="onOpenProgram" />
  <DownloadDialog v-model:visible="showDownloadDialog" :hex="downloadHex" :mcu="downloadMcu" />
</template>
