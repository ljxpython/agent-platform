<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseIcon from '@/components/base/BaseIcon.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import SearchInput from '@/components/platform/SearchInput.vue'
import SurfaceCard from '@/components/base/SurfaceCard.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/platform/EmptyState.vue'
import StateBanner from '@/components/platform/StateBanner.vue'
import { useAuthorization } from '@/composables/useAuthorization'
import KnowledgeWorkspaceNav from '@/modules/knowledge/components/KnowledgeWorkspaceNav.vue'
import { useKnowledgeProjectRoute } from '@/modules/knowledge/composables/useKnowledgeProjectRoute'
import {
  getProjectKnowledgeGraph,
  listProjectKnowledgeGraphLabels,
  listProjectKnowledgePopularGraphLabels,
  searchProjectKnowledgeGraphLabels,
} from '@/services/knowledge/knowledge.service'
import { resolvePlatformHttpErrorMessage } from '@/utils/http-error'

type RawGraphNode = Record<string, unknown>
type RawGraphEdge = Record<string, unknown>
type LayoutMode = 'force' | 'radial' | 'grid'
type GraphNodeLayout = RawGraphNode & {
  id: string
  label: string
  typeLabel: string
  degree: number
  properties: Record<string, unknown>
  searchText: string
  x: number
  y: number
}
type GraphEdgeLayout = RawGraphEdge & {
  id: string
  label: string
  sourceNode: GraphNodeLayout
  targetNode: GraphNodeLayout
}
type GraphRelationSummary = {
  edgeId: string
  label: string
  direction: 'outgoing' | 'incoming'
  nodeId: string
  nodeLabel: string
  nodeTypeLabel: string
}
type GraphPanelStat = {
  key: string
  label: string
  value: string | number
}

const GRAPH_WIDTH = 1200
const GRAPH_HEIGHT = 760
const GRAPH_CENTER = { x: GRAPH_WIDTH / 2, y: GRAPH_HEIGHT / 2 }
const GRAPH_PADDING = 84

const { projectId, project } = useKnowledgeProjectRoute()
const authorization = useAuthorization()

const labels = ref<string[]>([])
const popularLabels = ref<string[]>([])
const queryInput = ref('')
const loadingLabels = ref(false)
const loadingGraph = ref(false)
const error = ref('')
const selectedLabel = ref('')
const graph = ref<Record<string, unknown> | null>(null)
const selectedNodeId = ref('')
const zoom = ref(1)
const rotation = ref(0)
const panOffset = ref({ x: 0, y: 0 })
const maxDepth = ref(3)
const maxNodes = ref(200)
const layoutMode = ref<LayoutMode>('force')
const autoPositions = ref<Record<string, { x: number; y: number }>>({})
const dragNodeId = ref('')
const draggedPositions = ref<Record<string, { x: number; y: number }>>({})
const panAnchor = ref<{ pointerX: number; pointerY: number; originX: number; originY: number } | null>(null)
const nodeSearch = ref('')
const showLegend = ref(true)
const showNodeLabels = ref(true)
const showEdgeLabels = ref(true)
const enableNodeDrag = ref(true)
const showLabelPanel = ref(true)
const showSettingsPanel = ref(false)
const showInspectorPanel = ref(true)

const canRead = computed(() => authorization.can('project.knowledge.read', projectId.value))

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function resolveNodeProperties(node: RawGraphNode) {
  return isRecord(node.properties) ? node.properties : {}
}

function resolveNodeTypeLabel(node: RawGraphNode) {
  const properties = resolveNodeProperties(node)
  const labels = Array.isArray(node.labels) ? node.labels : []
  const firstLabel = labels.find((item) => typeof item === 'string' && item.trim())
  const fallback = [properties.entity_type, properties.type, properties.category].find(
    (item) => typeof item === 'string' && item.trim(),
  )
  return String(firstLabel || fallback || 'unknown')
}

function resolveNodeDisplayLabel(node: RawGraphNode, fallbackId: string) {
  const properties = resolveNodeProperties(node)
  const candidates = [
    properties.entity_name,
    properties.name,
    properties.title,
    properties.entity_id,
    properties.id,
    node.id,
  ]
  const firstCandidate = candidates.find((item) => typeof item === 'string' && item.trim())
  if (firstCandidate) {
    return String(firstCandidate)
  }
  const labels = Array.isArray(node.labels) ? node.labels.filter((item) => typeof item === 'string') : []
  return String(labels[0] || fallbackId)
}

function hashString(value: string) {
  let hash = 0
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0
  }
  return hash
}

const nodes = computed<RawGraphNode[]>(() =>
  Array.isArray(graph.value?.nodes) ? (graph.value?.nodes as RawGraphNode[]) : [],
)
const edges = computed<RawGraphEdge[]>(() =>
  Array.isArray(graph.value?.edges) ? (graph.value?.edges as RawGraphEdge[]) : [],
)

const nodeDegreeMap = computed(() => {
  const map = new Map<string, number>()
  for (const edge of edges.value) {
    const sourceId = String(edge.source || '')
    const targetId = String(edge.target || '')
    if (sourceId) {
      map.set(sourceId, (map.get(sourceId) || 0) + 1)
    }
    if (targetId) {
      map.set(targetId, (map.get(targetId) || 0) + 1)
    }
  }
  return map
})

const graphNodeMeta = computed(() =>
  nodes.value.map((node, index) => {
    const id = String(node.id || `node-${index}`)
    const properties = resolveNodeProperties(node)
    const label = resolveNodeDisplayLabel(node, id)
    const typeLabel = resolveNodeTypeLabel(node)
    return {
      ...node,
      id,
      label,
      typeLabel,
      degree: nodeDegreeMap.value.get(id) || 0,
      properties,
      searchText: `${label} ${typeLabel} ${Object.values(properties).join(' ')}`.toLowerCase(),
    }
  }),
)

