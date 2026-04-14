<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-white">Рекомендации</h1>
      <div class="flex gap-2 items-center">
        <select v-model="context" @change="load"
          class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none text-sm">
          <option value="general">Все</option>
          <option value="work">Для работы 💻</option>
          <option value="rest">Для отдыха 🌙</option>
          <option value="sport">Для спорта 🏋️</option>
        </select>
        <button @click="refresh"
          class="bg-surface-card border border-slate-700 text-slate-400 hover:text-white px-4 py-2 rounded-lg text-sm transition">
          🔄 Обновить
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-12 text-slate-400">Загрузка...</div>
    <div v-else-if="!recs.length" class="text-center py-16">
      <div class="text-5xl mb-4">✨</div>
      <p class="text-slate-400">Рекомендации ещё формируются</p>
      <p class="text-slate-500 text-sm mt-1">Слушайте треки — система изучит ваши вкусы</p>
    </div>
    <div v-else class="space-y-2">
      <div v-for="rec in recs" :key="rec.id" class="flex items-start gap-3 bg-surface-card rounded-xl p-3">
        <div class="flex-1">
          <TrackCard :track="rec.track" :queue="trackList" />
        </div>
        <div class="w-48 flex-shrink-0 text-xs">
          <span :class="reasonClass(rec.reason_type)"
            class="inline-block px-2 py-0.5 rounded-full mb-1 font-medium">
            {{ reasonLabel(rec.reason_type) }}
          </span>
          <p class="text-slate-500">{{ rec.reason_detail }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { recommendationsAPI } from '@/api'
import TrackCard from '@/components/track/TrackCard.vue'

const recs = ref([])
const context = ref('general')
const loading = ref(false)

const trackList = computed(() => recs.value.map(r => r.track))

async function load() {
  loading.value = true
  try {
    const { data } = await recommendationsAPI.get({ context: context.value, limit: 30 })
    recs.value = data
  } catch (e) {}
  finally { loading.value = false }
}

async function refresh() {
  await recommendationsAPI.refresh(context.value)
  setTimeout(load, 2000) // wait a bit for ML worker
}

function reasonLabel(type) {
  return { similar_track: '🎵 Похожий трек', favorite_artist: '⭐ Исполнитель', favorite_genre: '🎸 Жанр', context: '🎯 Контекст' }[type] || type
}

function reasonClass(type) {
  return {
    similar_track: 'bg-blue-900/40 text-blue-400',
    favorite_artist: 'bg-yellow-900/40 text-yellow-400',
    favorite_genre: 'bg-green-900/40 text-green-400',
    context: 'bg-purple-900/40 text-purple-400',
  }[type] || 'bg-slate-700 text-slate-400'
}

onMounted(load)
</script>
