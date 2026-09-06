import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Program } from '@/api/types'

export const useProgramStore = defineStore('program', () => {
    const currentProgram = ref<Program | null>(null)

    function setProgram(program: Program | null) {
        currentProgram.value = program
    }

    return { currentProgram, setProgram }
})
