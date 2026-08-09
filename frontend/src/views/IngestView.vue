<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useI18n } from '../i18n'

const { t } = useI18n()
const router = useRouter()
const step = ref(1)
const loading = ref(false)
const error = ref('')
const preview = ref(null)
const fields = reactive({
  full_name: '',
  company: '',
  title: '',
  phone: '',
  email: '',
  country: '',
  timezone: '',
  region: '',
  geo_zone: '',
  tags: '',
  notes: '',
})

function applyFields(extracted) {
  fields.full_name = extracted.full_name || ''
  fields.company = extracted.company || ''
  fields.title = extracted.title || ''
  fields.phone = extracted.phone || ''
  fields.email = extracted.email || ''
  fields.country = extracted.country || ''
  fields.timezone = extracted.timezone || ''
  fields.region = extracted.region || ''
  fields.geo_zone = extracted.geo_zone || ''
  fields.tags = (extracted.tags || []).join(', ')
  fields.notes = extracted.notes || ''
}

async function onFile(file) {
  if (!file) return
  loading.value = true
  error.value = ''
  try {
    const data = await api.ingestPreview(file)
    preview.value = data
    applyFields(data.extracted)
    step.value = 2
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function onInputChange(e) {
  const file = e.target.files?.[0]
  onFile(file)
}

function onDrop(e) {
  e.preventDefault()
  e.currentTarget.classList.remove('dragover')
  const file = e.dataTransfer.files?.[0]
  onFile(file)
}

async function confirmSave() {
  if (!preview.value) return
  loading.value = true
  error.value = ''
  try {
    const payload = {
      full_name: fields.full_name,
      company: fields.company || null,
      title: fields.title || null,
      phone: fields.phone || null,
      email: fields.email || null,
      country: fields.country || null,
      timezone: fields.timezone || null,
      region: fields.region || null,
      geo_zone: fields.geo_zone || null,
      tags: fields.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
      notes: fields.notes || null,
    }
    await api.ingestConfirm(preview.value.preview_id, payload)
    step.value = 3
  } catch (e) {
    error.value = e.message || String(e)
  } finally {
    loading.value = false
  }
}

function resetWizard() {
  step.value = 1
  preview.value = null
  error.value = ''
}

function dedupeText(hit) {
  return t.value.dedupe
    .replace('{name}', hit.full_name)
    .replace('{contact}', hit.email || hit.phone || '—')
}
</script>

<template>
  <section class="panel">
    <h2>{{ t.ingestTitle }}</h2>
    <p class="lede">{{ t.ingestLede }}</p>

    <div class="steps">
      <span class="step-pill" :class="{ active: step === 1, done: step > 1 }">{{ t.step1 }}</span>
      <span class="step-pill" :class="{ active: step === 2, done: step > 2 }">{{ t.step2 }}</span>
      <span class="step-pill" :class="{ active: step === 3 }">{{ t.step3 }}</span>
    </div>

    <p v-if="error" class="error-box">{{ error }}</p>

    <div v-if="step === 1">
      <label
        class="dropzone"
        @dragover.prevent="(e) => e.currentTarget.classList.add('dragover')"
        @dragleave.prevent="(e) => e.currentTarget.classList.remove('dragover')"
        @drop="onDrop"
      >
        <strong>{{ loading ? t.dropReading : t.dropStrong }}</strong>
        <span>{{ t.dropHint }}</span>
        <input type="file" accept="image/*" hidden :disabled="loading" @change="onInputChange" />
      </label>
    </div>

    <div v-else-if="step === 2 && preview">
      <ul v-if="preview.warnings?.length" class="warn-list">
        <li v-for="(w, i) in preview.warnings" :key="i">{{ w }}</li>
      </ul>
      <ul v-if="preview.dedupe_hits?.length" class="warn-list">
        <li v-for="hit in preview.dedupe_hits" :key="hit.id">{{ dedupeText(hit) }}</li>
      </ul>

      <div class="grid-2">
        <div>
          <p class="lede">{{ t.original }}</p>
          <img class="preview-img" :src="api.fileUrl(preview.original_image_url)" alt="" />
        </div>
        <div>
          <p class="lede">{{ t.processed }}</p>
          <img class="preview-img" :src="api.fileUrl(preview.processed_image_url)" alt="" />
        </div>
      </div>

      <div class="panel" style="margin-top: 1rem; box-shadow: none">
        <p class="lede">{{ t.ocrHint }}</p>
        <pre class="answer" style="max-height: 160px; overflow: auto; font-size: 0.85rem">{{
          preview.raw_ocr || t.emptyOcr
        }}</pre>
      </div>

      <div class="form-grid" style="margin-top: 1rem">
        <label>{{ t.fieldName }}<input v-model="fields.full_name" /></label>
        <label>{{ t.fieldCompany }}<input v-model="fields.company" /></label>
        <label>{{ t.fieldTitle }}<input v-model="fields.title" /></label>
        <label>{{ t.fieldPhone }}<input v-model="fields.phone" /></label>
        <label>{{ t.fieldEmail }}<input v-model="fields.email" /></label>
        <label>{{ t.fieldCountry }}<input v-model="fields.country" placeholder="Singapore / United States" /></label>
        <label>{{ t.fieldTimezone }}<input v-model="fields.timezone" placeholder="Asia/Singapore" /></label>
        <label>{{ t.fieldRegion }}<input v-model="fields.region" placeholder="Singapore" /></label>
        <label>
          {{ t.fieldGeoZone }}
          <select v-model="fields.geo_zone">
            <option value="">—</option>
            <option value="APAC">APAC</option>
            <option value="NA">NA</option>
            <option value="LATAM">LATAM</option>
            <option value="EU">EU</option>
            <option value="MEA">MEA</option>
          </select>
        </label>
        <label>{{ t.fieldTags }}<input v-model="fields.tags" placeholder="payments, fund bridging" /></label>
        <label class="full">{{ t.fieldNotes }}<textarea v-model="fields.notes" /></label>
      </div>

      <div class="cta-row">
        <button class="btn btn-ghost" type="button" :disabled="loading" @click="step = 1">{{ t.back }}</button>
        <button class="btn btn-primary" type="button" :disabled="loading || !fields.full_name" @click="confirmSave">
          {{ loading ? t.saving : t.confirm }}
        </button>
      </div>
    </div>

    <div v-else-if="step === 3">
      <p class="lede">{{ t.doneLede }}</p>
      <div class="cta-row">
        <button class="btn btn-primary" type="button" @click="router.push('/search')">{{ t.askNow }}</button>
        <button class="btn btn-ghost" type="button" @click="resetWizard">{{ t.scanAnother }}</button>
      </div>
    </div>
  </section>
</template>