function buildGridPositions(nodeList: Array<{ id: string }>) {
  const columns = Math.max(1, Math.ceil(Math.sqrt(nodeList.length || 1)))
  return Object.fromEntries(
    nodeList.map((node, index) => {
      const row = Math.floor(index / columns)
      const column = index % columns
      return [
        node.id,
        {
          x: 170 + column * 150,
          y: 150 + row * 130,
        },
      ]
    }),
  )
}

function buildRadialPositions(nodeList: Array<{ id: string; degree: number }>) {
  if (!nodeList.length) {
    return {}
  }

  const sorted = [...nodeList].sort((left, right) => right.degree - left.degree)
  const positions: Record<string, { x: number; y: number }> = {}
  const centerNode = sorted[0]
  positions[centerNode.id] = { ...GRAPH_CENTER }

  const remaining = sorted.slice(1)
  const ringSize = Math.max(6, Math.ceil(Math.sqrt(remaining.length || 1)) * 3)
  remaining.forEach((node, index) => {
    const ring = Math.floor(index / ringSize)
    const positionInRing = index % ringSize
    const itemsInRing = Math.min(ringSize, remaining.length - ring * ringSize)
    const radius = 150 + ring * 96
    const angle = (Math.PI * 2 * positionInRing) / Math.max(itemsInRing, 1)
    positions[node.id] = {
      x: clamp(GRAPH_CENTER.x + radius * Math.cos(angle), GRAPH_PADDING, GRAPH_WIDTH - GRAPH_PADDING),
      y: clamp(GRAPH_CENTER.y + radius * Math.sin(angle), GRAPH_PADDING, GRAPH_HEIGHT - GRAPH_PADDING),
    }
  })

  return positions
}

function buildForcePositions(nodeList: Array<{ id: string; degree: number }>, edgeList: RawGraphEdge[]) {
  if (!nodeList.length) {
    return {}
  }

  const positions = buildRadialPositions(nodeList)
  const displacements = new Map<string, { x: number; y: number }>()
  const nodeMap = new Map(nodeList.map((node) => [node.id, node]))
  const area = (GRAPH_WIDTH - GRAPH_PADDING * 2) * (GRAPH_HEIGHT - GRAPH_PADDING * 2)
  const k = Math.sqrt(area / Math.max(nodeList.length, 1)) * 0.78
  const edgePairs = edgeList
    .map((edge) => ({
      source: String(edge.source || ''),
      target: String(edge.target || ''),
    }))
    .filter((edge) => edge.source && edge.target && nodeMap.has(edge.source) && nodeMap.has(edge.target))

  for (let iteration = 0; iteration < 120; iteration += 1) {
    for (const node of nodeList) {
      displacements.set(node.id, { x: 0, y: 0 })
    }

    for (let i = 0; i < nodeList.length; i += 1) {
      for (let j = i + 1; j < nodeList.length; j += 1) {
        const left = nodeList[i]
        const right = nodeList[j]
        const leftPosition = positions[left.id]
        const rightPosition = positions[right.id]
        const deltaX = leftPosition.x - rightPosition.x
        const deltaY = leftPosition.y - rightPosition.y
        const distance = Math.max(Math.hypot(deltaX, deltaY), 1)
        const force = (k * k) / distance
        const offsetX = (deltaX / distance) * force
        const offsetY = (deltaY / distance) * force

        const leftDisplacement = displacements.get(left.id)!
        const rightDisplacement = displacements.get(right.id)!
        leftDisplacement.x += offsetX
        leftDisplacement.y += offsetY
        rightDisplacement.x -= offsetX
        rightDisplacement.y -= offsetY
      }
    }

    for (const edge of edgePairs) {
      const sourcePosition = positions[edge.source]
      const targetPosition = positions[edge.target]
      const deltaX = sourcePosition.x - targetPosition.x
      const deltaY = sourcePosition.y - targetPosition.y
      const distance = Math.max(Math.hypot(deltaX, deltaY), 1)
      const force = (distance * distance) / k
      const offsetX = (deltaX / distance) * force
      const offsetY = (deltaY / distance) * force

      const sourceDisplacement = displacements.get(edge.source)!
      const targetDisplacement = displacements.get(edge.target)!
      sourceDisplacement.x -= offsetX
      sourceDisplacement.y -= offsetY
      targetDisplacement.x += offsetX
      targetDisplacement.y += offsetY
    }

    const temperature = 24 * (1 - iteration / 120)
    for (const node of nodeList) {
      const position = positions[node.id]
      const displacement = displacements.get(node.id)!
      const magnitude = Math.max(Math.hypot(displacement.x, displacement.y), 1)
      const degreeBias = node.degree > 2 ? 0.05 : 0.02
      const toCenterX = (GRAPH_CENTER.x - position.x) * degreeBias
      const toCenterY = (GRAPH_CENTER.y - position.y) * degreeBias
      position.x = clamp(
        position.x + (displacement.x / magnitude) * Math.min(magnitude, temperature) + toCenterX,
        GRAPH_PADDING,
        GRAPH_WIDTH - GRAPH_PADDING,
      )
      position.y = clamp(
        position.y + (displacement.y / magnitude) * Math.min(magnitude, temperature) + toCenterY,
        GRAPH_PADDING,
        GRAPH_HEIGHT - GRAPH_PADDING,
      )
    }
  }

  return positions
}

function recomputeLayout() {
  if (!graphNodeMeta.value.length) {
    autoPositions.value = {}
    return
  }

  if (layoutMode.value === 'grid') {
    autoPositions.value = buildGridPositions(graphNodeMeta.value)
    return
  }

  if (layoutMode.value === 'radial') {
    autoPositions.value = buildRadialPositions(graphNodeMeta.value)
    return
  }

  autoPositions.value = buildForcePositions(graphNodeMeta.value, edges.value)
}

