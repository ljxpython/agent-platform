<script setup lang="ts">
import type { Message } from '@langchain/langgraph-sdk'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import type { LocationQueryRaw } from 'vue-router'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseDrawer from '@/components/base/BaseDrawer.vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import MarkdownContent from '@/components/platform/MarkdownContent.vue'
import EmptyState from '@/components/platform/EmptyState.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import { useUiStore } from '@/stores/ui'
import { useWorkspaceStore } from '@/stores/workspace'
import { CHAT_ATTACHMENT_ACCEPT } from '@/utils/chat-content'
import { copyText } from '@/utils/clipboard'
import { shortId } from '@/utils/format'
import {
  getHistoryEntryId,
  getHistoryEntryTime,
  getMessageAttachments,
  getMessageText,
  toPrettyJson
} from '@/utils/threads'
import ChatAttachmentPreview from './ChatAttachmentPreview.vue'
import ChatArtifactPanel from './ChatArtifactPanel.vue'
import ChatInterruptPanel from './ChatInterruptPanel.vue'
import ChatMessageMeta from './ChatMessageMeta.vue'
import ChatTasksFilesPanel from './ChatTasksFilesPanel.vue'
import { getChatMessageIdentifier } from '../branching'
import { useChatAttachments } from '../composables/useChatAttachments'
import { useChatWorkspace } from '../composables/useChatWorkspace'
import type { ChatResolvedTarget, ChatWorkspaceDisplay, ChatWorkspaceFeatures } from '../types'

const props = withDefaults(
  defineProps<{
    target: ChatResolvedTarget | null
    display: ChatWorkspaceDisplay
    features?: ChatWorkspaceFeatures
    initialThreadId?: string
    sourceNote?: string
    contextNotice?: string
    allowResetTarget?: boolean
  }>(),
  {
    features: () => ({}),
    initialThreadId: '',
    sourceNote: '',
    contextNotice: '',
    allowResetTarget: false
  }
)

const emit = defineEmits<{
  'reset-target': []
}>()

const route = useRoute()
const router = useRouter()
const uiStore = useUiStore()
const workspaceStore = useWorkspaceStore()

const composerInput = ref('')
const threadSearch = ref('')
const threadStatusFilter = ref<'all' | 'idle' | 'busy' | 'interrupted' | 'error'>('all')
const threadsDrawerOpen = ref(false)
const contextDrawerOpen = ref(false)
const messagesViewport = ref<HTMLDivElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const sourceNoteDismissed = ref(false)
const deletingThreadId = ref('')
const editingMessageId = ref('')
const editingMessageValue = ref('')
const draftRunOptions = reactive({
  modelId: '',
  enableTools: false,
  toolNames: [] as string[],
  temperature: '',
  maxTokens: '',
  debugMode: false
})

const workspace = useChatWorkspace({
  projectId: computed(() => workspaceStore.currentProjectId || ''),
  target: computed(() => props.target),
  initialThreadId: computed(() => props.initialThreadId?.trim() || '')
})
const attachmentState = useChatAttachments()

const currentProject = computed(() => workspaceStore.currentProject)
const renderMessages = computed(() => workspace.messages.value)
const displayMessages = computed(() => {
  const linkedToolCallIds = new Set<string>()

  for (const message of renderMessages.value) {
    if (message.type !== 'ai' || !Array.isArray(message.tool_calls)) {
      continue
    }

    for (const toolCall of message.tool_calls) {
      if (typeof toolCall?.id === 'string' && toolCall.id.trim()) {
        linkedToolCallIds.add(toolCall.id)
      }
    }
  }

  return renderMessages.value.filter((message) => {
    if (message.type !== 'tool') {
      return true
    }

    return !(typeof message.tool_call_id === 'string' && linkedToolCallIds.has(message.tool_call_id))
  })
})
const composerAttachments = computed(() => attachmentState.attachments.value)
const allowRunOptions = computed(() => props.features?.allowRunOptions ?? true)
const showHistory = computed(() => props.features?.showHistory ?? true)
const showArtifacts = computed(() => props.features?.showArtifacts ?? true)
const showContextBar = computed(() => props.features?.showContextBar ?? true)
const hasArtifactEntries = computed(() => {
  const rawEntries = workspace.displayState.value?.ui
  return Array.isArray(rawEntries) && rawEntries.length > 0
})
const hasComposerContent = computed(
  () => Boolean(composerInput.value.trim()) || composerAttachments.value.length > 0
)
const showContinueAction = computed(
  () => !workspace.sending.value && workspace.canContinueDebug.value
)
const hasBlockingInterrupt = computed(
  () => workspace.interruptPayload.value !== undefined && !workspace.canContinueDebug.value
)
const canSendFreshMessage = computed(
  () =>
    workspace.canSend.value &&
    !showContinueAction.value &&
    !hasBlockingInterrupt.value &&
    hasComposerContent.value
)
const sendButtonLabel = computed(() => (workspace.runOptions.debugMode ? 'Step' : '发送消息'))
const debugStatusDescription = computed(() => {
  if (!workspace.canContinueDebug.value) {
    return ''
  }

  const payload = workspace.interruptPayload.value
  if (!payload) {
    return '当前运行已在断点暂停，可以继续后续执行。'
  }

  return `当前运行已在断点暂停：${toPrettyJson(payload)}`
})

const selectedToolsLabel = computed(() => {
  if (!draftRunOptions.enableTools) {
    return '已关闭'
  }
  if (draftRunOptions.toolNames.length === 0) {
    return '全部按默认策略'
  }
  return `${draftRunOptions.toolNames.length} 个工具`
})

const headerPills = computed(() => [
  {
    label: 'Target',
    value: workspace.targetText.value
  },
  {
    label: 'Thread',
    value: workspace.activeThreadId.value ? shortId(workspace.activeThreadId.value) : '未创建'
  }
])

