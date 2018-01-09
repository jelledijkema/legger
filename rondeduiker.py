from math import sqrt,acos,pow,pi

# Dit zijn de functies die in het excelsheet 'berekening kunstwerken.xls', tabblad 'ronde duiker' staan.

#K3
def segmentberekening(mydiameter, mywaterpeil,mybod):
	seg =\
		(float\
			(\
				acos(\
					abs(\
						((float(mydiameter)/2)-(mywaterpeil-mybod))\
						/\
						(float(mydiameter)/2)\
					)\
				)\
				*\
				float(180)/pi*2\
			)\
			/\
			360\
		)\
		* (pi*(pow(float(mydiameter)/2,2)))\
		- (\
			abs(\
				pow(\
					(pow(float(mydiameter)/2,2))\
					-\
					(pow(\
						(float(mydiameter)/2) - (mywaterpeil-mybod)\
					,2)\
					)\
				,0.5)\
			)\
			* abs(\
				(float(mydiameter)/2) - (mywaterpeil-mybod)\
			)\
		)
	return seg

#K4
def natteoppervlak_cirkel(mydiameter,mywaterpeil,mybod):
	if   (mywaterpeil - mybod >= mydiameter):
		nop = pi*pow(float(mydiameter)/2,2)
	elif (mywaterpeil - mybod >= float(mydiameter)/2):
		nop = pi*pow(float(mydiameter)/2,2) - segmentberekening(mydiameter,mywaterpeil,mybod)
	else:
		nop = segmentberekening(mydiameter,mywaterpeil,mybod)
	return nop

#K6
def sectorberekening(mydiameter,mywaterpeil,mybod):
	mydiameter=1
	mywaterpeil=-2.9
	mybod=-3.7
	sec = (\
		2*(\
			(\
				acos(\
					float(abs(\
						(float(mydiameter)/2)-(mywaterpeil-mybod)\
					))\
					/\
					(float(mydiameter)/2)\
				)\
				*\
				float(180)/pi\
			)\
		)/\
		360*2*pi*float(mydiameter)/2\
	)
	return sec

#K7
def natteomtrek_cirkel(mydiameter,mywaterpeil,mybod):
	seg = segmentberekening(mydiameter,mywaterpeil,mybod)
	if   (mywaterpeil - mybod >= mydiameter):
		nom = 2*pi*float(mydiameter)/2
	elif (mywaterpeil - mybod < mydiameter) and (mywaterpeil - mybod >= float(mydiameter)/2):
		nom = (2*pi*float(mydiameter)/2) - sectorberekening(mydiameter,mywaterpeil,mybod)
	else:
		nom = sectorberekening(mydiameter,mywaterpeil,mybod)
	return nom

#K10
def uittreeverlies(mynop,myslootbodemhoogte,myslootbodembreedte,mytalud,mywaterpeil):
	uv = pow(\
		(\
			1-(\
				float(mynop)\
				/\
				(\
					(mywaterpeil-myslootbodemhoogte)\
					*\
					(myslootbodembreedte+(mywaterpeil-myslootbodemhoogte)*mytalud)\
				)\
			)\
		),2\
	)
	return uv

#K11
def kmwaarde(mytypemateriaal,mydiameter):
	kmwaarden = {'pvcpp':{0.40:90,0.50:90,0.60:90,0.70:90,0.80:90,0.90:90,1.00:90,1.10:90,1.20:90,1.25:90,1.30:90,1.40:90,1.50:90,1.60:90,1.70:90,1.75:90,1.80:90,1.90:90,2.00:90,2.10:90,2.20:90,2.25:90},'spiwel':{0.40:78,0.50:67,0.60:61,0.70:57,0.80:55,0.90:48,1.00:46,1.10:45,1.20:44,1.25:43,1.30:43,1.40:42,1.50:42,1.60:41,1.70:40,1.75:39,1.80:39,1.90:38,2.00:37,2.10:37,2.20:37,2.25:37},'beton':{0.40:75,0.50:75,0.60:75,0.70:75,0.80:75,0.90:75,1.00:75,1.10:75,1.20:75,1.25:75,1.30:75,1.40:75,1.50:75,1.60:75,1.70:75,1.75:75,1.80:75,1.90:75,2.00:75,2.10:75,2.20:75,2.25:75}}
	if ((mydiameter>0.35) and (mydiameter<2.3) and (mytypemateriaal in ['beton','pvcpp','spiwel'])):
		nearestdiameter = min(kmwaarden[mytypemateriaal].keys(), key=lambda x:abs(x-mydiameter))
		kmwaarde = kmwaarden[mytypemateriaal][nearestdiameter]
	return kmwaarde

#K12
def knikverlies(myaantalknikken,myknikhoek):
	knikverliezen={1:0.02,5:0.02,6:0.04,10:0.04,11:0.05,15:0.05,16:0.1,22.5:0.1,23:0.15,30:0.15,31:0.28,45:0.28,46:0.55,60:0.55,61:1.2,90:1.2}
	nearestknikhoek = min(knikverliezen.keys(), key=lambda x:abs(x-myknikhoek))
	thisknikverlies = knikverliezen[nearestknikhoek]*myaantalknikken
	return thisknikverlies

def bochtverlies(myaantalbochten,mybochthoek):
	bochtverliezen={1:0.03,15:0.03,16:0.045,22.5:0.045,23:0.05,30:0.05,31:0.08,45:0.08,46:0.1,60:0.1,61:0.23,90:0.23}
	nearestbochthoek = min(bochtverliezen.keys(), key=lambda x:abs(x-mybochthoek))
	thisbochtverlies = bochtverliezen[nearestbochthoek]*myaantalbochten
	return thisbochtverlies

#K13
def wrijvingsverlies(mykm,mynop,mynom,myduikerlengte):
	thiswv = float(2*9.81*myduikerlengte)\
	/\
	(\
		pow(mykm,2)\
		*\
		pow((float(thisnop)/thisnom),float(4)/3)\
	)
	return thiswv

#K14
def weerstandscoefficient_metsloot(myuv,mykv,mybv,mywv):
	thisiv = 0.6	#K9
	thiswc = float(1) / pow(thisiv+myuv+mykv+mybv+mywv,0.5)
	return thiswc

def weerstandscoefficient_zondersloot(mykv,mybv,mywv):
	thisiv = 1.5	#K9
	thiswc = float(1) / pow(thisiv+mykv+mybv+mywv,0.5)
	return thiswc

#E30
def opstuwing_zondersloot(mywc,mynop,mydebiet):
	thisopstuwing = 	float(\
			pow(float(mydebiet)/(mywc*mynop),2)\
			)/\
			(2*9.81)
	return thisopstuwing

def opstuwing_metsloot(mywc,mynop,mydebiet):
	thisopstuwing = 	float(\
			pow(float(mydebiet)/(mywc*mynop),2)\
			)/\
			(2*9.81)
	return thisopstuwing

def maxdebiet_zondersloot(mywc,mynop,myopstuwing):
	thismaxdebiet = mywc*mynop\
		    *pow(2*9.81*myopstuwing,0.5)
	return thismaxdebiet

def maxdebiet_metsloot(mywc,mynop,myopstuwing):
	thismaxdebiet = mywc*mynop\
		    *pow(2*9.81*myopstuwing,0.5)
	return thismaxdebiet

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