const graphNodes = computed<GraphNodeLayout[]>(() =>
  graphNodeMeta.value.map((node) => {
    const autoPosition = autoPositions.value[node.id] || GRAPH_CENTER
    const draggedPosition = draggedPositions.value[node.id]
    return {
      ...node,
      x: draggedPosition?.x ?? autoPosition.x,
      y: draggedPosition?.y ?? autoPosition.y,
    }
  }),
)

const graphEdges = computed<GraphEdgeLayout[]>(() => {
  const nodeMap = new Map(graphNodes.value.map((node) => [node.id, node]))
  return edges.value
    .map((edge, index) => {
      const sourceNode = nodeMap.get(String(edge.source || ''))
      const targetNode = nodeMap.get(String(edge.target || ''))
      if (!sourceNode || !targetNode) {
        return null
      }
      return {
        ...edge,
        id: String(edge.id || `${sourceNode.id}-${targetNode.id}-${index}`),
        label: String(edge.label || edge.type || edge.relation || '关联'),
        sourceNode,
        targetNode,
      }
    })
    .filter((edge): edge is GraphEdgeLayout => edge !== null)
})

const selectedNode = computed<GraphNodeLayout | null>(
  () => graphNodes.value.find((item) => item.id === selectedNodeId.value) ?? null,
)

const selectedNodeRelations = computed<GraphRelationSummary[]>(() => {
  if (!selectedNode.value) {
    return []
  }
  return graphEdges.value
    .filter(
      (edge) => edge.sourceNode.id === selectedNode.value?.id || edge.targetNode.id === selectedNode.value?.id,
    )
    .map((edge) => {
      const outgoing = edge.sourceNode.id === selectedNode.value?.id
      const node = outgoing ? edge.targetNode : edge.sourceNode
      return {
        edgeId: edge.id,
        label: edge.label || '关联',
        direction: outgoing ? 'outgoing' : 'incoming',
        nodeId: node.id,
        nodeLabel: node.label,
        nodeTypeLabel: node.typeLabel,
      }
    })
})

const nodeTypeLegend = computed(() => {
  const map = new Map<string, string>()
  for (const node of graphNodes.value) {
    if (!map.has(node.typeLabel)) {
      map.set(node.typeLabel, `hsl(${(map.size * 67) % 360} 72% 58%)`)
    }
  }
  return Array.from(map.entries()).map(([label, color]) => ({ label, color }))
})

const selectedLabelDisplay = computed(() => (selectedLabel.value === '*' ? '全部图谱' : selectedLabel.value || '未选择标签'))
const nodeSearchQuery = computed(() => nodeSearch.value.trim().toLowerCase())
const nodeSearchMatches = computed(() => {
  if (!nodeSearchQuery.value) {
    return graphNodes.value
  }
  return graphNodes.value.filter((node) => node.searchText.includes(nodeSearchQuery.value))
})
const nodeSearchMatchIds = computed(() => new Set(nodeSearchMatches.value.map((node) => node.id)))

const quickFocusNodes = computed(() => {
  const source = nodeSearchQuery.value
    ? nodeSearchMatches.value
    : [...graphNodes.value].sort((left, right) => right.degree - left.degree || left.label.localeCompare(right.label))
  return source.slice(0, 8)
})

const graphStats = computed(() => {
  const nodeCount = graphNodes.value.length
  const edgeCount = graphEdges.value.length
  const isolatedCount = graphNodes.value.filter((node) => node.degree === 0).length
  return {
    nodeCount,
    edgeCount,
    isolatedCount,
    visibleCount: nodeSearchQuery.value ? nodeSearchMatches.value.length : nodeCount,
  }
})

const panelStats = computed<GraphPanelStat[]>(() => [
  { key: 'layout', label: '布局', value: layoutMode.value },
  { key: 'nodes', label: '节点', value: graphStats.value.nodeCount },
  { key: 'edges', label: '关系', value: graphStats.value.edgeCount },
  { key: 'visible', label: '搜索命中', value: graphStats.value.visibleCount },
])

const selectedNodePropertyEntries = computed(() =>
  selectedNode.value ? Object.entries(selectedNode.value.properties).slice(0, 8) : [],
)

const graphTransformStyle = computed(() => ({
  transform: `translate(${panOffset.value.x}px, ${panOffset.value.y}px) scale(${zoom.value}) rotate(${rotation.value}rad)`,
  transformOrigin: 'center center',
}))

function adjustZoom(delta: number) {
  zoom.value = clamp(Number((zoom.value + delta).toFixed(2)), 0.55, 2.6)
}

function rotateGraph(delta: number) {
  rotation.value = Number((rotation.value + delta).toFixed(2))
}

function resetViewport() {
  zoom.value = 1
  rotation.value = 0
  panOffset.value = { x: 0, y: 0 }
}

function nodeFillColor(node: GraphNodeLayout) {
  const matched = nodeTypeLegend.value.find((item) => item.label === node.typeLabel)
  return matched?.color || '#60a5fa'
}

function nodeRadius(node: GraphNodeLayout) {
  const base = 16 + Math.min(node.degree, 8) * 1.6
  if (selectedNodeId.value === node.id) {
    return base + 7
  }
  if (nodeSearchQuery.value && nodeSearchMatchIds.value.has(node.id)) {
    return base + 3
  }
  return base
}

function nodeOpacity(node: GraphNodeLayout) {
  if (!nodeSearchQuery.value) {
    return 1
  }
  return nodeSearchMatchIds.value.has(node.id) ? 1 : 0.18
}

