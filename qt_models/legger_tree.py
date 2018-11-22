from PyQt4 import QtCore

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBrush, QColor, QIcon
from legger import settings
from tree import BaseTreeItem, BaseTreeModel, CHECKBOX_FIELD

HORIZONTAL_HEADERS = (
    {'field': 'hydro_id', 'column_width': 150},
    # {'field': 'feat_id', 'column_width': 25},
    {'field': 'sp', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
    {'field': 'ep', 'field_type': CHECKBOX_FIELD, 'column_width': 25, 'single_selection': True},
    {'field': 'selected', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50,
     'single_selection': True},
    {'field': 'hover', 'field_type': CHECKBOX_FIELD, 'show': False, 'column_width': 50},
    {'field': 'distance', 'header': 'afstand', 'show': False, 'column_width': 50},
    {'field': 'flow', 'header': 'debiet', 'column_width': 50},
    {'field': 'target_level', 'show': False, 'column_width': 50},
    {'field': 'depth', 'header': 'diepte', 'column_width': 50},
    {'field': 'width', 'header': 'breedte', 'column_width': 50},
    {'field': 'variant_min', 'show': False, 'column_width': 60},
    {'field': 'variant_max', 'show': False, 'column_width': 60},
    {'field': 'selected_depth', 'header': 'prof d', 'column_width': 60},
    {'field': 'selected_depth_tmp', 'header': 'sel', 'column_width': 50},
    {'field': 'selected_width', 'header': 'prof b', 'column_width': 60},
    {'field': 'over_depth', 'header': 'over d', 'column_width': 60},
    {'field': 'over_width', 'header': 'over b', 'column_width': 60},
    {'field': 'score', 'column_width': 50},
)


class hydrovak_class(object):
    """
    a trivial custom data object
    """

    def __init__(self, data_dict, feature, startpoint_feature=None, endpoint_feature=None):
        """

        data_dict (dict):
        """
        self.feature = feature
        self.startpoint_feature = startpoint_feature
        self.endpoint_feature = endpoint_feature

        self.feature_keys = {}
        self.data_dict = data_dict

    def __repr__(self):
        return "hydrovak - %s" % (self.get('hydro_id'))

    def data(self, column_nr, qvalue=False):
        # required
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

    def setData(self, column, value, role):
        if HORIZONTAL_HEADERS[column].get('field_type') == CHECKBOX_FIELD:
            if type(value) == bool:
                value = value
            elif value == Qt.Checked:
                value = True
            elif value == Qt.Unchecked:
                value = False

        if value == self.get(HORIZONTAL_HEADERS[column]['field']):
            return False
        else:
            return self.set(HORIZONTAL_HEADERS[column]['field'], value)

    def get(self, key, default_value=None):
        if key == 'feature':
            return self.feature
        elif key == 'startpoint':
            return self.startpoint_feature
        elif key == 'endpoint':
            return self.endpoint_feature
        elif key == 'icon':
            if not self.endpoint_feature:
                return QIcon()
            elif self.endpoint_feature.attributes()[2] == 'target':
                return QIcon(':/plugins/legger/media/circle_blue.png')
            elif self.endpoint_feature.attributes()[2] == 'end':
                return QIcon(':/plugins/legger/media/circle_white.png')
            else:
                return QIcon()
        elif key in self.feature_keys:
            return self.feature[key]
        else:
            return self.data_dict.get(key, default_value)

    def set(self, key, value):

        # if key in self.feature_keys:
        #     return False  # not implemented yet
        # else:
        self.data_dict[key] = value
        return True


class LeggerTreeItem(BaseTreeItem):
    """
    TreeItem implementation for 'legger' (each item is a 'hydrovak')
    """

    def __init__(self, data_item, parent, headers=HORIZONTAL_HEADERS):
        super(LeggerTreeItem, self).__init__(
            data_item, parent, headers
        )

    @property
    def hydrovak(self):
        return self.data_item

    def up(self, end=None):
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
        nodes = []
        if self.row() < self.parent().childCount() - 1:
            nodes.append(self.parent().child(self.row() + 1))
        if self.childCount() > 0:
            nodes.append(self.childs[0])
        return nodes

    def older(self):
        if self.row() == 0:
            return self.parent()
        else:
            return self.parent().child(self.row() - 1)


class LeggerTreeModel(BaseTreeModel):
    """
    TreeModel implementation for legger (hydrovakken). Specific function are added
    to work with the flattend tree structure (main branch stays on same level.
    """

    def __init__(self, parent=None, root_item=None,
                 item_class=LeggerTreeItem, headers=HORIZONTAL_HEADERS):

        super(LeggerTreeModel, self).__init__(
            parent, root_item, item_class, headers)

        # shortcuts to items (only one active at a time
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
        if role == QtCore.Qt.DisplayRole:
            if self.headers[index.column()].get('field_type') != CHECKBOX_FIELD:
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
        elif role == QtCore.Qt.DecorationRole and index.column() == 0:
            return item.icon()
        elif role == QtCore.Qt.DecorationRole and HORIZONTAL_HEADERS[index.column()]['field'] == 'add':
            return QIcon(':/plugins/legger/media/plus.png')
        elif role == QtCore.Qt.UserRole:
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
            :param index:
            :return:
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
