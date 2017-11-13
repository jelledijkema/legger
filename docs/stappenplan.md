### Woordenlijst
*Theoretisch profiel:* leggerprofiel, bestaat uit bodemhoogte, bodembreedte en talud (talud links en -rechts zijn identiek);
*Gemeten profiel:* dwarsprofiel van watergang, bestaat uit gemeten punten met x, y, z -coordinaten. Gemeten profielen kunnen een Z1 (vaste
bodem) of een Z2 (zachte bodem, sliblaag) bevatten.

### STAP 1
**_Korte omschrijving:_** Stap 1 omvat het samenstellen van basisinformatie: o.a. het afleiden van een maximum breedte en maximum
diepte. Stap 1 is in 4 delen gesplitst:
1. Bepalen segmenten (t.b.v. hydro-objecten zonder gemeten profielen);
1. Bepalen maximum breedte;
1. Bepalen maximum diepte;
1. Verrijken met gegevens (waaronder streefpeilen **(bespreken met Maarten, welk peil hanteren)**, grondsoort, initieel talud en steilste talud).

**INPUT**
* Gemeten profielen:
  * x, y, z coordinaten;
  * IWS_VOLGNR;
  * PRODIDENT;
  * PRWIDENT;
  * ???
* Hydro-objecten:
  * hydroobject_id
  * categorie (primair=1, secundair=2, tertiair=3)
  * in_peilgebied **(bespreken met Maarten, wat te doen met peilafwijkingen i.h.k.v. toetspeilen)**
* PeilgebiedPraktijk;
 * peilgebiedpraktijk_id
* Streefpeil (tabel)
* Watervlakken;
* Grondsoorten???
* Dieptemetingen baggeraars???

**OUTPUT DEEL 1.1**
* Segmenten van hydro-objecten (hydro-objecten, zonder gemeten profiel, kunnen gebruik maken van een ander hydo-
object, met gemeten   profiel, in hetzelfde segment);
    * Hydro-object ID;
    * Segment ID.

**OUTPUT DEEL 1.2**
* Hydro-objecten:
  * Hydro-object ID;
  * Maximum breedte.

**OUTPUT DEEL 1.3**
* Hydro-objecten:
  * Hydro-object ID;
  * Maximum diepte.

**OUTPUT DEEL 1.4**
* Hydro-objecten:
  * Hydro-object ID;
  * Peilvak ID???;
  * Streefpeil zomer;
  * Streefpeil winter;
  * Grondsoort;
  * Initieel talud;
  * Steilste talud;
  * Dieptemetingen baggeraars.

### STAP 2
**_Korte omschrijving:_** Stap 2 omvat het samenstellen van theoretische profielen. Hiervoor wordt van de in stap 1 afgeleide
maximum breedte en diepte gebruikt. Verder wordt van de gemeten profielen gebruik gemaakt. De maximum breedte is een harde
grens, de maximum diepte  een indicator en t.o.v. de gemeten profielen wordt een 'fit' berekend. Bijvoorbeeld, het theoretische profiel
past 95% binnen het gemeten profiel. In eerste instantie wordt uitgegaan van het initieel talud (zie stap 1), mocht geen passend profiel
worden gevonden wordt een steiler talud geitereerd. De iteratie kan doorlopen totdat het steilste talud is bereikt (zie wederom stap 1).
Debieten worden uit bijbehorende 3Di modellen gehaald. Stap 2 is in 3 delen gesplitst:
1. Samenstellen theoretische profielen, hierbij wordt gekeken naar opstuwing volgens de formule van Bos & Bijkerk **(welke ruwheidswaarde???)**
1. Verwerken gemeten profielen (tot platgeslagen gemeten profielen)
1. Berekenen fit **(welke fit aanhouden???)** 

**Moeten we hier een 4e stap toevoegen? Namelijk het verrijken van de data met debieten? Dan kan stap 1 in z'n geheel met FME  uitgevoerd
worden en valt de rest binnen Python.**

**INPUT**
* Resultaat stap 1;
* Gemeten profielen:
  * x, y, z coordinaten;
  * IWS_VOLGNR;
  * PRODIDENT;
  * PRWIDENT;
  *??? 
* Debiet (t=laatst, gaat om stationaire situatie)

**OUTPUT DEEL 2.1**
* Alle mogelijke theoretische profielen (per hydro-object);
  * Profiel ID
  * Bodemhoogte;
  * Bodembreedte;
  * Talud
  * Hydro-object ID

**OUTPUT DEEL 2.2**
* Platgeslagen gemeten profielen:
  * x, y coordinaten;
  * IWS_VOLGNR;
  * PROIDENT;
  * PRWIDENT;

**OUTPUT DEEL 2.3**
* Output deel 2.1 verrijkt met fit.

### STAP 3
**_Korte omschrijving:_** Stap drie omvat de laatste fase van de tool: het toewijzen van theoretische profielen middels een zoekalgorithme.
### Moeten we onderscheid aanbrengen tussen primair en belangrijk secundair en secundair tertiair (i.e. zonder afmetingen)??? Bespreken met Maarten.###

**INPUT:**
* Resultaat stap 1;
* Resultaat stap 2;
* Startpunten (bijvoorbeeld gemaal);
* Keuzemomenten (peilgrens, peilafwijkingsgrens). We moeten uitzoeken of de kruising van een peilgrens o.b.v. de in hydro-objecten
  aangegeven peilvakken kan worden afgeleidt.
  
**OUTPUT**
* Voorkeursprofiel (d.m.v. zoekalgorithme gekozen profiel) per hydro-object.


Uitgangspunten:
*Peilgrenzen en peilafwijkingsgrenzen kloppen, daarmee liggen dus ook alle kunstwerken op de juiste plek.
