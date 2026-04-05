<script setup lang="ts">
import { computed } from 'vue'
import markWorkspaceFrame from '@/assets/brand/mark-workspace-frame.svg'
import markPanelStack from '@/assets/brand/mark-panel-stack.svg'
import markMonogram from '@/assets/brand/mark-monogram.svg'

type BrandMarkVariant = 'workspace-frame' | 'panel-stack' | 'monogram'

const props = withDefaults(
  defineProps<{
    variant?: BrandMarkVariant
    alt?: string
  }>(),
  {
    variant: 'panel-stack',
    alt: 'Platform Workspace brand mark'
  }
)

const src = computed(() => {
  if (props.variant === 'panel-stack') {
    return markPanelStack
  }

  if (props.variant === 'monogram') {
    return markMonogram
  }

  return markWorkspaceFrame
})
</script>

<template>
  <img
    :src="src"
    :alt="alt"
    class="h-full w-full object-contain"
    draggable="false"
  >
</template>
