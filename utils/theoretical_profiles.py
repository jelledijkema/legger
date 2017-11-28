from pyspatialite import dbapi2 as sql
import pandas as pd
import numpy as np
import math
# import matplotlib.pyplot as plt
from pandas import DataFrame, Series

from legger.sql_models.legger import ProfielVarianten
from legger.sql_models.legger_database import LeggerDatabase

Km = 25  # coefficient van Manning in m**(1/3/s)
Kb = 23  # coefficient van Bos en Bijkerk in 1/s

""" Overige randvoorwaarden"""
Waterdiepte_initieel = 0.30  # (m) Watergangen ondieper dan 30cm niet wenselijk.
verhang_norm = 3.0  # (cm/km) Maximum verhangnorm voor Bos en Bijkerke en Manning.
Bodembreedte_minimaal = 0.50  # (m) Bodembreedte kan niet kleiner dan 50cm zijn.


def read_SpatiaLite(legger_db_filepath):
    table_name = "hydrokenmerken"

    conn = sql.connect(legger_db_filepath)
    c = conn.cursor()

    col1 = 'OBJECTID'
    col2 = 'DIEPTE'
    col3 = 'BREEDTE'
    col4 = 'INITIEELTALUD'
    col5 = 'STEILSTETALUD'
    col6 = 'GRONDSOORT'

    c.execute("Select ho.objectid, hk.diepte, hk.breedte, hk.initieeltalud, hk.steilstetalud, hk.grondsoort, "
              "ST_LENGTH(TRANSFORM(ho.geometry, 28992)) as length, tr.qend "
              "from hydroobject ho "
              "left outer join hydrokenmerken hk on ho.objectid = hk.objectid "
              "left outer join tdi_hydro_object_results tr on tr.hydroobject_id = hk.objectid")

    all_hits = c.fetchall()

    return DataFrame(all_hits, columns=[
        'OBJECTID',
        'DIEPTE',
        'BREEDTE',
        'INITIEELTALUD',
        'STEILSTETALUD',
        'GRONDSOORT',
        'LENGTH',
        'QEND'])


def filter_Onbruikbaar(dataframe_in, kolom):
    """ In de dataset zitten onvolmaaktheden, zoals informatie die ontbreekt of
    0 waarden. Deze worden eruit gefilterd en in een apart dataframe opgeslagen.
    """
    Onbruikbaar = dataframe_in[dataframe_in[kolom] == 0]  # Identificeer onbruikbare hydro-objecten met een waarde van 0
    Onbruikbaar = Onbruikbaar.append(
        dataframe_in[np.isnan(dataframe_in[kolom])])  # Er zitten wat NaN waarden in maxWaterbreedte.

    Onbruikbaar = Onbruikbaar.drop_duplicates()  # In het geval er dezelfde rij meerdere keren voorkomt.

    if (Onbruikbaar['OBJECTID'].count() == 0):
        print ("Er zijn geen Hydro objecten verwijderd.")
    else:
        print (str(Onbruikbaar['OBJECTID'].count()) + " Hydro object(en) verwijderd.")

    dataframe_uit = dataframe_in.drop(Onbruikbaar.index)

    return dataframe_uit


def bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud):
    """
    bla bla
    """
    Natte_Omtrek = (Bodembreedte
                    + (np.sqrt(Waterdiepte ** 2 + (Talud * Waterdiepte) ** 2))
                    + (np.sqrt(Waterdiepte ** 2 + (Talud * Waterdiepte) ** 2)))

    Oppervlak = (Bodembreedte * Waterdiepte
                 + (0.5 * (Waterdiepte * Talud) * Waterdiepte)
                 + (0.5 * (Waterdiepte * Talud) * Waterdiepte))

    Hydraulische_Straal = Oppervlak / Natte_Omtrek

    Verhang_Bos_Bijkerke = ((Maatgevend_Debiet / (
        Oppervlak * Kb * (Waterdiepte ** (0.333333)) * (Hydraulische_Straal ** 0.5))) ** 2) * 100000

    return Verhang_Bos_Bijkerke


def bereken_Manning(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud):
    Natte_Omtrek = (Bodembreedte
                    + (np.sqrt(Waterdiepte ** 2 + (Talud * Waterdiepte) ** 2))
                    + (np.sqrt(Waterdiepte ** 2 + (Talud * Waterdiepte) ** 2)))

    Oppervlak = (Bodembreedte * Waterdiepte
                 + (0.5 * (Waterdiepte * Talud) * Waterdiepte)
                 + (0.5 * (Waterdiepte * Talud) * Waterdiepte))

    Hydraulische_Straal = Oppervlak / Natte_Omtrek

    Verhang_Manning = ((Maatgevend_Debiet / (Oppervlak * Km * (Hydraulische_Straal ** (0.666667)))) ** 2) * 100000

    return Verhang_Manning


