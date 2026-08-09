<script setup>
import { RouterLink } from 'vue-router'
import { useI18n } from '../i18n'

const { t } = useI18n()
</script>

<template>
  <section class="hero">
    <h1>{{ t.homeTitle }}</h1>
    <p>{{ t.homeBody }}</p>
    <div class="cta-row">
      <RouterLink class="btn btn-primary" to="/search">{{ t.homeAsk }}</RouterLink>
      <RouterLink class="btn btn-ghost" to="/ingest">{{ t.homeScan }}</RouterLink>
    </div>
  </section>
</template>
