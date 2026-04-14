<template>
  <div class="flex h-screen overflow-hidden bg-surface text-slate-200">
    <!-- Sidebar -->
    <aside class="w-56 flex-shrink-0 bg-surface-card flex flex-col border-r border-slate-800">
      <div class="px-5 py-5 flex items-center gap-2">
        <span class="text-2xl">🎵</span>
        <span class="font-bold text-white text-lg">Фонотека</span>
      </div>

      <nav class="flex-1 px-3 space-y-1">
        <NavLink to="/catalog" icon="🔍">Каталог</NavLink>
        <NavLink to="/library" icon="📚">Моя фонотека</NavLink>
        <NavLink to="/playlists" icon="🎶">Плейлисты</NavLink>
        <NavLink to="/recommendations" icon="✨">Рекомендации</NavLink>
        <NavLink to="/assistant" icon="🤖">ИИ-ассистент</NavLink>
      </nav>

      <div class="p-4 border-t border-slate-800">
        <div class="text-sm text-slate-400 mb-1">{{ authStore.user?.username }}</div>
        <button @click="logout" class="text-xs text-slate-500 hover:text-red-400 transition">Выйти</button>
      </div>
    </aside>

    <!-- Main content area -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <main class="flex-1 overflow-y-auto pb-28">
        <router-view />
      </main>

      <!-- Audio Player — fixed bottom -->
      <AudioPlayer />
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NavLink from '@/components/layout/NavLink.vue'
import AudioPlayer from '@/components/player/AudioPlayer.vue'

const router = useRouter()
const authStore = useAuthStore()

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>
