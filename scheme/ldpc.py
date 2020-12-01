# **********************************************************************************************************************
# ПРОГРАММНЫЙ МОДУЛЬ ГЕНЕРАЦИИ СХЕМЫ ФУНКЦИОНАЛЬНОГО КОНТРОЛЯ НА ОСНОВЕ НИЗКОПЛОТНОСТНОГО LDPC КОДА
# **********************************************************************************************************************
import scheme as sch
import numpy as np
import random
# **********************************************************************************************************************
from scheme.clusterization import clusterization
# **********************************************************************************************************************
def create_ldpc_circuit(scheme, n_pass):

    if n_pass == 0:
        groups = [[i + 1 for i in range(scheme.outputs())]]
    else:
        clusters, groups = clusterization(scheme, n_pass)

    ldpc_ced = create_ced(scheme, groups)

    return ldpc_ced

def create_ced(scheme, groups):

    n_groups = len(groups)  # число разложений (групп)

    schemes = list()
    coders = list()
    decoders = list()

    d1 = {(0, i): [] for i in scheme.__inputs__}
    d2 = {}
    out = []

    for num in range(n_groups):

        outputs = [scheme.__outputs__[groups[num][i] - 1] for i in range(len(groups[num]))]
        scheme_1 = scheme.subscheme_by_outputs(outputs)
        scheme_2, coder, decoder = create_ced_for_group(scheme_1, groups[num], num)
        schemes.append(scheme_2)

        coders.append(coder)
        decoders.append(decoder)

        for i in scheme_1.__inputs__:   d1[(0, i)].append((num + 1, scheme_2.__inputs__[scheme_1.__inputs__.index(i)]))
        d2.update({(0, i): [(num + 1, i)] for i in scheme_1.__outputs__})
        out += [(num + 1, i) for i in scheme_2.__outputs__]

    conn = {}
    conn.update(d1)
    conn.update(d2)

    renamed = {}
    n = 1

    for i in scheme.__elements__.keys():
        if i not in scheme.__outputs__:
            renamed[i] = 'wire_{}'.format(n)
            n += 1

    scheme.rename_labels(renamed)

    ldpc_ced = sch.merge_schemes([scheme] + schemes, conn, out)

    ldpc_ced.__outputs__ = ['out_ced_{}'.format(i + 1) for i in range(scheme.outputs())]
    ldpc_ced.__outputs__ += scheme.__outputs__ + ['{}_out'.format(i) for i in scheme.__outputs__]

    return ldpc_ced, coders, decoders

def create_ced_for_group(scheme, group, num):

    k = scheme.outputs()
    m = k
    p = submatrix_p(k, m)

    coder = sch.replicate(scheme, 1)
    coder = create_coder(coder, p, k + m, num)

    renamed = {i: '{}_out'.format(i) for i in scheme.__outputs__}
    coder.rename_labels(renamed)
    coder.__outputs__ = ['{}_out'.format(i) for i in scheme.__outputs__] + coder.__outputs__

    hx = hx_with_elements(coder.__outputs__, np.hstack([p, np.eye(k, k, dtype=int)]), 2 * k, k)

    d1 = {i: [] for i in scheme.__outputs__}

    for i in range(k):
        for hx_str in hx:
            if coder.__outputs__[i] in hx_str:   d1[scheme.__outputs__[i]] += hx_str

    for i in scheme.__outputs__:
        check_eq = d1[i]
        ind_0 = scheme.__outputs__.index(i)
        for j in range(2):
            index = check_eq.index(coder.__outputs__[ind_0])
            check_eq.remove(check_eq[index])

    inputs = [d1[i] for i in d1]
    for i in range(k):  inputs[i] = [scheme.__outputs__[i]] + inputs[i]

    decoder = sch.scheme_alt()
    decoder.__outputs__ = ['out_ced_{}'.format(i) for i in group]
    decoder.__inputs__ = list(sorted(set([n3 for n2 in range(k) for n3 in inputs[n2]])))

    n = 1
    for i in range(k):  decoder, n = create_decoder(decoder, inputs[i], decoder.__outputs__[i], num, n)

    decoder.__inputs__ = scheme.__outputs__ + coder.__outputs__

    conn = {(0, i): [(1, i)] for i in coder.__outputs__}
    out = [(1, i) for i in decoder.__outputs__] + [(0, '{}_out'.format(i)) for i in scheme.__outputs__]

    ced = sch.merge_schemes([coder, decoder], conn, out)

    return ced, coder, decoder

