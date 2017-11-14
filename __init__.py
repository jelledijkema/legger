import logging

log = logging.getLogger('legger')
log.setLevel(logging.DEBUG)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load main tool class
    :param iface: QgsInterface. A QGIS interface instance.
    """
    from .qgistools_plugin import Legger

    return Legger(iface)
