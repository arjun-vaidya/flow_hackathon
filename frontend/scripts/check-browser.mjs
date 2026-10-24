import assert from 'node:assert/strict'
import { mkdir, readFile } from 'node:fs/promises'
import { chromium } from 'playwright'

// Requires the dev server. Uses an isolated context, never a personal browser profile.
const baseURL = process.env.PULL_PREVIEW_URL ?? 'http://127.0.0.1:5173'
const browser = await chromium.launch({
  channel: process.env.PULL_BROWSER_CHANNEL ?? 'chrome',
  headless: true,
})
const context = await browser.newContext({
  viewport: { width: 1440, height: 1100 },
  reducedMotion: 'reduce',
})
const page = await context.newPage()
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
await mkdir('test-results', { recursive: true })
async function screenshot(name) {
  await page.screenshot({ path: `test-results/${name}.png`, fullPage: true })
}
async function checkWidth() {
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    'Page must fit viewport without horizontal overflow',
  )
}
try {
  const response = await page.goto(baseURL)
  assert.equal(response.status(), 200)
  await page
    .getByRole('heading', { name: 'Find your next founder conversation.' })
    .waitFor()
  await screenshot('discovery-desktop')
  await checkWidth()
  await page
    .getByRole('button', { name: 'AI agent monitoring', exact: true })
    .click()
  await page.getByRole('button', { name: 'Find opportunities' }).click()
  await page
    .getByRole('heading', { name: 'Builders worth a closer look.' })
    .waitFor()
  await page.getByRole('link', { name: 'Maya Chen', exact: true }).waitFor()
  await screenshot('shortlist-desktop')
  await page.getByRole('checkbox', { name: 'Compare TraceNest' }).check()
  await page.getByRole('checkbox', { name: 'Compare AgentCanvas' }).check()
  await page.getByRole('button', { name: 'Compare (2/2)' }).click()
  await page.getByRole('dialog').waitFor()
  await page.keyboard.press('Escape')
  await page
    .getByRole('button', { name: 'Save TraceNest', exact: true })
    .click()
  await page.reload()
  assert.equal(
    await page
      .getByRole('button', { name: 'Unsave TraceNest' })
      .getAttribute('aria-pressed'),
    'true',
  )
  await page.getByRole('link', { name: 'Maya Chen', exact: true }).click()
  await page
    .getByRole('heading', {
      name: 'The users are asking. Is there a company here?',
    })
    .waitFor()
  await page
    .getByRole('img', { name: /Synthetic monthly contributions/ })
    .waitFor()
  await screenshot('brief-desktop')
  await checkWidth()
  await page
    .getByRole('button', { name: /A request for managed hosting/ })
    .click()
  await page.getByRole('dialog').waitFor()
  await screenshot('evidence-desktop')
  await page.keyboard.press('Escape')
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export brief' }).click()
  const download = await downloadPromise
  assert.equal(download.suggestedFilename(), 'pull-tracenest-demo-brief.md')
  assert.match(
    await readFile(await download.path(), 'utf8'),
    /FICTIONAL DEMO — NOT VERIFIED RESEARCH/,
  )
  await page.getByRole('link', { name: 'Saved 1' }).click()
  await page.getByRole('link', { name: 'Maya Chen', exact: true }).waitFor()
  assert.equal(
    await page.getByRole('link', { name: 'Eli Brooks', exact: true }).count(),
    0,
  )
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 })
    for (const [path, name] of [
      ['/', 'discovery'],
      ['/shortlist', 'shortlist'],
      ['/builders/tracenest', 'brief'],
    ]) {
      await page.goto(`${baseURL}${path}`)
      await page.getByRole('heading', { level: 1 }).waitFor()
      if (name === 'brief')
        await page
          .getByRole('img', { name: /Synthetic monthly contributions/ })
          .waitFor()
      await checkWidth()
      if (width === 390) await screenshot(`${name}-mobile`)
    }
  }
  assert.deepEqual(errors, [], 'Browser should not report uncaught errors')
  console.log(
    'PASS: search, compare, evidence, saved persistence, export, deep links, and desktop/390px/320px layouts.',
  )
} finally {
  await context.close()
  await browser.close()
}
