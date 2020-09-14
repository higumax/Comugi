import argparse
from pathlib import Path
from comugi.comugi import Comugi
from utils import const

from time import time
from tqdm import tqdm


def argparser():
    default_dictionary = const.DICTIONARIES[0]  # mecab-ipa

    parser = argparse.ArgumentParser(description="Load vocabulary")
    parser.add_argument(
        "--dict_type",
        "-t",
        help="type of dictionary",
        type=str,
        default=default_dictionary,
        choices=const.DICTIONARIES,
    )
    parser.add_argument(
        "--da_path",
        "-da",
        help="Path to double array idx",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.DOUBLEARRAY_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--dict_path",
        "-d",
        help="Path to dictionary",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.DICTIONARY_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--vocab_path",
        "-v",
        help="Path to vocabulary file",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.VOCABULARY_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--mat_path",
        "-m",
        help="Path to transition cost matrix file",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.MATRIX_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--char_range_path",
        "-cr",
        help="Path to char category range file",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.CATEGORY_RANGE_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--char_policy_path",
        "-cp",
        help="Path to char category policy file",
        default=Path(
            f"{const.DATA_DIR}/{default_dictionary}-{const.CATEGORY_POLICY_FILE_SUFFIX}"
        ),
    )
    parser.add_argument(
        "--nbest", "-n", help="N best path analysis", type=int, default=1
    )
    return parser.parse_args()


def run(comugi, sentence, n_best):
    results = comugi.tokenize(sentence, n_best)
    print(f"表層型\t品詞\t品詞1\t原型\t発音")
    for tokens in results:
        for t in tokens:
            node = comugi.get_node(t)
            print(
                f"{node.surface}\t{node.item['pos']}\t{node.item['pos1']}\t{node.item['base']}\t{node.item['pronunciation']}"
            )


if __name__ == "__main__":
    args = argparser()

    start = time()
    comugi = Comugi(
        args.da_path,
        args.dict_path,
        args.vocab_path,
        args.mat_path,
        args.char_range_path,
        args.char_policy_path,
    )
    end = time()
    print(f"time = {end - start:.3f}")

    # message = "「その意見、僕はagreeです」や、「プライオリティ高めでお願いします👊」などの横文字ビジネス会話"

    print("input sentence (press 'exit' to exit)")
    while True:
        message = input()
        message = message.rstrip()
        if message == "exit":
            break

        run(comugi, message, args.nbest)

