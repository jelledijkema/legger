#   profile_match.py
#   onderdeel van leggertool
#   plaatst theoretische profielen zo goed mogelijk binnen gemeten profielen

from pyspatialite import dbapi2 as sql
import math
import shapely
import shapely.geometry
import time
import future_builtins
import logging


logger = logging.getLogger('legger.utils.profile_match')


def mk_pro_x_hy_kompas(cur, straal=0.5, aantalstappen=90, srid=28992):
    """ Voor alle gemeten profielen wordt het snijpunt met het bijbehorende hydroobject gemaakt en het azimut
    (kompasrichting) van het hydroobject ter plekke.
    Invoer: cur =  een cursor naar de database met gemetenprofielen, hydroobjecten en theoretische profielen
            straal = de straal van een semi-cirkel met als middelpunt het snijpunt van gemetenprofiel en hydroobject
            aantalstappen = het aantal lijnstukken van de semi-cirkel
            srid = het nummer van het geografische referentiestelsel; 28992 =  Rijksdriehoekmeting
    Uitvoer: gevulde tabel pro_x_hy_kompas in de database

    Op de loodlijn op het lijnstuk van het hydroobject ter plekke van het snijpunt, worden later het gemeten
    profiel en de theoretische profielen geprojecteerd.
    Het snijpunt met de kompasrichting wordt opgeslagen in tabel pro_x_hy_kompas in de database.

    Het snijpunt wordt bepaald met de spatialite functie Intersection(profiellijn,hydroobject)
    De kommpasrichting wordt bepaald met de spatialite functie Azimuth(punt1,punt2)
    punt1 en punt2 worden bepaald door Intersection(profiellijn, cirkeltje_om_snijpunt)
    cirkeltje_om_snijpunt wordt gemaakt door Buffer(snijpunt, straal, aantalstappen)
    straal is een variabele evenals aantal stappen"""

    cur.execute('drop table if exists pro_x_hy_kompas')
    cur.execute('create table pro_x_hy_kompas (pro_id bigint primary key, ovk_ovk_id bigint, kompas float,'
                'CONSTRAINT fk_pro  FOREIGN KEY (pro_id) REFERENCES pro(pro_id), '
                'CONSTRAINT fk_hy  FOREIGN KEY (ovk_ovk_id) REFERENCES hydroobject(objectid)) ')
    cur.execute('select DiscardGeometryColumn("pro_x_hy_kompas","geometry")')
    cur.execute('select AddGeometryColumn("pro_x_hy_kompas", "geometry", %d, "POINT")' % srid)
    cur.execute('insert into pro_x_hy_kompas (pro_id, ovk_ovk_id, geometry, kompas)'
                ' select pro_id, ovk_ovk_id, Intersection(pro.GEOMETRY, hydroobject.GEOMETRY),'
                'Azimuth('
                'PointN(Intersection(pro.GEOMETRY,Buffer(Intersection(pro.GEOMETRY, hydroobject.GEOMETRY),%f,%d)),1), '
                'PointN(Intersection(pro.GEOMETRY,Buffer(Intersection(pro.GEOMETRY, hydroobject.GEOMETRY),%f,%d)),2)) '
                'from pro inner join hydroobject on '
                '(pro.ovk_ovk_id=hydroobject.objectid)' % (straal, aantalstappen, straal, aantalstappen))
    return


def peilperprofiel(cur):
    """ Haal per gemeten profiel het heersende peil op.
    Invoer: cur =  een cursor naar de database met gemetenprofielen, hydroobjecten en theoretische profielen
    Uitvoer: een dictionary met als sleutel het id van het profiel en als waarde het peil

    In versie 0 wordt domweg op grond van de administratieve joins de waterhoogte uit de tabel streefpeilen gebruikt
    Dit kan later zo nodig verfijnt worden met een spatial join
    In het testgebied Geestmerambacht levert de gebruikte query 43 null waarden op voor waterhoogte
       steekproeven geven aan dat dit vooral komt doordat profielen geselecteerd zijn met een buffer
       rond het gebied      """
    q = '''select pro.pro_id, pro.ovk_ovk_id, streefpeil.waterhoogte from 
            pro left outer join hydroobject on (pro.ovk_ovk_id = hydroobject.objectid) 
            left outer join peilgebiedpraktijk on (hydroobject.ws_in_peilgebied = peilgebiedpraktijk.code) 
            left outer join streefpeil on (peilgebiedpraktijk.objectid=streefpeil.peilgebiedpraktijkid)
        '''
    prof = {}

    for r in cur.execute(q):
        prof[r[0]] = (r[1], r[2])
    return prof


