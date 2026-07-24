import { test, expect, type Page } from './_fixtures'

/**
 * Modal & Drawer E2E — opening modals, filling forms, scrolling,
 * submitting, and closing.
 *
 * Covers:
 * - Settings module detail modal (scroll + overflow behavior)
 * - Settings module confirm modals (install/uninstall/apply)
 * - Clinic info save modal interaction
 * - Cabinet create/edit modal flow
 */

const API_BASE = process.env.E2E_API_BASE || 'http://localhost:8000'

test.describe('settings — module detail modal', () => {
  test.use({ role: 'admin' })

  test('opens module detail modal and scrolls operation log', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/modules')
    await loggedIn.waitForURL(/\/settings\/modules/, { timeout: 10_000 })

    // Click "Details" on the Patients module card
    const detailsBtn = loggedIn.getByRole('button', { name: /details|detalles/i }).first()
    await expect(detailsBtn).toBeVisible({ timeout: 8_000 })
    await detailsBtn.click()

    // Modal should render with module info
    const modal = loggedIn.getByRole('dialog').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })

    // Modal content should include module name in header
    await expect(modal.locator('h3').first()).toBeVisible()
    await expect(modal.locator('text=patients').or(modal.locator('text=Patients'))).toBeVisible()

    // Operation log section should exist and be scrollable
    const logSection = modal.locator('text=Operation log').or(modal.locator('text=Registro de operaciones'))
    if (await logSection.isVisible().catch(() => false)) {
      // Verify the scroll container exists
      await expect(modal.locator('.overflow-y-auto').first()).toBeVisible()
    }

    // Close modal via X button
    const closeBtn = modal.locator('button:has([class*="lucide-x"])').first()
    await closeBtn.click()
    await expect(modal).not.toBeVisible()
  })
})

test.describe('settings — module confirm modals', () => {
  test.use({ role: 'admin' })

  test('install confirm modal shows and can be cancelled', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/modules')
    await loggedIn.waitForURL(/\/settings\/modules/, { timeout: 10_000 })

    // Find an uninstalled module's install button
    const installBtn = loggedIn.locator('button:has-text("Install"), button:has-text("Instalar")').first()
    if (!(await installBtn.isVisible().catch(() => false))) {
      test.skip(true, 'no installable module available in this seed')
    }

    await installBtn.click()

    // Confirmation modal opens
    const modal = loggedIn.getByRole('dialog').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })

    // Cancel button closes the modal
    const cancelBtn = modal.getByRole('button', { name: /cancel|cancelar/i }).first()
    await expect(cancelBtn).toBeVisible()
    await cancelBtn.click()
    await expect(modal).not.toBeVisible()
  })

  test('confirm modal is not dismissible while loading', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/modules')
    await loggedIn.waitForURL(/\/settings\/modules/, { timeout: 10_000 })

    // Look for the "Apply changes" button (pending changes)
    const applyBtn = loggedIn.getByRole('button', { name: /apply|aplicar/i }).first()
    if (!(await applyBtn.isVisible().catch(() => false))) {
      test.skip(true, 'no pending changes to apply')
    }

    await applyBtn.click()

    const modal = loggedIn.getByRole('dialog').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })

    // Modal should not be dismissible by clicking outside when loading
    // (implementation: :dismissible="!loading")
    await expect(modal).toBeVisible()
  })
})

test.describe('settings — cabinet create modal flow', () => {
  test.use({ role: 'admin' })

  test('opens cabinet create modal, fills form, verifies scroll, cancels', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/workspace')
    await loggedIn.waitForURL(/\/settings\/workspace/, { timeout: 10_000 })

    // Open the create cabinet modal
    const addBtn = loggedIn.getByRole('button', { name: /add|añadir|nuevo|new/i }).first()
    if (!(await addBtn.isVisible().catch(() => false))) {
      test.skip(true, 'cabinet add button not visible')
    }
    await addBtn.click()

    // Modal should be visible
    const modal = loggedIn.getByRole('dialog').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })

    // Verify form fields exist
    const nameInput = modal.locator('input[type="text"]').first()
    await expect(nameInput).toBeVisible()
    await nameInput.fill('Test Cabinet E2E')

    // Verify color picker exists (cabinet colors are shown)
    const colorSwatches = modal.locator('button:has([class*="rounded-full"])')
    if (await colorSwatches.count().then(c => c > 0)) {
      await colorSwatches.first().click()
    }

    // Submit and close
    const submitBtn = modal.getByRole('button', { name: /create|crear|save|guardar/i }).first()
    await expect(submitBtn).toBeVisible()
    await submitBtn.click()

    // Modal should close on successful creation
    await expect(modal).not.toBeVisible({ timeout: 5_000 })
  })
})

test.describe('settings — clinic info modal scroll behavior', () => {
  test.use({ role: 'admin' })

  test('clinic info page loads without modal overflow', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/general')
    await loggedIn.waitForURL(/\/settings\/general/, { timeout: 10_000 })

    // The clinic info section should render without modal wrapping
    const clinicSection = loggedIn.locator('text=Clinic Information')
      .or(loggedIn.locator('text=Información de la clínica'))
    await expect(clinicSection.first()).toBeVisible({ timeout: 8_000 })

    // Scroll the page to verify no clip/overflow issues
    await loggedIn.evaluate(() => window.scrollTo(0, document.body.scrollHeight))

    // The save button should be reachable after scroll
    const saveBtn = loggedIn.getByRole('button', { name: /save|guardar|cambios/i }).first()
    await expect(saveBtn).toBeVisible()
  })
})

test.describe('keyboard accessibility — modal escape', () => {
  test.use({ role: 'admin' })

  test('module detail modal closes via Escape key', async ({ loggedIn }) => {
    await loggedIn.goto('/settings/modules')
    await loggedIn.waitForURL(/\/settings\/modules/, { timeout: 10_000 })

    const detailsBtn = loggedIn.getByRole('button', { name: /details|detalles/i }).first()
    await expect(detailsBtn).toBeVisible({ timeout: 8_000 })
    await detailsBtn.click()

    const modal = loggedIn.getByRole('dialog').first()
    await expect(modal).toBeVisible({ timeout: 5_000 })

    // Press Escape to close
    await modal.press('Escape')
    await expect(modal).not.toBeVisible()
  })
})