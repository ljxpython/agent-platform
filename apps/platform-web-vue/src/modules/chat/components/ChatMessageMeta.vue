<script setup lang="ts">
import type { Message } from '@langchain/langgraph-sdk'
import { computed, ref, watch } from 'vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import { getMessageText } from '@/utils/chat-content'
import { toPrettyJson } from '@/utils/threads'

type ToolCallResultMap = Record<string, Message>

type SubAgentCard = {
  id: string
  name: string
  status: 'pending' | 'completed'
  input: string
  output?: string
}

const props = defineProps<{
  message: Message
  allMessages: Message[]
  defaultExpanded?: boolean
}>()

const toolOpenMap = ref<Record<string, boolean>>({})
const subAgentOpenMap = ref<Record<string, boolean>>({})

function normalizeToolArgs(args: unknown): Record<string, unknown> {
  if (args && typeof args === 'object' && !Array.isArray(args)) {
    return args as Record<string, unknown>
  }

  if (typeof args === 'string') {
    try {
      const parsed = JSON.parse(args)
      if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
        return parsed as Record<string, unknown>
      }
    } catch {
      // ignore parse failure
    }

    return {
      input: args
    }
  }

  return {}
}

function normalizeToolCallInput(args: unknown): string {
  if (args == null) {
    return ''
  }
  if (typeof args === 'string') {
    return args
  }
  if (typeof args === 'object') {
    const record = args as Record<string, unknown>
    const task =
      typeof record.task === 'string'
        ? record.task
        : typeof record.description === 'string'
          ? record.description
          : ''
    if (task.trim()) {
      return task
    }
    return toPrettyJson(record)
  }
  return String(args)
}

function getSubAgentName(args: unknown): string {
  if (!args || typeof args !== 'object') {
    return 'sub-agent'
  }

  const record = args as Record<string, unknown>
  return typeof record.subagent_type === 'string' && record.subagent_type.trim()
    ? record.subagent_type.trim()
    : 'sub-agent'
}

const toolResultsByCallId = computed<ToolCallResultMap>(() => {
  return props.allMessages.reduce<ToolCallResultMap>((result, item) => {
    if (item.type === 'tool' && typeof item.tool_call_id === 'string' && item.tool_call_id.trim()) {
      result[item.tool_call_id] = item
    }
    return result
  }, {})
})

const visibleToolCalls = computed(() => {
  if (props.message.type !== 'ai' || !Array.isArray(props.message.tool_calls)) {
    return []
  }

  return props.message.tool_calls.filter((item) => item && item.name !== 'task')
})

const subAgentCards = computed<SubAgentCard[]>(() => {
  if (props.message.type !== 'ai' || !Array.isArray(props.message.tool_calls)) {
    return []
  }

  return props.message.tool_calls
    .filter((item) => item?.name === 'task')
    .map((toolCall, index) => {
      const id =
        typeof toolCall.id === 'string' && toolCall.id.trim()
          ? toolCall.id
          : `task-${props.message.id || 'message'}-${index + 1}`
      const toolResult = toolCall.id ? toolResultsByCallId.value[toolCall.id] : undefined
      const output = toolResult ? getMessageText(toolResult.content) : ''

      return {
        id,
        name: getSubAgentName(toolCall.args),
        status: toolResult ? 'completed' : 'pending',
        input: normalizeToolCallInput(toolCall.args),
        output: output || undefined
      }
    })
})

watch(
  () => props.message.id,
  () => {
    toolOpenMap.value = {}
    subAgentOpenMap.value = {}
  },
  { immediate: true }
)
</script>

