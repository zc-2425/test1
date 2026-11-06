<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  AppButton,
  AppEmptyState,
  AppModal,
  AppSelect,
  AppSlider,
  AppTagInput,
  AppTextarea,
  AppTextField
} from '@/components/ui'
import { workflowsApi } from '@/api/resources'
import { getWorkflowGraph, runWorkflow, saveWorkflowGraph, type RunResult } from '@/api/workflows'
import type { WorkflowDto } from '@/api/types'
import { useResource } from '@/composables/useResource'
import { toast } from '@/composables/useToast'
import { confirm } from '@/composables/useConfirm'
import {
  NODE_HEIGHT,
  NODE_META_MAP,
  NODE_TYPES,
  NODE_WIDTH,
  defaultConfigFor,
  type CanvasEdge,
  type CanvasNode,
  type NodeField
} from './nodeSchemas'

/**
 * 工作流画布（原型 03-工作流-节点库-*.png）。
 *
 * 这是整个项目唯一没有现成组件能直接套的地方，所以全部自己实现：
 * - 平移：在画布空白处 pointerdown + move 改 offset
 * - 缩放：滚轮改 scale（0.4 ~ 1.6），以光标为锚点
 * - 拖节点：pointerdown 在节点上，位移除以 scale 才是画布坐标
 * - 连线：从节点右侧圆点 pointerdown 拉出临时线，pointerup 落在另一个节点上则建边
 * - 属性面板：nodeType → 字段 schema 驱动，10 种节点各不相同
 *
 * 没引 @vue-flow/core 的理由：它自带一套节点模型与样式系统，和现有 M3 视觉对齐成本高；
 * 而练手项目的价值恰恰在于把这套交互自己写一遍。
 */
const route = useRoute()
const router = useRouter()
const workflowId = String(route.params.id ?? '')

const {
  data: workflow,
  error,
  notFound
} = useResource<WorkflowDto>(() => workflowsApi.get(workflowId))

const canvasRef = ref<HTMLElement | null>(null)
const nodes = ref<CanvasNode[]>([])
const edges = ref<CanvasEdge[]>([])
const selectedId = ref<string | null>(null)
const scale = ref(1)
const offset = reactive({ x: 40, y: 40 })

const runOpen = ref(false)
const running = ref(false)
const saving = ref(false)
const runInput = ref('你们的退款政策是什么？')
const runResult = ref<RunResult | null>(null)

let nodeSeq = 0

function nextNodeId(): string {
  nodeSeq += 1
  return `n${nodeSeq}`
}

/** 用工作流的 node_count 造一条初始链路：开始 → 若干处理节点 → 结束 */
function seedNodes(count: number): void {
  const total = Math.max(2, count)
  const middles = ['llm', 'retrieval', 'agent', 'transform', 'condition', 'code', 'http', 'qa']
  const types = [
    'start',
    ...Array.from({ length: total - 2 }, (_, i) => middles[i % middles.length]),
    'end'
  ]
  nodeSeq = 0
  nodes.value = types.map((type, index) => ({
    id: nextNodeId(),
    type,
    x: 120,
    y: 40 + index * 104,
    config: defaultConfigFor(type)
  }))
  edges.value = nodes.value.slice(0, -1).map((node, index) => ({
    id: `e${index + 1}`,
    from: node.id,
    to: nodes.value[index + 1].id
  }))
}

/**
 * 打开画布时读库里的图；库里还没有节点才用 node_count 造一条临时链路。
 * R4 之前这里是纯前端内存，刷新就丢。
 */
const graphLoading = ref(false)

async function loadGraph(): Promise<void> {
  graphLoading.value = true
  try {
    const graph = await getWorkflowGraph(workflowId)
    if (graph.nodes.length) {
      nodes.value = graph.nodes.map((node) => ({
        id: node.id,
        type: node.type,
        x: node.x,
        y: node.y,
        label: node.name || undefined,
        config: node.config
      }))
      edges.value = graph.edges.map((edge) => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label || undefined
      }))
      // 让新建节点从已有 id 之后接着编号，避免撞名
      nodeSeq = nodes.value.length
    } else if (workflow.value && !nodes.value.length) {
      seedNodes(workflow.value.node_count)
    }
  } catch (cause) {
    toast('画布加载失败', { tone: 'error', description: String(cause) })
  } finally {
    graphLoading.value = false
  }
}

