<script setup>
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { KIM_CONTACT, KIM_MAILS, KIM_NOW } from '../data/kimTimeline'

const props = defineProps({
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const pageRef = ref(null)
const timelineRef = ref(null)
const connectorsRef = ref(null)
const activeId = ref(null)
let leaveTimer = null
let resizeTimer = null

const PAD_TOP = 48
const PAD_BOTTOM = 88
const TIMELINE_HEIGHT = 1200

function parseDate(iso) {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).getTime()
}

function formatDate(iso) {
  const [y, m, d] = iso.split('-')
  return `${y}.${m}.${d}`
}

function collectBounds() {
  const stamps = [parseDate(KIM_NOW)]
  KIM_MAILS.forEach((m) => {
    stamps.push(parseDate(m.sent))
    if (m.ddl) stamps.push(parseDate(m.ddl))
  })
  return { min: Math.min(...stamps), max: Math.max(...stamps) }
}

function yFor(iso, min, max, height) {
  const t = parseDate(iso)
  const ratio = (t - min) / (max - min || 1)
  return PAD_TOP + ratio * (height - PAD_TOP - PAD_BOTTOM)
}

function clearActive() {
  pageRef.value?.classList.remove('is-focusing')
  timelineRef.value?.querySelectorAll('.is-active').forEach((el) => el.classList.remove('is-active'))
  connectorsRef.value?.querySelectorAll('.is-active').forEach((el) => el.classList.remove('is-active'))
  activeId.value = null
}

function activate(id) {
  if (leaveTimer) {
    clearTimeout(leaveTimer)
    leaveTimer = null
  }
  if (activeId.value === id) return

  clearActive()
  activeId.value = id
  pageRef.value?.classList.add('is-focusing')

  timelineRef.value?.querySelectorAll(`[data-id="${id}"]`).forEach((el) => {
    if (
      el.classList.contains('tl-mail') ||
      el.classList.contains('tl-node') ||
      el.classList.contains('tl-ddl-date-label')
    ) {
      el.classList.add('is-active')
    }
  })
  connectorsRef.value?.querySelector(`line[data-id="${id}"]`)?.classList.add('is-active')
}

function scheduleDeactivate(id) {
  if (leaveTimer) clearTimeout(leaveTimer)
  leaveTimer = setTimeout(() => {
    const stillHot = timelineRef.value?.querySelector(`[data-hot="${id}"]:hover`)
    if (!stillHot) clearActive()
  }, 50)
}

function bindHot(el, mailId) {
  el.addEventListener('mouseenter', () => activate(mailId))
  el.addEventListener('mouseleave', () => scheduleDeactivate(mailId))
  el.addEventListener('focus', () => activate(mailId))
  el.addEventListener('blur', () => scheduleDeactivate(mailId))
}

function build() {
  const timeline = timelineRef.value
  const svg = connectorsRef.value
  if (!timeline || !svg) return

  timeline.style.height = `${TIMELINE_HEIGHT}px`
  svg.setAttribute('viewBox', `0 0 ${timeline.clientWidth || 800} ${TIMELINE_HEIGHT}`)
  svg.setAttribute('width', '100%')
  svg.setAttribute('height', String(TIMELINE_HEIGHT))

  const { min, max } = collectBounds()
  const grayRail = timeline.querySelector('.tl-rail.gray')
  const blackRail = timeline.querySelector('.tl-rail.black')
  const gX = (grayRail?.offsetLeft ?? 32) + 0.5
  const bX = (blackRail?.offsetLeft ?? 152) + 0.5

  const nowY = yFor(KIM_NOW, min, max, TIMELINE_HEIGHT)
  const nowEl = timeline.querySelector('.tl-now')
  if (nowEl) nowEl.style.top = `${nowY}px`

  timeline.querySelectorAll('.tl-mail, .tl-node, .tl-ddl-date-label').forEach((el) => el.remove())
  svg.innerHTML = ''

  KIM_MAILS.forEach((mail) => {
    const sentY = yFor(mail.sent, min, max, TIMELINE_HEIGHT)

    const mailEl = document.createElement('article')
    mailEl.className = 'tl-mail'
    mailEl.dataset.id = mail.id
    mailEl.style.top = `${sentY}px`
    mailEl.innerHTML = `
      <div class="tl-mail-hit" data-hot="${mail.id}">
        <div class="tl-mail-subject">
          ${mail.subject}
          <span class="tl-mail-side ${mail.side}">${mail.side === 'us' ? '我方' : '对方'}</span>
        </div>
        <div class="tl-mail-date">${formatDate(mail.sent)}</div>
      </div>
      <div class="tl-summary" data-hot="${mail.id}">
        <div class="tl-summary-kicker">摘要 · AI Translated</div>
        <div class="tl-summary-body">${mail.summary}</div>
        ${
          mail.ddlNote
            ? `<div class="tl-summary-ddl"><strong>DDL</strong> · ${mail.ddlNote}</div>`
            : ''
        }
        <div class="tl-hint">点击查看全文（示意）</div>
      </div>
    `
    timeline.appendChild(mailEl)

    const sendNode = document.createElement('button')
    sendNode.type = 'button'
    sendNode.className = `tl-node send ${mail.side}`
    sendNode.dataset.id = mail.id
    sendNode.dataset.hot = mail.id
    sendNode.style.top = `${sentY}px`
    sendNode.setAttribute('aria-label', mail.subject)
    timeline.appendChild(sendNode)

    if (mail.ddl) {
      const ddlY = yFor(mail.ddl, min, max, TIMELINE_HEIGHT)

      const ddlNode = document.createElement('button')
      ddlNode.type = 'button'
      ddlNode.className = `tl-node ddl ${mail.side}`
      ddlNode.dataset.id = mail.id
      ddlNode.dataset.hot = mail.id
      ddlNode.style.top = `${ddlY}px`
      ddlNode.setAttribute('aria-label', `DDL ${mail.ddl}`)
      timeline.appendChild(ddlNode)

      const ddlLabel = document.createElement('div')
      ddlLabel.className = 'tl-ddl-date-label'
      ddlLabel.dataset.id = mail.id
      ddlLabel.style.top = `${ddlY}px`
      ddlLabel.textContent = formatDate(mail.ddl)
      timeline.appendChild(ddlLabel)

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line')
      line.setAttribute('x1', String(bX))
      line.setAttribute('y1', String(sentY))
      line.setAttribute('x2', String(gX))
      line.setAttribute('y2', String(ddlY))
      line.setAttribute('stroke', mail.side === 'us' ? '#e00000' : '#1a00e0')
      line.dataset.id = mail.id
      svg.appendChild(line)
    }

    bindHot(mailEl.querySelector('.tl-mail-hit'), mail.id)
    bindHot(mailEl.querySelector('.tl-summary'), mail.id)
    bindHot(sendNode, mail.id)
    const ddlBtn = timeline.querySelector(`.tl-node.ddl[data-id="${mail.id}"]`)
    if (ddlBtn) bindHot(ddlBtn, mail.id)
  })

  if (activeId.value) {
    const keep = activeId.value
    activeId.value = null
    activate(keep)
  }
}

function onKeydown(e) {
  if (!props.open) return
  if (e.key === 'Escape') {
    if (activeId.value) clearActive()
    else emit('close')
  }
}

function onResize() {
  clearTimeout(resizeTimer)
  resizeTimer = setTimeout(build, 120)
}

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
      await nextTick()
      build()
    } else {
      document.body.style.overflow = ''
      clearActive()
    }
  }
)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('resize', onResize)
  if (leaveTimer) clearTimeout(leaveTimer)
  if (resizeTimer) clearTimeout(resizeTimer)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="timeline-overlay" role="dialog" aria-modal="true" aria-label="Email timeline">
      <button type="button" class="timeline-back" aria-label="Back" @click="emit('close')">
        ←
      </button>

      <div ref="pageRef" class="tl-page">
        <aside class="tl-hud">
          <div class="tl-hud-label">Contact</div>
          <h1 class="tl-hud-name">Kim<br />Wexler</h1>
          <div class="tl-hud-meta">
            <div class="tl-hud-row">
              <span class="tl-hud-key">Title</span>
              <span class="tl-hud-val">{{ KIM_CONTACT.title }}</span>
            </div>
            <div class="tl-hud-row">
              <span class="tl-hud-key">Firm</span>
              <span class="tl-hud-val">{{ KIM_CONTACT.firm }}</span>
            </div>
            <div class="tl-hud-row">
              <span class="tl-hud-key">Email</span>
              <span class="tl-hud-val">{{ KIM_CONTACT.email }}</span>
            </div>
            <div class="tl-hud-row">
              <span class="tl-hud-key">Locale</span>
              <span class="tl-hud-val">{{ KIM_CONTACT.locale }}</span>
            </div>
          </div>
          <div class="tl-hud-legend">
            <div class="legend-item"><span class="legend-swatch us"></span>我方往来</div>
            <div class="legend-item"><span class="legend-swatch them"></span>对方往来</div>
            <div class="legend-item"><span class="legend-swatch send"></span>发送节点</div>
            <div class="legend-item"><span class="legend-swatch ddl"></span>截止日期</div>
          </div>
        </aside>

        <main class="tl-stage">
          <header class="tl-stage-header">
            <div class="tl-stage-title">Correspondence Timeline</div>
            <div class="tl-stage-range">2026.05 — 2026.08</div>
          </header>

          <div ref="timelineRef" class="tl-timeline">
            <div class="tl-rails">
              <div class="tl-rail gray"><span class="tl-rail-caption">DDL</span></div>
              <div class="tl-rail black"><span class="tl-rail-caption">Sent</span></div>
            </div>

            <svg ref="connectorsRef" class="tl-connectors" xmlns="http://www.w3.org/2000/svg"></svg>
            <div class="tl-now">
              <div class="tl-now-line"></div>
              <div class="tl-now-tick"></div>
              <div class="tl-now-label">Now · 2026.08.11</div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.timeline-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: #fbfbf9;
  overflow: auto;
}

