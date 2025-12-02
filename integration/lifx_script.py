import json
import requests
import datetime
import time

ENTRY_TYPE_NOTE = 1
ENTRY_TYPE_ERROR = 4

FORMAT_TEXT = 'text'
FORMAT_JSON = 'json'
FORMAT_MARKDOWN = 'markdown'


def make_note_entry(human_readable, contents=None, context=None):
    entry = {
        'Type': ENTRY_TYPE_NOTE,
        'ContentsFormat': FORMAT_JSON if isinstance(contents, (dict, list)) else FORMAT_TEXT,
        'Contents': contents if contents is not None else human_readable,
        'ReadableContentsFormat': FORMAT_MARKDOWN,
        'HumanReadable': human_readable,
    }
    if context:
        entry['EntryContext'] = context
    return entry


def make_error_entry(message):
    return {
        'Type': ENTRY_TYPE_ERROR,
        'ContentsFormat': FORMAT_TEXT,
        'Contents': message,
        'ReadableContentsFormat': FORMAT_TEXT,
        'HumanReadable': message,
    }


class LifxClient:
    def __init__(self, base_url, api_token, verify=True, proxy=False):
        self.base_url = (base_url or "").rstrip("/")
        self.api_token = api_token
        self.verify = bool(verify)

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        })

    def _request(self, method, path, json_data=None, params=None, raw_response=False):
        url = self.base_url + path
        resp = self.session.request(
            method=method,
            url=url,
            json=json_data,
            params=params,
            verify=self.verify,
        )
        if raw_response:
            return resp
        if resp.status_code >= 400:
            raise Exception(f"LIFX API error {resp.status_code}: {resp.text}")
        try:
            return resp.json()
        except Exception:
            return resp.text

    def list_lights(self, selector='all'):
        return self._request("GET", f"/lights/{selector}")

    def set_state(self, selector, payload):
        return self._request("PUT", f"/lights/{selector}/state", json_data=payload)

    def toggle_power(self, selector, payload):
        return self._request("POST", f"/lights/{selector}/toggle", json_data=payload)

    def breathe_effect(self, selector, payload):
        return self._request("POST", f"/lights/{selector}/effects/breathe", json_data=payload)

    def pulse_effect(self, selector, payload):
        return self._request("POST", f"/lights/{selector}/effects/pulse", json_data=payload)

    def list_scenes(self):
        return self._request("GET", "/scenes")

    def activate_scene(self, scene_uuid, payload):
        return self._request(
            "PUT",
            f"/scenes/scene_id:{scene_uuid}/activate",
            json_data=payload,
            raw_response=True,
        )

    def get_with_headers(self, path):
        resp = self._request("GET", path, raw_response=True)
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return data, resp.headers, resp.status_code


def _bool_arg(val):
    if val is None:
        return None
    v = str(val).lower().strip()
    if v in ("true", "yes", "y", "1"):
        return True
    if v in ("false", "no", "n", "0"):
        return False
    return None


def _normalize_severity(val):
    if val is None:
        return None
    v = str(val).lower().strip()
    mapping = {
        "1": "low", "low": "low",
        "2": "medium", "medium": "medium", "moderate": "medium",
        "3": "high", "high": "high",
        "4": "critical", "critical": "critical", "crit": "critical"
    }
    return mapping.get(v)


def _severity_defaults(sev):
    return {
        "low": ("green", 3),
        "medium": ("yellow", 5),
        "high": ("orange", 7),
        "critical": ("red", 10),
    }.get(sev, ("red", 5))


def _fmt_ts_relative(ts):
    if ts is None or ts == "":
        return "-"
    try:
        ts_int = int(ts)
        dt = datetime.datetime.fromtimestamp(ts_int)
        now = datetime.datetime.now()
        delta = now - dt
        abs_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        seconds = int(delta.total_seconds())
        if seconds < 0:
            return abs_str

        days = seconds // 86400
        if days >= 365:
            years = days // 365
            rel = f"{years} year{'s' if years != 1 else ''}"
        elif days >= 30:
            months = days // 30
            rel = f"{months} month{'s' if months != 1 else ''}"
        elif days >= 1:
            rel = f"{days} day{'s' if days != 1 else ''}"
        else:
            hours = seconds // 3600
            if hours >= 1:
                rel = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                minutes = seconds // 60
                if minutes >= 1:
                    rel = f"{minutes} minute{'s' if minutes != 1 else ''}"
                else:
                    rel = f"{seconds} second{'s' if seconds != 1 else ''}"

        return f"{abs_str} ({rel} ago)"
    except Exception:
        return str(ts)


