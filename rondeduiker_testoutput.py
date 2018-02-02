from rondeduiker import *

# tmp variabelen
thisdiameter = 1
thistypemateriaal = 'spiwel'
thisbod = -3.7	#binnen onderkant duiker
thiswaterpeil = -2.9
thisslootbodemhoogte = -3.6
thisslootbodembreedte = 1 
thistalud = 1.5
thisaantalknikken = 1 
thisknikhoek = 10
thisaantalbochten = 0 
thisbochthoek = 10
thisduikerlengte = 18
thisopstuwing = 0.253
thisdebiet = 0.253

thisseg = segmentberekening(thisdiameter,thiswaterpeil,thisbod)
thissec = sectorberekening(thisdiameter,thiswaterpeil,thisbod)
thiskm = kmwaarde(thistypemateriaal,thisdiameter)
thisnop = natteoppervlak_cirkel(thisdiameter,thiswaterpeil,thisbod)
thisnom = natteomtrek_cirkel(thisdiameter,thiswaterpeil,thisbod)
thiskv = knikverlies(thisaantalknikken,thisknikhoek)
thisbv = bochtverlies(thisaantalbochten,thisbochthoek)
thisuv = uittreeverlies(thisnop,thisslootbodemhoogte,thisslootbodembreedte,thistalud,thiswaterpeil)
thiswv = wrijvingsverlies(thiskm,thisnop,thisnom,thisduikerlengte)
thiswcsloot = weerstandscoefficient_metsloot(thisuv,thiskv,thisbv,thiswv)
thiswcnosloot = weerstandscoefficient_zondersloot(thiskv,thisbv,thiswv)
thisopstuwsloot = opstuwing_metsloot(thiswcsloot,thisnop,thisdebiet)
thisopstuwnosloot = opstuwing_zondersloot(thiswcnosloot,thisnop,thisdebiet)
thismaxdbsloot = maxdebiet_metsloot(thiswcsloot,thisnop,thisopstuwing)
thismaxdbnosloot = maxdebiet_zondersloot(thiswcnosloot,thisnop,thisopstuwing)

print """\
	segmentberekening: %s
	sectorberekening: %s
	kmwaarde: %s
	natteoppervlak: %s
	natteomtrek: %s
	uittreeverlies: %s
	weerstandcoefficient met sloot: %s
	weerstandcoefficient zonder sloot: %s
	knikverlies: %s
	bochtverlies: %s
	wrijvingsverlies: %s
	max.debiet zonder sloot: %s
	opstuwing zonder sloot: %s
	max.debiet met sloot: %s
	opstuwing met sloot: %s\
"""%(thisseg,thissec,thiskm,thisnop,thisnom,thisuv,thiswcsloot,thiswcnosloot,thiskv,thisbv,thiswv,thismaxdbnosloot,thisopstuwnosloot,thismaxdbsloot,thisopstuwsloot)
