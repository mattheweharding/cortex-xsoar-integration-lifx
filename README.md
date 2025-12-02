# 💡LIFX Integration for Cortex XSOAR / XSIAM
![LIFXLogo](assets/lifx.svg)

Control your **LIFX smart lights** directly from Cortex XSOAR / XSIAM.

Use lighting as a security signal, automate visual alerts, set ambiance scenes, and deeply integrate LIFX into your workflows.

---

## 🚀 Features

### 🎯 Core Capabilities
- List and manage all LIFX lights
- Set power, brightness, color, infrared, and fast mode
- Toggle power with optional transitions
- Trigger **breathe** and **pulse** effects
- Activate LIFX **Scenes** (with human-readable timestamps)
- Generate **visual alert flashes** for WildFire, XDR, SIEM, or XSIAM alerts
- Built-in **Health Check** with:
  - HTTP status
  - Rate limit info
  - Human-readable rate limit reset time
  - Millisecond latency calculation
- Highly readable markdown output for the XSOAR War Room

---

## 🔑 Obtaining Your LIFX API Token

1. Go to the LIFX Cloud:  
   https://cloud.lifx.com
2. Click **Settings → Personal access tokens**  
   https://cloud.lifx.com/settings
3. Click **Generate New Token**
4. Name it something like `XSOAR-LIFX-Integration`
5. Copy the token and paste it into the integration settings under:
   **LIFX API Access Token**

Your token becomes the header:

```
Authorization: Bearer <token>
```

---

## 🎯 Selectors Reference

LIFX selectors identify which lights a command targets.

| Selector Example        | Meaning                                         |
|-------------------------|-------------------------------------------------|
| `all`                   | All lights                                      |
| `group:OverCabinet`     | All lights in the OverCabinet group             |
| `label:Desk Lamp`       | Light with the label "Desk Lamp"                |
| `location:Office`       | All lights in the Office location               |
| `id:d073d5431234`       | Specific bulb by LIFX ID                        |

Selectors apply to all major commands:

- lifx-list-lights  
- lifx-set-state  
- lifx-toggle-power  
- lifx-breathe-effect  
- lifx-pulse-effect  
- lifx-alert-flash  

---

## 📦 Commands Overview

### `lifx-list-lights`
Lists all lights for a selector.

```
!lifx-list-lights selector="group:OverCabinet"
```

Markdown table includes:

- ID  
- Label  
- Group  
- Location  
- Hue/Saturation/Kelvin  
- Brightness  

Optional to display the raw JSON output:

```
verbose=true
```

---

### `lifx-list-scenes`
Lists all scenes with a clean table:

| Name | UUID | Lights | Created At | Updated At |
|------|------|--------|------------|------------|

Dates are auto‑formatted as:
```
2025-01-02 20:25:00 (2 months ago)
```

Use:

```
!lifx-list-scenes
```

---

### `lifx-set-state`
Set power, color, brightness, or infrared levels.

Examples:
```
!lifx-set-state selector="all" power="on"
!lifx-set-state selector="label:Desk Lamp" color="blue"
!lifx-set-state selector="group:OverCabinet" brightness="0.5"
```

---

### `lifx-toggle-power`

```
!lifx-toggle-power selector="location:Office"
```

---

### `lifx-breathe-effect`
```
!lifx-breathe-effect selector="all" color="red" period="1.5" cycles="5"
```

### `lifx-pulse-effect`
```
!lifx-pulse-effect selector="group:OverCabinet" color="yellow"
```

---

### 🚨 `lifx-alert-flash` (perfect for WildFire)

Triggers a severity-based flash:

| Severity | Default Color | Default Cycles |
|----------|----------------|----------------|
| low      | green          | 3              |
| medium   | yellow         | 5              |
| high     | orange         | 7              |
| critical | red            | 10             |

Use:
```
!lifx-alert-flash selector="group:OverCabinet" severity="critical"
```

Override as needed:
```
cycles=20 color="purple"
```

---

### `lifx-test-connection`
Runs a connection test with a readable diagnostic table:

```
!lifx-test-connection selector="all"
```

---

### `lifx-health-check`
Shows API health, rate limits, and reset time:

```
!lifx-health-check
```

Example output:

| Field          | Value                                   |
|----------------|-----------------------------------------|
| HTTP Status    | 200                                     |
| Latency (ms)   | 87                                      |
| Rate Limit     | 60                                      |
| Rate Remaining | 35                                      |
| Rate Reset     | 2025-01-02 20:25:00 (in 2 minutes)      |
| OK             | True                                    |

---

## 🤝 Contributions

Pull requests are welcome!  
Feel free to submit feature enhancements, bug fixes, or improvements to effects & formatting.

---

## 📜 License

MIT License  
Copyright © 2025
