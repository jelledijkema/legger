import logging
import os
import sys

log = logging.getLogger('legger')
log.setLevel(logging.DEBUG)

sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'external')
)

tdi_external = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            os.path.pardir,
                            'ThreeDiToolbox',
                            'external')

# temporary fix of libary geoalchemy2 in ThreeDiToolbox
geoalchemy_fix_file = os.path.join(tdi_external, 'geoalchemy2', '__init__.py')
f = open(geoalchemy_fix_file, 'r')
new_content = f.read().replace(
    """
                            bind.execute("VACUUM %s" % table.name)""",
    """
                            try:
                                bind.execute("VACUUM %s"%table.name)
                            except:
                                pass
    """)
f.close()
f = open(geoalchemy_fix_file, 'w')
f.write(new_content)
f.close()

sys.path.append(tdi_external)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load main tool class
    :param iface: QgsInterface. A QGIS interface instance.
    """
    from .qgistools_plugin import Legger

    return Legger(iface)
