from functools import partial
from pyramid.exceptions import ConfigurationError
from pyramid.path import DottedNameResolver
from rutter.urlmap import URLMap
from rutter.urlmap import _default_not_found_app
from rutter.urlmap import _normalize_url
from rutter.urlmap import _parse_path_expression
import logging
import threading

logger = logging.getLogger(__name__)


class App(object):
    """
    A wrapper for reload an application based on a monitor
    """
    resolve = staticmethod(DottedNameResolver(None).maybe_resolve)
    reload_lock = threading.Lock()

    def __init__(self, loader):
        self.loader = loader
        self.checks = {}
        self.current_app = None
        self.app_loader = None

    def __call__(self, environ, start_response):
        if self.current_app is None:
            raise RuntimeError("No registered app")
        return self.current_app(environ, start_response)

    def init_app(self, conf_list, global_conf):
        try:
            _, spec = next((name, spec) for name, spec in conf_list if name == 'app')
        except StopIteration:
            raise ConfigurationError("App name and specification required"
                                     " for prismconf.reloadable.App")

        self.app_loader = partial(self.loader.get_app, spec, global_conf=global_conf)
        app = self.current_app = self.app_loader()
        return app

    def load_monitors(self, conf_list, global_conf):
        mon_specs = ((name, spec) for name, spec in conf_list \
                     if name != 'app')
        for name, spec in mon_specs:
            mon = self.resolve(spec)(self, global_conf)
            yield name, mon

    @classmethod
    def factory(cls, loader, global_conf, **local_conf):
        app = cls(loader)
        conf_list = local_conf.items()
        inner_app = app.init_app(conf_list, global_conf)
        checks = {name:mon for name, mon\
                  in app.load_monitors(conf_list, global_conf)}
        app.checks.update(checks)
        logger.debug("%s %s", inner_app, checks)
        return app


factory = App.factory


class URLMap(URLMap):
    """
    Reloadable composite app
    """
    _default_not_found_app = _default_not_found_app

    def __init__(self, not_found_app=None):
        self.applications = []
        self.not_found_application = not_found_app or self._default_not_found_app
        self.loaders = {}

    def __call__(self, environ, start_response):
        host = environ.get('HTTP_HOST', environ.get('SERVER_NAME')).lower()
        if ':' in host:
            host, port = host.split(':', 1)
        else:
            if environ['wsgi.url_scheme'] == 'http':
                port = '80'
            else:
                port = '443'
        hostport = host + ':' + port
        path_info = environ.get('PATH_INFO')
        path_info = _normalize_url(path_info, False)[1]
        for dom_url, app in self.applications:
            domain, app_url = dom_url
            if domain and domain != host and domain != hostport:
                continue
            if (path_info == app_url
                or path_info.startswith(app_url + '/')):
                environ['SCRIPT_NAME'] += app_url
                environ['PATH_INFO'] = path_info[len(app_url):]
                return app(environ, start_response)
        environ['paste.urlmap_object'] = self
        return self.not_found_application(environ, start_response)


def urlmap_factory(loader, global_conf, **local_conf):
    if 'not_found_app' in local_conf:
        not_found_app = local_conf.pop('not_found_app')
    else:
        not_found_app = global_conf.get('not_found_app')

    if not_found_app:
        not_found_app = loader.get_app(not_found_app, global_conf=global_conf)

    if not_found_app is not None:
        urlmap = URLMap(not_found_app=not_found_app)
    else:
        urlmap = URLMap()

    for path, app_name in local_conf.items():
        path = _parse_path_expression(path)
        app = loader.get_app(app_name, global_conf=global_conf)
        urlmap[path] = app
        urlmap.loaders[path] = (loader, global_conf, threading.Lock())
    return urlmap
