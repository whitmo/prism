from ConfigParser import RawConfigParser
from functools import wraps
from path import path
from pyramid.config import Configurator
from pyramid.path import DottedNameResolver
import inspect


truthy = frozenset(('t', 'true', 'y', 'yes', 'on', '1'))


class stacked_settings(object):
    resolve = staticmethod(DottedNameResolver(None).maybe_resolve)

    def __init__(self, handler=None):
        if handler is None:
            self.handler = self.stack_config

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

    def stack_config(self, global_config, **settings):
        settings = self.base_handler(global_config, **settings)
        sources = settings.get('config.sources', None)
        if not (sources is None):
            for extra in self.additional_settings(sources, settings):
                settings.update(extra)
        return settings

    @classmethod
    def stack_globalconfig_and_settings(cls, global_config, **settings):
        defaults = global_config.copy()
        defaults.update(settings)
        return defaults

    base_handler = stack_globalconfig_and_settings

    @staticmethod
    def asbool(value):
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        value = str(value).strip()
        return value.lower() in truthy

    @staticmethod
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
    
    def to_config(cls, global_config, app_settings):
        config_file = global_config.get('__file__')
        settings = cls.load_settings_from_file(config_file)
        settings.update(app_settings)

        caller = caller_module()
        resolver = DottedNameResolver(caller)
        package = resolver.get_package()
        config = Configurator(settings=settings, package=package)
        return config


compose_settings = stacked_settings()


class sources(object):
    # defaults.update(cls.load_settings_from_file(global_config['__file__']))

    @staticmethod
    def ini_file(settings):
        settings.get()
        if not 'config.ini_file' in settings:
            fp = settings['__file__']
            
        fps = fp.strip().split('')
        out = dict()
        load = stacked_settings.load_settings_from_file
        [out.update(load(fp)) for fp in fps]
        return out



def caller_module(depth=1):
    frm = inspect.stack()[depth + 1]
    caller = inspect.getmodule(frm[0])
    return caller


