


def python_value(value, default_value=None, func=None):
    """
    help function for translating QVariant Null values into None
    value: QVariant value or python value
    default_value: value in case provided value is None
    func (function): function for transforming value
    :return: python value
    """

    # check on QVariantNull... type
    if hasattr(value, 'isNull') and value.isNull():
        return default_value
    else:
        if default_value is not None and value is None:
            return default_value
        else:
            if func is not None:
                return func(value)
            else:
                return value