import apiClient from './client'
import type { BuildResult, Program } from './types'

export async function getPrograms(): Promise<Program[]> {
    const response = await apiClient.get<Program[]>('/programs/')
    return response.data
}

export async function getProgram(id: string): Promise<Program> {
    const response = await apiClient.get<Program>(`/programs/${id}`)
    return response.data
}

export async function createProgram(name: string, mcu: string): Promise<Program> {
    const response = await apiClient.post<Program>('/programs/', {
        request_in: { name, mcu },
    })
    return response.data
}

export async function updateProgram(
    id: string,
    fields: { name?: string; mcu?: string },
): Promise<Program> {
    const response = await apiClient.put<Program>(`/programs/${id}`, {
        request_in: fields,
    })
    return response.data
}

export async function deleteProgram(id: string): Promise<void> {
    await apiClient.delete(`/programs/${id}`)
}

export async function addBlock(
    programId: string,
    blockTypeName: string,
    position: { x: number; y: number },
): Promise<Program> {
    const response = await apiClient.post<Program>(`/programs/${programId}/blocks`, {
        program_id: programId,
        block_type_name: blockTypeName,
        block_position: position,
    })
    return response.data
}

export async function deleteBlock(programId: string, blockId: string): Promise<void> {
    await apiClient.delete(`/programs/${programId}/blocks/${blockId}`)
}

export async function updateBlock(
    programId: string,
    blockId: string,
    blockName?: string,
    blockConfig?: Record<string, unknown>,
    blockPosition?: { x: number; y: number },
): Promise<Program> {
    const response = await apiClient.put<Program>(`/programs/${programId}/blocks/${blockId}`, {
        program_id: programId,
        ...(blockName !== undefined && { block_name: blockName }),
        ...(blockConfig !== undefined && { block_config: blockConfig }),
        ...(blockPosition !== undefined && { block_position: blockPosition }),
    })
    return response.data
}

export async function connectBlocks(
    programId: string,
    sourceBlockId: string,
    sourcePort: string,
    targetBlockId: string,
    targetPort: string,
): Promise<Program> {
    const response = await apiClient.patch<Program>(`/programs/${programId}/connect`, {
        source_block_id: sourceBlockId,
        source_port: sourcePort,
        target_block_id: targetBlockId,
        target_port: targetPort,
    })
    return response.data
}

export async function removeConnection(programId: string, connectionId: string): Promise<Program> {
    const response = await apiClient.delete<Program>(
        `/programs/${programId}/connections/${connectionId}`,
    )
    return response.data
}

export async function buildProgram(programId: string): Promise<BuildResult> {
    const response = await apiClient.post<BuildResult>(`/programs/${programId}/build`)
    return response.data
}
