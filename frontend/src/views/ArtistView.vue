<template>
  <div class="p-6" v-if="data">
    <div class="flex items-center gap-4 mb-8">
      <img v-if="data.artist.image_url" :src="data.artist.image_url" alt=""
           class="w-20 h-20 rounded-full object-cover" />
      <div v-else class="w-20 h-20 rounded-full bg-surface-card flex items-center justify-center text-3xl">🎤</div>
      <div>
        <h1 class="text-2xl font-bold text-white">{{ data.artist.name }}</h1>
        <p class="text-slate-400 text-sm">{{ data.track_count }} треков · {{ data.albums.length }} альбомов</p>
        <p v-if="data.artist.bio" class="text-slate-500 text-sm mt-1">{{ data.artist.bio }}</p>
      </div>
    </div>

    <div v-if="data.albums.length">
      <h2 class="text-lg font-semibold text-white mb-3">Альбомы</h2>
      <div class="flex gap-3 mb-8 flex-wrap">
        <router-link v-for="album in data.albums" :key="album.id" :to="`/albums/${album.id}`"
          class="bg-surface-card hover:bg-surface-elevated rounded-xl p-3 w-36 transition block">
          <img v-if="album.cover_url" :src="album.cover_url" alt="" class="w-full aspect-square rounded-lg object-cover mb-2" />
          <div v-else class="w-full aspect-square rounded-lg bg-surface-elevated flex items-center justify-center text-2xl mb-2">💿</div>
          <div class="text-white text-sm font-medium truncate">{{ album.title }}</div>
          <div class="text-slate-500 text-xs">{{ album.release_year }}</div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { tracksAPI } from '@/api'

const route = useRoute()
const data = ref(null)

onMounted(async () => {
  const { data: d } = await tracksAPI.getArtist(route.params.id)
  data.value = d
})
</script>
