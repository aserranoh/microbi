import { ref } from 'vue'

// avrdude.js is loaded as a plain script in index.html; it exposes window.Module
declare global {
    interface Window {
        Module: (() => Promise<AvrdudeModule>) & { locateFile?: (path: string, dir: string) => string }
        funcs: AvrdudeModule
        activePort: SerialPort | null
        avrdudeLog: string[]
    }
}

interface AvrdudeModule {
    FS: {
        writeFile(path: string, data: string): void
    }
    cwrap(
        name: string,
        returnType: string,
        argTypes: string[],
        opts?: { async: boolean },
    ): (...args: unknown[]) => Promise<number>
    _malloc(size: number): number
    _errorCallback(): void
    _dataCallback(ptr: number, length: number): void
    HEAPU8: Uint8Array
}

let moduleReady: Promise<void> | null = null

function initModule(): Promise<void> {
    if (moduleReady) return moduleReady
    moduleReady = (async () => {
        const funcs = await window.Module()
        window.funcs = funcs

        const confResponse = await fetch('/avrdude/avrdude.conf')
        const confText = await confResponse.text()
        funcs.FS.writeFile('/tmp/avrdude.conf', confText)
    })()
    return moduleReady
}

export function useAvrdude() {
    const log = ref<string[]>([])
    const flashing = ref(false)

    async function listPorts(): Promise<SerialPort[]> {
        return navigator.serial.getPorts()
    }

    async function requestPort(): Promise<SerialPort> {
        return navigator.serial.requestPort()
    }

    async function flash(port: SerialPort, hexContent: string, mcu: string): Promise<void> {
        await initModule()

        window.activePort = port
        window.avrdudeLog = []
        log.value = []

        window.funcs.FS.writeFile('/tmp/program.hex', hexContent)

        const args = [
            'avrdude',
            '-P', '/dev/null',
            '-V',
            '-p', mcu,
            '-c', 'stk500v1',
            '-C', '/tmp/avrdude.conf',
            '-b', '115200',
            '-D',
            '-U', 'flash:w:/tmp/program.hex:i',
        ].join(' ')

        flashing.value = true
        try {
            const startAvrdude = window.funcs.cwrap('startAvrdude', 'number', ['string'], {
                async: true,
            })
            await startAvrdude(args)
        } finally {
            flashing.value = false
            log.value = window.avrdudeLog ?? []
        }
    }

    return { listPorts, requestPort, flash, flashing, log }
}