def bereken_profielMaxWaterbreedte(ObjectID, Maatgevend_Debiet, Lengte, Talud, Maximale_Waterbreedte,
                                   Waterdiepte_initieel):
    """ Berekenen van een dwarsprofiel op basis van maximale breedte en minimale diepte die
        aan de norm voldoet.
    """

    # initiele waarden
    Waterdiepte = Waterdiepte_initieel
    Bodembreedte = Maximale_Waterbreedte - Talud * Waterdiepte - Talud * Waterdiepte

    Verhang_Bos_Bijkerke = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)
    Verhang_Manning = bereken_Manning(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)

    # iteratie
    while Verhang_Bos_Bijkerke > verhang_norm or Verhang_Manning > verhang_norm:

        Waterdiepte = Waterdiepte + 0.05

        # Als de taluds elkaar raken (bodembreedte = minimum bodembreedte) dan is de iteratie klaar.
        if Maximale_Waterbreedte - Talud * Waterdiepte - Talud * Waterdiepte >= Bodembreedte_minimaal:

            Bodembreedte = Maximale_Waterbreedte - Talud * Waterdiepte - Talud * Waterdiepte

            # Daarna volgt een update van het verhang:

            Verhang_Bos_Bijkerke = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)
            Verhang_Manning = bereken_Manning(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)

        # Tenzij de bodembreedte te klein is geworden.
        else:

            print ("De bodembreedte is te klein geworden voor " + str(ObjectID))

            Waterdiepte = Waterdiepte - 0.05  # De originele diepte weer "terugzetten"

            # Gevolgd door een update van het verhang:

            Verhang_Bos_Bijkerke = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)
            Verhang_Manning = bereken_Manning(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)
            break

    profiel = pd.DataFrame([[ObjectID,
                             Maatgevend_Debiet,
                             Lengte,
                             Talud,
                             Maximale_Waterbreedte,
                             Waterdiepte,
                             Bodembreedte,
                             Verhang_Bos_Bijkerke,
                             Verhang_Manning]],
                           columns=['ObjectID', 'Maatgevend_Debiet', 'Lengte', 'Talud',
                                    'Maximale_Waterbreedte', 'Waterdiepte', 'Bodembreedte',
                                    'Verhang_Bos_Bijkerke', 'Verhang_Manning'])
    return profiel


def bereken_Opstuwing(ObjectID, Lengte, Verhang):
    """ bereken de Opstuwing die uit het berekende Verhang volgt."""

    Opstuwing = (float(Verhang) * (
        float(Lengte) / 1000.0))  # Verhang (in cm/km) wordt vermenigvuldigt met (Lengte (in m) / 1000 (in m/km))

    if Verhang > verhang_norm:
        print str(ObjectID) + " voldoet niet aan de norm van " + str(
            verhang_norm) + " cm/km."  # hydro objecten met een te grote opstuwing

    return ObjectID, Opstuwing


