<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Dialog from 'primevue/dialog'
import Select from 'primevue/select'
import Button from 'primevue/button'
import { useAvrdude } from '@/composables/useAvrdude'
import { getDevice } from '@/api/devices'
import type { DeviceInfo } from '@/api/types'

const { t } = useI18n()

const props = defineProps<{
  visible: boolean
  hex: string
  mcu: string
}>()
const emit = defineEmits<{
  (e: 'update:visible', v: boolean): void
}>()

const { listPorts, requestPort, flash, flashing } = useAvrdude()

interface PortItem {
  port: SerialPort
  device: DeviceInfo
}

const portItems = ref<PortItem[]>([])
const selectedItem = ref<PortItem | null>(null)
const flashError = ref<string | null>(null)
const showSuccess = ref(false)
const successDeviceName = ref('')

async function buildPortItems(): Promise<void> {
  const ports = await listPorts()
  portItems.value = await Promise.all(
    ports.map(async (port) => {
      const info = port.getInfo()
      const vendor = info.usbVendorId?.toString(16).padStart(4, '0') ?? '0000'
      const product = info.usbProductId?.toString(16).padStart(4, '0') ?? '0000'
      const device = await getDevice(`${vendor}:${product}`)
      return { port, device }
    }),
  )
  if (portItems.value.length > 0 && !selectedItem.value) {
    selectedItem.value = portItems.value[0] ?? null
  }
}

watch(
  () => props.visible,
  (visible) => {
    if (!visible) return
    flashError.value = null
    showSuccess.value = false
    selectedItem.value = null
    buildPortItems()
  },
)

async function onGrantPort() {
  try {
    await requestPort()
    await buildPortItems()
  } catch {
    // user cancelled the picker
  }
}

async function onFlash() {
  if (!selectedItem.value) return
  flashError.value = null
  try {
    await flash(selectedItem.value.port, props.hex, props.mcu)
    successDeviceName.value = selectedItem.value.device.name
    showSuccess.value = true
  } catch (err) {
    flashError.value = err instanceof Error ? err.message : String(err)
  }
}

function onSuccessClose() {
  showSuccess.value = false
  emit('update:visible', false)
}

function onClose() {
  emit('update:visible', false)
}
</script>

<template>
  <Dialog
    :visible="props.visible"
    :modal="true"
    :closable="!flashing"
    :draggable="false"
    class="w-[28rem]"
    @update:visible="emit('update:visible', $event)"
  >
    <template #header>
      <span class="font-semibold text-lg w-full text-center">{{ t('dialog.download.title') }}</span>
    </template>

    <div class="flex flex-col gap-3">
      <!-- Port selector -->
      <div v-if="!flashing" class="flex flex-col gap-1">
        <label class="text-xs text-surface-500">{{ t('dialog.download.port_label') }}</label>
        <div class="flex gap-2">
          <Select
            v-model="selectedItem"
            :options="portItems"
            option-label="device.name"
            :placeholder="t('dialog.download.no_ports')"
            class="flex-1"
          />
          <Button
            :label="t('dialog.download.grant_port')"
            severity="secondary"
            @click="onGrantPort"
          />
        </div>
      </div>

      <!-- Spinner while flashing -->
      <div v-if="flashing" class="flex flex-col items-center gap-3 py-4">
        <i class="pi pi-spin pi-spinner text-4xl text-primary" />
        <span class="text-sm text-surface-500">{{ t('dialog.download.flashing') }}</span>
      </div>

      <div v-if="flashError" class="text-sm text-red-600">
        {{ flashError }}
      </div>
    </div>

    <template #footer>
      <div v-if="!flashing" class="flex justify-end gap-2">
        <Button
          :label="t('dialog.download.close')"
          severity="secondary"
          @click="onClose"
        />
        <Button
          :label="t('dialog.download.flash')"
          icon="pi pi-download"
          :disabled="!selectedItem"
          @click="onFlash"
        />
      </div>
    </template>
  </Dialog>

  <!-- Success message box -->
  <Dialog
    :visible="showSuccess"
    :modal="true"
    :closable="false"
    :draggable="false"
    class="w-80"
    @update:visible="showSuccess = $event"
  >
    <template #header>
      <span class="font-semibold text-lg w-full text-center">{{ t('dialog.download.success_title') }}</span>
    </template>
    <p class="text-sm text-center">
      {{ t('dialog.download.success_message', { device: successDeviceName }) }}
    </p>
    <template #footer>
      <div class="flex justify-center">
        <Button :label="t('dialog.download.success_close')" @click="onSuccessClose" />
      </div>
    </template>
  </Dialog>
</template>

