# **********************************************************************************************************************
# ПРОГРАММНЫЙ МОДУЛЬ ГЕНЕРАЦИИ СХЕМЫ ФУНКЦИОНАЛЬНОГО КОНТРОЛЯ НА ОСНОВЕ КОДИРОВАНИЯ В ТРЕХБИТНОМ ПРОСТРАНСТВЕ ХЭММИНГА
# **********************************************************************************************************************
import scheme as sch
import os
import random
import numpy as np
# **********************************************************************************************************************
def create_hemming_circuit(scheme):
    # Функция переименования узлов схемы
    renamed_scheme = sch.replicate(scheme, 1)
    n = renamed_elements_in_scheme(renamed_scheme, 'inp_', 'wire_', 0)

    # "Утроение" основной схемы
    scheme_2 = sch.merge_schemes([renamed_scheme] * 3)
    scheme_3 = sch.scheme_alt()
    inputs = list()

    # Вычисление числа ЛЭ основной схемы
    k = scheme.elements()

    # Для каждого ЛЭ основной схемы создается сбоеустойчивый аналог данного ЛЭ в базисе 3битоного пространства Хэмминга
    # Определение выходов сбоеустойчивого аналога ЛЭ
    for element in sorted(renamed_scheme.__elements__.keys()):
        outputs = [element, element + '_1', element + '_2']

        # Определение входов аналога, если ЛЭ основной схемы является двувходовым
        if len(renamed_scheme.__elements__[element][1]) == 2:
            inputs = [renamed_scheme.__elements__[element][1][0],
                      renamed_scheme.__elements__[element][1][0] + '_1',
                      renamed_scheme.__elements__[element][1][0] + '_2',
                      renamed_scheme.__elements__[element][1][1],
                      renamed_scheme.__elements__[element][1][1] + '_1',
                      renamed_scheme.__elements__[element][1][1] + '_2']

        # Если ЛЭ основной схемы - одновходовой
        elif len(renamed_scheme.__elements__[element][1]) == 1:
            inputs = [renamed_scheme.__elements__[element][1][0],
                      renamed_scheme.__elements__[element][1][0] + '_1',
                      renamed_scheme.__elements__[element][1][0] + '_2']

        # Определение типа (выполняемой функции) ЛЭ основной схемы
        node_type = renamed_scheme.__elements__[element][0]

        # Генерация подсхемы subscheme сбоеустойчивого аналога ЛЭ основной схемы
        if node_type == 'INV':
            subscheme, k = create_ft_analog_inv(inputs, outputs, k)             # Сбоеустойчивый аналог ЛЭ INV
        elif node_type == 'BUF':
            subscheme, k = create_ft_analog_buf(inputs, outputs, k)             # Сбоеустойчивый аналог ЛЭ BUF
        elif node_type == 'AND':
            subscheme, k = create_ft_analog_and2(inputs, outputs, k)            # Сбоеустойчивый аналог ЛЭ AND2
        elif node_type == 'OR':
            subscheme, k = create_ft_analog_or2(inputs, outputs, k)             # Сбоеустойчивый аналог ЛЭ OR2
        elif node_type == 'XOR':
            subscheme, k = create_ft_analog_xor2(inputs, outputs, k)            # Сбоеустойчивый аналог ЛЭ XOR2
        elif node_type == 'NAND':
            subscheme, k = create_ft_analog_nand2(inputs, outputs, k)           # Сбоеустойчивый аналог ЛЭ NAND2
        elif node_type == 'NOR':
            subscheme, k = create_ft_analog_nor2(inputs, outputs, k)            # Сбоеустойчивый аналог ЛЭ NOR2
        elif node_type == 'XNOR':
            subscheme, k = create_ft_analog_xnor2(inputs, outputs, k)           # Сбоеустойчивый аналог ЛЭ XNOR2
        elif node_type == 'GND':
            subscheme = {element: renamed_scheme.__elements__[element]}         # GND
        else:   subscheme = 0

        if node_type == 'GND':  scheme_3.__elements__.update(subscheme)
        else:                   scheme_3.__elements__.update(subscheme.__elements__)

    scheme_3.__inputs__ = scheme_2.__inputs__
    scheme_3.__outputs__ = scheme_2.__outputs__

    # Добавление подсхемы входного преобразователя
    scheme_4 = create_input_transducer(renamed_scheme, scheme_3)

    # Добавление подсхемы выходного преобразователя
    hem_ced = create_output_transducer(renamed_scheme, scheme_4, k)

    return hem_ced

