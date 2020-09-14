# -*- coding: utf-8 -*-

from enum import Enum
import os
import sys
import time
from tqdm import tqdm


class FLAGS:
    UNUSED = 0
    END = -sys.maxsize


class DoubleArray:
    """
    CRUD on Double array
    Attributes
    ----------
    base : int
        base array of double array
    check : int
        check array of double array
    block_size : int
        one block size of double array
        (size of base and check array are increased by one block_size)
    most_r : int
        rightmost index ever used
        (currently not used)
    """

    def __init__(self):
        self.block_size = 0xFFFF
        self.base = [FLAGS.UNUSED] * self.block_size
        self.check = [FLAGS.UNUSED] * self.block_size

        self.start_point = 1  # from which search begins

    def debug(self):
        xlim = 20
        for i in range(xlim):
            print("|{:3}".format(i + 1), end="")
        print()
        print("----" * xlim)
        for b in self.base[1 : xlim + 1]:
            if b == FLAGS.END:
                print("|  E", end="")
            else:
                print("|{:3}".format(b), end="")
        print()

        for c in self.check[1 : xlim + 1]:
            if c == FLAGS.END:
                print("|  E", end="")
            else:
                print("|{:3}".format(c), end="")
        print()
        print("ARRAY SIZE: ", len(self.base))

    def extend_array(self, diff):
        self.base.extend([FLAGS.UNUSED] * diff)
        self.check.extend([FLAGS.UNUSED] * diff)

    def search(self, sentence):
        code_point = sentence

        s = 1
        result = []
        num_point = 0
        for point in code_point:

            next_s = abs(self.base[s]) + point
            next_check = self.check[next_s]
            if next_check == s:
                s = next_s
                num_point += 1
            else:
                # print("遷移失敗 : ", sentence)
                break  # 遷移失敗→検索終わったので抜ける

            if self.base[s] < 0:
                result.append(code_point[:num_point].decode("utf-8"))
                if self.base[s] == FLAGS.END:
                    break

        return result

    def insert(self, vocabulary):
        """
        Parameters
        ----------
        vocabulary : str
            inserted vocabulary
        Returns
        -------
        """
        code_point = vocabulary

        s = 1
        for point in code_point:
            cur_base = self.base[s]

            if cur_base >= 0.9 * len(self.base):
                self.extend_array(self.block_size)

            if cur_base == FLAGS.UNUSED or cur_base == FLAGS.END:
                # 今見てる番号のbaseは使われていない
                # この場合はこのpointのみの遷移を探せばいい
                x = self._search_position([point])
                self.base[s] = -x if cur_base == FLAGS.END else x
                self.check[x + point] = s
                s = x + point
            else:
                # 今見てるbaseはすでに使われている
                # この場合はこのbaseからの遷移がOKかここからは未踏か競合してるかの3択
                check_pos = abs(self.base[s]) + point
                if self.check[check_pos] == FLAGS.UNUSED:
                    # 未踏
                    self.check[check_pos] = s
                    s = check_pos
                    continue
                elif self.check[check_pos] == s:
                    # 遷移OK
                    s = check_pos
                    continue
                else:
                    # 競合
                    # 競合したコードポイントすべてを置き直す
                    conflict_indices, conflict_points = self._check_confliction(
                        s, point
                    )
                    x = self._search_position(conflict_points)
                    self._resolve_confliction(s, x, conflict_indices, conflict_points)

                    # 引き続き処理する
                    s = abs(self.base[s]) + point
        else:
            if self.base[s] == FLAGS.UNUSED:
                self.base[s] = FLAGS.END
            else:
                self.base[s] = -abs(self.base[s])

    def _check_confliction(self, s, point):
        """
        search and retur一行
        ----------
        s : int
            current position
        point : int
            part of code point (int representation)
        Returns
        -------
        conflict_indices : [int]
            conflicted position indices
        conflict_points : [int]
            conflicted part of code point
        """
        conflict_indices = []
        conflict_points = [point]

        # 高速化版
        cur_base = abs(self.base[s])
        for idx in range(cur_base, cur_base + 0xFF):
            if self.check[idx] == s:
                conflict_indices.append(idx)
                conflict_points.append(idx - cur_base)

        # こっちは正しく動くが遅いもの
        # for idx, check in enumerate(self.check):
        #     if check == s:
        #         conflict_indices.append(idx)
        #         conflict_points.append(idx - abs(self.base[s]))

        return conflict_indices, conflict_points

    # KEY TO SPEED UP🔑
    def _search_position(self, points):
        """
        search for a placeable position
        Parameters
        ----------
        points : [int]
            conflicted part of code point
        Return
        ------
        x : int
            valid position
        """
        x = self.start_point
        while not self._is_placeable(x, points):
            x += 1
        self.start_point = x
        return x

    def _is_placeable(self, x, points):
        """
        Check whether the given position is placeable
        Parameters
        ----------
        x : int
            the given position to be checked
        points : [int]
            points to be placed
        Return
        ------
         : boolean
            placeable or not
        """
        for p in points:
            if self.check[x + p] != FLAGS.UNUSED:
                return False
        return True

    # @profile
    def _resolve_confliction(self, s, x, indices, points):
        # update the conflicted base
        self.base[s] = -x if self.base[s] < 0 else x

        # 新しい遷移先のcheckを更新する
        for p in points:
            self.check[x + p] = s

        # 元遷移先のbaseを新しい場所にコピーする
        for idx, p in zip(indices, points[1:]):
            self.base[x + p] = self.base[idx]

            # 元遷移先からさらに遷移するノードのcheckをつけかえる
            # 競合した文字ごとに行う
            if self.base[idx] == FLAGS.END:
                continue
            else:
                cur_base = abs(self.base[idx])
                for i in range(cur_base, cur_base + 0x1FF):
                    if self.check[i] == idx:
                        self.check[i] = x + p

            # こちらは正しいけど遅いやつ
            # for i in range(1, len(self.base)):
            #     if self.check[i] == idx:
            #         self.check[i] = x + p

        for idx in indices:
            # 競合地点をクリアする
            self.base[idx] = FLAGS.UNUSED
            self.check[idx] = FLAGS.UNUSED

        return

    def build(self, vocabularies):
        for vocab in tqdm(vocabularies):
            self.insert(vocab.encode("utf-8"))

    def save(self, filepath):
        """
        save double array
        Parameters
        ----------
        filepath : str
            filepath
        """
        with open(filepath, mode="w") as f:
            line_base = ",".join(map(str, self.base))
            line_check = ",".join(map(str, self.check))
            f.write(line_base)
            f.write("\n")
            f.write(line_check)

    def load(self, filepath):
        """
        load double array
        Parameters
        ----------
        filepath : str
            filepath
        """
        if not os.path.isfile(filepath):
            print("File open error: {} not found".format(filepath))
            return

        with open(filepath, "r") as f:
            lines = f.readlines()

            if len(lines) != 2:
                print("Format error: ")
                return

            self.base = [int(x) for x in lines[0].split(",")]
            self.check = [int(x) for x in lines[1].split(",")]

