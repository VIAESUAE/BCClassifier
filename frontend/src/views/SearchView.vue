<script setup>
import { ref, watch } from 'vue'
import { api } from '../api/client'
import { useI18n } from '../i18n'

const { t, examples, locale } = useI18n()
const query = ref(t.value.defaultQuery)
const loading = ref(false)
const error = ref('')
const result = ref(null)

watch(locale, () => {
  query.value = t.value.defaultQuery
  result.value = null
  error.value = ''
})

async function runSearch(q) {
  if (q) query.value = q
  if (!query.value.trim()) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.ragQuery(query.value.trim())
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="panel">
    <h2>{{ t.searchTitle }}</h2>
    <p class="lede">{{ t.searchLede }}</p>

    <div class="search-box">
      <input
        v-model="query"
        type="search"
        :placeholder="t.searchPlaceholder"
        @keydown.enter="runSearch()"
      />
      <button class="btn btn-primary" type="button" :disabled="loading" @click="runSearch()">
        {{ loading ? t.searching : t.searchBtn }}
      </button>
    </div>

    <div class="examples">
      <button v-for="ex in examples" :key="ex" class="chip" type="button" @click="runSearch(ex)">
        {{ ex }}
      </button>
    </div>

    <p v-if="error" class="error-box" style="margin-top: 1rem">{{ error }}</p>

    <div v-if="result" style="margin-top: 1.25rem">
      <p v-if="result.demo_notice" class="lede">{{ result.demo_notice }}</p>
      <div class="panel" style="box-shadow: none">
        <h3 style="margin-top: 0; font-family: var(--font-display); font-weight: 400">{{ t.answer }}</h3>
        <p class="answer">{{ result.answer }}</p>
      </div>

      <p class="lede" style="margin-top: 1rem">
        {{ t.filters }}
        <template v-if="result.filters_applied?.geo_zones?.length">
          geo {{ result.filters_applied.geo_zones.join(', ') }} ·
        </template>
        <template v-if="result.filters_applied?.regions?.length">
          {{ t.regionLabel }} {{ result.filters_applied.regions.join(', ') }} ·
        </template>
        <template v-if="result.filters_applied?.tags?.length">
          {{ t.tagsLabel }} {{ result.filters_applied.tags.join(', ') }}
        </template>
        <template
          v-if="
            !result.filters_applied?.regions?.length &&
            !result.filters_applied?.tags?.length &&
            !result.filters_applied?.geo_zones?.length
          "
        >
          {{ t.filterSemantic }}
        </template>
      </p>

      <div class="hit-list">
        <article v-for="hit in result.hits" :key="hit.card.id" class="hit">
          <div class="hit-head">
            <h3>{{ hit.card.full_name }}</h3>
            <span v-if="hit.card.geo_zone" class="tag">{{ hit.card.geo_zone }}</span>
          </div>
          <p class="meta">
            {{ hit.card.title || '—' }} · {{ hit.card.company || '—' }} ·
            {{ hit.card.region || '—' }} · {{ hit.card.timezone_display || hit.card.timezone || '—' }}
          </p>
          <p v-if="hit.card.local_time_label" class="local-time">{{ hit.card.local_time_label }}</p>
          <div>
            <span v-for="tag in hit.card.tags || []" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <p class="reason">score {{ hit.score }} · {{ hit.match_reason }}</p>
        </article>
      </div>
    </div>
  </section>
</template>