def create_input_transducer(scheme_1, scheme_2):
    # Функция генерации вх. преобразователя и добавления его в СФК на основе кодирования в 3битном пространстве Хэмминга
    # scheme_1 - основная комбинационная схема
    # scheme_2 - схема, в которой ЛЭ были заменены на сбоеустойчивые аналоги в 3битном пространстве Хэмминга

    # Создание словаря соединений
    con = dict()

    # Создание списка выходов объединенной схемы scheme_2
    out = list()

    # Создание пустой подсхемы входного преобразователя inp_transducer
    inp_transducer = sch.scheme_alt()

    # Добавление входов для подсхемы входного преобразователя inp_transducer
    inp_transducer.__inputs__ = ['x_0']

    for i in range(scheme_1.inputs() - 1):    inp_transducer.__inputs__.append('x_{}'.format(i + 1))

    # Добавление выходов для подсхемы входного преобразователя inp_transducer
    inp_transducer.__outputs__ = inp_transducer.__inputs__

    # Генерация словаря соединений
    # Например:
    # {(1,'x_1'): [(0, 'a'), (0, 'a_1'), (0, 'a_2')]}, где 'x_1' - вход преобразователя,
    # 'a','a_1','a_2' - входы схемы
    for i in range(scheme_1.inputs()):  con[(1, 'x_{}'.format(i))] = [(0, scheme_1.__inputs__[i]),
                                                                      (0, scheme_1.__inputs__[i] + '_1'),
                                                                      (0, scheme_1.__inputs__[i] + '_2')]

    # Генерация выходов объединенной схемы
    for i in range(scheme_2.outputs()):   out.append((0, scheme_2.__outputs__[i]))

    # Объединение схемы hemming_scheme и подсхемы входного преобразователя inp_transducer
    scheme_2 = sch.merge_schemes([scheme_2, inp_transducer], con, out)

    return scheme_2

def create_output_transducer(scheme_1, scheme_2, k):
    # Функция генерации входного преобразователя и добавления его в СФК на основе кодирования в трехбитном пространстве
    # Хэмминга
    # scheme_1 - основная комбинационная схема
    # scheme_2 - СФК на основе кодирования в трехбитном пространстве Хэмминга без выходных преобразователей

    # Создание словаря соединений
    con = dict()

    # Создание пустой подсхемы выходного преобразователя out_transducer
    out_transducer = sch.scheme_alt()

    # Генерация входов выходного преобразователя out_transducer
    out_transducer.__inputs__ = ['_{}_'.format(k), '_{}_'.format(k + 1), '_{}_'.format(k + 2)]

    # Генерация выхода выходного преобразователя out_transducer
    out_transducer.__outputs__ = ['y']

    # Генерация элементов выходного преобразователя out_transducer
    out_transducer.__elements__ = {'_{}_'.format(k + 4): ('OR', ['_{}_'.format(k), '_{}_'.format(k + 1)]),
                                   '_{}_'.format(k + 5): ('NAND', ['_{}_'.format(k), '_{}_'.format(k + 1)]),
                                   '_{}_'.format(k + 6): ('NAND', ['_{}_'.format(k + 4), '_{}_'.format(k + 2)]),
                                   'y': ('NAND', ['_{}_'.format(k + 5), '_{}_'.format(k + 6)])}

    # Копирование выходных преобразователей out_transducer по числу выходов основной схемы
    out_transducer = sch.merge_schemes([out_transducer] * int(scheme_2.outputs() / 3))

    # Генерация словаря соединений
    for i in range(scheme_1.outputs()):
        con[(0, scheme_2.__outputs__[i])] = ([(1, out_transducer.__inputs__[3 * i])])
        con[(0, scheme_2.__outputs__[scheme_1.outputs() + i])] = ([(1, out_transducer.__inputs__[3 * i + 1])])
        con[(0, scheme_2.__outputs__[2 * scheme_1.outputs() + i])] = ([(1, out_transducer.__inputs__[3 * i + 2])])

    # Генерация выходов объединенной схемы
    out = [(1, i) for i in out_transducer.__outputs__]

    # Объединение СФК и выходного преобразователя out_transducer
    scheme_2 = sch.merge_schemes([scheme_2, out_transducer], con, out)

    # Приведение выхода результирующей схемы к общему виду
    del scheme_2.__elements__['y']
    scheme_2.__elements__['y_0'] = ('NAND', ['_{}_'.format(k + 5), '_{}_'.format(k + 6)])
    scheme_2.__outputs__[0] = 'y_0'

    return scheme_2

