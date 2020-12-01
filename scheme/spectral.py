# **********************************************************************************************************************
# ПРОГРАММНЫЙ МОДУЛЬ ГЕНЕРАЦИИ СХЕМЫ ФУНКЦИОНАЛЬНОГО КОНТРОЛЯ НА ОСНОВЕ СПЕКТРАЛЬНОГО R КОДА
# **********************************************************************************************************************
import scheme as sch
import numpy as np
import itertools as it
import random
# **********************************************************************************************************************
from scheme.clusterization import clusterization
# **********************************************************************************************************************
def create_spec_circuit(scheme, n_pass):
    # Функция генерации СФК на основе спектрального R кода с учетом применения алгоритма кластеризации

    if n_pass == 0:
        groups = [[i+1 for i in range(scheme.outputs())]]
        # Q = 0
    else:
        clusters, groups = clusterization(scheme, n_pass)

    scheme_3 = list()
    coders = list()
    decoders = list()
    cone = list()
    l3 = list()

    n = 1

    for i in range(len(groups)):
        outputs = []

        for j in range(len(groups[i])): outputs.append(scheme.__outputs__[groups[i][j] - 1])

        scheme_1 = scheme.subscheme_by_outputs(outputs)
        scheme_2, cone, n, coder, decoder = create_ced_for_group(scheme_1, groups[i], cone, n)
        scheme_3.append(scheme_2)

        coders.append(coder)
        decoders.append(decoder)

    conn = dict()
    out = list()

    for n0 in range(scheme.inputs()):
        l1 = list()
        l2 = list()

        for n1 in range(len(groups)):
            if scheme_3[n1].__inputs__.count(scheme.__inputs__[n0]) != 0:   l1.append(n1)

        for n2 in range(len(l1)):   l2.append((l1[n2] + 1, scheme.__inputs__[n0]))

        conn[(0, scheme.__inputs__[n0])] = l2

    for n3 in range(len(groups)):
        n_out = scheme_3[n3].outputs() - 2
        inp_1 = scheme_3[n3].__inputs__[(-n_out):]

        for n4 in range(len(inp_1)):    conn[(0, scheme.__outputs__[groups[n3][n4] - 1])] = [(n3 + 1, inp_1[n4])]
    cir = [scheme]

    for n5 in range(len(groups)):   cir.append(scheme_3[n5])

    for n6 in range(len(scheme_3)):
        for n7 in range(scheme_3[n6].outputs()): out.append((n6 + 1, scheme_3[n6].__outputs__[n7]))

    result = sch.merge_schemes(cir, conn, out)
    t_cone = result.subscheme_by_outputs(['_s0'])

    for n8 in range(scheme.elements()):
        if list(t_cone.__elements__).count(list(scheme.__elements__)[n8]) > 0:
            del t_cone.__elements__[list(scheme.__elements__)[n8]]

    l3 += list(t_cone.__elements__.keys())

    for n7 in range(len(groups) - 1):
        t_cone = result.subscheme_by_outputs(['_s0_{}'.format(n7 + 1)])

        for n8 in range(scheme.elements()):
            if list(t_cone.__elements__).count(list(scheme.__elements__)[n8]) > 0:
                del t_cone.__elements__[list(scheme.__elements__)[n8]]

        l3 += list(t_cone.__elements__.keys())

    cone += l3

    if n_pass != 0:

        old_out = sorted(result.__outputs__)

        n_or = len(groups) - 1

        for i in range(n_or):    result.__elements__['bit_{}'.format(i + 1)] = ('OR', [old_out[i], old_out[i + 1]])

        bit = 'bit_{}'.format(n_or)

        old_out = old_out[len(groups):]

        for i in range(n_or):    result.__elements__['flag_error_{}'.format(i + 1)] = ('OR', [old_out[i], old_out[i + 1]])

        flag = 'flag_error_{}'.format(n_or)

        old_out = old_out[len(groups):]

        result.__outputs__ = ['out_{}'.format(i + 1) for i in range(len(old_out))]

        result.__outputs__ += [bit, flag]

    return result, cone, coders, decoders

