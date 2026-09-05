import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BlockType, Program } from '@/api/types'
import { getBlockTypes } from '@/api/blockTypes'

export const useProgramStore = defineStore('program', () => {
    const currentProgram = ref<Program | null>(null)
    const blockTypes = ref<BlockType[]>([])

    function setProgram(program: Program | null) {
        currentProgram.value = program
    }

    async function loadBlockTypes() {
        blockTypes.value = await getBlockTypes()
    }

    function getBlockType(name: string): BlockType | undefined {
        return blockTypes.value.find((bt) => bt.name === name)
    }

    return { currentProgram, blockTypes, setProgram, loadBlockTypes, getBlockType }
})
