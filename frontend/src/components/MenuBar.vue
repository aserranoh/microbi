<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import Menubar from 'primevue/menubar'
import Button from 'primevue/button'
import type { MenuItem } from 'primevue/menuitem'
import NewProgramDialog from '@/components/dialogs/NewProgramDialog.vue'
import OpenProgramDialog from '@/components/dialogs/OpenProgramDialog.vue'
import { useProgramStore } from '@/stores/program'
import { createProgram, deleteProgram, generateCode } from '@/api/programs'
import type { Program } from '@/api/types'

const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const programStore = useProgramStore()

const isDark = ref(document.documentElement.classList.contains('dark'))
const showNewDialog = ref(false)
const showOpenDialog = ref(false)

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
        label: t('menu.project_build'),
        icon: 'pi pi-cog',
        command: async () => {
          if (!programStore.currentProgram) {
            toast.add({ severity: 'warn', summary: t('toast.error_title'), detail: t('toast.no_program_open'), life: 3000 })
            return
          }
          try {
            const result = await generateCode(programStore.currentProgram.id)
            if (result.errors.length > 0) {
              const detail = result.errors.map((e) => `${e.block_name}: ${e.error_message}`).join('\n')
              toast.add({ severity: 'error', summary: t('toast.build_error'), detail, life: 8000 })
            } else {
              const blob = new Blob([result.code], { type: 'text/plain' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = 'main.cpp'
              a.click()
              URL.revokeObjectURL(url)
              toast.add({ severity: 'success', summary: t('toast.success_title'), detail: t('toast.build_success'), life: 3000 })
            }
          } catch {
            toast.add({ severity: 'error', summary: t('toast.error_title'), detail: t('toast.error_title'), life: 3000 })
          }
        },
      },
    ],
  },
])

async function onNewProgram(name: string) {
  try {
    const program = await createProgram(name)
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
      class="flex-1"
      :pt="{ root: { style: 'border: none; box-shadow: none; background: transparent; padding: 0;' } }"
    />
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
</template>
