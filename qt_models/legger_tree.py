"""
    specific implementation of QgsTreeModel for hydrovakken, used for the hydrovakken tree.
    to change visible data in tree, modify the HORIZONTAL_HEADERS config
"""

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBrush, QColor, QIcon
from legger import settings
from tree import BaseTreeItem, BaseTreeModel, CHECKBOX_FIELD, INDICATION_HOVER
from qgis.core import NULL

# field and display config of 'hydrovakken'
HORIZONTAL_HEADERS = (
    {'field': 'hydro_id', 'column_width': 150},
    # {'field': 'feat_id', 'column_width': 25},
    {'field': 'sp', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
    {'field': 'ep', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
    {'field': 'selected', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50,
     'single_selection': True},
    {'field': 'hover', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50},
    {'field': 'distance', 'header': 'afstand', 'show': False, 'column_width': 50},
    {'field': 'length', 'header': 'Lengte', 'show': False, 'column_width': 50},
    {'field': 'category', 'header': 'cat', 'column_width': 40},
    {'field': 'begroeiingsvariant_id', 'header': 'beg', 'column_width': 40},
    {'field': 'flow', 'header': 'debiet', 'show': False, 'column_width': 50},
    {'field': 'target_level', 'show': False, 'column_width': 50},
    {'field': 'depth', 'header': 'diepte', 'show': False, 'column_width': 50},
    {'field': 'width', 'header': 'breedte', 'show': False, 'column_width': 50},
    {'field': 'variant_min_depth', 'show': False, 'column_width': 60},
    {'field': 'variant_max_depth', 'show': False, 'column_width': 60},
    {'field': 'selected_depth_tmp', 'header': 'sel d', 'column_width': 60},
    {'field': 'selected_depth', 'header': 'prof d', 'column_width': 60},
    {'field': 'selected_width', 'header': 'prof b', 'column_width': 60},
    {'field': 'over_depth', 'header': 'over d', 'column_width': 60},
    {'field': 'over_width', 'header': 'over b', 'column_width': 60},
    {'field': 'selected_begroeiingsvariant_id', 'header': 'beg', 'column_width': 40},
    {'field': 'score', 'show': True, 'column_width': 50},
    {'field': 'selected_variant_id', 'show': False, 'column_width': 100},
    {'field': 'selected_remarks', 'header': 'opm', 'show': True, 'column_width': 30, 'field_type': INDICATION_HOVER},
)


class hydrovak_class(object):
    """
    a trivial custom data object for 'hydrovakken'
    gets information from feature or own data dict (extra fields)
    """

    def __init__(self, data_dict, feature):
        """

        data_dict (dict): initial data
        feature (QgsFeature): QGis feature of hydrovak
        """
        self.feature = feature

        self.feature_keys = [field.name() for field in feature.fields()]
        self.data_dict = data_dict

        self.field_mapping = {
            'category': 'categorieoppwaterlichaam',
            'flow': 'debiet',
            'target_level': 'streefpeil',
            'hydro_id': 'id',
            'length': 'lengte',
            'depth': 'diepte',
            'width': 'breedte',
            'variant_min_depth': 'min_diepte',
            'variant_max_depth': 'max_diepte',
            'selected_depth': 'geselecteerd_diepte',
            'selected_width': 'geselecteerd_breedte',
            'selected_variant_id': 'geselecteerde_variant',
            'begroeiingsvariant_id': 'begroeiingsvariant_id',
            'selected_begroeiingsvariant_id': 'geselecteerde_begroeiingsvariant',
            'selected_remarks': 'selectie_opmerkingen',
        }

    def __repr__(self):
        return "hydrovak - %s" % (self.get('hydro_id'))

    def __getitem__(self, key, default_value=None):
        return self.get(key, default_value)

    def __setitem__(self, key, value):
        self.set(key, value)
        return self

    def update(self, update_dict):
        """ same as dict.update. set mulitple values at once"""
        for key, value in update_dict.items():
            self.set(key, value)
        return self

    def data(self, column_nr, qvalue=False):
        """get function used by QtModel"""
        if column_nr <= len(HORIZONTAL_HEADERS):
            if qvalue:
                if HORIZONTAL_HEADERS[column_nr].get('field_type') == CHECKBOX_FIELD:
                    if self.get(HORIZONTAL_HEADERS[column_nr]['field']):
                        return Qt.Checked
                    else:
                        return Qt.Unchecked
            return self.get(HORIZONTAL_HEADERS[column_nr]['field'])
        else:
            return None

    def setData(self, column, value, role=Qt.DisplayRole):
        """
        set function used by QtModel

        column (int): column number (item number in list HORIZONTAL_HEADERS)
        value (any): value to set on item
        role (int): not used QtRole (implemented to be equal to Qt implementation)

        return (bool): data changed
        """
        if HORIZONTAL_HEADERS[column].get('field_type') == CHECKBOX_FIELD:
            if type(value) == bool:
                value = value
            elif value == Qt.Checked:
                value = True
            elif value == Qt.Unchecked:
                value = False

        if value == self.get(HORIZONTAL_HEADERS[column]['field']):
            # data not changed
            return False
        else:
            self.set(HORIZONTAL_HEADERS[column]['field'], value)
            return True

    def get(self, key, default_value=None):
        if key == 'feature':
            return self.feature
        elif key == 'icon':
            if not self.data_dict.get('end_arc_type'):
                return QIcon()
            elif self.data_dict.get('end_arc_type') == 'target':
                return QIcon(':/plugins/legger/media/circle_blue.png')
            elif self.data_dict.get('end_arc_type') == 'end':
                return QIcon(':/plugins/legger/media/circle_white.png')
            else:
                return QIcon()
        elif key in self.field_mapping and self.field_mapping[key] in self.feature_keys:
            return transform_none(self.feature[self.field_mapping[key]])
        else:
            return self.data_dict.get(key, default_value)

    def set(self, key, value):
        if key == 'feature':
            self.feature = value
        elif key == 'icon':
            pass
        elif key in self.field_mapping and self.field_mapping[key] in self.feature_keys:
            self.feature[self.field_mapping[key]] = value
        else:
            self.data_dict[key] = value
        return self


class LeggerTreeItem(BaseTreeItem):
    """
    TreeItem implementation for 'legger' (each item is a 'hydrovak').
    implements the parent and child relations
    """

    def __init__(self, data_item, parent, headers=HORIZONTAL_HEADERS):
        super(LeggerTreeItem, self).__init__(
            data_item, parent, headers
        )

    @property
    def hydrovak(self):
        """access to hydrovak class object"""
        return self.data_item

    def up(self, end=None):
        """
        get list of path of hydrovakken downstream hydrovak (following the mainstream) till end hydrovak or
        till there are no downstream hydrovakken anymore

        end (LeggerTreeItem): node where to stop
        returns (list): list of TreeItems
        """

        up_list = []
        node = self
        while node != end and node is not None and node.hydrovak is not None:
            up_list.append(node)
            if node.row() != 0:
                node = node.parent().child(node.row() - 1)
            else:
                node = node.parent()

        if node is not None:
            up_list.append(node)
        return up_list

    def younger(self):
        """go from hydrovak to upstream hydrovakken"""

        nodes = []
        if self.row() < self.parent().childCount() - 1:
            nodes.append(self.parent().child(self.row() + 1))
        if self.childCount() > 0:
            nodes.append(self.childs[0])
        return nodes

    def older(self):
        """go from hydrovak to downstream hydrovak"""

        if self.row() == 0:
            return self.parent()
        else:
            return self.parent().child(self.row() - 1)


class LeggerTreeModel(BaseTreeModel):
    """
    TreeModel implementation for legger (hydrovakken). Specific function are added
    to work with the flattend tree structure (main branch stays on same level).
    """

    def __init__(self, parent=None, root_item=None,
                 item_class=LeggerTreeItem, headers=HORIZONTAL_HEADERS):

        super(LeggerTreeModel, self).__init__(
            parent, root_item, item_class, headers)

        # shortcuts to items (only one active at a time)
        self.ep = None
        self.sp = None
        self.hover = None
        self.selected = None

    def data(self, index, role):
        """
        get data of field (required QAbstractItemModel function)

        index (QIndex): Index of row and field
        role (QtRole): type of data returned (value or style attribute)
        return (could be everything): value or None of role is not supported
        """
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == Qt.DisplayRole:
            if self.headers[index.column()].get('field_type') == INDICATION_HOVER:
                if item.data(index.column()):
                    return '*'
                else:
                    return None
            elif self.headers[index.column()].get('field_type') != CHECKBOX_FIELD:
                return item.data(index.column())
        elif role == Qt.BackgroundRole:
            if item.hydrovak.get('selected'):
                return QBrush(QColor(*settings.SELECT_COLOR))
            elif item.hydrovak.get('hover'):
                return QBrush(QColor(*settings.HOVER_COLOR))
            else:
                return QBrush(Qt.transparent)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter
        elif role == Qt.CheckStateRole:
            if self.headers[index.column()].get('field_type') == CHECKBOX_FIELD:
                return item.data(index.column(), qvalue=True)
            else:
                return None
        elif role == Qt.DecorationRole and index.column() == 0:
            return item.icon()
        elif role == Qt.ToolTipRole:
            if self.headers[index.column()].get('field_type') == INDICATION_HOVER:
                return item.data(index.column())
        elif role == Qt.DecorationRole and HORIZONTAL_HEADERS[index.column()]['field'] == 'add':
            return QIcon(':/plugins/legger/media/plus.png')
        elif role == Qt.UserRole:
            if item:
                return item
        return None

    def find_younger(self, start_index, key, value):
        """
        Get all downstream nodes till field name (key) is equal to value

        start_index (QModelIndex): index of startpoint
        key (str): field name of seach value
        value (...): search value
        return (QModelIndex): index where younger item is equal to value
        """

        def search(node):
            """
            recursive function checking siblings
            index:
            return:
            """
            if node.row() < node.parent().childCount() - 1:
                young = node.parent().child(node.row() + 1)
                if young.hydrovak.get(key) == value:
                    index = self.createIndex(young.row(), 0, young)
                    return index
                result = search(young)
                if result:
                    return result

            if node.childCount() > 0:
                child = node.child(0)
                if child.hydrovak.get(key) == value:
                    index = self.createIndex(child.row(), 0, child)
                    return index
                result = search(child)
                if result:
                    return result

        start_item = start_index.internalPointer()

        result = search(start_item)
        return result

    def find_older(self, start_index, key, value):
        """
        get all upstream nodes  till field name (key) is equal to value

        start_index (QModelIndex): index of startpoint
        key (str): field name of seach value
        value (...): search value
        return (QModelIndex): index where older item is equal to value
        """

        def search(node):
            """
            recursive function checking parents
            """
            if node is None or node.hydrovak is None:
                return None

            if node.hydrovak.get(key) == value:
                index = self.createIndex(node.row(), 0, node)
                return index

            if node.row() > 0:
                result = search(node.parent().child(node.row() - 1))
            else:
                result = search(node.parent())
            if result:
                return result

        start_item = start_index.internalPointer()
        result = search(start_item)
        return result

    def get_open_endleaf(self, tree_widget=None):
        """
        get endpoint following all 'open' branches

        tree_widget (QTreeWidget): tree widget to be searched. Overwrites the widget set with the function .setTreeWidget
        return (ModelItem): Model item
        """
        if tree_widget is None:
            tree_widget = self.tree_widget

        def loop(node):
            index = self.createIndex(node.row(), 0, node)
            if tree_widget and tree_widget.isExpanded(index):  # node.childCount() > 0 and :
                result = loop(node.child(0))
            elif node.parent().childCount() - 1 == node.row():
                return node
            else:
                result = loop(node.parent().child(node.row() + 1))

            if result:
                return result

        result = loop(self.rootItem.child(0))
        return result

    def data_change_post_process(self, index, to_index):
        """
        stores direct links to hovered and selected rows and to
        start and endpoint of selected traject

        index (QModelIndex): start index (row)
        to_index (QModelIndex): end index (row) - not supported
        return: None
        """
        col = self.column(index.column())

        if col['field'] == 'hover':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                self.hover = index.internalPointer()
            elif index.internalPointer() == self.hover:
                self.hover = None

            # update color background of all cells in row
            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))

        elif col['field'] == 'selected':
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                self.selected = index.internalPointer()
                self.tree_widget.update(index)

            elif index.internalPointer() == self.selected:
                self.selected = None

            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))

        elif col['field'] == 'sp':
            # if no endpoint selected, also select endpoint
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                index_ep = self.find_younger(start_index=index, key='ep', value=True)
                if index_ep is None:
                    leaf_endpoint = self.get_open_endleaf()
                    self.setDataItemKey(
                        leaf_endpoint, 'ep', True, role=Qt.CheckStateRole)
                else:
                    self.ep = index_ep.internalPointer()
                    self.sp = index.internalPointer()
            else:
                self.ep = None

        elif col['field'] == 'ep':
            # if no startpoint selected, also select startpoint
            value = self.data(index, role=Qt.CheckStateRole)
            if value:
                index_sp = self.find_older(start_index=index, key='sp', value=True)
                if index_sp is None:
                    self.setDataItemKey(
                        self.rootItem.child(0), 'sp', True, role=Qt.CheckStateRole)
                else:
                    self.ep = index.internalPointer()
                    self.sp = index_sp.internalPointer()
            else:
                self.ep = None