watch(workflow, (value) => {
  if (value) void loadGraph()
  if (route.query.run === '1') runOpen.value = true
})

/* ---------------- 坐标 ---------------- */
function toCanvas(clientX: number, clientY: number): { x: number; y: number } {
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return { x: 0, y: 0 }
  return {
    x: (clientX - rect.left - offset.x) / scale.value,
    y: (clientY - rect.top - offset.y) / scale.value
  }
}

/** 出线点在节点底部中点，入线点在下一个节点顶部中点 —— 竖向流程要这么连才不打架 */
function nodeBottom(node: CanvasNode): { x: number; y: number } {
  return { x: node.x + NODE_WIDTH / 2, y: node.y + NODE_HEIGHT }
}

function nodeTop(node: CanvasNode): { x: number; y: number } {
  return { x: node.x + NODE_WIDTH / 2, y: node.y }
}

/** 竖向贝塞尔：控制点沿 y 方向拉开，画出来是平滑的父子连接线 */
function edgePath(from: CanvasNode, to: CanvasNode): string {
  const start = nodeBottom(from)
  const end = nodeTop(to)
  const dy = Math.max(30, Math.abs(end.y - start.y) / 2)
  return `M ${start.x} ${start.y} C ${start.x} ${start.y + dy}, ${end.x} ${end.y - dy}, ${end.x} ${end.y}`
}

/* ---------------- 画布平移 ---------------- */
const panning = ref(false)
let panStart = { x: 0, y: 0, ox: 0, oy: 0 }

function onCanvasPointerDown(event: PointerEvent): void {
  if (event.button !== 0) return
  selectedId.value = null
  panning.value = true
  panStart = { x: event.clientX, y: event.clientY, ox: offset.x, oy: offset.y }
  window.addEventListener('pointermove', onPanMove)
  window.addEventListener('pointerup', onPanEnd)
}

function onPanMove(event: PointerEvent): void {
  if (!panning.value) return
  offset.x = panStart.ox + (event.clientX - panStart.x)
  offset.y = panStart.oy + (event.clientY - panStart.y)
}

function onPanEnd(): void {
  panning.value = false
  window.removeEventListener('pointermove', onPanMove)
  window.removeEventListener('pointerup', onPanEnd)
}

function onWheel(event: WheelEvent): void {
  event.preventDefault()
  const before = toCanvas(event.clientX, event.clientY)
  const next = Math.min(1.6, Math.max(0.4, scale.value + (event.deltaY > 0 ? -0.1 : 0.1)))
  scale.value = Number(next.toFixed(2))
  const rect = canvasRef.value?.getBoundingClientRect()
  if (!rect) return
  // 缩放后保持光标下的画布点不动
  offset.x = event.clientX - rect.left - before.x * scale.value
  offset.y = event.clientY - rect.top - before.y * scale.value
}

/* ---------------- 拖节点 ---------------- */
const dragging = ref<string | null>(null)
let dragStart = { x: 0, y: 0, nx: 0, ny: 0 }

function onNodePointerDown(event: PointerEvent, node: CanvasNode): void {
  event.stopPropagation()
  selectedId.value = node.id
  dragging.value = node.id
  dragStart = { x: event.clientX, y: event.clientY, nx: node.x, ny: node.y }
  window.addEventListener('pointermove', onNodeMove)
  window.addEventListener('pointerup', onNodeEnd)
}

function onNodeMove(event: PointerEvent): void {
  if (!dragging.value) return
  const node = nodes.value.find((item) => item.id === dragging.value)
  if (!node) return
  node.x = dragStart.nx + (event.clientX - dragStart.x) / scale.value
  node.y = dragStart.ny + (event.clientY - dragStart.y) / scale.value
}

function onNodeEnd(): void {
  dragging.value = null
  window.removeEventListener('pointermove', onNodeMove)
  window.removeEventListener('pointerup', onNodeEnd)
}

/* ---------------- 连线 ---------------- */
const linking = reactive({ active: false, from: '', x: 0, y: 0 })

function onPortPointerDown(event: PointerEvent, node: CanvasNode): void {
  event.stopPropagation()
  linking.active = true
  linking.from = node.id
  const point = toCanvas(event.clientX, event.clientY)
  linking.x = point.x
  linking.y = point.y
  window.addEventListener('pointermove', onLinkMove)
  window.addEventListener('pointerup', onLinkEnd)
}