function edgeOpacity(edge: GraphEdgeLayout) {
  if (selectedNodeId.value) {
    return edge.sourceNode.id === selectedNodeId.value || edge.targetNode.id === selectedNodeId.value ? 0.92 : 0.12
  }
  if (nodeSearchQuery.value) {
    const sourceMatched = nodeSearchMatchIds.value.has(edge.sourceNode.id)
    const targetMatched = nodeSearchMatchIds.value.has(edge.targetNode.id)
    return sourceMatched || targetMatched ? 0.58 : 0.1
  }
  return 0.46
}

function edgeStrokeColor(edge: GraphEdgeLayout) {
  if (selectedNodeId.value && (edge.sourceNode.id === selectedNodeId.value || edge.targetNode.id === selectedNodeId.value)) {
    return '#2563eb'
  }
  return '#94a3b8'
}

function edgeControlPoint(edge: GraphEdgeLayout) {
  const x1 = edge.sourceNode.x
  const y1 = edge.sourceNode.y
  const x2 = edge.targetNode.x
  const y2 = edge.targetNode.y
  const deltaX = x2 - x1
  const deltaY = y2 - y1
  const distance = Math.max(Math.hypot(deltaX, deltaY), 1)
  const normalX = -deltaY / distance
  const normalY = deltaX / distance
  const curveDirection = hashString(edge.id) % 2 === 0 ? 1 : -1
  const curveOffset = clamp(distance * 0.14, 16, 48) * curveDirection
  const midX = (x1 + x2) / 2
  const midY = (y1 + y2) / 2
  return {
    x: midX + normalX * curveOffset,
    y: midY + normalY * curveOffset,
  }
}

function edgePath(edge: GraphEdgeLayout) {
  const control = edgeControlPoint(edge)
  return `M ${edge.sourceNode.x} ${edge.sourceNode.y} Q ${control.x} ${control.y} ${edge.targetNode.x} ${edge.targetNode.y}`
}

function edgeLabelPosition(edge: GraphEdgeLayout) {
  const control = edgeControlPoint(edge)
  return {
    x: 0.25 * edge.sourceNode.x + 0.5 * control.x + 0.25 * edge.targetNode.x,
    y: 0.25 * edge.sourceNode.y + 0.5 * control.y + 0.25 * edge.targetNode.y - 8,
  }
}

function focusNode(nodeId: string) {
  selectedNodeId.value = nodeId
  showInspectorPanel.value = true
  zoom.value = Math.max(zoom.value, 1.06)
  panOffset.value = { x: 0, y: 0 }
  draggedPositions.value = {
    ...draggedPositions.value,
    [nodeId]: { ...GRAPH_CENTER },
  }
}

function focusAll() {
  selectedNodeId.value = ''
  nodeSearch.value = ''
  draggedPositions.value = {}
  resetViewport()
  recomputeLayout()
}

function startDrag(nodeId: string) {
  if (!enableNodeDrag.value) {
    return
  }
  dragNodeId.value = nodeId
}

function startPan(event: MouseEvent) {
  if (dragNodeId.value || !graph.value) {
    return
  }
  panAnchor.value = {
    pointerX: event.clientX,
    pointerY: event.clientY,
    originX: panOffset.value.x,
    originY: panOffset.value.y,
  }
}

function stopInteractions() {
  dragNodeId.value = ''
  panAnchor.value = null
}

function updateDraggedPosition(event: MouseEvent) {
  if (!dragNodeId.value) {
    return
  }
  const target = event.currentTarget as SVGElement | null
  if (!target) {
    return
  }
  const rect = target.getBoundingClientRect()
  const x = clamp(((event.clientX - rect.left) / rect.width) * GRAPH_WIDTH, GRAPH_PADDING / 2, GRAPH_WIDTH - GRAPH_PADDING / 2)
  const y = clamp(((event.clientY - rect.top) / rect.height) * GRAPH_HEIGHT, GRAPH_PADDING / 2, GRAPH_HEIGHT - GRAPH_PADDING / 2)
  draggedPositions.value = {
    ...draggedPositions.value,
    [dragNodeId.value]: { x, y },
  }
}

function updatePointer(event: MouseEvent) {
  if (panAnchor.value) {
    panOffset.value = {
      x: panAnchor.value.originX + (event.clientX - panAnchor.value.pointerX),
      y: panAnchor.value.originY + (event.clientY - panAnchor.value.pointerY),
    }
    return
  }
  updateDraggedPosition(event)
}

async function loadGraphLabels() {
  if (!projectId.value || !canRead.value) {
    labels.value = []
    popularLabels.value = []
    graph.value = null
    return
  }

  loadingLabels.value = true
  error.value = ''
  try {
    const [nextLabels, nextPopular] = await Promise.all([
      queryInput.value.trim()
        ? searchProjectKnowledgeGraphLabels(projectId.value, queryInput.value.trim(), 50)
        : listProjectKnowledgeGraphLabels(projectId.value),
      listProjectKnowledgePopularGraphLabels(projectId.value, 10),
    ])
    labels.value = nextLabels
    popularLabels.value = nextPopular

    if (!selectedLabel.value) {
      await openGraph('*')
    }
  } catch (loadError) {
    labels.value = []
    popularLabels.value = []
    error.value = resolvePlatformHttpErrorMessage(loadError, '知识图谱标签加载失败', '知识图谱')
  } finally {
    loadingLabels.value = false
  }
}

async function openGraph(label: string) {
  if (!projectId.value || !canRead.value || !label.trim()) {
    return
  }

  loadingGraph.value = true
  error.value = ''
  selectedLabel.value = label.trim()
  try {
    graph.value = await getProjectKnowledgeGraph(projectId.value, {
      label: selectedLabel.value,
      max_depth: maxDepth.value,
      max_nodes: maxNodes.value,
    })
    const firstNode = Array.isArray(graph.value?.nodes) ? graph.value?.nodes[0] : null
    selectedNodeId.value =
      firstNode && typeof firstNode === 'object'
        ? String((firstNode as Record<string, unknown>).id || '')
        : ''
    nodeSearch.value = ''
    draggedPositions.value = {}
    resetViewport()
    recomputeLayout()
  } catch (graphError) {
    graph.value = null
    selectedNodeId.value = ''
    error.value = resolvePlatformHttpErrorMessage(graphError, '知识图谱加载失败', '知识图谱')
  } finally {
    loadingGraph.value = false
  }
}