.timeline-back {
  position: fixed;
  top: 1.25rem;
  left: 1.25rem;
  z-index: 1001;
  appearance: none;
  border: 0;
  background: rgba(251, 251, 249, 0.72);
  backdrop-filter: blur(18px) saturate(1.1);
  -webkit-backdrop-filter: blur(18px) saturate(1.1);
  color: #121212;
  font-family: "Cormorant Garamond", "Noto Serif SC", serif;
  font-size: 1.35rem;
  line-height: 1;
  padding: 0.65rem 0.85rem;
  cursor: pointer;
  transition: background 0.2s ease;
}

.timeline-back:hover {
  background: rgba(251, 251, 249, 0.92);
}

.tl-page {
  --tl-bg: #fbfbf9;
  --tl-ink: #121212;
  --tl-muted: #6a6a66;
  --tl-line-gray: #c5c5c0;
  --tl-line-black: #1a1a1a;
  --tl-us: #e00000;
  --tl-them: #1a00e0;
  --tl-now: #121212;
  --tl-hud-w: 240px;
  --tl-rail-gap: 120px;
  --tl-dot: 10px;

  display: grid;
  grid-template-columns: var(--tl-hud-w) 1fr;
  min-height: 100vh;
  color: var(--tl-ink);
  font-family: "Noto Serif SC", "Songti SC", "SimSun", serif;
  font-weight: 400;
  -webkit-font-smoothing: antialiased;
}

