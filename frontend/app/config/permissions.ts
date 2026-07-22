/**
 * Centralized permission configuration.
 *
 * All permission checks should reference this config instead of
 * hardcoding permission strings throughout the codebase.
 */

// Resource-action permission mapping
export const PERMISSIONS = {
  patients: {
    read: 'patients.read',
    write: 'patients.write'
  },
  medicalHistory: {
    read: 'patients_clinical.medical.read',
    write: 'patients_clinical.medical.write'
  },
  emergencyContact: {
    read: 'patients_clinical.emergency.read',
    write: 'patients_clinical.emergency.write'
  },
  appointments: {
    read: 'agenda.appointments.read',
    write: 'agenda.appointments.write'
  },
  users: {
    read: 'admin.users.read',
    write: 'admin.users.write'
  },
  odontogram: {
    read: 'odontogram.read',
    write: 'odontogram.write',
    treatmentsRead: 'odontogram.treatments.read',
    treatmentsWrite: 'odontogram.treatments.write'
  },
  catalog: {
    read: 'catalog.read',
    write: 'catalog.write',
    admin: 'catalog.admin'
  },
  budget: {
    read: 'budget.read',
    write: 'budget.write',
    admin: 'budget.admin',
    renegotiate: 'budget.renegotiate',
    acceptInClinic: 'budget.accept_in_clinic'
  },
  billing: {
    read: 'billing.read',
    write: 'billing.write',
    admin: 'billing.admin'
  },
  notifications: {
    templatesRead: 'notifications.templates.read',
    templatesWrite: 'notifications.templates.write',
    preferencesRead: 'notifications.preferences.read',
    preferencesWrite: 'notifications.preferences.write',
    logsRead: 'notifications.logs.read',
    send: 'notifications.send',
    settingsRead: 'notifications.settings.read',
    settingsWrite: 'notifications.settings.write'
  },
  reports: {
    billingRead: 'reports.billing.read',
    budgetsRead: 'reports.budgets.read',
    schedulingRead: 'reports.scheduling.read'
  },
  documents: {
    read: 'media.documents.read',
    write: 'media.documents.write'
  },
  attachments: {
    read: 'media.attachments.read',
    write: 'media.attachments.write'
  },
  treatmentPlans: {
    read: 'treatment_plan.plans.read',
    write: 'treatment_plan.plans.write',
    confirm: 'treatment_plan.plans.confirm',
    close: 'treatment_plan.plans.close',
    reactivate: 'treatment_plan.plans.reactivate'
  },
  clinicalNotes: {
    read: 'clinical_notes.notes.read',
    write: 'clinical_notes.notes.write'
  },
  agents: {
    view: 'agents.view',
    supervise: 'agents.supervise',
    configure: 'agents.configure',
    manage: 'agents.manage'
  },
  admin: {
    clinicRead: 'admin.clinic.read',
    clinicWrite: 'admin.clinic.write',
    brandingRead: 'admin.branding.read',
    brandingWrite: 'admin.branding.write',
    tenantsWrite: 'admin.tenants.write'
  },
  migrationImport: {
    jobRead: 'migration_import.job.read',
    jobWrite: 'migration_import.job.write',
    jobExecute: 'migration_import.job.execute',
    binaryWrite: 'migration_import.binary.write'
  },
  payments: {
    recordRead: 'payments.record.read',
    recordWrite: 'payments.record.write',
    recordRefund: 'payments.record.refund',
    reportsRead: 'payments.reports.read'
  },
  verifactu: {
    settingsRead: 'verifactu.settings.read',
    settingsConfigure: 'verifactu.settings.configure',
    queueManage: 'verifactu.queue.manage',
    recordsRead: 'verifactu.records.read',
    environmentPromote: 'verifactu.environment.promote'
  },
  recalls: {
    read: 'recalls.read',
    write: 'recalls.write',
    delete: 'recalls.delete'
  },
  whatsappKapso: {
    settingsRead: 'whatsapp_kapso.settings.read',
    settingsWrite: 'whatsapp_kapso.settings.write'
  },
  schedules: {
    clinicHoursRead: 'schedules.clinic_hours.read',
    clinicHoursWrite: 'schedules.clinic_hours.write',
    professionalRead: 'schedules.professional.read',
    professionalWrite: 'schedules.professional.write',
    professionalOwnRead: 'schedules.professional.own.read',
    professionalOwnWrite: 'schedules.professional.own.write'
  },
  periodontogram: {
    read: 'periodontogram.read',
    write: 'periodontogram.write'
  },
  copilot: {
    chat: 'copilot.chat',
    historyRead: 'copilot.history.read',
    historyReadAll: 'copilot.history.read_all',
    supervise: 'copilot.supervise',
    configure: 'copilot.configure'
  },
  accountingExport: {
    read: 'accounting_export.export.read',
    run: 'accounting_export.export.run'
  },
  staff: {
    read: 'staff.staff.read',
    write: 'staff.staff.write',
    readOwn: 'staff.staff.read_own',
    delete: 'staff.staff.delete',
    manageRoles: 'staff.staff.manage_roles'
  },
  tasks: {
    read: 'staff.tasks.read',
    readOwn: 'staff.tasks.read_own',
    write: 'staff.tasks.write',
    writeOwn: 'staff.tasks.write_own',
    status: 'staff.tasks.status',
    delete: 'staff.tasks.delete'
  },
  finance: {
    read: 'staff.finance.read',
    readOwn: 'staff.finance.read_own',
    write: 'staff.finance.write',
    payout: 'staff.finance.payout'
  },
  audit: {
    read: 'staff.audit.read'
  },
  chat: {
    read: 'staff.chat.read',
    write: 'staff.chat.write',
    own: 'staff.chat.own'
  }
} as const
