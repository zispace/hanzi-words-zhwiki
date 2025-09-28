import logging
from pathlib import Path
import re
import httpx


def fetch_version(url: str) -> str | None:
    try:
        response = httpx.get(url)
        response.raise_for_status()
        # if response.status_code != 200:
        #     return None
        dates = re.findall(r'<a href="(\d+)/?">', response.text)
        if len(dates) == 0:
            return None
        latest = max(dates)
        logging.info(f"✅ 获取最新日期版本为 = {latest}")
        return latest
    except httpx.HTTPError as e:
        logging.error(f"❌ HTTP 错误: {e}")
    except Exception as e:
        logging.error(f"❌ 下载失败: {e}")
    return None


def download_file(url: str, save_dir: str, chunk_size: int = 8192) -> Path | None:
    """
    使用 httpx 流式下载大文件并保存到本地。

    :param url: 要下载的文件 URL
    :param local_filename: 本地保存的文件名
    :param chunk_size: 每次读取的数据块大小（默认 8KB）
    """
    local_filename = Path(save_dir, url.split("/")[-1])
    if local_filename.exists():
        logging.warning(f"⚠️ 文件存在 {local_filename}")
        return local_filename
    try:
        with httpx.stream("GET", url, timeout=None) as response:
            response.raise_for_status()  # 检查 HTTP 错误
            with open(local_filename, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=chunk_size):
                    f.write(chunk)
        logging.info(f"✅ 文件已成功下载 {local_filename}")
        return local_filename
    except httpx.HTTPError as e:
        logging.error(f"❌ HTTP 错误: {e}")
    except Exception as e:
        logging.error(f"❌ 下载失败: {e}")
    return None
