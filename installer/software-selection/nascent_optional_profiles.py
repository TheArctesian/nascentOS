"""Bounded VPN/gaming choices; render validated module constants only."""
import importlib.util
from pathlib import Path

GAMING_KEYS = ('enable', 'gamemode', 'gamescope', 'steam', 'steamGamescopeSession', 'maxMapCount')
STEAM = {'id': 'steam', 'name': 'Steam', 'license': 'Proprietary / Valve terms',
         'url': 'https://store.steampowered.com/subscriber_agreement/'}


def vpn_adapter():
    here = Path(__file__).resolve().parent
    locations = (here / 'vpn-support/installer_adapter.py', here.parents[1] / 'vpn-support/installer_adapter.py')
    for path in locations:
        if path.is_file():
            spec = importlib.util.spec_from_file_location('nascent_vpn_installer_adapter', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise ValueError('VPN selection support is missing from the installer source')


def providers(system):
    return vpn_adapter().available_providers(system)


def validate_vpn(provider, system):
    vpn_adapter().render_selection(provider, system)
    return provider


def gaming_defaults(enabled=False):
    return dict.fromkeys(GAMING_KEYS, False) | {'enable': enabled, 'gamemode': enabled, 'gamescope': enabled}


def validate_gaming(value, system):
    if not isinstance(value, dict) or set(value) - set(GAMING_KEYS):
        raise ValueError('Invalid gaming selection')
    if any(type(item) is not bool for item in value.values()):
        raise ValueError('Gaming choices must be booleans')
    result = gaming_defaults(value.get('enable', False))
    result.update(value)
    if not result['enable'] and any(result[key] for key in GAMING_KEYS if key != 'enable'):
        raise ValueError('Gaming components require the gaming profile')
    if result['steam'] and system != 'x86_64-linux':
        raise ValueError('Steam requires x86_64-linux')
    if result['steamGamescopeSession'] and not (result['steam'] and result['gamescope']):
        raise ValueError('Steam gamescope session requires Steam and gamescope')
    return result


def render_vpn(provider, system):
    return vpn_adapter().render_selection(provider, system)


def render_gaming(value, system):
    value = validate_gaming(value, system)
    options = {'enable': 'enable', 'gamemode': 'gamemode.enable', 'gamescope': 'gamescope.enable',
               'steam': 'steam.enable', 'steamGamescopeSession': 'steam.gamescopeSession.enable',
               'maxMapCount': 'tuning.maxMapCount.enable'}
    return '{ ... }: {\n' + ''.join(
        f'  nascent.gaming.{options[key]} = {str(value[key]).lower()};\n' for key in GAMING_KEYS) + '}\n'
