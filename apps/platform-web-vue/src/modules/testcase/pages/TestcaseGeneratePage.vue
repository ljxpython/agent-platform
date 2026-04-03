<script setup lang="ts">
import { computed } from 'vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import TestcaseOverviewStrip from '@/components/platform/TestcaseOverviewStrip.vue'
import TestcaseWorkspaceNav from '@/components/platform/TestcaseWorkspaceNav.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspaceStore = useWorkspaceStore()

const overview = computed(() => null)
</script>

<template>
  <section class="pw-page-shell">
    <TestcaseWorkspaceNav />

    <PageHeader
      eyebrow="Testcase"
      title="Testcase · AI 对话生成"
      description="这里后续会固定绑定 `test_case_agent`。当前先把 testcase 工作区的一级入口和三个二级页面结构迁过来，避免导航和层级继续乱着。"
    />

    <TestcaseOverviewStrip :overview="overview" />

    <SurfaceCard class="space-y-4">
      <div class="text-sm font-semibold text-gray-900 dark:text-white">
        当前状态
      </div>
      <p class="text-sm leading-7 text-gray-500 dark:text-dark-300">
        generate 子页会作为 testcase 的 AI 对话入口，后面接入 `test_case_agent` 聊天模板。当前阶段先把工作区壳层、层级和导航结构打稳。
      </p>
      <div class="pw-card-glass p-4 text-sm text-gray-500 dark:text-dark-300">
        当前项目：{{ workspaceStore.currentProject?.name || '未选择' }}
      </div>
    </SurfaceCard>
  </section>
</template>
