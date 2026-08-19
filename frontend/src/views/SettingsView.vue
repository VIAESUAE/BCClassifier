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
const llmTest = ref(null)
const testing = ref(false)
const testingLlm = ref(false)
const testError = ref('')
const llmError = ref('')

onMounted(() => {
  Object.assign(form, getClientSettings())
  if (!form.openaiBaseUrl) form.openaiBaseUrl = 'https://openrouter.ai/api/v1'
  if (!form.model) form.model = 'google/gemma-2-9b-it:free'
})

function applyOpenRouterPreset() {
  form.openaiBaseUrl = 'https://openrouter.ai/api/v1'
  if (!form.model || form.model.includes('gpt-4')) {
    form.model = 'google/gemma-2-9b-it:free'
  }
}

function save() {
  saveClientSettings(form)
  savedMsg.value = t.value.settingsSaved
  testError.value = ''
  llmError.value = ''
}

async function testBackend() {
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

async function testLlm() {
  save()
  testingLlm.value = true
  llmError.value = ''
  llmTest.value = null
  try {
    llmTest.value = await api.testLlm()
  } catch (e) {
    llmError.value = e.message || String(e)
  } finally {
    testingLlm.value = false
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
        <span class="field-hint">{{ t.settingsApiBaseHint }}</span>
      </label>
      <label class="full">
        {{ t.settingsApiKey }}
        <input v-model="form.apiKey" type="password" autocomplete="off" placeholder="sk-or-..." />
      </label>
      <label class="full">
        {{ t.settingsOpenaiBase }}
        <input v-model="form.openaiBaseUrl" placeholder="https://openrouter.ai/api/v1" />
        <span class="field-hint">{{ t.settingsOpenaiBaseHint }}</span>
      </label>
      <label class="full">
        {{ t.settingsModel }}
        <input v-model="form.model" placeholder="google/gemma-2-9b-it:free" />
      </label>
    </div>

    <div class="cta-row">
      <button class="btn btn-ghost" type="button" @click="applyOpenRouterPreset">
        {{ t.settingsOpenRouterPreset }}
      </button>
    </div>

    <p class="filter-hint">{{ t.settingsHint }}</p>

    <div class="cta-row">
      <button class="btn btn-primary" type="button" @click="save">{{ t.settingsSave }}</button>
      <button class="btn btn-ghost" type="button" :disabled="testing" @click="testBackend">
        {{ testing ? t.settingsTesting : t.settingsTestBackend }}
      </button>
      <button class="btn btn-ghost" type="button" :disabled="testingLlm" @click="testLlm">
        {{ testingLlm ? t.settingsTesting : t.settingsTestLlm }}
      </button>
    </div>

    <p v-if="savedMsg" class="filter-hint" style="color: var(--accent-deep)">{{ savedMsg }}</p>
    <p v-if="testError" class="error-box" style="margin-top: 1rem">{{ testError }}</p>
    <p v-if="llmError" class="error-box" style="margin-top: 1rem">{{ llmError }}</p>
    <div v-if="health" class="panel" style="margin-top: 1rem; box-shadow: none">
      <p class="answer">
        Backend OK · cards={{ health.card_count }} · llm_key_detected={{ health.has_llm }}
      </p>
    </div>
    <div v-if="llmTest" class="panel" style="margin-top: 1rem; box-shadow: none">
      <p class="answer">LLM OK · sample: {{ llmTest.provider_sample }}</p>
    </div>
  </section>
</template>
