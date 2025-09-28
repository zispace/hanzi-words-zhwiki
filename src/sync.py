"""
zhwiki词条
"""

import argparse
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import opencc
from utils.cc import filter_words, format_word
from utils.dl import download_file, fetch_version
from utils.file import split_gz_by_lines, split_words_by_lines

CATEGORIES = ["zhwiki", "zhwiktionary"]
CATE_NAMES = ["main", "more"]

URL_INDEX = "https://dumps.wikimedia.org/{cate}/"
URL_FILE = "https://dumps.wikimedia.org/{cate}/{date}/{cate}-{date}-all-titles-in-ns0.gz"

EN_PUNCTUATION = "!\"#$%&'()*+,./:;<=>?@[\\]^_`{|}~"
ZH_PUNCTUATION = "‘’“”…、。〈〉《》「」『』【】〔〕·！（），：；？～—"
# ZH_PUNCTUATION2 = "§×†‡※□▭〃〻﹏＿／－—─"
CJK_CHAR = "〇一-龥龦-鿿㐀-䶿𠀀-𪛟𪜀-𫜹𫝀-𫠝𫠠-𬺡𬺰-𮯠𰀀-𱍊𱍐-𲎯𮯰-𮹝豈-龎丽-𪘀"
MIN_WORD_LEN = 2


def _now():
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%m:%S%z")


def _update_config(config_file, stats: dict):
    stats["update"] = _now()
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def download_data(date: str, config_file: str, save_gz_dir: str) -> tuple[bool, dict]:
    save_gz_dir = Path(save_gz_dir)
    if not save_gz_dir.exists():
        logging.debug(f"📔 创建目录 = {save_gz_dir}")
        save_gz_dir.mkdir(parents=True)

    if Path(config_file).exists():
        logging.info(f"🔖 读取配置 {config_file}")
        with open(config_file, encoding="utf-8") as f:
            version_stats = json.load(f)
    else:
        version_stats = {
            "update": "",
        }
        for cate in CATEGORIES:
            version_stats[cate] = {}
    old_versions = [version_stats[cate].get("version") for cate in CATEGORIES]

    out = []
    for cate in CATEGORIES:
        version = date
        if not version:
            url = URL_INDEX.format(cate=cate)
            version = fetch_version(url)
            logging.info(f"version = {version}")

        if version:
            file_url = URL_FILE.format(cate=cate, date=version)
            save_file = download_file(file_url, save_gz_dir)
            out.append(save_file)
            version_stats[cate] = {
                "version": version,
                "file": save_file.name,
                "count": None,
            }

    is_updated = False
    for cate, old_version in zip(CATEGORIES, old_versions):
        new_version = version_stats[cate]["version"]
        if new_version != old_version:
            is_updated = True
            break

    if is_updated:
        _update_config(config_file, version_stats)
    return is_updated, version_stats


def convert_gz2text(stats: dict, gz_dir: str, text_dir: str, lines: int) -> dict:
    for cate in CATEGORIES:
        data = stats[cate]
        file = data["file"]
        gz_file = Path(gz_dir, file)
        save_dir = Path(text_dir, cate)
        count = split_gz_by_lines(gz_file, save_dir, lines_per_file=lines)
        stats[cate]["count"] = count

    return stats


# 转化
def format_texts(data_dir: str | Path, save_dir: str | Path, lines: int) -> None:
    zh_word = []
    zh_word_extra = []
    zh_word_more = []
    en_word = []
    unk_word = []

    pattern_postfix = r"_\(([^)]+)\)$"
    pattern_en = rf"^[\w{EN_PUNCTUATION}\- ]+$"
    pattern_has_cjk = rf"[{CJK_CHAR}]+"
    pattern_cjk = rf"^[{CJK_CHAR}]+$"
    pattern_cjk_more = rf"^[{CJK_CHAR}\-·/]+$"
    pattern_cjk_extra = rf"^[{CJK_CHAR}{EN_PUNCTUATION}{ZH_PUNCTUATION}\-\w ]+$"

    files = Path(data_dir).glob("*.txt")
    files = sorted(files)
    logging.info(f"ℹ️ {data_dir} 文件共有 = {len(files)}")

    for file in files:
        logging.debug(f"🔖 读取 {file}")

        with open(file, encoding="utf-8") as f:
            for word in f:
                extra = re.findall(pattern_postfix, word)  # 补充后缀分类词汇
                for w in [word] + extra:
                    flag, out = format_word(
                        w,
                        pattern_postfix,
                        pattern_en,
                        pattern_has_cjk,
                        pattern_cjk,
                        pattern_cjk_more,
                        pattern_cjk_extra,
                        MIN_WORD_LEN,
                    )

                    match flag:
                        case 1:
                            zh_word.append(out)
                        case 2:
                            zh_word_more.append(out)
                        case 3:
                            zh_word_extra.append(out)
                        case 4:
                            en_word.append(out)
                        case _:
                            unk_word.append(out)

    logging.info("初始化 opencc")
    converter = opencc.OpenCC("t2s.json")

    save_data = [zh_word, zh_word_more]
    for words, keyword in zip(save_data, CATE_NAMES):
        save_path = Path(save_dir, keyword)
        filtered_words = filter_words(converter, words)

        logging.info(f"ℹ️ {save_path} 过滤后词数 {len(words)} => {len(filtered_words)}")
        split_words_by_lines(filtered_words, save_path, lines_per_file=lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default="")
    parser.add_argument("--config", type=str, default="version.json")
    parser.add_argument("--gz", type=str, default="temp")
    parser.add_argument("--raw", type=str, default="raw")
    parser.add_argument("--dict", type=str, default="dict")
    parser.add_argument("--lines", type=int, default=100000)

    args = parser.parse_args()
    logging.info(f"↩ 输入参数 = {args}")

    is_updated, stats = download_data(args.date, args.config, args.gz)
    if not is_updated:
        logging.info("未更新")
        return

    stats = convert_gz2text(stats, args.gz, args.raw, args.lines)
    _update_config(args.config, stats)

    for cate in CATEGORIES:
        data_dir = Path(args.raw, cate)
        save_dir = Path(args.dict, cate)
        format_texts(data_dir, save_dir, args.lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s\t%(message)s")

    main()
