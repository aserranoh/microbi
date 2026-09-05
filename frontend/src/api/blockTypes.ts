import apiClient from './client'
import type { BlockType } from './types'

export async function getBlockTypes(): Promise<BlockType[]> {
    const response = await apiClient.get<BlockType[]>('/block-types/')
    return response.data
}
