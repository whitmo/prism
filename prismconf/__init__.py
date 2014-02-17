from ConfigParser import RawConfigParser
from functools import wraps
from functools import partial
from path import path
import inspect

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
    here = path(filename).abspath().parent
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


def simple_prep_config(global_config, **settings):
    defaults = global_config.copy()
    defaults.update(load_settings_from_file(global_config['__file__']))
    defaults.update(settings)
    return defaults


class settings_hierarchy(object):
    resolve = staticmethod(DottedNameResolver(None).maybe_resolve)
    base_handler = staticmethod(simple_prep_config)

    def __init__(self, handler=None):
        if handler is None:
            self.handler = self.stacked_prep_config

    def __call__(self, callee):
        @wraps(callee)
        def inner(global_config, **settings):
            settings = self.handler(global_config, **settings)
            return callee(settings)
        return inner

    def additional_settings(self, source_specs, settings):
        settings = settings.copy()
        sources = source_specs.split()
        for source in (x.strip() for x in sources):
            source_handler = self.resolve(source)
            if not (source_handler, None):
                yield source_handler(settings)

    def stacked_prep_config(self, global_config, **settings):
        settings = self.base_handler(global_config, **settings)
        sources = settings.get('config.sources', None)
        if not (sources is None):
            for extra in self.additional_settings(sources):
                settings.update(extra)
        return settings

# ENV transform mapping  
compose_settings = settings_hierarchy()
compose_settings_no_gc = partial(settings_hierarchy(), {})
