<template>
  <div class="p-6 flex flex-col h-full">
    <h1 class="text-2xl font-bold text-white mb-1">ИИ-ассистент</h1>
    <p class="text-slate-400 text-sm mb-6">Опишите настроение или активность — создам плейлист специально для вас</p>

    <!-- Example prompts -->
    <div class="flex flex-wrap gap-2 mb-6">
      <button v-for="example in examples" :key="example"
        @click="prompt = example"
        class="text-xs bg-surface-card border border-slate-700 text-slate-400 hover:text-white
               hover:border-brand-500 px-3 py-1.5 rounded-full transition">
        {{ example }}
      </button>
    </div>

    <!-- Preview -->
    <div v-if="preview" class="bg-surface-card rounded-xl p-5 mb-5 border border-brand-700/40 flex-1 overflow-hidden flex flex-col">
      <div class="flex items-start justify-between mb-3">
        <div>
          <div class="text-white font-semibold text-lg">{{ preview.title }}</div>
          <div class="text-slate-400 text-sm">{{ preview.track_count }} треков · {{ preview.context }}</div>
        </div>
        <button @click="clearPreview" class="text-slate-600 hover:text-slate-400 transition text-lg leading-none">✕</button>
      </div>

      <p v-if="preview.ai_explanation" class="text-slate-400 text-sm mb-4 italic">
        {{ preview.ai_explanation }}
      </p>

      <!-- Track list -->
      <div class="overflow-y-auto flex-1 space-y-1 mb-5">
        <div v-for="pt in preview.tracks" :key="pt.track.id"
             class="flex items-center gap-3 py-1.5 px-2 rounded-lg hover:bg-surface-elevated transition">
          <span class="text-slate-600 text-xs w-5 text-right flex-shrink-0">{{ pt.position + 1 }}</span>
          <img v-if="pt.track.cover_url" :src="pt.track.cover_url" alt=""
               class="w-8 h-8 rounded object-cover flex-shrink-0" />
          <div v-else class="w-8 h-8 rounded bg-surface-elevated flex items-center justify-center flex-shrink-0 text-sm">🎵</div>
          <div class="flex-1 overflow-hidden">
            <div class="text-white text-sm truncate">{{ pt.track.title }}</div>
            <div class="text-slate-500 text-xs truncate">{{ pt.track.artist_name }}</div>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex gap-3 pt-3 border-t border-slate-700">
        <button @click="savePlaylist" :disabled="saving"
          class="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white
                 py-2.5 rounded-xl font-medium transition text-sm">
          {{ saving ? 'Сохраняю...' : '💾 Сохранить плейлист' }}
        </button>
        <button @click="regenerate" :disabled="loading"
          class="px-4 bg-surface-elevated hover:bg-slate-700 disabled:opacity-40 text-slate-300
                 py-2.5 rounded-xl transition text-sm border border-slate-700">
          {{ loading ? '...' : '🔄 Пересоздать' }}
        </button>
        <button @click="clearPreview"
          class="px-4 bg-surface-elevated hover:bg-red-900/30 text-slate-500 hover:text-red-400
                 py-2.5 rounded-xl transition text-sm border border-slate-700">
          Отклонить
        </button>
      </div>
    </div>

    <!-- Saved confirmation -->
    <div v-if="savedPlaylist" class="bg-green-900/20 border border-green-700/30 rounded-xl p-4 mb-5 flex items-center justify-between">
      <div>
        <div class="text-green-400 text-sm font-medium">✓ Плейлист сохранён</div>
        <div class="text-slate-400 text-xs">{{ savedPlaylist.title }}</div>
      </div>
      <router-link :to="`/playlists/${savedPlaylist.id}`"
        class="text-brand-400 hover:text-brand-300 text-sm transition">
        Открыть →
      </router-link>
    </div>

    <!-- Input -->
    <div class="mt-auto">
      <div class="flex gap-3 items-end">
        <div class="flex-1">
          <select v-model="context"
            class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white text-sm mb-2 focus:outline-none w-full">
            <option value="general">Контекст: обычный</option>
            <option value="work">Для работы 💻</option>
            <option value="rest">Для отдыха 🌙</option>
            <option value="sport">Для спорта 🏋️</option>
          </select>
          <div class="flex gap-2">
            <input v-model="prompt" type="text"
              placeholder="Хочу что-то энергичное для пробежки..."
              @keydown.enter="generate"
              class="flex-1 bg-surface-card border border-slate-700 rounded-xl px-4 py-3 text-white
                     placeholder:text-slate-500 focus:outline-none focus:border-brand-500 transition" />
            <button @click="generate" :disabled="!prompt.trim() || loading"
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
const lastPrompt = ref('')
const context = ref('general')
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const preview = ref(null)
const savedPlaylist = ref(null)

const examples = [
  'Составь плейлист для пробежки',
  'Хочу что-нибудь спокойное для работы',
  'Энергичные треки для тренировки',
  'Расслабляющая музыка для вечера',
  'Что-нибудь в стиле рок',
  'Треки с высоким темпом',
]

async function generate() {
  if (!prompt.value.trim() || loading.value) return
  error.value = ''
  savedPlaylist.value = null
  loading.value = true
  lastPrompt.value = prompt.value
  try {
    const { data } = await playlistsAPI.previewAI({
      prompt: prompt.value,
      context: context.value,
    })
    preview.value = { ...data, _context: context.value }
    prompt.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка генерации плейлиста'
  } finally {
    loading.value = false
  }
}

async function regenerate() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    const { data } = await playlistsAPI.previewAI({
      prompt: lastPrompt.value,
      context: preview.value._context || context.value,
    })
    preview.value = { ...data, _context: preview.value._context || context.value }
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка генерации плейлиста'
  } finally {
    loading.value = false
  }
}

async function savePlaylist() {
  if (saving.value || !preview.value) return
  saving.value = true
  try {
    const { data } = await playlistsAPI.createAI({
      prompt: preview.value.ai_prompt,
      context: preview.value._context || context.value,
    })
    savedPlaylist.value = data
    preview.value = null
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}

function clearPreview() {
  preview.value = null
}
</script>
