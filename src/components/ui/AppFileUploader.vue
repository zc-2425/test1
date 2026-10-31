<script setup lang="ts">
import { computed, ref } from 'vue'

/**
 * 文件上传区（拖拽 + 点击选择）。
 *
 * P4 阶段只做本地选择与列表管理，**不发请求**——后端的真实上传接口（知识库/数据集文档）
 * 在 P7 与创建页一起接；那时这个组件会多一个 `upload` 函数 prop 负责传输。
 */
const model = defineModel<File[]>({ default: () => [] })

const props = withDefaults(
  defineProps<{
    label?: string
    hint?: string
    /** 例：'.pdf,.docx' 或 'image/*' */
    accept?: string
    multiple?: boolean
    disabled?: boolean
    /** 单文件大小上限（MB） */
    maxSizeMb?: number
  }>(),
  { multiple: true, disabled: false, maxSizeMb: 50 }
)

const emit = defineEmits<{ (e: 'error', message: string): void }>()

const inputRef = ref<HTMLInputElement | null>(null)
const dragging = ref(false)

const totalSize = computed(() => model.value.reduce((sum, file) => sum + file.size, 0))

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function pick(): void {
  if (props.disabled) return
  inputRef.value?.click()
}

function acceptFiles(files: FileList | null): void {
  if (!files?.length) return
  const incoming = Array.from(files)
  const accepted: File[] = []

  for (const file of incoming) {
    if (file.size > props.maxSizeMb * 1024 * 1024) {
      emit('error', `${file.name} 超过 ${props.maxSizeMb} MB 限制`)
      continue
    }
    if (model.value.some((f) => f.name === file.name && f.size === file.size)) continue
    accepted.push(file)
  }

  model.value = props.multiple ? [...model.value, ...accepted] : accepted.slice(0, 1)
}

function onInputChange(event: Event): void {
  const input = event.target as HTMLInputElement
  acceptFiles(input.files)
  input.value = ''
}

function onDrop(event: DragEvent): void {
  dragging.value = false
  if (props.disabled) return
  acceptFiles(event.dataTransfer?.files ?? null)
}

function remove(index: number): void {
  model.value = model.value.filter((_, i) => i !== index)
}
</script>

<template>
  <div class="uploader">
    <label v-if="label" class="uploader__label">{{ label }}</label>

    <div
      class="uploader__zone"
      :class="{ 'is-dragging': dragging, 'is-disabled': disabled }"
      role="button"
      tabindex="0"
      @click="pick"
      @keydown.enter.prevent="pick"
      @keydown.space.prevent="pick"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <i class="mdi mdi-cloud-upload-outline uploader__icon" aria-hidden="true" />
      <p class="uploader__title">把文件拖到这里，或<span class="uploader__link">点击选择</span></p>
      <p class="uploader__hint">{{ hint || `支持常见文档格式，单个不超过 ${maxSizeMb} MB` }}</p>
      <input
        ref="inputRef"
        class="uploader__input"
        type="file"
        :accept="accept"
        :multiple="multiple"
        :disabled="disabled"
        @change="onInputChange"
      />
    </div>

    <ul v-if="model.length" class="uploader__list">
      <li v-for="(file, index) in model" :key="`${file.name}-${file.size}`" class="uploader__item">
        <i class="mdi mdi-file-document-outline" aria-hidden="true" />
        <span class="uploader__name">{{ file.name }}</span>
        <span class="uploader__size">{{ formatSize(file.size) }}</span>
        <button
          type="button"
          class="uploader__remove"
          :aria-label="`移除 ${file.name}`"
          @click="remove(index)"
        >
          <i class="mdi mdi-close" aria-hidden="true" />
        </button>
      </li>
      <li v-if="model.length > 1" class="uploader__total">
        共 {{ model.length }} 个文件 / {{ formatSize(totalSize) }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.uploader {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  min-width: 0;
}

.uploader__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.uploader__zone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: var(--spacing-6) var(--spacing-4);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-low);
  cursor: pointer;
  text-align: center;
  transition:
    border-color var(--motion-fast) var(--motion-ease),
    background-color var(--motion-fast) var(--motion-ease);
}

.uploader__zone:hover,
.uploader__zone.is-dragging {
  border-color: var(--color-primary);
  background: rgba(103, 80, 164, 0.05);
}

.uploader__zone.is-dragging {
  border-style: solid;
}

.uploader__zone.is-disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.uploader__icon {
  font-size: 28px;
  color: var(--color-primary);
}

.uploader__title {
  font: var(--font-body-md);
  color: var(--color-text);
}

.uploader__link {
  color: var(--color-primary);
  font-weight: 500;
}

.uploader__hint {
  font: var(--font-label-sm);
  color: var(--color-text-tertiary);
}

.uploader__input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.uploader__list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.uploader__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: 6px var(--spacing-3);
  border: 1px solid var(--color-divider);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  font: var(--font-body-sm);
  color: var(--color-text-secondary);
}

.uploader__item .mdi {
  font-size: 16px;
  color: var(--color-text-tertiary);
}

.uploader__name {
  flex: 1 1 auto;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.uploader__size {
  flex: 0 0 auto;
  font-size: 12px;
  color: var(--color-text-tertiary);
}

.uploader__remove {
  flex: 0 0 auto;
  width: 20px;
  height: 20px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-text-tertiary);
  font-size: 14px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.uploader__remove:hover {
  background: var(--status-danger-bg);
  color: var(--status-danger);
}

.uploader__total {
  font-size: 12px;
  color: var(--color-text-tertiary);
  text-align: right;
}
</style>
