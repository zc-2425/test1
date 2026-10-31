<script setup lang="ts">
/**
 * 文本输入：包 v-text-field，统一成 M3 outlined + 必填星号 + 错误提示。
 *
 * 为什么包而不是自绘：校验态、输入法组合事件、可访问性（aria-invalid / aria-describedby）、
 * 浮动标签动画这些脏活 Vuetify 已经做对了；主题在 P2 已配成 outlined + density comfortable，
 * 视觉和原型一致。样式微调只在下面 :deep() 里做。
 *
 * 其余属性（rules / maxlength / clearable / prefix / mask …）通过 $attrs 透传，
 * 不在这里逐个列举——列举会立刻过时。
 */
defineOptions({ inheritAttrs: false })

const model = defineModel<string | number | null>({ default: '' })

withDefaults(
  defineProps<{
    label?: string
    placeholder?: string
    hint?: string
    error?: string
    required?: boolean
    disabled?: boolean
    readonly?: boolean
    type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url'
    /** 左侧内嵌图标，如 mdi-email-outline */
    prefixIcon?: string
    /** 右侧内嵌图标（点击事件需要页面自己绑 #append） */
    suffixIcon?: string
    autofocus?: boolean
    /** 紧凑高度，筛选条里用 */
    dense?: boolean
  }>(),
  { type: 'text', dense: false }
)
</script>

<template>
  <div class="app-text-field" :class="{ 'is-dense': dense }">
    <label v-if="label" class="app-text-field__label">
      {{ label }}
      <span v-if="required" class="app-text-field__required">*</span>
    </label>
    <v-text-field
      v-model="model"
      v-bind="$attrs"
      :variant="'outlined'"
      :density="dense ? 'compact' : 'comfortable'"
      :type="type"
      :placeholder="placeholder"
      :prepend-inner-icon="prefixIcon"
      :append-inner-icon="suffixIcon"
      :disabled="disabled"
      :readonly="readonly"
      :autofocus="autofocus"
      :error-messages="error || undefined"
      :hint="hint"
      :persistent-hint="!!hint"
      hide-details="auto"
      color="primary"
    >
      <template v-for="(_, name) in $slots" #[name]="slotProps">
        <slot :name="name" v-bind="slotProps ?? {}" />
      </template>
    </v-text-field>
  </div>
</template>

<style scoped>
.app-text-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.app-text-field__label {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-secondary);
}

.app-text-field__required {
  color: var(--status-danger);
  margin-left: 2px;
}

.app-text-field :deep(.v-field) {
  border-radius: var(--radius-sm);
}

.app-text-field :deep(.v-field__input) {
  font-size: 13px;
  min-height: 40px;
}

.app-text-field.is-dense :deep(.v-field__input) {
  min-height: 34px;
  font-size: 12.5px;
}

.app-text-field :deep(.v-field__prepend-inner .v-icon),
.app-text-field :deep(.v-field__append-inner .v-icon) {
  font-size: 18px;
  color: var(--color-text-tertiary);
}

.app-text-field :deep(.v-messages__message) {
  font-size: 12px;
  line-height: 16px;
  color: var(--color-text-tertiary);
}
</style>
