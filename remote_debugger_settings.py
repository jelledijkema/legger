

try:
    import pydevd
except ImportError:
    import sys

    sys.path.append('C:\\Program Files\\JetBrains\\PyCharm 2020.3.3\\debug-eggs\\pydevd-pycharm.egg')
    import pydevd_pycharm


pydevd_pycharm.settrace('localhost',
                        port=5555,
                        stdoutToServer=True,
                        stderrToServer=True,
                        suspend=False) #, trace_only_current_thread=True