.tl-hud {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  padding: 3.5rem 1.75rem 2rem 2.25rem;
  border-right: 1px solid rgba(18, 18, 18, 0.08);
  transition: filter 0.35s ease, opacity 0.35s ease;
}

.tl-hud-label {
  font-family: "Cormorant Garamond", "Noto Serif SC", serif;
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--tl-muted);
  margin-bottom: 2.25rem;
}

.tl-hud-name {
  font-family: "Cormorant Garamond", "Noto Serif SC", serif;
  font-size: 2rem;
  font-weight: 500;
  line-height: 1.15;
  letter-spacing: 0.01em;
  margin: 0 0 1.75rem;
}

.tl-hud-meta {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.tl-hud-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.tl-hud-key {
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--tl-muted);
  font-family: "Cormorant Garamond", serif;
}

.tl-hud-val {
  font-size: 0.88rem;
  line-height: 1.45;
}

.tl-hud-legend {
  margin-top: auto;
  padding-top: 3rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  font-size: 0.72rem;
  color: var(--tl-muted);
}

.legend-swatch {
  width: 14px;
  height: 1px;
  flex-shrink: 0;
}

.legend-swatch.us {
  background: var(--tl-us);
  height: 1.5px;
}

.legend-swatch.them {
  background: var(--tl-them);
  height: 1.5px;
}