def create_coder(coder, p, l, num):
    # Функция генерации кодера для СФК на основе низкоплотностного (LDPC) кода
    new_outputs = list()
    n = 1
    x, y = np.where(p == 1)
    y = y.tolist()

    name = 'rbit_{}_{}'

    # Генерация ЛЭ необходимых для вычисления кодером проверочных разрядов генерированной СФК
    for i in range(0, l, 2):
        coder.__elements__[name.format(num, n)] = ('XOR', [coder.__outputs__[y[i]], coder.__outputs__[y[i + 1]]])
        new_outputs.append(name.format(num, n))
        n += 1

    coder.__outputs__ = new_outputs

    return coder

def create_decoder(decoder, inputs, output, num, n):
    # Функция генерирования элементов декодера, реализующих систему раздельных проверок генерированной СФК
    name = 'decoder_{}_{}'
    decoder.__elements__.update({name.format(num, n): ('XOR', [inputs[1], inputs[2]]),
                                 name.format(num, n + 1): ('XOR', [inputs[3], inputs[4]]),
                                 name.format(num, n + 2): ('OR', [inputs[0], name.format(num, n)]),
                                 name.format(num, n + 3): ('NAND', [inputs[0], name.format(num, n)]),
                                 name.format(num, n + 4): ('NAND', [name.format(num, n + 1), name.format(num, n + 2)]),
                                 output: ('NAND', [name.format(num, n + 3), name.format(num, n + 4)])})
    n += 5

    return decoder, n

def submatrix_p(k, m):
    # Функция генерации оптимальной подматрицы P необходимой для составления системы раздельных проверок
    n0 = 0
    n1 = 0
    p = []

    while n0 < 1:
        # Функция генерации случайной подматрицы P
        p1 = list()
        b1 = list()

        for i in range(m):
            p1.append([])
            for j in range(k):  p1[i].append(0)
        for i in range(k):      b1.append(i)

        ones_in_string = 2 * k / m
        if int(ones_in_string) != ones_in_string:   ones_in_string = int(ones_in_string) + 1

        ones_in_string = int(ones_in_string)

        i = 0
        while i < m:
            flag1 = True

            if k > 70 and m < k:
                if i < (m - 3):
                    rand = random.sample(b1, ones_in_string)
                    for i1 in rand: p1[i][i1] = 1

                if i == (m - 1):
                    for i1 in range(k):
                        q = 0
                        for j1 in range(m):
                            if p1[j1][i1] == 1:   q += 1
                        if q < 2:                 p1[i][i1] = 1

                if i == (m - 2):
                    qw = 0
                    for i1 in range(k):
                        if qw < ones_in_string:
                            q = 0
                            for j1 in range(m):
                                if p1[j1][i1] == 1: q += 1
                            if q < 2:
                                p1[i][i1] = 1
                                qw += 1

                if i == (m - 3):
                    qw = 0
                    for i1 in range(k):
                        if qw < ones_in_string:
                            q = 0
                            for j1 in range(m):
                                if p1[j1][i1] == 1: q += 1
                            if q < 2:
                                p1[i][i1] = 1
                                qw += 1

            else:
                if i < (m - 1):
                    rand = random.sample(b1, ones_in_string)
                    for i1 in rand: p1[i][i1] = 1

                if i == (m - 1):
                    for i1 in range(k):
                        q = 0
                        for j1 in range(m):
                            if p1[j1][i1] == 1:     q += 1
                        if q < 2:                   p1[i][i1] = 1

            for i1 in range(k):
                q = 0
                for j1 in range(m):
                    if p1[j1][i1] == 1:     q += 1
                if q > 2:
                    flag1 = False
                    for i2 in range(k):     p1[i][i2] = 0
                    break
            if flag1:   i += 1

        p = np.array(p1)

        # Проверка сгенерированной матрицы на соответствие необходимым для генерации СФК условиям
        flag = independent_equations_check(p)
        if flag:  n0 += 1
        n1 += 1

    return p

def independent_equations_check(p):
    # Функция проверки сгенерированной матрицы на соответствие заданным условиям

    main_flag = True
    for j in range(len(p[0])):
        k = 0
        for i in range(len(p)):
            if p[i][j] == 1:    k += 1
        if k < 2:
            main_flag = False
            break

    if main_flag:
        for j in range(len(p[0])):
            # exitFlag = False

            for i in range(len(p)):
                if p[i][j] == 1:
                    for i1 in range(i + 1, len(p)):
                        if p[i1][j] == 1:
                            k = 0
                            for j1 in range(len(p[0])):
                                if j1 == j: continue
                                if p[i][j1] == 1 & p[i1][j1] == 1:  k += 1
                            # if k == 0:  exitFlag = True
                            if k > 0:   main_flag = False
                            break
                    break
                if not main_flag:
                    break

    return main_flag

