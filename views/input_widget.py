"""
    Interface for adding profiles
"""

from qgis.PyQt import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
from legger.sql_models.legger import Varianten
from legger.utils.theoretical_profiles import calc_pitlo_griffioen
from legger.sql_models.legger import BegroeiingsVariant

# try:
#     _fromUtf8 = QtCore.QString.fromUtf8
# except AttributeError:
#     def _fromUtf8(s):
#         return s
#
# try:
#     _encoding = QtGui.QApplication.UnicodeUTF8
#
#
#     def _translate(context, text, disambig):
#         return QtGui.QApplication.translate(context, text, disambig, _encoding)
# except AttributeError:
#     def _translate(context, text, disambig):
#         return QtGui.QApplication.translate(context, text, disambig)


class LeggerPlotWidget(pg.PlotWidget):
    def __init__(self, parent=None, name=""):
        super(LeggerPlotWidget, self).__init__(parent)
        self.name = name
        self.showGrid(True, True, 0.5)
        self.setLabel("bottom", "breedte", "m")
        self.setLabel("left", "hoogte", "m tov waterlijn")

        self.series = {}
        self.hydro_object = None  # todo: verwijzing naar hydro object in kwestie

    def set_data(self, ditch_width, waterdepth, ditch_slope, ditch_bottomwidth):
        self.ditch_width = ditch_width
        self.waterdepth = waterdepth
        self.ditch_slope = ditch_slope
        self.ditch_bottomwidth = ditch_bottomwidth

        self.draw_lines()

    def draw_lines(self):
        self.clear()

        x = [
            - 0.5 * self.ditch_width,
            -0.5 * self.ditch_bottomwidth,
            0.5 * self.ditch_bottomwidth,
            0.5 * self.ditch_width
        ]

        y = [
            0,
            -1 * self.waterdepth,
            -1 * self.waterdepth,
            0
        ]

        # Todo: verbinding met bestaand gemeten profiel
        plot_item = pg.PlotDataItem(
            x=x,
            y=y,
            connect='finite',
            pen=pg.mkPen(color=(140, 0, 140), width=2)
        )
        self.addItem(plot_item)
        self.autoRange()


