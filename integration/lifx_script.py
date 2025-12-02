"""
Cortex XSOAR / XSIAM integration for LIFX smart lights.

This version is intentionally self-contained:
- Does NOT import CommonServerPython
- Uses only `demisto`, `requests`, and `json`
- Returns classic entry objects (dicts) via demisto.results()

Commands implemented (must match YAML command names):
    - test-module
    - lifx-list-lights
    - lifx-set-state
    - lifx-toggle-power
    - lifx-breathe-effect
    - lifx-pulse-effect
    - lifx-list-scenes
    - lifx-activate-scene
    - lifx-alert-flash
    - lifx-test-connection
"""

import json
import requests


# Basic Demisto entry constants (same as CommonServerPython usually provides)
ENTRY_TYPE_NOTE = 1
ENTRY_TYPE_ERROR = 4

FORMAT_TEXT = 'text'
FORMAT_JSON = 'json'
FORMAT_MARKDOWN = 'markdown'


def make_note_entry(human_readable, contents=None, context=None):
    """
    Build a standard note entry for the War Room.
    """
    entry = {
        'Type': ENTRY_TYPE_NOTE,
        'ContentsFormat': FORMAT_JSON if isinstance(contents, (dict, list)) else FORMAT_TEXT,
        'Contents': contents if contents is not None else human_readable,
        'ReadableContentsFormat': FORMAT_MARKDOWN,
        'HumanReadable': human_readable,
    }
    if context is not None:
        entry['EntryContext'] = context
    return entry


def make_error_entry(message):
    """
    Build a standard error entry for the War Room.
    """
    return {
        'Type': ENTRY_TYPE_ERROR,
        'ContentsFormat': FORMAT_TEXT,
        'Contents': message,
        'ReadableContentsFormat': FORMAT_TEXT,
        'HumanReadable': message,
    }


class LifxClient(object):
    """
    Minimal HTTP client for the LIFX Cloud API.
    """

    def __init__(self, base_url, api_token, verify=True, proxy=False):
        # Normalize base URL
        self.base_url = (base_url or '').rstrip('/')
        self.api_token = api_token
        self.verify = bool(verify)

        # Let the platform handle proxies; if you really need manual proxy
        # configuration, extend here. For now, we just trust env/engine.
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'Bearer {}'.format(api_token),
            'Content-Type': 'application/json',
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
            # Keep it simple: raise a descriptive error
            raise Exception('LIFX API error {}: {}'.format(resp.status_code, resp.text))

        try:
            return resp.json()
        except Exception:
            # If it isn't JSON, return the raw text
            return resp.text

    def list_lights(self, selector='all'):
        return self._request('GET', '/lights/{}'.format(selector or 'all'))

    def set_state(self, selector, payload):
        return self._request('PUT', '/lights/{}/state'.format(selector), json_data=payload)

    def toggle_power(self, selector, payload):
        return self._request('POST', '/lights/{}/toggle'.format(selector), json_data=payload)

    def breathe_effect(self, selector, payload):
        return self._request('POST', '/lights/{}/effects/breathe'.format(selector), json_data=payload)

    def pulse_effect(self, selector, payload):
        return self._request('POST', '/lights/{}/effects/pulse'.format(selector), json_data=payload)

    def list_scenes(self):
        return self._request('GET', '/scenes')

    def activate_scene(self, scene_uuid, payload):
        return self._request(
            'PUT',
            '/scenes/scene_id:{}/activate'.format(scene_uuid),
            json_data=payload,
            raw_response=True,
        )


# -----------------------------------------
# Helpers
# -----------------------------------------
def _bool_arg(val):
    if val is None:
        return None
    v = str(val).strip().lower()
    if v in ('true', 'yes', 'y', '1'):
        return True
    if v in ('false', 'no', 'n', '0'):
        return False
    return None


def _normalize_severity(val):
    if val is None:
        return None
    v = str(val).strip().lower()
    if v in ('1', 'low'):
        return 'low'
    if v in ('2', 'medium', 'moderate'):
        return 'medium'
    if v in ('3', 'high'):
        return 'high'
    if v in ('4', 'critical', 'crit'):
        return 'critical'
    return None


def _severity_defaults(severity):
    if severity == 'low':
        return 'green', 3
    if severity == 'medium':
        return 'yellow', 5
    if severity == 'high':
        return 'orange', 7
    if severity == 'critical':
        return 'red', 10
    return 'red', 5