<template>
  <div
    v-if="visibleToolCalls.length > 0 || subAgentCards.length > 0"
    class="mt-4 space-y-3"
  >
    <div
      v-if="visibleToolCalls.length > 0"
      class="space-y-2"
    >
      <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
        Tool Calls
      </div>

      <div
        v-for="(toolCall, index) in visibleToolCalls"
        :key="toolCall.id || `${toolCall.name}-${index}`"
        class="overflow-hidden rounded-2xl border border-slate-200/80 bg-slate-50/80 dark:border-dark-700 dark:bg-dark-800/70"
      >
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 px-3 py-3 text-left transition hover:bg-white/70 dark:hover:bg-dark-700/70"
          @click="toolOpenMap[toolCall.id || `${toolCall.name}-${index}`] = !(toolOpenMap[toolCall.id || `${toolCall.name}-${index}`] ?? defaultExpanded ?? true)"
        >
          <div class="flex min-w-0 items-center gap-3">
            <span
              class="inline-flex h-2.5 w-2.5 rounded-full"
              :class="
                toolCall.id && toolResultsByCallId[toolCall.id]
                  ? 'bg-emerald-500'
                  : 'animate-pulse bg-sky-500'
              "
            />
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {{ toolCall.name || 'Unknown Tool' }}
              </div>
              <div class="mt-1 text-xs text-slate-500 dark:text-dark-300">
                {{ toolCall.id || `tool-${index + 1}` }}
              </div>
            </div>
          </div>

          <BaseIcon
            :name="toolOpenMap[toolCall.id || `${toolCall.name}-${index}`] ?? defaultExpanded ?? true ? 'chevron-down' : 'chevron-right'"
            size="sm"
            class="shrink-0 text-slate-400"
          />
        </button>

        <div
          v-if="toolOpenMap[toolCall.id || `${toolCall.name}-${index}`] ?? defaultExpanded ?? true"
          class="border-t border-slate-200/80 px-3 py-3 dark:border-dark-700"
        >
          <div
            v-if="Object.keys(normalizeToolArgs(toolCall.args)).length > 0"
            class="space-y-2"
          >
            <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
              Args
            </div>
            <div class="space-y-2">
              <div
                v-for="(value, key) in normalizeToolArgs(toolCall.args)"
                :key="key"
                class="rounded-2xl bg-white px-3 py-3 dark:bg-dark-900/80"
              >
                <div class="text-xs font-semibold text-slate-900 dark:text-white">
                  {{ key }}
                </div>
                <pre class="mt-2 overflow-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-600 dark:text-dark-100">{{ typeof value === 'string' ? value : toPrettyJson(value) }}</pre>
              </div>
            </div>
          </div>

          <div
            v-if="toolCall.id && toolResultsByCallId[toolCall.id]"
            class="mt-3 space-y-2"
          >
            <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
              Result
            </div>
            <pre class="overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-white px-3 py-3 text-xs leading-6 text-slate-600 dark:bg-dark-900/80 dark:text-dark-100">{{ getMessageText(toolResultsByCallId[toolCall.id].content) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="subAgentCards.length > 0"
      class="space-y-2"
    >
      <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
        Sub Agents
      </div>

      <div
        v-for="item in subAgentCards"
        :key="item.id"
        class="overflow-hidden rounded-2xl border border-slate-200/80 bg-slate-50/80 dark:border-dark-700 dark:bg-dark-800/70"
      >
        <button
          type="button"
          class="flex w-full items-center justify-between gap-3 px-3 py-3 text-left transition hover:bg-white/70 dark:hover:bg-dark-700/70"
          @click="subAgentOpenMap[item.id] = !(subAgentOpenMap[item.id] ?? false)"
        >
          <div class="flex min-w-0 items-center gap-3">
            <span
              class="inline-flex h-2.5 w-2.5 rounded-full"
              :class="item.status === 'completed' ? 'bg-emerald-500' : 'animate-pulse bg-amber-400'"
            />
            <div class="min-w-0">
              <div class="truncate text-sm font-semibold text-slate-900 dark:text-white">
                {{ item.name }}
              </div>
              <div class="mt-1 text-xs text-slate-500 dark:text-dark-300">
                {{ item.status === 'completed' ? 'completed' : 'running' }}
              </div>
            </div>
          </div>

          <BaseIcon
            :name="subAgentOpenMap[item.id] ? 'chevron-down' : 'chevron-right'"
            size="sm"
            class="shrink-0 text-slate-400"
          />
        </button>

        <div
          v-if="subAgentOpenMap[item.id]"
          class="space-y-3 border-t border-slate-200/80 px-3 py-3 dark:border-dark-700"
        >
          <div>
            <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
              Input
            </div>
            <pre class="mt-2 overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-white px-3 py-3 text-xs leading-6 text-slate-600 dark:bg-dark-900/80 dark:text-dark-100">{{ item.input || '<empty>' }}</pre>
          </div>

          <div v-if="item.output">
            <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
              Output
            </div>
            <pre class="mt-2 overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-white px-3 py-3 text-xs leading-6 text-slate-600 dark:bg-dark-900/80 dark:text-dark-100">{{ item.output }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