.legend-swatch.ddl {
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--tl-line-gray);
  border-radius: 50%;
  background: transparent;
}

.legend-swatch.send {
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--tl-line-black);
  border-radius: 50%;
  background: transparent;
}

.tl-stage {
  position: relative;
  padding: 3.5rem 3rem 6rem 2.5rem;
}

.tl-stage-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 2.5rem;
  padding-left: calc(2rem + var(--tl-rail-gap) + 1.5rem);
  transition: filter 0.35s ease, opacity 0.35s ease;
}

.tl-stage-title {
  font-family: "Cormorant Garamond", serif;
  font-size: 0.75rem;
  letter-spacing: 0.28em;
  text-transform: uppercase;
  color: var(--tl-muted);
}

.tl-stage-range {
  font-size: 0.75rem;
  color: var(--tl-muted);
  letter-spacing: 0.04em;
}

.tl-timeline {
  position: relative;
  min-height: 920px;
}

.tl-rails {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.tl-rail {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
}

.tl-rail.gray {
  left: 2rem;
  background: var(--tl-line-gray);
}

.tl-rail.black {
  left: calc(2rem + var(--tl-rail-gap));
  background: var(--tl-line-black);
}

.tl-rail-caption {
  position: absolute;
  top: -1.6rem;
  left: 0;
  font-family: "Cormorant Garamond", serif;
  font-size: 0.65rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--tl-muted);
  white-space: nowrap;
  transform: translateX(-50%);
}

.tl-connectors {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
  pointer-events: none;
  transition: filter 0.35s ease, opacity 0.35s ease;
}

.tl-connectors :deep(line) {
  stroke-width: 1;
  fill: none;
}

.tl-now {
  position: absolute;
  left: 0;
  right: 0;
  height: 0;
  z-index: 5;
  pointer-events: none;
  transition: filter 0.35s ease, opacity 0.35s ease;
}

.tl-now-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  border-top: 1px solid var(--tl-now);
  opacity: 0.85;
}

.tl-now-label {
  position: absolute;
  right: 0;
  top: -0.85rem;
  font-family: "Cormorant Garamond", serif;
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  background: var(--tl-bg);
  padding-left: 0.6rem;
}

.tl-now-tick {
  position: absolute;
  left: calc(2rem + var(--tl-rail-gap));
  top: 0;
  width: 7px;
  height: 7px;
  background: var(--tl-now);
  transform: translate(-50%, -50%) rotate(45deg);
}

.tl-page.is-focusing .tl-hud,
.tl-page.is-focusing .tl-stage-header,
.tl-page.is-focusing .tl-now,
.tl-page.is-focusing :deep(.tl-mail:not(.is-active)),
.tl-page.is-focusing :deep(.tl-node:not(.is-active)),
.tl-page.is-focusing :deep(.tl-ddl-date-label:not(.is-active)),
.tl-page.is-focusing .tl-connectors :deep(line:not(.is-active)) {
  filter: blur(7px);
  opacity: 0.32;
}

.tl-page.is-focusing :deep(.tl-mail.is-active) {
  filter: none;
  opacity: 1;
  z-index: 30;
}

.tl-page.is-focusing :deep(.tl-node.is-active),
.tl-page.is-focusing :deep(.tl-ddl-date-label.is-active) {
  filter: none;
  opacity: 1;
  z-index: 31;
}

.tl-page.is-focusing .tl-connectors :deep(line.is-active) {
  filter: none;
  opacity: 1;
  stroke-width: 1.35;
}

.tl-page.is-focusing :deep(.tl-mail.is-active .tl-summary) {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  filter: none;
}

@media (max-width: 860px) {
  .tl-page {
    grid-template-columns: 1fr;
    --tl-rail-gap: 88px;
  }

  .tl-hud {
    position: relative;
    height: auto;
    border-right: none;
    border-bottom: 1px solid rgba(18, 18, 18, 0.08);
    padding: 2rem 1.5rem;
  }

  .tl-hud-legend {
    margin-top: 2rem;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 1rem 1.5rem;
  }

  .tl-stage {
    padding: 2rem 1.25rem 4rem;
  }

  .tl-stage-header {
    padding-left: 0;
    flex-direction: column;
    gap: 0.4rem;
  }

  .timeline-back {
    top: 0.75rem;
    left: 0.75rem;
  }
}
</style>

