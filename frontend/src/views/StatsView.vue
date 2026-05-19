<template>
  <div class="p-6 max-w-6xl mx-auto">
    <h1 class="text-2xl font-bold text-white mb-6">Моя статистика</h1>

    <div v-if="loading" class="text-center py-20 text-slate-400">Загрузка...</div>
    <div v-else-if="!stats" class="text-center py-20 text-slate-500">
      <div class="text-5xl mb-3">📊</div>
      <p>Статистика появится после первых прослушиваний</p>
    </div>
    <template v-else>

      <!-- Summary cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-3xl mb-1">🕐</div>
          <div class="text-2xl font-bold text-white">{{ formatTime(stats.summary.total_minutes) }}</div>
          <div class="text-xs text-slate-500 mt-1">Всего прослушано</div>
        </div>
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-3xl mb-1">▶️</div>
          <div class="text-2xl font-bold text-white">{{ stats.summary.total_plays }}</div>
          <div class="text-xs text-slate-500 mt-1">Воспроизведений</div>
        </div>
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-3xl mb-1">🎵</div>
          <div class="text-2xl font-bold text-white">{{ stats.summary.unique_tracks }}</div>
          <div class="text-xs text-slate-500 mt-1">Уникальных треков</div>
        </div>
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-3xl mb-1">🔥</div>
          <div class="text-2xl font-bold text-white">{{ stats.summary.streak_days }}</div>
          <div class="text-xs text-slate-500 mt-1">Дней подряд</div>
        </div>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-slate-400 text-sm mb-1">Среднее прослушивание</div>
          <div class="flex items-end gap-2">
            <span class="text-xl font-bold text-white">{{ stats.summary.avg_completion }}%</span>
          </div>
          <div class="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div class="h-full bg-brand-500 rounded-full transition-all"
                 :style="{ width: stats.summary.avg_completion + '%' }"></div>
          </div>
        </div>
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-slate-400 text-sm mb-1">Пропускаемость</div>
          <div class="flex items-end gap-2">
            <span class="text-xl font-bold text-white">{{ stats.summary.skip_rate }}%</span>
          </div>
          <div class="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
            <div class="h-full bg-red-500 rounded-full transition-all"
                 :style="{ width: stats.summary.skip_rate + '%' }"></div>
          </div>
        </div>
        <div class="bg-surface-card rounded-xl p-4 border border-slate-800">
          <div class="text-slate-400 text-sm mb-1">Всего часов</div>
          <div class="text-xl font-bold text-white">{{ stats.summary.total_hours }} ч</div>
          <div class="text-xs text-slate-600 mt-1">
            {{ stats.summary.total_minutes }} минут
          </div>
        </div>
      </div>

      <!-- Activity chart — last 30 days -->
      <div class="bg-surface-card rounded-xl p-5 border border-slate-800 mb-8">
        <h2 class="text-white font-semibold mb-4">Активность за 30 дней</h2>
        <div class="flex items-end gap-0.5 h-24">
          <div v-for="day in stats.activity" :key="day.date"
               class="flex-1 flex flex-col items-center gap-0.5 group relative">
            <div class="absolute bottom-full mb-1 bg-slate-800 text-white text-xs px-2 py-1 rounded
                        opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-10">
              {{ formatDate(day.date) }}: {{ day.plays }} трек{{ pluralPlays(day.plays) }},
              {{ day.minutes }} мин
            </div>
            <div class="w-full rounded-sm transition-all"
                 :class="day.plays > 0 ? 'bg-brand-500 hover:bg-brand-400' : 'bg-slate-800'"
                 :style="{ height: barHeight(day.plays) + '%', minHeight: day.plays > 0 ? '4px' : '2px' }">
            </div>
          </div>
        </div>
        <div class="flex justify-between text-xs text-slate-600 mt-2">
          <span>{{ formatDate(stats.activity[0]?.date) }}</span>
          <span>Сегодня</span>
        </div>
      </div>

      <!-- Hour of day heatmap -->
      <div class="bg-surface-card rounded-xl p-5 border border-slate-800 mb-8">
        <h2 class="text-white font-semibold mb-4">Когда слушаю музыку</h2>
        <div class="flex items-end gap-1 h-16">
          <div v-for="h in stats.by_hour" :key="h.hour"
               class="flex-1 flex flex-col items-center gap-1 group relative">
            <div class="absolute bottom-full mb-1 bg-slate-800 text-white text-xs px-2 py-1 rounded
                        opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-10">
              {{ h.hour }}:00 — {{ h.plays }} воспроизв.
            </div>
            <div class="w-full rounded-sm transition-all"
                 :class="hourColor(h.plays)"
                 :style="{ height: Math.max(hourBarHeight(h.plays), h.plays > 0 ? 8 : 2) + 'px' }">
            </div>
            <span v-if="h.hour % 6 === 0" class="text-xs text-slate-600">{{ h.hour }}ч</span>
            <span v-else class="text-xs text-transparent">·</span>
          </div>
        </div>
      </div>

      <!-- Top tracks + Top artists + Top genres -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">

        <!-- Top tracks -->
        <div class="bg-surface-card rounded-xl p-5 border border-slate-800">
          <h2 class="text-white font-semibold mb-4">Любимые треки</h2>
          <div v-if="!stats.top_tracks.length" class="text-slate-500 text-sm">Пока нет данных</div>
          <div v-else class="space-y-3">
            <div v-for="(track, i) in stats.top_tracks" :key="track.id"
                 class="flex items-center gap-3">
              <span class="text-slate-600 text-sm w-4 text-right flex-shrink-0">{{ i + 1 }}</span>
              <img v-if="track.cover_url" :src="track.cover_url" alt=""
                   class="w-9 h-9 rounded-lg object-cover flex-shrink-0" />
              <div v-else class="w-9 h-9 rounded-lg bg-surface-elevated flex items-center justify-center flex-shrink-0">🎵</div>
              <div class="flex-1 overflow-hidden">
                <div class="text-white text-sm truncate">{{ track.title }}</div>
                <div class="text-slate-500 text-xs truncate">{{ track.artist_name }}</div>
              </div>
              <div class="text-right flex-shrink-0">
                <div class="text-xs text-brand-400 font-medium">{{ track.play_count }}×</div>
                <div class="text-xs text-slate-600">{{ track.avg_completion }}%</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top artists -->
        <div class="bg-surface-card rounded-xl p-5 border border-slate-800">
          <h2 class="text-white font-semibold mb-4">Любимые исполнители</h2>
          <div v-if="!stats.top_artists.length" class="text-slate-500 text-sm">Пока нет данных</div>
          <div v-else class="space-y-3">
            <div v-for="(artist, i) in stats.top_artists" :key="artist.id">
              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-2 overflow-hidden">
                  <span class="text-slate-600 text-xs w-4 text-right flex-shrink-0">{{ i + 1 }}</span>
                  <span class="text-white text-sm truncate">{{ artist.name }}</span>
                </div>
                <span class="text-xs text-slate-500 flex-shrink-0 ml-2">{{ Math.round(artist.score * 100) }}%</span>
              </div>
              <div class="h-1 bg-slate-700 rounded-full overflow-hidden ml-6">
                <div class="h-full bg-purple-500 rounded-full"
                     :style="{ width: (artist.score / maxArtistScore * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Top genres -->
        <div class="bg-surface-card rounded-xl p-5 border border-slate-800">
          <h2 class="text-white font-semibold mb-4">Любимые жанры</h2>
          <div v-if="!stats.top_genres.length" class="text-slate-500 text-sm">Пока нет данных</div>
          <div v-else class="space-y-3">
            <div v-for="(genre, i) in stats.top_genres" :key="genre.name">
              <div class="flex items-center justify-between mb-1">
                <div class="flex items-center gap-2">
                  <span class="text-slate-600 text-xs w-4 text-right flex-shrink-0">{{ i + 1 }}</span>
                  <span class="text-white text-sm">{{ genre.name }}</span>
                </div>
                <span class="text-xs text-slate-500">{{ Math.round(genre.score * 100) }}%</span>
              </div>
              <div class="h-1 bg-slate-700 rounded-full overflow-hidden ml-6">
                <div class="h-full bg-green-500 rounded-full"
                     :style="{ width: (genre.score / maxGenreScore * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { statsAPI } from '@/api'