# -----------------------------------------
# Command implementations
# -----------------------------------------
def lifx_list_lights_command(client, args):
    selector = args.get('selector') or 'all'
    lights = client.list_lights(selector)
    if not isinstance(lights, list):
        lights = [lights]

    human = 'LIFX Lights (selector="{}"):\n```json\n{}\n```'.format(
        selector, json.dumps(lights, indent=2)
    )
    context = {'LIFX.Light': lights}
    demisto.results(make_note_entry(human, contents=lights, context=context))


def lifx_set_state_command(client, args):
    selector = args.get('selector') or 'all'
    payload = {}

    for field in ('power', 'color'):
        if args.get(field):
            payload[field] = args.get(field)

    for f in ('brightness', 'duration', 'infrared'):
        if args.get(f) is not None:
            payload[f] = float(args[f])

    fast = _bool_arg(args.get('fast'))
    if fast is not None:
        payload['fast'] = fast

    if not payload:
        demisto.results(make_error_entry('No state fields were provided.'))
        return

    result = client.set_state(selector, payload)
    human = 'LIFX Set State (selector="{}")\n```json\n{}\n```'.format(
        selector, json.dumps(result, indent=2)
    )
    context = {'LIFX.State': result}
    demisto.results(make_note_entry(human, contents=result, context=context))


def lifx_toggle_power_command(client, args):
    selector = args.get('selector') or 'all'
    payload = {}

    if args.get('duration'):
        payload['duration'] = float(args['duration'])

    result = client.toggle_power(selector, payload)
    human = 'LIFX Toggle Power (selector="{}")\n```json\n{}\n```'.format(
        selector, json.dumps(result, indent=2)
    )
    context = {'LIFX.Toggle': result}
    demisto.results(make_note_entry(human, contents=result, context=context))


def lifx_breathe_effect_command(client, args):
    selector = args.get('selector') or 'all'
    if not args.get('color'):
        demisto.results(make_error_entry('color argument is required for lifx-breathe-effect'))
        return

    payload = {'color': args.get('color')}

    if args.get('from_color') is not None:
        payload['from_color'] = args.get('from_color')

    if args.get('period') is not None:
        payload['period'] = float(args['period'])

    if args.get('cycles') is not None:
        payload['cycles'] = float(args['cycles'])

    if args.get('peak') is not None:
        payload['peak'] = float(args['peak'])

    persist = _bool_arg(args.get('persist'))
    if persist is not None:
        payload['persist'] = persist

    power_on = _bool_arg(args.get('power_on'))
    if power_on is not None:
        payload['power_on'] = power_on

    result = client.breathe_effect(selector, payload)
    human = 'LIFX Breathe Effect (selector="{}")\n```json\n{}\n```'.format(
        selector, json.dumps(result, indent=2)
    )
    context = {'LIFX.Breathe': result}
    demisto.results(make_note_entry(human, contents=result, context=context))


def lifx_pulse_effect_command(client, args):
    selector = args.get('selector') or 'all'
    if not args.get('color'):
        demisto.results(make_error_entry('color argument is required for lifx-pulse-effect'))
        return

    payload = {'color': args.get('color')}

    if args.get('from_color'):
        payload['from_color'] = args.get('from_color')

    if args.get('period'):
        payload['period'] = float(args['period'])

    if args.get('cycles'):
        payload['cycles'] = float(args['cycles'])

    persist = _bool_arg(args.get('persist'))
    if persist is not None:
        payload['persist'] = persist

    power_on = _bool_arg(args.get('power_on'))
    if power_on is not None:
        payload['power_on'] = power_on

    result = client.pulse_effect(selector, payload)
    human = 'LIFX Pulse Effect (selector="{}")\n```json\n{}\n```'.format(
        selector, json.dumps(result, indent=2)
    )
    context = {'LIFX.Pulse': result}
    demisto.results(make_note_entry(human, contents=result, context=context))


def lifx_list_scenes_command(client, args):
    scenes = client.list_scenes()
    if not isinstance(scenes, list):
        scenes = [scenes]

    human = 'LIFX Scenes:\n```json\n{}\n```'.format(json.dumps(scenes, indent=2))
    context = {'LIFX.Scene': scenes}
    demisto.results(make_note_entry(human, contents=scenes, context=context))