async function refreshCurrentGraph() {
  if (selectedLabel.value) {
    await openGraph(selectedLabel.value)
    return
  }
  await loadGraphLabels()
}

watch(
  () =>
    `${layoutMode.value}|${graphNodeMeta.value.map((node) => node.id).join(',')}|${edges.value
      .map((edge) => `${String(edge.source || '')}->${String(edge.target || '')}`)
      .join(',')}`,
  () => {
    draggedPositions.value = {}
    recomputeLayout()
  },
  { immediate: true },
)

watch(
  () => projectId.value,
  () => {
    selectedLabel.value = ''
    graph.value = null
    draggedPositions.value = {}
    autoPositions.value = {}
    nodeSearch.value = ''
    showLegend.value = true
    showNodeLabels.value = true
    showEdgeLabels.value = true
    enableNodeDrag.value = true
    showLabelPanel.value = true
    showSettingsPanel.value = false
    showInspectorPanel.value = true
    layoutMode.value = 'force'
    resetViewport()
    void loadGraphLabels()
  },
  { immediate: true },
)
</script>

<template>
  <section class="pw-page-shell">
    <PageHeader
      eyebrow="Knowledge"
      :title="project ? `${project.name} · 知识图谱` : '知识图谱'"
      description="把 LightRAG 用户侧的图谱工作流压到一个图谱工作区里：标签切换、搜索、布局、设置、属性与图例都内嵌在图中。"
    />

    <KnowledgeWorkspaceNav
      v-if="projectId"
      :project-id="projectId"
    />

    <StateBanner
      v-if="projectId && !canRead"
      class="mt-4"
      title="当前角色没有知识图谱读取权限"
      description="请联系项目管理员授予 project.knowledge.read 权限后，再浏览当前项目的知识图谱。"
      variant="info"
    />
    <StateBanner
      v-else-if="error"
      class="mt-4"
      title="知识图谱异常"
      :description="error"
      variant="danger"
    />

    <SurfaceCard class="mt-4 overflow-hidden">
      <div class="relative h-[76vh] min-h-[720px] max-h-[900px] overflow-hidden rounded-[28px] border border-gray-100 bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.16),_rgba(255,255,255,0)_58%),linear-gradient(135deg,_rgba(148,163,184,0.08),_rgba(148,163,184,0.02))] dark:border-dark-800 dark:bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.22),_rgba(15,23,42,0)_58%),linear-gradient(135deg,_rgba(30,41,59,0.92),_rgba(15,23,42,0.96))]">
        <div class="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(148,163,184,0.12)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.12)_1px,transparent_1px)] bg-[length:40px_40px]" />

        <div class="absolute left-4 top-4 z-40 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition"
            :class="showLabelPanel ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-white/70 bg-white/85 text-gray-600 dark:border-dark-700 dark:bg-dark-950/80 dark:text-dark-300'"
            @click="showLabelPanel = !showLabelPanel"
          >
            标签面板
          </button>
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition"
            :class="showSettingsPanel ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-white/70 bg-white/85 text-gray-600 dark:border-dark-700 dark:bg-dark-950/80 dark:text-dark-300'"
            @click="showSettingsPanel = !showSettingsPanel"
          >
            设置
          </button>
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition"
            :class="showInspectorPanel ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-white/70 bg-white/85 text-gray-600 dark:border-dark-700 dark:bg-dark-950/80 dark:text-dark-300'"
            @click="showInspectorPanel = !showInspectorPanel"
          >
            属性
          </button>
          <button
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-medium transition"
            :class="showLegend ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-white/70 bg-white/85 text-gray-600 dark:border-dark-700 dark:bg-dark-950/80 dark:text-dark-300'"
            @click="showLegend = !showLegend"
          >
            图例
          </button>
        </div>

        <div class="absolute left-1/2 top-4 z-30 flex -translate-x-1/2 flex-wrap items-center justify-center gap-2 px-4">
          <span
            class="inline-flex items-center gap-2 rounded-full border border-white/80 bg-white/90 px-4 py-1.5 text-sm font-semibold text-gray-900 shadow-lg backdrop-blur dark:border-dark-700 dark:bg-dark-950/85 dark:text-white"
          >
            <BaseIcon
              name="graph"
              size="xs"
            />
            {{ selectedLabelDisplay }}
          </span>
          <span
            v-for="item in panelStats"
            :key="item.key"
            class="rounded-full border border-white/80 bg-white/90 px-3 py-1.5 text-xs text-gray-600 shadow-lg backdrop-blur dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-300"
          >
            {{ item.label }} · {{ item.value }}
          </span>
        </div>

        <div class="absolute left-4 top-16 z-30 w-[288px] max-w-[calc(100%-2rem)] space-y-3">
          <div
            v-if="showLabelPanel"
            class="max-h-[560px] overflow-auto rounded-3xl border border-white/80 bg-white/90 p-4 shadow-xl backdrop-blur dark:border-dark-700 dark:bg-dark-950/88"
          >
            <div class="flex items-start justify-between gap-3">
              <div>
                <div class="text-xs font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                  图谱入口
                </div>
                <div class="mt-2 text-sm text-gray-600 dark:text-dark-300">
                  像 LightRAG 一样，先在图里切标签，再继续搜索和聚焦。
                </div>
              </div>
              <BaseButton
                variant="secondary"
                :disabled="loadingGraph || !canRead"
                @click="void refreshCurrentGraph()"
              >
                刷新
              </BaseButton>
            </div>

            <div class="mt-4">
              <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                推荐入口
              </div>
              <div class="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs transition"
                  :class="selectedLabel === '*' ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:text-dark-300'"
                  @click="void openGraph('*')"
                >
                  全部图谱
                </button>
                <button
                  v-for="label in popularLabels"
                  :key="label"
                  type="button"
                  class="rounded-full border px-3 py-1 text-xs transition"
                  :class="selectedLabel === label ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:text-dark-300'"
                  @click="void openGraph(label)"
                >
                  {{ label }}
                </button>
              </div>
            </div>

            <div class="mt-4">
              <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                标签搜索
              </div>
              <div class="mt-2 flex items-end gap-2">
                <div class="flex-1">
                  <SearchInput
                    v-model="queryInput"
                    placeholder="搜索实体标签"
                  />
                </div>
                <BaseButton
                  variant="secondary"
                  :disabled="loadingLabels || !canRead"
                  @click="void loadGraphLabels()"
                >
                  查找
                </BaseButton>
              </div>
            </div>

            <div class="mt-4">
              <div class="mb-2 flex items-center justify-between gap-3">
                <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                  标签列表
                </div>
                <div class="text-xs text-gray-400 dark:text-dark-500">
                  {{ labels.length }}
                </div>
              </div>
              <div class="max-h-[180px] space-y-2 overflow-auto pr-1">
                <button
                  v-for="label in labels"
                  :key="label"
                  type="button"
                  class="flex w-full items-center justify-between gap-3 rounded-2xl border px-3 py-2.5 text-left text-sm transition"
                  :class="selectedLabel === label ? 'border-primary-300 bg-primary-50 text-primary-700 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200' : 'border-gray-100 bg-white text-gray-700 hover:border-primary-200 hover:text-primary-700 dark:border-dark-800 dark:bg-dark-900 dark:text-dark-200'"
                  @click="void openGraph(label)"
                >
                  <span class="truncate">{{ label }}</span>
                  <BaseIcon
                    name="chevron-right"
                    size="xs"
                  />
                </button>
              </div>
            </div>
          </div>

          <div
            v-if="showSettingsPanel"
            class="max-h-[360px] overflow-auto rounded-3xl border border-white/80 bg-white/90 p-4 shadow-xl backdrop-blur dark:border-dark-700 dark:bg-dark-950/88"
          >
            <div class="text-xs font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
              图谱设置
            </div>

            <div class="mt-4 grid gap-3 sm:grid-cols-2">
              <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-dark-200">
                max_depth
                <input
                  v-model.number="maxDepth"
                  min="1"
                  max="8"
                  type="number"
                  class="pw-input"
                >
              </label>
              <label class="flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-dark-200">
                max_nodes
                <input
                  v-model.number="maxNodes"
                  min="1"
                  max="2000"
                  type="number"
                  class="pw-input"
                >
              </label>
            </div>

            <label class="mt-4 flex flex-col gap-2 text-sm font-medium text-gray-700 dark:text-dark-200">
              布局
              <BaseSelect v-model="layoutMode">
                <option value="force">force</option>
                <option value="radial">radial</option>
                <option value="grid">grid</option>
              </BaseSelect>
            </label>

            <div class="mt-4 grid gap-2 text-sm text-gray-700 dark:text-dark-200">
              <label class="flex items-center gap-2">
                <input v-model="showNodeLabels" type="checkbox">
                显示节点标签
              </label>
              <label class="flex items-center gap-2">
                <input v-model="showEdgeLabels" type="checkbox">
                显示边标签
              </label>
              <label class="flex items-center gap-2">
                <input v-model="enableNodeDrag" type="checkbox">
                启用节点拖动
              </label>
            </div>

            <div class="mt-4 rounded-2xl border border-gray-100 bg-gray-50/80 px-3 py-3 text-xs text-gray-500 dark:border-dark-800 dark:bg-dark-900/70 dark:text-dark-400">
              参数修改后点“刷新”重拉子图；布局切换会直接在当前图里重新计算位置。
            </div>
          </div>
        </div>

        <div class="absolute right-4 top-16 z-30 w-[288px] max-w-[calc(100%-2rem)] space-y-3">
          <div class="max-h-[380px] overflow-auto rounded-3xl border border-white/80 bg-white/90 p-4 shadow-xl backdrop-blur dark:border-dark-700 dark:bg-dark-950/88">
            <div class="flex items-center justify-between gap-3">
              <div class="text-xs font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                节点搜索
              </div>
              <div class="text-xs text-gray-400 dark:text-dark-500">
                {{ nodeSearchMatches.length }}
              </div>
            </div>
            <div class="mt-2">
              <SearchInput
                v-model="nodeSearch"
                placeholder="搜索当前子图中的节点"
              />
            </div>

            <div class="mt-4">
              <div class="mb-2 flex items-center justify-between gap-3">
                <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                  快速定位
                </div>
                <div class="text-xs text-gray-400 dark:text-dark-500">
                  {{ quickFocusNodes.length }}
                </div>
              </div>
              <div
                v-if="quickFocusNodes.length"
                class="space-y-2"
              >
                <button
                  v-for="node in quickFocusNodes"
                  :key="node.id"
                  type="button"
                  class="flex w-full items-center justify-between gap-3 rounded-2xl border border-gray-100 px-3 py-2.5 text-left text-sm transition hover:border-primary-200 hover:text-primary-700 dark:border-dark-800 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
                  @click="focusNode(node.id)"
                >
                  <div class="min-w-0">
                    <div class="truncate font-medium">{{ node.label }}</div>
                    <div class="mt-1 text-xs text-gray-400 dark:text-dark-500">
                      {{ node.typeLabel }} · degree {{ node.degree }}
                    </div>
                  </div>
                  <BaseIcon
                    name="search"
                    size="xs"
                  />
                </button>
              </div>
              <p
                v-else
                class="text-sm text-gray-500 dark:text-dark-300"
              >
                当前没有符合搜索条件的节点。
              </p>
            </div>

            <div
              v-if="showLegend"
              class="mt-4 border-t border-gray-100 pt-4 dark:border-dark-800"
            >
              <div class="mb-2 flex items-center justify-between gap-3">
                <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                  Legend
                </div>
                <div class="text-xs text-gray-400 dark:text-dark-500">
                  {{ nodeTypeLegend.length }}
                </div>
              </div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="item in nodeTypeLegend"
                  :key="item.label"
                  class="inline-flex max-w-full items-center gap-2 rounded-full border border-gray-100 bg-gray-50/80 px-3 py-1.5 text-xs text-gray-600 dark:border-dark-800 dark:bg-dark-900/70 dark:text-dark-300"
                >
                  <span
                    class="h-2.5 w-2.5 shrink-0 rounded-full"
                    :style="{ backgroundColor: item.color }"
                  />
                  <span class="truncate">{{ item.label }}</span>
                </span>
              </div>
            </div>
          </div>

          <div
            v-if="showInspectorPanel"
            class="max-h-[420px] overflow-auto rounded-3xl border border-white/80 bg-white/90 p-4 shadow-xl backdrop-blur dark:border-dark-700 dark:bg-dark-950/88"
          >
            <div class="flex items-center justify-between gap-3">
              <div class="text-xs font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                属性面板
              </div>
              <div class="text-xs text-gray-400 dark:text-dark-500">
                {{ selectedNode ? 'selected' : 'idle' }}
              </div>
            </div>

            <template v-if="selectedNode">
              <div class="mt-3 rounded-3xl border border-primary-100 bg-primary-50/70 px-4 py-4 dark:border-primary-900/40 dark:bg-primary-950/10">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="truncate text-base font-semibold text-gray-900 dark:text-white">
                      {{ selectedNode.label }}
                    </div>
                    <div class="mt-1 text-sm text-gray-500 dark:text-dark-400">
                      {{ selectedNode.typeLabel }} · degree {{ selectedNode.degree }}
                    </div>
                  </div>
                  <span
                    class="mt-1 h-3.5 w-3.5 rounded-full"
                    :style="{ backgroundColor: nodeFillColor(selectedNode) }"
                  />
                </div>

                <div
                  v-if="selectedNodePropertyEntries.length"
                  class="mt-4 grid gap-2"
                >
                  <div
                    v-for="[key, value] in selectedNodePropertyEntries"
                    :key="key"
                    class="rounded-2xl border border-white/70 bg-white/80 px-3 py-2 text-sm dark:border-dark-700 dark:bg-dark-950/70"
                  >
                    <div class="text-[11px] uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                      {{ key }}
                    </div>
                    <div class="mt-1 break-words text-gray-700 dark:text-dark-200">
                      {{ typeof value === 'string' ? value : JSON.stringify(value) }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-4">
                <div class="mb-2 flex items-center justify-between gap-3">
                  <div class="text-[11px] font-semibold uppercase tracking-[0.12em] text-gray-400 dark:text-dark-500">
                    关联关系
                  </div>
                  <div class="text-xs text-gray-400 dark:text-dark-500">
                    {{ selectedNodeRelations.length }}
                  </div>
                </div>
                <div
                  v-if="selectedNodeRelations.length"
                  class="space-y-2"
                >
                  <button
                    v-for="relation in selectedNodeRelations"
                    :key="relation.edgeId"
                    type="button"
                    class="w-full rounded-2xl border border-gray-100 px-3 py-2.5 text-left text-sm transition hover:border-primary-200 hover:text-primary-700 dark:border-dark-800 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
                    @click="focusNode(relation.nodeId)"
                  >
                    <div class="flex items-center justify-between gap-3">
                      <span class="truncate font-medium">{{ relation.nodeLabel }}</span>
                      <span class="rounded-full border border-gray-200 px-2 py-0.5 text-[11px] text-gray-500 dark:border-dark-700 dark:text-dark-400">
                        {{ relation.direction === 'outgoing' ? 'out' : 'in' }}
                      </span>
                    </div>
                    <div class="mt-1 text-xs text-gray-400 dark:text-dark-500">
                      {{ relation.label }} · {{ relation.nodeTypeLabel }}
                    </div>
                  </button>
                </div>
              </div>

              <details class="mt-4 rounded-2xl border border-gray-100 bg-gray-50/70 px-3 py-3 dark:border-dark-800 dark:bg-dark-900/60">
                <summary class="cursor-pointer text-sm font-medium text-gray-700 dark:text-dark-200">
                  查看原始节点 JSON
                </summary>
                <pre class="mt-3 overflow-auto rounded-2xl bg-gray-950/92 p-4 text-xs leading-6 text-white dark:bg-dark-950">{{ JSON.stringify(selectedNode, null, 2) }}</pre>
              </details>
            </template>
            <p
              v-else
              class="mt-4 text-sm text-gray-500 dark:text-dark-300"
            >
              点击图中的节点，或使用节点搜索 / 快速定位后，这里会展示属性和关联关系。
            </p>
          </div>
        </div>

        <div class="absolute bottom-4 left-4 z-30 flex max-w-[calc(100%-2rem)] flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-2xl border border-white/80 bg-white/90 px-3 py-2 text-xs font-medium text-gray-700 shadow-lg backdrop-blur transition hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-200 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
            @click="adjustZoom(-0.2)"
          >
            缩小
          </button>
          <button
            type="button"
            class="rounded-2xl border border-white/80 bg-white/90 px-3 py-2 text-xs font-medium text-gray-700 shadow-lg backdrop-blur transition hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-200 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
            @click="adjustZoom(0.2)"
          >
            放大
          </button>
          <button
            type="button"
            class="rounded-2xl border border-white/80 bg-white/90 px-3 py-2 text-xs font-medium text-gray-700 shadow-lg backdrop-blur transition hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-200 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
            @click="rotateGraph(-0.4)"
          >
            左转
          </button>
          <button
            type="button"
            class="rounded-2xl border border-white/80 bg-white/90 px-3 py-2 text-xs font-medium text-gray-700 shadow-lg backdrop-blur transition hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-200 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
            @click="rotateGraph(0.4)"
          >
            右转
          </button>
          <button
            type="button"
            class="rounded-2xl border border-white/80 bg-white/90 px-3 py-2 text-xs font-medium text-gray-700 shadow-lg backdrop-blur transition hover:border-primary-300 hover:text-primary-700 dark:border-dark-700 dark:bg-dark-950/85 dark:text-dark-200 dark:hover:border-primary-900/50 dark:hover:text-primary-200"
            @click="resetViewport"
          >
            重置
          </button>
          <button
            type="button"
            class="rounded-2xl border border-primary-200 bg-primary-50 px-3 py-2 text-xs font-medium text-primary-700 shadow-lg backdrop-blur transition hover:border-primary-300 dark:border-primary-900/50 dark:bg-primary-950/20 dark:text-primary-200"
            @click="focusAll"
          >
            聚焦全部
          </button>
        </div>

        <template v-if="graphStats.nodeCount">
          <svg
            viewBox="0 0 1200 760"
            class="relative z-[1] h-full w-full cursor-grab active:cursor-grabbing"
            :style="graphTransformStyle"
            @mousedown="startPan"
            @mousemove="updatePointer"
            @mouseup="stopInteractions"
            @mouseleave="stopInteractions"
          >
            <defs>
              <filter
                id="knowledge-graph-node-shadow"
                x="-50%"
                y="-50%"
                width="200%"
                height="200%"
              >
                <feDropShadow
                  dx="0"
                  dy="8"
                  stdDeviation="8"
                  flood-color="#0f172a"
                  flood-opacity="0.14"
                />
              </filter>
              <marker
                id="knowledge-graph-arrow"
                markerWidth="8"
                markerHeight="8"
                refX="6"
                refY="3"
                orient="auto"
              >
                <path
                  d="M0,0 L0,6 L6,3 z"
                  fill="#94a3b8"
                />
              </marker>
            </defs>
            <g
              v-for="edge in graphEdges"
              :key="edge.id"
              :opacity="edgeOpacity(edge)"
            >
              <path
                :d="edgePath(edge)"
                :stroke="edgeStrokeColor(edge)"
                stroke-width="2.4"
                fill="none"
                marker-end="url(#knowledge-graph-arrow)"
              />
              <text
                v-if="showEdgeLabels"
                :x="edgeLabelPosition(edge).x"
                :y="edgeLabelPosition(edge).y"
                text-anchor="middle"
                class="fill-gray-500 text-[10px] font-medium dark:fill-dark-400"
              >
                {{ edge.label }}
              </text>
            </g>
            <g
              v-for="node in graphNodes"
              :key="node.id"
              class="cursor-pointer"
              :opacity="nodeOpacity(node)"
              @click="selectedNodeId = node.id"
              @mousedown.stop="startDrag(node.id)"
            >
              <circle
                v-if="selectedNodeId === node.id || (nodeSearchQuery && nodeSearchMatchIds.has(node.id))"
                :cx="node.x"
                :cy="node.y"
                :r="nodeRadius(node) + 12"
                :fill="nodeFillColor(node)"
                opacity="0.14"
              />
              <circle
                :cx="node.x"
                :cy="node.y"
                :r="nodeRadius(node)"
                :fill="selectedNodeId === node.id ? nodeFillColor(node) : 'white'"
                :stroke="nodeFillColor(node)"
                :stroke-width="selectedNodeId === node.id ? 3.2 : 2"
                filter="url(#knowledge-graph-node-shadow)"
              />
              <circle
                :cx="node.x"
                :cy="node.y"
                :r="Math.max(4, Math.min(8, node.degree + 2))"
                :fill="selectedNodeId === node.id ? 'white' : nodeFillColor(node)"
                opacity="0.9"
              />
              <text
                v-if="showNodeLabels"
                :x="node.x"
                :y="node.y + nodeRadius(node) + 18"
                text-anchor="middle"
                class="fill-gray-700 text-[11px] font-semibold dark:fill-dark-100"
              >
                {{ node.label }}
              </text>
              <text
                v-if="showNodeLabels"
                :x="node.x"
                :y="node.y + nodeRadius(node) + 34"
                text-anchor="middle"
                class="fill-gray-400 text-[10px] dark:fill-dark-500"
              >
                {{ node.typeLabel }}
              </text>
            </g>
          </svg>
        </template>
        <div
          v-else
          class="relative z-[1] flex h-full items-center justify-center"
        >
          <EmptyState
            title="当前标签下暂无可展示子图"
            description="可以切换到其他标签，或者提高 max_nodes / max_depth 后重新拉取。"
            icon="graph"
          />
        </div>

        <div
          v-if="loadingGraph"
          class="absolute inset-0 z-30 flex items-center justify-center bg-white/65 backdrop-blur dark:bg-dark-950/70"
        >
          <div class="rounded-2xl border border-gray-200 bg-white px-5 py-4 text-sm text-gray-600 shadow-lg dark:border-dark-700 dark:bg-dark-950 dark:text-dark-200">
            正在刷新知识图谱…
          </div>
        </div>
      </div>
    </SurfaceCard>
  </section>
</template>
