import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { eventsAPI } from '@/api'

export const usePlayerStore = defineStore('player', () => {
  const queue = ref([])          // array of track objects
  const currentIndex = ref(-1)
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const volume = ref(0.8)
  const context = ref('general')

  // Tracking for events
  let eventStartTime = null
  let eventStartPosition = 0

  const currentTrack = computed(() =>
    currentIndex.value >= 0 ? queue.value[currentIndex.value] : null
  )

  function playTrack(track, newQueue = null) {
    if (newQueue) queue.value = newQueue
    const idx = queue.value.findIndex(t => t.id === track.id)
    if (idx === -1) {
      queue.value.unshift(track)
      currentIndex.value = 0
    } else {
      currentIndex.value = idx
    }
    isPlaying.value = true
    eventStartTime = Date.now()
    eventStartPosition = 0
  }

  function playQueue(tracks) {
    queue.value = tracks
    currentIndex.value = 0
    isPlaying.value = true
    eventStartTime = Date.now()
  }

  function togglePlay() {
    isPlaying.value = !isPlaying.value
  }

  function next() {
    _recordEvent(false)
    if (currentIndex.value < queue.value.length - 1) {
      currentIndex.value++
      eventStartTime = Date.now()
    }
  }

  function prev() {
    _recordEvent(false)
    if (currentIndex.value > 0) {
      currentIndex.value--
      eventStartTime = Date.now()
    }
  }

  function onEnded() {
    _recordEvent(false)
    if (currentIndex.value < queue.value.length - 1) {
      currentIndex.value++
      eventStartTime = Date.now()
    } else {
      isPlaying.value = false
    }
  }

  function onTimeUpdate(time, dur) {
    currentTime.value = time
    duration.value = dur
  }

  function skipTrack() {
    _recordEvent(true)
    next()
  }

  function _recordEvent(skipped) {
    const track = currentTrack.value
    if (!track) return
    if (!eventStartTime) eventStartTime = Date.now()
    const playedSeconds = (Date.now() - eventStartTime) / 1000
    const playedRatio = duration.value > 0 ? Math.min(playedSeconds / duration.value, 1.0) : 0

    eventsAPI.record({
      track_id: track.id,
      played_seconds: playedSeconds,
      played_ratio: playedRatio,
      skipped,
      repeated: false,
      liked: false,
      context: context.value,
    }).catch(() => {})
  }

  function likeCurrentTrack() {
    const track = currentTrack.value
    if (!track) return
    eventsAPI.record({
      track_id: track.id,
      played_seconds: currentTime.value,
      played_ratio: duration.value > 0 ? currentTime.value / duration.value : 0,
      skipped: false,
      repeated: false,
      liked: true,
      context: context.value,
    }).catch(() => {})
  }

  return {
    queue, currentIndex, currentTrack, isPlaying,
    currentTime, duration, volume, context,
    playTrack, playQueue, togglePlay, next, prev,
    onEnded, onTimeUpdate, skipTrack, likeCurrentTrack,
  }
})