def create_ft_analog_buf(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ BUF
    buf = '_{}_'

    ft_buf = sch.scheme_alt()
    ft_buf.__inputs__ = inputs
    ft_buf.__outputs__ = outputs

    ft_buf.__elements__ = {buf.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                           buf.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                           buf.format(k + 3): ('NAND', [buf.format(k + 1), inputs[2]]),
                           outputs[0]: ('NAND', [buf.format(k + 2), buf.format(k + 3)]),

                           buf.format(k + 4): ('OR', [inputs[0], inputs[1]]),
                           buf.format(k + 5): ('NAND', [inputs[0], inputs[1]]),
                           buf.format(k + 6): ('NAND', [buf.format(k + 4), inputs[2]]),
                           outputs[1]: ('NAND', [buf.format(k + 5), buf.format(k + 6)]),

                           buf.format(k + 7): ('OR', [inputs[0], inputs[1]]),
                           buf.format(k + 8): ('NAND', [inputs[0], inputs[1]]),
                           buf.format(k + 9): ('NAND', [buf.format(k + 7), inputs[2]]),
                           outputs[2]: ('NAND', [buf.format(k + 8), buf.format(k + 9)])}

    k += 9

    return ft_buf, k

def create_ft_analog_inv(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ INV
    inv = '_{}_'

    ft_inv = sch.scheme_alt()
    ft_inv.__inputs__ = inputs
    ft_inv.__outputs__ = outputs

    ft_inv.__elements__ = {inv.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                           inv.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                           inv.format(k + 3): ('NAND', [inv.format(k + 1), inputs[2]]),
                           outputs[0]: ('AND', [inv.format(k + 2), inv.format(k + 3)]),

                           inv.format(k + 4): ('OR', [inputs[0], inputs[1]]),
                           inv.format(k + 5): ('NAND', [inputs[0], inputs[1]]),
                           inv.format(k + 6): ('NAND', [inv.format(k + 4), inputs[2]]),
                           outputs[1]: ('AND', [inv.format(k + 5), inv.format(k + 6)]),

                           inv.format(k + 7): ('OR', [inputs[0], inputs[1]]),
                           inv.format(k + 8): ('NAND', [inputs[0], inputs[1]]),
                           inv.format(k + 9): ('NAND', [inv.format(k + 7), inputs[2]]),
                           outputs[2]: ('AND', [inv.format(k + 8), inv.format(k + 9)])}

    k += 9

    return ft_inv, k

def create_ft_analog_and2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ AND2
    and2 = '_{}_'

    ft_and2 = sch.scheme_alt()
    ft_and2.__inputs__ = inputs
    ft_and2.__outputs__ = outputs

    ft_and2.__elements__ = {and2.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                            and2.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                            and2.format(k + 3): ('OR', [inputs[3], inputs[4]]),
                            and2.format(k + 4): ('NAND', [inputs[3], inputs[4]]),
                            and2.format(k + 5): ('NAND', [and2.format(k + 1), inputs[2]]),
                            and2.format(k + 6): ('NAND', [and2.format(k + 3), inputs[5]]),
                            and2.format(k + 7): ('NAND', [and2.format(k + 5), and2.format(k + 2)]),
                            and2.format(k + 8): ('NAND', [and2.format(k + 6), and2.format(k + 4)]),
                            outputs[0]: ('AND', [and2.format(k + 7), and2.format(k + 8)]),

                            and2.format(k + 9): ('OR', [inputs[0], inputs[1]]),
                            and2.format(k + 10): ('NAND', [inputs[0], inputs[1]]),
                            and2.format(k + 11): ('OR', [inputs[3], inputs[4]]),
                            and2.format(k + 12): ('NAND', [inputs[3], inputs[4]]),
                            and2.format(k + 13): ('NAND', [and2.format(k + 9), inputs[2]]),
                            and2.format(k + 14): ('NAND', [and2.format(k + 11), inputs[5]]),
                            and2.format(k + 15): ('NAND', [and2.format(k + 13), and2.format(k + 10)]),
                            and2.format(k + 16): ('NAND', [and2.format(k + 14), and2.format(k + 12)]),
                            outputs[1]: ('AND', [and2.format(k + 15), and2.format(k + 16)]),

                            and2.format(k + 17): ('OR', [inputs[0], inputs[1]]),
                            and2.format(k + 18): ('NAND', [inputs[0], inputs[1]]),
                            and2.format(k + 19): ('OR', [inputs[3], inputs[4]]),
                            and2.format(k + 20): ('NAND', [inputs[3], inputs[4]]),
                            and2.format(k + 21): ('NAND', [and2.format(k + 17), inputs[2]]),
                            and2.format(k + 22): ('NAND', [and2.format(k + 19), inputs[5]]),
                            and2.format(k + 23): ('NAND', [and2.format(k + 21), and2.format(k + 18)]),
                            and2.format(k + 24): ('NAND', [and2.format(k + 22), and2.format(k + 20)]),
                            outputs[2]: ('AND', [and2.format(k + 23), and2.format(k + 24)])}

    k += 24

    return ft_and2, k

def create_ft_analog_nand2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ NAND2
    nand2 = '_{}_'

    ft_nand2 = sch.scheme_alt()
    ft_nand2.__inputs__ = inputs
    ft_nand2.__outputs__ = outputs

    ft_nand2.__elements__ = {nand2.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                             nand2.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                             nand2.format(k + 3): ('OR', [inputs[3], inputs[4]]),
                             nand2.format(k + 4): ('NAND', [inputs[3], inputs[4]]),
                             nand2.format(k + 5): ('NAND', [nand2.format(k + 1), inputs[2]]),
                             nand2.format(k + 6): ('NAND', [nand2.format(k + 3), inputs[5]]),
                             nand2.format(k + 7): ('NAND', [nand2.format(k + 5), nand2.format(k + 2)]),
                             nand2.format(k + 8): ('NAND', [nand2.format(k + 6), nand2.format(k + 4)]),
                             outputs[0]: ('NAND', [nand2.format(k + 7), nand2.format(k + 8)]),

                             nand2.format(k + 9): ('OR', [inputs[0], inputs[1]]),
                             nand2.format(k + 10): ('NAND', [inputs[0], inputs[1]]),
                             nand2.format(k + 11): ('OR', [inputs[3], inputs[4]]),
                             nand2.format(k + 12): ('NAND', [inputs[3], inputs[4]]),
                             nand2.format(k + 13): ('NAND', [nand2.format(k + 9), inputs[2]]),
                             nand2.format(k + 14): ('NAND', [nand2.format(k + 11), inputs[5]]),
                             nand2.format(k + 15): ('NAND', [nand2.format(k + 13), nand2.format(k + 10)]),
                             nand2.format(k + 16): ('NAND', [nand2.format(k + 14), nand2.format(k + 12)]),
                             outputs[1]: ('NAND', [nand2.format(k + 15), nand2.format(k + 16)]),

                             nand2.format(k + 17): ('OR', [inputs[0], inputs[1]]),
                             nand2.format(k + 18): ('NAND', [inputs[0], inputs[1]]),
                             nand2.format(k + 19): ('OR', [inputs[3], inputs[4]]),
                             nand2.format(k + 20): ('NAND', [inputs[3], inputs[4]]),
                             nand2.format(k + 21): ('NAND', [nand2.format(k + 17), inputs[2]]),
                             nand2.format(k + 22): ('NAND', [nand2.format(k + 19), inputs[5]]),
                             nand2.format(k + 23): ('NAND', [nand2.format(k + 21), nand2.format(k + 18)]),
                             nand2.format(k + 24): ('NAND', [nand2.format(k + 22), nand2.format(k + 20)]),
                             outputs[2]: ('NAND', [nand2.format(k + 23), nand2.format(k + 24)])}

    k += 24

    return ft_nand2, k

def create_ft_analog_or2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ OR2
    or2 = '_{}_'

    ft_or2 = sch.scheme_alt()
    ft_or2.__inputs__ = inputs
    ft_or2.__outputs__ = outputs

    ft_or2.__elements__ = {or2.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                           or2.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                           or2.format(k + 3): ('OR', [inputs[3], inputs[4]]),
                           or2.format(k + 4): ('NAND', [inputs[3], inputs[4]]),
                           or2.format(k + 5): ('AND', [or2.format(k + 2), or2.format(k + 4)]),
                           or2.format(k + 6): ('NAND', [or2.format(k + 1), inputs[2]]),
                           or2.format(k + 7): ('NAND', [or2.format(k + 3), inputs[5]]),
                           or2.format(k + 8): ('AND', [or2.format(k + 6), or2.format(k + 7)]),
                           outputs[0]: ('NAND', [or2.format(k + 5), or2.format(k + 8)]),

                           or2.format(k + 9): ('OR', [inputs[0], inputs[1]]),
                           or2.format(k + 10): ('NAND', [inputs[0], inputs[1]]),
                           or2.format(k + 11): ('OR', [inputs[3], inputs[4]]),
                           or2.format(k + 12): ('NAND', [inputs[3], inputs[4]]),
                           or2.format(k + 13): ('AND', [or2.format(k + 10), or2.format(k + 12)]),
                           or2.format(k + 14): ('NAND', [or2.format(k + 9), inputs[2]]),
                           or2.format(k + 15): ('NAND', [or2.format(k + 11), inputs[5]]),
                           or2.format(k + 16): ('AND', [or2.format(k + 14), or2.format(k + 15)]),
                           outputs[1]: ('NAND', [or2.format(k + 13), or2.format(k + 16)]),

                           or2.format(k + 17): ('OR', [inputs[0], inputs[1]]),
                           or2.format(k + 18): ('NAND', [inputs[0], inputs[1]]),
                           or2.format(k + 19): ('OR', [inputs[3], inputs[4]]),
                           or2.format(k + 20): ('NAND', [inputs[3], inputs[4]]),
                           or2.format(k + 21): ('AND', [or2.format(k + 18), or2.format(k + 20)]),
                           or2.format(k + 22): ('NAND', [or2.format(k + 17), inputs[2]]),
                           or2.format(k + 23): ('NAND', [or2.format(k + 19), inputs[5]]),
                           or2.format(k + 24): ('AND', [or2.format(k + 22), or2.format(k + 23)]),
                           outputs[2]: ('NAND', [or2.format(k + 21), or2.format(k + 24)])}

    k += 24

    return ft_or2, k

def create_ft_analog_nor2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ NOR2
    nor2 = '_{}_'

    ft_nor2 = sch.scheme_alt()
    ft_nor2.__inputs__ = inputs
    ft_nor2.__outputs__ = outputs

    ft_nor2.__elements__ = {nor2.format(k + 1): ('OR', [inputs[0], inputs[1]]),
                            nor2.format(k + 2): ('NAND', [inputs[0], inputs[1]]),
                            nor2.format(k + 3): ('OR', [inputs[3], inputs[4]]),
                            nor2.format(k + 4): ('NAND', [inputs[3], inputs[4]]),
                            nor2.format(k + 5): ('AND', [nor2.format(k + 2), nor2.format(k + 4)]),
                            nor2.format(k + 6): ('NAND', [nor2.format(k + 1), inputs[2]]),
                            nor2.format(k + 7): ('NAND', [nor2.format(k + 3), inputs[5]]),
                            nor2.format(k + 8): ('AND', [nor2.format(k + 6), nor2.format(k + 7)]),
                            outputs[0]: ('AND', [nor2.format(k + 5), nor2.format(k + 8)]),

                            nor2.format(k + 9): ('OR', [inputs[0], inputs[1]]),
                            nor2.format(k + 10): ('NAND', [inputs[0], inputs[1]]),
                            nor2.format(k + 11): ('OR', [inputs[3], inputs[4]]),
                            nor2.format(k + 12): ('NAND', [inputs[3], inputs[4]]),
                            nor2.format(k + 13): ('AND', [nor2.format(k + 10), nor2.format(k + 12)]),
                            nor2.format(k + 14): ('NAND', [nor2.format(k + 9), inputs[2]]),
                            nor2.format(k + 15): ('NAND', [nor2.format(k + 11), inputs[5]]),
                            nor2.format(k + 16): ('AND', [nor2.format(k + 14), nor2.format(k + 15)]),
                            outputs[1]: ('AND', [nor2.format(k + 13), nor2.format(k + 16)]),

                            nor2.format(k + 17): ('OR', [inputs[0], inputs[1]]),
                            nor2.format(k + 18): ('NAND', [inputs[0], inputs[1]]),
                            nor2.format(k + 19): ('OR', [inputs[3], inputs[4]]),
                            nor2.format(k + 20): ('NAND', [inputs[3], inputs[4]]),
                            nor2.format(k + 21): ('AND', [nor2.format(k + 18), nor2.format(k + 20)]),
                            nor2.format(k + 22): ('NAND', [nor2.format(k + 17), inputs[2]]),
                            nor2.format(k + 23): ('NAND', [nor2.format(k + 19), inputs[5]]),
                            nor2.format(k + 24): ('AND', [nor2.format(k + 22), nor2.format(k + 23)]),
                            outputs[2]: ('AND', [nor2.format(k + 21), nor2.format(k + 24)])}

    k += 24

    return ft_nor2, k

def create_ft_analog_xor2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ XOR2
    xor2 = '_{}_'
    ft_xor2 = sch.scheme_alt()
    ft_xor2.__inputs__ = inputs
    ft_xor2.__outputs__ = outputs

    ft_xor2.__elements__ = {xor2.format(k + 1): ('AND', [inputs[2], inputs[1]]),
                            xor2.format(k + 2): ('OR', [inputs[2], inputs[1]]),
                            xor2.format(k + 3): ('AND', [xor2.format(k + 2), inputs[0]]),
                            xor2.format(k + 4): ('OR', [inputs[3], inputs[4]]),
                            xor2.format(k + 5): ('NAND', [inputs[3], inputs[4]]),
                            xor2.format(k + 6): ('NOR', [xor2.format(k + 1), xor2.format(k + 3)]),
                            xor2.format(k + 7): ('NAND', [xor2.format(k + 4), inputs[5]]),
                            xor2.format(k + 8): ('NAND', [xor2.format(k + 5), xor2.format(k + 7)]),
                            outputs[0]: ('XNOR', [xor2.format(k + 6), xor2.format(k + 8)]),

                            xor2.format(k + 9): ('AND', [inputs[2], inputs[1]]),
                            xor2.format(k + 10): ('OR', [inputs[2], inputs[1]]),
                            xor2.format(k + 11): ('AND', [xor2.format(k + 10), inputs[0]]),
                            xor2.format(k + 12): ('OR', [inputs[3], inputs[4]]),
                            xor2.format(k + 13): ('NAND', [inputs[3], inputs[4]]),
                            xor2.format(k + 14): ('NOR', [xor2.format(k + 9), xor2.format(k + 11)]),
                            xor2.format(k + 15): ('NAND', [xor2.format(k + 12), inputs[5]]),
                            xor2.format(k + 16): ('NAND', [xor2.format(k + 13), xor2.format(k + 15)]),
                            outputs[1]: ('XNOR', [xor2.format(k + 14), xor2.format(k + 16)]),

                            xor2.format(k + 17): ('AND', [inputs[2], inputs[1]]),
                            xor2.format(k + 18): ('OR', [inputs[2], inputs[1]]),
                            xor2.format(k + 19): ('AND', [xor2.format(k + 18), inputs[0]]),
                            xor2.format(k + 20): ('OR', [inputs[3], inputs[4]]),
                            xor2.format(k + 21): ('NAND', [inputs[3], inputs[4]]),
                            xor2.format(k + 22): ('NOR', [xor2.format(k + 17), xor2.format(k + 19)]),
                            xor2.format(k + 23): ('NAND', [xor2.format(k + 20), inputs[5]]),
                            xor2.format(k + 24): ('NAND', [xor2.format(k + 21), xor2.format(k + 23)]),
                            outputs[2]: ('XNOR', [xor2.format(k + 22), xor2.format(k + 24)])}

    k += 24

    return ft_xor2, k

def create_ft_analog_xnor2(inputs, outputs, k):
    # Функция генерации сбоеустойчивого аналога ЛЭ XNOR2
    xnor2 = '_{}_'

    ft_xnor2 = sch.scheme_alt()
    ft_xnor2.__inputs__ = inputs
    ft_xnor2.__outputs__ = outputs

    ft_xnor2.__elements__ = {xnor2.format(k + 1): ('AND', [inputs[2], inputs[1]]),
                             xnor2.format(k + 2): ('OR', [inputs[2], inputs[1]]),
                             xnor2.format(k + 3): ('AND', [xnor2.format(k + 2), inputs[0]]),
                             xnor2.format(k + 4): ('OR', [inputs[3], inputs[4]]),
                             xnor2.format(k + 5): ('NAND', [inputs[3], inputs[4]]),
                             xnor2.format(k + 6): ('NOR', [xnor2.format(k + 1), xnor2.format(k + 3)]),
                             xnor2.format(k + 7): ('NAND', [xnor2.format(k + 4), inputs[5]]),
                             xnor2.format(k + 8): ('NAND', [xnor2.format(k + 5), xnor2.format(k + 7)]),
                             outputs[0]: ('XOR', [xnor2.format(k + 6), xnor2.format(k + 8)]),

                             xnor2.format(k + 9): ('AND', [inputs[2], inputs[1]]),
                             xnor2.format(k + 10): ('OR', [inputs[2], inputs[1]]),
                             xnor2.format(k + 11): ('AND', [xnor2.format(k + 10), inputs[0]]),
                             xnor2.format(k + 12): ('OR', [inputs[3], inputs[4]]),
                             xnor2.format(k + 13): ('NAND', [inputs[3], inputs[4]]),
                             xnor2.format(k + 14): ('NOR', [xnor2.format(k + 9), xnor2.format(k + 11)]),
                             xnor2.format(k + 15): ('NAND', [xnor2.format(k + 12), inputs[5]]),
                             xnor2.format(k + 16): ('NAND', [xnor2.format(k + 13), xnor2.format(k + 15)]),
                             outputs[1]: ('XOR', [xnor2.format(k + 14), xnor2.format(k + 16)]),

                             xnor2.format(k + 17): ('AND', [inputs[2], inputs[1]]),
                             xnor2.format(k + 18): ('OR', [inputs[2], inputs[1]]),
                             xnor2.format(k + 19): ('AND', [xnor2.format(k + 18), inputs[0]]),
                             xnor2.format(k + 20): ('OR', [inputs[3], inputs[4]]),
                             xnor2.format(k + 21): ('NAND', [inputs[3], inputs[4]]),
                             xnor2.format(k + 22): ('NOR', [xnor2.format(k + 17), xnor2.format(k + 19)]),
                             xnor2.format(k + 23): ('NAND', [xnor2.format(k + 20), inputs[5]]),
                             xnor2.format(k + 24): ('NAND', [xnor2.format(k + 21), xnor2.format(k + 23)]),
                             outputs[2]: ('XOR', [xnor2.format(k + 22), xnor2.format(k + 24)])}

    k += 24

    return ft_xnor2, k

def renamed_elements_in_scheme(scheme, inp_name_pattern, elem_name_pattern, n=0):
    # Функция переименования элементов комбинационной схемы
    # Создание словаря для переименования элементов
    renamed_dict = dict()

    # Добавление в словарь элементов для переименования входов комбинационной схемы по заданному пользователем шаблону
    # inp_name_pattern
    renamed_dict.update({scheme.__inputs__[i]:  inp_name_pattern + '{}'.format(i + 1) for i in range(scheme.inputs())})

    # Создание списка имен элементов без учета выходов комбинационной схемы
    list_elements = list(set(scheme.element_labels()).difference(scheme.__outputs__))

    # Добавление в словарь элементов для переименования ЛЭ комбинационной схемы по заданному пользователем шаблону
    # elem_name_pattern
    if n == 0:
        renamed_dict.update({list_elements[i]: elem_name_pattern + '{}'.format(i + 1)
                             for i in range(scheme.elements() - scheme.outputs())})
        n += scheme.elements() - scheme.outputs() + 1
    else:
        renamed_elements = dict()
        for i in range(scheme.elements() - scheme.outputs()):
            renamed_elements[list_elements[i]] = elem_name_pattern + '{}'.format(n)
            n += 1

        renamed_dict.update(renamed_elements)

    # Добавление в словарь элементов для переименования выходов комбинационной схемы по заданному пользователем шаблону
    # elem_name_pattern
    renamed_out = dict()
    for i in range(scheme.outputs()):
        # renamed_out[scheme.__outputs__[i]] = elem_name_pattern + '{}'.format(n)
        renamed_out[scheme.__outputs__[i]] = 'out_{}'.format(n)
        n += 1

    renamed_dict.update(renamed_out)

    # Переименование входов, выходов и ЛЭ комбинационной схемы с помощью полученного словаря
    scheme.rename_labels(renamed_dict)

    return n

def calc_structure_redundancy_hemming_ced(scheme):
    # Вычисление предполагаемой структурной избыточности СФК (Хэмминг)
    # Вычисление числа одновходовых ЛЭ в комбинационной схеме
    num = 0

    for element in scheme.__elements__:
        element_type = scheme.__elements__[element][0]
        if element_type == 'BUF' or element_type == 'INV':  num += 1

    # Вычисление предполагаемой структурной избыточности СФК на основе кодирования в трехбитном пространстве Хэмминга
    # без определения чувствительных участков комбинационной схемы
    predict_redundancy = 27 * scheme.elements() - 15 * num + 4 * scheme.outputs()

    return predict_redundancy


def error_simulation(ced, rate, n=1500000):
    # Проведение моделирования по инжектированию ошибок rate-кратности в схему функционального контроля
    t_errors = [0, 0]

    n_inputs = ced.inputs()
    n_elements = ced.elements()
    # scheme_outputs = scheme.outputs()
    ced_outputs = ced.outputs()

    # element_list = sorted(ced.__elements__.keys())

    n_max = 2 ** n_inputs * n_elements

    if rate == 1 and n_max <= n:
        capacity = 2 ** n_inputs
        num = n_max
        input_list = exhaustive_stimulus(n_inputs)

        for i in range(n_elements):
            error_list = [0] * n_elements
            error_list[i] = 2 ** capacity - 1

            result = ced.process(input_list, error_list, capacity)
            check = ced.process(input_list, [0] * ced.elements(), capacity)

            print('result = ', result)
            print('check = ', check)

            t_errors = def_type_of_err(result, check, ced_outputs, t_errors, capacity)

    else:
        num = n
        capacity = n // n_elements

        if capacity != 0:
            for i in range(n_elements):
                input_list = list()

                for j in range(n_inputs):   input_list.append(random.randint(0, 2 ** capacity - 1))

                error_list = [0] * n_elements

                while error_list.count(2 ** capacity - 1) != rate:
                    # для инжектирования только в инф. разряды
                    # k = random.randint(0, c_1.elements() - 1)
                    # для инжектирование ошибок в схему без ограничений
                    # k = random.randint(0, c_0.elements() - 1)
                    k = random.randint(0, ced.elements() - 1)

                    error_list[k] = 2 ** capacity - 1

                result = ced.process(input_list, error_list, capacity)
                check = ced.process(input_list, [0] * ced.elements(), capacity)

                t_errors = def_type_of_err(result, check, ced_outputs, t_errors, capacity)

        capacity = n % n_elements

        for i in range(capacity):
            input_list = list()

            for j in range(n_inputs):   input_list.append(random.randint(0, 1))

            error_list = [0] * n_elements

            while error_list.count(1) != rate:
                # для инжектирования только в инф. разряды
                # k = random.randint(0, c_1.elements() - 1)
                # для инжектирование ошибок в схему без ограничений
                # k = random.randint(0, c_0.elements() - 1)
                k = random.randint(0, ced.elements() - 1)

                error_list[k] = 1

            result = ced.process(input_list, error_list)
            check = ced.process(input_list, [0] * ced.elements())

            t_errors = def_type_of_err(result, check, ced_outputs, t_errors, 1)

    return t_errors, num

def def_type_of_err(result, check, ced_outputs, t_errors, capacity):
    condition = []

    result = list(result)
    check = list(check)

    for i in range(ced_outputs):                                    # преобразование списка result в необходимый формат
        result[i] = list(bin(result[i])[2:].zfill(capacity))
        for j in range(capacity):   result[i][j] = int(result[i][j])

    for i in range(ced_outputs):                                    # преобразование списка check в необходимый формат
        check[i] = list(bin(check[i])[2:].zfill(capacity))
        for j in range(capacity):   check[i][j] = int(check[i][j])

    result = np.transpose(result)
    check = np.transpose(check)

    for i in range(capacity): condition.append(np.array_equal(result[i], check[i]))  # сравнение выходов СФК и эталона

    for i in range(capacity):
        if condition[i]:    t_errors[0] += 1
        else:               t_errors[1] += 1

    return t_errors

def exhaustive_stimulus(n_inputs):
    tmp = 1
    result = []

    for i in range(n_inputs - 1, -1, -1):
        result.append((2**(2**i)-1)*tmp)
        tmp *= (1+2**(2**i))

    return result
