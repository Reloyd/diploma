<template>
  <div class="fixed bottom-0 left-0 right-0 bg-surface-card border-t border-slate-800 px-6 py-3 z-50"
       v-if="player.currentTrack">
    <!-- Progress bar -->
    <div class="absolute top-0 left-0 right-0 h-0.5 bg-slate-700 cursor-pointer" @click="seek">
      <div class="h-full bg-brand-500 transition-all"
           :style="{ width: progressPercent + '%' }"></div>
    </div>

    <div class="flex items-center gap-4 max-w-7xl mx-auto">
      <!-- Cover + info -->
      <div class="flex items-center gap-3 w-64 flex-shrink-0">
        <img v-if="player.currentTrack.cover_url"
             :src="player.currentTrack.cover_url" alt="cover"
             class="w-12 h-12 rounded-lg object-cover bg-slate-700" />
        <div v-else class="w-12 h-12 rounded-lg bg-surface-elevated flex items-center justify-center text-xl">🎵</div>
        <div class="overflow-hidden">
          <div class="text-white text-sm font-medium truncate">{{ player.currentTrack.title }}</div>
          <div class="text-slate-400 text-xs truncate">{{ player.currentTrack.artist_name || player.currentTrack.artist?.name }}</div>
        </div>
        <!-- Like -->
        <button @click="toggleLike"
          :class="player.currentTrack.in_library ? 'text-red-400' : 'text-slate-400 hover:text-red-400'"
          class="transition ml-auto text-sm">
          {{ player.currentTrack.in_library ? '♥' : '♡' }}
        </button>
      </div>

      <!-- Controls -->
      <div class="flex items-center gap-4 flex-1 justify-center">
        <button @click="player.prev()" class="text-slate-400 hover:text-white transition text-xl">⏮</button>
        <button @click="togglePlay"
          class="w-10 h-10 bg-brand-600 hover:bg-brand-700 rounded-full flex items-center justify-center transition text-white">
          {{ player.isPlaying ? '⏸' : '▶' }}
        </button>
        <button @click="player.next()" class="text-slate-400 hover:text-white transition text-xl">⏭</button>
      </div>

      <!-- Time + Volume -->
      <div class="flex items-center gap-4 w-64 justify-end flex-shrink-0">
        <span class="text-xs text-slate-400">
          {{ formatTime(player.currentTime) }} / {{ formatTime(player.duration) }}
        </span>
        <div class="flex items-center gap-2">
          <span class="text-slate-400 text-sm">🔊</span>
          <input type="range" min="0" max="1" step="0.05" :value="player.volume"
            @input="setVolume" class="w-20 accent-brand-500" />
        </div>
      </div>
    </div>

    <!-- Hidden audio element -->
    <audio ref="audioEl" :src="player.currentTrack.file_url"
           :volume="player.volume"
           @timeupdate="onTimeUpdate"
           @ended="player.onEnded()"
           @loadedmetadata="onLoadedMetadata"
           class="hidden" />
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { libraryAPI } from '@/api'

const player = usePlayerStore()
const audioEl = ref(null)

async function toggleLike() {
  const track = player.currentTrack
  if (!track) return
  try {
    if (track.in_library) {
      await libraryAPI.remove(track.id)
      track.in_library = false
    } else {
      await libraryAPI.add(track.id)
      track.in_library = true
    }
    player.likeCurrentTrack()
  } catch (e) {
    console.error('toggleLike error', e)
  }
}

const progressPercent = computed(() =>
  player.duration > 0 ? (player.currentTime / player.duration) * 100 : 0
)

watch(() => player.currentTrack, () => {
  if (!audioEl.value) return
  audioEl.value.load()
  if (player.isPlaying) audioEl.value.play().catch(() => {})
})

watch(() => player.isPlaying, (playing) => {
  if (!audioEl.value) return
  playing ? audioEl.value.play().catch(() => {}) : audioEl.value.pause()
})

function togglePlay() {
  player.togglePlay()
}

function onTimeUpdate() {
  if (!audioEl.value) return
  player.onTimeUpdate(audioEl.value.currentTime, audioEl.value.duration || 0)
}

function onLoadedMetadata() {
  if (!audioEl.value) return
  player.onTimeUpdate(audioEl.value.currentTime, audioEl.value.duration || 0)
  if (player.isPlaying) audioEl.value.play().catch(() => {})
}

function setVolume(e) {
  player.volume = parseFloat(e.target.value)
  if (audioEl.value) audioEl.value.volume = player.volume
}

function seek(e) {
  if (!audioEl.value || !player.duration) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  audioEl.value.currentTime = ratio * player.duration
}

function formatTime(sec) {
  if (!sec || isNaN(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>
