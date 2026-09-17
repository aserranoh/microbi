/// <reference types="vite/client" />

// Minimal Web Serial API type declarations
interface SerialPortInfo {
    usbVendorId?: number
    usbProductId?: number
}

interface SerialOptions {
    baudRate: number
    dataBits?: number
    stopBits?: number
    parity?: string
    bufferSize?: number
    flowControl?: string
}

interface SerialOutputSignals {
    dataTerminalReady?: boolean
    requestToSend?: boolean
    break?: boolean
}

interface SerialPort {
    readonly readable: ReadableStream<Uint8Array> | null
    readonly writable: WritableStream<Uint8Array> | null
    getInfo(): SerialPortInfo
    open(options: SerialOptions): Promise<void>
    close(): Promise<void>
    setSignals(signals: SerialOutputSignals): Promise<void>
}

interface SerialPortRequestOptions {
    filters?: { usbVendorId?: number; usbProductId?: number }[]
}

interface Serial {
    getPorts(): Promise<SerialPort[]>
    requestPort(options?: SerialPortRequestOptions): Promise<SerialPort>
}

interface Navigator {
    readonly serial: Serial
}
