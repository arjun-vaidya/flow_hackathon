import assert from 'node:assert/strict'
import { chromium } from 'playwright'
import { mkdir, readFile } from 'node:fs/promises'

// Requires the explicit fixture registry server on port 8001; never changes the live server.
const backend = process.env.GRADIENT_FIXTURE_URL ?? 'http://127.0.0.1:8001'
const registry = await fetch(`${backend}/api/modules`).then((response) =>
  response.json(),
)
assert.equal(
  registry.mode,
  'demo',
  'Only run this check against the synthetic fixture server',
)
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const context = await browser.newContext({
  viewport: { width: 1440, height: 1100 },
})
const page = await context.newPage()
const errors = []
page.on('pageerror', (error) => errors.push(error.message))
await page.route('http://127.0.0.1:8000/**', (route) =>
  route.continue({
    url: route.request().url().replace('http://127.0.0.1:8000', backend),
  }),
)
try {
  await page.goto(process.env.GRADIENT_PREVIEW_URL ?? 'http://127.0.0.1:5173')
  await page
    .getByRole('button', { name: 'Research modules', exact: true })
    .click()
  await page.getByRole('textbox').fill('Replay research integration')
  await page.getByRole('button', { name: 'Find opportunities' }).click()
  await page.getByText('Synthetic integration fixture · Run complete').waitFor()
  await mkdir('test-results', { recursive: true })
  await page.screenshot({
    path: 'test-results/module-progress.png',
    fullPage: true,
  })
  await page.getByRole('link', { name: 'View opportunities' }).click()
  await page
    .getByRole('link', { name: 'Synthetic Builder', exact: true })
    .click()
  await page.getByRole('heading', { name: 'Replay Fixture' }).waitFor()
  assert.equal(
    await page.getByRole('img', { name: /Synthetic monthly/ }).count(),
    0,
  )
  await page.getByRole('button', { name: 'Save Replay Fixture' }).click()
  await page
    .getByRole('button', { name: /Synthetic project and user request/ })
    .click()
  assert.equal(
    await page
      .getByRole('link', { name: /Open original source/ })
      .getAttribute('href'),
    'https://example.com/gradient-fixture',
  )
  await page.keyboard.press('Escape')
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Export brief' }).click()
  const download = await downloadPromise
  const brief = await readFile(await download.path(), 'utf8')
  assert.match(brief, /FICTIONAL DEMO/)
  assert.match(brief, /https:\/\/example.com\/gradient-fixture/)
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 })
    assert.ok(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
    )
    await page.screenshot({
      path: `test-results/module-brief-${width}.png`,
      fullPage: true,
    })
  }
  await page.getByRole('link', { name: 'Saved 1' }).click()
  await page
    .getByRole('link', { name: 'Synthetic Builder', exact: true })
    .waitFor()
  await page.reload()
  await page
    .getByRole('link', { name: 'Synthetic Builder', exact: true })
    .waitFor()
  assert.equal(await page.getByText('Maya Chen').count(), 0)
  assert.deepEqual(errors, [])
  console.log(
    'PASS: backend module run → status → shortlist → brief → citations → export → saved persistence; desktop and mobile layouts.',
  )
} finally {
  await context.close()
  await browser.close()
}