function onLinkMove(event: PointerEvent): void {
  if (!linking.active) return
  const point = toCanvas(event.clientX, event.clientY)
  linking.x = point.x
  linking.y = point.y
}

function onLinkEnd(event: PointerEvent): void {
  if (linking.active) {
    const target = (
      document.elementFromPoint(event.clientX, event.clientY) as HTMLElement | null
    )?.closest('[data-node-id]')
    const targetId = target?.getAttribute('data-node-id')
    if (targetId && targetId !== linking.from) {
      const exists = edges.value.some((edge) => edge.from === linking.from && edge.to === targetId)
      if (!exists) {
        edges.value.push({ id: `e${Date.now()}`, from: linking.from, to: targetId })
        toast('已连接', { tone: 'success', description: '节点之间建立了一条边' })
      }
    }
  }
  linking.active = false
  window.removeEventListener('pointermove', onLinkMove)
  window.removeEventListener('pointerup', onLinkEnd)
}

/** 临时连线（拖拽中的那条虚线） */
const tempPath = computed(() => {
  if (!linking.active) return ''
  const from = nodes.value.find((node) => node.id === linking.from)
  if (!from) return ''
  const start = nodeBottom(from)
  const dy = Math.max(30, Math.abs(linking.y - start.y) / 2)
  return `M ${start.x} ${start.y} C ${start.x} ${start.y + dy}, ${linking.x} ${linking.y - dy}, ${linking.x} ${linking.y}`
})

/* ---------------- 增删节点 ---------------- */
function addNode(type: string): void {
  const rect = canvasRef.value?.getBoundingClientRect()
  const center = rect
    ? toCanvas(rect.left + rect.width / 2, rect.top + rect.height / 2)
    : { x: 200, y: 200 }
  const node: CanvasNode = {
    id: nextNodeId(),
    type,
    x: center.x - NODE_WIDTH / 2,
    y: center.y - NODE_HEIGHT / 2,
    config: defaultConfigFor(type)
  }
  nodes.value.push(node)
  selectedId.value = node.id
}

function selectNode(id: string): void {
  selectedId.value = id
}

const selectedNode = computed(
  () => nodes.value.find((node) => node.id === selectedId.value) ?? null
)
const selectedMeta = computed(() =>
  selectedNode.value ? NODE_META_MAP[selectedNode.value.type] : null
)

function deleteSelected(): void {
  const id = selectedId.value
  if (!id) return
  nodes.value = nodes.value.filter((node) => node.id !== id)
  edges.value = edges.value.filter((edge) => edge.from !== id && edge.to !== id)
  selectedId.value = null
}

function autoLayout(): void {
  nodes.value.forEach((node, index) => {
    node.x = 120
    node.y = 40 + index * 104
  })
  toast('已重新布局', { tone: 'info' })
}

function zoomBy(delta: number): void {
  scale.value = Number(Math.min(1.6, Math.max(0.4, scale.value + delta)).toFixed(2))
}

function resetView(): void {
  scale.value = 1
  offset.x = 40
  offset.y = 40
}

function onKeydown(event: KeyboardEvent): void {
  if ((event.key === 'Delete' || event.key === 'Backspace') && selectedId.value) {
    const target = event.target as HTMLElement
    // 输入框里按退格不能删节点
    if (['INPUT', 'TEXTAREA'].includes(target.tagName)) return
    event.preventDefault()
    deleteSelected()
  }
}

window.addEventListener('keydown', onKeydown)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('pointermove', onPanMove)
  window.removeEventListener('pointerup', onPanEnd)
  window.removeEventListener('pointermove', onNodeMove)
  window.removeEventListener('pointerup', onNodeEnd)
  window.removeEventListener('pointermove', onLinkMove)
  window.removeEventListener('pointerup', onLinkEnd)
})

/* ---------------- 属性面板 ---------------- */
function fieldValue(field: NodeField): unknown {
  return selectedNode.value?.config[field.key] ?? field.defaultValue ?? ''
}

function setField(field: NodeField, value: unknown): void {
  if (!selectedNode.value) return
  selectedNode.value.config[field.key] = value
}

const nodeLabel = computed(() => {
  const node = selectedNode.value
  if (!node) return ''
  return node.label ?? NODE_META_MAP[node.type]?.label ?? node.type
})

