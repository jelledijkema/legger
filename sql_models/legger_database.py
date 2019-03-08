import copy
import logging
import os

from osgeo import ogr
from ThreeDiToolbox.utils.threedi_database import (ThreediDatabase)

from .legger import Base

log = logging.getLogger(__name__)


class LeggerDatabase(ThreediDatabase):
    """Wrapper around sqlalchemy interface with functions to create, update
        databases and get connections.
        This class is equal to ThreeDiDatabase, except fix_views
        Two functions create_db and get_metadata added because of link to Base
        (code is beside link to different 'Base;  equal to ThreediDatabase)
    """

    def create_db(self, overwrite=False):
        if self.db_type == 'spatialite':

            if overwrite and os.path.isfile(self.settings['db_file']):
                os.remove(self.settings['db_file'])

            drv = ogr.GetDriverByName('SQLite')
            db = drv.CreateDataSource(self.settings['db_file'],
                                      ["SPATIALITE=YES"])
            Base.metadata.create_all(self.engine)

    def get_metadata(self, including_existing_tables=False, engine=None):

        if including_existing_tables:
            metadata = copy.deepcopy(Base.metadata)
            if engine is None:
                engine = self.engine

            metadata.bind = engine
            metadata.reflect(extend_existing=True)
            return metadata
        else:
            if self._base_metadata is None:
                self._base_metadata = copy.deepcopy(Base.metadata)
            return self._base_metadata

    def fix_views(self):
        """function overwrite, function is not relevant"""
        raise NotImplementedError('fix views not relevant in this context')
