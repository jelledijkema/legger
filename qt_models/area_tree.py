from PyQt4 import QtCore

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QBrush, QColor, QIcon
from legger import settings
from tree import BaseTreeItem, BaseTreeModel, CHECKBOX_FIELD

HORIZONTAL_HEADERS = (
    {'field': 'target_level', 'header': 'streefpeil', 'column_width': 300},
    {'field': 'selected', 'show': False, 'field_type': CHECKBOX_FIELD, 'column_width': 50,
     'single_selection': True},
    {'field': 'hover', 'show': False, 'field_type': CHECKBOX_FIELD, 'column_width': 50},
    {'field': 'weight', 'header': 'omvang', 'column_width': 50},
    {'field': 'distance', 'header': 'afstand', 'column_width': 50},
)


class area_class(object):
    """
    a trivial custom data object
    """

    def __init__(self, data_dict):
        """

        data_dict (dict):
        """

        self.data_dict = data_dict

    def __repr__(self):
        return "area - %.2f" % (self.get('target_level'))

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
        if key == 'icon':
            return QIcon()
        else:
            return self.data_dict.get(key, default_value)

    def set(self, key, value):

        self.data_dict[key] = value
        return True


class AreaTreeItem(BaseTreeItem):
    """
    TreeItem implementation for areas ('peilvakken')
    """

    def __init__(self, data_item, parent, headers=HORIZONTAL_HEADERS):
        super(AreaTreeItem, self).__init__(
            data_item, parent, headers
        )

    @property
    def area(self):
        return self.data_item


class AreaTreeModel(BaseTreeModel):
    """
    a model to display a the 'hydrovakken'. Tree is flattend (with main branch on same level) to prevent
    to many levels. Including functions for getting upstream and downstream.

    Fields (Columns) are defined in HORIZONTAL_HEADERS on top of this script

    """

    def __init__(self, parent=None, root_item=None,
                 item_class=AreaTreeItem, headers=HORIZONTAL_HEADERS):

        super(AreaTreeModel, self).__init__(
            parent, root_item, item_class, headers)

        # shortcuts to items (only one active at a time
        self.ep = None
        self.sp = None
        self.hover = None

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
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter
        elif role == Qt.CheckStateRole:
            if self.headers[index.column()].get('field_type') == CHECKBOX_FIELD:
                return item.data(index.column(), qvalue=True)
            else:
                return None
        elif role == Qt.BackgroundRole:
            if item.area.get('selected'):
                return QBrush(QColor(*settings.SELECT_COLOR))
            elif item.area.get('hover'):
                return QBrush(QColor(*settings.HOVER_COLOR))
            else:
                return QBrush(Qt.transparent)
        elif role == QtCore.Qt.DecorationRole and index.column() == 0:
            return item.icon()
        elif role == QtCore.Qt.UserRole:
            if item:
                return item
        return None

    def data_change_post_process(self, index, to_index):
        """
        stores direct links to hovered and selected rows

        index (QModelIndex):
        to_index (QModelIndex):
        return: None
        """

        col = self.column(index.column())

        if col['field'] == 'hover':
            value = self.data(index, Qt.CheckStateRole)
            if value:
                self.hover = index.internalPointer()

            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))

        elif col['field'] == 'selected':
            value = self.data(index, Qt.CheckStateRole)
            if value:
                self.selected = index.internalPointer()

            for colnr in range(0, len(HORIZONTAL_HEADERS)):
                self.tree_widget.update(self.index(index.row(), colnr, index.parent()))
