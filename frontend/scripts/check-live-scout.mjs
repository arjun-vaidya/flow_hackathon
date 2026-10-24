import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { mkdir } from 'node:fs/promises'

// Opt-in, read-only live check. Requires the GitHub Scout factory on port 8000.
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } })
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
try {
  await page.goto(process.env.GRADIENT_PREVIEW_URL ?? 'http://127.0.0.1:5173')
  await page
    .getByRole('button', { name: 'Research modules', exact: true })
    .click()
  await page.getByRole('textbox').fill('repo:langfuse/langfuse')
  await page.getByRole('button', { name: 'Find opportunities' }).click()
  await page.getByText('GitHub Scout · basic search', { exact: true }).waitFor()
  await page
    .getByText('Connected research modules · Run partial', { exact: true })
    .waitFor({ timeout: 65000 })
  await page
    .getByText('1 opportunities assembled so far.', { exact: false })
    .waitFor()
  const runUrl = page.url()
  await page.getByRole('link', { name: 'View opportunities' }).click()
  await page
    .getByRole('link', { name: 'Builder identity unknown', exact: true })
    .click()
  await page
    .getByRole('heading', { name: 'langfuse/langfuse', exact: true, level: 1 })
    .waitFor()
  await page.getByText('REVIEW: pending', { exact: true }).waitFor()
  assert.equal(await page.getByText('DEMO DATA', { exact: true }).count(), 0)
  await page
    .getByRole('button', { name: /^Self-reported.*langfuse\/langfuse/ })
    .first()
    .click()
  assert.equal(
    await page
      .getByRole('link', { name: /Open original source/ })
      .getAttribute('href'),
    'https://github.com/langfuse/langfuse',
  )
  await page.keyboard.press('Escape')
  await mkdir('test-results', { recursive: true })
  await page.screenshot({
    path: 'test-results/live-github-scout.png',
    fullPage: true,
  })
  assert.deepEqual(errors, [])
  console.log(
    `PASS: live GitHub → module output → shortlist → cited brief. Run: ${runUrl}`,
  )
} finally {
  await browser.close()
}
