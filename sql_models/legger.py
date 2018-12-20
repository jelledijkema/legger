import datetime
import logging

from geoalchemy2.types import Geometry
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Integer, String)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

logger = logging.getLogger('legger.sql_models.legger')

Base = declarative_base()


class Waterdeel(Base):
    __tablename__ = 'waterdeel'
    extend_existing = True

    objectid = Column(Integer)
    id = Column(Integer, primary_key=True)
    shape_length = Column(Float)
    shape_area = Column(Float)
    geometry = Column("GEOMETRY", Geometry(geometry_type='MULTIPOLYGON', srid=28992))

    def __str__(self):
        return u'Waterdeel {0}'.format(
            self.id)


class HydroObject(Base):
    __tablename__ = 'hydroobject'
    extend_existing = True

    objectid = Column(Integer)
    id = Column(Integer, primary_key=True)
    geometry = Column("GEOMETRY", Geometry(geometry_type='MULTILINESTRING', srid=28992))
    code = Column(String(50), index=True)
    categorieoppwaterlichaam = Column(Integer)
    streefpeil = Column(Float)
    debiet = Column(Float)
    channel_id = Column(Integer)  # link to 3di id
    flowline_id = Column(Integer)  # link to 3di id
    # shape_length = Column(Float)

    varianten = relationship("Varianten",
                             uselist=True,
                             lazy='dynamic',
                             back_populates="hydro")

    profielen = relationship("Profielen",
                             back_populates="hydro")

    kenmerken = relationship("Kenmerken",
                             back_populates="hydro")

    geselecteerd = relationship("GeselecteerdeProfielen",
                                uselist=False,
                                back_populates="hydro")

    figuren = relationship("ProfielFiguren",
                           primaryjoin="HydroObject.id == ProfielFiguren.hydro_id",
                           lazy='dynamic',
                           # foreign_keys=[id],
                           back_populates="hydro")

    def __str__(self):
        return u'Hydro object {0}'.format(
            self.code)


class Profielen(Base):
    __tablename__ = 'profielen'

    objectid = Column(Integer)
    id = Column(Integer, primary_key=True)  # varchar??
    proident = Column(String(24))
    bron_profiel = Column(String(50))
    pro_id = Column(Integer, index=True)
    hydro_id = Column(Integer,
                      ForeignKey(HydroObject.__tablename__ + ".id"))
    # shape_lengte = Column(Float)
    hydro = relationship(HydroObject,
                         back_populates="profielen")

    profielpunten = relationship(
        "Profielpunten",
        back_populates="profiel")

    def __str__(self):
        return u'profiel {0} - {1}'.format(
            self.id, self.proident)


class Profielpunten(Base):
    __tablename__ = 'profielpunten'

    objectid = Column(Integer, primary_key=True)
    pbp_id = Column(Integer)
    prw_id = Column(Integer)
    pbpident = Column(String(24))
    osmomsch = Column(String(60))
    iws_volgnr = Column(Integer)
    iws_hoogte = Column(Float)
    afstand = Column(Float)
    pro_pro_id = Column(Integer,
                        ForeignKey(Profielen.__tablename__ + '.pro_id'))
    geometry = Column("GEOMETRY", Geometry(geometry_type='POINT', srid=28992))

    profiel = relationship(
        "Profielen",
        back_populates="profielpunten")

    def __str__(self):
        return u'profielpunt {0}'.format(
            self.pbpident)


class Kenmerken(Base):
    __tablename__ = 'kenmerken'

    objectid = Column(Integer)
    id = Column(Integer, primary_key=True)
    diepte = Column(Float)
    bron_diepte = Column(String(50))
    bodemhoogte = Column(Float)
    breedte = Column(Float)
    bron_breedte = Column(String(50))
    lengte = Column(Float)
    taludvoorkeur = Column(Float)
    steilste_talud = Column(Float)
    grondsoort = Column(String(50))
    bron_grondsoort = Column(String(50))
    hydro_id = Column(Integer,
                      ForeignKey(HydroObject.__tablename__ + ".objectid"))

    hydro = relationship(HydroObject,
                         # foreign_keys='ws_in_peilgebied',
                         back_populates="kenmerken")

    def __str__(self):
        return u'kenmerken {0}'.format(
            self.id)


class Varianten(Base):
    __tablename__ = 'varianten'

    id = Column(String(), primary_key=True)
    diepte = Column(Float)
    waterbreedte = Column(Float)
    bodembreedte = Column(Float)
    talud = Column(Float)
    # maatgevend_debiet = Column(Float)
    verhang_bos_bijkerk = Column(Float)
    opmerkingen = Column(String())
    hydro_id = Column(Integer,
                      ForeignKey(HydroObject.__tablename__ + ".id"))

    hydro = relationship(HydroObject,
                         # foreign_keys='ws_in_peilgebied',
                         uselist=False,
                         back_populates="varianten")

    # geselecteerd = relationship("GeselecteerdeProfielen",
    #                        back_populates="variant")

    def __str__(self):
        return u'profiel_variant {0}'.format(
            self.id)


class GeselecteerdeProfielen(Base):
    __tablename__ = 'geselecteerd'

    hydro_id = Column(Integer,
                      ForeignKey(HydroObject.__tablename__ + ".id"),
                      primary_key=True)
    variant_id = Column(String(),
                        ForeignKey(Varianten.__tablename__ + ".id"))
    selected_on = Column(DateTime, default=datetime.datetime.utcnow)

    hydro = relationship(HydroObject,
                         back_populates="geselecteerd")

    variant = relationship(Varianten)
    # back_populates="geselecteerd")


class ProfielFiguren(Base):
    __tablename__ = 'profielfiguren'

    # object_id = Column(Integer, primary_key=True)
    hydro_id = Column('id_hydro', Integer,
                      ForeignKey(HydroObject.__tablename__ + ".id"))
    profid = Column(String(16), primary_key=True)
    type_prof = Column(String(1))
    coord = Column(String())
    peil = Column(Float)
    t_talud = Column(Float)
    t_waterdiepte = Column(Float)
    t_bodembreedte = Column(Float)
    t_fit = Column(Float)
    t_afst = Column(Float)
    g_rest = Column(Float)
    t_overdiepte = Column(Float)
    t_overbreedte_l = Column(Float)
    t_overbreedte_r = Column(Float)

    hydro = relationship(HydroObject,
                         primaryjoin="HydroObject.id == ProfielFiguren.hydro_id",
                         # foreign_keys=[hydro_id],
                         back_populates="figuren")

    def __str__(self):
        return u'profiel_figuren {0} - {1}'.format(
            self.hydro_id, self.profid)


class DuikerSifonHevel(Base):
    __tablename__ = 'duikersifonhevel'
    extend_existing = True

    objectid = Column(Integer)
    id = Column(Integer, primary_key=True)
    geometry = Column("GEOMETRY", Geometry(geometry_type='MULTILINESTRING', srid=28992))
    code = Column(String(50), index=True)
    categorie = Column(Integer)
    lengte = Column(Float)
    hoogteopening = Column(Float)
    breedteopening = Column(Float)
    hoogtebinnenonderkantbene = Column(Float)
    hoogtebinnenonderkantbov = Column(Float)
    vormkoker = Column(Float)
    # shape_lengte = Column(Float)

    debiet = Column(Float)  # extra?
    channel_id = Column(Integer)  # extra?
    flowline_id = Column(Integer)  # extra?

    def __str__(self):
        return u'DuikerSifonHevel {0}'.format(
            self.code)
