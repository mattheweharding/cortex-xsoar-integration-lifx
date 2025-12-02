# Changelog

All notable changes to the **LIFX Integration for Cortex XSOAR / XSIAM** will be documented in this file.

---

## v1.0.0 — Initial Public Release (2025-12-01)

### ✨ Features
- Full LIFX Cloud API integration
- Support for all major light management operations:
  - List lights
  - Set state (power, brightness, color, infrared, fast mode)
  - Toggle power
  - Breathe effect
  - Pulse effect
- Scene management:
  - List scenes with markdown formatting
  - Human-readable timestamps for `created_at` and `updated_at`
  - Per-scene light tables
  - Activate scenes with optional transition duration
- Visual security responses:
  - `lifx-alert-flash` for WildFire / XDR / SIEM events
  - Severity-based defaults (color and cycles)
  - Customizable override parameters
- Operational tools:
  - `lifx-test-connection` with diagnostic table
  - `lifx-health-check` with:
    - HTTP status
    - Latency calculation
    - Rate limit details
    - Human-readable rate reset time
- Highly readable markdown output across all commands

### 🛠 Improvements
- Clean internal error reporting
- Selector normalization and flexibility
- Added verbose mode to multiple commands (includes JSON output)
- Consistent formatting across all tables and command responses

### 📄 Documentation
- GitHub README added
- API token instructions included
- Selector cheat sheet added
- Example WildFire playbook included
- Repository structure recommendation included

---

## v0.5.0 — Pre-Release / Internal Build (2025-11-15)
- Initial development version
- Basic LIFX API connectivity & authentication
- Early tests for scene listing and light effects
- No markdown formatting
- No health check or verbose mode

---

## v0.1.0 — PoC Draft (2025-11-10)
- Proof of concept created to flash lights during WildFire alerts
- Minimal script using direct raw API calls
- No integration YAML, no documentation, no formatting

---