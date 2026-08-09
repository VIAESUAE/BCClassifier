import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import IngestView from '../views/IngestView.vue'
import SearchView from '../views/SearchView.vue'
import CardsView from '../views/CardsView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/ingest', name: 'ingest', component: IngestView },
    { path: '/search', name: 'search', component: SearchView },
    { path: '/cards', name: 'cards', component: CardsView },
    { path: '/settings', name: 'settings', component: SettingsView },
  ],
  scrollBehavior() {
    return { top: 0 }
  },
})

export default router
