import apiClient from './client'
import type { DeviceInfo } from './types'

export async function getDevice(deviceId: string): Promise<DeviceInfo> {
    const response = await apiClient.get<DeviceInfo>(`/devices/${deviceId}`)
    return response.data
}
