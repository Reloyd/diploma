<template>
  <div class="p-6 flex flex-col h-full max-h-screen">
    <h1 class="text-2xl font-bold text-white mb-2">ИИ-ассистент</h1>
    <p class="text-slate-400 text-sm mb-6">Опишите настроение или активность — создам плейлист специально для вас</p>

    <!-- Example prompts -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button v-for="example in examples" :key="example"
        @click="prompt = example"
        class="text-xs bg-surface-card border border-slate-700 text-slate-400 hover:text-white hover:border-brand-500 px-3 py-1.5 rounded-full transition">
        {{ example }}
      </button>
    </div>

    <!-- Last created playlist -->
    <div v-if="createdPlaylist" class="bg-surface-card rounded-xl p-4 mb-6 border border-brand-700/30">
      <div class="flex items-center justify-between mb-3">
        <div>
          <div class="text-white font-semibold">{{ createdPlaylist.title }}</div>
          <div class="text-slate-400 text-sm">{{ createdPlaylist.track_count }} треков</div>
        </div>
        <router-link :to="`/playlists/${createdPlaylist.id}`"
          class="text-brand-400 hover:text-brand-300 text-sm transition">
          Открыть →
        </router-link>
      </div>
      <p v-if="createdPlaylist.ai_explanation" class="text-slate-400 text-sm mb-3">
        {{ createdPlaylist.ai_explanation }}
      </p>
      <div class="space-y-1 max-h-40 overflow-y-auto">
        <div v-for="pt in createdPlaylist.tracks.slice(0, 8)" :key="pt.track.id"
          class="text-sm text-slate-300 flex items-center gap-2">
          <span class="text-slate-600">{{ pt.position + 1 }}.</span>
          {{ pt.track.title }} — {{ pt.track.artist_name }}
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="mt-auto">
      <div class="flex gap-3 items-end">
        <div class="flex-1">
          <select v-model="context" class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white text-sm mb-2 focus:outline-none w-full">
            <option value="general">Контекст: обычный</option>
            <option value="work">Для работы 💻</option>
            <option value="rest">Для отдыха 🌙</option>
            <option value="sport">Для спорта 🏋️</option>
          </select>
          <div class="flex gap-2">
            <input v-model="prompt" type="text"
              placeholder="Хочу что-то энергичное для пробежки..."
              @keydown.enter="send"
              class="flex-1 bg-surface-card border border-slate-700 rounded-xl px-4 py-3 text-white
                     placeholder:text-slate-500 focus:outline-none focus:border-brand-500 transition" />
            <button @click="send" :disabled="!prompt.trim() || loading"
              class="bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white px-5 py-3 rounded-xl font-medium transition">
              {{ loading ? '...' : '→' }}
            </button>
          </div>
        </div>
      </div>
      <p v-if="error" class="text-red-400 text-sm mt-2">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { playlistsAPI } from '@/api'

const router = useRouter()
const prompt = ref('')
const context = ref('general')
const loading = ref(false)
const error = ref('')
const createdPlaylist = ref(null)

const examples = [
  'Составь плейлист для пробежки',
  'Хочу что-нибудь спокойное для работы',
  'Энергичные треки для тренировки',
  'Расслабляющая музыка для вечера',
  'Что-нибудь в стиле рок',
  'Треки с высоким темпом',
]

async function send() {
  if (!prompt.value.trim() || loading.value) return
  error.value = ''
  loading.value = true
  try {
    const { data } = await playlistsAPI.createAI({ prompt: prompt.value, context: context.value })
    createdPlaylist.value = data
    prompt.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка создания плейлиста'
  } finally {
    loading.value = false
  }
}
</script>
