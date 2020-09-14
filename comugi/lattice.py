import sys
import heapq
from copy import deepcopy, copy
from functools import lru_cache


class Vocab:
    def __init__(self, item):
        self.surface = item["surface"]
        self.length = len(self.surface)
        self.item = item

    def __str__(self):
        return self.surface
        # return f"{self.surface}, {self.min_prev.surface}"

    def get_lid(self):
        return self.item["lid"]

    def get_rid(self):
        return self.item["rid"]

    def get_em_cost(self):
        return self.item["em_cost"]


class VocabContainer:
    def __init__(self, vocab_list):
        self.vocabs = tuple(vocab_list)

    def __getitem__(self, x):
        return self.vocabs[x]


class NodeContainer:
    def __init__(self):
        self.nodes = []

    def __getitem__(self, x):
        return self.nodes[x]

    def __len__(self):
        return len(self.nodes)

    def add(self, vocab):
        self.nodes.append(vocab)
        return len(self.nodes)

    def clear(self):
        self.nodes = []


class NodePointer:
    def __init__(self, ptr, lid=0, rid=0, em_cost=0, length=0, min_cost=sys.maxsize):
        self.ptr = ptr

        self.em_cost = em_cost
        self.lid = lid
        self.rid = rid
        self.length = length

        self.min_prev = None
        self.min_cost = min_cost

        self.next = None

    def copy(self):
        r = NodePointer(self.ptr, self.lid, self.rid, self.em_cost, self.length, self.min_cost)
        r.min_prev = self.min_prev
        return r

    def get_node(self, node_container):
        return node_container[self.ptr]

class CostManager:
    def __init__(self, matrix):
        self.matrix = matrix

    def get_emission_cost(self, node_ptr):
        return node_ptr.em_cost

    def get_transition_cost(self, lnode_ptr, rnode_ptr):
        return self.matrix[lnode_ptr.lid][rnode_ptr.rid]


class Lattice:
    def __init__(self):
        self.node_container = NodeContainer()
        self.begin_nodes = [[]]
        self.end_nodes = [[]]
        self.sentence = ""
        self._length = 0

        self.bos_node = None
        self.eos_node = None

    # def debug(self):
    #     for i in range(self._length + 1):
    #         print(f"B{i} : ", end="")
    #         for node in self.begin_nodes[i]:
    #             print(f"{node.surface}", end=" ")
    #         print("")
    #         print(f"E{i} : ", end="")
    #         for node in self.end_nodes[i]:
    #             print(f"{node.surface}", end=" ")
    #         print("")
    #         print("-" * 30)
    #     pass

    def __len__(self):
        return len(self.node_container)

    def set_bos_node(self):
        return NodePointer(ptr=-1, min_cost=0)

    def set_eos_node(self):
        return NodePointer(ptr=-2)

    def set_sentence(self, sentence):
        self.sentence = sentence
        self._length = len(sentence)

        self.node_container.clear()
        self.begin_nodes = [[] for _ in range(self._length + 1)]
        self.end_nodes = [[] for _ in range(self._length + 1)]

        # insert bos, eos node
        self.bos_node = self.set_bos_node()
        self.eos_node = self.set_eos_node()
        self.end_nodes[0].append(self.bos_node)
        self.begin_nodes[self._length].append(self.eos_node)

    def add_node(self, node):
        self.node_container.add(node)

    def insert(self, begin, node_ptr, node, length):
        # append vocab in use
        self.add_node(node)

        # insert node pointer to node in use
        self.begin_nodes[begin].append(node_ptr)
        end = begin + length
        self.end_nodes[end].append(node_ptr)
        return node_ptr

    def calc_forward_cost(self, cm):
        for (begin_nodes, end_nodes) in zip(self.begin_nodes, self.end_nodes):
            for rnode in begin_nodes:
                rnode_em_cost = rnode.em_cost
                for lnode in end_nodes:
                    trans_cost = cm.get_transition_cost(lnode, rnode)
                    cost = lnode.min_cost + rnode_em_cost + trans_cost
                    if cost < rnode.min_cost:
                        rnode.min_cost = cost
                        rnode.min_prev = lnode

    def get_best_path(self):
        e = self.begin_nodes[self._length][0]  # EOS node
        best_path = [e]
        while e.min_prev != None:
            best_path.append(e.min_prev)
            e = e.min_prev

        return [best_path[::-1]]

    def get_nbest_path(self, cm, n_best):
        e = self.begin_nodes[self._length][0]  # EOS node
        q = [
            (0, 0, self._length, id(e), e)
        ]  # tuple means (priority, backward_cost, current position, id, node)
        count = 0

        n_best_path = []
        while len(q) != 0:
            _, cost, cur_pos, _, node = heapq.heappop(q)
            if node.min_prev == None:  # reach BOS node
                path = []
                while node.next is not None:
                    path.append(node)
                    node = node.next
                n_best_path.append(path)
                count += 1
                if count == n_best:
                    break
            else:
                for lnode in self.end_nodes[cur_pos]:
                    backward_cost = (
                        cost + cm.get_transition_cost(lnode, node) + lnode.em_cost
                    )
                    forward_cost = lnode.min_cost
                    priority = forward_cost + backward_cost

                    tmp_lnode = lnode.copy()

                    heapq.heappush(
                        q,
                        (
                            priority,
                            backward_cost,
                            cur_pos - lnode.length,
                            id(tmp_lnode),
                            tmp_lnode,
                        ),
                    )

                    if len(q) % 10000 == 0:
                        print(len(q), sys.getsizeof(q))

        return n_best_path

    def calc_path(self, cm, best_n):
        self.calc_forward_cost(cm)

        if best_n == 1:
            return self.get_best_path()
        else:
            return self.get_nbest_path(cm, best_n)
