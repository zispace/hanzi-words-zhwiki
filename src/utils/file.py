import gzip
import logging
from pathlib import Path
import shutil


def split_gz_by_lines(
    input_gz_path, save_dir, output_prefix="", lines_per_file=100000, encoding="utf-8"
) -> int:
    """
    将 .gz 文本文件按行数分割为多个 .gz 小文件。

    :param input_gz_path: 输入的 .gz 文件路径
    :param output_prefix: 输出文件前缀，如 'part'
    :param lines_per_file: 每个小文件包含的行数
    :param encoding: 文本编码
    """
    part_num = 1
    line_count = 0
    out_file = None
    save_dir = Path(save_dir)
    if save_dir.exists():
        logging.warning(f"⚠️ 删除目录 {save_dir}")
        shutil.rmtree(save_dir)

    logging.debug(f"📔 创建目录 = {save_dir}")
    save_dir.mkdir(parents=True, exist_ok=True)
    try:
        logging.info(f"🔖 读取gz文件: {input_gz_path}")
        with gzip.open(input_gz_path, "rt", encoding=encoding) as f_in:
            f_in.readline()  # 忽略第一行
            for line in f_in:
                if line_count % lines_per_file == 0:
                    # 关闭上一个输出文件（如果不是第一个）
                    if out_file is not None:
                        out_file.close()

                    # 打开新的输出 .gz 文件
                    name = f"{part_num:03d}.txt"
                    if output_prefix:
                        name = output_prefix.strip("_ ") + "_" + name
                    output_path = Path(save_dir, name)
                    # out_file = gzip.open(output_path, 'wt', encoding=encoding)
                    out_file = open(output_path, "w", encoding=encoding)
                    logging.debug(f"🖊 正在写入: {part_num} / {output_path}")
                    part_num += 1

                out_file.write(line)
                line_count += 1

        # 关闭最后一个文件
        if out_file is not None:
            out_file.close()

        logging.info(f"✅ 共分割为 {part_num - 1} 个文件，总行数: {line_count}")

    except Exception as e:
        logging.error(f"❌ 错误: {e}")
        if out_file and not out_file.closed:
            out_file.close()

    return line_count


def split_words_by_lines(
    words, save_dir, output_prefix="", lines_per_file=100000, encoding="utf-8"
) -> int:
    part_num = 1
    line_count = 0
    out_file = None

    save_dir = Path(save_dir)
    if save_dir.exists():
        logging.warning(f"⚠️ 删除目录 {save_dir}")
        shutil.rmtree(save_dir)

    logging.debug(f"📔 创建目录 = {save_dir}")
    save_dir.mkdir(parents=True, exist_ok=True)
    for line in words:
        if line_count % lines_per_file == 0:
            # 关闭上一个输出文件（如果不是第一个）
            if out_file is not None:
                out_file.close()

            # 打开新的输出 .gz 文件
            name = f"{part_num:03d}.txt"
            if output_prefix:
                name = output_prefix.strip("_ ") + "_" + name
            output_path = Path(save_dir, name)
            out_file = open(output_path, "w", encoding=encoding)
            logging.debug(f"🖊 正在写入: {part_num} / {output_path}")
            part_num += 1

        out_file.write(line + "\n")
        line_count += 1

    # 关闭最后一个文件
    if out_file is not None:
        out_file.close()
    logging.info(f"✅ 共分割为 {part_num - 1} 个文件，总行数: {line_count}")
    return line_count


def merge_files(data_dir, output_file):
    files = Path(data_dir).glob("*.txt")
    files = sorted(files)

    logging.info(f"ℹ️ {data_dir} 文件共有 = {len(files)}")
    count = 0
    with open(output_file, "w", encoding="utf-8") as fw:
        for file in files:
            logging.debug(f"🔖 读取 {file}")
            with open(file, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
                        fw.write(line)

    logging.debug("保存完成，共{count}行")