<style>
/* Dynamically inserted timeline nodes (unscoped) */
.tl-mail {
  position: absolute;
  left: calc(2rem + 120px + 1.5rem);
  right: 1rem;
  transform: translateY(-50%);
  z-index: 3;
  pointer-events: none;
  transition: filter 0.35s ease, opacity 0.35s ease;
}

.tl-mail-hit {
  display: block;
  width: fit-content;
  max-width: 28rem;
  pointer-events: auto;
  cursor: pointer;
}

.tl-mail-subject {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.4;
  color: #121212;
}

.tl-mail-date {
  margin-top: 0.2rem;
  font-family: "Cormorant Garamond", serif;
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  color: #6a6a66;
}

.tl-mail-side {
  display: inline-block;
  margin-left: 0.55rem;
  font-size: 0.65rem;
  letter-spacing: 0.12em;
}

.tl-mail-side.us {
  color: #e00000;
}

.tl-mail-side.them {
  color: #1a00e0;
}

.tl-summary {
  position: absolute;
  left: 0;
  top: calc(100% + 0.65rem);
  width: min(26rem, 70vw);
  padding: 1.1rem 1.2rem 1.15rem;
  background: rgba(251, 251, 249, 0.72);
  backdrop-filter: blur(18px) saturate(1.1);
  -webkit-backdrop-filter: blur(18px) saturate(1.1);
  opacity: 0;
  visibility: hidden;
  transform: translateY(4px);
  transition: opacity 0.3s ease, transform 0.3s ease, visibility 0.3s;
  pointer-events: none;
  z-index: 20;
}

.tl-mail.is-active .tl-summary {
  pointer-events: auto;
}

.tl-summary-kicker {
  font-family: "Cormorant Garamond", serif;
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: #6a6a66;
  margin-bottom: 0.55rem;
}

.tl-summary-body {
  font-size: 0.86rem;
  line-height: 1.7;
  font-weight: 300;
  color: #121212;
}

.tl-summary-ddl {
  margin-top: 0.75rem;
  padding-top: 0.7rem;
  border-top: 1px solid rgba(18, 18, 18, 0.08);
  font-size: 0.78rem;
  line-height: 1.5;
  color: #6a6a66;
}

.tl-summary-ddl strong {
  font-weight: 500;
  color: #121212;
}

.tl-hint {
  margin-top: 0.55rem;
  font-family: "Cormorant Garamond", serif;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  color: #6a6a66;
  font-style: italic;
}

.tl-node {
  position: absolute;
  z-index: 2;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fbfbf9;
  cursor: pointer;
  transition: transform 0.25s ease;
  pointer-events: auto;
  padding: 0;
  appearance: none;
}

.tl-node::after {
  content: "";
  position: absolute;
  inset: -5px;
  border-radius: 50%;
}

.tl-node.send {
  left: calc(2rem + 120px);
  border: 1.5px solid #1a1a1a;
}

.tl-node.send.us {
  border-color: #e00000;
}

.tl-node.send.them {
  border-color: #1a00e0;
}

.tl-node.ddl {
  left: 2rem;
  border: 1.5px solid #c5c5c0;
}

.tl-node.ddl.us {
  border-color: #e00000;
}

.tl-node.ddl.them {
  border-color: #1a00e0;
}

.tl-node:hover,
.tl-node:focus-visible,
.tl-mail.is-active .tl-node.send,
.tl-mail.is-active .tl-node.ddl {
  transform: translate(-50%, -50%) scale(1.25);
  outline: none;
}

.tl-ddl-date-label {
  position: absolute;
  left: 2rem;
  transform: translate(-100%, -50%);
  margin-left: -0.75rem;
  font-family: "Cormorant Garamond", serif;
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  color: #6a6a66;
  white-space: nowrap;
  pointer-events: none;
  transition: filter 0.35s ease, opacity 0.35s ease;
  z-index: 2;
}

@media (max-width: 860px) {
  .tl-mail {
    left: calc(2rem + 88px + 1.5rem);
  }

  .tl-node.send {
    left: calc(2rem + 88px);
  }

  .tl-mail-subject {
    font-size: 0.88rem;
  }
}
</style>
