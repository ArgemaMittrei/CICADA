# ******************************************************************************************************************************************
# ПРОГРАММНЫЙ МОДУЛЬ КЛАСТЕРИЗАЦИИ ВЫХОДОВ КОМБИНАЦИОННОЙ СХЕМЫ НА ГРУППЫ
# **********************************************************************************************************************
import itertools as it
import numpy as np
import random
# **********************************************************************************************************************
from collections import Counter
from collections import OrderedDict
# **********************************************************************************************************************
def clusterization(scheme, n_pass=1):
    # Функция выполнения алгоритма кластеризации выходов основной схемы
    # Вычисление числа выходов основной схемы
    k = scheme.outputs()
    list_nodes = [[i for i in range(k)]]
    n_clusters = 2
    result = []

    correlation_matrix = gen_correlation_matrix(scheme)

    for i in range(n_pass):
        result = []
        for n0 in list_nodes:
            if len(n0) == k:    matrix = correlation_matrix[:]
            else:
                matrix = list()
                for n1 in n0:
                    l2 = list()
                    for n2 in n0:   l2.append(toFix(correlation_matrix[n1][n2], 4))
                    matrix.append(l2)

            list_highest_values = calc_highest_values(matrix, len(n0), n_clusters, n0)

            clusters = {}

            for n3 in range(n_clusters): clusters[n3] = [0, [list_highest_values[n3]]]

            used_nodes = list_highest_values[:]
            unused_nodes = list(set(n0) - set(used_nodes))

            for step in range(len(unused_nodes)):
                cost_max = []
                cost_min = []
                nodes_max = []
                nodes_min = []
                nodes = []

                for n4 in unused_nodes:
                    cost = [0, 0]
                    for n5 in range(2):
                        cost[n5] = clusters[n5][0]
                        for n6 in clusters[n5][1]: cost[n5] += correlation_matrix[n4][n6]

                    cost_max.append(round(np.array(cost).max(), 4))
                    cost_min.append(round(np.array(cost).min(), 4))

                    nodes_max.append(cost.index(np.array(cost).max()))

                    if cost.index(np.array(cost).max()) == 1:   nodes_min.append(0)
                    else:                                       nodes_min.append(1)

                    nodes.append(n4)

                cost_max = [float(cm) for cm in cost_max]
                cost_min = [float(cm) for cm in cost_min]

                s1 = np.array(cost_max).max()
                node_max = nodes[cost_max.index(s1)]
                s2 = cost_min[nodes.index(node_max)]
                cluster_min = nodes_min[cost_min.index(s2)]

                if s1 != s2:
                    clusters[cluster_min][0] = cost_min[nodes.index(node_max)]
                    clusters[cluster_min][1].append(node_max)
                else:
                    if len(clusters[0][1]) <= len(clusters[1][1]):
                        clusters[0][0] = cost_min[nodes.index(node_max)]
                        clusters[0][1].append(node_max)
                    else:
                        clusters[1][0] = cost_min[nodes.index(node_max)]
                        clusters[1][1].append(node_max)

                unused_nodes.remove(node_max)

            list_nodes = []

            result.append((toFix(clusters[0][0], 4), clusters[0][1]))
            result.append((toFix(clusters[1][0], 4), clusters[1][1]))

            for n7 in result:   list_nodes.append(n7[1])

    final_clusters = {i + 1: result[i] for i in range(len(result))}

    result = [i[1] for i in result]

    for i in range(len(result)):
        for j in range(len(result[i])): result[i][j] = result[i][j] + 1

    s1 = 0
    for cluster in final_clusters:    s1 += float(final_clusters[cluster][0])

    # Q = np.triu(correlation_matrix).sum()/s1

    return final_clusters, result