def create_ced_for_group(scheme, group, cone=None, n=0):
    if cone is None:    cone = []
    spectral_ced = sch.scheme_alt()

    if scheme.outputs() != 1:
        # Вычисление основных параметров спектрального R-кода
        k = scheme.outputs()

        m = int(np.ceil(np.log2(k)))+1

        gx = matrix_gx(k, m-1)
        gx_elements = gx_with_elements(scheme, gx, k, m)
        gx_count_one = gx_with_count_one(gx)

        outputs = []

        for i in range(scheme.outputs()): outputs.append(scheme.__outputs__[i])

        # Создание копии основной схемы для кодера
        scheme_1 = sch.replicate(scheme, 1)

        # Генерирование подсхемы кодера для СФК на основе спектрального R-кода
        coder, n = create_coder(scheme_1, gx_elements, gx_count_one, m, n)

        # Минимизирование подсхемы кодера для СФК на основе спектрального R-кода с помощью Yosys
        # coder_min = create_circuit_external_yosys(coder)

        # Генерирование подсхемы декодера для СФК на основе спектрального R-кода
        decoder, n = create_decoder(scheme, gx_elements, outputs, gx_count_one, m, k, n)

        # Минимизирование подсхемы декодера для СФК на основе спектрального R-кода с помощью Yosys
        # decoder_min = create_circuit_external_yosys(decoder)

        # n_decoder_out = len(decoder_min.__outputs__)
        n_decoder_out = len(decoder.__outputs__)

        # Генерирование подсхемы мультиплексора для СФК на основе спектрального R-кода
        # mux_inputs = decoder_min.__outputs__[:(n_decoder_out-1)]
        mux_inputs = decoder.__outputs__[:(n_decoder_out - 1)]

        mux, n = create_mux(mux_inputs, scheme.__outputs__, k, n, group)

        # cone += mux.__elements__

        # Объединение подсхем декодера и мультиплексора
        conn = dict()
        out = list()

        # for n1 in range(k): conn[(0, decoder_min.__outputs__[n1])] = [(1, decoder_min.__outputs__[n1])]
        for n1 in range(k): conn[(0, decoder.__outputs__[n1])] = [(1, decoder.__outputs__[n1])]
        for n2 in range(k): conn[(0, scheme.__outputs__[n2])] = [(1, scheme.__outputs__[n2])]

        conn[(0, '_s0')] = [(1, '_s0')]
        conn[(0, 'n_s0')] = [(1, 'n_s0')]

        for n3 in range(k):     out.append((1, mux.__outputs__[n3]))

        out.append((0, '_s0'))
        out.append((0, 'flag'))

        # scheme_2 = sch.merge_schemes([decoder_min, mux], conn, out)
        scheme_2 = sch.merge_schemes([decoder, mux], conn, out)

        # Объединение подсхем кодера и scheme_2
        conn = dict()
        out = list()

        # for n4 in range(m):   conn[(0, coder_min.__outputs__[n4])] = [(1, scheme_2.__inputs__[k+n4])]
        # for n5 in range(scheme_2.outputs()):    out.append((1, scheme_2.__outputs__[n5]))
        # spectral_ced = sch.merge_schemes([coder_min, scheme_2], conn, out)

        for n4 in range(m):                     conn[(0, coder.__outputs__[n4])] = [(1, scheme_2.__inputs__[k+n4])]
        for n5 in range(scheme_2.outputs()):    out.append((1, scheme_2.__outputs__[n5]))
        spectral_ced = sch.merge_schemes([coder, scheme_2], conn, out)

    return spectral_ced, cone, n, coder, decoder

def create_coder(coder, gx1, one, m, n):
    # Функция генерации подсхемы кодера СФК на основе спектрального R-кода
    for num in range(m):
        if one[num] != 1:
            for i in range(one[num]-1):
                if i == 0:
                    coder.__elements__['coder_{}'.format(n)] = ('XOR', [gx1[num][0], gx1[num][1]])
                    n += 1
                else:
                    coder.__elements__['coder_{}'.format(n)] = ('XOR', [gx1[num][i+1], 'coder_{}'.format(n-1)])
                    n += 1
            coder.__outputs__.append('coder_{}'.format(n-1))
        else:   coder.__outputs__.append(gx1[num][0])

    outputs = []
    for j in range(m):  outputs.append(coder.__outputs__[coder.outputs()-m+j])
    coder.__outputs__ = outputs

    return coder, n

