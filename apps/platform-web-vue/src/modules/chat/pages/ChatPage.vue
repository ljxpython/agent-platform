<script setup lang="ts">
import { computed, watchEffect } from 'vue'
import { useRoute } from 'vue-router'
import BaseIcon from '@/components/base/BaseIcon.vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/platform/EmptyState.vue'
import MetricCard from '@/components/platform/MetricCard.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import { useWorkspaceStore } from '@/stores/workspace'
import {
  clearRecentChatTarget,
  normalizeChatTarget,
  readRecentChatTarget,
  writeRecentChatTarget
} from '@/utils/chatTarget'

const route = useRoute()
const workspaceStore = useWorkspaceStore()

const explicitTarget = computed(() =>
  normalizeChatTarget({
    targetType: typeof route.query.targetType === 'string' ? route.query.targetType : null,
    assistantId: typeof route.query.assistantId === 'string' ? route.query.assistantId : null,
    graphId: typeof route.query.graphId === 'string' ? route.query.graphId : null
  })
)

const savedTarget = computed(() => {
  const projectId = workspaceStore.currentProjectId
  if (!projectId || explicitTarget.value) {
    return null
  }
  return readRecentChatTarget(projectId)
})

const activeTarget = computed(() => explicitTarget.value || savedTarget.value)
const targetSource = computed(() => (explicitTarget.value ? 'query' : savedTarget.value ? 'recent' : 'none'))
const threadId = computed(() =>
  typeof route.query.threadId === 'string' && route.query.threadId.trim() ? route.query.threadId.trim() : ''
)

watchEffect(() => {
  if (explicitTarget.value && workspaceStore.currentProjectId) {
    writeRecentChatTarget(workspaceStore.currentProjectId, explicitTarget.value)
  }
})

const stats = computed(() => [
  {
    label: '当前项目',
    value: workspaceStore.currentProject?.name || '未选择',
    hint: '聊天目标总是绑定到当前工作区项目',
    icon: 'project',
    tone: 'primary'
  },
  {
    label: '目标类型',
    value: activeTarget.value?.targetType || '未设置',
    hint: activeTarget.value ? `来源：${targetSource.value}` : '首次进入时需要先选 assistant 或 graph',
    icon: 'chat',
    tone: 'success'
  },
  {
    label: '目标 ID',
    value: activeTarget.value?.graphId || activeTarget.value?.assistantId || '--',
    hint: threadId.value ? `附带 threadId：${threadId.value}` : '当前没有 thread 上下文',
    icon: 'assistant',
    tone: 'warning'
  }
])

