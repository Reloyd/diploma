<template>
  <div class="min-h-screen flex items-center justify-center bg-surface">
    <div class="w-full max-w-md bg-surface-card rounded-2xl p-8 shadow-2xl">
      <div class="text-center mb-8">
        <div class="text-4xl mb-2">🎵</div>
        <h1 class="text-2xl font-bold text-white">Создать аккаунт</h1>
      </div>
      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm text-slate-400 mb-1">Имя пользователя</label>
          <input v-model="form.username" type="text" required
            class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2.5 text-white
                   focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div>
          <label class="block text-sm text-slate-400 mb-1">Email</label>
          <input v-model="form.email" type="email" required
            class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2.5 text-white
                   focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div>
          <label class="block text-sm text-slate-400 mb-1">Пароль</label>
          <input v-model="form.password" type="password" required minlength="6"
            class="w-full bg-surface-elevated border border-slate-700 rounded-lg px-4 py-2.5 text-white
                   focus:outline-none focus:border-brand-500 transition" />
        </div>
        <div v-if="error" class="text-red-400 text-sm">{{ error }}</div>
        <button type="submit" :disabled="loading"
          class="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition">
          {{ loading ? 'Регистрируем...' : 'Зарегистрироваться' }}
        </button>
      </form>
      <p class="text-center text-slate-400 mt-6 text-sm">
        Уже есть аккаунт?
        <router-link to="/login" class="text-brand-500 hover:underline">Войти</router-link>
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
const form = ref({ username: '', email: '', password: '' })
const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  loading.value = true
  try {
    await authStore.register(form.value.username, form.value.email, form.value.password)
    router.push('/')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка регистрации'
  } finally {
    loading.value = false
  }
}
</script>
