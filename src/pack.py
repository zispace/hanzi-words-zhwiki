"""
合并打包RIME词典文件
"""

import argparse
import json
import logging
import re
from pathlib import Path
from textwrap import dedent

from pypinyin import lazy_pinyin

CATEGORIES = ["zhwiki", "zhwiktionary"]
CATE_NAMES = ["main", "more"]
CHAR_8105 = "㧐㧟䏝𬉼㤘𠳐䥽䁖𥻗䦃㸆𠙶𬣙𨙸𬇕䜣𬣞𬘓𫭟𫭢㧑𫇭𫐄㕮𫵷㑇𣲘𣲗𬇙㳇𬣡𫸩䢺𨚕𫘜𬘘𫘝䢼𦭜㭎𬨂𬀩𬀪㟃𬬩㑊𫍣𬣳𬩽𬮿𬯀𫰛𬳵𬳶䌹𫠊㛃𬍛𬜬𦰡㭕䴓䶮𪾢𪨰𫓧𬬮𬬱𬬭䏡𦙶㶲㳚㳘𬘡𬳽𬘩𫄧𪟝𬍤𫭼𬜯䓖𬂩𫠆𨐈𬌗𫑡𪨶𬬸𬬻𬬹𬬿𬭁𫢸𫗧𬊈𬒈𨺙㛚𬳿𫄨𬘫䂮𫮃㙍䓫䓬䓨䓛䴕㫰𬱖𬟽䎃𫓯𫟹𫟼㿠䝙䏲𠅤䴔𬇹𬍡㥄𬤇𫍯𬤊𫍲𬯎𬘬𬘭𬴂𫘦𫟅𬘯𫘧㙘𪣻𡎚𬃊𬷕𫐐𬹼𧿹𫶇𫖮𬭊𨱇𫓶𬭎𫖯䐃𬱟𫛭㺄𫷷𬮱𬊤𣸣㴔㛹𬴃𫘨䴖𤧛𬪩𬒔䃅𬨎𫐓䣘𫫇㬊𫓹𬭚𬭛䅟𬕂䲟𬶋𬶍𦝼𫔶𫌀𫖳𫘪𫘬𫞩𡐓𪤗𣗋𬸘䃎𬒗𥔲𫚖䴗㬎𨱏𬭤㙦𫚕𬶐𬶏𩽾𬸚㽏㮾𬤝𬙂㻬䗖㠇𬭩䴘𩾃㵐𬸣𫍽𬴊𬞟𥕢𫟦𬺈𫠜㬚䗛㠓𪩘𬭬𨱑𬭯𫗴𬸦𫄷𤩽㘎𬭳𬭶𫔍𬭸𨱔𬭼𫔎𬸪䲠𬶟𬶠䗪𬶨𦈡𫄸𬟁𥖨䗴䲢𦒍䎖䴙𬙊㰀𬶭𩾌𨟠𬶮𨭉㸌𬙋𤫉𬺓𫚭"

WORD_SUFFIXES = ["列表", "对照表"]


def is_ignore(w: str) -> bool:
    """忽略 XX列表等词语"""
    return len(w) > 2 and w.endswith(tuple(WORD_SUFFIXES))


def merge_data(data_dir):
    files = []
    for cate in CATEGORIES:
        files += sorted(Path(data_dir, cate, CATE_NAMES[0]).glob("*.txt"))

    logging.info(f"读取词语, {data_dir}, 文件共{len(files)}")
    words = set()
    for file in files:
        with open(file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    words.add(line)
    logging.info(f"合计词语共 {len(words)}")

    # CJK基本区+规范字8105补充
    pattern_cjk = rf"^[〇\u4e00-\u9fff{CHAR_8105}]+$"
    word_common = []
    word_rare = []
    for w in words:
        if re.match(pattern_cjk, w):
            word_common.append(w)
        else:
            word_rare.append(w)

    logging.info(f"常用/规范词语共 {len(word_common)}")
    logging.info(f"生僻字词语共 {len(word_rare)}")

    word_common = sorted(word_common, key=lambda x: (len(x), x))
    word_rare = sorted(word_rare, key=lambda x: (len(x), x))
    return word_common, word_rare


def save_rime_file(save_dir, name, version, words):
    fm = """
    # Rime dictionary
    # encoding: utf-8
    #
    #
    ---
    name: {name}
    version: "{version}"
    sort: by_weight
    ...
    """
    logging.info("解析拼音")
    words_py = parse_pinyin(words)

    save_dir = Path(save_dir)
    if not save_dir.exists():
        logging.debug(f"创建目录 {save_dir}")
        save_dir.mkdir(parents=True)
    save_file = Path(save_dir, f"{name}.dict.yaml")
    logging.info(f"保存到{save_file}, 词数 = {len(words_py)} / {len(words)}")

    fm_out = fm.format(name=name, version=version)
    fm_out = dedent(fm_out).strip()
    with open(save_file, "w", encoding="utf-8") as f:
        f.write(fm_out + "\n")
        for w in words_py:
            f.write(w + "\n")


def parse_pinyin(words: list[str]) -> list[str]:
    out = []
    for w in words:
        if not w:
            out.append(w)

        py = lazy_pinyin(w)  # TODO 未考虑多音字
        py_str = " ".join(py)
        if len(py) != len(w) or not re.match(r"^[a-z ]+$", py_str):
            logging.debug(f"Ignore word = {w}, pinyin = {py_str}")
            continue
        out.append("\t".join([w, py_str]))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="version.json")
    parser.add_argument("--dict", type=str, default="dict")
    parser.add_argument("--output", type=str, default="release")

    args = parser.parse_args()
    logging.info(f"↩ 输入参数 = {args}")

    data_dir = args.dict
    save_dir = args.output
    config_file = args.config
    with open(config_file, encoding="utf-8") as f:
        stats = json.load(f)
        version = stats[CATEGORIES[0]]["version"]

    word_common, word_rare = merge_data(data_dir)
    word_common = [w for w in word_common if not is_ignore(w)]
    word_rare = [w for w in word_rare if not is_ignore(w)]

    word_common_main = [w for w in word_common if len(w) <= 4]
    word_common_more = [w for w in word_common if len(w) > 4]

    save_rime_file(save_dir, "zhwiki", version, word_common_main)
    save_rime_file(save_dir, "zhwiki-ext", version, word_common_more + [""] + word_rare)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s\t%(message)s")

    main()
