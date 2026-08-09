<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { api } from './api/client'
import { useI18n } from './i18n'

const { locale, setLocale, t } = useI18n()
const health = ref(null)

onMounted(async () => {
  try {
    health.value = await api.health()
  } catch {
    health.value = null
  }
})

watch(locale, () => {
  document.documentElement.lang = locale.value === 'zh' ? 'zh-CN' : 'en'
})

const banner = computed(() => {
  if (!health.value) return t.value.demoOff
  return t.value.demoOn
    .replace('{n}', String(health.value.card_count))
    .replace('{llm}', health.value.has_llm ? t.value.llmOn : t.value.llmOff)
})
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <RouterLink to="/" class="brand">
        <strong>CardLedger</strong>
        <span>{{ t.brandSub }}</span>
      </RouterLink>
      <div class="topbar-right">
        <nav class="nav">
          <RouterLink to="/search">{{ t.navAsk }}</RouterLink>
          <RouterLink to="/ingest">{{ t.navIngest }}</RouterLink>
          <RouterLink to="/cards">{{ t.navCards }}</RouterLink>
          <RouterLink to="/settings">{{ t.navSettings }}</RouterLink>
        </nav>
        <div class="lang-switch" role="group" aria-label="Language">
          <button type="button" :class="{ active: locale === 'zh' }" @click="setLocale('zh')">中文</button>
          <button type="button" :class="{ active: locale === 'en' }" @click="setLocale('en')">EN</button>
        </div>
      </div>
    </header>

    <div class="demo-banner">{{ banner }}</div>

    <RouterView />

    <p class="footer-note">{{ t.footer }}</p>
  </div>
</template>
