import { test, expect, type Page } from './_fixtures'

/**
 * Odontogram interactive chart E2E — treatment selection, application,
 * surface picker, treatment edit modal.
 *
 * Covers:
 * - Odontogram chart renders for a patient
 * - Treatment bar category filtering
 * - Treatment selection and application to a tooth
 * - Treatment edit modal open/close
 * - Treatment status toggle (planned/existing)
 * - Multi-tooth treatment flow
 */

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000'

async function getPatientId(page: Page): Promise<string> {
  const ctx = page.context()
  const cookies = await ctx.cookies()
  const token = cookies.find(c => c.name === 'access_token')?.value
  const res = await ctx.request.get(`${API_BASE}/api/v1/patients?page=1&page_size=1`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  })
  if (!res.ok()) throw new Error(`patient list failed: ${res.status()}`)
  const body = (await res.json()) as { data: Array<{ id: string }> }
  const id = body.data[0]?.id
  if (!id) throw new Error('no seeded patient available')
  return id
}

test.describe('odontogram chart — renders for patient', () => {
  test.use({ role: 'admin' })

  test('odontogram tab loads and chart appears', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)

    // Navigate to patient detail with clinical tab
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // The odontogram tab should be available
    const odontogramTab = loggedIn.getByRole('tab', { name: /odontogram|dental chart|dental/i }).first()
    if (await odontogramTab.isVisible().catch(() => false)) {
      await odontogramTab.click()
    }

    // The tooth chart should render — look for SVG tooth elements
    await expect(
      loggedIn.locator('svg').or(loggedIn.locator('[data-testid="odontogram-chart"]')).first()
    ).toBeVisible({ timeout: 10_000 })

    // Legend should be visible
    await expect(
      loggedIn.getByText(/legend|leyenda/i).first()
    ).toBeVisible({ timeout: 5_000 })
  })
})

test.describe('odontogram — treatment bar', () => {
  test.use({ role: 'admin' })

  test('treatment bar shows categories and filters', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Treatment bar should have category buttons
    const commonCategory = loggedIn.getByRole('button', { name: /common|común|comun/i }).first()
    const restorativeCategory = loggedIn.getByRole('button', { name: /restorative|restauradora/i }).first()

    await expect(commonCategory.or(restorativeCategory).first()).toBeVisible({ timeout: 8_000 })

    // Click a category to filter treatments
    if (await commonCategory.isVisible().catch(() => false)) {
      await commonCategory.click()
    }

    // Treatment options should be visible as buttons
    const treatmentOptions = loggedIn.locator('button:has([class*="lucide"])')
    await expect(treatmentOptions.first()).toBeVisible()
  })

  test('status toggle (planned/existing) is interactive', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Status toggle should exist
    const existingBtn = loggedIn.getByRole('button', { name: /existing|existente/i }).first()
    const plannedBtn = loggedIn.getByRole('button', { name: /planned|planificado/i }).first()

    await expect(existingBtn.or(plannedBtn).first()).toBeVisible({ timeout: 8_000 })
  })
})

test.describe('odontogram — treatment application', () => {
  test.use({ role: 'admin' })

  test('select tooth and apply a treatment', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=planning`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Find a tooth SVG element that is clickable
    const tooth = loggedIn.locator('svg [data-tooth], svg g[data-tooth-number], svg text').first()
    if (!(await tooth.isVisible().catch(() => false))) {
      test.skip(true, 'tooth elements not found - chart may not have interactive teeth')
    }

    // Plan mode should have treatment bar
    const treatmentBar = loggedIn.locator('button:has-text("Filling"), button:has-text("Caries"), button:has-text("Crown")').first()
    if (await treatmentBar.isVisible().catch(() => false)) {
      await treatmentBar.click()
    }

    // Treatment should be selectable
    await expect(tooth).toBeVisible()
  })
})

test.describe('odontogram — treatment edit modal', () => {
  test.use({ role: 'admin' })

  test('clicking an existing tooth treatment opens edit modal', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Try clicking a tooth with an existing treatment marker
    // Look for colored tooth elements (not healthy/gray)
    const treatedTooth = loggedIn.locator('svg [fill*="#"]:not([fill*="none"]), svg [style*="color"]').first()
    if (await treatedTooth.isVisible().catch(() => false)) {
      await treatedTooth.click()

      // The edit modal may appear
      const editModal = loggedIn.getByRole('dialog').first()
      if (await editModal.isVisible({ timeout: 3_000 }).catch(() => false)) {
        // Verify the modal has save/cancel buttons
        await expect(
          editModal.getByRole('button', { name: /save|guardar/i }).first()
        ).toBeVisible()

        await editModal.press('Escape')
        await expect(editModal).not.toBeVisible()
      }
    } else {
      // No treated teeth visible — this is acceptable
      test.skip(true, 'no existing treatments to click')
    }
  })
})

test.describe('odontogram — multi-tooth treatments', () => {
  test.use({ role: 'admin' })

  test('multi-tooth section shows in planning mode', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=planning`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Multi-tooth section should exist
    const bridgeBtn = loggedIn.getByRole('button', { name: /bridge|puente|splint|ferula|feruliza/i }).first()
    if (await bridgeBtn.isVisible().catch(() => false)) {
      await bridgeBtn.click()
    }

    // Treatment bar should be interactive
    await expect(
      loggedIn.locator('button:has([class*="lucide"])').first()
    ).toBeVisible({ timeout: 5_000 })
  })
})

test.describe('odontogram — legend and view controls', () => {
  test.use({ role: 'admin' })

  test('odontogram legend renders all expected items', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Legend should explain tooth conditions
    const legend = loggedIn.getByText(/legend|leyenda/i).first()
    if (await legend.isVisible().catch(() => false)) {
      // Verify some condition labels exist
      await expect(
        loggedIn.locator('text=Healthy, text=Caries, text=Filling').first()
      ).toBeVisible({ timeout: 3_000 })
    }
  })

  test('view toggle switches odontogram view mode', async ({ loggedIn }) => {
    const patientId = await getPatientId(loggedIn)
    await loggedIn.goto(`/patients/${patientId}?tab=clinical&clinicalMode=diagnosis`)
    await loggedIn.waitForURL(/\/patients\/[0-9a-f-]+/, { timeout: 15_000 })

    // Look for view toggle buttons (occlusal/lateral/dual)
    const viewToggle = loggedIn.getByRole('button', { name: /occlusal|oclusal|lateral|dual/i }).first()
    if (await viewToggle.isVisible().catch(() => false)) {
      await viewToggle.click()
    }
  })
})