function clearTarget() {
  if (!workspaceStore.currentProjectId) {
    return
  }
  clearRecentChatTarget(workspaceStore.currentProjectId)
  window.location.href = '/workspace/chat'
}
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Chat"
      title="Agent Chat"
      description="聊天工作区先把目标选择和最近目标复用这条链路稳定下来。首次进入时引导用户先去选目标，之后默认复用当前项目最近一次使用的 assistant 或 graph。"
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

    <EmptyState
      v-if="!workspaceStore.currentProject"
      icon="project"
      title="请先选择项目"
      description="Chat 是项目级工作区。没有项目上下文，assistant、graph、thread 这些目标都不成立。"
    />

    <div
      v-else-if="!activeTarget"
      class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_360px]"
    >
      <SurfaceCard class="space-y-5">
        <div class="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
          <BaseIcon
            name="chat"
            size="sm"
            class="text-primary-500"
          />
          首次进入引导
        </div>
        <p class="text-sm leading-7 text-gray-500 dark:text-dark-300">
          当前项目还没有保存最近聊天目标。先去 Assistants 或 Graphs 里选一个真正要对话的目标，再回到这里。后面再打开 Chat，就不会再看到这块引导页了。
        </p>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="pw-card-glass p-4">
            <div class="text-sm font-semibold text-gray-900 dark:text-white">
              从 Assistants 进入
            </div>
            <p class="mt-2 text-sm leading-7 text-gray-500 dark:text-dark-300">
              当你已经确认具体 assistant，需要按 assistant_id 固定聊天目标时，优先从这里进入。
            </p>
            <div class="mt-4">
              <router-link
                class="pw-btn pw-btn-secondary"
                to="/workspace/assistants"
              >
                去选 Assistant
              </router-link>
            </div>
          </div>
          <div class="pw-card-glass p-4">
            <div class="text-sm font-semibold text-gray-900 dark:text-white">
              从 Graphs 进入
            </div>
            <p class="mt-2 text-sm leading-7 text-gray-500 dark:text-dark-300">
              当你要调固定 graph，例如 `sql_agent` 或业务图谱目录里的某个 graph，优先从这里进入。
            </p>
            <div class="mt-4">
              <router-link
                class="pw-btn pw-btn-secondary"
                to="/workspace/graphs"
              >
                去选 Graph
              </router-link>
            </div>
          </div>
        </div>
      </SurfaceCard>

      <SurfaceCard class="space-y-4">
        <div class="pw-page-eyebrow">
          Shortcuts
        </div>
        <div class="space-y-3 text-sm leading-7 text-gray-500 dark:text-dark-300">
          <p>如果你要走固定 SQL 问答流程，可以直接去 SQL Agent，它会把 `sql_agent` 预绑定为聊天目标。</p>
          <p>如果你是做 testcase AI 对话生成，后面会在 Testcase 的 generate 子页里绑定 `test_case_agent`。</p>
        </div>
      </SurfaceCard>
    </div>

    <div
      v-else
      class="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_360px]"
    >
      <SurfaceCard class="space-y-5">
        <div class="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
          <BaseIcon
            name="chat"
            size="sm"
            class="text-primary-500"
          />
          当前聊天目标
        </div>
        <div class="pw-card-glass p-4">
          <div class="text-xs font-semibold uppercase tracking-[0.14em] text-gray-400 dark:text-dark-400">
            Target
          </div>
          <div class="mt-2 text-lg font-semibold text-gray-950 dark:text-white">
            {{ activeTarget.targetType === 'graph' ? 'Graph' : 'Assistant' }}
          </div>
          <div class="mt-2 break-all text-sm text-gray-500 dark:text-dark-300">
            {{ activeTarget.graphId || activeTarget.assistantId }}
          </div>
          <div class="mt-2 text-xs text-gray-400 dark:text-dark-400">
            来源：{{ targetSource }}{{ threadId ? ` · threadId=${threadId}` : '' }}
          </div>
        </div>

        <StateBanner
          title="目标复用已生效"
          description="这次打开 Chat 已经不再显示首次引导，而是直接复用当前项目最近一次使用的目标。后续真实对话画布迁入时，会直接消费这份目标配置。"
          variant="success"
        />

        <div class="flex flex-wrap gap-3">
          <router-link
            class="pw-btn pw-btn-secondary"
            :to="activeTarget.targetType === 'graph' ? '/workspace/graphs' : '/workspace/assistants'"
          >
            切换目标来源
          </router-link>
          <button
            type="button"
            class="pw-btn pw-btn-ghost"
            @click="clearTarget"
          >
            清空最近目标
          </button>
        </div>
      </SurfaceCard>

      <SurfaceCard class="space-y-4">
        <div class="pw-page-eyebrow">
          Notes
        </div>
        <div class="space-y-3 text-sm leading-7 text-gray-500 dark:text-dark-300">
          <p>显式 query 参数优先级高于本地保存的最近目标。</p>
          <p>只要带着目标进入一次，当前项目下后续再次打开 Chat 就会直接复用。</p>
          <p>当需要彻底换方向时，去目标来源页重新选择，或者直接清空最近目标。</p>
        </div>
      </SurfaceCard>
    </div>
  </section>
</template>