const stats = ref(null)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await statsAPI.get()
    stats.value = data.summary.total_plays > 0 ? data : null
    if (data.summary.total_plays === 0) stats.value = data // show empty state with zeros
    stats.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const maxActivity = computed(() => {
  if (!stats.value) return 1
  return Math.max(...stats.value.activity.map(d => d.plays), 1)
})

const maxHourPlays = computed(() => {
  if (!stats.value) return 1
  return Math.max(...stats.value.by_hour.map(h => h.plays), 1)
})

const maxArtistScore = computed(() => {
  if (!stats.value?.top_artists.length) return 1
  return Math.max(...stats.value.top_artists.map(a => a.score), 0.01)
})

const maxGenreScore = computed(() => {
  if (!stats.value?.top_genres.length) return 1
  return Math.max(...stats.value.top_genres.map(g => g.score), 0.01)
})

function barHeight(plays) {
  return Math.round((plays / maxActivity.value) * 100)
}

function hourBarHeight(plays) {
  return Math.round((plays / maxHourPlays.value) * 56)
}

function hourColor(plays) {
  if (plays === 0) return 'bg-slate-800'
  const ratio = plays / maxHourPlays.value
  if (ratio > 0.66) return 'bg-brand-500'
  if (ratio > 0.33) return 'bg-brand-700'
  return 'bg-brand-900'
}

function formatTime(minutes) {
  if (minutes < 60) return `${minutes} мин`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return m > 0 ? `${h}ч ${m}м` : `${h}ч`
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

function pluralPlays(n) {
  if (n % 10 === 1 && n % 100 !== 11) return ''
  if ([2,3,4].includes(n % 10) && ![12,13,14].includes(n % 100)) return 'а'
  return 'ов'
}

onMounted(load)
</script>
