#
# #### Deel 3:
# # in het geval de iteratie (deel 1 en 2) niet opnieuw wordt gedaan, uncomment de volgende line
# hydro_Objecten_Varianten = pd.read_excel('Export_Dwarsprofielen_Marken_V4.xlsx')
# WL = pd.read_excel('Breedste_Dwarsprofielen_Marken_V4.xlsx')
# # dit zijn alle mogelijke dwarsprofielen per hydro object voor polder Marken.
#
# # !!! Vergeet niet de tabel WL in te laden, dus het eerste gedeelte van deel 1.
#
# # Met de functie matplotlib kunnen de berekende dwarsprofielen grafisch weergegeven worden.
#
#
# # Deel 3 plot de berekende mogelijke dwarsprofielen binnen het fysieke domein van de hydro objecten.
# # Er wordt uitgegaan van een assenstelsel (x,y) waarbij (0,0) het midden van de watergang (x=0) en de waterhoogte (y=0) voorstelt.
# # Het domein van de geplotte ruimte is dus:
# # - voor x [-0,5*maximale Waterbreedte, 0,5*maximale Waterbreedte]
# # - voor y is het [0, maximale Waterdiepte].
# # De mogelijke dwarsprofielen worden dus weergegeven met het midden van de waterbreedte op x=0 en de waterdiepte t.o.v. y=0.
#
#
# # In[35]:
#
# Gemeten_profielen = pd.read_excel('gemeten_profielen_Marken.xlsx')
#
# # In[133]:
#
# # De code om de gemeten profielen te tekenen.
# #
# # for i, rows in WL.iterrows():
# #    hydro_object = WL.ObjectID[i]
# #
# #    x_list = list()
# #    y_list = list()
# #    nr_list = list()
# #
# #    for k, rows in Gemeten_profielen.iterrows():
# #        if ((Gemeten_profielen.CODE[k]) == hydro_object and (Gemeten_profielen.OSMOMSCH[k] == "Z1")):
# #            nr = (Gemeten_profielen.IWS_VOLGNR[k])
# #            x = (Gemeten_profielen.x_gp[k])
# #            y = (Gemeten_profielen.y_gp[k])
# #
# #            x_list.append(x)
# #            y_list.append(y)
# #            nr_list.append(nr)
# #
# #    x_ser = pd.Series(x_list, index=nr_list, name='x')
# #    y_ser = pd.Series(y_list, index=nr_list, name= 'y')
# #
# #    Profiel = pd.concat([x_ser,y_ser], axis=1)
# #    Profiel = Profiel.sort_index(ascending=True)
# #
# #    if (len(x_list) >0):
# #        plt.plot(Profiel.x,Profiel.y,color='brown',linewidth=2,label=hydro_object)
# #        plt.title(hydro_object)
# #        plt.show()
# #
#
#
# # In[57]:
#
# import time
#
# start = time.time()
#
# # De theoretische profielen worden geplot. Samen met relevante plots van waterbreedte, oeverwanden, en bodemdiepte.
# # De theoretische profielen komen uit dit script (deel 1 en deel 2).
# # De randvoorwaarden worden in dezelfde figuur weergegeven:
# # Het streefpeil wordt weergegeven.
# # De "zijkanten" worden weergegeven als verticale lijnen op waterbreedte.
# # {NOG NIET} de bodemhoogte wordt weergegeven.
# # Ook worden gemeten profielen geplot, want in Marken is daar informatie over.
#
# for i, rows in WL.iterrows():
#     # Laadt voor elke hydro object de ID code, maximale waterbreedte en (voorlopige) maximale diepte in.
#     hydro_object = WL.ObjectID[i]
#     Max_breedte = WL.Maximale_Waterbreedte[i]
#     diepte = WL.Waterdiepte[i]
#     talud = WL.Talud[i]
#
#     Max_diepte = 0
#     streefpeil = -1.05
#
#     # plot de maximale breedte als een blauwe onderbroken lijn. Dit is op streefpeilniveau.
#     x1 = [0, Max_breedte]
#     y1 = [streefpeil, streefpeil]
#     plt.plot(x1, y1, linestyle='--', color='blue', label="Water oppervlak")
#
#     # gebruik de hydro_object code om in de varianten tabel de regels op te zoeken met die objectcode en teken
#     # voor elke hydro object + diepte combinatie het dwarsprofiel in met 3 lijnstukken.
#
#     # x = [0,
#     #     (hydro_Objecten_Varianten.Waterdiepte[j]*talud),
#     #     ((hydro_Objecten_Varianten.Waterdiepte[j]*talud) + hydro_Objecten_Varianten.Bodembreedte[j]),
#     #     ((hydro_Objecten_Varianten.Waterdiepte[j]*talud)*2)+(hydro_Objecten_Varianten.Bodembreedte[j])]
#
#     for j, rows in hydro_Objecten_Varianten.iterrows():
#         if hydro_Objecten_Varianten.ObjectID[j] == hydro_object:
#             x = [(0.5 * (Max_breedte - hydro_Objecten_Varianten.Waterbreedte[j])),
#                  (0.5 * (Max_breedte - hydro_Objecten_Varianten.Bodembreedte[j])),
#                  (hydro_Objecten_Varianten.Bodembreedte[j] + (
#                  0.5 * (Max_breedte - hydro_Objecten_Varianten.Bodembreedte[j]))),
#                  (Max_breedte - (0.5 * (Max_breedte - hydro_Objecten_Varianten.Waterbreedte[j])))]
#             y = [streefpeil,
#                  streefpeil - 1 * hydro_Objecten_Varianten.Waterdiepte[j],
#                  streefpeil - 1 * hydro_Objecten_Varianten.Waterdiepte[j],
#                  streefpeil]
#             labelnaam = str(hydro_Objecten_Varianten.Object_DiepteID[j])
#
#             plt.plot(x, y, label=labelnaam)
#
#             # zorg dat max_diepte ook echt de maxDiepte is door deze variabele te updaten.
#             if hydro_Objecten_Varianten.Waterdiepte[j] > Max_diepte:
#                 Max_diepte = hydro_Objecten_Varianten.Waterdiepte[j]
#
#     # deze lijn kun je teken om de symmetrie lijn te tekenen.
#     # x2 = [0,0]
#     # y2 = [0,-1*Max_diepte]
#     # plt.plot(x2,y2,linestyle=':',color='black',label="Waterdiepte")
#
#     # idealiter komt hier nog:
#     # x5 = [-0.5*Max_breedte,-0.5*Max_breedte]
#     # y5 = [-1*Max_diepte,-1*Max_diepte]
#     # Maar alleen als er iets bekend is over de max diepte
#
#     # Voor de hydro objecten met een gemeten profiel
#     x_list = list()
#     y_list = list()
#     nr_list = list()
#
#     for k, rows in Gemeten_profielen.iterrows():
#         if ((Gemeten_profielen.CODE[k]) == hydro_object and (Gemeten_profielen.OSMOMSCH[k] == "Z1")):
#             nr = (Gemeten_profielen.IWS_VOLGNR[k])
#             x = (Gemeten_profielen.x_gp[k])
#             y = (Gemeten_profielen.y_gp[k])
#
#             x_list.append(x)
#             y_list.append(y)
#             nr_list.append(nr)
#
#     x_ser = pd.Series(x_list, index=nr_list, name='x')
#     y_ser = pd.Series(y_list, index=nr_list, name='y')
#
#     Profiel_z1 = pd.concat([x_ser, y_ser], axis=1)
#     Profiel_z1 = Profiel_z1.sort_index(ascending=True)
#
#     x_list = list()
#     y_list = list()
#     nr_list = list()
#
#     for l, rows in Gemeten_profielen.iterrows():
#         if ((Gemeten_profielen.CODE[l]) == hydro_object and (Gemeten_profielen.OSMOMSCH[l] == "Z2")):
#             nr = (Gemeten_profielen.IWS_VOLGNR[l])
#             x = (Gemeten_profielen.x_gp[l])
#             y = (Gemeten_profielen.y_gp[l])
#
#             x_list.append(x)
#             y_list.append(y)
#             nr_list.append(nr)
#
#     x_ser = pd.Series(x_list, index=nr_list, name='x')
#     y_ser = pd.Series(y_list, index=nr_list, name='y')
#
#     Profiel_z2 = pd.concat([x_ser, y_ser], axis=1)
#     Profiel_z2 = Profiel_z2.sort_index(ascending=True)
#
#     if (len(x_list) > 0):
#         plt.plot(Profiel_z2.x, Profiel_z2.y, color='#cb7723', linewidth=2, label="Gemeten profiel baggerlaag")
#         plt.plot(Profiel_z1.x, Profiel_z1.y, color='#653700', linewidth=2, label="Gemeten profiel vaste bodem")
#
#     else:
#         # Dit zijn twee verticale lijnen om de oevers aan te geven.
#         x3 = [0, (Max_diepte * talud)]
#         y3 = [streefpeil, streefpeil - 1 * Max_diepte]
#         plt.plot(x3, y3, color='black', linewidth=2, label='Linkeroever')
#
#         x4 = [(Max_breedte), (Max_breedte - (Max_diepte * talud))]
#         y4 = [streefpeil, streefpeil - 1 * Max_diepte]
#         plt.plot(x4, y4, color='black', linewidth=2, label='Rechteroever')
#
#     # hier wordt aan elke plot een titel en een legenda toegevoegd
#     plt.title(hydro_object)
#
#     # Hier wordt de legenda gegenereerd.
#     axis = plt.subplot(111)
#     axis.legend(loc='lower right', bbox_to_anchor=(1.5, 0), fancybox=True, shadow=True, ncol=1)
#
#     # Figuur direct laten zien of opslaan
#     plt.show()
#     # plt.savefig(hydro_object, format='png')
#
# end = time.time()
# print ("Klaar in " + str(end - start) + " seconden.")