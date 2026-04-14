<template>
  <div class="group flex items-center gap-3 p-3 rounded-xl bg-surface-card hover:bg-surface-elevated transition cursor-pointer"
       @click="play">
    <!-- Cover -->
    <div class="relative w-12 h-12 flex-shrink-0">
      <img v-if="track.cover_url" :src="track.cover_url" alt=""
           class="w-full h-full rounded-lg object-cover" />
      <div v-else class="w-full h-full rounded-lg bg-surface-elevated flex items-center justify-center text-xl">🎵</div>
      <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
        <div class="bg-brand-600 rounded-full w-8 h-8 flex items-center justify-center text-white text-sm">▶</div>
      </div>
    </div>

    <!-- Info -->
    <div class="flex-1 overflow-hidden">
      <div class="text-white text-sm font-medium truncate" :class="{ 'text-brand-400': isPlaying }">
        {{ track.title }}
      </div>
      <div class="text-slate-400 text-xs truncate">
        <router-link :to="`/artists/${track.artist_id || track.artist?.id}`"
          class="hover:text-white transition" @click.stop>
          {{ track.artist_name || track.artist?.name }}
        </router-link>
        <span v-if="track.album" class="mx-1">·</span>
        <span v-if="track.album">{{ track.album.title }}</span>
      </div>
    </div>

    <!-- Duration + actions -->
    <div class="flex items-center gap-2 ml-auto">
      <span class="text-xs text-slate-500">{{ formatDuration(track.duration_sec) }}</span>
      <button v-if="showLibrary" @click.stop="toggleLibrary"
        :class="track.in_library ? 'text-brand-400' : 'text-slate-500 hover:text-white'"
        class="transition text-sm">{{ track.in_library ? '♥' : '♡' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { libraryAPI } from '@/api'

const props = defineProps({
  track: { type: Object, required: true },
  queue: { type: Array, default: null },
  showLibrary: { type: Boolean, default: true },
})
const emit = defineEmits(['library-changed'])

const player = usePlayerStore()
const isPlaying = computed(() =>
  player.currentTrack?.id === props.track.id && player.isPlaying
)

function play() {
  player.playTrack(props.track, props.queue)
}

async function toggleLibrary() {
  if (props.track.in_library) {
    await libraryAPI.remove(props.track.id)
    props.track.in_library = false
  } else {
    await libraryAPI.add(props.track.id)
    props.track.in_library = true
  }
  emit('library-changed', props.track)
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>
