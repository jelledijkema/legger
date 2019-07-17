

try:
    import pydevd
except ImportError:
    import sys
    sys.path.append('C:\\Program Files\\JetBrains\\PyCharm 2019.1.3\\debug-eggs\\pydevd-pycharm.egg')
    import pydevd


pydevd.settrace('localhost',
                port=3106,
                stdoutToServer=True,
                stderrToServer=True,
                suspend=False,
                trace_only_current_thread=True)