import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { BlockType } from '@/api/types'
import { getBlockTypes } from '@/api/blockTypes'

export const useBlockTypesStore = defineStore('blockTypes', () => {
    const blockTypes = ref<BlockType[]>([])
    const loaded = ref(false)

    async function load() {
        if (loaded.value) return
        blockTypes.value = await getBlockTypes()
        loaded.value = true
    }

    function getByName(name: string): BlockType | undefined {
        return blockTypes.value.find((bt) => bt.name === name)
    }

    return { blockTypes, load, getByName }
})
