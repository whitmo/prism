from ConfigParser import RawConfigParser
import inspect
import os.path

from pyramid.config import Configurator
from pyramid.path import DottedNameResolver

def config_from_settings(global_config, app_settings):
    config_file = global_config.get('__file__')
    settings = load_settings_from_file(config_file)
    settings.update(app_settings)

    caller = caller_module()
    resolver = DottedNameResolver(caller)
    package = resolver.get_package()
    config = Configurator(settings=settings, package=package)
    return config

def load_settings_from_file(filename):
    here = os.path.abspath(os.path.dirname(filename))
    parser = RawConfigParser({'here': here})
    parser.read(filename)

    settings = {}
    for section in parser.sections():
        prefix = section.replace(':', '.')
        for k, v in parser.items(section):
            settings[prefix + '.' + k] = v

    return settings

truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))

def asbool(value):
    if value is None:
        return False

    if isinstance(value, bool):
        return value

    value = str(value).strip()
    return value.lower() in truthy

def caller_module(depth=1):
    frm = inspect.stack()[depth + 1]
    caller = inspect.getmodule(frm[0])
    return caller
