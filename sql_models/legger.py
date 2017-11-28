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
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    objectid = Column(Integer, index=True)
    geometry = Column("GEOMETRY", Geometry(geometry_type='POLYGON', srid=28992))

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class PeilgebiedPraktijk(Base):
    __tablename__ = 'peilgebiedpraktijk'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    geometry = Column("GEOMETRY", Geometry(geometry_type='POLYGON', srid=28992))
    objectid = Column(Integer)
    code = Column(String(), index=True)
    naam = Column(String())

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
    geometry = Column("GEOMETRY", Geometry(geometry_type='LINESTRING', srid=28992))
    objectid = Column(Integer, index=True)
    code = Column(String(), index=True)
    categorieoppwaterlichaam = Column(String())
    ws_in_peilgebied = Column(String(),
                              ForeignKey(PeilgebiedPraktijk.__tablename__ + ".code"))

    peilgebied = relationship(PeilgebiedPraktijk,
                              # foreign_keys='ws_in_peilgebied',
                              back_populates="hydro_objects")

    tdi_result = relationship("TdiHydroObjectResults",
                              uselist=False,
                              back_populates="hydroobject")

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class TdiHydroObjectResults(Base):
    __tablename__ = 'tdi_hydro_object_results'

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
        return u'Hydro object 3di result {0}'.format(
            self.hydrobject)


class DuikerSifonHevel(Base):
    __tablename__ = 'duikersifonhevel'
    extend_existing = True

    ogc_fid = Column("OGC_FID", Integer, primary_key=True)
    geometry = Column("GEOMETRY", Geometry(geometry_type='LINESTRING', srid=28992))
    objectid = Column(Integer, index=True)
    code = Column(String(), index=True)
    categorie = Column(Integer)
    lengte = Column(Float)
    hoogteopening = Column(Float)
    breedteopening = Column(Float)
    hoogtebinnenonderkantbov = Column(Float)
    vormkoker = Column(Float)

    tdi_culvert_result = relationship("TdiCulvertResults",
                                      uselist=False,
                                      back_populates="duiker_sifon_hevel")

    def __str__(self):
        return u'DuikerSifonHevel {0}'.format(
            self.code)


class TdiCulvertResults(Base):
    __tablename__ = 'tdi_culvert_results'

    id = Column(Integer,
                primary_key=True)
    code = Column(String(),
                  ForeignKey(DuikerSifonHevel.__tablename__ + ".code"))
    source = Column(String())
    qend = Column(Float)

    duiker_sifon_hevel = relationship(DuikerSifonHevel,
                                      back_populates="tdi_culvert_result")

    def __str__(self):
        return u'Culvert 3di result {0}'.format(
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

# todo: add prw, pro, pbp, profielpunten
