<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { readRecentChatTarget, writeRecentChatTarget } from '@/utils/chatTarget'

const workspaceStore = useWorkspaceStore()
const notice = ref('')

const currentProject = computed(() => workspaceStore.currentProject)
const recentTarget = computed(() => {
  const projectId = workspaceStore.currentProjectId
  if (!projectId) {
    return null
  }
  return readRecentChatTarget(projectId)
})

const stats = computed(() => [
  {
    label: '预绑定 Graph',
    value: 'sql_agent',
    hint: 'SQL Agent 永远指向固定图谱目标',
    icon: 'sql-agent',
    tone: 'primary'
  },
  {
    label: '当前项目',
    value: currentProject.value?.name || '未选择',
    hint: '聊天目标会绑定到当前项目上下文',
    icon: 'project',
    tone: 'success'
  },
  {
    label: '最近聊天目标',
    value: recentTarget.value?.graphId || recentTarget.value?.assistantId || '--',
    hint: recentTarget.value ? `最近写入类型：${recentTarget.value.targetType}` : '当前项目还没有聊天目标偏好',
    icon: 'chat',
    tone: 'warning'
  }
])

function bindSqlAgent() {
  const projectId = workspaceStore.currentProjectId
  if (!projectId) {
    return
  }

  writeRecentChatTarget(projectId, {
    targetType: 'graph',
    graphId: 'sql_agent'
  })
  notice.value = '已将 sql_agent 写入当前项目的最近聊天目标，后续 Chat 页面会直接复用这个目标。'
}
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Agent"
      title="SQL Agent"
      description="SQL Agent 先做成专用启动页，把 `sql_agent` 这个固定图谱目标绑定到当前项目工作区。等 Chat 工作区完全迁过来后，这里会直接落到真实对话体验。"
    />

    <StateBanner
      v-if="notice"
      title="目标绑定成功"
      :description="notice"
      variant="success"
    />

    <div class="grid gap-4 xl:grid-cols-3">
      <MetricCard
        v-for="item in stats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :hint="item.hint"
        :icon="item.icon"
        :tone="item.tone"
      />
    </div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_360px]">
      <SurfaceCard class="space-y-5">
        <div class="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
          <BaseIcon
            name="sql-agent"
            size="sm"
            class="text-primary-500"
          />
          SQL Agent 入口说明
        </div>
        <p class="text-sm leading-7 text-gray-500 dark:text-dark-300">
          这块先把 SQL Agent 的目标绑定链路迁过来，不再依赖旧平台页面。当前阶段先把 graph 目标写入当前项目偏好，后面 Chat 页面完成迁移后会直接消费这份偏好。
        </p>
        <div class="pw-card-glass p-4">
          <div class="text-xs font-semibold uppercase tracking-[0.14em] text-gray-400 dark:text-dark-400">
            当前绑定
          </div>
          <div class="mt-2 text-lg font-semibold text-gray-950 dark:text-white">
            graph: sql_agent
          </div>
          <div class="mt-2 text-sm text-gray-500 dark:text-dark-300">
            适合直接进入数据库问答、查询解释和 SQL 调试场景。
          </div>
        </div>
        <div class="flex flex-wrap gap-3">
          <BaseButton
            :disabled="!currentProject"
            @click="bindSqlAgent"
          >
            设为当前项目聊天目标
          </BaseButton>
          <router-link
            class="pw-btn pw-btn-secondary"
            to="/workspace/graphs"
          >
            查看图谱目录
          </router-link>
        </div>
      </SurfaceCard>

      <SurfaceCard class="space-y-4">
        <div class="pw-page-eyebrow">
          Next
        </div>
        <div class="space-y-3 text-sm leading-7 text-gray-500 dark:text-dark-300">
          <p>当前页先解决目标绑定，不在这里硬塞半残的聊天实现。</p>
          <p>下一步 Chat 工作区迁过来后，会直接复用当前项目保存的最近目标偏好。</p>
        </div>
      </SurfaceCard>
    </div>
  </section>
</template>