const threadStatusFilters = [
  { value: 'all', label: '全部' },
  { value: 'interrupted', label: '待处理' },
  { value: 'busy', label: '运行中' },
  { value: 'idle', label: '空闲' },
  { value: 'error', label: '异常' }
] as const

function calcDayDiff(rawValue: string) {
  const value = rawValue.trim()
  if (!value || value === '--') {
    return Number.POSITIVE_INFINITY
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return Number.POSITIVE_INFINITY
  }

  const now = new Date()
  const nowAtMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const dateAtMidnight = new Date(date.getFullYear(), date.getMonth(), date.getDate())
  return Math.floor((nowAtMidnight.getTime() - dateAtMidnight.getTime()) / (1000 * 60 * 60 * 24))
}

function threadGroupKey(item: { status: string; updatedAt: string }) {
  if (item.status === 'interrupted') {
    return 'interrupted'
  }

  const dayDiff = calcDayDiff(item.updatedAt)
  if (dayDiff <= 0) {
    return 'today'
  }
  if (dayDiff === 1) {
    return 'yesterday'
  }
  if (dayDiff < 7) {
    return 'week'
  }
  return 'older'
}

const threadGroupLabels: Record<string, string> = {
  interrupted: '待处理',
  today: '今天',
  yesterday: '昨天',
  week: '最近一周',
  older: '更早'
}

const filteredThreadSummary = computed(() => {
  const normalizedQuery = threadSearch.value.trim().toLowerCase()
  const normalizedStatus = threadStatusFilter.value

  const items = workspace.threadSummary.value.filter((item) => {
    const matchesStatus = normalizedStatus === 'all' ? true : item.status === normalizedStatus
    const matchesQuery = [item.title, item.preview, item.time, item.status]
      .join(' ')
      .toLowerCase()
      .includes(normalizedQuery)

    return matchesStatus && matchesQuery
  })

  return items
})

const groupedThreadSummary = computed(() => {
  const groups: Array<{ key: string; label: string; items: typeof filteredThreadSummary.value }> = []
  const order = ['interrupted', 'today', 'yesterday', 'week', 'older']

  for (const key of order) {
    const items = filteredThreadSummary.value.filter((item) => threadGroupKey(item) === key)
    if (items.length > 0) {
      groups.push({
        key,
        label: threadGroupLabels[key] || key,
        items
      })
    }
  }

  return groups
})

function syncThreadIdToRoute(threadId: string) {
  const nextQuery: LocationQueryRaw = { ...route.query }

  if (threadId.trim()) {
    nextQuery.threadId = threadId.trim()
  } else {
    delete nextQuery.threadId
  }

  void router.replace({
    path: route.path,
    query: nextQuery
  })
}

watch(
  () => workspace.activeThreadId.value,
  (threadId) => {
    syncThreadIdToRoute(threadId || '')
  }
)

watch(
  () => props.sourceNote,
  () => {
    sourceNoteDismissed.value = false
  }
)

watch(
  () => displayMessages.value.length,
  async () => {
    await nextTick()
    if (messagesViewport.value) {
      messagesViewport.value.scrollTop = messagesViewport.value.scrollHeight
    }
  }
)

watch(
  () => workspace.activeThreadId.value,
  () => {
    editingMessageId.value = ''
    editingMessageValue.value = ''
    deletingThreadId.value = ''
  }
)

function getMessageId(message: Message, index: number) {
  return getChatMessageIdentifier(message, index)
}

function getMessageMeta(message: Message, index: number) {
  return workspace.messageMetadataById.value[getMessageId(message, index)]
}

function getMessageBranchIndex(message: Message, index: number) {
  const meta = getMessageMeta(message, index)
  if (!meta?.branchOptions?.length) {
    return -1
  }
  return meta.branchOptions.indexOf(meta.branch || '')
}

function hasBranchSwitcher(message: Message, index: number) {
  return (getMessageMeta(message, index)?.branchOptions?.length || 0) > 1
}

function selectPreviousMessageBranch(message: Message, index: number) {
  const meta = getMessageMeta(message, index)
  const branchIndex = getMessageBranchIndex(message, index)
  if (!meta?.branchOptions || branchIndex <= 0) {
    return
  }

  workspace.selectBranch(meta.branchOptions[branchIndex - 1] || '')
}

function selectNextMessageBranch(message: Message, index: number) {
  const meta = getMessageMeta(message, index)
  const branchIndex = getMessageBranchIndex(message, index)
  if (!meta?.branchOptions || branchIndex < 0 || branchIndex >= meta.branchOptions.length - 1) {
    return
  }

  workspace.selectBranch(meta.branchOptions[branchIndex + 1] || '')
}

function canEditMessage(message: Message, index: number) {
  const meta = getMessageMeta(message, index)
  return (
    message.type === 'human' &&
    !workspace.sending.value &&
    !hasBlockingInterrupt.value &&
    Boolean(meta?.parentCheckpoint?.checkpoint_id?.trim())
  )
}

function canRetryMessage(message: Message, index: number) {
  const meta = getMessageMeta(message, index)
  return (
    message.type === 'ai' &&
    !workspace.sending.value &&
    !hasBlockingInterrupt.value &&
    Boolean(meta?.parentCheckpoint?.checkpoint_id?.trim())
  )
}

function buildEditedMessageContent(message: Message, nextText: string): Message['content'] {
  const normalizedText = nextText.trim()

  if (Array.isArray(message.content)) {
    const attachments = getMessageAttachments(message.content)
    return normalizedText
      ? ([{ type: 'text', text: normalizedText }, ...attachments] as Message['content'])
      : (attachments as unknown as Message['content'])
  }

  return normalizedText
}

async function handleCopyMessage(message: Message) {
  const text = getMessageText(message.content).trim()
  if (!text) {
    uiStore.pushToast({
      type: 'warning',
      title: '没有可复制的文本',
      message: '当前消息主要是附件或结构化数据。'
    })
    return
  }

  const copied = await copyText(text)
  uiStore.pushToast({
    type: copied ? 'success' : 'error',
    title: copied ? '消息已复制' : '复制失败',
    message: copied ? '已写入系统剪贴板。' : '浏览器拒绝了复制动作。'
  })
}

