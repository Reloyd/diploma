<template>
  <div class="p-6" v-if="playlist">
    <div class="flex items-start justify-between mb-6">
      <div class="flex-1 mr-4">
        <!-- Title (editable) -->
        <div class="flex items-center gap-3 mb-2">
          <span class="text-3xl">{{ contextIcon(playlist.context) }}</span>
          <template v-if="editing">
            <input v-model="editTitle" @keyup.enter="saveEdit" @keyup.escape="cancelEdit"
              class="text-2xl font-bold bg-surface-elevated border border-brand-500 rounded-lg px-2 py-0.5
                     text-white focus:outline-none w-80" />
          </template>
          <template v-else>
            <h1 class="text-2xl font-bold text-white">{{ playlist.title }}</h1>
          </template>
          <span v-if="playlist.source === 'ai'"
            class="text-xs text-brand-400 bg-brand-900/30 px-2 py-1 rounded-full">AI</span>
          <button v-if="!editing && playlist.source !== 'ai'" @click="startEdit"
            class="text-slate-500 hover:text-white transition text-sm">✏️</button>
          <template v-if="editing">
            <button @click="saveEdit" class="text-green-400 hover:text-green-300 transition text-sm font-medium">Сохранить</button>
            <button @click="cancelEdit" class="text-slate-500 hover:text-white transition text-sm">Отмена</button>
          </template>
        </div>
        <!-- Description (editable) -->
        <template v-if="editing">
          <input v-model="editDescription" placeholder="Описание плейлиста..."
            class="text-sm bg-surface-elevated border border-slate-600 rounded-lg px-3 py-1.5 text-white
                   focus:outline-none focus:border-brand-500 w-full max-w-xl placeholder:text-slate-500" />
        </template>
        <template v-else>
          <p v-if="playlist.description" class="text-slate-400 text-sm max-w-xl">{{ playlist.description }}</p>
          <p v-else-if="playlist.ai_explanation" class="text-slate-400 text-sm max-w-xl">{{ playlist.ai_explanation }}</p>
          <p v-else-if="playlist.source !== 'ai'" class="text-slate-500 text-sm cursor-pointer hover:text-slate-400 transition"
             @click="startEdit">+ Добавить описание</p>
        </template>
      </div>
      <div class="flex gap-2 flex-shrink-0">
        <button @click="showAddModal = true"
          class="bg-surface-card hover:bg-surface-elevated border border-slate-700 text-slate-300 hover:text-white
                 px-4 py-2 rounded-lg text-sm transition">
          + Добавить треки
        </button>
        <button @click="playAll" v-if="playlist.tracks.length"
          class="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition">
          ▶ Играть всё
        </button>
        <button @click="deletePlaylist"
          class="bg-surface-card hover:bg-red-900/30 border border-slate-700 text-slate-400 hover:text-red-400
                 px-4 py-2 rounded-lg text-sm transition">
          🗑️
        </button>
      </div>
    </div>

    <!-- Track list -->
    <div v-if="!playlist.tracks.length" class="text-center py-12 text-slate-500">
      Плейлист пуст — добавьте треки через кнопку выше
    </div>
    <div v-else class="space-y-1">
      <div v-for="pt in playlist.tracks" :key="pt.track.id"
           class="flex items-center gap-2">
        <span class="text-slate-600 text-sm w-6 text-right flex-shrink-0">{{ pt.position + 1 }}</span>
        <TrackCard :track="pt.track" :queue="trackList" class="flex-1" />
        <button @click="removeTrack(pt.track.id)"
          class="text-slate-600 hover:text-red-400 transition text-sm flex-shrink-0 px-2">✕</button>
      </div>
    </div>
  </div>
  <div v-else class="p-6 text-center text-slate-400">Загрузка...</div>

  <!-- Add tracks modal -->
  <Teleport to="body">
    <div v-if="showAddModal"
         class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
         @click.self="showAddModal = false">
      <div class="bg-surface-card rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl border border-slate-700">
        <div class="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 class="text-white font-semibold">Добавить треки</h2>
          <button @click="showAddModal = false" class="text-slate-400 hover:text-white transition">✕</button>
        </div>
        <div class="p-4 border-b border-slate-700">
          <input v-model="addSearch" @input="debouncedSearch" type="text"
            placeholder="Поиск треков..."
            class="w-full bg-surface-elevated border border-slate-600 rounded-lg px-4 py-2 text-white
                   placeholder:text-slate-500 focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div class="overflow-y-auto flex-1 p-2">
          <div v-if="addLoading" class="text-center py-8 text-slate-400 text-sm">Поиск...</div>
          <div v-else-if="!searchResults.length" class="text-center py-8 text-slate-500 text-sm">
            Начните вводить название трека
          </div>
          <div v-else class="space-y-1">
            <div v-for="track in searchResults" :key="track.id"
                 class="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-elevated transition cursor-pointer group"
                 @click="addTrack(track)">
              <img v-if="track.cover_url" :src="track.cover_url" alt=""
                   class="w-10 h-10 rounded-lg object-cover flex-shrink-0" />
              <div v-else class="w-10 h-10 rounded-lg bg-surface-elevated flex items-center justify-center text-lg flex-shrink-0">🎵</div>
              <div class="flex-1 overflow-hidden">
                <div class="text-white text-sm font-medium truncate">{{ track.title }}</div>
                <div class="text-slate-400 text-xs truncate">{{ track.artist_name }}</div>
              </div>
              <span v-if="alreadyInPlaylist(track.id)"
                class="text-xs text-slate-500 flex-shrink-0">уже добавлен</span>
              <span v-else
                class="text-xs text-brand-400 opacity-0 group-hover:opacity-100 transition flex-shrink-0">+ добавить</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { playlistsAPI, tracksAPI } from '@/api'
