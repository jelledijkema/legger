# from qgis.utils import plugins
#
# try:
#     tdi_plugin = plugins['ThreeDiToolbox']
#
#
# except:
#     raise ImportError("For ThreeDiStatistics tool the ThreeDiToolbox plugin must be installed, "
#                       "version xxx or higher")
#
# ts_datasource = tdi_plugin.ts_datasource
#
# db_path_result_sqlite = ts_datasource.rows[0].spatialite_cache_filepath().replace('\\', '/')
# db_path_model_sqlite = ts_datasource.model_spatialite_filepath
# result_ds = ts_datasource.rows[0].datasource()