function startEditMessage(message: Message, index: number) {
  if (!canEditMessage(message, index)) {
    return
  }

  editingMessageId.value = getMessageId(message, index)
  editingMessageValue.value = getMessageText(message.content)
}

function cancelEditMessage() {
  editingMessageId.value = ''
  editingMessageValue.value = ''
}

async function submitEditMessage(message: Message, index: number) {
  const messageId = getMessageId(message, index)
  if (editingMessageId.value !== messageId) {
    return
  }

  const nextContent = buildEditedMessageContent(message, editingMessageValue.value)
  const hasText = getMessageText(nextContent).trim().length > 0
  const hasAttachments = Array.isArray(nextContent) && getMessageAttachments(nextContent).length > 0

  if (!hasText && !hasAttachments) {
    uiStore.pushToast({
      type: 'warning',
      title: '消息内容不能为空',
      message: '至少保留一段文本或者附件。'
    })
    return
  }

  const updated = await workspace.editHumanMessage(messageId, nextContent)
  if (updated) {
    cancelEditMessage()
    uiStore.pushToast({
      type: 'success',
      title: '已基于历史节点重发消息',
      message: '新的分支回复已经开始生成。'
    })
  }
}

async function handleRetryMessage(message: Message, index: number) {
  const retried = await workspace.retryMessage(getMessageId(message, index))
  if (retried) {
    uiStore.pushToast({
      type: 'success',
      title: '已重新生成回复',
      message: '当前回复会从对应 checkpoint 重新执行。'
    })
  }
}

async function handleDeleteThread(threadId: string) {
  if (!threadId.trim() || deletingThreadId.value) {
    return
  }

  const confirmed =
    typeof window === 'undefined'
      ? true
      : window.confirm('删除这个会话后无法恢复，确认继续吗？')

  if (!confirmed) {
    return
  }

  deletingThreadId.value = threadId
  try {
    await workspace.deleteThread(threadId)
    uiStore.pushToast({
      type: 'success',
      title: '会话已删除',
      message: threadId
    })
  } catch (error) {
    uiStore.pushToast({
      type: 'error',
      title: '删除失败',
      message: error instanceof Error ? error.message : '线程删除失败'
    })
  } finally {
    deletingThreadId.value = ''
  }
}

function messageRoleLabel(message: Message) {
  if (message.type === 'human') {
    return '你'
  }
  if (message.type === 'tool') {
    return 'Tool'
  }
  if (message.type === 'system') {
    return 'System'
  }
  return 'Agent'
}

function messageBubbleClass(message: Message) {
  if (message.type === 'human') {
    return 'border-primary-200 bg-primary-50/90 text-primary-950 dark:border-primary-900/40 dark:bg-primary-950/30 dark:text-primary-50'
  }
  if (message.type === 'tool') {
    return 'border-amber-200 bg-amber-50/90 text-amber-950 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-50'
  }
  if (message.type === 'system') {
    return 'border-gray-200 bg-gray-50 text-gray-800 dark:border-dark-700 dark:bg-dark-900/70 dark:text-gray-200'
  }
  return 'border-white/70 bg-white/95 text-gray-900 dark:border-dark-700 dark:bg-dark-900/85 dark:text-white'
}

function messageWrapClass(message: Message) {
  return message.type === 'human' ? 'items-end' : 'items-start'
}

async function handleSend() {
  const sent = await workspace.sendMessage(composerInput.value, composerAttachments.value)
  if (sent) {
    composerInput.value = ''
    attachmentState.resetAttachments()
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

function handleComposerKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    void handleSend()
  }
}

function handleComposerPaste(event: ClipboardEvent) {
  void attachmentState.handlePaste(event)
}

function openFilePicker() {
  fileInputRef.value?.click()
}

async function handleSelectThread(threadId: string) {
  await workspace.selectThread(threadId)
  threadsDrawerOpen.value = false
}

function handleResetTarget() {
  emit('reset-target')
  contextDrawerOpen.value = false
}

function syncDraftRunOptions() {
  draftRunOptions.modelId = workspace.runOptions.modelId
  draftRunOptions.enableTools = workspace.runOptions.enableTools
  draftRunOptions.toolNames = [...workspace.runOptions.toolNames]
  draftRunOptions.temperature = workspace.runOptions.temperature
  draftRunOptions.maxTokens = workspace.runOptions.maxTokens
  draftRunOptions.debugMode = workspace.runOptions.debugMode
}

function openContextDrawer() {
  syncDraftRunOptions()
  contextDrawerOpen.value = true
}

function toggleDraftTool(toolKey: string) {
  const normalizedToolKey = toolKey.trim()
  if (!normalizedToolKey) {
    return
  }

  const exists = draftRunOptions.toolNames.includes(normalizedToolKey)
  draftRunOptions.toolNames = exists
    ? draftRunOptions.toolNames.filter((item) => item !== normalizedToolKey)
    : [...draftRunOptions.toolNames, normalizedToolKey]
}

function restoreDraftRunOptions() {
  syncDraftRunOptions()
}

function applyDraftRunOptions() {
  workspace.runOptions.modelId = draftRunOptions.modelId
  workspace.runOptions.enableTools = draftRunOptions.enableTools
  workspace.runOptions.toolNames = [...draftRunOptions.toolNames]
  workspace.runOptions.temperature = draftRunOptions.temperature
  workspace.runOptions.maxTokens = draftRunOptions.maxTokens
  workspace.runOptions.debugMode = draftRunOptions.debugMode
  contextDrawerOpen.value = false
}

async function handleContinue() {
  await workspace.continueDebugRun()
}

