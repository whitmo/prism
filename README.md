Prism
=====

Some helpers for configuring and serving `pyramid` apps.


## Stacked settings

`prism` provides a number of utilities for managing configuration
values, most notably the `compose_settings` decorator for use with
`paste.deploy` styles configuration.

This spelling (in it's most basic form):

 ```python
 from prism import config

 @config.compose_setttings
 def main(settings):
     ...
 ```

is rougly equivalent to:

 ```python
 # OLD WAY

 def main(global_config, settings):
     settings = global_config.copy()
     settings.update(settings)
     ...
 ```

The decorator also adds a plugin point for adding additional overrides
to the settings mapping.

For example, this plugin will roll up and flatten all the sections in
an inifile and add them to your settings.

 ```ini
 [app:main]
 use = egg:MyApp
 config.sources =
   prism.config.sources.ini_file

 config.ini_file = /path/to/some/config.ini
 ```


