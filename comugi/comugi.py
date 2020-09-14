import sys
import pickle
from .double_array import DoubleArray
from .lattice import Lattice, CostManager, Vocab, NodePointer, VocabContainer
from copy import deepcopy
from functools import lru_cache


class Comugi:
    def __init__(
        self,
        double_array_path,
        dictitonary_path,
        vocabulary_path,
        matrix_path,
        char_range_path,
        char_policy_path,
    ):
        self.da = DoubleArray()
        self.da.load(double_array_path)

        self.lattice = Lattice()

        self.dictionary = self.load(dictitonary_path)

        v = self.load(vocabulary_path)
        vocabs = list(map(lambda x: Vocab(x), v))
        self.vocab_container = VocabContainer(vocabs)
        del v, vocabs

        mat = self.load(matrix_path)
        self.cost_manager = CostManager(mat)

        self.char_category_range = self.load(char_range_path)
        self.char_category_policy = self.load(char_policy_path)

    def load(self, filepath):
        try:
            with open(filepath, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(e)
            sys.exit()

    @lru_cache(maxsize=2048)
    def detect_char_category(self, c):
        ord_c = ord(c)
        for key in self.char_category_range.keys():
            segments = self.char_category_range[key]
            for seg in segments:
                if seg[0] <= ord_c and ord_c <= seg[1]:
                    return key
        # warnings.warn(f"Letter {c} was not found in any category.")
        return self.detect_char_category("#")

    def filter_unknown_words(self, sentence, char_category):
        idx = 0
        unk_words = [[] for _ in range(len(sentence))]
        while idx < len(sentence):
            cat_name = char_category[idx]
            unk_group = self.char_category_policy[cat_name]["group"]
            unk_length = self.char_category_policy[cat_name]["length"]

            tmp_idx = idx

            # group same category letters as long as possible
            if unk_group == 1:
                tmp_word = ""
                while idx < len(sentence):
                    cur_cat_name = char_category[idx]
                    cur_char = sentence[idx]
                    if cat_name == cur_cat_name:
                        tmp_word += cur_char
                        idx += 1
                    else:
                        break
                unk_words[tmp_idx].append(tmp_word)

            # group same category letters by predefined length
            else:
                tmp_word = ""
                t = 0
                while t < unk_length and idx + t < len(sentence):
                    cur_cat_name = char_category[idx + t]
                    cur_char = sentence[idx + t]
                    if cat_name == cur_cat_name:
                        t += 1
                        tmp_word += cur_char
                        unk_words[tmp_idx].append(tmp_word)
                    else:
                        break
                idx += 1

        return unk_words

    def set_node_pointer(self, idx, vocab):
        lid = vocab.get_lid()
        rid = vocab.get_rid()
        em_cost = vocab.get_em_cost()
        return NodePointer(idx, lid, rid, em_cost, len(vocab.surface))

    def set_lattice(self, sentence):
        self.lattice.set_sentence(sentence)
        char_category = [self.detect_char_category(c) for c in sentence]

        unk_words_list = self.filter_unknown_words(sentence, char_category)

        vocab_counter = 0

        def regist_unk_words(unk_words, category_name):
            idxs = self.dictionary[category_name]
            for unk_word in unk_words:
                for idx in idxs:
                    vocab = self.vocab_container[idx]
                    vocab.surface = unk_word
                    node_ptr = self.set_node_pointer(idx, vocab)
                    self.lattice.insert(
                        begin=i, node_ptr=node_ptr, node=vocab, length=len(unk_word)
                    )

        def regist_words(words):
            for common_prefix_str in words:
                idxs = self.dictionary[common_prefix_str]
                for idx in idxs:
                    vocab = self.vocab_container[idx]
                    node_ptr = self.set_node_pointer(idx, vocab)
                    self.lattice.insert(
                        begin=i,
                        node_ptr=node_ptr,
                        node=vocab,
                        length=len(common_prefix_str),
                    )

        for i in range(len(sentence)):
            cat_name = char_category[i]

            # check whether to invoke unknown word handling
            unk_invoke = self.char_category_policy[cat_name]["invoke"]

            # It assumes the categories of unk_words beginning from the same idx are all identical.
            if unk_invoke == 1:  # always invoke
                unk_words = unk_words_list[i]
                regist_unk_words(unk_words, cat_name)

            else:  # invoke when any vocabulary was not found in (known) dictionary
                input_str = sentence[i:]
                res = self.da.search(input_str.encode("utf-8"))
                if len(res) > 0:
                    regist_words(res)
                else:
                    unk_words = unk_words_list[i]
                    regist_unk_words(unk_words, cat_name)

    def get_node(self, node_ptr):
        idx = node_ptr.ptr
        if idx == -1 or idx == -2:
            return Vocab(
                {
                    "surface": "__BOS__" if idx == -1 else "__EOS__",
                    "pos": None,
                    "pos1": None,
                    "base": None,
                    "pronunciation": None,
                    "lid": 0,
                    "rid": 0,
                    "em_cost": 0,
                }
            )
        else:
            return node_ptr.get_node(self.vocab_container)

    def tokenize(self, sentence, best_n=1):
        assert best_n >= 1
        assert type(best_n) is int
        self.set_lattice(sentence)
        # print(len(self.lattice))
        tokens = self.lattice.calc_path(self.cost_manager, best_n)
        return tokens