/* ---------------- 运行 ---------------- */
async function runNow(): Promise<void> {
  if (running.value) return
  running.value = true
  runResult.value = null
  try {
    runResult.value = await runWorkflow(workflowId, runInput.value)
  } catch (cause) {
    toast('运行失败', { tone: 'error', description: String(cause) })
  } finally {
    running.value = false
  }
}

async function saveCanvas(): Promise<void> {
  // R4：整图落库（节点配置 + 连线一起），node_count 由后端按实际节点数回写
  saving.value = true
  try {
    const result = await saveWorkflowGraph(workflowId, {
      nodes: nodes.value.map((node) => ({
        id: node.id,
        type: node.type,
        name: node.label ?? '',
        x: node.x,
        y: node.y,
        config: node.config
      })),
      edges: edges.value.map((edge) => ({
        id: edge.id,
        from: edge.from,
        to: edge.to,
        label: edge.label ?? ''
      }))
    })
    toast('已保存', { tone: 'success', description: `${result.nodes} 个节点 / ${result.edges} 条连线` })
  } catch (cause) {
    toast('保存失败', { tone: 'error', description: String(cause) })
  } finally {
    saving.value = false
  }
}

async function publish(): Promise<void> {
  const ok = await confirm({
    title: '发布这个工作流？',
    description: '发布后可以被应用与 Agent 引用。',
    confirmText: '发布'
  })
  if (!ok) return
  try {
    await workflowsApi.update(workflowId, { status: '已发布' })
    toast('已发布', { tone: 'success' })
  } catch (cause) {
    toast('发布失败', { tone: 'error', description: String(cause) })
  }
}
</script>

