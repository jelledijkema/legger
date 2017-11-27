import logging

from sqlalchemy import (
    Boolean, Column, Integer, String, Float, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2.types import Geometry

logger = logging.getLogger('legger.sql_models.legger')

Base = declarative_base()


class waterdeel(Base):
    __tablename__ = 'waterdeel'
    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer, index=True)

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class PeilgebiedPraktijk(Base):
    __tablename__ = 'peilgebiedpraktijk'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer)
    code = Column(String(), index=True)
    naam = Column(String())
    geometry = Column("GEOMETRY", Geometry())

    hydro_objects = relationship("HydroObject",
                                 # foreign_keys='code',
                                 back_populates="peilgebied")

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class HydroObject(Base):
    __tablename__ = 'hydroobject'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer, index=True)
    code = Column(String(), index=True)
    categorieoppwaterlichaam = Column(String())
    ws_in_peilgebied = Column(String(),
                              ForeignKey(PeilgebiedPraktijk.__tablename__ + ".code"))

    geometry = Column("GEOMETRY", Geometry())
    peilgebied = relationship(PeilgebiedPraktijk,
                              # foreign_keys='ws_in_peilgebied',
                              back_populates="hydro_objects")

    tdi_result = relationship("TdiResults",
                              uselist=False,
                              back_populates="hydroobject")

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class TdiResults(Base):
    __tablename__ = 'tdi_results'

    hydroobject_id = Column(Integer,
                            ForeignKey(HydroObject.__tablename__ + ".objectid"),
                            primary_key=True)
    qend = Column(Float)
    channel_id = Column(Integer)
    flowline_id = Column(Integer)
    nr_candidates = Column(Integer)
    score = Column(Float)

    hydroobject = relationship(HydroObject,
                               back_populates="tdi_result")

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class Streefpeil(Base):
    __tablename__ = 'streefpeil'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer)
    soortstreefpeil = Column(Integer)
    waterhoogte = Column(Float)
    peilgebiedpraktijkid = Column(Integer)
    peilafwijkinggebiedid = Column(Integer)

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class MaxBreedte(Base):
    __tablename__ = 'max_breedte'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer)
    code = Column(String())
    width = Column(String())  # todo: float?

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class Talud(Base):
    __tablename__ = 'talud'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    code = Column(String())
    initieel_talud = Column(Integer)  # todo: float?
    steilste_talud = Column(Integer)  # todo: float?

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)