async function handleCancelRun() {
  await workspace.cancelActiveRun()
}
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      :eyebrow="props.target?.targetType === 'graph' ? 'Graph Chat' : 'Assistant Chat'"
      :title="display.title"
      :description="display.description"
    />

    <div
      v-if="sourceNote && !sourceNoteDismissed"
      class="relative"
    >
      <StateBanner
        title="目标来源"
        :description="sourceNote"
        variant="info"
      />
      <button
        type="button"
        class="absolute right-3 top-3 rounded-xl p-2 text-gray-400 transition hover:bg-white/80 hover:text-gray-700 dark:hover:bg-dark-900/80 dark:hover:text-dark-100"
        aria-label="关闭目标来源提示"
        @click="sourceNoteDismissed = true"
      >
        <BaseIcon
          name="x"
          size="sm"
        />
      </button>
    </div>

    <StateBanner
      v-if="contextNotice"
      title="上下文说明"
      :description="contextNotice"
      variant="success"
    />

    <StateBanner
      v-if="workspace.error.value"
      title="聊天线程加载失败"
      :description="workspace.error.value"
      variant="danger"
    />

    <StateBanner
      v-if="workspace.detailError.value"
      title="当前对话运行失败"
      :description="workspace.detailError.value"
      variant="danger"
    />

    <StateBanner
      v-if="workspace.runtimeError.value"
      title="运行时目录加载失败"
      :description="workspace.runtimeError.value"
      variant="warning"
    />

    <StateBanner
      v-if="debugStatusDescription"
      title="Debug 已暂停"
      :description="debugStatusDescription"
      variant="info"
    />

    <StateBanner
      v-if="hasBlockingInterrupt"
      title="等待人工决策"
      description="当前运行进入 interrupt 状态。先处理下面的中断面板，再继续和 agent 交互。"
      variant="warning"
    />

    <StateBanner
      v-if="workspace.isViewingBranch.value"
      title="当前正在查看历史分支"
      description="你现在看到的是某个 checkpoint 分支下的消息快照。继续发送、编辑或重试时，会基于这个分支重新生成新的对话路径。"
      variant="info"
    />

    <EmptyState
      v-if="!currentProject"
      icon="project"
      title="请先选择项目"
      description="Chat 是严格的项目级工作区。没有项目上下文，线程、图谱和助手这些东西全都不成立。"
    />

    <EmptyState
      v-else-if="!target"
      icon="chat"
      title="请先选择聊天目标"
      description="当前页已经是聊天工作台，但没有明确 assistant 或 graph，先从入口页选一个真实目标再进来。"
    />

    <SurfaceCard
      v-else
      class="flex min-h-[720px] flex-col overflow-hidden p-0"
    >
      <div class="border-b border-gray-100 px-6 py-5 dark:border-dark-800">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div class="min-w-0">
            <div class="text-lg font-semibold text-gray-900 dark:text-white">
              {{ workspace.selectedThreadSummary.value?.title || display.emptyTitle || '开始一个新对话' }}
            </div>
            <div class="mt-2 text-sm leading-7 text-gray-500 dark:text-dark-300">
              {{
                workspace.selectedThreadSummary.value?.preview ||
                  display.emptyDescription ||
                  '选择历史 thread 或直接发第一条消息，消息画布会在这里持续复用。'
              }}
            </div>

            <div
              v-if="showContextBar"
              class="mt-4 flex flex-wrap gap-2"
            >
              <span
                v-for="pill in headerPills"
                :key="pill.label"
                class="pw-pill"
              >
                <span class="text-gray-400 dark:text-dark-400">{{ pill.label }}</span>
                <span class="max-w-[220px] truncate text-gray-700 dark:text-white">{{ pill.value }}</span>
              </span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <BaseButton
              variant="secondary"
              @click="threadsDrawerOpen = true"
            >
              <BaseIcon
                name="threads"
                size="sm"
              />
              会话 {{ workspace.threadItems.value.length }}
            </BaseButton>
            <BaseButton
              variant="secondary"
              @click="openContextDrawer"
            >
              <BaseIcon
                name="runtime"
                size="sm"
              />
              运行上下文
            </BaseButton>
            <BaseButton
              variant="secondary"
              :disabled="workspace.loadingThreads.value || workspace.loadingThreadDetail.value"
              @click="workspace.refreshActiveThread"
            >
              <BaseIcon
                name="refresh"
                size="sm"
              />
              刷新
            </BaseButton>
            <BaseButton
              :disabled="!workspace.canStartThread.value"
              @click="workspace.startNewThread"
            >
              <BaseIcon
                name="chat"
                size="sm"
              />
              新对话
            </BaseButton>
          </div>
        </div>
      </div>

      <div
        class="min-h-0 flex-1 overflow-hidden"
        :class="showArtifacts && hasArtifactEntries ? 'lg:grid lg:grid-cols-[minmax(0,1fr)_360px]' : ''"
      >
        <div
          ref="messagesViewport"
          class="min-h-0 overflow-y-auto px-6 py-5"
        >
          <div
            v-if="workspace.loadingThreadDetail.value && renderMessages.length === 0"
            class="space-y-4"
          >
            <div
              v-for="index in 3"
              :key="index"
              class="pw-card-glass h-28 animate-pulse"
            />
          </div>

          <div
            v-else-if="displayMessages.length === 0"
            class="flex h-full items-center justify-center"
          >
            <EmptyState
              icon="chat"
              :title="display.emptyTitle || '从这里开始第一轮对话'"
              :description="display.emptyDescription || '输入框已经可用。发出第一条消息时会自动创建 thread，并把后续历史沉淀到当前项目。'"
            />
          </div>

          <div
            v-else
            class="space-y-5"
          >
            <div
              v-for="(message, index) in displayMessages"
              :key="getMessageId(message, index)"
              class="flex flex-col gap-2"
              :class="messageWrapClass(message)"
            >
              <div class="text-xs font-semibold uppercase tracking-[0.14em] text-gray-400 dark:text-dark-400">
                {{ messageRoleLabel(message) }}
              </div>
              <div
                class="max-w-[88%] rounded-[24px] border px-4 py-3 shadow-soft"
                :class="messageBubbleClass(message)"
              >
                <div
                  v-if="getMessageAttachments(message.content).length > 0"
                  class="flex flex-wrap gap-3"
                  :class="message.type === 'human' ? 'justify-end' : ''"
                >
                  <ChatAttachmentPreview
                    v-for="(attachment, attachmentIndex) in getMessageAttachments(message.content)"
                    :key="`${message.id || message.type}-attachment-${attachmentIndex}`"
                    :block="attachment"
                    compact
                  />
                </div>
                <textarea
                  v-if="editingMessageId === getMessageId(message, index)"
                  v-model="editingMessageValue"
                  rows="5"
                  class="pw-input resize-y border-0 bg-transparent px-0 py-0 text-sm leading-7 shadow-none focus:ring-0"
                  :class="getMessageAttachments(message.content).length > 0 ? 'mt-3' : ''"
                />
                <pre
                  v-else-if="message.type !== 'ai' && getMessageText(message.content)"
                  class="whitespace-pre-wrap break-words text-sm leading-7"
                  :class="getMessageAttachments(message.content).length > 0 ? 'mt-3' : ''"
                >{{ getMessageText(message.content) }}</pre>
                <MarkdownContent
                  v-else-if="getMessageText(message.content)"
                  :content="getMessageText(message.content)"
                  :class="getMessageAttachments(message.content).length > 0 ? 'mt-3' : ''"
                />
                <div
                  v-else-if="getMessageAttachments(message.content).length === 0"
                  class="text-sm leading-7 text-gray-500 dark:text-dark-300"
                >
                  当前消息没有可渲染的文本内容。
                </div>
                <div
                  v-if="message.type === 'ai'"
                >
                  <ChatMessageMeta
                    :message="message"
                    :all-messages="renderMessages"
                    :default-expanded="workspace.sending.value"
                  />
                </div>
              </div>

              <div
                class="flex max-w-[88%] flex-wrap items-center gap-2 text-xs"
                :class="message.type === 'human' ? 'justify-end self-end' : 'justify-start self-start'"
              >
                <template v-if="editingMessageId === getMessageId(message, index)">
                  <button
                    type="button"
                    class="rounded-full border border-gray-200 px-3 py-1.5 font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900 dark:border-dark-700 dark:text-dark-200 dark:hover:bg-dark-800"
                    @click="cancelEditMessage"
                  >
                    取消编辑
                  </button>
                  <button
                    type="button"
                    class="rounded-full bg-primary-600 px-3 py-1.5 font-medium text-white transition hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
                    :disabled="workspace.sending.value"
                    @click="submitEditMessage(message, index)"
                  >
                    提交重发
                  </button>
                </template>

                <template v-else>
                  <button
                    type="button"
                    class="rounded-full border border-gray-200 px-3 py-1.5 font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900 dark:border-dark-700 dark:text-dark-200 dark:hover:bg-dark-800"
                    @click="handleCopyMessage(message)"
                  >
                    复制
                  </button>
                  <button
                    v-if="canEditMessage(message, index)"
                    type="button"
                    class="rounded-full border border-gray-200 px-3 py-1.5 font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900 dark:border-dark-700 dark:text-dark-200 dark:hover:bg-dark-800"
                    @click="startEditMessage(message, index)"
                  >
                    编辑
                  </button>
                  <button
                    v-if="canRetryMessage(message, index)"
                    type="button"
                    class="rounded-full border border-gray-200 px-3 py-1.5 font-medium text-gray-600 transition hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900 dark:border-dark-700 dark:text-dark-200 dark:hover:bg-dark-800"
                    @click="handleRetryMessage(message, index)"
                  >
                    重试
                  </button>

                  <div
                    v-if="hasBranchSwitcher(message, index)"
                    class="inline-flex items-center gap-2 rounded-full border border-gray-200 px-2 py-1 dark:border-dark-700"
                  >
                    <button
                      type="button"
                      class="rounded-full p-1 text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40 dark:text-dark-300 dark:hover:bg-dark-800 dark:hover:text-white"
                      :disabled="getMessageBranchIndex(message, index) <= 0 || workspace.sending.value"
                      @click="selectPreviousMessageBranch(message, index)"
                    >
                      <BaseIcon
                        name="chevron-left"
                        size="xs"
                      />
                    </button>
                    <span class="min-w-[64px] text-center font-medium text-gray-500 dark:text-dark-300">
                      {{ getMessageBranchIndex(message, index) + 1 }} /
                      {{ getMessageMeta(message, index)?.branchOptions?.length }}
                    </span>
                    <button
                      type="button"
                      class="rounded-full p-1 text-gray-500 transition hover:bg-gray-100 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40 dark:text-dark-300 dark:hover:bg-dark-800 dark:hover:text-white"
                      :disabled="
                        getMessageBranchIndex(message, index) >=
                          ((getMessageMeta(message, index)?.branchOptions?.length ?? 1) - 1) || workspace.sending.value
                      "
                      @click="selectNextMessageBranch(message, index)"
                    >
                      <BaseIcon
                        name="chevron-right"
                        size="xs"
                      />
                    </button>
                  </div>
                </template>
              </div>
            </div>

            <div
              v-if="workspace.sending.value"
              class="flex items-start"
            >
              <div class="rounded-[24px] border border-white/70 bg-white/95 px-4 py-3 shadow-soft dark:border-dark-700 dark:bg-dark-900/85">
                <div class="flex items-center gap-2 text-sm text-gray-500 dark:text-dark-300">
                  <span class="h-2 w-2 animate-pulse rounded-full bg-primary-400" />
                  <span class="h-2 w-2 animate-pulse rounded-full bg-primary-300 [animation-delay:120ms]" />
                  <span class="h-2 w-2 animate-pulse rounded-full bg-primary-200 [animation-delay:240ms]" />
                  <span>正在生成回复...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <ChatArtifactPanel
          v-if="showArtifacts && hasArtifactEntries"
          :values="workspace.displayState.value"
        />
      </div>

      <div class="border-t border-gray-100 px-6 py-5 dark:border-dark-800">
        <div class="rounded-[26px] border border-white/70 bg-white/95 p-4 shadow-soft dark:border-dark-700 dark:bg-dark-900/90">
          <ChatInterruptPanel
            v-if="hasBlockingInterrupt"
            :interrupt="workspace.interruptPayload.value"
            :submitting="workspace.sending.value"
            :on-resume="workspace.resumeInterruptedRun"
          />

          <ChatTasksFilesPanel
            :values="workspace.displayState.value"
            :is-running="workspace.sending.value"
            :has-interrupt="workspace.interruptPayload.value !== undefined"
            :on-update-state="workspace.updateThreadStatePatch"
          />

          <div
            v-if="composerAttachments.length > 0"
            class="mb-4 flex flex-wrap gap-3"
          >
            <ChatAttachmentPreview
              v-for="(attachment, index) in composerAttachments"
              :key="`composer-attachment-${index}`"
              :block="attachment"
              removable
              @remove="attachmentState.removeAttachment(index)"
            />
          </div>

          <textarea
            v-model="composerInput"
            rows="5"
            class="pw-input min-h-[132px] resize-none border-0 bg-transparent px-0 py-0 shadow-none focus:ring-0"
            placeholder="输入消息。Enter 发送，Shift + Enter 换行。"
            :disabled="workspace.sending.value || hasBlockingInterrupt"
            @keydown="handleComposerKeydown"
            @paste="handleComposerPaste"
          />

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap items-center gap-3 text-xs leading-6 text-gray-400 dark:text-dark-400">
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-full border border-gray-200 px-3 py-1.5 text-gray-600 transition hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700 dark:border-dark-700 dark:text-dark-200 dark:hover:border-primary-900/40 dark:hover:bg-primary-950/20 dark:hover:text-primary-100"
                :disabled="workspace.sending.value || hasBlockingInterrupt"
                @click="openFilePicker"
              >
                <BaseIcon
                  name="paperclip"
                  size="sm"
                />
                <span>上传图片 / PDF</span>
              </button>
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                multiple
                :accept="CHAT_ATTACHMENT_ACCEPT"
                @change="attachmentState.handleInputChange"
              >
              <span>
                {{
                  workspace.lastEventAt.value
                    ? `最近响应：${workspace.lastEventAt.value}`
                    : '支持 JPEG、PNG、GIF、WEBP、PDF，也支持直接粘贴图片。'
                }}
              </span>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <BaseButton
                variant="secondary"
                :disabled="!workspace.canStartThread.value"
                @click="workspace.startNewThread"
              >
                空白对话
              </BaseButton>
              <BaseButton
                v-if="showContinueAction"
                variant="secondary"
                @click="handleContinue"
              >
                <BaseIcon
                  name="chevron-right"
                  size="sm"
                />
                Continue
              </BaseButton>
              <BaseButton
                :variant="workspace.sending.value ? 'danger' : 'primary'"
                :disabled="workspace.sending.value ? workspace.cancelling.value : !canSendFreshMessage"
                @click="workspace.sending.value ? handleCancelRun() : handleSend()"
              >
                <BaseIcon
                  :name="workspace.sending.value ? 'x' : 'chat'"
                  size="sm"
                />
                {{
                  workspace.sending.value
                    ? workspace.cancelling.value
                      ? '取消中...'
                      : '取消运行'
                    : sendButtonLabel
                }}
              </BaseButton>
            </div>
          </div>
        </div>
      </div>
    </SurfaceCard>

    <BaseDrawer
      :show="threadsDrawerOpen"
      title="会话列表"
      side="left"
      width="narrow"
      @close="threadsDrawerOpen = false"
    >
      <div class="space-y-4">
        <div
          v-if="showContextBar"
          class="pw-card-glass p-4"
        >
          <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
            Current Target
          </div>
          <div class="mt-2 text-sm font-semibold text-gray-900 dark:text-white">
            {{ workspace.targetText.value }}
          </div>
          <div class="mt-1 text-xs leading-6 text-gray-500 dark:text-dark-300">
            {{ workspace.targetTypeText.value }} 模式会继续复用当前项目里的 thread 历史。
          </div>
        </div>

        <div class="flex items-center gap-2">
          <BaseInput
            v-model="threadSearch"
            placeholder="搜索会话标题、预览或状态"
          />
          <button
            type="button"
            class="pw-topbar-action h-11 px-3"
            :disabled="!workspace.canStartThread.value"
            @click="workspace.startNewThread"
          >
            <BaseIcon
              name="chat"
              size="sm"
            />
          </button>
        </div>

        <div class="flex flex-wrap gap-2">
          <button
            v-for="filter in threadStatusFilters"
            :key="filter.value"
            type="button"
            class="rounded-full border px-3 py-1.5 text-xs font-medium transition"
            :class="
              threadStatusFilter === filter.value
                ? 'border-primary-200 bg-primary-50 text-primary-700 dark:border-primary-900/40 dark:bg-primary-950/25 dark:text-primary-100'
                : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:text-gray-900 dark:border-dark-700 dark:bg-dark-900 dark:text-dark-300 dark:hover:text-white'
            "
            @click="threadStatusFilter = filter.value"
          >
            {{ filter.label }}
          </button>
        </div>

        <div
          v-if="workspace.loadingThreads.value && workspace.threadItems.value.length === 0"
          class="space-y-3"
        >
          <div
            v-for="index in 4"
            :key="index"
            class="pw-card-glass h-24 animate-pulse"
          />
        </div>

        <div
          v-else-if="workspace.threadItems.value.length === 0"
          class="pw-card-glass p-4 text-sm leading-7 text-gray-500 dark:text-dark-300"
        >
          还没有会话。第一条消息发出去时会自动创建 thread，你也可以先手动新建一个空白对话。
        </div>

        <div
          v-else-if="filteredThreadSummary.length === 0"
          class="pw-card-glass p-4 text-sm leading-7 text-gray-500 dark:text-dark-300"
        >
          没有命中当前筛选条件。
        </div>

        <div
          v-else
          class="space-y-4"
        >
          <div
            v-for="group in groupedThreadSummary"
            :key="group.key"
            class="space-y-2"
          >
            <div class="px-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
              {{ group.label }}
            </div>

            <div class="space-y-2">
              <div
                v-for="item in group.items"
                :key="item.id"
                class="group relative"
              >
                <button
                  type="button"
                  class="w-full rounded-2xl border px-4 py-3 pr-12 text-left transition"
                  :class="
                    item.id === workspace.activeThreadId.value
                      ? 'border-primary-200 bg-primary-50/85 shadow-soft dark:border-primary-900/40 dark:bg-primary-950/25'
                      : 'border-transparent bg-transparent hover:border-gray-200 hover:bg-gray-50 dark:hover:border-dark-700 dark:hover:bg-dark-900/60'
                  "
                  @click="handleSelectThread(item.id)"
                >
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="truncate text-sm font-semibold text-gray-900 dark:text-white">
                        {{ item.title }}
                      </div>
                      <div class="mt-1 line-clamp-2 text-xs leading-6 text-gray-500 dark:text-dark-300">
                        {{ item.preview || '当前 thread 还没有可展示的消息预览。' }}
                      </div>
                    </div>
                    <BaseIcon
                      v-if="item.id === workspace.activeThreadId.value"
                      name="check"
                      size="sm"
                      class="mt-1 shrink-0 text-primary-500"
                    />
                  </div>
                  <div class="mt-3 flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.14em] text-gray-400 dark:text-dark-400">
                    <span>{{ item.time }}</span>
                    <span>{{ item.status }}</span>
                  </div>
                </button>

                <button
                  type="button"
                  class="absolute right-3 top-3 rounded-full border border-transparent px-2 py-1 text-[11px] font-medium text-gray-400 opacity-0 transition hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600 group-hover:opacity-100 dark:hover:border-rose-900/40 dark:hover:bg-rose-950/20 dark:hover:text-rose-300"
                  :class="deletingThreadId === item.id ? 'opacity-100' : ''"
                  :disabled="deletingThreadId === item.id"
                  @click.stop="handleDeleteThread(item.id)"
                >
                  {{ deletingThreadId === item.id ? '删除中' : '删除' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseDrawer>

    <BaseDrawer
      :show="contextDrawerOpen"
      title="运行上下文与参数"
      side="right"
      width="wide"
      @close="contextDrawerOpen = false"
    >
      <div class="space-y-5">
        <div class="pw-card-glass p-4">
          <div class="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-400 dark:text-dark-400">
            当前上下文
          </div>
          <div class="mt-3 space-y-3 text-sm leading-7 text-gray-600 dark:text-dark-300">
            <div class="flex items-start justify-between gap-3">
              <span>Target</span>
              <span class="max-w-[220px] break-all text-right font-semibold text-gray-900 dark:text-white">{{ workspace.targetText.value }}</span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <span>项目</span>
              <span class="max-w-[220px] text-right font-semibold text-gray-900 dark:text-white">{{ currentProject?.name || '--' }}</span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <span>Thread</span>
              <span class="max-w-[220px] break-all text-right font-semibold text-gray-900 dark:text-white">{{ workspace.activeThreadId.value || '--' }}</span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <span>Run</span>
              <span class="max-w-[220px] break-all text-right font-semibold text-gray-900 dark:text-white">{{ workspace.lastRunId.value || '--' }}</span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <span>Branch</span>
              <span class="max-w-[220px] break-all text-right font-semibold text-gray-900 dark:text-white">
                {{ workspace.selectedBranch.value || 'latest' }}
              </span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <span>最近消息</span>
              <span class="max-w-[220px] text-right text-gray-500 dark:text-dark-300">{{ workspace.latestMessagePreview.value || '暂无' }}</span>
            </div>
          </div>
        </div>

        <div
          v-if="allowRunOptions"
          class="space-y-4"
        >
          <div class="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
            <BaseIcon
              name="runtime"
              size="sm"
              class="text-primary-500"
            />
            Run Options
          </div>

          <label class="block">
            <span class="pw-input-label">模型</span>
            <select
              v-model="draftRunOptions.modelId"
              class="pw-select"
            >
              <option value="">
                使用默认模型
              </option>
              <option
                v-for="model in workspace.runtimeModels.value"
                :key="model.id"
                :value="model.model_id"
              >
                {{ model.display_name || model.model_id }}
              </option>
            </select>
          </label>

          <div class="pw-card-glass p-4">
            <label class="flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-white">
                  工具开关
                </div>
                <div class="mt-1 text-xs leading-6 text-gray-500 dark:text-dark-300">
                  {{ selectedToolsLabel }}
                </div>
              </div>
              <input
                v-model="draftRunOptions.enableTools"
                type="checkbox"
                class="pw-table-checkbox"
              >
            </label>

            <div
              v-if="draftRunOptions.enableTools"
              class="mt-4 max-h-56 space-y-2 overflow-y-auto"
            >
              <label
                v-for="tool in workspace.runtimeTools.value"
                :key="tool.id"
                class="flex items-start gap-3 rounded-2xl border border-white/70 bg-white/80 px-3 py-3 text-sm dark:border-dark-700 dark:bg-dark-900/70"
              >
                <input
                  :checked="draftRunOptions.toolNames.includes(tool.tool_key)"
                  type="checkbox"
                  class="pw-table-checkbox mt-1"
                  @change="toggleDraftTool(tool.tool_key)"
                >
                <div class="min-w-0">
                  <div class="font-semibold text-gray-900 dark:text-white">
                    {{ tool.name || tool.tool_key }}
                  </div>
                  <div class="mt-1 text-xs leading-6 text-gray-500 dark:text-dark-300">
                    {{ tool.description || tool.source || '暂无描述' }}
                  </div>
                </div>
              </label>

              <div
                v-if="workspace.runtimeTools.value.length === 0 && !workspace.loadingRuntime.value"
                class="text-xs leading-6 text-gray-400 dark:text-dark-400"
              >
                当前没有可选工具目录。
              </div>
            </div>
          </div>

          <div class="pw-card-glass p-4">
            <label class="flex items-center justify-between gap-3">
              <div>
                <div class="text-sm font-semibold text-gray-900 dark:text-white">
                  Debug Mode
                </div>
                <div class="mt-1 text-xs leading-6 text-gray-500 dark:text-dark-300">
                  打开后，发送消息会先在工具执行前暂停，你可以逐步继续执行。
                </div>
              </div>
              <input
                v-model="draftRunOptions.debugMode"
                type="checkbox"
                class="pw-table-checkbox"
              >
            </label>
          </div>

          <div class="grid gap-4 md:grid-cols-2">
            <label class="block">
              <span class="pw-input-label">Temperature</span>
              <input
                v-model="draftRunOptions.temperature"
                class="pw-input"
                placeholder="例如 0.2"
              >
            </label>
            <label class="block">
              <span class="pw-input-label">Max Tokens</span>
              <input
                v-model="draftRunOptions.maxTokens"
                class="pw-input"
                placeholder="例如 4096"
              >
            </label>
          </div>
        </div>

        <div
          v-if="showHistory"
          class="space-y-3"
        >
          <details class="pw-card-glass overflow-hidden p-4">
            <summary class="cursor-pointer list-none">
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-2 text-sm font-semibold text-gray-900 dark:text-white">
                  <BaseIcon
                    name="threads"
                    size="sm"
                    class="text-primary-500"
                  />
                  最近历史
                </div>
                <div class="text-xs text-gray-400 dark:text-dark-400">
                  调试用
                </div>
              </div>
            </summary>

            <div class="mt-4 space-y-3">
              <div
                v-if="workspace.isViewingBranch.value"
                class="flex items-center justify-between gap-3 rounded-2xl border border-primary-200 bg-primary-50/70 px-3 py-3 text-sm dark:border-primary-900/40 dark:bg-primary-950/20"
              >
                <div class="min-w-0">
                  <div class="font-semibold text-gray-900 dark:text-white">
                    当前正在查看历史分支
                  </div>
                  <div class="mt-1 break-all text-xs leading-6 text-gray-500 dark:text-dark-300">
                    {{ workspace.selectedBranch.value }}
                  </div>
                </div>
                <BaseButton
                  variant="ghost"
                  @click="workspace.selectBranch('')"
                >
                  返回最新
                </BaseButton>
              </div>

              <div
                v-if="workspace.historyItems.value.length === 0"
                class="text-sm leading-7 text-gray-500 dark:text-dark-300"
              >
                当前 thread 还没有 checkpoint 历史，或者还没开始对话。
              </div>

              <details
                v-for="(entry, historyIndex) in workspace.historyItems.value"
                :key="getHistoryEntryId(entry, historyIndex)"
                class="rounded-2xl border border-white/70 bg-white/80 p-4 dark:border-dark-700 dark:bg-dark-900/70"
              >
                <summary class="cursor-pointer list-none">
                  <div class="flex items-center justify-between gap-3">
                    <div class="text-sm font-semibold text-gray-900 dark:text-white">
                      {{ getHistoryEntryId(entry, historyIndex) }}
                    </div>
                    <div class="text-xs text-gray-400 dark:text-dark-400">
                      {{ getHistoryEntryTime(entry) }}
                    </div>
                  </div>
                </summary>
                <div class="mt-3 flex justify-end">
                  <BaseButton
                    variant="ghost"
                    @click="workspace.selectBranch(getHistoryEntryId(entry, historyIndex))"
                  >
                    查看此分支
                  </BaseButton>
                </div>
                <pre class="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-2xl bg-gray-950 px-3 py-3 text-xs leading-6 text-gray-100 dark:bg-black/50">{{ toPrettyJson(entry) }}</pre>
              </details>
            </div>
          </details>
        </div>

        <div
          v-if="showArtifacts"
          class="pw-card-glass p-4 text-sm leading-7 text-gray-500 dark:text-dark-300"
        >
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            Artifact 侧栏
          </div>
          <p class="mt-2">
            当前 thread 如果存在 `values.ui` 条目，会在主画布右侧直接展开 artifact 侧栏。没有数据时，这里只保留口径说明，不再继续放空占位。
          </p>
        </div>

        <div
          v-if="allowResetTarget"
          class="pw-card-glass p-4"
        >
          <div class="text-sm font-semibold text-gray-900 dark:text-white">
            默认聊天目标
          </div>
          <p class="mt-2 text-sm leading-7 text-gray-500 dark:text-dark-300">
            这个动作只会清掉当前项目保存的默认聊天入口，不会删除任何 thread、消息或后端运行数据。
          </p>
          <div class="mt-4">
            <BaseButton
              variant="ghost"
              @click="handleResetTarget"
            >
              重置默认聊天目标
            </BaseButton>
          </div>
        </div>
      </div>

      <template
        v-if="allowRunOptions"
        #footer
      >
        <div class="flex flex-wrap items-center gap-3">
          <BaseButton
            variant="ghost"
            @click="restoreDraftRunOptions"
          >
            还原
          </BaseButton>
          <BaseButton @click="applyDraftRunOptions">
            确定
          </BaseButton>
        </div>
      </template>
    </BaseDrawer>
  </section>
</template>