class NewWindow(QtWidgets.QWidget):
    def __init__(self, legger_item, db_session, callback_on_save=None):
        super(NewWindow, self).__init__()
        self._new_window = None

        self.legger_item = legger_item
        self.session = db_session
        self.callback_on_save = callback_on_save

        self.setup_ui()

        self.variants = self.session.query(BegroeiingsVariant).order_by('friction_manning')

        self.begroeiings_combo.insertItems(
            0, [v.naam for v in self.variants]
        )
        default_index = [i for i, v in enumerate(self.variants) if v.is_default]
        if len(default_index) == 0:
            default_index = 0
        else:
            default_index = default_index[0]

        self.begroeiings_combo.setCurrentIndex(default_index)
        # self.selected_variant = self.variants[default_index]

        self.ditch_width = None
        self.waterdepth = None
        self.ditch_slope = None

    def calculate(self):
        verhang_bericht = ""
        bodembreedte_bericht = ""

        try:
            self.ditch_width = float(self.input_ditch_width.value())
            self.waterdepth = float(self.input_waterdepth.value())
            self.ditch_slope = float(self.input_ditch_slope.value())
            begroeiings_variant = self.variants[self.begroeiings_combo.currentIndex()]

            self.output_info.setText('')
            self.comments.setText(str(''))

            test1 = 1 / (self.ditch_width * self.waterdepth * self.ditch_slope)  # een check of er 0 waarden zijn.

            self.ditch_bottomwidth = self.ditch_width - (self.ditch_slope * self.waterdepth) * 2

            self.plot_widget.set_data(self.ditch_width,
                                      self.waterdepth,
                                      self.ditch_slope,
                                      self.ditch_bottomwidth)

            if self.ditch_bottomwidth <= 0:
                verhang_bericht = "Verhang kan nu niet berekend worden."
                bodembreedte_bericht = "Bodembreedte is negatief of 0"
            else:
                placeholder_norm_flow = self.legger_item.hydrovak.get('flow', 0)
                self.verhang = calc_pitlo_griffioen(
                    placeholder_norm_flow,
                    self.ditch_bottomwidth,
                    self.waterdepth,
                    self.ditch_slope,
                    friction_manning=begroeiings_variant.friction_manning,
                    friction_begroeiing=begroeiings_variant.friction_begroeiing,
                    begroeiingsdeel=begroeiings_variant.begroeiingsdeel)

                bodembreedte_bericht = ("{0:.2f} cm/ km is het verhang\n"
                                        "{1:.2f} m is de bodembreedte"
                                        ).format(float(self.verhang), float(self.ditch_bottomwidth))

        except ZeroDivisionError:
            verhang_bericht = "Delen door 0!"
            bodembreedte_bericht = "Geen berekening mogelijk"

        except Exception as e:
            verhang_bericht = "Om onbekende redenen kan er geen berekening voor verhang worden gemaakt. foutmelding: {}".format(
                e.message)
            bodembreedte_bericht = "Controleer of dit hydro object alle input variabelen heeft."

        finally:
            self.output_info.setText(verhang_bericht)
            self.comments.setText(str(bodembreedte_bericht))

    def cancel_application(self):
        self.close()

    def save_and_close(self):

        if self.ditch_width is not None and self.waterdepth is not None and self.ditch_slope is not None:

            found = False
            id_value = ''
            i = 0
            while not found:
                id_value = "{hydro_id}_{depth}".format(
                    hydro_id=self.legger_item.hydrovak.get('hydro_id'),
                    depth=self.waterdepth
                )
                if i > 0:
                    id_value += '_{0}'.format(i)
                count = self.session.query(Varianten).filter(Varianten.id == id_value).count()

                if count == 0:
                    found = True
                else:
                    i += 1

            begroeiings_variant = self.variants[self.begroeiings_combo.currentIndex()]

            variant = Varianten(
                id=id_value,
                diepte=self.waterdepth,
                waterbreedte=self.ditch_width,
                bodembreedte=self.ditch_bottomwidth,
                talud=self.ditch_slope,
                verhang=self.verhang,
                opmerkingen='handmatig aangemaakt',
                begroeiingsvariant=begroeiings_variant,
                hydro_id=self.legger_item.hydrovak.get('hydro_id')
            )

            self.session.add(variant)
            self.session.commit()

            if self.callback_on_save is not None:
                self.callback_on_save(self.legger_item, variant)

        self.close()

    def setup_ui(self):

        # Scherm bestaat uit een paar hoofdonderdelen:
        # VerticalLayout als hoofd layout, bestaande uit 3 rijen:
        #   - Bovenste rij bestaat uit een Horizontal Layout met 3 kolommen:
        #       - linkerkolom bestaat uit een Vertical Layout met introtext
        #       - middenkolom bestaante uit een Vertical Layout met invoer label, invoer parameters, en Bereken knop:
        #           - invoer parameters worden als spinbox in aparte groupbox toegevoegd om een net label te geven.
        #       - en rechterkolom bestaande uit een Vertical Layout met uitvoer textbox
        #   - Middelste rij met grafische weergave van de dwarsdoorsnede als Figuur
        #   - Onderste rij is ook en Horizontal Layout met 2 knoppen naast elkaar: Opslaan en Annuleren

        # Hoofd layout definieren
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setObjectName("verticalLayout")

        # Bovenste rij in hoofd layout definieren
        self.upper_row = QtWidgets.QHBoxLayout()
        self.upper_row.setObjectName("Upper row")

        # Linker kolom in bovenste rij definitie
        self.left_column = QtWidgets.QVBoxLayout()
        self.left_column.setObjectName("Left column")

        # Intro text
        self.intro_text = QtWidgets.QTextEdit(self)
        self.intro_text.setText("Hier kun je zelf een profiel definieren.\n"
                                "Vul van boven naar beneden een waarde in voor:\n"
                                "- Waterbreedte;\n"
                                "- Waterdiepte;\n"
                                "- Talud.\n\n"
                                "Met de knop 'Bereken' kun je het nieuwe profiel doorrekenen.\n"
                                "Als het profiel naar behoeven is, druk dan op 'Opslaan' om het profiel op te nemen in de database.\n"
                                "Om het scherm te verlaten kan op 'Annuleren' gedrukt worden.")
        self.intro_text.setObjectName("introductie_text")

        self.left_column.addWidget(self.intro_text)  # introtext toevoegen aan linkerkolom

        # Middelste kolom in bovenste rij
        self.middle_column = QtWidgets.QVBoxLayout()
        self.middle_column.setObjectName("middelste_kolom")

        # Invoer van parameters
        # Titel
        self.input_label = QtWidgets.QLabel(self.tr("Invoer van parameters:"))
        self.middle_column.addWidget(self.input_label)  # label toevoegen aan middenkolom

        # Spinbox waterbreedte
        self.input_ditch_width = QtWidgets.QDoubleSpinBox(self)
        self.input_ditch_width.setSuffix(" m")
        self.input_ditch_width.setSingleStep(0.1)
        self.input_ditch_width.setObjectName("Invoer_waterbreedte")

        self.groupBox_ditch_width = QtWidgets.QGroupBox(self)
        self.groupBox_ditch_width.setTitle("Waterbreedte")

        self.vbox_ditch_width = QtWidgets.QVBoxLayout()
        self.vbox_ditch_width.addWidget(self.input_ditch_width)
        self.groupBox_ditch_width.setLayout(self.vbox_ditch_width)

        self.middle_column.addWidget(self.groupBox_ditch_width)  # waterbreedte spinner toevoegen

        # Spinbox waterdiepte
        self.input_waterdepth = QtWidgets.QDoubleSpinBox(self)
        self.input_waterdepth.setSuffix(" m")
        self.input_waterdepth.setSingleStep(0.1)
        self.input_waterdepth.setObjectName("Invoer_waterdiepte")

        self.groupBox_waterdepth = QtWidgets.QGroupBox(self)
        self.groupBox_waterdepth.setTitle("Waterdiepte")

        self.vbox_waterdepth = QtWidgets.QVBoxLayout()
        self.vbox_waterdepth.addWidget(self.input_waterdepth)
        self.groupBox_waterdepth.setLayout(self.vbox_waterdepth)

        self.middle_column.addWidget(self.groupBox_waterdepth)  # waterdiepte spinner toevoegen aan midden kolom

        # Spinbox talud
        self.input_ditch_slope = QtWidgets.QDoubleSpinBox(self)
        self.input_ditch_slope.setSuffix(" m breedte / m hoogteverschil")
        self.input_ditch_slope.setSingleStep(0.1)
        self.input_ditch_slope.setValue(1)  # initieel 1:1
        self.input_ditch_slope.setObjectName("Invoer_talud")

        self.groupBox_ditch_slope = QtWidgets.QGroupBox(self)
        self.groupBox_ditch_slope.setTitle("Talud")

        self.vbox_ditch_slope = QtWidgets.QVBoxLayout()
        self.vbox_ditch_slope.addWidget(self.input_ditch_slope)

        self.groupBox_ditch_slope.setLayout(self.vbox_ditch_slope)

        self.middle_column.addWidget(self.groupBox_ditch_slope)  # talud spinner toevoegen aan midden kolom

        # begroeiings selection
        self.begroeiings_combo = QtWidgets.QComboBox(self)
        self.groupBox_begroeiing = QtWidgets.QGroupBox(self)
        self.groupBox_begroeiing.setTitle("Begroeiingsgraad")
        self.vbox_begroeiing = QtWidgets.QVBoxLayout()
        self.vbox_begroeiing.addWidget(self.begroeiings_combo)
        self.groupBox_begroeiing.setLayout(self.vbox_begroeiing)

        self.middle_column.addWidget(self.groupBox_begroeiing)

        # Bereken
        self.calc_button = QtWidgets.QPushButton()
        self.calc_button.setObjectName("Bereken_knop")
        self.calc_button.clicked.connect(self.calculate)
        self.middle_column.addWidget(self.calc_button)  # bereken knop toevoegen aan midden kolom

        # Verticale Spacer om alles naar boven te drukken.
        spacerItem_middle_column = QtWidgets.QSpacerItem(10, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.middle_column.addItem(spacerItem_middle_column)

        # Rechterkolom
        self.right_column = QtWidgets.QVBoxLayout()
        self.right_column.setObjectName("Rechter Kolom")

        self.output_info = QtWidgets.QTextEdit(self)
        self.output_info.setObjectName("output_info")

        self.right_column.addWidget(self.output_info)

        self.comments = QtWidgets.QTextEdit(self)
        self.comments.setObjectName("opmerkingen")

        self.right_column.addWidget(self.comments)

        # Verticale kolommen toevoegen aan de bovenste rij (horizontale lay-out)
        self.upper_row.addLayout(self.left_column)  # kolom met introtext en invoer parameters toevoegen
        self.upper_row.addLayout(self.middle_column)
        self.upper_row.addLayout(self.right_column)  # kolom met output toevoegen

        # Horizontale bovenste rij toevoegen aan bovenkant verticale HOOFD layout.
        self.verticalLayout.addLayout(self.upper_row)

        # FIGUREN MAKEN
        # Figuur vlak aanmaken
        self.plot_widget = LeggerPlotWidget(self)
        self.plot_widget.setObjectName("Figuur")

        # Figuurvlak toevoegen in het MIDDEN van de HOOFD lay-out.
        self.verticalLayout.addWidget(self.plot_widget)

        # OPSLAAN / ANNULEREN KNOPPEN
        # Vlak maken voor de knoppen
        self.bottom_row = QtWidgets.QHBoxLayout()  # knoppen komen naast elkaar dus een horizontal layout.
        self.bottom_row.setObjectName("Bottom_row")

        # Sluiten knop
        self.cancel_button = QtWidgets.QPushButton(self)
        self.cancel_button.setObjectName("Sluiten")
        self.cancel_button.clicked.connect(self.cancel_application)
        self.bottom_row.addWidget(self.cancel_button)

        # Opslaan knop
        self.save_button = QtWidgets.QPushButton(self)
        self.save_button.setObjectName("Opslaan")
        self.save_button.clicked.connect(self.save_and_close)
        self.bottom_row.addWidget(self.save_button)

        # Opslaan / Annuleer knoppen toevoegen aan onderkant verticale HOOFD layout
        self.verticalLayout.addLayout(self.bottom_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle("Dialog")

        self.calc_button.setText("Berekenen")
        self.save_button.setText("Opslaan en sluiten")
        self.cancel_button.setText("Annuleer")