def hx_with_elements(outputs, hx, k, m):
    # Функция генерации проверочной матрицы, состоящей только из используемых ЛЭ
    hx_elements = []

    for i in range(m):
        list_1 = []
        for j in range(k):
            if hx[i][j] == 1:
                list_1.append(outputs[:k][j])
        if list_1:
            hx_elements.append(list_1)

    return hx_elements

def error_simulation(scheme, ced, rate, n=1500000):
    # Проведение моделирования по инжектированию ошибок rate-кратности
    # в схему функционального контроля на основе спектрального R-кода
    t_errors = [0, 0, 0]

    n_inputs = ced.inputs()
    n_elements = ced.elements()
    scheme_outputs = scheme.outputs()
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

            t_errors = def_type_of_err(result, check, ced_outputs, scheme_outputs, t_errors, capacity)

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

                t_errors = def_type_of_err(result, check, ced_outputs, scheme_outputs, t_errors, capacity)

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

            t_errors = def_type_of_err(result, check, ced_outputs, scheme_outputs, t_errors, 1)

    return t_errors, num

def def_type_of_err(result, check, ced_outputs, scheme_outputs, t_errors, capacity):
    condition_1, condition_2, condition_3 = [], [], []

    result = list(result)
    check = list(check)

    for i in range(ced_outputs):                        # преобразование списка result в необходимый формат
        result[i] = list(bin(result[i])[2:].zfill(capacity))
        for j in range(capacity):   result[i][j] = int(result[i][j])

    for i in range(ced_outputs):                        # преобразование списка check в необходимый формат
        check[i] = list(bin(check[i])[2:].zfill(capacity))
        for j in range(capacity):   check[i][j] = int(check[i][j])

    res_1 = result[scheme_outputs:][:scheme_outputs]    # выходы основной схемы
    res_2 = result[scheme_outputs:][scheme_outputs:]    # выходы копии основной схемы
    result = result[:scheme_outputs]                    # выходы СФК

    result = np.transpose(result)
    res_1 = np.transpose(res_1)
    res_2 = np.transpose(res_2)

    check = check[:scheme_outputs]
    check = np.transpose(check)

    for i in range(capacity):
        condition_1.append(np.array_equal(result[i], check[i]))     # сравнение выходов СФК и "эталона"
    for i in range(capacity):
        condition_2.append(np.array_equal(result[i], res_1[i]))     # сравнение выходов СФК и основной схемы
    for i in range(capacity):
        condition_3.append(np.array_equal(result[i], res_2[i]))     # сравнение выходов СФК и копии основной схемы

    for i in range(capacity):
        if condition_1[i]:
            if not condition_2[i]:          t_errors[1] += 1
            elif condition_2[i]:
                if condition_3[i]:          t_errors[0] += 1
                elif not condition_3[i]:    t_errors[1] += 1
        elif not condition_1[i]:            t_errors[2] += 1

    return t_errors

def exhaustive_stimulus(n_inputs):
    tmp = 1
    result = []

    for i in range(n_inputs - 1, -1, -1):
        result.append((2**(2**i)-1)*tmp)
        tmp *= (1+2**(2**i))

    return result

def calc_structure_redundancy_ldpc(scheme):
    # Функция вычисления предполагаемой структурной избыточности СФК на основе низкоплотностного (LDPC) кода
    # В зависимости от полученных результатов корреляционного анализа вычисляется структурная избыточность
    # для СФК с применением алгоритма кластеризации

    # Вычисление предплагаемой структурной избыточности СФК без кластеризации
    predict_redundancy = {0: 2 * scheme.elements() + 7 * scheme.outputs()}

    # Вычисление предплагаемой структурной избыточности СФК c кластеризацией на 2 и 4 кластера
    for n_pass in 1, 2:
        clusters, groups = clusterization(scheme, n_pass)

        ced = 0

        for group in groups:
            outputs = [scheme.__outputs__[group[i] - 1] for i in range(len(group))]
            scheme_1 = scheme.subscheme_by_outputs(outputs)
            ced += scheme_1.elements() + 7 * scheme_1.outputs()

        predict_redundancy.update({2*n_pass:  scheme.elements() + ced})

    return predict_redundancy
