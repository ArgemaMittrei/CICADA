import os
import sys
import numpy as np

import scheme as sch
import scheme.gui as design
import scheme.ldpc as ldpc
import scheme.spectral as spectral
import scheme.hemming_space as hemming
import scheme.clusterization as cluster

from datetime import *
from time import time as t
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QColor, QIcon

pathname = os.getcwd()


def actAbout():
    about = QMessageBox()
    about.setWindowTitle('About')
    about.setText('CICADA: Tool to Design Circuits with Error Correction and Detection Abilities!\n\n'+
                  'This program allows you to determine best method for the synthesis of CED\n'+
                  'for a specific combination scheme based on its main characteristics.\n\n' +
                  'Author:\n' + 'ZHukova T.D. (IPPM RAS)\n' + 'zhukova_t@ippm.ru')
    about.exec_()


class AppSystemCED(QMainWindow, design.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.actionOpen.triggered.connect(self.actMenuOpenFile)
        self.actionExit.triggered.connect(qApp.quit)
        self.actionAbout.triggered.connect(actAbout)
        self.path = None
        self.circuit = None
        self.constraint = None
        self.filename = None

        dt = datetime.now()
        start_date = 'Start program - {}.{}.{}'.format(dt.day, dt.month, dt.year)
        start_time = 'Time - {:02d}:{:02d}:{:02d}'.format(dt.hour, dt.minute, dt.second)

        self.textEdit.setText(start_date + '\n' + start_time + '\n' + '\n' +
                              'To start working with program, need to open the circuit file, enter constraint on '
                              'structural redundancy, and then select the synthesis methods of CED circuit for which '
                              'you want to perform analyze.\n\nPress Start button to determine the best synthesis '
                              'method for received combinational circuit, taking into account the entered constraint.')

        self.pushButton.clicked.connect(self.actStart)

    def actMenuOpenFile(self):
        self.path = QFileDialog.getOpenFileName(None, 'Open file...', '', 'Text files, *.txt')[0]
        filename = os.path.normpath(self.path).split(os.sep)
        self.filename = filename[len(filename)-1][:-4]

    def actStart(self):
        # ==============================================================================================================
        p1, p2, p3, p4, f4 = 0.2, 0.1, 0.02, 0.009, 0.2
        ced_hemming = None
        ced_spectral = None
        ced_spectral_2 = None
        ced_spectral_4 = None
        rel_spectral = None
        ced_ldpc = None
        ced_ldpc_2 = None
        ced_ldpc_4 = None
        rel_ldpc = None
        rel_result = None
        result = None
        error_1 = False
        coders = None
        decoders = None
        # correlation_matrix = None
        # ==============================================================================================================
        options = [False, False]
        if self.checkBox_5.checkState() == 2: options[0] = True     # Log file
        if self.checkBox_6.checkState() == 2: options[1] = True     # Verilog file
        # ==============================================================================================================
        mtd = [False, False, False, False]
        if self.checkBox.checkState() == 2:     mtd[0] = True       # Clusterization
        if self.checkBox_4.checkState() == 2:   mtd[1] = True       # 3bits Hemming space
        if self.checkBox_3.checkState() == 2:   mtd[2] = True       # Spectral R-code
        if self.checkBox_2.checkState() == 2:   mtd[3] = True       # LDPC code
        # ==============================================================================================================
        if not self.path:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('Combinational circuit is not received.')
            return
        # ==============================================================================================================
        if mtd[0] and not mtd[3] and not mtd[2]:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('To perform clusterization, select method based on spectral or LDPC codes.')
            return
        # ==============================================================================================================
        if not mtd[3] and not mtd[2] and not mtd[1]:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('To perform analysis, select synthesis methods of CED circuit.')
            return
        # ==============================================================================================================
        dt = datetime.now()
        start_time = 'Start time - {:02d}:{:02d}:{:02d}'.format(dt.hour, dt.minute, dt.second)
        # ==============================================================================================================
        self.textEdit.setTextColor(QColor(0, 0, 0))
        self.textEdit.append('\n' + start_time + '\n')
        self.textEdit.append('Combinational circuit is received:')
        self.circuit = sch.read_scheme(self.path)
        self.textEdit.append(self.path)
        # ==============================================================================================================
        if mtd[2] and self.circuit.outputs() < 2:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('For this combinational circuit, it is not possible to generate a CED circuit based on'
                                 ' Spectral R-code.')
            error_1 = True
        # ==============================================================================================================
        if mtd[3] and self.circuit.outputs() < 3:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('For this combinational circuit, it is not possible to generate a CED circuit based on'
                                 ' LDPC code.')
            error_1 = True
        # ==============================================================================================================
        if error_1: return
        # ==============================================================================================================
        if mtd[0] and self.circuit.outputs() < 10:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('For this combinational circuit, it is not possible to perform clustarization.')
            return
        # ==============================================================================================================
        self.constraint = self.spinBox.value()
        if self.constraint == 0:
            self.textEdit.setTextColor(QColor(255, 0, 0))
            self.textEdit.append('Constraint on the value of structural redundancy is not received.')
            return
        # ==============================================================================================================
        t1 = round(float(t()), 2)
        # ==============================================================================================================
        self.textEdit.setTextColor(QColor(0, 0, 0))
        self.textEdit.append('Constraint on the value of structural redundancy is received:')
        self.textEdit.append(str(self.constraint))
        # ==============================================================================================================
        self.textEdit.append('Determining main characteristics of combinational circuit:')
        # ==============================================================================================================
        inp = self.circuit.inputs()
        k = self.circuit.outputs()
        n = self.circuit.elements()
        self.textEdit.append('PO = {}'.format(str(k)))
        self.textEdit.append('PI = {}'.format(str(inp)))
        self.textEdit.append('Structure redundancy = {}'.format(str(n)))
        # ==============================================================================================================
        if mtd[1]:
            self.textEdit.append('CED circuit based on coding in 3bits Hemming space:')
            num = 0
            for element in self.circuit.__elements__:
                element_type = self.circuit.__elements__[element][0]
                if element_type == 'BUF' or element_type == 'INV':  num += 1
            ced_hemming = 27 * n - 15 * num + 4 * k
            self.textEdit.append('Structure redundancy =  {}'.format(str(ced_hemming)))
        # ==============================================================================================================
        if mtd[3]:
            self.textEdit.append('CED circuit based on LDPC code:')
            ced_ldpc = 2 * n + 7 * k
            self.textEdit.append('Structure redundancy =  {}'.format(str(ced_ldpc)))
            beta_1 = n / ced_ldpc
            rel_ldpc = beta_1 * (p1 + p2 + p3 + p4) + 4 * k / ced_ldpc * 0.75
            self.textEdit.append('Reliability characteristic =  {}%'.format(str(round(rel_ldpc * 100, 2))))
        # ==============================================================================================================
        if mtd[2]:
            self.textEdit.append('CED circuit based on Spectral R-code:')
            m = int(np.ceil(np.log2(k))) + 1
            xor = 0
            gx = list(np.sum(spectral.matrix_gx(self.circuit.outputs(), m - 1), 1))
            for i in gx:
                if i >= 2:
                    xor += i - 1
            ced_spectral = 2 * n + 2 * xor + 3 * m + m * k + 2 * k + 2
            self.textEdit.append('Structure redundancy =  {}'.format(str(ced_spectral)))
            beta_2 = n / (ced_spectral - n - k + 1)
            rel_spectral = beta_2 * p3 + beta_2 * p4 * f4 + k / (ced_spectral - n - k + 1) + (
                    1 - (2 ** (2 * k + 1) - 1) / (2 ** (3 * k + 1) - 1)) * ((3 * k + 1) / (ced_spectral - n - k + 1))

            self.textEdit.append('Reliability characteristic =  {}%'.format(str(round(rel_spectral * 100, 2))))
        # ==============================================================================================================
        if mtd[0]:
            if mtd[3] or mtd[2]:
                self.textEdit.append('Compiling matrix of dependencies.')
                # correlation_matrix = cluster.gen_correlation_matrix(self.circuit)
                self.textEdit.append('Clusterization combinational circuit outputs into 2 groups.')
                clusters_2, groups_2 = cluster.clusterization(self.circuit, 1)
                # ======================================================================================================
                if mtd[3]:
                    self.textEdit.append('CED circuit based on LDPC code:')
                    ced_groups = 0
                    ldpc_elements, ldpc_outputs = [], []
                    for group in groups_2:
                        out_ldpc = [self.circuit.__outputs__[group[i] - 1] for i in range(len(group))]
                        if len(out_ldpc) >= 3:
                            sch_ldpc = self.circuit.subscheme_by_outputs(out_ldpc)
                            ced_groups += sch_ldpc.elements() + 7 * sch_ldpc.outputs()
                            ldpc_elements.append(sch_ldpc.elements())
                            ldpc_outputs.append(sch_ldpc.outputs())
                        else:
                            ldpc_elements.append(0)
                            ldpc_outputs.append(len(group))
                    ced_ldpc_2 = n + ced_groups
                    self.textEdit.append('Structure redundancy =  {}'.format(str(ced_ldpc_2)))
                # ======================================================================================================
                if mtd[2]:
                    self.textEdit.append('CED circuit based on Spectral R-code:')
                    spectral_groups = 0
                    xor = 0
                    m = 0
                    spectral_elements, spectral_outputs = [], []
                    for group in groups_2:
                        out_spectral = [self.circuit.__outputs__[group[i] - 1] for i in range(len(group))]
                        if len(out_spectral) >= 2:
                            sch_spectral = self.circuit.subscheme_by_outputs(out_spectral)
                            m = int(np.ceil(np.log2(sch_spectral.outputs()))) + 1
                            xor = 0
                            gx = list(np.sum(spectral.matrix_gx(sch_spectral.outputs(), m - 1), 1))
                            sp_elem = sch_spectral.elements()
                            sp_out = sch_spectral.outputs()
                            for i in gx:
                                if i >= 2:  xor += i - 1
                        else:
                            sp_elem = 0
                            sp_out = len(group)
                        spectral_elements.append(sp_elem)
                        spectral_outputs.append(sp_out)
                        spectral_groups += sp_elem + 2 * xor + 3 * m + m * sp_out + 2 * sp_out + 2
                    ced_spectral_2 = n + spectral_groups + 2
                    self.textEdit.append('Structure redundancy =  {}'.format(str(ced_spectral_2)))
                # ======================================================================================================
                self.textEdit.append('Clusterization combinational circuit outputs into 4 groups.')
                clusters_4, groups_4 = cluster.clusterization(self.circuit, 2)
                # ======================================================================================================
                if mtd[3]:
                    self.textEdit.append('CED circuit based on LDPC code:')
                    ced_groups = 0
                    ldpc_elements, ldpc_outputs = [], []
                    for group in groups_4:
                        out_ldpc = [self.circuit.__outputs__[group[i] - 1] for i in range(len(group))]
                        if len(out_ldpc) >= 3:
                            sch_ldpc = self.circuit.subscheme_by_outputs(out_ldpc)
                            ced_groups += sch_ldpc.elements() + 7 * sch_ldpc.outputs()
                            ldpc_elements.append(sch_ldpc.elements())
                            ldpc_outputs.append(sch_ldpc.outputs())
                        else:
                            ldpc_elements.append(0)
                            ldpc_outputs.append(len(group))
                    ced_ldpc_4 = n + ced_groups
                    self.textEdit.append('Structure redundancy =  {}'.format(str(ced_ldpc_4)))
                # ======================================================================================================
                if mtd[2]:
                    self.textEdit.append('CED circuit based on Spectral R-code:')
                    spectral_groups = 0
                    xor = 0
                    m = 0
                    spectral_elements, spectral_outputs = [], []
                    for group in groups_4:
                        out_spectral = [self.circuit.__outputs__[group[i] - 1] for i in range(len(group))]
                        if len(out_spectral) >= 2:
                            sch_spectral = self.circuit.subscheme_by_outputs(out_spectral)
                            m = int(np.ceil(np.log2(sch_spectral.outputs()))) + 1
                            xor = 0
                            gx = list(np.sum(spectral.matrix_gx(sch_spectral.outputs(), m - 1), 1))
                            sp_elem = sch_spectral.elements()
                            sp_out = sch_spectral.outputs()
                            for i in gx:
                                if i >= 2:  xor += i - 1
                        else:
                            sp_elem = 0
                            sp_out = len(group)
                        spectral_elements.append(sp_elem)
                        spectral_outputs.append(sp_out)
                        if sp_elem != 0:
                            spectral_groups += sp_elem + 2 * xor + 3 * m + m * sp_out + 2 * sp_out + 2
                        else:
                            spectral_groups += 0
                    ced_spectral_4 = n + spectral_groups + 6
                    self.textEdit.append('Structure redundancy =  {}'.format(str(ced_spectral_4)))
        # ==============================================================================================================
        if mtd[1] is True and ced_hemming <= self.constraint:
            self.textEdit.append('Selected method based on encoding in 3bits Hemming space.')
            result = hemming.create_hemming_circuit(self.circuit)
            rel_result = 0.00
            method = 'H'
            t2 = round(float(t()), 2)
        # ==============================================================================================================
        # Without clusterization
        # ==============================================================================================================
        elif mtd[0] is False and mtd[2] is True and mtd[3] is False:    # Spectral
            if self.constraint >= ced_spectral:
                self.textEdit.append('Selected method based on Spectral R-code.')
                result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                method = 'R'
                t2 = round(float(t()), 2)
                sim = spectral.error_simulation(result, cone, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
        elif mtd[0] is False and mtd[2] is False and mtd[3] is True:    # LDPC
            if self.constraint > ced_ldpc:
                self.textEdit.append('Selected method based on LDPC code')
                result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                method = 'L'
                t2 = round(float(t()), 2)
                sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
        elif mtd[0] is False and mtd[2] is True and mtd[3] is True:     # Spectral + LDPC
            if self.constraint >= ced_spectral and self.constraint >= ced_ldpc:
                if rel_spectral <= rel_ldpc:
                    self.textEdit.append('Selected method based on Spectral R-code.')
                    result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                    method = 'R'
                    t2 = round(float(t()), 2)
                    sim = spectral.error_simulation(result, cone, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                else:
                    self.textEdit.append('Selected method based on LDPC code.')
                    result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                    method = 'L'
                    t2 = round(float(t()), 2)
                    sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_spectral <= self.constraint:
                self.textEdit.append('Selected method based on Spectral R-code.')
                result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                method = 'R'
                t2 = round(float(t()), 2)
                sim = spectral.error_simulation(result, cone, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_ldpc <= self.constraint:
                self.textEdit.append('Selected method based on LDPC code.')
                result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                method = 'L'
                t2 = round(float(t()), 2)
                sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
                self.label_8.setText("None")
                self.label_9.setText("0")
                self.label_10.setText("0")
                self.label_11.setText("0")
                self.label_12.setText("0.00 %")
                self.label_13.setText("None")
        # ==============================================================================================================
        # With clusterization
        # ==============================================================================================================
        elif mtd[0] is True and mtd[2] is True and mtd[3] is False:             # Spectral
            if ced_spectral_4 <= self.constraint and ced_spectral_4 != n:
                self.textEdit.append('Selected method based on Spectral R-code with clusterization on 4 groups.')
                result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 2)
                method = 'R4'
                t2 = round(float(t()), 2)
                sim = spectral.error_simulation(result, cone, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_spectral_2 <= self.constraint and ced_spectral_2 != n:
                self.textEdit.append('Selected method based on Spectral R-code with clusterization on 2 groups.')
                result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 1)
                method = 'R2'
                t2 = round(float(t()), 2)
                sim = spectral.error_simulation(result, cone, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_spectral <= self.constraint:
                self.textEdit.append('Selected method based on Spectral R-code without clusterization.')
                result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                method = 'R'
                t2 = round(float(t()), 2)
                sim = spectral.error_simulation(result, cone, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
                self.label_8.setText("None")
                self.label_9.setText("0")
                self.label_10.setText("0")
                self.label_11.setText("0")
                self.label_12.setText("0.00 %")
                self.label_13.setText("None")
        elif mtd[0] is True and mtd[2] is False and mtd[3] is True:             # LDPC
            if ced_ldpc_4 <= self.constraint and ced_ldpc_4 != n:
                self.textEdit.append('Selected method based on LDPC code with clusterization on 4 groups.')
                result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 2)
                method = 'L4'
                t2 = round(float(t()), 2)
                sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_ldpc_2 <= self.constraint and ced_ldpc_2 != n:
                self.textEdit.append('Selected method based on LDPC code with clusterization on 2 groups.')
                result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 1)
                method = 'L2'
                t2 = round(float(t()), 2)
                sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            elif ced_ldpc <= self.constraint:
                self.textEdit.append('Selected method based on LDPC code without clusterization.')
                result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                method = 'L'
                t2 = round(float(t()), 2)
                sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                rel_result = round(sim[0][2] / sim[1] * 100, 2)
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
                self.label_8.setText("None")
                self.label_9.setText("0")
                self.label_10.setText("0")
                self.label_11.setText("0")
                self.label_12.setText("0.00 %")
                self.label_13.setText("None")
        elif mtd[0] is True and mtd[2] is True and mtd[3] is True:      # Spectral + LDPC
            if self.constraint >= ced_spectral and self.constraint >= ced_ldpc:
                if rel_spectral <= rel_ldpc:
                    if ced_spectral_4 <= self.constraint and ced_spectral_4 != n:
                        self.textEdit.append('Selected method based on Spectral R-code with clusterization on '
                                             '4 groups.')
                        result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 2)
                        method = 'R4'
                        t2 = round(float(t()), 2)
                        sim = spectral.error_simulation(result, cone, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    elif ced_spectral_2 <= self.constraint and ced_spectral_2 != n:
                        self.textEdit.append('Selected method based on Spectral R-code with clusterization on '
                                             '2 groups.')
                        result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 1)
                        method = 'R2'
                        t2 = round(float(t()), 2)
                        sim = spectral.error_simulation(result, cone, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    elif ced_spectral <= self.constraint:
                        self.textEdit.append('Selected method based on Spectral R-code without clusterization.')
                        result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                        method = 'R'
                        t2 = round(float(t()), 2)
                        sim = spectral.error_simulation(result, cone, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    else:
                        t2 = round(float(t()), 2)
                        self.textEdit.append(
                            'It is not possible to generate CED circuit for selected structural constraint!')
                        method = 'E'
                        self.label_8.setText("None")
                        self.label_9.setText("0")
                        self.label_10.setText("0")
                        self.label_11.setText("0")
                        self.label_12.setText("0.00 %")
                        self.label_13.setText("None")
                else:
                    if ced_ldpc_4 <= self.constraint and ced_ldpc_4 != n:
                        self.textEdit.append('Selected method based on LDPC code with clusterization on 4 groups.')
                        result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 2)
                        method = 'L4'
                        t2 = round(float(t()), 2)
                        sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    elif ced_ldpc_2 <= self.constraint and ced_ldpc_2 != n:
                        self.textEdit.append('Selected method based on LDPC code with clusterization on 2 groups.')
                        result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 1)
                        method = 'L2'
                        t2 = round(float(t()), 2)
                        sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    elif ced_ldpc <= self.constraint:
                        self.textEdit.append('Selected method based on LDPC code without clusterization.')
                        result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                        method = 'L'
                        t2 = round(float(t()), 2)
                        sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                        rel_result = round(sim[0][2] / sim[1] * 100, 2)
                    else:
                        t2 = round(float(t()), 2)
                        self.textEdit.append(
                            'It is not possible to generate CED circuit for selected structural constraint!')
                        method = 'E'
                        self.label_8.setText("None")
                        self.label_9.setText("0")
                        self.label_10.setText("0")
                        self.label_11.setText("0")
                        self.label_12.setText("0.00 %")
                        self.label_13.setText("None")
            elif ced_spectral <= self.constraint:
                if ced_spectral_4 <= self.constraint and ced_spectral_4 != n:
                    self.textEdit.append('Selected method based on Spectral R-code with clusterization on 4 groups.')
                    result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 2)
                    method = 'R4'
                    t2 = round(float(t()), 2)
                    sim = spectral.error_simulation(result, cone, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                elif ced_spectral_2 <= self.constraint and ced_spectral_2 != n:
                    self.textEdit.append('Selected method based on Spectral R-code with clusterization on 2 groups.')
                    result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 1)
                    method = 'R2'
                    t2 = round(float(t()), 2)
                    sim = spectral.error_simulation(result, cone, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                elif ced_spectral <= self.constraint:
                    self.textEdit.append('Selected method based on Spectral R-code without clusterization.')
                    result, cone, coders, decoders = spectral.create_spec_circuit(self.circuit, 0)
                    method = 'R'
                    t2 = round(float(t()), 2)
                    sim = spectral.error_simulation(result, cone, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                else:
                    t2 = round(float(t()), 2)
                    self.textEdit.append('It is not possible to generate CED circuit for selected structural '
                                         'constraint!')
                    method = 'E'
                    self.label_8.setText("None")
                    self.label_9.setText("0")
                    self.label_10.setText("0")
                    self.label_11.setText("0")
                    self.label_12.setText("0.00 %")
                    self.label_13.setText("None")
            elif ced_ldpc <= self.constraint:
                if ced_ldpc_4 <= self.constraint and ced_ldpc_4 != n:
                    self.textEdit.append('Selected method based on LDPC code with clusterization on 4 groups.')
                    result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 2)
                    method = 'L4'
                    t2 = round(float(t()), 2)
                    sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                elif ced_ldpc_2 <= self.constraint and ced_ldpc_2 != n:
                    self.textEdit.append('Selected method based on LDPC code with clusterization on 2 groups.')
                    result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 1)
                    method = 'L2'
                    t2 = round(float(t()), 2)
                    sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                elif ced_ldpc <= self.constraint:
                    self.textEdit.append('Selected method based on LDPC code without clusterization.')
                    result, coders, decoders = ldpc.create_ldpc_circuit(self.circuit, 0)
                    method = 'L'
                    t2 = round(float(t()), 2)
                    sim = ldpc.error_simulation(self.circuit, result, 1, 10000)
                    rel_result = round(sim[0][2] / sim[1] * 100, 2)
                else:
                    t2 = round(float(t()), 2)
                    self.textEdit.append('It is not possible to generate CED circuit for selected structural '
                                         'constraint!')
                    method = 'E'
                    self.label_8.setText("None")
                    self.label_9.setText("0")
                    self.label_10.setText("0")
                    self.label_11.setText("0")
                    self.label_12.setText("0.00 %")
                    self.label_13.setText("None")
            else:
                t2 = round(float(t()), 2)
                self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
                method = 'E'
                self.label_8.setText("None")
                self.label_9.setText("0")
                self.label_10.setText("0")
                self.label_11.setText("0")
                self.label_12.setText("0.00 %")
                self.label_13.setText("None")
        else:
            t2 = round(float(t()), 2)
            self.textEdit.append('It is not possible to generate CED circuit for selected structural constraint!')
            method = 'E'
            self.label_8.setText("None")
            self.label_9.setText("0")
            self.label_10.setText("0")
            self.label_11.setText("0")
            self.label_12.setText("0.00 %")
            self.label_13.setText("None")
        # ==============================================================================================================
        t3 = round(float(t()), 2)
        t4 = round(float(t2) - float(t1), 2)
        self.textEdit.append('Search time = {}s'.format(str(t4)))
        # ==============================================================================================================
        if options[1] is True:
            if method == 'E':
                self.textEdit.append('CED circuit was not generated. Unable to save file in Verilog format.')
            else:
                self.textEdit.append('CED subcircuits are saved in Verilog format.')
                if method != 'H':
                    for n_coder in range(0, len(coders)):
                        verilog_filename = pathname + '//result//{}_coder_{}.v'.format(self.filename, n_coder+1)
                        coders[n_coder].print_verilog_in_file(verilog_filename, 'coder_{}'.format(n_coder+1))
                    for n_decoder in range(0, len(decoders)):
                        verilog_filename = pathname + '//result//{}_decoder_{}.v'.format(self.filename, n_decoder+1)
                        decoders[n_decoder].print_verilog_in_file(verilog_filename, 'decoder_{}'.format(n_decoder+1))
                else:
                    verilog_filename = pathname + '//result//{}.v'.format(self.filename)
                    result.print_verilog_in_file(verilog_filename, 'CED_circuit')
                self.textEdit.append('Files saved.')
        # ==============================================================================================================
        if method != 'E':
            self.textEdit.append('Determining main characteristics of received CED circuit:')
            self.textEdit.append('PO = {}'.format(str(result.outputs())))
            self.textEdit.append('PI = {}'.format(str(result.inputs())))
            self.textEdit.append('Structure redundancy =  {}'.format(str(result.elements())))
            self.textEdit.append('Reliability characteristic =  {}%'.format(str(rel_result)))

            if method == 'H':       self.label_8.setText('Hemming')
            elif method == 'R':     self.label_8.setText('Spectral R-code')
            elif method == 'L':     self.label_8.setText('LDPC code')

            self.label_9.setText(str(result.elements()))
            self.label_10.setText(str(result.inputs()))
            self.label_11.setText(str(result.outputs()))
            self.label_12.setText(str(rel_result) + ' %')

            if method == 'R4' or method == 'L4':    self.label_13.setText('4 groups')
            elif method == 'R2' or method == 'L2':  self.label_13.setText('2 groups')
            else:                                   self.label_13.setText('Without clusterization')
        # ==============================================================================================================
        # LOG FILE - ON
        # ==============================================================================================================
        if options[0] is True:
            log_filename = pathname + '//result//{}.txt'.format(self.filename)
            f = open(log_filename, "a")
            f.write(start_time + '\n')
            f.write('Start program.\n')
            f.write('Input circuit is received.\n')
            f.write('Constraint to structure redundancy for CED circuit is received.\n')
            f.write('Constraint = {}\n'.format(self.constraint))
            f.write('Determining main characteristics of combinational circuit:\n')
            f.write('PI = {}\n'.format(inp))
            f.write('PO = {}\n'.format(k))
            f.write('Structure redundancy =  {}\n'.format(n))
            if mtd[1] is True:
                f.write('Calculation of estimated structure redundancy for CED circuit based on encoding in 3bits '
                        'Hemming space:\n')
                f.write('Structure redundancy =  {}\n'.format(ced_hemming))
            if mtd[3] is True:
                f.write('Calculation of estimated structure redundancy for CED circuit based on LDPC code:\n')
                f.write('Structure redundancy =  {}\n'.format(ced_ldpc))
                f.write('Calculation of estimated reliability characteristic for CED circuit based on LDPC code:\n')
                f.write('Reliability characteristic =  {}%\n'.format(round(rel_ldpc, 2)))
            if mtd[2] is True:
                f.write('Calculation of estimated structure redundancy for CED circuit based on Spectral R-code:\n')
                f.write('Structure redundancy =  {}\n'.format(ced_spectral))
                f.write('Calculation of estimated reliability characteristic for CED circuit based on Spectral '
                        'R-code:\n')
                f.write('Reliability characteristic =  {}%\n'.format(round(rel_spectral, 2)))
            if mtd[0] is True:
                if mtd[2] is True or mtd[3] is True:
                    f.write('Compiling matrix of dependencies.\n')
                    f.write('Clusterization circuit outputs into 2 groups.\n')
                    if mtd[3] is True:
                        f.write('Calculation of estimated structure redundancy for CED circuit based on LDPC code:\n')
                        f.write('Structure redundancy =  {}\n'.format(ced_ldpc_2))
                    if mtd[2] is True:
                        f.write('Calculation of estimated structure redundancy for CED circuit based on Spectral '
                                'R-code:\n')
                        f.write('Structure redundancy =  {}\n'.format(ced_spectral_2))
                    f.write('Clusterization circuit outputs into 4 groups.\n')
                    if mtd[3] is True:
                        f.write('Calculation of estimated structure redundancy for CED circuit based on LDPC code:\n')
                        f.write('Structure redundancy =  {}\n'.format(ced_ldpc_4))
                    if mtd[2] is True:
                        f.write('Calculation of estimated structure redundancy for CED circuit based on Spectral '
                                'R-code:\n')
                        f.write('Structure redundancy =  {}\n'.format(ced_spectral_4))
            if method == 'E':
                f.write('It is not possible to generate CED circuit for selected structural constraint!\n')
                f.write('Time  {}s\n'.format(round(float(t3) - float(t1), 2)))
                f.close()
            else:
                f.write('Selected method based on ')

                if method == 'H':       f.write('encoding in 3bits Hemming space.\n')
                elif method == 'R4':    f.write('Spectral R-code with clusterization on 4 groups.\n')
                elif method == 'R2':    f.write('Spectral R-code with clusterization on 2 groups.\n')
                elif method == 'R':     f.write('Spectral R-code without clusterization.\n')
                elif method == 'L4':    f.write('LDPC code with clusterization on 4 groups.\n')
                elif method == 'L2':    f.write('LDPC code with clusterization on 2 groups.\n')
                elif method == 'L':     f.write('LDPC code without clusterization.\n')

                f.write('Search time = {}s\n'.format(t4))
                f.write('Determining main characteristics of received CED circuit:\n')
                f.write('PO = {}\n'.format(result.outputs()))
                f.write('PI =  {}\n'.format(result.inputs()))
                f.write('Structure redundancy =  {}\n'.format(result.elements()))
                f.write('Reliability characteristic =  {}%\n'.format(rel_result))
                if options[0] is True:
                    f.write('Recording Verilog files.\n')
                    f.write('Files saved.\n')
                f.write('Time {}s\n'.format(round(float(t3) - float(t1), 2)))
                f.close()

        self.textEdit.append('Program execution time {}s\n'.format(str(round(float(t3) - float(t1), 2))))


def main():

    app = QApplication(sys.argv)
    window = AppSystemCED()
    window.setWindowIcon(QIcon('ippm_ras.png'))
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
