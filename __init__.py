import logging
import os
import sys

log = logging.getLogger('legger')
log.setLevel(logging.DEBUG)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'external')
)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)),
                 os.path.pardir,
                 'ThreeDiToolbox',
                 'external')
)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load main tool class
    :param iface: QgsInterface. A QGIS interface instance.
    """
    from .qgistools_plugin import Legger

    return Legger(iface)