import { usePlayerStore } from '@/stores/player'
import TrackCard from '@/components/track/TrackCard.vue'

const route = useRoute()
const router = useRouter()
const player = usePlayerStore()
const playlist = ref(null)

// Edit state
const editing = ref(false)
const editTitle = ref('')
const editDescription = ref('')

// Add tracks modal
const showAddModal = ref(false)
const addSearch = ref('')
const searchResults = ref([])
const addLoading = ref(false)
let searchTimer = null

const trackList = computed(() => playlist.value?.tracks.map(pt => pt.track) || [])
const playlistTrackIds = computed(() => new Set(playlist.value?.tracks.map(pt => pt.track.id) || []))

function alreadyInPlaylist(trackId) {
  return playlistTrackIds.value.has(trackId)
}

async function load() {
  const { data } = await playlistsAPI.get(route.params.id)
  playlist.value = data
}

// Edit
function startEdit() {
  editTitle.value = playlist.value.title
  editDescription.value = playlist.value.description || ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
}

async function saveEdit() {
  if (!editTitle.value.trim()) return
  try {
    await playlistsAPI.update(route.params.id, {
      title: editTitle.value.trim(),
      description: editDescription.value.trim() || null,
    })
    playlist.value.title = editTitle.value.trim()
    playlist.value.description = editDescription.value.trim() || null
    editing.value = false
  } catch (e) {
    console.error('saveEdit error', e)
  }
}

// Add tracks
function debouncedSearch() {
  clearTimeout(searchTimer)
  if (!addSearch.value.trim()) { searchResults.value = []; return }
  searchTimer = setTimeout(searchTracks, 350)
}

async function searchTracks() {
  addLoading.value = true
  try {
    const { data } = await tracksAPI.list({ q: addSearch.value, per_page: 20 })
    searchResults.value = data.items
  } catch (e) {
    searchResults.value = []
  } finally {
    addLoading.value = false
  }
}

async function addTrack(track) {
  if (alreadyInPlaylist(track.id)) return
  try {
    await playlistsAPI.addTrack(route.params.id, track.id)
    await load()
  } catch (e) {
    console.error('addTrack error', e)
  }
}

async function removeTrack(trackId) {
  await playlistsAPI.removeTrack(route.params.id, trackId)
  await load()
}

async function deletePlaylist() {
  if (!confirm('Удалить плейлист?')) return
  await playlistsAPI.delete(route.params.id)
  router.push('/playlists')
}

function playAll() {
  if (trackList.value.length) player.playQueue(trackList.value)
}

function contextIcon(ctx) {
  return { work: '💻', rest: '🌙', sport: '🏋️', general: '🎵' }[ctx] || '🎵'
}

onMounted(load)
</script>
