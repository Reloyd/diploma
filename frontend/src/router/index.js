import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { guest: true } },
  { path: '/register', component: () => import('@/views/RegisterView.vue'), meta: { guest: true } },
  {
    path: '/',
    component: () => import('@/views/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/catalog' },
      { path: 'catalog', component: () => import('@/views/CatalogView.vue') },
      { path: 'library', component: () => import('@/views/LibraryView.vue') },
      { path: 'playlists', component: () => import('@/views/PlaylistsView.vue') },
      { path: 'playlists/:id', component: () => import('@/views/PlaylistDetailView.vue') },
      { path: 'recommendations', component: () => import('@/views/RecommendationsView.vue') },
      { path: 'assistant', component: () => import('@/views/AssistantView.vue') },
      { path: 'artists/:id', component: () => import('@/views/ArtistView.vue') },
      { path: 'albums/:id', component: () => import('@/views/AlbumView.vue') },
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) return '/login'
  if (to.meta.guest && token) return '/'
})

export default router
