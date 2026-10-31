<script setup lang="ts">
import { AppConfirmHost, AppToastHost } from '@/components/ui'
</script>

<template>
  <v-app>
    <RouterView />
    <!-- 全局反馈宿主：toast() / confirm() 是命令式调用，渲染锚点在这里 -->
    <AppToastHost />
    <AppConfirmHost />
  </v-app>
</template>