def lifx_list_lights_command(client, args):
    selector = args.get("selector") or "all"
    verbose = _bool_arg(args.get("verbose"))

    lights = client.list_lights(selector)
    if not isinstance(lights, list):
        lights = [lights]

    md = []
    md.append(f"## LIFX Lights (selector="{selector}")

")
    md.append(
        "| ID | Label | Power | Connected | Group | Location | Color | Brightness |
"
        "|----|-------|-------|-----------|-------|----------|-------|------------|
"
    )

    for l in lights:
        lid = l.get("id", "")
        label = l.get("label", "")
        power = l.get("power", "")
        connected = l.get("connected", "")
        group = (l.get("group") or {}).get("name", "")
        location = (l.get("location") or {}).get("name", "")
        color = l.get("color") or {}
        if isinstance(color, dict):
            color_str = f"h:{color.get('hue','')}, s:{color.get('saturation','')}, k:{color.get('kelvin','')}"
        else:
            color_str = str(color)
        brightness = l.get("brightness", "")

        md.append(
            f"| {lid} | {label} | {power} | {connected} | {group} | {location} | {color_str} | {brightness} |
"
        )

    if verbose:
        md.append("
### Raw JSON
```json
")
        md.append(json.dumps(lights, indent=2))
        md.append("
```
")

    demisto.results(make_note_entry("".join(md), lights, {"LIFX.Light": lights}))


def lifx_set_state_command(client, args):
    selector = args.get("selector") or "all"
    payload = {}

    for f in ("power", "color"):
        if args.get(f):
            payload[f] = args.get(f)

    for f in ("brightness", "duration", "infrared"):
        if args.get(f) is not None:
            payload[f] = float(args[f])

    fast = _bool_arg(args.get("fast"))
    if fast is not None:
        payload["fast"] = fast

    if not payload:
        demisto.results(make_error_entry("No state fields were provided."))
        return

    result = client.set_state(selector, payload)
    md = []
    md.append(f"## LIFX Set State (selector="{selector}")

")
    md.append("```json
")
    md.append(json.dumps(result, indent=2))
    md.append("
```
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.State": result}))


def lifx_toggle_power_command(client, args):
    selector = args.get("selector") or "all"
    payload = {}

    if args.get("duration"):
        payload["duration"] = float(args["duration"])

    result = client.toggle_power(selector, payload)

    md = []
    md.append(f"## LIFX Toggle Power (selector="{selector}")

")
    md.append("```json
")
    md.append(json.dumps(result, indent=2))
    md.append("
```
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.Toggle": result}))


def lifx_breathe_effect_command(client, args):
    selector = args.get("selector") or "all"
    if not args.get("color"):
        demisto.results(make_error_entry("color argument is required for lifx-breathe-effect"))
        return

    payload = {"color": args.get("color")}

    if args.get("from_color"):
        payload["from_color"] = args.get("from_color")

    for f in ("period", "cycles", "peak"):
        if args.get(f):
            payload[f] = float(args[f])

    persist = _bool_arg(args.get("persist"))
    if persist is not None:
        payload["persist"] = persist

    power_on = _bool_arg(args.get("power_on"))
    if power_on is not None:
        payload["power_on"] = power_on

    result = client.breathe_effect(selector, payload)

    md = []
    md.append(f"## LIFX Breathe Effect (selector="{selector}")

")
    md.append("```json
")
    md.append(json.dumps(result, indent=2))
    md.append("
```
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.Breathe": result}))


def lifx_pulse_effect_command(client, args):
    selector = args.get("selector") or "all"
    if not args.get("color"):
        demisto.results(make_error_entry("color argument is required for lifx-pulse-effect"))
        return

    payload = {"color": args.get("color")}

    if args.get("from_color"):
        payload["from_color"] = args.get("from_color")

    for f in ("period", "cycles"):
        if args.get(f):
            payload[f] = float(args[f])

    persist = _bool_arg(args.get("persist"))
    if persist is not None:
        payload["persist"] = persist

    power_on = _bool_arg(args.get("power_on"))
    if power_on is not None:
        payload["power_on"] = power_on

    result = client.pulse_effect(selector, payload)

    md = []
    md.append(f"## LIFX Pulse Effect (selector="{selector}")

")
    md.append("```json
")
    md.append(json.dumps(result, indent=2))
    md.append("
```
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.Pulse": result}))


def lifx_list_scenes_command(client, args):
    verbose = _bool_arg(args.get("verbose"))

    scenes = client.list_scenes()
    if not isinstance(scenes, list):
        scenes = [scenes]

    md = []
    md.append("## LIFX Scenes

")
    md.append(
        "| Name | UUID | Lights | Created At | Updated At |
"
        "|------|------|--------|------------|------------|
"
    )

    for s in scenes:
        name = s.get("name", "-")
        uuid = s.get("uuid", "-")
        states = s.get("states") or s.get("lights") or []

        created = _fmt_ts_relative(s.get("created_at"))
        updated = _fmt_ts_relative(s.get("updated_at"))

        md.append(
            f"| {name} | {uuid} | {len(states)} | {created} | {updated} |
"
        )

    for idx, s in enumerate(scenes, start=1):
        name = s.get("name", "-")
        uuid = s.get("uuid", "-")

        md.append("
---
")
        md.append(f"### Scene {idx}: `{name}`

")
        md.append(f"**UUID:** `{uuid}`

")

        states = s.get("states") or s.get("lights") or []
        if states:
            md.append(
                "| Index | Selector | Brightness | Hue | Saturation | Kelvin |
"
                "|------:|----------|-----------:|----:|-----------:|-------:|
"
            )
            for i, st in enumerate(states, start=1):
                state_obj = st.get("state", st)

                selector = (
                    st.get("selector")
                    or state_obj.get("selector")
                    or state_obj.get("label")
                    or state_obj.get("serial_number")
                    or "-"
                )

                brightness = state_obj.get("brightness", "")
                color = state_obj.get("color", {}) or {}

                hue = color.get("hue", state_obj.get("hue", ""))
                sat = color.get("saturation", state_obj.get("saturation", ""))
                kelvin = color.get("kelvin", state_obj.get("kelvin", ""))

                md.append(
                    f"| {i} | {selector} | {brightness} | {hue} | {sat} | {kelvin} |
"
                )
        else:
            md.append("_No lights found in this scene._
")

    if verbose:
        md.append("
### Raw JSON
```json
")
        md.append(json.dumps(scenes, indent=2))
        md.append("
```
")

    demisto.results(make_note_entry("".join(md), scenes, {"LIFX.Scene": scenes}))


def lifx_activate_scene_command(client, args):
    uuid = args.get("scene_uuid")
    if not uuid:
        demisto.results(make_error_entry("scene_uuid argument is required"))
        return

    payload = {}
    if args.get("duration"):
        payload["duration"] = float(args["duration"])

    fast = _bool_arg(args.get("fast"))
    if fast is not None:
        payload["fast"] = fast

    resp = client.activate_scene(uuid, payload)
    result = {"status": resp.status_code}

    md = []
    md.append("## LIFX Activate Scene

")
    md.append(f"Scene UUID: `{uuid}`  
")
    md.append(f"HTTP Status: `{resp.status_code}`
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.SceneActivation": result}))


def lifx_alert_flash_command(client, args):
    selector = args.get("selector") or "all"
    severity_raw = args.get("severity")
    severity = _normalize_severity(severity_raw)

    if severity:
        default_color, default_cycles = _severity_defaults(severity)
    else:
        default_color, default_cycles = ("red", 5)

    color = args.get("color") or default_color
    cycles = float(args.get("cycles") or default_cycles)
    period = float(args.get("period") or 0.7)

    persist = _bool_arg(args.get("persist"))
    power_on = _bool_arg(args.get("power_on"))

    payload = {
        "color": color,
        "cycles": cycles,
        "period": period,
        "persist": False if persist is None else persist,
        "power_on": True if power_on is None else power_on,
    }

    result = client.pulse_effect(selector, payload)

    md = []
    md.append("## LIFX Alert Flash

")
    md.append(f"- Selector: `{selector}`
")
    md.append(f"- Severity: `{severity_raw}` (normalized: `{severity}`)
")
    md.append(f"- Color: `{color}`
")
    md.append(f"- Cycles: `{cycles}`
")
    md.append(f"- Period: `{period}`
")

    demisto.results(make_note_entry("".join(md), result, {"LIFX.AlertFlash": result}))


def lifx_test_connection_command(client, args):
    selector = args.get("selector") or "all"

    diag = {
        "BaseURL": client.base_url,
        "Selector": selector,
        "VerifySSL": client.verify,
    }

    start = time.time()
    try:
        lights = client.list_lights(selector)
        if not isinstance(lights, list):
            lights = [lights]
        diag["Status"] = "success"
        diag["LightsReturned"] = len(lights)
        diag["Error"] = ""
    except Exception as e:
        lights = []
        diag["Status"] = "failed"
        diag["LightsReturned"] = 0
        diag["Error"] = str(e)

    latency_ms = int((time.time() - start) * 1000)
    diag["LatencyMS"] = latency_ms

    md = []
    md.append("## LIFX Connection Test

")
    md.append("| Field | Value |
")
    md.append("|-------|-------|
")
    md.append(f"| **Base URL** | `{diag['BaseURL']}` |
")
    md.append(f"| **Selector** | `{diag['Selector']}` |
")
    md.append(f"| **Verify SSL** | `{diag['VerifySSL']}` |
")
    md.append(f"| **Status** | `{diag['Status']}` |
")
    md.append(f"| **Lights Found** | `{diag['LightsReturned']}` |
")
    md.append(f"| **Latency (ms)** | `{diag['LatencyMS']}` |
")
    md.append(f"| **Error** | `{diag['Error'] or '(none)'}` |
")

    context = {"LIFX.ConnectionTest": {"Info": diag, "Lights": lights}}
    demisto.results(make_note_entry("".join(md), context, context))


def lifx_health_check_command(client, args):
    start = time.time()
    data, headers, status = client.get_with_headers("/lights/all")
    latency_ms = int((time.time() - start) * 1000)

    remaining = headers.get("X-RateLimit-Remaining") or headers.get("X-RateLimit-Remaining-Short") or "-"
    limit = headers.get("X-RateLimit-Limit") or headers.get("X-RateLimit-Limit-Short") or "-"

    reset_raw = headers.get("X-RateLimit-Reset") or "-"
    reset = _fmt_ts_relative(reset_raw) if reset_raw not in ("", "-") else "-"

    ok = 200 <= status < 400

    md = []
    md.append("## LIFX Health Check

")
    md.append("| Field | Value |
")
    md.append("|-------|-------|
")
    md.append(f"| **HTTP Status** | `{status}` |
")
    md.append(f"| **Latency (ms)** | `{latency_ms}` |
")
    md.append(f"| **Rate Limit** | `{limit}` |
")
    md.append(f"| **Rate Remaining** | `{remaining}` |
")
    md.append(f"| **Rate Reset** | `{reset}` |
")
    md.append(f"| **OK** | `{ok}` |
")

    context = {
        "LIFX.HealthCheck": {
            "Status": status,
            "LatencyMS": latency_ms,
            "RateLimit": limit,
            "RateRemaining": remaining,
            "RateReset": reset,
            "OK": ok,
        }
    }

    demisto.results(make_note_entry("".join(md), context, context))


def test_module(client):
    client.list_lights("all")
    demisto.results("ok")


def main():
    params = demisto.params() or {}
    base = params.get("url")
    token = params.get("api_token")
    insecure = params.get("insecure")

    client = LifxClient(
        base_url=base,
        api_token=token,
        verify=not insecure,
        proxy=params.get("proxy"),
    )

    cmd = demisto.command()
    args = demisto.args()

    try:
        if cmd == "test-module":
            test_module(client)
        elif cmd == "lifx-list-lights":
            lifx_list_lights_command(client, args)
        elif cmd == "lifx-set-state":
            lifx_set_state_command(client, args)
        elif cmd == "lifx-toggle-power":
            lifx_toggle_power_command(client, args)
        elif cmd == "lifx-breathe-effect":
            lifx_breathe_effect_command(client, args)
        elif cmd == "lifx-pulse-effect":
            lifx_pulse_effect_command(client, args)
        elif cmd == "lifx-list-scenes":
            lifx_list_scenes_command(client, args)
        elif cmd == "lifx-activate-scene":
            lifx_activate_scene_command(client, args)
        elif cmd == "lifx-alert-flash":
            lifx_alert_flash_command(client, args)
        elif cmd == "lifx-test-connection":
            lifx_test_connection_command(client, args)
        elif cmd == "lifx-health-check":
            lifx_health_check_command(client, args)
        else:
            demisto.results(make_error_entry(f"Command '{cmd}' is not implemented."))
    except Exception as e:
        demisto.results(make_error_entry(f"Failed to execute '{cmd}'. Error: {e}"))


if __name__ in ("__main__", "builtin", "builtins"):
    main()
