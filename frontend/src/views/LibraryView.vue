<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-white mb-6">Моя фонотека</h1>

    <div class="flex gap-3 mb-6">
      <select v-model="filterArtist" @change="loadLibrary(1)"
        class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none">
        <option value="">Все исполнители</option>
        <option v-for="a in artists" :key="a.id" :value="a.id">{{ a.name }}</option>
      </select>
      <select v-model="filterGenre" @change="loadLibrary(1)"
        class="bg-surface-card border border-slate-700 rounded-lg px-3 py-2 text-white focus:outline-none">
        <option value="">Все жанры</option>
        <option v-for="g in genres" :key="g.id" :value="g.name">{{ g.name }}</option>
      </select>
    </div>

    <div v-if="loading" class="text-center py-12 text-slate-400">Загрузка...</div>
    <div v-else-if="!tracks.length" class="text-center py-16">
      <div class="text-5xl mb-4">📚</div>
      <p class="text-slate-400">В вашей фонотеке ещё нет треков</p>
      <p class="text-slate-500 text-sm mt-1">Добавляйте треки из каталога</p>
    </div>
    <div v-else class="space-y-1">
      <TrackCard v-for="track in tracks" :key="track.id" :track="track" :queue="tracks" />
    </div>

    <div v-if="totalPages > 1" class="flex justify-center gap-2 mt-6">
      <button v-for="p in totalPages" :key="p" @click="loadLibrary(p)"
        :class="p === currentPage ? 'bg-brand-600 text-white' : 'bg-surface-card text-slate-400 hover:text-white'"
        class="w-9 h-9 rounded-lg text-sm transition">{{ p }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { libraryAPI, tracksAPI } from '@/api'
import TrackCard from '@/components/track/TrackCard.vue'

const tracks = ref([])
const artists = ref([])
const genres = ref([])
const filterArtist = ref('')
const filterGenre = ref('')
const loading = ref(false)
const currentPage = ref(1)
const totalPages = ref(1)

async function loadLibrary(page = 1) {
  loading.value = true
  currentPage.value = page
  try {
    const params = { page, per_page: 20 }
    if (filterArtist.value) params.artist_id = filterArtist.value
    if (filterGenre.value) params.genre = filterGenre.value
    const { data } = await libraryAPI.get(params)
    tracks.value = data.items.map(t => ({ ...t, in_library: true }))
    totalPages.value = Math.ceil(data.total / 20)
    // Extract artists for filter
    const artistMap = {}
    data.items.forEach(t => { if (t.artist) artistMap[t.artist.id] = t.artist })
    artists.value = Object.values(artistMap)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadGenres() {
  const { data } = await tracksAPI.listGenres()
  genres.value = data
}

onMounted(() => { loadLibrary(); loadGenres() })
</script>
