import sys
import csv
import pickle
from collections import defaultdict
from pathlib import Path


def load_dictionary(dict_path, dict_type="mecab-ipa"):
    if (
        dict_type == "mecab-ipa"
        or dict_type == "mecab-juman"
        or dict_type == "mecab-neologd"
        or dict_type == "mecab-unidic"
    ):
        return load_vocabulary(dict_path, dict_type)


def load_cost_matrix(dict_path, dict_type="mecab-ipa"):
    if (
        dict_type == "mecab-ipa"
        or dict_type == "mecab-juman"
        or dict_type == "mecab-neologd"
        or dict_type == "mecab-unidic"
    ):
        mat_def_file = "matrix.def"

    mat_path = Path(f"{dict_path}/{mat_def_file}")
    if not mat_path.is_file():
        print(f"{mat_path} is not found.")
        sys.exit()

    with open(mat_path, mode="r", encoding="euc_jp") as f:
        header = f.readline()
        row, col = map(int, header.split())

        cost_matrix = [[0 for _ in range(col)] for __ in range(row)]

        lines = f.readlines()
        for line in lines:
            r, c, cost = map(int, line.split())
            cost_matrix[r][c] = cost
    return cost_matrix


def format_item(item, is_known, dict_type):
    if (
        dict_type == "mecab-ipa"
        or dict_type == "mecab-juman"
        or dict_type == "mecab-neologd"
        or dict_type == "mecab-unidic"
    ):
        formatted = {
            "surface": item[0],
            "pos": item[4],
            "pos1": item[5],
            "base": item[10],
            "known": is_known,
            "pronunciation": item[12] if is_known else None,
            "lid": int(item[1]),
            "rid": int(item[2]),
            "em_cost": int(item[3]),
        }
    else:
        formatted = {}
    return formatted


def load_vocabulary(dict_path, dict_type):
    dictionary = defaultdict(list)
    count = 0
    vocabularies = []
    for csv_file in Path(dict_path).glob("*.csv"):
        print(f"Loading {csv_file}")
        with open(csv_file, mode="r", encoding="euc_jp") as f:
            reader = csv.reader(f)
            for item in reader:
                item = format_item(item, is_known=True, dict_type=dict_type)
                dictionary[item["surface"]].append(count)
                vocabularies.append(item)
                count += 1

    print(f"Vocabulary size = {len(list(dictionary.keys()))}")
    return dictionary, vocabularies


def load_unk_dictionary(dict_path, dict_type="mecab-ipa"):
    if (
        dict_type == "mecab-ipa"
        or dict_type == "mecab-juman"
        or dict_type == "mecab-neologd"
        or dict_type == "mecab-unidic"
    ):
        unk_def_file = "unk.def"

    unk_path = Path(f"{dict_path}/{unk_def_file}")
    unk_dictionary = defaultdict(list)
    with open(unk_path, "r", encoding="euc_jp") as f:
        reader = csv.reader(f)
        for item in reader:
            item = format_item(item, is_known=False, dict_type=dict_type)
            if (
                item["surface"] not in unk_dictionary
            ):  # currently one item for one char category
                unk_dictionary[item["surface"]].append(item)
    return unk_dictionary


def load_char_def(dict_path, dict_type):
    if (
        dict_type == "mecab-ipa"
        or dict_type == "mecab-juman"
        or dict_type == "mecab-neologd"
        or dict_type == "mecab-unidic"
    ):
        def_file = "char.def"

    char_category_policy = defaultdict(dict)
    char_category_range = defaultdict(list)

    char_def = Path(f"{dict_path}/{def_file}")
    with open(char_def, "r", encoding="euc_jp") as f:
        lines = f.readlines()

        for line in lines:

            # ignore comment line
            if line.startswith("#"):
                continue

            # ignore comment part
            elems = line.rstrip().split()
            ignore_idx = len(elems)
            for i, elem in enumerate(elems):
                if elem.startswith("#"):
                    ignore_idx = i
            elems = elems[:ignore_idx]

            # ignore blank line
            if len(elems) == 0:
                continue

            # char category definition
            if len(elems) == 4:
                category = elems[0]
                char_category_policy[category]["invoke"] = int(elems[1])
                char_category_policy[category]["group"] = int(elems[2])
                char_category_policy[category]["length"] = int(elems[3])

            # category mapping : match 0xXX..0xYY ZZZZ or 0xXX ZZZZ
            if len(elems) == 2:
                code_map = elems[0].split("..")
                map_range = []
                if len(code_map) == 2:  # type 0xXXX..0xYY
                    map_range = tuple(
                        map(lambda x: int(x, 16), code_map)
                    )  # convert str to int
                else:  # type 0xXXXX ZZZZ
                    tmp = int(code_map[0], 16)  # convert str to int
                    map_range = (tmp, tmp)

                category = elems[1]
                char_category_range[category].append(map_range)

    return char_category_policy, char_category_range