def bereken_Varianten(HO_Voldoen):
    # Tabel met hydro_Objecten codes en hoeveel "opties" er zijn.
    Opties_tabel = DataFrame(data=HO_Voldoen.ObjectID, columns=['ObjectID', 'aantal'])

    # Tabel waarin de varianten worden opgenomen, eerst wordt een leeg dataframe aangemaakt.
    Varianten_tabel = DataFrame(columns=['ObjectID', 'Object_DiepteID', 'Talud',
                                         'Waterdiepte', 'Waterbreedte', 'Bodembreedte',
                                         'Maatgevend_Debiet', 'Verhang_Bos_Bijkerke'])
    # De kern van de iteratie:

    for i, rows in HO_Voldoen.iterrows():
        count = 0

        # Harde stop: als bodembreedte 0.5 is, dan kan de iteratie niet plaatsvinden
        while (round(HO_Voldoen.Maximale_Waterbreedte[i], 1) -
                           (HO_Voldoen.Waterdiepte[i] + 0.05 * count) * HO_Voldoen.Talud[i] * 2 > 0.5):

            ObjectID = HO_Voldoen.ObjectID[i]
            Object_DiepteID = (str(HO_Voldoen.ObjectID[i]) + "_" +
                               str(round(HO_Voldoen.Waterdiepte[i] * 100 + (count * 5), 0)))

            Talud = HO_Voldoen.Talud[i]
            Waterdiepte = HO_Voldoen.Waterdiepte[i] + 0.05 * count
            Waterbreedte = round(HO_Voldoen.Maximale_Waterbreedte[i], 1)
            Bodembreedte = Waterbreedte - (Waterdiepte * Talud * 2)

            Maatgevend_Debiet = HO_Voldoen.Maatgevend_Debiet[i]

            Verhang_BB = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)

            # Er mag een iteratie plaatsvinden als verhang onder de 2,5 is. Niet absoluut nauwkeurig, maar bij benadering werkt het.
            while (Verhang_BB < 2.5):
                Waterbreedte = Waterbreedte - 0.05
                Bodembreedte = Waterbreedte - (Waterdiepte * Talud * 2)

                Verhang_BB = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)

            Bodembreedte = round(Bodembreedte, 2)

            if Bodembreedte < 0.50:
                print(Object_DiepteID + ": iteratie stopt vanwege te smalle bodembreedte")
                break
            print ("Voor " + str(ObjectID) + " bij een diepte van " + str(Waterdiepte) +
                   " is de bodembreedte " + str(Bodembreedte) + " en het verhang " + str(Verhang_BB))
            df_temp = pd.DataFrame([[ObjectID,
                                     Object_DiepteID,
                                     Talud,
                                     Waterdiepte,
                                     Waterbreedte,
                                     Bodembreedte,
                                     Maatgevend_Debiet,
                                     Verhang_BB]],
                                   columns=['ObjectID', 'Object_DiepteID', 'Talud',
                                            'Waterdiepte', 'Waterbreedte', 'Bodembreedte',
                                            'Maatgevend_Debiet', 'Verhang_Bos_Bijkerke'])

            Varianten_tabel = Varianten_tabel.append(df_temp)

            count = count + 1

        if count == 0:
            # Komt voor bij hele lage maatgevende debieten, dan is er maar een hele kleine legger nodig.
            # Door de iteratie met een kleiner wordende waterbreedte als dat mogelijk is onder het verhang, wordt de bodembreedte
            # negatief en faalt de iteratie. Voor deze hydro_objecten wordt er apart 1 legger gemaakt.
            print ("minimaal bakje!")
            Bodembreedte = 0.5
            Waterbreedte = Bodembreedte + Talud * Waterdiepte

            Verhang_BB = bereken_BosBijkerke(Maatgevend_Debiet, Bodembreedte, Waterdiepte, Talud)

            df_temp = pd.DataFrame([[ObjectID,
                                     Object_DiepteID,
                                     Talud,
                                     Waterdiepte,
                                     Waterbreedte,
                                     Bodembreedte,
                                     Maatgevend_Debiet,
                                     Verhang_BB]],
                                   columns=['ObjectID', 'Object_DiepteID', 'Talud',
                                            'Waterdiepte', 'Waterbreedte', 'Bodembreedte',
                                            'Maatgevend_Debiet', 'Verhang_Bos_Bijkerke'])

            Varianten_tabel = Varianten_tabel.append(df_temp)
            count = 1

        Opties_tabel.aantal[Opties_tabel.ObjectID == Opties_tabel.ObjectID[i]] = count
    Varianten_tabel = Varianten_tabel.reset_index(drop=True)

    return Varianten_tabel


def print_Objecten_VoldoenNiet(input_tabel):
    if "ObjectID" in input_tabel.columns:
        if "Verhang_Bos_Bijkerke" in input_tabel.columns:
            if "Verhang_Manning" in input_tabel.columns:

                for i, rows in input_tabel.iterrows():
                    if max(float(input_tabel.Verhang_Bos_Bijkerke[i]),
                           float(input_tabel.Verhang_Manning[i])) > verhang_norm:
                        print input_tabel.ObjectID[i]

            else:
                print ("Geen Verhang data in de vorm van 'Verhang_Manning' als kolom")
        else:
            print ("Geen Verhang data in de vorm van 'Verhang_Bos_Bijkerke' als kolom")
    else:
        print ("Geen 'ObjectID'")


