# LIFX Integration for Cortex XSOAR / XSIAM
Smart Lighting Control & SOC Alert Visualization

![Banner](assets/banner.svg)

This repository contains a fully custom, self-contained integration for controlling **LIFX smart lights** using **Cortex XSOAR or XSIAM**.  
It enables automation playbooks to manipulate lighting effects, activate scenes, and visually signal SOC alerts—for example, **flashing red when WildFire detects a malicious file**.

---

## 🚀 Features

- Full LIFX Cloud API support
- Power, color, brightness, and infrared control
- Pulse & Breathe effects
- Scene listing and activation
- **Alert-based flashing** tied to SOC severity
- Fully self-contained Python (no CommonServerPython dependency)
- Works on XSOAR 6, XSOAR 8, XSIAM
- Custom connection test command

---

```
lifx-xsoar-integration/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── integration/
│   ├── LIFX.yml
│   └── lifx_script.py
├── examples/
│   ├── list_lights.md
│   ├── flash_on_severity.md
│   ├── activate_scene.md
│   └── test_connection.md
├── playbooks/
│   ├── wildfire_flash_example/
│   │   ├── wildfire_flash_example.yml
│   │   └── README.md
│   └── reusable_lifx_flash/
│       ├── lifx_flash_subplaybook.yml
│       └── README.md
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   ├── selectors_reference.md
│   ├── troubleshooting.md
│   └── api_reference.md
├── assets/
│   ├── banner.svg
│   ├── lifx_logo.png
│   ├── xsoar_logo.png
│   └── screenshots/
└── .github/
    ├── ISSUE_TEMPLATE.md
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        ├── lint.yml
        └── validate.yml
```

---

## 🔧 Requirements

### LIFX Account
- LIFX Cloud account
- **Personal Access Token**: https://cloud.lifx.com/settings

### XSOAR / XSIAM Environment
- Python 3 integration
- Recommended Docker image:

```
demisto/python3:3.12.8.3296088
```

---

## 🛠 Installation

### 1. Upload Integration
1. Go to **Settings → Integrations
2. Click the **Upload Integration** button
3. Select `LIFX.yml`
4. Add a new instance

### 2. Configure Settings

| Setting | Value |
|--------|-------|
| API Base URL | `https://api.lifx.com/v1` |
| API Token | Your LIFX Token |
| Docker Image | `demisto/python3:3.12.8.3296088` |
| Run in Separate Container | Enabled |

Click **Test** → Should return: `ok`.

---

## 🔍 Testing Connectivity

```
!lifx-test-connection selector="all"
```

Returns:
- Base URL
- SSL status
- Number of detected lights
- Error details if any

---

## 💡 Supported Commands

### Listing Commands
```
!lifx-list-lights selector="all"
!lifx-list-scenes
```

### State & Power Control
```
!lifx-set-state selector="label:DeskLamp" power="on" color="blue"
!lifx-toggle-power selector="group:SOC"
```

### Effects
```
!lifx-breathe-effect selector="label:OverCabinet" color="cyan" period=1.2 cycles=3
!lifx-pulse-effect selector="group:SOC" color="red" cycles=5
```

### Scene Activation
```
!lifx-activate-scene scene_uuid="abcd1234ef567890"
```

### Alert Flashing (Severity-Based)
```
!lifx-alert-flash selector="group:OverCabinet" severity="critical"
```

---

## 🔎 Selector Cheat Sheet

| Selector | Example | Matches |
|----------|---------|---------|
| `all` | `all` | All lights |
| `label:` | `label:DeskLamp` | Match by label |
| `group:` | `group:OverCabinet` | Match group |
| `location:` | `location:Kitchen` | Match location |
| `id:` | `id:d073d5000001` | Match device ID |

---

## ⚡ Example Playbook Snippet

```yaml
- id: flash_soc_lights
  task:
    id: flash_soc_lights
    scriptName: LIFX
    scriptarguments:
      selector:
        simple: "group:OverCabinet"
      severity:
        simple: "${incident.severity}"
    type: regular
    next: ""
  taskid: flash_soc_lights
```

---

## 🐞 Troubleshooting

### 401 Unauthorized
- Regenerate token  
- Remove whitespace  
- Ensure correct LIFX account  

### Lights Offline
- Ensure stable 2.4 GHz WiFi  
- Update firmware via mobile app  

---

## 📜 License
Released under the **MIT License**.

---

## 🤝 Contributing
Pull requests are welcome—feel free to submit improvements or enhancements.

---

## 📬 Contact
For issues or enhancements, open a GitHub Issue.