<template>
  <div class="canvas-page">
    <AppEmptyState
      v-if="notFound"
      icon="mdi-sitemap-outline"
      title="这个工作流不存在"
      description="它可能已被删除，或者链接里的 ID 不对"
    >
      <template #action>
        <AppButton size="sm" icon="mdi-arrow-left" @click="router.push('/workflow/list')">
          返回列表
        </AppButton>
      </template>
    </AppEmptyState>

    <template v-else>
      <!-- 工具栏（画布页没有侧栏，这里充当页头） -->
      <header class="canvas-toolbar">
        <button type="button" class="canvas-toolbar__back" @click="router.push('/workflow/list')">
          <i class="mdi mdi-arrow-left" aria-hidden="true" />
        </button>
        <div class="canvas-toolbar__title">
          <span class="canvas-toolbar__name">{{ workflow?.name ?? '加载中…' }}</span>
          <span class="canvas-toolbar__meta">
            {{ nodes.length }} 个节点 · {{ edges.length }} 条连线 · {{ Math.round(scale * 100) }}%
          </span>
        </div>
        <div class="canvas-toolbar__actions">
          <AppButton variant="secondary" size="sm" icon="mdi-auto-fix" @click="autoLayout">
            自动布局
          </AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-magnify-minus" @click="zoomBy(-0.1)">
            缩小
          </AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-magnify-plus" @click="zoomBy(0.1)">
            放大
          </AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-content-save" @click="saveCanvas">
            保存
          </AppButton>
          <AppButton variant="secondary" size="sm" icon="mdi-upload" @click="publish"
            >发布</AppButton
          >
          <AppButton size="sm" icon="mdi-play" @click="runOpen = true">运行</AppButton>
        </div>
      </header>

      <p v-if="error" class="u-page__error">{{ error }}</p>

      <div class="canvas-body">
        <!-- 节点库 -->
        <aside class="node-library">
          <h2 class="node-library__title">节点库</h2>
          <button
            v-for="meta in NODE_TYPES"
            :key="meta.type"
            type="button"
            class="node-library__item"
            :title="meta.description"
            @click="addNode(meta.type)"
          >
            <i :class="['mdi', meta.icon]" aria-hidden="true" />
            <span>{{ meta.label }}</span>
            <i class="mdi mdi-plus node-library__plus" aria-hidden="true" />
          </button>
          <p class="node-library__hint">点击添加；拖动节点、从右侧圆点连线</p>
        </aside>

        <!-- 画布 -->
        <div
          ref="canvasRef"
          class="canvas-area"
          :class="{ 'is-panning': panning }"
          @pointerdown="onCanvasPointerDown"
          @wheel="onWheel"
        >
          <div
            class="canvas-layer"
            :style="{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }"
          >
            <svg class="canvas-edges" width="4000" height="3000" aria-hidden="true">
              <path
                v-for="edge in edges"
                :key="edge.id"
                :d="
                  edgePath(
                    nodes.find((n) => n.id === edge.from)!,
                    nodes.find((n) => n.id === edge.to)!
                  )
                "
                class="canvas-edge"
              />
              <path v-if="linking.active" :d="tempPath" class="canvas-edge is-temp" />
            </svg>

            <div
              v-for="node in nodes"
              :key="node.id"
              :data-node-id="node.id"
              class="canvas-node"
              :class="[
                `is-${NODE_META_MAP[node.type]?.tone ?? 'process'}`,
                { 'is-selected': node.id === selectedId }
              ]"
              :style="{ left: `${node.x}px`, top: `${node.y}px` }"
              @pointerdown="onNodePointerDown($event, node)"
              @click.stop="selectNode(node.id)"
            >
              <i
                :class="['mdi', NODE_META_MAP[node.type]?.icon ?? 'mdi-circle']"
                aria-hidden="true"
              />
              <span class="canvas-node__label">{{
                node.label ?? NODE_META_MAP[node.type]?.label
              }}</span>
              <span class="canvas-node__port is-in" />
              <span
                class="canvas-node__port is-out"
                title="拖动连线"
                @pointerdown.stop="onPortPointerDown($event, node)"
              />
            </div>
          </div>

          <div class="canvas-area__hint">
            <span>滚轮缩放 · 空白处拖动平移 · 节点右侧圆点拖出连线 · Delete 删除</span>
            <button type="button" class="canvas-area__reset" @click="resetView">复位视图</button>
          </div>
        </div>

        <!-- 属性面板 -->
        <aside class="node-panel">
          <template v-if="selectedNode && selectedMeta">
            <header class="node-panel__head">
              <div class="node-panel__title">
                <i :class="['mdi', selectedMeta.icon]" aria-hidden="true" />
                <span>{{ nodeLabel }}</span>
              </div>
              <button
                type="button"
                class="node-panel__delete"
                title="删除节点"
                @click="deleteSelected"
              >
                <i class="mdi mdi-trash-can-outline" aria-hidden="true" />
              </button>
            </header>

            <p class="node-panel__desc">{{ selectedMeta.description }}</p>

            <div class="node-panel__fields">
              <div v-for="field in selectedMeta.fields" :key="field.key">
                <AppTextField
                  v-if="field.control === 'text'"
                  :model-value="String(fieldValue(field) ?? '')"
                  :label="field.label"
                  :placeholder="field.placeholder"
                  :hint="field.hint"
                  dense
                  @update:model-value="(value) => setField(field, value)"
                />

                <AppTextarea
                  v-else-if="field.control === 'textarea'"
                  :model-value="String(fieldValue(field) ?? '')"
                  :label="field.label"
                  :rows="field.rows ?? 3"
                  :placeholder="field.placeholder"
                  :hint="field.hint"
                  @update:model-value="(value) => setField(field, value)"
                />

                <textarea
                  v-else-if="field.control === 'code'"
                  class="node-panel__code"
                  :rows="field.rows ?? 5"
                  :value="String(fieldValue(field) ?? '')"
                  spellcheck="false"
                  @input="setField(field, ($event.target as HTMLTextAreaElement).value)"
                />

                <AppSelect
                  v-else-if="field.control === 'select'"
                  :model-value="String(fieldValue(field) ?? '') || null"
                  :label="field.label"
                  :items="field.options ?? []"
                  :hint="field.hint"
                  dense
                  @update:model-value="(value) => setField(field, value)"
                />

                <AppSlider
                  v-else-if="field.control === 'slider'"
                  :model-value="Number(fieldValue(field) ?? 0)"
                  :label="field.label"
                  :min="field.min ?? 0"
                  :max="field.max ?? 1"
                  :step="field.step ?? 0.1"
                  :hint="field.hint"
                  @update:model-value="(value) => setField(field, value)"
                />

                <AppTextField
                  v-else-if="field.control === 'number'"
                  :model-value="String(fieldValue(field) ?? '')"
                  :label="field.label"
                  type="number"
                  dense
                  @update:model-value="(value) => setField(field, Number(value))"
                />

                <AppTagInput
                  v-else-if="field.control === 'tags'"
                  :model-value="(fieldValue(field) as string[]) ?? []"
                  :label="field.label"
                  :hint="field.hint"
                  :max="8"
                  @update:model-value="(value) => setField(field, value)"
                />
              </div>
            </div>

            <p class="node-panel__id">
              节点 ID：<code>{{ selectedNode.id }}</code>
            </p>
          </template>

          <AppEmptyState
            v-else
            size="sm"
            icon="mdi-cursor-default-click-outline"
            title="未选中节点"
            description="点画布上的节点查看并编辑它的配置"
          />
        </aside>
      </div>

      <!-- 运行弹窗 -->
      <AppModal
        v-model="runOpen"
        title="运行工作流"
        subtitle="输入一段内容，查看每个节点的执行情况"
        :max-width="720"
      >
        <div class="run-modal">
          <AppTextarea v-model="runInput" label="输入" :rows="2" />
          <div class="run-modal__actions">
            <AppButton size="sm" icon="mdi-play" :loading="running" @click="runNow">运行</AppButton>
            <span v-if="runResult" class="run-modal__summary">
              {{ runResult.steps.length }} 步 · {{ runResult.durationMs }} ms ·
              {{ runResult.tokens.prompt }} → {{ runResult.tokens.completion }} tokens
            </span>
          </div>

          <div v-if="runResult" class="run-steps">
            <div v-for="step in runResult.steps" :key="step.nodeId" class="run-step">
              <span class="run-step__dot" />
              <div class="run-step__body">
                <div class="run-step__head">
                  <span class="run-step__name">{{ step.name }}</span>
                  <span class="run-step__meta">
              {{ step.nodeType }} · {{ step.durationMs }} ms
              <template v-if="step.mode">· {{ step.mode === 'real' ? '真实调用' : '模拟' }}</template>
              <template v-if="step.status !== '成功'">· {{ step.status }}</template>
            </span>
                </div>
                <p v-if="step.output" class="run-step__output">{{ step.output }}</p>
              </div>
            </div>
            <p class="run-steps__result">{{ runResult.output }}</p>
          </div>
          <div v-else class="run-modal__placeholder">点击运行按钮查看结果…</div>
        </div>
        <template #footer>
          <AppButton variant="secondary" size="sm" @click="runOpen = false">关闭</AppButton>
          <AppButton size="sm" :loading="running" @click="runNow">运行</AppButton>
        </template>
      </AppModal>
    </template>
  </div>
