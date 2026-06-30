# UI Context

## Purpose

The UI is a minimal reviewer-facing demo surface. Swagger UI remains the primary API documentation and testing tool. The custom UI exists only to make the core workflow easier to see end to end.

## Theme

Use a clean, utilitarian operations-dashboard style. Prioritize readable tables, clear form fields, and obvious actions over visual polish.

## Colors

Use plain CSS custom properties. Keep the palette neutral and restrained.

| Role | CSS Variable | Value |
| --- | --- | --- |
| Page background | `--bg-base` | `#f6f8fb` |
| Surface | `--bg-surface` | `#ffffff` |
| Primary text | `--text-primary` | `#172033` |
| Muted text | `--text-muted` | `#667085` |
| Primary accent | `--accent-primary` | `#2563eb` |
| Border | `--border-default` | `#d9e2ec` |
| Error | `--state-error` | `#b42318` |
| Success | `--state-success` | `#027a48` |

## Typography

| Role | Font | Variable |
| --- | --- | --- |
| UI text | System sans-serif | `--font-sans` |
| Code/mono | System monospace | `--font-mono` |

## Border Radius

| Context | Value |
| --- | --- |
| Small controls | `4px` |
| Tables and panels | `6px` |
| Modals/overlays | Not planned for v1 |

## Component Approach

- Use static HTML, CSS, and minimal vanilla JavaScript.
- Do not add a frontend framework unless the design changes.
- UI code lives in `app/static/`.
- UI fetches backend APIs; it must not seed data or bypass API behavior.

## Layout Patterns

- Single-page dashboard.
- Top section: app title, default home context, Swagger link.
- Appliance section: table of appliances plus compact registration form.
- Collection section: home-level collect button and latest collection result.
- Metrics section: filters and historical metrics table.
- Reports section: daily/custom report controls and report summary table.

## UI Controls

- Use native form inputs and buttons.
- Use select controls for vendor and appliance type where supported values are known.
- Use tables for appliances, metrics, and reports.
- Use simple status labels for active/inactive appliance state.

## UI Rules

- Do not create seed data from the UI.
- Do not expose appliance-level manual collection.
- Do not show raw JSON as the main report UI; render standardized report responses into tables.
- Keep all UI actions backed by documented APIs in `context/feature-design.md`.
