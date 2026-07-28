# Booking module

Public appointment booking for patients via a shareable link. **Optional, removable.**

## Public API

Routes mounted at `/api/v1/booking/`.

- `GET   /{slug}`                         — public booking page data
- `POST  /{slug}`                         — submit a booking request

## Dependencies

`manifest.depends = ["agenda", "patients", "schedules"]`.

## Permissions

None (public-facing endpoints).

## CHANGELOG

See `./CHANGELOG.md`.
