<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Плейлисты</h1>
      <button @click="showCreate = true"
        class="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
        + Создать
      </button>
    </div>

    <div v-if="!playlists.length" class="text-center py-16">
      <div class="text-5xl mb-4">🎶</div>
      <p class="text-slate-400">У вас пока нет плейлистов</p>
      <p class="text-slate-500 text-sm mt-1">Создайте вручную или через ИИ-ассистента</p>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <router-link v-for="pl in playlists" :key="pl.id" :to="`/playlists/${pl.id}`"
        class="bg-surface-card hover:bg-surface-elevated rounded-xl p-4 transition block">
        <div class="flex items-center justify-between mb-2">
          <span class="text-lg">{{ contextIcon(pl.context) }}</span>
          <span v-if="pl.source === 'ai'" class="text-xs text-brand-400 bg-brand-900/30 px-2 py-0.5 rounded-full">AI</span>
        </div>
        <div class="font-semibold text-white truncate">{{ pl.title }}</div>
        <div class="text-sm text-slate-400 mt-1">{{ pl.track_count }} треков</div>
        <div class="text-xs text-slate-600 mt-2">{{ formatDate(pl.created_at) }}</div>
      </router-link>
    </div>

    <!-- Create modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div class="bg-surface-card rounded-2xl p-6 w-full max-w-md">
        <h2 class="text-white font-semibold text-lg mb-4">Новый плейлист</h2>
        <input v-model="newTitle" placeholder="Название..." type="text"
          class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none mb-3" />
        <select v-model="newContext"
          class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none mb-4">
          <option value="general">Обычный</option>
          <option value="work">Для работы 💻</option>
          <option value="rest">Для отдыха 🌙</option>
          <option value="sport">Для спорта 🏋️</option>
        </select>
        <div class="flex gap-2">
          <button @click="createPlaylist" class="flex-1 bg-brand-600 hover:bg-brand-700 text-white py-2 rounded-lg font-medium transition">
            Создать
          </button>
          <button @click="showCreate = false" class="flex-1 bg-surface-elevated text-slate-400 hover:text-white py-2 rounded-lg transition">
            Отмена
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { playlistsAPI } from '@/api'

const playlists = ref([])
const showCreate = ref(false)
const newTitle = ref('')
const newContext = ref('general')

async function loadPlaylists() {
  const { data } = await playlistsAPI.list()
  playlists.value = data
}

async function createPlaylist() {
  if (!newTitle.value.trim()) return
  await playlistsAPI.create({ title: newTitle.value, context: newContext.value })
  newTitle.value = ''
  showCreate.value = false
  await loadPlaylists()
}

function contextIcon(ctx) {
  return { work: '💻', rest: '🌙', sport: '🏋️', general: '🎵' }[ctx] || '🎵'
}

function formatDate(d) {
  return new Date(d).toLocaleDateString('ru-RU')
}

onMounted(loadPlaylists)
</script>