def gen_correlation_matrix(scheme, n=1000000):
    # Функция генерации матрицы корреляции
    res = list()
    capacity = n // scheme.elements()

    if capacity != 0:
        for i in range(scheme.elements()):

            input_list = [random.randint(0, 2 ** capacity - 1) for j in range(scheme.inputs())]

            error_list = [0] * scheme.elements()
            error_list[i] = 2 ** capacity - 1

            result = list(scheme.process(input_list, error_list, capacity))
            check = list(scheme.process(input_list, [0] * scheme.elements(), capacity))

            for inp in range(scheme.outputs()):
                result[inp] = list(bin(result[inp])[2:].zfill(capacity))
                for cap in range(capacity):     result[inp][cap] = int(result[inp][cap])

            for inp in range(scheme.outputs()):
                check[inp] = list(bin(check[inp])[2:].zfill(capacity))
                for cap in range(capacity):     check[inp][cap] = int(check[inp][cap])

            result = np.transpose(result)
            check = np.transpose(check)

            l1 = result != check
            l2 = list()
            for item_1 in l1:
                l3 = list()
                for j in range(scheme.outputs()):
                    if item_1[j]: l3.append(j)
                l2.append(l3)

            l3 = list(filter(([]).__ne__, l2))

            res += l3

    capacity = n % scheme.elements()

    if capacity != 0:
        for i in range(scheme.elements()):

            input_list = [random.randint(0, 2 ** capacity - 1) for j in range(scheme.inputs())]

            error_list = [0] * scheme.elements()
            error_list[i] = 2 ** capacity - 1

            result = list(scheme.process(input_list, error_list, capacity))
            check = list(scheme.process(input_list, [0] * scheme.elements(), capacity))

            for inp in range(scheme.outputs()):
                result[inp] = list(bin(result[inp])[2:].zfill(capacity))
                for cap in range(capacity):     result[inp][cap] = int(result[inp][cap])

            for inp in range(scheme.outputs()):
                check[inp] = list(bin(check[inp])[2:].zfill(capacity))
                for cap in range(capacity):     check[inp][cap] = int(check[inp][cap])

            result = np.transpose(result)
            check = np.transpose(check)

            l1 = result != check
            l2 = list()
            for item_1 in l1:
                l3 = list()
                for j in range(scheme.outputs()):
                    if item_1[j]: l3.append(j)
                l2.append(l3)

            l3 = list(filter(([]).__ne__, l2))
            res += l3

    num = len(res)
    res_1 = [str(item_1) for item_1 in res]

    c = Counter(res_1)
    a = [(eval(i), c[i]) for i in c]
    corr_matrix_1 = np.zeros((scheme.outputs(), scheme.outputs()), dtype=np.double)
    for item_0, cnt in a:
        for x, y in it.combinations(item_0, 2):
            corr_matrix_1[x][y] += cnt
            corr_matrix_1[y][x] += cnt

    corr_matrix_2 = corr_matrix_1 / num

    return np.array(corr_matrix_2)

def calc_highest_values(correlation_matrix, k, n_clusters, list_nodes):
    # Функция вычисления наиболее больших значений корреляции в матрицы взаимосвязности
    d1 = {}
    for i in range(k):
        for j in range(k):
            if correlation_matrix[i][j] in d1:
                d1[correlation_matrix[i][j]].append([list_nodes[i], list_nodes[j]])
            else:
                d1[correlation_matrix[i][j]] = [[list_nodes[i], list_nodes[j]]]

    l1 = list(d1.keys())
    l1.sort(reverse=True)

    highest_values = []

    for i in range(len(l1)):
        for j in range(len(d1[l1[i]])):     highest_values.append(d1[l1[i]][j])

    for i in range(len(highest_values)):    highest_values[i] = highest_values[i][0]

    highest_values = list(OrderedDict(zip(highest_values, it.repeat(None))))[0:n_clusters]

    return highest_values

def toFix(numObj, digits=4):
    # Функция округления числа до digits знаков после запятой
    return f"{numObj:.{digits}f}"