</template>

<style scoped>
.canvas-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.canvas-toolbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-2) var(--spacing-4);
  border-bottom: var(--border-width) solid var(--color-border);
  background: var(--color-surface);
}

.canvas-toolbar__back {
  width: 30px;
  height: 30px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 18px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.canvas-toolbar__back:hover {
  background: var(--color-surface-container);
}

.canvas-toolbar__title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1 1 auto;
}

.canvas-toolbar__name {
  font: var(--font-title-md);
  color: var(--color-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.canvas-toolbar__meta {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.canvas-toolbar__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  flex: 0 0 auto;
}

.canvas-body {
  flex: 1 1 auto;
  display: flex;
  min-height: 0;
}

/* ---- 节点库 ---- */
.node-library {
  flex: 0 0 auto;
  width: 152px;
  padding: var(--spacing-3);
  border-right: var(--border-width) solid var(--color-border);
  background: var(--color-sidebar-bg);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.node-library__title {
  font: var(--font-label-md);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-2);
  padding-left: var(--spacing-2);
}

.node-library__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: 8px var(--spacing-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
}

.node-library__item:hover {
  background: var(--color-surface-container);
  color: var(--color-primary);
}

.node-library__item .mdi {
  font-size: 16px;
}

.node-library__plus {
  margin-left: auto;
  opacity: 0;
  font-size: 14px;
}

.node-library__item:hover .node-library__plus {
  opacity: 1;
}

.node-library__hint {
  margin-top: auto;
  padding: var(--spacing-2);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  line-height: 18px;
}

/* ---- 画布 ---- */
.canvas-area {
  position: relative;
  flex: 1 1 auto;
  min-width: 0;
  overflow: hidden;
  cursor: grab;
  background-color: var(--color-bg);
  background-image: radial-gradient(var(--color-surface-variant) 1px, transparent 1px);
  background-size: 16px 16px;
}

.canvas-area.is-panning {
  cursor: grabbing;
}

.canvas-layer {
  position: absolute;
  left: 0;
  top: 0;
  transform-origin: 0 0;
  width: 4000px;
  height: 3000px;
}

.canvas-edges {
  position: absolute;
  left: 0;
  top: 0;
  overflow: visible;
  pointer-events: none;
}

.canvas-edge {
  fill: none;
  stroke: var(--color-border);
  stroke-width: 2;
}

.canvas-edge.is-temp {
  stroke: var(--color-primary);
  stroke-dasharray: 6 4;
}

.canvas-node {
  position: absolute;
  width: 168px;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 var(--spacing-3);
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: 13px;
  cursor: move;
  user-select: none;
}

.canvas-node.is-terminal {
  border-left-color: var(--status-success);
}

.canvas-node.is-process {
  border-left-color: var(--color-primary);
}

.canvas-node.is-branch {
  border-left-color: var(--status-warning);
}

.canvas-node.is-selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(103, 80, 164, 0.24);
}

.canvas-node .mdi {
  font-size: 16px;
  color: var(--color-primary);
}

.canvas-node__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.canvas-node__port {
  position: absolute;
  top: 50%;
  width: 10px;
  height: 10px;
  margin-top: -5px;
  border-radius: 50%;
  border: 2px solid var(--color-surface);
  background: var(--color-border);
}

.canvas-node__port.is-in {
  left: 50%;
  top: -6px;
  margin-left: -5px;
  margin-top: 0;
}

.canvas-node__port.is-out {
  left: 50%;
  top: auto;
  bottom: -6px;
  margin-left: -5px;
  margin-top: 0;
  cursor: crosshair;
}

.canvas-node__port.is-out:hover {
  background: var(--color-primary);
}

.canvas-area__hint {
  position: absolute;
  left: var(--spacing-3);
  bottom: var(--spacing-3);
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: 6px var(--spacing-3);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.86);
  border: var(--border-width) solid var(--color-divider);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.canvas-area__reset {
  border: 0;
  background: transparent;
  color: var(--color-primary);
  font-family: inherit;
  font-size: 12px;
  cursor: pointer;
}

/* ---- 属性面板 ---- */
.node-panel {
  flex: 0 0 auto;
  width: 300px;
  padding: var(--spacing-3);
  border-left: var(--border-width) solid var(--color-border);
  background: var(--color-surface);
  overflow-y: auto;
}

.node-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-2);
}

