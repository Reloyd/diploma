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

      <!-- Add to playlist button -->
      <div class="relative" @click.stop>
        <button @click="togglePlaylistMenu"
          class="text-slate-500 hover:text-white transition text-base opacity-0 group-hover:opacity-100 px-1"
          title="Добавить в плейлист">
          ⊕
        </button>

        <!-- Dropdown -->
        <div v-if="showPlaylistMenu"
             class="absolute right-0 bottom-full mb-1 bg-slate-800 border border-slate-700 rounded-xl
                    shadow-2xl z-50 min-w-48 py-1 overflow-hidden">
          <div class="px-3 py-2 text-xs text-slate-500 border-b border-slate-700">
            Добавить в плейлист
          </div>
          <div v-if="loadingPlaylists" class="px-3 py-2 text-xs text-slate-400">
            Загрузка...
          </div>
          <div v-else-if="!playlists.length" class="px-3 py-2 text-xs text-slate-400">
            Нет плейлистов
          </div>
          <div v-else class="max-h-48 overflow-y-auto">
            <button v-for="pl in playlists" :key="pl.id"
              @click="addToPlaylist(pl)"
              class="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-700
                     hover:text-white transition flex items-center gap-2">
              <span class="text-base">{{ contextIcon(pl.context) }}</span>
              <span class="truncate flex-1">{{ pl.title }}</span>
              <span v-if="addedTo === pl.id" class="text-green-400 text-xs flex-shrink-0">✓</span>
            </button>
          </div>
          <div class="border-t border-slate-700 px-3 py-2">
            <router-link to="/playlists" @click="showPlaylistMenu = false"
              class="text-xs text-brand-400 hover:text-brand-300 transition">
              + Создать новый плейлист
            </router-link>
          </div>
        </div>
      </div>

      <!-- Library button -->
      <button v-if="showLibrary" @click.stop="toggleLibrary"
        :class="track.in_library ? 'text-brand-400' : 'text-slate-500 hover:text-white'"
        class="transition text-sm">{{ track.in_library ? '♥' : '♡' }}</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import { libraryAPI, playlistsAPI } from '@/api'

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

// Playlist menu
const showPlaylistMenu = ref(false)
const playlists = ref([])
const loadingPlaylists = ref(false)
const addedTo = ref(null)

async function togglePlaylistMenu() {
  if (showPlaylistMenu.value) {
    showPlaylistMenu.value = false
    return
  }
  showPlaylistMenu.value = true
  addedTo.value = null
  if (!playlists.value.length) {
    loadingPlaylists.value = true
    try {
      const { data } = await playlistsAPI.list()
      playlists.value = data
    } catch (e) {}
    finally { loadingPlaylists.value = false }
  }
}

async function addToPlaylist(pl) {
  try {
    await playlistsAPI.addTrack(pl.id, props.track.id)
    addedTo.value = pl.id
    setTimeout(() => { showPlaylistMenu.value = false; addedTo.value = null }, 800)
  } catch (e) {
    console.error('addToPlaylist error', e)
  }
}

function contextIcon(ctx) {
  return { work: '💻', rest: '🌙', sport: '🏋️', general: '🎵' }[ctx] || '🎵'
}

// Close menu on outside click
function onOutsideClick(e) {
  if (showPlaylistMenu.value) showPlaylistMenu.value = false
}
onMounted(() => document.addEventListener('click', onOutsideClick))
onUnmounted(() => document.removeEventListener('click', onOutsideClick))

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
