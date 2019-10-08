from PyQt4.QtCore import QSize, Qt
from ThreeDiToolbox.models.base import BaseModel, CHECKBOX_FIELD, COLOR_FIELD, VALUE_FIELD
from ThreeDiToolbox.models.base_fields import ColorField as OrigColorField, ValueField as OrigValueField, CheckboxField as OrigCheckboxField


class ValueField(OrigValueField):
    """Field implementation for Values, which (for now) can be everything
    which can be showed in plain text (string, int, float)"""

    def __init__(self, round=None, column_tooltip=None, color_from=None, *args, **kwargs):
        super(ValueField, self).__init__(*args, **kwargs)
        self.round = round
        self.column_tooltip = column_tooltip
        self.color_from = color_from
        self.field_type = VALUE_FIELD


class ColorField(OrigColorField):

    def __init__(self, column_tooltip=None, color_from=None, *args, **kwargs):
        super(ColorField, self).__init__(*args, **kwargs)
        self.column_tooltip = column_tooltip
        self.color_from = color_from
        self.field_type = COLOR_FIELD


class CheckboxField(OrigCheckboxField):

    def __init__(self, column_tooltip=None, color_from=None, **kwargs):
        super(CheckboxField, self).__init__(**kwargs)
        self.column_tooltip = column_tooltip
        self.color_from = color_from
        self.field_type = CHECKBOX_FIELD


class ModifiedBaseModel(BaseModel):

    def data(self, index, role=Qt.DisplayRole):
        """Qt function to get data from items for the visible columns"""

        if not index.isValid():
            return None

        item = self.rows[index.row()]

        if role == Qt.DisplayRole:
            col = item[index.column()]
            if col.field_type == VALUE_FIELD:
                if self.columns[index.column()].round is not None and col.value is not None:
                    return round(float(col.value), col.round)
                else:
                    return col.value
        elif role == Qt.BackgroundRole:
            field = item[index.column()]
            if field.field_type == COLOR_FIELD:
                return field.qvalue
            elif field.color_from is not None:
                return getattr(item, field.color_from).qvalue
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter
        elif role == Qt.CheckStateRole:
            if item[index.column()].field_type == CHECKBOX_FIELD:
                return item[index.column()].qvalue
            else:
                return None
        # elif role == Qt.ToolTipRole:
        #     return 'tooltip'

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
                return self.columns[col_nr].column_name
            elif role == Qt.ToolTipRole:
                return self.columns[col_nr].column_tooltip
        else:
            # give grey balk at start of row a small dimension to select row
            if Qt.SizeHintRole:
                return QSize(10, 0)
