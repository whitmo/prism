from mock import Mock
from mock import call
from pyramid.exceptions import ConfigurationError
import unittest


class TestReloadableApp(unittest.TestCase):
    response_mock = Mock(name='response')
    app_mock = Mock(name='make_app')
    app_mock.get_app.side_effect = response_mock
    check_mock = Mock(name='make_check')

    def teardown(self):
        self.app_mock.reset_mock()
        self.check_mock.reset_mock()

    def makeone(self, gc, **lc):
        from .. import reloadable
        self.loader = Mock()
        app = reloadable.App.factory(self.loader, gc, **lc)
        return app

    def test_app_empty(self):
        with self.assertRaises(ConfigurationError):
            self.makeone({}, **{})

    def test_app_named_no_check(self):
        app = self.makeone({}, app='prismconf.tests.test_reloadable.TestReloadableApp.app_mock')
        assert not app.checks
        assert app.app_loader.func is self.loader.get_app

    def test_app_named_w_check(self):
        hpath = 'prismconf.tests.test_reloadable.TestReloadableApp.{0}'
        gc = {}
        app = self.makeone(gc,
                           app=hpath.format('app_mock'),
                           checker=hpath.format('check_mock'))

        assert 'checker' in app.checks
        assert self.check_mock.called
        assert self.check_mock.call_args == call(app, gc)

    def test_wsgi_check_true(self):
        hpath = 'prismconf.tests.test_reloadable.TestReloadableApp.{0}'
        gc = {}
        app = self.makeone(gc,
                           app=hpath.format('app_mock'),
                           checker=hpath.format('check_mock'))

        res = app({}, Mock())
        #import pdb;pdb.set_trace()
        pass