""" Van elk hydro-Object is de volgende informatie verzameld:
- ID
- Maatgevende afvoer
- Taludhelling
- Maximale Waterbreedte
- Lengte (dit is nodig om iets te kunnen zeggen over de impact op het geheel)

Hieruit wordt berekend:
- Wat de minimale benodigde waterdiepte is bij de berekende waterbreedte om aan de opstuwingsnorm (3 cm/km) te voldoen.
- Wat de bijbehorende bodembreedte is. De bodembreedte moet minimaal 0,5 m zijn.

Er wordt begonnen met een initiele waterdiepte van 0,3m. 

Verhang wordt berekend met Bos en Bijkerke en Manning. Ook het absolute verhang (verhang*lengte hydro-object) wordt berekend.

Als het mogelijk is om een dwarsprofiel te genereren die aan de opstuwingsnorm voldoet, dan wordt deze opgeslagen als
"dwarsprofiel met maximale waterbreedte en minimale waterdiepte" in een aparte excel.

In een volgende berekening wordt dit profiel verdiept (met een vaste waarde) en versmald (middels een iteratie).
De nieuw berekende breedte bij deze verdieping van het dwarsprofiel wordt gevonden door breedte af te laten nemen totdat 
de opstuwing groter is dan de norm.
De iteratie stopt dus als:
- opstuwing > norm
- de bodembreedte kleiner wordt dan 0,5m.
"""

"""
Deel 1: inlezen SpatiaLite

zie definitie read_SpatiaLite(polder)

"""

"""
Oude Manier:
Dataframe in elkaar zetten.
Dit stuk gaat vervangen worden door een plugin naar een database in SQLite.
Uitkomst: Database in Python met de volgende info
- ObjectID
- Maatgevend Debiet door het object
- Lengte van het object
- Talud helling
- Waterbreedte (maximaal)


frame1 = pd.read_excel('reach_waterlopen_spatialjoin_Marken.xlsx')
frame2 = pd.read_excel('Tabel_Waterbreedte_Marken.xlsx')


Hydro_objecten = DataFrame(frame1,columns=['ID','Discharge','LENGTE','WS_TALUD_L']) # Alle interessante kolommen in een dataframe
Hydro_objecten.columns = ['ObjectID','Maatgevend_Debiet','Lengte','Talud'] # Herbenoemen kolommen

Aanvulling = DataFrame(frame2,columns=['CODE','width']) # Aanmaken van een dataframe
Aanvulling.columns = ['ObjectID','Maximale_Waterbreedte']

Hydro_objecten = pd.merge(Hydro_objecten,Aanvulling,on='ObjectID',how='left') # Samenvoegen van beide tabellen, op de ObjectID data

del frame1
del frame2
"""

""" De benodigde coefficienten voor verhang berekening van Manning en Bos en Bijkerke (mag varieren):"""


