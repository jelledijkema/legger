# todo:
#  - 'opstuwingsnorm' selection?
#  - correct or selectable friction values


# -*- coding: utf-8 -*-
from __future__ import division

import logging

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QComboBox, QWidget
from legger.sql_models.legger import BegroeiingsVariant, HydroObject, get_or_create
from legger.sql_models.legger_database import LeggerDatabase
from legger.sql_models.legger_views import create_legger_views
from legger.utils.profile_match_a import doe_profinprof, maaktabellen
from legger.utils.read_tdi_results import (get_timestamps, read_tdi_culvert_results, read_tdi_results,
                                           write_tdi_culvert_results_to_db, write_tdi_results_to_db)
from legger.utils.snap_points import snap_points
from legger.utils.theoretical_profiles import Kb, create_theoretical_profiles, write_theoretical_profile_results_to_db
from pyspatialite import dbapi2 as dbapi

log = logging.getLogger(__name__)

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class ProfileCalculationWidget(QWidget):  # , FORM_CLASS):
    """Dialog for making the pre-process steps for the Legger"""
    closingDialog = pyqtSignal()

    def __init__(
            self, parent, iface, polder_datasource, ts_datasource,
            parent_class):
        """Constructor

        parent (QtWidget): Qt parent Widget
        iface (QgisInterface: QGiS interface
        polder_datasource (str): Path to the 'legger' spatialite of a polder
        ts_datasource (TimeseriesDatasourceModel): 3di datasource of results
        parent_class: the tool class which instantiated this widget. Is used
             here for storing volatile information
        returns: None
        """
        super(ProfileCalculationWidget, self).__init__(parent)

        self.parent_class = parent_class
        self.iface = iface
        self.polder_datasource = polder_datasource
        self.ts_datasource = ts_datasource
        self.timestep = -1
        self.surge_selection = -1

        errormessage = "Kies eerst 3di output (model en netCDF) in de 'Select 3di results' van 3di plugin."
        try:
            self.path_model_db = self.ts_datasource.model_spatialite_filepath
        except:
            self.path_model_db = errormessage

        try:
            self.path_result_db = self.ts_datasource.rows[0].spatialite_cache_filepath().replace('\\', '/')
        except:
            self.path_result_db = errormessage

        try:
            self.path_result_nc = self.ts_datasource.rows[0].file_path.value
        except:
            self.path_result_nc = errormessage

        if self.path_model_db is None:
            self.path_model_db = errormessage

        # timestep combobox
        self.last_timestep_text = 'laatste tijdstap'
        self.timestamps = []

        try:
            self.timestamps = get_timestamps(self.path_result_nc)
        except:
            pass

        self.setup_ui()

        # fill timestep combobox
        choices = [self.last_timestep_text] + ['%.0f' % t for t in self.timestamps]
        self.timestep_combo_box.insertItems(0, choices)
        self.timestep_combo_box.setCurrentIndex(0)

        # set time combobox listeners
        self.timestep_combo_box.currentIndexChanged.connect(
            self.timestep_selection_change)

        # surge combobox
        self.last_surge_text = "kies opstuwingsnorm"

        # fill surge combobox
        surge_choices = [self.last_surge_text] + ['%s' % s for s in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]]
        self.surge_combo_box.insertItems(0, surge_choices)
        self.surge_combo_box.setCurrentIndex(0)

        # set surge combobox listeners
        self.surge_combo_box.currentIndexChanged.connect(
            self.surge_selection_change)

    def timestep_selection_change(self, nr):
        """Proces new selected timestep in combobox

        :param nr:
        :return:
        """
        text = self.timestep_combo_box.currentText()
        if text == self.last_timestep_text:
            self.timestep = -1
        else:
            self.timestep = nr - 1

    def surge_selection_change(self, nr):
        """Proces new selected timestep in combobox

        :param nr:
        :return:
        """
        text = self.surge_combo_box.currentText()
        if text == self.last_surge_text:
            self.surge_selection = 3.0
        else:
            self.surge_selection = text

    def closeEvent(self, event):
        """
        event (QtEvent): event triggering close
        returns: None
        """
        # set listeners
        self.timestep_combo_box.currentIndexChanged.disconnect(
            self.timestep_selection_change)

        self.closingDialog.emit()
        self.close()
        event.accept()

    def save_spatialite(self):
        """Change active modelsource. Called by combobox when selected
        spatialite changed
        returns: None
        """

        self.close()

    def explain_step1(self):
        """
        Uitleg van stap 1
        """
        # detailed information on UPPER ROW groupbox
        self.msg_upper_row = QtGui.QMessageBox(self)
        self.msg_upper_row.setIcon(QtGui.QMessageBox.Information)
        self.msg_upper_row.setText("<b>Het selecteren van een tijdstap voor de leggerdatabase<b>")
        self.msg_upper_row.setInformativeText("In het netCDF bestand waar de 3di resultaten zijn opgeslagen is per "
                                              "'flowline' voor elke tijdstap informatie beschikbaar. Dit betekent dat "
                                              "eerst een tijdstap gekozen moet worden om de resultaten van deze tijdstap "
                                              "op te kunnen halen.\n"
                                              "In het geval van de hydraulische toets, wat gebruikt wordt voor de legger, "
                                              "zijn we geinteresseerd in de debieten over de 'flowlines' waarbij "
                                              "de neerslag som een stationair evenwicht heeft berijkt.\n\n"
                                              "Tip: In de BWN studie rekenen we een som door van 1 dag droog, 5 "
                                              "dagen regen en weer 2 dagen droog. Voor het meest stationaire moment "
                                              "selecteer de tijdstap tussen ongeveer 2/3 en 3/4 van de grootste tijdstap")

        self.box_step1.addWidget(self.msg_upper_row)

    def execute_step1(self):
        """
       Eerste stap in klaarzetten van de data:
        - update legger database met data vanuit de netcdf (koppeling debieten van gekozen tijdstap)
        returns: None
        """
        # first update legger spatialite according to schema, using sqlAlchemy
        db = LeggerDatabase(
            {
                'db_path': self.polder_datasource
            },
            'spatialite'
        )
        # db.create_and_check_fields()
        # do one query, don't know what the reason was for this...
        session = db.get_session()
        session.query(HydroObject)

        timestamp = 'laatst' if self.timestep == 0 else '{0} op {1:.0f} s'.format(self.timestep + 1,
                                                                                  self.timestamps[self.timestep])
        self.feedbackmessage = 'Neem tijdstap {0}'.format(timestamp)

        # try:
        if True:
            # read 3di channel results
            result = read_tdi_results(
                self.path_model_db,
                self.path_result_db,
                self.path_result_nc,
                self.polder_datasource,
                self.timestep
            )
            self.feedbackmessage += "\nDatabases zijn gekoppeld."

        # except Exception, e:
        #     self.feedbackmessage += "\nDatabases zijn niet gekoppeld. melding: {0}\n".format(e.message)
        # finally:
        #     self.feedbacktext.setText(self.feedbackmessage)

        try:
            # write 3di channel result to legger spatialite
            write_tdi_results_to_db(
                result,
                self.polder_datasource)

            con_legger = dbapi.connect(self.polder_datasource)
            create_legger_views(con_legger)

            self.feedbackmessage = self.feedbackmessage + "\n3Di resultaten weggeschreven naar polder database."
        except:
            self.feedbackmessage = self.feedbackmessage + "\nFout in wegschrijven 3Di resultaten naar polder database."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            # read 3di culvert results
            culv_results = read_tdi_culvert_results(
                self.path_model_db,
                self.path_result_db,
                self.path_result_nc,
                self.polder_datasource,
                self.timestep
            )
            self.feedbackmessage = self.feedbackmessage + "\n3Di culverts ingelezen."
        except:
            self.feedbackmessage = self.feedbackmessage + "\nFout, 3Di culverts niet ingelezen."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

        try:
            # write 3di culvert results to legger spatialite
            write_tdi_culvert_results_to_db(culv_results,
                                            self.polder_datasource)
            self.feedbackmessage = self.feedbackmessage + "\n3Di culvert resultaten weggeschreven."
        except:
            self.feedbackmessage = self.feedbackmessage + "\nFout, 3Di culvert resultaten niet weggeschreven."
        finally:
            self.feedbacktext.setText(self.feedbackmessage)

    def explain_step2(self):
        """
        Uitleg van stap 1
        """
        # detailed information on UPPER ROW groupbox
        self.msg_middle_row = QtGui.QMessageBox(self)
        self.msg_middle_row.setIcon(QtGui.QMessageBox.Information)
        self.msg_middle_row.setText("<b>Het berekenen van de varianten voor de leggerdatabase<b>")
        self.msg_middle_row.setInformativeText("Alle randvoorwaarden zijn nu bekend:\n"
                                               "breedte, diepte, Q, talud.\n"
                                               "Met de gekozen norm voor verhang wordt met iteraties berekend "
                                               "welke mogelijke leggerprofielen er mogelijk zijn. Dit betekent dat "
                                               "per hydro-object idealiter een hele lijst van 'mogelijke profielen' "
                                               "wordt berekend. Dat betekent dat er vanuit hydraulisch oogpunt dus "
                                               "ruimte is voor keuze.\n"
                                               "Let op: als een bestaande 'leggerdatabase' is ingelezen, dan kan het "
                                               "zo zijn dat door deze actie uit te voeren bestaande varianten worden "
                                               "overschreven met nieuwe (omdat randvoorwaarde verhang nu anders is.")

        self.box_step2.addWidget(self.msg_middle_row)

    def execute_step2(self):

        db = LeggerDatabase(
            {
                'db_path': self.polder_datasource
            },
            'spatialite'
        )
        db.create_and_check_fields()
        # do one query, don't know what the reason was for this...
        session = db.get_session()

        # delete existing variants
        # session.execute("Verwijder van varianten")
        # session.execute("Verwijder begroeiingsvariant")
        session.commit()

        get_or_create(session, BegroeiingsVariant, naam='standaard',
                      defaults={'friction': Kb, 'is_default': True})

        get_or_create(session, BegroeiingsVariant, naam='deels begroeid',
                      defaults={'friction': 0.75 * Kb})

        get_or_create(session, BegroeiingsVariant, naam='sterk begroeid',
                      defaults={'friction': 0.5 * Kb})
        session.commit()

        for bv in session.query(BegroeiingsVariant).all():

            try:
                profiles = create_theoretical_profiles(self.polder_datasource, bv)
                self.feedbackmessage = "Profielen zijn berekend."
            except:
                self.feedbackmessage = "Fout, profielen konden niet worden berekend."
            finally:
                self.feedbacktext.setText(self.feedbackmessage)

            try:
                write_theoretical_profile_results_to_db(session, profiles, bv)
                self.feedbackmessage = self.feedbackmessage + ("\nProfielen opgeslagen in legger db.")
            except:
                self.feedbackmessage = self.feedbackmessage + ("\nFout, profielen niet opgeslagen in legger database.")
            finally:
                self.feedbacktext.setText(self.feedbackmessage)

    def execute_step3(self):

        con_legger = dbapi.connect(self.polder_datasource)
        maaktabellen(con_legger.cursor())
        con_legger.commit()
        doe_profinprof(con_legger.cursor(), con_legger.cursor())
        con_legger.commit()

        self.feedbacktext.setText("De fit % zijn berekend.")

    def execute_snap_points(self):
        con_legger = dbapi.connect(self.polder_datasource)
        snap_points(con_legger.cursor())

        self.feedbacktext.setText("De punten zijn gesnapt.")

    def execute_pre_fill(self):
        self.feedbacktext.setText("Waarschuwing: nog niet geimplementeerd")

    def setup_ui(self):
        self.verticalLayout = QtGui.QVBoxLayout(self)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))

        self.information_row = QtGui.QHBoxLayout()
        self.information_row.setObjectName(_fromUtf8("Information row"))
        self.upper_row = QtGui.QHBoxLayout()
        self.upper_row.setObjectName(_fromUtf8("Upper row"))
        self.middle_row = QtGui.QHBoxLayout()
        self.middle_row.setObjectName(_fromUtf8("Middle row"))
        self.bottom_row = QtGui.QHBoxLayout()
        self.bottom_row.setObjectName(_fromUtf8("Bottom row"))
        self.feedback_row = QtGui.QHBoxLayout()
        self.feedback_row.setObjectName(_fromUtf8("Feedback row"))
        self.exit_row = QtGui.QHBoxLayout()
        self.exit_row.setObjectName(_fromUtf8("Exit row"))

        # Selected file name and location in INFORMATION ROW groupbox
        self.polder_filename = QtGui.QLineEdit(self)
        self.polder_filename.setText(self.polder_datasource)
        self.polder_filename.setObjectName(_fromUtf8("polder legger filename"))

        self.model_filename = QtGui.QLineEdit(self)
        self.model_filename.setText(self.path_model_db)
        self.model_filename.setObjectName(_fromUtf8("model filename"))

        self.result_filename = QtGui.QLineEdit(self)
        self.result_filename.setText(self.path_result_nc)
        self.result_filename.setObjectName(_fromUtf8("result filename"))

        self.connection_filename = QtGui.QLineEdit(self)
        self.connection_filename.setText(self.path_result_db)
        self.connection_filename.setObjectName(_fromUtf8("connection filename"))

        # Assembling INFORMATION ROW groubox
        self.box_info = QtGui.QVBoxLayout()
        self.box_info.addWidget(self.polder_filename)  # intro text toevoegen aan box.
        self.box_info.addWidget(self.model_filename)
        self.box_info.addWidget(self.result_filename)
        self.box_info.addWidget(self.connection_filename)

        self.groupBox_info = QtGui.QGroupBox(self)
        self.groupBox_info.setTitle("Bestanden gekozen:")
        self.groupBox_info.setLayout(self.box_info)  # box toevoegen aan groupbox
        self.information_row.addWidget(self.groupBox_info)

        # timestep selection for UPPER ROW groupbox:
        self.timestep_combo_box = QComboBox(self)

        # Assembling step 1 row
        self.step1_button = QtGui.QPushButton(self)
        self.step1_button.setObjectName(_fromUtf8("stap1"))
        self.step1_button.clicked.connect(self.execute_step1)
        self.step1_explanation_button = QtGui.QPushButton(self)
        self.step1_explanation_button.setObjectName(_fromUtf8("uitleg_stap1"))
        self.step1_explanation_button.clicked.connect(self.explain_step1)

        self.groupBox_step1 = QtGui.QGroupBox(self)
        self.groupBox_step1.setTitle("stap 1: Kies een tijdstap")
        self.box_step1 = QtGui.QVBoxLayout()
        self.box_step1.addWidget(self.timestep_combo_box)
        self.box_step1.addWidget(self.step1_button)
        self.box_step1.addWidget(self.step1_explanation_button)
        self.groupBox_step1.setLayout(self.box_step1)  # box toevoegen aan groupbox
        self.upper_row.addWidget(self.groupBox_step1)

        # surge selection:
        self.surge_combo_box = QComboBox(self)

        # Assembling step 2 row
        self.step2_button = QtGui.QPushButton(self)
        self.step2_button.setObjectName(_fromUtf8("stap2"))
        self.step2_button.clicked.connect(self.execute_step2)
        self.step2_explanation_button = QtGui.QPushButton(self)
        self.step2_explanation_button.setObjectName(_fromUtf8("uitleg_stap2"))
        self.step2_explanation_button.clicked.connect(self.explain_step2)

        self.groupBox_step2 = QtGui.QGroupBox(self)
        self.groupBox_step2.setTitle("stap2: bereken de varianten")
        self.box_step2 = QtGui.QVBoxLayout()
        self.box_step2.addWidget(self.surge_combo_box)
        self.box_step2.addWidget(self.step2_button)
        self.box_step2.addWidget(self.step2_explanation_button)
        self.groupBox_step2.setLayout(self.box_step2)  # box toevoegen aan groupbox
        self.middle_row.addWidget(self.groupBox_step2)

        # Assembling step 3 row
        self.step3_button = QtGui.QPushButton(self)
        self.step3_button.setObjectName(_fromUtf8("Stap 3"))
        self.step3_button.clicked.connect(self.execute_step3)
        self.groupBox_step3 = QtGui.QGroupBox(self)
        self.groupBox_step3.setTitle("Step3:")
        self.box_step3 = QtGui.QHBoxLayout()
        self.box_step3.addWidget(self.step3_button)
        self.groupBox_step3.setLayout(self.box_step3)  # box toevoegen aan groupbox
        self.bottom_row.addWidget(self.groupBox_step3)

        # Assembling step 4 row
        self.snap_points_button = QtGui.QPushButton(self)
        self.snap_points_button.setObjectName(_fromUtf8("Snap points"))
        self.snap_points_button.clicked.connect(self.execute_snap_points)
        self.groupBox_snap_points = QtGui.QGroupBox(self)
        self.groupBox_snap_points.setTitle("Stap 4:")
        self.box_snap_points = QtGui.QHBoxLayout()
        self.box_snap_points.addWidget(self.snap_points_button)
        self.groupBox_snap_points.setLayout(self.box_snap_points)  # box toevoegen aan groupbox
        self.bottom_row.addWidget(self.groupBox_snap_points)

        # Assembling step 5 row
        self.pre_fill_button = QtGui.QPushButton(self)
        self.pre_fill_button.setObjectName(_fromUtf8("Snap points"))
        self.pre_fill_button.clicked.connect(self.execute_pre_fill)
        self.groupBox_pre_fill = QtGui.QGroupBox(self)
        self.groupBox_pre_fill.setTitle("Stap 5:")
        self.box_pre_fill = QtGui.QHBoxLayout()
        self.box_pre_fill.addWidget(self.pre_fill_button)
        self.groupBox_pre_fill.setLayout(self.box_pre_fill)  # box toevoegen aan groupbox
        self.bottom_row.addWidget(self.groupBox_pre_fill)

        # Assembling feedback row
        self.feedbacktext = QtGui.QTextEdit(self)
        self.feedbackmessage = "Nog geen berekening uitgevoerd"
        self.feedbacktext.setText(self.feedbackmessage)
        self.feedbacktext.setObjectName(_fromUtf8("feedback"))

        self.feedback_row.addWidget(self.feedbacktext)

        # Assembling exit row
        self.cancel_button = QtGui.QPushButton(self)
        self.cancel_button.setObjectName(_fromUtf8("Cancel"))
        self.cancel_button.clicked.connect(self.close)
        self.exit_row.addWidget(self.cancel_button)

        self.save_button = QtGui.QPushButton(self)
        self.save_button.setObjectName(_fromUtf8("Close"))
        self.save_button.clicked.connect(self.save_spatialite)
        self.exit_row.addWidget(self.save_button)

        # Lay-out in elkaar zetten.
        self.verticalLayout.addLayout(self.information_row)
        self.verticalLayout.addLayout(self.upper_row)
        self.verticalLayout.addLayout(self.middle_row)
        self.verticalLayout.addLayout(self.bottom_row)
        self.verticalLayout.addLayout(self.feedback_row)
        self.verticalLayout.addLayout(self.exit_row)

        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Bereken de profielvarianten van de polder",
                                         None))  # todo: maak een merge met de poldernaam.
        self.save_button.setText(_translate("Dialog", "Opslaan en sluiten", None))
        self.step1_explanation_button.setText(_translate("Dialog", "Uitleg stap 1", None))
        self.step1_button.setText(_translate("Dialog", "Verbindt resultaten van netCDF aan de hydro-objecten", None))
        self.step2_explanation_button.setText(_translate("Dialog", "Uitleg stap 2", None))
        self.step2_button.setText(_translate("Dialog", "Bereken alle mogelijke leggerprofielen", None))
        self.step3_button.setText(
            _translate("Dialog", "Bereken de fit van de berekende profielen", None))
        self.snap_points_button.setText(
            _translate("Dialog", "Snap eindpunten van lijnen", None))

        self.pre_fill_button.setText(
            _translate("Dialog", "Vul profielen in waar duidelijk", None))

        self.cancel_button.setText(_translate("Dialog", "Cancel", None))