def create_decoder(scheme, gx2, input1, one, m, k, n):
    # Функция генерации подсхемы декодера для СФК на основе спектрального R-кода
    decoder = sch.scheme_alt()
    decoder.__inputs__ = input1
    dc = list()

    for i in range(m):  decoder.__inputs__.append('decoder_in_{}'.format(i))

    outputs = []

    for num in range(m):
        if one[num] != 1:
            for i in range(one[num]-1):
                if i == 0:
                    decoder.__elements__['decoder_{}'.format(n)] = ('XOR', [gx2[num][0], gx2[num][1]])
                    n += 1
                else:
                    decoder.__elements__['decoder_{}'.format(n)] = ('XOR', [gx2[num][i + 1], 'decoder_{}'.format(n-1)])
                    n += 1
            decoder.__outputs__.append('decoder_{}'.format(n-1))
        else:   decoder.__outputs__.append(gx2[num][0])

    for i in range(m):  decoder.__outputs__.append(decoder.__inputs__[scheme.outputs() + i])
    for j in range(m):
        decoder.__elements__['_s{}'.format(j)] = ('XOR', [decoder.__outputs__[j], decoder.__outputs__[j+m]])
        outputs.append('_s{}'.format(j))

    decoder.__outputs__ = outputs
    list_1 = outputs[1:]
    outputs = []

    for n_inv in range(len(decoder.__outputs__)):
        decoder.__elements__['n' + decoder.__outputs__[n_inv]] = ('INV', [decoder.__outputs__[n_inv]])
        outputs.append('n' + decoder.__outputs__[n_inv])

    decoder.__outputs__ += outputs
    list_0 = outputs[1:]

    if m - 1 != 1:
        dc = list()

        for vector in it.product((0, 1), repeat=(m-1)): dc.append(list(vector))

        dc = dc[:k]

        for i in range(k):
            for j in range(m-1):
                if dc[i][j] == 0:   dc[i][j] = list_0[j]
                else:               dc[i][j] = list_1[j]

        outputs = []

    if k != 2:
        for i in range(k):
            for j in range(m-2):
                if j == 0:
                    decoder.__elements__['decoder_{}'.format(n)] = ('AND', [dc[i][0], dc[i][1]])
                    decoder.__outputs__ = ['decoder_{}'.format(n)]
                    if (m-1) == 2:  outputs.append('decoder_{}'.format(n))
                    n += 1
                else:
                    decoder.__elements__['decoder_{}'.format(n)] = ('AND', [decoder.__outputs__[j - 1], dc[i][j+1]])
                    decoder.__outputs__.append('decoder_{}'.format(n))
                    if j == m-3:    outputs.append('decoder_{}'.format(n))
                    n += 1

        decoder.__outputs__ = outputs
    else:   decoder.__outputs__ = ['n_s1', '_s1']

    for i in range(k):
        decoder.__elements__['decoder_{}'.format(n)] = ('XOR', [decoder.__inputs__[i], decoder.__outputs__[i]])
        n += 1
        if i == 0:  outputs = ['decoder_{}'.format(n-1)]
        else:       outputs.append('decoder_{}'.format(n-1))

    decoder.__outputs__ = outputs

    if (m-1) != 1:
        for i in range(m-2):
            if i == 0:
                decoder.__elements__['decoder_{}'.format(n)] = ('OR', [list_1[0], list_1[1]])
                n += 1
            else:
                decoder.__elements__['decoder_{}'.format(n)] = ('OR', [list_1[i+1], 'decoder_{}'.format(n-1)])
                n += 1

    if k != 2:  out = 'decoder_{}'.format(n-1)
    else:       out = '_s1'

    in1 = 'decoder_{}'.format(n)
    n += 1
    in2 = 'decoder_{}'.format(n)
    n += 1

    decoder.__outputs__.append('_s0')
    decoder.__outputs__.append('n_s0')

    decoder.__elements__[in1] = ('AND', [out, 'n_s0'])
    decoder.__elements__[in2] = ('AND', ['decoder_0', '_s0'])
    decoder.__elements__['flag'] = ('OR', [in1, in2])
    decoder.__outputs__.append('flag')
    decoder.__elements__['decoder_0'] = ('GND', [])

    return decoder, n

