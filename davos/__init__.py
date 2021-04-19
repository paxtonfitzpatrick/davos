import pkg_resources

from davos._davos import Davos


__all__ = ['davos', 'smuggle', 'activate', 'deactivate', 'is_active']
__version__ = pkg_resources.get_distribution('davos').version


davos = Davos()
davos.initialize()

smuggle = davos.smuggler
activate = davos.activate_parser
deactivate = davos.deactivate_parser
is_active = davos.parser_is_active