def create_theoretical_profiles(legger_db_filepath):
    Hydro_objecten = read_SpatiaLite(legger_db_filepath)
    print (Hydro_objecten)

    """
    Er zitten hydro objecten tussen waarvan geen opstuwing kan worden berekend omdat er "cruciale" data ontbreekt. 
    Specificeer de naam van de kolom
    
    """

    kolom = "BREEDTE"
    Hydro_objecten = filter_Onbruikbaar(Hydro_objecten, kolom)

    # In[43]:

    """ 
    Het bereken van een leggerprofiel per hydro-object op basis van de maximale waterbreedte.
    """
    HO = pd.DataFrame(
        columns=['ObjectID', 'Maatgevend_Debiet', 'Lengte', 'Talud', 'Maximale_Waterbreedte', 'Waterdiepte',
                 'Bodembreedte', 'Verhang_Bos_Bijkerke', 'Verhang_Manning'])

    for i, rows in Hydro_objecten.iterrows():

        ObjectID = Hydro_objecten.OBJECTID[i]

        if Hydro_objecten.GRONDSOORT[i] == "veenweide":
            Talud = 3.0
        else:
            Talud = 2.0
        Maximale_Waterbreedte = Hydro_objecten.BREEDTE[i]

        Maatgevend_Debiet = 0.05  # Hydro_objecten.Maatgevend_Debiet[i]
        Lengte = 10  # Hydro_objecten.Lengte[i]

        profiel = bereken_profielMaxWaterbreedte(ObjectID, Maatgevend_Debiet, Lengte, Talud, Maximale_Waterbreedte,
                                                 Waterdiepte_initieel)

        HO = HO.append(profiel)
    HO = HO.reset_index(drop=True)

    # Identificeer profielen die niet voldoen
    print_Objecten_VoldoenNiet(HO)

    """ Toevoegen van opstuwing"""
    Opstuwing = pd.DataFrame(columns=['ObjectID', 'Opstuwing'])

    for i, rows in HO.iterrows():
        ObjectID = HO.ObjectID[i]
        Lengte = HO.Lengte[i]
        Verhang = max(float(HO.Verhang_Bos_Bijkerke[i]),
                      float(HO.Verhang_Manning[i]))  # maximum van de twee berekeningen

        resultaat = bereken_Opstuwing(ObjectID, Lengte, Verhang)

        """ Opnemen resultaten in tabel"""
        df_temp = pd.DataFrame([resultaat],
                               columns=['ObjectID', 'Opstuwing'])

        Opstuwing = Opstuwing.append(df_temp)

    Opstuwing = Opstuwing.reset_index(drop=True)

    HO = pd.merge(HO, Opstuwing, on='ObjectID', how='left')

    """Tabel waarbij wat statistieken zichtbaar kunnen worden gemaakt """

    # todo: maak er een functie van
    # todo: beschrijving toevoegen.

    e = 0.5  # Welke totale opstuwing is interessant?

    pd.DataFrame({'hoeveel hydro_objecten niet voldoen': pd.Series(
        [(len(HO[HO['Verhang_Manning'] > verhang_norm])),
         (len(HO[HO['Verhang_Bos_Bijkerke'] > verhang_norm])),
         (len(HO[HO['Opstuwing'] > e])),
         len(HO['ObjectID'])],
        index=[("# watergangen met Verhang Manning > " + str(verhang_norm)),
               "# watergangen met Verhang Bos Bijkerke > " + str(verhang_norm),
               "Verhang absoluut => " + str(e) + " cm over hydro object",
               "Totaal aantal watergangen"]
    )})

    """Einde deel 1
    Tot hier is de informatie in de hydro-objecten vertaald naar een leggerprofiel waarbij
    de maximum waterbreedte als uitgangspunt is genomen.
    Van elk hydro-object is de opstuwing berekend en ook een absolute opstuwing.
    Er zijn excel exports gemaakt waarbij deze informatie is vastgelegd als tussenstap.
    En een tabel met de hydro-objecten waar geen voldoende data is voor deze tussenstap.
    ~~~~
    """

    # HO.to_excel(
    #     'bereken_En_Visualiseren_Dwarsprofielen_v3.xlsx')  # Exporteer de waardes van de dwarsprofielen met een zo breed mogelijk profiel
    # Onbruikbaar.to_excel(
    #     'Onbruikbaar_bereken_En_Visualiseren_Dwarsprofielen_v3.xlsx')  # Exporteer de onbruikbare hydro-objecten

    """
    ~~~~
    Deel 2: Van een profiel met maximale breedte en minimale diepte, naar Opties en Varianten.
    In dit gedeelte worden er voor de hydro-objecten meerdere leggerprofielen berekend.
    Uitgangspositie is het profiel met de maximale breedte en minimale diepte.
    """

    # Uncomment de volgende lijn als er vanaf dit punt wordt aangevangen
    # HO = pd.read_excel('bereken_En_Visualiseren_Dwarsprofielen_v3.xlsx')

    # Scheidt de profielen die voldoen van die niet voldoen
    HO_Voldoen = HO[HO['Verhang_Manning'] <= verhang_norm]
    HO_Voldoen_niet = HO[HO['Verhang_Manning'] > verhang_norm]

    # todo: maak universeler door het toevoegen van Verhang_BB als limiterende factor.
    HO_Varianten = bereken_Varianten(HO_Voldoen)

    # Exporteer de onbruikbare hydro-objecten
    # HO_Varianten.to_excel('Export_Dwarsprofielen_Marken_v2.xlsx')

    return HO_Varianten


def write_theoretical_profile_results_to_db(profile_results, path_legger_db):
    db = LeggerDatabase(
        {
            'db_path': path_legger_db
        },
        'spatialite'
    )
    db.create_and_check_fields()
    session = db.get_session()

    profiles = []

    for i, rows in profile_results.iterrows():
        profiles.append(ProfielVarianten(
            hydro_object_id=profile_results.ObjectID[i],
            id=profile_results.Object_DiepteID[i],
            talud=profile_results.Talud[i],
            waterdiepte=profile_results.Waterdiepte[i],
            waterbreedte=profile_results.Waterbreedte[i],
            bodembreedte=profile_results.Bodembreedte[i],
            maatgevend_debiet=profile_results.Maatgevend_Debiet[i],
            verhang_bos_bijkerk=profile_results.Verhang_Bos_Bijkerke[i],
        ))

    session.execute("Delete from {0}".format(ProfielVarianten.__tablename__))

    session.bulk_save_objects(profiles)
    session.commit()
