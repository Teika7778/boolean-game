import copy
import itertools
import tqdm
from graphviz import Digraph
import uuid
import pandas as pd

"""
игорки совершают действия двух различных видов:
1. Выбор переменной из общего набора
2. Присовение значение переменной из их набора

1. Select = 0
2. Set    = 1
"""


class LocalGameState:
    def __init__(self, action, actor, varpull, varref):
        """
        :param action:  действие, которое совершается в ТЕКУЩЕМ ходу (0/1)
        :param actor:   тот, кто совершает это действие (F / V)
        :param varpull: отображение из множеста переменных в {V/F/U}
        :param varref:  отображение из множеста переменных в {0, 1, U}
        """
        self.action = action
        self.player = actor
        self.varpull = varpull
        self.varref = varref

    def isfullref(self):
        """
        :return: Полный ли список переменных
        """
        return all([x != "U" for x in self.varref])

    def isfullpull(self):
        """
        :return: Полный ли пулл переменных
        """
        return all([x != "U" for x in self.varpull])

    def proceed(self, next_action, next_actor):
        """
        Создает все возможные узлы, которые вообще можно создать из данного
        :return:
        """
        states = []
        if self.action == 0:  # SELECT
            for x in self.varpull:
                if self.varpull[x] != "U":
                    continue
                pull = copy.copy(self.varpull)
                pull[x] = self.player
                states.append(LocalGameState(
                    next_action,
                    next_actor,
                    pull,
                    copy.copy(self.varref)
                ))
        else:  # SET
            for x in self.varref:
                if self.varref[x] != "U" or self.varpull[x] != self.player:
                    continue
                ref0 = copy.copy(self.varref)
                ref1 = copy.copy(self.varref)
                ref0[x] = "0"
                ref1[x] = "1"
                states.append(LocalGameState(
                    next_action,
                    next_actor,
                    copy.copy(self.varpull),
                    ref0
                ))
                states.append(LocalGameState(
                    next_action,
                    next_actor,
                    copy.copy(self.varpull),
                    ref1
                ))
        return states


class GameNode:
    def __init__(self, state: LocalGameState):
        self.state = state
        self.parent = None
        self.value = None
        self.child = []


def build_tree(n, seq):
    """

    :param n:  - количество переменных, должно быть четным
    :param seq: последовательность ходов, состоит из пар
    [(F, 0), (V, 0), (F, 1)]
    :return: корень дерева
    """
    initial = GameNode(LocalGameState(
        seq[0][1],
        seq[0][0],
        generate_empty(n),
        generate_empty(n)
    ))
    cur = [initial]
    for i in range(1, len(seq) + 1):
        new_cur = []
        for x in cur:
            local = None
            if i == len(seq):
                local = x.state.proceed(None, None)
            else:
                local = x.state.proceed(seq[i][1], seq[i][0])
            local_nodes = [GameNode(x) for x in local]
            for y in local_nodes:
                new_cur.append(y)
                y.parent = x
            x.child = local_nodes
        cur = new_cur
    return initial


def eval_tree(node: GameNode, f):  # Является ли дерево определенным для V
    if node.state.player is None:  # Мвркер для базовго случая
        # Потому что только в листьях нет игрока для хода
        pos = 0
        for i in range(len(node.state.varref)):
            pos += 2 ** i * int(node.state.varref[i])
            # получаем номер в таблице истинности
        node.value = f[pos]
        return f[pos]
    # Рекурсия
    cur = 1 if node.state.player == "F" else 0
    for c in node.child:
        val = eval_tree(c, f) # значение всех детей
        cur = (cur and val) if node.state.player == "F" else (cur or val)
        # И если ходит F, иначе ИЛИ
    node.value = cur
    return cur


def generate_empty(n):
    # Чтобы избежать дублирования кода
    d = dict()
    for i in range(n):
        d[i] = "U"
    return d


def generate_binary_arrays(n):
    return list(itertools.product([0, 1], repeat=n))


def solve_for_seq(seq):
    # Строим одно дерево для всех функций
    T = build_tree(4, seq)
    # Количесво побед V и количество побед F
    V = [0] * 17
    F = [0] * 17

    for ar in tqdm.tqdm(generate_binary_arrays(16)):
        if eval_tree(T, list(ar)) == 1: # Значение корня
            V[sum(list(ar))] += 1
        else:
            F[sum(list(ar))] += 1

    print_res(V, F)


def print_res(V, F):
    # Функция для красвого оформления вывода
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

    df = pd.DataFrame({
        'V[i]': V,
        'F[i]': F
    })

    df_transposed = df.T
    df_transposed.columns = [f'{i}' for i in range(len(V))]

    df_transposed.index = ['V', 'F']

    print(df_transposed)


solve_for_seq(seq=[("F", 0), ("F", 0), ("V", 0), ("V", 0), ("F", 1), ("F", 1), ("V", 1), ("V", 1)]) # 1.1
solve_for_seq(seq=[("F", 0), ("F", 0), ("V", 0), ("V", 0), ("V", 1), ("V", 1), ("F", 1), ("F", 1)]) # 1.2
solve_for_seq(seq=[("F", 0), ("F", 0), ("V", 0), ("V", 0), ("F", 1), ("V", 1), ("F", 1), ("V", 1)]) # 1.3
solve_for_seq(seq=[("F", 0), ("F", 0), ("V", 0), ("V", 0), ("V", 1), ("F", 1), ("V", 1), ("F", 1)]) # 1.4
solve_for_seq(seq=[("F", 0), ("F", 1), ("V", 0), ("V", 1), ("F", 0), ("F", 1), ("V", 0), ("V", 1)]) # 2.1
solve_for_seq(seq=[("V", 0), ("V", 1), ("F", 0), ("F", 1), ("V", 0), ("V", 1), ("F", 0), ("F", 1)]) # 2.2