def lifx_activate_scene_command(client, args):
    scene_uuid = args.get('scene_uuid')
    if not scene_uuid:
        demisto.results(make_error_entry('scene_uuid argument is required for lifx-activate-scene'))
        return

    payload = {}
    if args.get('duration'):
        payload['duration'] = float(args['duration'])

    fast = _bool_arg(args.get('fast'))
    if fast is not None:
        payload['fast'] = fast

    resp = client.activate_scene(scene_uuid, payload)
    human = 'LIFX scene {} activation returned HTTP {}.'.format(scene_uuid, resp.status_code)
    context = {'LIFX.SceneActivation': {'status': resp.status_code}}
    demisto.results(make_note_entry(human, contents={'status': resp.status_code}, context=context))


def lifx_alert_flash_command(client, args):
    selector = args.get('selector') or 'all'

    severity_raw = args.get('severity')
    severity = _normalize_severity(severity_raw)

    color_arg = args.get('color')
    cycles_arg = args.get('cycles')

    if severity and not color_arg:
        default_color, default_cycles = _severity_defaults(severity)
    else:
        default_color, default_cycles = 'red', 5

    color = color_arg or default_color
    cycles = float(cycles_arg) if cycles_arg else float(default_cycles)
    period = float(args.get('period') or 0.7)

    power_on = _bool_arg(args.get('power_on'))
    if power_on is None:
        power_on = True

    persist = _bool_arg(args.get('persist'))
    if persist is None:
        persist = False

    payload = {
        'color': color,
        'cycles': cycles,
        'period': period,
        'power_on': power_on,
        'persist': persist,
    }

    result = client.pulse_effect(selector, payload)
    human = (
        "LIFX alert flash executed for selector='{selector}', "
        "severity='{severity}', color='{color}', cycles={cycles}, period={period}."
    ).format(
        selector=selector,
        severity=severity_raw,
        color=color,
        cycles=cycles,
        period=period,
    )
    context = {'LIFX.AlertFlash': result}
    demisto.results(make_note_entry(human, contents=result, context=context))


def lifx_test_connection_command(client, args):
    selector = args.get('selector') or 'all'

    diag = {
        'BaseURL': client.base_url,
        'SelectorTested': selector,
        'VerifySSL': client.verify,
    }

    try:
        lights = client.list_lights(selector)
        if not isinstance(lights, list):
            lights = [lights]

        diag['Status'] = 'success'
        diag['LightsReturned'] = len(lights)
        diag['Error'] = ''
    except Exception as e:
        lights = []
        diag['Status'] = 'failed'
        diag['LightsReturned'] = 0
        diag['Error'] = str(e)

    human = 'LIFX Connection Test:\n```json\n{}\n```'.format(json.dumps(diag, indent=2))
    context = {
        'LIFX.ConnectionTest': {
            'Info': diag,
            'Lights': lights,
        }
    }
    demisto.results(make_note_entry(human, contents=context['LIFX.ConnectionTest'], context=context))


def test_module(client):
    """
    Called by the Test button.
    """
    # Just do a small call and fail loudly if it breaks.
    client.list_lights('all')
    demisto.results('ok')


def main():
    params = demisto.params() or {}
    base_url = params.get('url')
    api_token = params.get('api_token')
    insecure = params.get('insecure', False)

    client = LifxClient(
        base_url=base_url,
        api_token=api_token,
        verify=not insecure,
        proxy=params.get('proxy', False),
    )

    cmd = demisto.command()
    args = demisto.args()

    try:
        if cmd == 'test-module':
            test_module(client)
        elif cmd == 'lifx-list-lights':
            lifx_list_lights_command(client, args)
        elif cmd == 'lifx-set-state':
            lifx_set_state_command(client, args)
        elif cmd == 'lifx-toggle-power':
            lifx_toggle_power_command(client, args)
        elif cmd == 'lifx-breathe-effect':
            lifx_breathe_effect_command(client, args)
        elif cmd == 'lifx-pulse-effect':
            lifx_pulse_effect_command(client, args)
        elif cmd == 'lifx-list-scenes':
            lifx_list_scenes_command(client, args)
        elif cmd == 'lifx-activate-scene':
            lifx_activate_scene_command(client, args)
        elif cmd == 'lifx-alert-flash':
            lifx_alert_flash_command(client, args)
        elif cmd == 'lifx-test-connection':
            lifx_test_connection_command(client, args)
        else:
            demisto.results(make_error_entry('Command {} is not implemented.'.format(cmd)))
    except Exception as e:
        # Last-resort error return
        demisto.results(make_error_entry('Failed to execute {}. Error: {}'.format(cmd, e)))


if __name__ in ('__main__', 'builtin', 'builtins'):
    main()