<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from '../api/client'
import { useI18n } from '../i18n'
import { zonesForLocale } from '../markets'

const { t, locale } = useI18n()
const cards = ref([])
const error = ref('')
const geoZone = ref('')
const place = ref('')
const tick = ref(0)
let timer = null

const zones = computed(() => zonesForLocale(locale.value))
const placeOptions = computed(() => {
  const zone = zones.value.find((z) => z.id === geoZone.value)
  return zone?.places || []
})

async function loadCards() {
  error.value = ''
  try {
    const params = { lang: locale.value }
    if (geoZone.value) params.geo_zone = geoZone.value
    if (place.value) params.place = place.value
    cards.value = await api.listCards(params)
  } catch (e) {
    error.value = e.message || String(e)
  }
}

function onZoneChange() {
  place.value = ''
  loadCards()
}

function localLabel(card) {
  void tick.value
  if (!card.timezone) return card.local_time_label || ''
  try {
    const time = new Intl.DateTimeFormat(locale.value === 'zh' ? 'zh-CN' : 'en-US', {
      timeZone: card.timezone,
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(new Date())
    const city = card.city_label || card.region || card.country || card.timezone
    return `${city} · ${t.value.localTimePrefix} ${time}`
  } catch {
    return card.local_time_label || ''
  }
}

watch(locale, loadCards)

onMounted(() => {
  loadCards()
  timer = setInterval(() => {
    tick.value += 1
  }, 30000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <section class="panel">
    <h2>{{ t.cardsTitle }}</h2>
    <p class="lede">{{ t.cardsLede }}</p>

    <div class="filter-bar">
      <label class="filter-field">
        <span>{{ t.filterZone }}</span>
        <select v-model="geoZone" @change="onZoneChange">
          <option value="">{{ t.geoAll }}</option>
          <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.label }}</option>
        </select>
      </label>

      <label class="filter-field">
        <span>{{ t.filterPlace }}</span>
        <select v-model="place" :disabled="!geoZone" @change="loadCards">
          <option value="">{{ geoZone ? t.placeAll : t.pickZoneFirst }}</option>
          <option v-for="p in placeOptions" :key="p.id" :value="p.id">{{ p.label }}</option>
        </select>
      </label>
    </div>

    <p class="filter-hint">{{ t.directoryHint }}</p>

    <p v-if="error" class="error-box" style="margin-top: 1rem">{{ error }}</p>
    <p v-else-if="!cards.length" class="empty">{{ t.emptyCards }}</p>

    <div class="hit-list">
      <article v-for="card in cards" :key="card.id" class="hit">
        <div class="hit-head">
          <h3>{{ card.full_name }}</h3>
          <span v-if="card.geo_zone" class="tag">{{ card.geo_zone }}</span>
        </div>
        <p class="meta">
          {{ card.title || '—' }} · {{ card.company || '—' }} · {{ card.email || t.noEmail }}
        </p>
        <p class="meta">
          {{ card.country || '—' }} · {{ card.region || '—' }} ·
          {{ card.timezone_display || card.timezone || '—' }}
        </p>
        <p v-if="localLabel(card)" class="local-time">{{ localLabel(card) }}</p>
        <div>
          <span v-for="tag in card.tags || []" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </article>
    </div>
  </section>
</template>