def haal_meetprofielen(cur, profielsoort="Z1"):
    """ Haal de gemeten profieelpunten op uit de database voor de profielsoort vastebodem
     Bepaal de punten die meedoen op grond van het peil dat bij het hydroobject waar de
     reeks punten bijhoort
     Invoer:    cur = een cursor naar de database met gemetenprofielen, hydroobjecten en theoretische profielen
                profielsoort = de code voor de harde bodem
     Uitvoer:   een dictionary met
     Aanpak:
     a) haal voor alle gemetenprofielen de peilen op en werk door met de profielen die een peil hebben
     b) haal per profiel de punten op volgorde van iws_volgnummer op
     c) doorloop de punten, zodra een punt onder het peil komt: bepaal snijpunt van de
                """
    prof = {}
    peilvanprofiel = peilperprofiel(cur)
    q = '''select "c"."pro_pro_id", "b"."iws_volgnr", X("a"."GEOMETRY"), Y("a"."GEOMETRY"),
             "b"."iws_hoogte"
            from "profielpunten" as "a" 
             join "pbp" as "b" on ("a"."OGC_FID" = "b"."OGC_FID")
             join "prw" as "c" on ("b"."OGC_FID" = "c"."OGC_FID")
            where "c"."pro_pro_id" = %d and "c"."osmomsch" = "%s"
            order by "b"."iws_volgnr" 
                '''
    for proid in peilvanprofiel:
        if peilvanprofiel[proid][1] is not None:
            print peilvanprofiel[proid], proid
            prof[proid] = {}
            prof[proid]['hydroid'] = peilvanprofiel[proid][0]
            prof[proid]['peil'] = peilvanprofiel[proid][1]
            s = 0
            for r in cur.execute(q % (proid, profielsoort)):
                if s == 0:  # beginconditie
                    links = r
                    s = 1
                    if links[4] <= peilvanprofiel[proid][1]:
                        omlaag = 0  # profiel start onder peil, omhoog zoeken
                        meedoen = 1  # volgende punten lager dan peil doen mee met profiel
                        prof[proid]['orig'] = [[r[2], r[3], peilvanprofiel[proid][1]]]  # eerste punt van profiel
                    else:
                        omlaag = 1   # eerste punt boven peil, omlaag zoeken
                        meedoen = 0  # punten boven peil doen niet mee
                else:   # alle volgende punten
                    rechts = r
                    if meedoen:  # er is al een punt lager dan peil gevonden dus omhoog kijken
                        if not omlaag:  # en alleen als we omhoog kijken
                            if rechts[4] > peilvanprofiel[proid][1]:   # OK, dit wordt het laatste punt
                                factor = (peilvanprofiel[proid][1] - links[4]) / \
                                         (rechts[4] - links[4])
                                nieuwex = links[2] + factor * (rechts[2] - links[2])
                                nieuwey = links[3] + factor * (rechts[3] - links[3])
                                prof[proid]["orig"].append([nieuwex, nieuwey, peilvanprofiel[proid][1]])
                                break
                            elif rechts[4] == peilvanprofiel[proid][1]:  # toeval precies op peil
                                if links[4] == rechts[4]:
                                    """dit is de uitzondering dat een profiel start precies op 
                                       het peil, het meest linkse punt moet vervangen worden
                                       """
                                    prof[proid]["orig"][0] = [rechts[2], rechts[3], rechts[4]]
                                else:   # OK dit is het laatste punt
                                    prof[proid]["orig"].append([rechts[2], rechts[3], rechts[4]])
                                    break
                            else:   # we kijken omhoog, punt is lager dan peil, punt toevoegen
                                prof[proid]["orig"].append([rechts[2], rechts[3], rechts[4]])
                    else:   # meedoen nog op nul
                        if omlaag:      # alleen als we omlaag kijken voor een doorsnijding met het peil
                            if rechts[4] <= peilvanprofiel[proid][1]:  # ok dit punt ligt onder het peil
                                meedoen = 1    # volgende punten gaan meedoen
                                omlaag = 0     # en we gaan omhoog kijken
                                if rechts[4] == peilvanprofiel[proid][1]:     # toeval perecies op peil
                                    prof[proid]['orig'] = [[rechts[2], rechts[3], rechts[4]]]
                                else:
                                    factor = (peilvanprofiel[proid][1] - links[4]) / (rechts[4] - links[4])
                                    nieuwex = links[2] + factor * (rechts[2] - links[2])
                                    nieuwey = links[3] + factor * (rechts[3] - links[3])
                                    prof[proid]['orig'] = [[nieuwex, nieuwey, peilvanprofiel[proid][1]]]
                    links = rechts
            prof[proid]['waterbreedte_orig'] = math.sqrt((prof[proid]['orig'][-1][0]-prof[proid]['orig'][0][0]) *\
                                                    (prof[proid]['orig'][-1][0]-prof[proid]['orig'][0][0]) +\
                                                    (prof[proid]['orig'][-1][1]-prof[proid]['orig'][0][1]) * \
                                                    (prof[proid]['orig'][-1][1] - prof[proid]['orig'][0][1]))
    return prof


def projecteerprofiel(prof,  projectie="eindpunt" ):
    """" Verrijk profielen met de projectie op een rechte lijn
    Invoer: prof = dictionary met gemeten profielen; punten staan onder key "orig"
            projectie = keuze soort projectie van de xy punten van het gemeten profiel; waarden:
                   eindpunt: op de rechte tussen de eindpunten van het gemeten profiel
                   loodlijn: op de loodlijn op het lijnstuk van het hydroObject tpv het kruispunt
                             van het lijnstuk van het hydroobject met de gemeten profiellijn (pro)
    In eerste instantie is alleen eindpunt geimplementeerd!
    """
    return prof


con = sql.connect('../tests/data/test_spatialite_with_theoretical_profiles.sqlite')
cur0 = con.cursor()
p = peilperprofiel(cur0)
print p
b = cur0.execute('select AsText(extent(GEOMETRY)) from pro where pro.pro_id=22488')
print cur0.fetchone()
gemprof = haal_meetprofielen(cur0)
print
print '----- 22531 ---'
print gemprof[22531]
print
print '----- 54577 ---'
print gemprof[54577]