def create_mux(input_1, input_2, k, n, groups=None):
    # Функция генерации подсхемы мультиплексора для СФК на основе спектрального R-кода
    outputs = []
    mux = sch.scheme_alt()
    mux.__inputs__ = input_1 + input_2

    for i in range(k):
        wire_1 = 'mux_{}'.format(n)
        n += 1

        wire_2 = 'mux_{}'.format(n)
        n += 1

        mux.__elements__[wire_1] = ('AND', [mux.__inputs__[k+i+2], 'n_s0'])
        mux.__elements__[wire_2] = ('AND', [mux.__inputs__[i], '_s0'])

        if groups is None:
            mux.__elements__['out_{}'.format(i + 1)] = ('OR', [wire_1, wire_2])
            outputs.append('out_{}'.format(i + 1))
        else:
            mux.__elements__['out_{}'.format(groups[i])] = ('OR', [wire_1, wire_2])
            outputs.append('out_{}'.format(groups[i]))

    mux.__outputs__ = outputs

    return mux, n

def matrix_gx(k, a):
    # Функция генерации порождающей матрицы G(x) для СФК (Спектральный R-код)
    l1 = list()

    for vector in it.product((0, 1), repeat=a): l1.append([1] + list(vector))
    gx = np.transpose(l1[:k])

    return gx

def gx_with_elements(scheme, gx, k, m):

    gx_elements = []

    for i in range(m):
        list_1 = []
        for j in range(k):
            if gx[i][j] == 1:   list_1.append(scheme.__outputs__[:k][j])
        if list_1:              gx_elements.append(list_1)

    return gx_elements

def gx_with_count_one(gx):
    return np.sum(gx, 1)

def error_simulation(ced, cone, rate, n):
    # Проведение моделирования по инжектированию ошибок rate-кратности
    # в схему функционального контроля на основе спектрального R-кода
    t_errors = [0, 0, 0, 0, 0]

    n_inputs = ced.inputs()
    n_elements = ced.elements()
    n_outputs = ced.outputs()

    element_list = sorted(ced.__elements__.keys())

    n_max = 2 ** n_inputs * n_elements

    if rate == 1 and n_max <= n:

        capacity = 2 ** n_inputs
        num = n_max - len(cone) * capacity
        input_list = exhaustive_stimulus(n_inputs)
        protect_index = list()

        for n1 in range(len(cone)):     protect_index.append(element_list.index(cone[n1]))

        for i in range(n_elements):
            if protect_index.count(i) == 0:

                error_list = [0] * n_elements
                error_list[i] = 2 ** capacity - 1

                result = ced.process(input_list, error_list, capacity)
                check = ced.process(input_list, [0] * ced.elements(), capacity)

                t_errors = def_type_of_err(result, check, n_outputs, t_errors, capacity)

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

                    while cone.count(element_list[k]) != 0:

                        k = random.randint(0, ced.elements() - 1)
                        # для инжектирования только в инф. разряды
                        # k = random.randint(0, c_1.elements() - 1)
                        # для инжектирование ошибок в схему без ограничений
                        # k = random.randint(0, c_0.elements() - 1)

                    error_list[k] = 2 ** capacity - 1

                result = ced.process(input_list, error_list, capacity)
                check = ced.process(input_list, [0] * ced.elements(), capacity)

                t_errors = def_type_of_err(result, check, n_outputs, t_errors, capacity)

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

                while cone.count(element_list[k]) != 0:
                    # для инжектирования только в инф. разряды
                    # k = random.randint(0, c_1.elements() - 1)
                    # для инжектирование ошибок в схему без ограничений
                    # k = random.randint(0, c_0.elements() - 1)
                    k = random.randint(0, ced.elements() - 1)
                error_list[k] = 1

            result = ced.process(input_list, error_list)
            check = ced.process(input_list, [0] * ced.elements())

            t_errors = def_type_of_err(result, check, n_outputs, t_errors, 1)

    return t_errors, num

