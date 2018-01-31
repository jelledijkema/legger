import os
import inspect

from PyQt4.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt4.QtCore import Qt, QSize


class LeggerTreeModel(QStandardItemModel):

    def __init__(self, parent=None):
        super(LeggerTreeModel, self).__init__(parent)

        self.columns = [
            {'name': 'tak', 'field': 'name'},
            {'name': 'diepte', 'field': 'depth'},
            {'name': 'breedte', 'field': 'width'},
        ]

        self.add_items(self, [{
            'name': 'root',
            'width': 10,
            'depth': 2,
            'children': [
                {'name': 'b1'},
                {'name': 'b2'},
                {'name': 'b3'},
            ]
        }, {
            'name': 'root2',
            'width': 5,
            'depth': 1.2,
            'children': []
        }])

        self.setColumnCount(3)

    def add_items(self, parent, elements):
        icon = QIcon(':/plugins/legger/media/icon_legger.png')

        for row in elements:
            item = []
            for col in self.columns:
                value = row.get(col['field'], '')
                item.append(QStandardItem(str(value)))
            item[0].setIcon(icon)

            parent.appendRow(item)

            if 'children' in row:
                self.add_items(item[0], row['children'])

    def headerData(
            self, col_nr, orientation=Qt.Horizontal, role=Qt.DisplayRole):
        """
        required Qt function for getting column information
        :param col_nr: column number
        :param orientation: Qt orientation of header Qt.Horizontal or
                            Qt.Vertical
        :param role: Qt Role (DisplayRole, SizeHintRole, etc)
        :return: value of column, given the role
        """
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if col_nr < len(self.columns):
                    return self.columns[col_nr]['name']
                else:
                    pass
        else:
            # give grey balk at start of row a small dimension to select row
            if Qt.SizeHintRole:
                return QSize(10, 0)
