import logging
import os.path
from collections import OrderedDict
import tempfile

from qgis.core import (QgsDataSourceUri, QgsProject, QgsProject, QgsVectorLayer, QgsLayerTreeNode)

log = logging.getLogger(__name__)


class LayerManager():

    def __init__(self, iface, spatialite_path):

        self.iface = iface
        self.spatialite_path = spatialite_path

        self.legger_root_name = 'legger'
        self.legger_netwerktool_name = 'aanwijzen'
        self.legger_maplayers_name = 'kaartlagen'

    def _get_or_create_group(self, base_group, name, position=0, open_new=True, open_existing=True, clear=False):
        new = False
        group = base_group.findGroup(name)
        if group is None:
            group = base_group.insertGroup(position, name)
            new = True
            group.setExpanded(open_new)
        else:
            group.setExpanded(open_existing)
            if clear:
                group.removeAllChildren()
        return group, new

    def add_layer_to_group(self, group, vector_layer, style_path, visible=True, position=0):
        vector_layer.loadNamedStyle(style_path)
        QgsProject.instance().addMapLayer(
            vector_layer,
            False)
        group.insertLayer(position, vector_layer)
        QgsProject.instance().layerTreeRoot().findLayer(vector_layer).setItemVisibilityChecked(visible)
        # legend = self.iface.legendInterface()
        # legend.setLayerVisible(vector_layer, visible)

    def get_or_create_legger_root(self, clear=False):
        root = QgsProject.instance().layerTreeRoot()
        return self._get_or_create_group(root, self.legger_root_name, clear=clear)

    def get_or_create_networktool_root(self, clear=False):
        legger_root, new = self.get_or_create_legger_root()
        return self._get_or_create_group(legger_root, self.legger_netwerktool_name, clear=clear)

    def get_or_create_maplayers_root(self, clear=False):
        legger_root, new = self.get_or_create_legger_root()
        return self._get_or_create_group(legger_root, self.legger_maplayers_name, position=2, clear=clear)

    def add_layers_to_map(self):
        # {layer_name: [(name, layer, field, style, geometry_field, range), ...], ... }

        styled_layers = OrderedDict([
            ('basisgegevens', [
                ('debiet', 'hydroobject', 'debiet', 'debiet', 'geometry', 'min_max_line'),
                ('categorie', 'hydroobject', 'categorieoppwaterlichaam', 'category', 'geometry', 'min_max_line'),
                # ('du debiet', 'duikersifonhevel', 'debiet', 'debiet', 'geometry', 'min_max_line'),
            ]),
            ('afgeleid', [
            ]),
            ('tbv begroeiingsgraad', [
                ('aanwijzen', 'hydroobject', 'begroeiingsvariant_id', 'begroeiingsvariant', 'geometry', None),
                ('begroeiingsadvies', 'begroeiingsadvies', 'advies_id', 'begroeiingsvariant', 'geometry', None),
                ('begroeiingsvariant', 'begroeiingsadvies', 'aangew_bv_id', 'begroeiingsvariant',
                 'geometry', None),
                # ('sterk min profiel', 'ruimte_view', 'ruim', 'min_max_line', 'geometry', None),
                # ('ruimte', 'ruimte_view', 'over_width', 'min_max_line', 'geometry', None),
            ]),
            ('gekozen legger', [
                ('verhang', 'hydroobjects_selected_legger', '', 'verhang', 'geometry', None),
                ('voortgang', 'hydroobjects_selected_legger', '', 'voortgang', 'geometry', None),
                ('gekozen diepte [m]', 'hydroobjects_selected_legger', '', 'gekozen_diepte', 'geometry', None),
                ('overdiepte [m]', 'hydroobjects_selected_legger', '', 'overdiepte', 'geometry', None),
                ('gekozen bodembreedte [m]', 'hydroobjects_selected_legger', '', 'gekozen_bodembreedte', 'geometry',
                 None),
                ('gekozen waterbreedte [m]', 'hydroobjects_selected_legger', '', 'gekozen_waterbreedte', 'geometry',
                 None),
                ('gekozen overbreedte totaal [m]', 'hydroobjects_selected_legger', '', 'overbreedte_totaal', 'geometry',
                 None),
                ('gekozen begroeiingsvariant', 'hydroobjects_selected_legger', 'geselecteerde_begroeiingsvariant',
                 'gekozen_begroeiingsvariant', 'geometry', None),
            ]),
            ('achtergrond', [
                ('watervlakken', 'waterdeel', '', 'waterdeel', 'geometry', None),
            ])
        ])

        maplayer_group, new = self.get_or_create_maplayers_root()
        maplayer_group.removeAllChildren()

        # add source stat metadata
        uri = QgsDataSourceUri()
        uri.setDatabase(self.spatialite_path.replace('\\', '/'))
        uri.setDataSource('', 'legger_source', '')

        # vector_layer = QgsVectorLayer(uri.uri(), 'metadata statistiek bronnen', 'spatialite')
        # QgsProject.instance().addMapLayer(
        #     vector_layer,
        #     False)
        # stat_group.insertLayer(0, vector_layer)

        tmp_dir = tempfile.gettempdir()

        for group, layers in styled_layers.items():
            qgroup = maplayer_group.insertGroup(100, group)
            qgroup.setExpanded(False)

            for layer in layers:
                uri = QgsDataSourceUri()
                uri.setDatabase(self.spatialite_path.replace('\\', '/'))
                uri.setDataSource('', layer[1], layer[4])

                vector_layer = QgsVectorLayer(uri.uri(), layer[0], 'spatialite')

                if vector_layer.isValid():
                    style_path = os.path.join(
                        os.path.dirname(os.path.realpath(__file__)),
                        os.path.pardir,
                        'layer_styles',
                        'legger',
                        layer[3] + '.qml')
                    style = open(style_path, 'r').read()

                    # replace by column name
                    style = style.replace('<<variable>>', layer[2])

                    new_style_path = os.path.join(tmp_dir, 'cr_' + layer[3] + '_' + layer[2] + '.qml')

                    new_style_file = open(new_style_path, 'w')
                    new_style_file.write(style)
                    new_style_file.close()

                    self.add_layer_to_group(qgroup, vector_layer, new_style_path, visible=False, position=100)
