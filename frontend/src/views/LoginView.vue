<template>
  <div class="min-h-screen flex items-center justify-center bg-surface">
    <div class="w-full max-w-md bg-surface-card rounded-2xl p-8 shadow-2xl">
      <div class="text-center mb-8">
        <div class="text-4xl mb-2">🎵</div>
        <h1 class="text-2xl font-bold text-white">Фонотека</h1>
        <p class="text-slate-400 mt-1">Войдите в свой аккаунт</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm text-slate-400 mb-1">Имя пользователя</label>
          <input v-model="form.username" type="text" required
            class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2.5
                   text-white focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div>
          <label class="block text-sm text-slate-400 mb-1">Пароль</label>
          <input v-model="form.password" type="password" required
            class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2.5
                   text-white focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div v-if="error" class="text-red-400 text-sm">{{ error }}</div>
        <button type="submit" :disabled="loading"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white
                 font-semibold py-2.5 rounded-lg transition">
          {{ loading ? 'Входим...' : 'Войти' }}
        </button>
      </form>

      <p class="text-center text-slate-400 mt-6 text-sm">
        Нет аккаунта?
        <router-link to="/register" class="text-brand-500 hover:underline">Зарегистрироваться</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ username: '', password: '' })
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await authStore.login(form.value.username, form.value.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Неверные данные'
  } finally {
    loading.value = false
  }
}
</script>
