# Handover: Modal/Overlay Scroll Audit & Fix

## What was done

Applied Nuxt UI v4 scroll-containment pattern (`max-h-[90vh] flex flex-col` + `shrink-0` header/footer + `overflow-y-auto` body) to **all overlay components** across the workspace to prevent content clipping on small viewports and long content.

## Pattern used

### For `<UModal>` with `<template #content><UCard>`:
```vue
<UCard :ui="{
  root: 'max-h-[90vh] flex flex-col',
  header: { base: 'shrink-0' },
  body: { base: 'flex-1 min-h-0 overflow-y-auto' },
  footer: { base: 'shrink-0' }
}">
```

### For `<UModal>` with `#body`/`#footer` slots directly:
```vue
<UModal :ui="{
  content: 'max-h-[90vh] flex flex-col',
  body: { base: 'overflow-y-auto flex-1' },
  footer: { base: 'shrink-0' },
  header: { base: 'shrink-0' }
}">
```

### For `<USlideover>` with `<UCard>` inside:
```vue
<UCard :ui="{
  root: 'max-h-[90vh] flex flex-col',
  header: { base: 'shrink-0' },
  body: { base: 'flex-1 min-h-0 overflow-y-auto' },
  footer: { base: 'shrink-0' }
}">
```

## Files modified (commit `fd5ded9`)

**Treatment plan modals (6):**
- `backend/app/modules/treatment_plan/frontend/components/clinical/modals/ClosePlanModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/modals/ConfirmPlanModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/modals/ContactLogModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/modals/ReactivatePlanModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/modals/ReopenPlanModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/clinical/notes/CompletionNudgeModal.vue`

**Treatment plan detail (1):**
- `backend/app/modules/treatment_plan/frontend/components/treatment-plans/TreatmentPlanDetail.vue`

**Payments (1):**
- `backend/app/modules/payments/frontend/components/RefundConfirmModal.vue`

**Budget modals (3):**
- `backend/app/modules/budget/frontend/components/clinical/modals/AcceptInClinicModal.vue`
- `backend/app/modules/budget/frontend/components/clinical/modals/RenegotiateBudgetModal.vue`
- `backend/app/modules/budget/frontend/components/clinical/modals/SetPublicCodeModal.vue`

**Odontogram (2):**
- `backend/app/modules/odontogram/frontend/components/odontogram/MultiToothConfirmPopup.vue`
- `backend/app/modules/odontogram/frontend/components/odontogram/TreatmentPicker.vue`

**Media (2):**
- `backend/app/modules/media/frontend/components/media/DocumentGallery.vue`
- `backend/app/modules/media/frontend/components/media/DocumentViewer.vue`

**Recalls (1):**
- `backend/app/modules/recalls/frontend/components/SetRecallModal.vue`

**Settings admin pages (2):**
- `frontend/app/components/settings/pages/CabinetsPage.vue`
- `frontend/app/components/settings/pages/UsersPage.vue`

**Shared (1):**
- `frontend/app/components/shared/FilterBar.vue`

## Files also fixed in previous commit (`2bd3656`)
- `frontend/app/components/settings/modules/ModuleDetailModal.vue`
- `frontend/app/components/settings/modules/ModuleConfirmModal.vue`
- `backend/app/modules/odontogram/frontend/components/odontogram/TreatmentEditModal.vue`
- `frontend/app/layouts/default.vue` (slideover)
- `frontend/i18n/locales/en.json` (missing i18n keys)
- `frontend/tests/e2e/modal-interactions.spec.ts`
- `frontend/tests/e2e/navigation-layout.spec.ts`
- `frontend/tests/e2e/odontogram-chart.spec.ts`
- `UI_TESTING_CHECKLIST.md`

## Already correct (no fix needed)
These files were audited and already had proper scroll containment:

- `frontend/app/components/shared/CollectAmountModal.vue` — `max-h-[90vh] flex flex-col` + `body: 'overflow-y-auto'`
- `backend/app/modules/patients/frontend/components/patient/PatientSectionEditModal.vue`
- `backend/app/modules/budget/frontend/components/budget/BudgetItemModal.vue`
- `backend/app/modules/billing/frontend/components/billing/InvoiceItemModal.vue`
- `backend/app/modules/billing/frontend/components/billing/NewInvoiceItemModal.vue`
- `backend/app/modules/agenda/frontend/components/clinical/AppointmentModal.vue`
- `backend/app/modules/treatment_plan/frontend/components/treatment-plans/TreatmentPlanModal.vue`
- `backend/app/modules/payments/frontend/components/PaymentCreateModal.vue`
- `backend/app/modules/catalog/frontend/components/catalog/CatalogItemModal.vue`
- `backend/app/modules/media/frontend/components/media/PhotoLightbox.vue` (fullscreen, uses `flex-1 overflow-hidden`)
- `frontend/app/components/HelpButton.vue` (already `flex-1 min-h-0 overflow-hidden` for iframe)
- `backend/app/modules/copilot/frontend/components/CopilotMount.vue` (already `flex-1 overflow-hidden`)
- `frontend/app/components/settings/SettingsSearch.vue` (command palette, has `max-h-96 overflow-y-auto` on results)

## What remains

1. **SurfaceSelectorPopup.vue** — uses `<UPopover>` (not a modal), contains tooth SVG surfaces. Popovers auto-position and typically don't need max-height constraints, but verify on small viewports.
2. **DiagnosisMode.vue** — has no overlay, it's an inline component.
3. **Page-level inline overlays** — `catalog/index.vue`, `catalog/vat-types/index.vue`, `patients/index.vue`, `patients/[id].vue`, `budgets/[id].vue`, `p/budget/[token].vue`, `invoices/[id]/index.vue` — these pages may use `UModal` inline. If they do, apply the same pattern.
4. **verifactu/** modules and `schedules/*` — not audited yet.
5. **PerioIndicesBanner.vue, NoteComposer.vue, TreatmentNoteButton.vue, NoteComposerModal.vue** — if they contain overlays.
6. **SetRecallModal.vue** — uses `#body` slot; fixed with `:ui` on UModal but verify the `flex-1` doesn't break the multi-section layout.

## Critical conventions reminder

- **Nuxt UI v4** — `v-model:open` (not `v-model`), use `:ui` prop, not `ui` prop
- **Python backend**: `backend/app/modules/<name>/`
- **Vue frontend layers**: `frontend/app/` (host) and `backend/app/modules/<name>/frontend/` (module layers)
- **No `node`, `npm`, `npx` available** in this terminal environment — can't run dev server or tests
- **Git available at**: `"C:\Users\6284\Downloads\PortableGit\mingw64\libexec\git-core\git.exe"`
- **Remote**: `https://github.com/abobakr-Abaza/mytool.git` (PAT auth in URL)