.node-panel__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font: var(--font-title-md);
  color: var(--color-text);
}

.node-panel__title .mdi {
  color: var(--color-primary);
  font-size: 16px;
}

.node-panel__delete {
  width: 26px;
  height: 26px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 16px;
  cursor: pointer;
}

.node-panel__delete:hover {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}

.node-panel__desc {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  line-height: 18px;
  margin-bottom: var(--spacing-3);
}

.node-panel__fields {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.node-panel__code {
  width: 100%;
  padding: var(--spacing-2);
  border: var(--border-width) solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface-low);
  font-family: var(--font-family-mono);
  font-size: 12px;
  line-height: 20px;
  resize: vertical;
}

.node-panel__id {
  margin-top: var(--spacing-4);
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.node-panel__id code {
  font-family: var(--font-family-mono);
}

/* ---- 运行弹窗 ---- */
.run-modal {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.run-modal__actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.run-modal__summary {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.run-modal__placeholder {
  min-height: 96px;
  padding: var(--spacing-3);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface-low);
  font: var(--font-body-sm);
  color: var(--color-text-tertiary);
}

.run-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  max-height: 320px;
  overflow-y: auto;
}

.run-step {
  display: flex;
  gap: var(--spacing-2);
  align-items: flex-start;
}

.run-step__dot {
  flex: 0 0 auto;
  width: 8px;
  height: 8px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--status-success);
}

.run-step__body {
  min-width: 0;
  flex: 1 1 auto;
}

.run-step__head {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-2);
}

.run-step__name {
  font: var(--font-body-md);
  color: var(--color-text);
}

.run-step__meta {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.run-step__output {
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.run-steps__result {
  margin-top: var(--spacing-2);
  padding: var(--spacing-3);
  border-radius: var(--radius-sm);
  background: var(--color-primary-tint);
  font: var(--font-body-md);
  color: var(--color-text);
}
</style>