<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api, getClientSettings, saveClientSettings } from '../api/client'
import { useI18n } from '../i18n'

const { t } = useI18n()
const form = reactive({
  apiBase: '',
  apiKey: '',
  openaiBaseUrl: '',
  model: '',
})
const savedMsg = ref('')
const health = ref(null)
const testing = ref(false)
const testError = ref('')

onMounted(() => {
  Object.assign(form, getClientSettings())
  if (!form.openaiBaseUrl) form.openaiBaseUrl = 'https://api.openai.com/v1'
  if (!form.model) form.model = 'gpt-4o-mini'
})

function save() {
  saveClientSettings(form)
  savedMsg.value = t.value.settingsSaved
  testError.value = ''
}

async function testConnection() {
  save()
  testing.value = true
  testError.value = ''
  health.value = null
  try {
    health.value = await api.health()
  } catch (e) {
    testError.value = e.message || String(e)
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <section class="panel">
    <h2>{{ t.settingsTitle }}</h2>
    <p class="lede">{{ t.settingsLede }}</p>

    <div class="form-grid" style="margin-top: 0.5rem">
      <label class="full">
        {{ t.settingsApiBase }}
        <input v-model="form.apiBase" placeholder="http://127.0.0.1:8000" />
      </label>
      <label class="full">
        {{ t.settingsApiKey }}
        <input v-model="form.apiKey" type="password" autocomplete="off" placeholder="sk-..." />
      </label>
      <label class="full">
        {{ t.settingsOpenaiBase }}
        <input v-model="form.openaiBaseUrl" placeholder="https://api.openai.com/v1" />
      </label>
      <label class="full">
        {{ t.settingsModel }}
        <input v-model="form.model" placeholder="gpt-4o-mini" />
      </label>
    </div>

    <p class="filter-hint">{{ t.settingsHint }}</p>

    <div class="cta-row">
      <button class="btn btn-primary" type="button" @click="save">{{ t.settingsSave }}</button>
      <button class="btn btn-ghost" type="button" :disabled="testing" @click="testConnection">
        {{ testing ? t.settingsTesting : t.settingsTest }}
      </button>
    </div>

    <p v-if="savedMsg" class="filter-hint" style="color: var(--accent-deep)">{{ savedMsg }}</p>
    <p v-if="testError" class="error-box" style="margin-top: 1rem">{{ testError }}</p>
    <div v-if="health" class="panel" style="margin-top: 1rem; box-shadow: none">
      <p class="answer">
        status={{ health.status }} · cards={{ health.card_count }} · llm={{ health.has_llm }}
      </p>
    </div>
  </section>
</template>