def def_type_of_err(result, check, n_outputs, t_errors, capacity):
    # Функция подсчета ошибок определенного типа
    outputs_check = list()
    pbit_check = list()
    flag_check = list()

    result_pbit = list()
    result_flag = list()
    check_pbit = list()
    check_flag = list()

    result = list(result)
    check = list(check)

    outputs = n_outputs-2

    for i in range(n_outputs):
        result[i] = list(bin(result[i])[2:].zfill(capacity))
        for j in range(capacity):       result[i][j] = int(result[i][j])

    for i in range(n_outputs):
        check[i] = list(bin(check[i])[2:].zfill(capacity))
        for j in range(capacity):       check[i][j] = int(check[i][j])

    result_pbit.append(result[outputs])
    result_flag.append(result[outputs+1])

    check_pbit.append(check[outputs])
    check_flag.append(check[outputs+1])

    result = result[:outputs]
    check = check[:outputs]

    result = np.transpose(result)
    check = np.transpose(check)

    result_pbit = np.transpose(result_pbit)
    result_flag = np.transpose(result_flag)

    check_pbit = np.transpose(check_pbit)
    check_flag = np.transpose(check_flag)

    for i in range(capacity): outputs_check.append(np.array_equal(result[i], check[i]))
    for i in range(capacity): pbit_check.append(np.array_equal(result_pbit[i], check_pbit[i]))
    for i in range(capacity): flag_check.append(np.array_equal(result_flag[i], check_flag[i]))

    for i in range(capacity):
        if outputs_check[i] and pbit_check[i] and flag_check[i]:
            t_errors[0] += 1            # Маскирование ошибки
        elif outputs_check[i] and not pbit_check[i] and flag_check[i]:
            t_errors[1] += 1            # Исправление ошибки
        elif outputs_check[i] and not flag_check[i]:
            t_errors[2] += 1            # Ложная тревога
        elif not outputs_check[i] and not flag_check[i]:
            t_errors[3] += 1            # Обнаружение двукратной ошибки
        elif not outputs_check[i] and flag_check[i]:
            t_errors[4] += 1            # Пропуск ошибки

    return t_errors

def exhaustive_stimulus(n_inputs):
    tmp = 1
    result = []

    for i in range(n_inputs - 1, -1, -1):
        result.append((2**(2**i)-1)*tmp)
        tmp *= (1+2**(2**i))

    return result

def calc_structure_redundancy_spectral(scheme):
    # Вычисление предполагаемой структурной избыточности СФК на основе спектрального R-кода
    # В зависимости от полученных результатов корреляционного анализа вычисляется структурная избыточность для СФК с
    # применением алгоритма кластеризации

    # Число проверочных разрядов
    m = int(np.ceil(np.log2(scheme.outputs()))) + 1
    # Число ЛЭ XOR2 для вычисления проверочных разрядов
    xor = 0
    # Получение матрицы G(x) специального вида
    gx = np.sum(matrix_gx(scheme.outputs(), m - 1), 1).tolist()

    # Определение числа ЛЭ XOR2 необходимых для вычисления проверочных разрядов
    for i in gx:
        if i >= 2:  xor += i - 1

    # Вычисление предплагаемой структурной избыточности СФК без кластеризации
    n = 2 * scheme.elements() + 2 * xor + 3 * m + m * scheme.outputs() + 2 * scheme.outputs() + 2
    predict_redundancy = {0: n}

    # Вычисление предплагаемой структурной избыточности СФК c кластеризацией на 2 и 4 кластера
    for n_pass in 1, 2:
        clusters, groups = clusterization(scheme, n_pass)

        ced = 0

        for group in groups:
            outputs = [scheme.__outputs__[group[i] - 1] for i in range(len(group))]
            scheme_1 = scheme.subscheme_by_outputs(outputs)
            m = int(np.ceil(np.log2(scheme_1.outputs()))) + 1

            xor = 0

            gx = np.sum(matrix_gx(scheme_1.outputs(), m - 1), 1).tolist()

            for i in gx:
                if i >= 2:  xor += i - 1

            ced += scheme_1.elements() + 2 * xor + 3 * m + m * scheme_1.outputs() + 2 * scheme_1.outputs() + 2

        predict_redundancy.update({2 * n_pass:  scheme.elements() + ced + n_pass * (n_pass + 1)})

    return predict_redundancy[0], predict_redundancy[2], predict_redundancy[4]

def toFix(numObj, digits=4):
    # Функция округления числа до digits знаков после запятой
    return f"{numObj:.{digits}f}"
