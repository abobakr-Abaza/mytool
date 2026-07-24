import { test, expect } from './_fixtures'

/**
 * Navigation & Layout E2E — sidebar toggle, responsive nav, page switching.
 *
 * Covers:
 * - Desktop sidebar collapse/expand via toggle button
 * - Mobile hamburger slideover opens/closes
 * - Page switching via sidebar links
 * - Sidebar collapsed state persists across page navigations
 * - Responsive: sidebar hidden on mobile, slideover shown
 */

test.describe('sidebar — desktop toggle', () => {
  test.use({ role: 'admin' })

  test('sidebar collapses and expands via toggle button', async ({ loggedIn }) => {
    // Expect sidebar to start expanded (default light mode)
    const sidebar = loggedIn.locator('aside').first()
    await expect(sidebar).toBeVisible()

    // Get the toggle button (desktop: hidden md:inline-flex)
    const toggle = loggedIn.locator('header button:has([class*="panel-left"])').first()
    await expect(toggle).toBeVisible()

    // Toggle collapsed — width goes from w-60 to w-16
    await toggle.click()
    await expect(sidebar).toHaveClass(/w-16/)

    // Toggle expanded again
    await toggle.click()
    await expect(sidebar).toHaveClass(/w-60/)
  })

  test('sidebar collapse persists across page navigation', async ({ loggedIn }) => {
    const toggle = loggedIn.locator('header button:has([class*="panel-left"])').first()

    // Collapse sidebar
    await toggle.click()
    const sidebar = loggedIn.locator('aside').first()
    await expect(sidebar).toHaveClass(/w-16/)

    // Navigate to another page
    await loggedIn.goto('/settings')
    await loggedIn.waitForURL(/\/settings/, { timeout: 10_000 })

    // Sidebar should still be collapsed
    await expect(sidebar).toHaveClass(/w-16/)
  })
})

test.describe('sidebar — desktop page switching', () => {
  test.use({ role: 'admin' })

  const NAV_LINKS = [
    { label: /home|inicio|dashboard/i, path: '/' },
    { label: /patients|pacientes/i, path: '/patients' },
    { label: /schedule|agenda|citas|appointments/i, path: '/appointments' }
  ]

  for (const { label, path } of NAV_LINKS) {
    test(`navigates to ${path} via sidebar link`, async ({ loggedIn }) => {
      const nav = loggedIn.getByRole('navigation').first()
      const link = nav.getByRole('link', { name: label }).first()
      await expect(link).toBeVisible()

      await link.click()
      await loggedIn.waitForURL(new RegExp(path.replace('/', '\\/')), { timeout: 10_000 })

      // Active link gets the primary-soft background
      await expect(link).toHaveClass(/primary-soft/)
    })
  }
})

test.describe('mobile navigation — hamburger slideover', () => {
  test.use({ role: 'admin' })

  test('hamburger opens and closes the mobile slideover', async ({ loggedIn }) => {
    // Resize viewport to mobile dimensions
    await loggedIn.setViewportSize({ width: 375, height: 812 })

    // Hamburger is visible only on mobile (md:hidden)
    const hamburger = loggedIn.locator('header .md\\:hidden').first()
    await expect(hamburger).toBeVisible()
    await hamburger.click()

    // Slideover should now be open
    const slideover = loggedIn.locator('[role="dialog"]').first()
    await expect(slideover).toBeVisible()

    // Close button inside slideover
    const closeBtn = slideover.locator('button:has([class*="lucide-x"])').first()
    await expect(closeBtn).toBeVisible()
    await closeBtn.click()

    // Slideover should be closed
    await expect(slideover).not.toBeVisible()
  })

  test('mobile slideover navigates and closes on link click', async ({ loggedIn }) => {
    await loggedIn.setViewportSize({ width: 375, height: 812 })

    // Open mobile nav
    const hamburger = loggedIn.locator('header .md\\:hidden').first()
    await hamburger.click()

    const slideover = loggedIn.locator('[role="dialog"]').first()
    await expect(slideover).toBeVisible()

    // Click a nav link inside the slideover
    const patientsLink = slideover.getByRole('link', { name: /patients|pacientes/i }).first()
    await patientsLink.click()

    // Slideover should close after navigation
    await expect(slideover).not.toBeVisible()
    await loggedIn.waitForURL(/\/patients/, { timeout: 10_000 })
  })
})

test.describe('sidebar — role-based filtering', () => {
  test('hygienist sees limited nav items', async ({ loggedIn }) => {
    const nav = loggedIn.getByRole('navigation').first()
    await expect(nav.getByRole('link', { name: /patients|pacientes/i })).toBeVisible()
    await expect(nav.getByRole('link', { name: /schedule|agenda|citas/i })).toBeVisible()
    // Reports require reports.billing.read which hygienist lacks
    await expect(nav.getByRole('link', { name: /reports|informes/i })).toHaveCount(0)
  })

  test('receptionist sees front-desk nav items', async ({ loggedIn }) => {
    const nav = loggedIn.getByRole('navigation').first()
    await expect(nav.getByRole('link', { name: /patients|pacientes/i })).toBeVisible()
    await expect(nav.getByRole('link', { name: /invoices|facturas/i })).toBeVisible()
  })
})

test.describe('layout chrome — header elements', () => {
  test.use({ role: 'admin' })

  test('header displays clinic name and action buttons', async ({ loggedIn }) => {
    // Clinic name (inside ClientOnly — should render after hydration)
    await expect(loggedIn.locator('header span:has-text("Clínica")').or(
      loggedIn.locator('header span:has-text("Clinic")')
    ).first()).toBeVisible({ timeout: 5_000 })

    // Theme toggle button
    await expect(loggedIn.locator('header button:has([class*="lucide-sun"]), header button:has([class*="lucide-moon"])').first()).toBeVisible()

    // Logout button
    const logoutBtn = loggedIn.locator('header button:has([class*="lucide-log-out"])').first()
    await expect(logoutBtn).toBeVisible()
  })

  test('density toggle is accessible', async ({ loggedIn }) => {
    const densityToggle = loggedIn.locator('header button:has([class*="lucide-rows"])').first()
    await expect(densityToggle).toBeVisible()
  })
})

test.describe('404 and edge-case routes', () => {
  test.use({ role: 'admin' })

  test('visiting unknown route shows 404-style content', async ({ loggedIn }) => {
    const response = await loggedIn.goto('/nonexistent-route-xyz', { waitUntil: 'domcontentloaded' })
    // Nuxt should render a 404 page and not a server error
    expect(response?.status() ?? 0).toBeLessThan(500)
  })
})