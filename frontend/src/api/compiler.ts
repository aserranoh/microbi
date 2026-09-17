import apiClient from './client'

export async function getMcus(): Promise<string[]> {
    const response = await apiClient.get<string[]>('/compiler/mcus/')
    return response.data
}
