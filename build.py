from pathlib import Path
from time import time
import argparse
import pickle
from comugi.double_array import DoubleArray
import utils.dict_loader as dl
from utils import const


def argparser():
    parser = argparse.ArgumentParser(description="Build up dictionaries.")
    parser.add_argument(
        "--dict_path",
        "-d",
        help="Path to the dictionary",
        type=str,
        default=Path(f"{const.DATA_DIR}/mecab-ipadic-2.7.0-20070801"),
    )
    parser.add_argument(
        "--dict_type", "-t", help="type of dictionary", type=str, default="mecab-ipa"
    )
    return parser.parse_args()


if __name__ == "__main__":

    args = argparser()

    # create data directory if not exist
    if not Path(const.DATA_DIR).is_dir():
        Path(const.DATA_DIR).mkdir()

    # load all vocabularies and save them in readable format to comugi
    print("-" * 20)
    print("Load word dictionary")   
    dictionary, vocabularies = dl.load_dictionary(args.dict_path, args.dict_type)

    # load unknown word dictionary
    unk_dictionary = dl.load_unk_dictionary(args.dict_path, args.dict_type)

    # merge normal dictionary and unknown word dictionary
    sz = len(vocabularies)
    for k, v in unk_dictionary.items():
        vocabularies.extend(v)
        l = len(v)
        dictionary[k].extend(list(range(sz, sz + l)))
        sz += l

    # dict save
    dict_savepath = Path(
        f"{const.DATA_DIR}/{args.dict_type}-{const.DICTIONARY_FILE_SUFFIX}"
    )
    vocab_savepath = Path(
        f"{const.DATA_DIR}/{args.dict_type}-{const.VOCABULARY_FILE_SUFFIX}"
    )
    with open(dict_savepath, "wb") as f:
        pickle.dump(dictionary, f, protocol=4)
    with open(vocab_savepath, "wb") as f:
        pickle.dump(vocabularies, f, protocol=4)
    print("Done.")


    # extract surface from dictionary
    surfaces = list(dictionary.keys())
    surfaces.sort()

    # double array build up
    print("-" * 20)
    print("Build up double array index.")
    da = DoubleArray()
    start = time()
    da.build(surfaces)
    end = time()
    da_savepath = Path(
        f"{const.DATA_DIR}/{args.dict_type}-{const.DOUBLEARRAY_FILE_SUFFIX}"
    )
    da.save(da_savepath)
    print("Done.")
    print(f"Elapsed time = {end - start:.3f}[sec]")

    # load transition cost matrix file
    print("-" * 20)
    print("Load transition cost matrix")
    cm = dl.load_cost_matrix(args.dict_path, args.dict_type)
    mat_savepath = Path(f"{const.DATA_DIR}/{args.dict_type}-{const.MATRIX_FILE_SUFFIX}")
    with open(mat_savepath, "wb") as f:
        pickle.dump(cm, f, protocol=4)
    print("Done.")


    # load char category policy
    print("-" * 20)
    print("Load char category policy")
    char_cat_policy, char_cat_range = dl.load_char_def(args.dict_path, args.dict_type)

    cat_policy_savepath = Path(
        f"{const.DATA_DIR}/{args.dict_type}-{const.CATEGORY_POLICY_FILE_SUFFIX}"
    )
    with open(cat_policy_savepath, "wb") as f:
        pickle.dump(char_cat_policy, f, protocol=4)

    cat_range_savepath = Path(
        f"{const.DATA_DIR}/{args.dict_type}-{const.CATEGORY_RANGE_FILE_SUFFIX}"
    )
    with open(cat_range_savepath, "wb") as f:
        pickle.dump(char_cat_range, f, protocol=4)

    print("Done.")
