<template>
  <div class="p-6" v-if="data">
    <div class="flex items-start gap-5 mb-8">
      <img v-if="data.album.cover_url" :src="data.album.cover_url" alt=""
           class="w-36 h-36 rounded-xl object-cover" />
      <div v-else class="w-36 h-36 rounded-xl bg-surface-card flex items-center justify-center text-5xl">💿</div>
      <div>
        <p class="text-slate-400 text-sm mb-1">Альбом</p>
        <h1 class="text-2xl font-bold text-white">{{ data.album.title }}</h1>
        <router-link :to="`/artists/${data.artist.id}`" class="text-brand-400 hover:underline text-sm">
          {{ data.artist.name }}
        </router-link>
        <p class="text-slate-500 text-sm">{{ data.album.release_year }} · {{ data.tracks.length }} треков</p>
        <button @click="playAll" class="mt-3 bg-brand-600 hover:bg-brand-700 text-white px-5 py-2 rounded-lg text-sm font-medium transition">
          ▶ Слушать альбом
        </button>
      </div>
    </div>
    <div class="space-y-1">
      <TrackCard v-for="track in data.tracks" :key="track.id" :track="track" :queue="data.tracks" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { tracksAPI } from '@/api'
import { usePlayerStore } from '@/stores/player'
import TrackCard from '@/components/track/TrackCard.vue'

const route = useRoute()
const player = usePlayerStore()
const data = ref(null)

function playAll() {
  if (data.value?.tracks.length) player.playQueue(data.value.tracks)
}

onMounted(async () => {
  const { data: d } = await tracksAPI.getAlbum(route.params.id)
  data.value = d
})
</script>
