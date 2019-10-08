try:
    from qgis.utils import iface
except Exception:
    iface = None


def messagebar_message(title, msg, level=None, duration=0, prevent_duplicates=True):
    """ Show message in the message bar (just above the map)
    args:
        title: (str) title of messages, showed bold in the start of the message
        msg: (str) message
        level: (int) INFO = 0, WARNING = 1, CRITICAL = 2, SUCCESS = 3. It is
            possible to use QgsMessage.INFO, etc
        duration: (int) how long this the message displays in seconds
    """
    try:
        from qgis.gui import QgsMessageBar
        if not level:
            level = QgsMessageBar.INFO
    except ImportError:
        print("%s: %s" % (title, msg))

    if iface is not None:
        if (prevent_duplicates and
                iface.messageBar().currentItem() is not None and
                hasattr(iface.messageBar().currentItem(), 'title') and
                iface.messageBar().currentItem().title() == title):
            return

        iface.messageBar().pushMessage(title, msg, level, duration)
