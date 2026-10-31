<script setup lang="ts">
import { computed } from 'vue'
import AppButton from './AppButton.vue'
import AppModal from './AppModal.vue'
import { settleConfirm, useConfirmState } from '@/composables/useConfirm'

const state = useConfirmState()

/** 双向绑定到 v-dialog：点遮罩或按 Esc = 取消 */
const open = computed({
  get: () => state.open,
  set: (value: boolean) => {
    if (!value) settleConfirm(false)
  }
})
</script>

<template>
  <AppModal v-model="open" :title="state.title" :max-width="420" hide-close>
    <p v-if="state.description" class="confirm__desc">{{ state.description }}</p>
    <template #footer>
      <AppButton variant="secondary" size="sm" @click="settleConfirm(false)">
        {{ state.cancelText }}
      </AppButton>
      <AppButton :variant="state.tone === 'danger' ? 'danger' : 'primary'" size="sm" @click="settleConfirm(true)">
        {{ state.confirmText }}
      </AppButton>
    </template>
  </AppModal>
</template>

<style scoped>
.confirm__desc {
  font: var(--font-body-md);
  color: var(--color-text-secondary);
  line-height: 22px;
}
</style>
