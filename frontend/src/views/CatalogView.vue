<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-white mb-6">Каталог</h1>

    <!-- Search + filters -->
    <div class="flex gap-3 mb-6 flex-wrap">
      <input v-model="search" type="text" placeholder="Поиск треков..."
        @input="debouncedSearch"
        class="flex-1 min-w-48 bg-surface-card border border-slate-700 rounded-lg px-4 py-2 text-white
               placeholder:text-slate-500 focus:outline-none focus:border-brand-500 transition" />
      <select v-model="selectedGenre" @change="loadTracks(1)"
        class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none">
        <option value="">Все жанры</option>
        <option v-for="g in genres" :key="g.id" :value="g.name">{{ g.name }}</option>
      </select>
    </div>

    <!-- Track list -->
    <div v-if="loading" class="text-center py-12 text-slate-400">Загрузка...</div>
    <div v-else-if="!tracks.length" class="text-center py-12 text-slate-500">
      Треки не найдены
    </div>
    <div v-else class="space-y-1">
      <TrackCard v-for="track in tracks" :key="track.id" :track="track" :queue="tracks" />
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-6">
      <button v-for="p in totalPages" :key="p" @click="loadTracks(p)"
        :class="p === currentPage ? 'bg-brand-600 text-white' : 'bg-surface-card text-slate-400 hover:text-white'"
        class="w-9 h-9 rounded-lg text-sm transition">{{ p }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { tracksAPI } from '@/api'
import TrackCard from '@/components/track/TrackCard.vue'

const tracks = ref([])
const genres = ref([])
const search = ref('')
const selectedGenre = ref('')
const loading = ref(false)
const currentPage = ref(1)
const total = ref(0)
const perPage = 20
const totalPages = ref(1)

let searchTimer = null

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadTracks(1), 400)
}

async function loadTracks(page = 1) {
  loading.value = true
  currentPage.value = page
  try {
    const params = { page, per_page: perPage }
    if (search.value) params.q = search.value
    if (selectedGenre.value) params.genre = selectedGenre.value
    const { data } = await tracksAPI.list(params)
    tracks.value = data.items
    total.value = data.total
    totalPages.value = Math.ceil(data.total / perPage)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadGenres() {
  try {
    const { data } = await tracksAPI.listGenres()
    genres.value = data
  } catch (e) {}
}

onMounted(() => {
  loadTracks()
  loadGenres()
})
</script>
