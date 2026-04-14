<template>
  <router-link :to="to"
    class="flex items-center gap-3 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-elevated transition text-sm font-medium"
    active-class="text-white bg-surface-elevated !text-brand-400">
    <span>{{ icon }}</span>
    <slot />
  </router-link>
</template>

<script setup>
defineProps(['to', 'icon'])
</script>
