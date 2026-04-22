import io
import os
import zipfile
import tarfile


SUPPORTED_ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2"}


def is_archive(filename: str) -> bool:
    """判断文件是否为支持的压缩包格式"""
    lower = filename.lower()
    for ext in SUPPORTED_ARCHIVE_EXTENSIONS:
        if lower.endswith(ext):
            return True
    return False


def _decode_zip_filename(info: zipfile.ZipInfo) -> str:
    """正确解码 ZIP 内文件名。

    Python zipfile 对未设置 UTF-8 标志位(bit 11)的条目默认使用 CP437 解码，
    导致中文文件名乱码。此函数用原始字节重新尝试 UTF-8 → GBK 解码。
    """
    # flag_bits bit 11 = 1 表示文件名已用 UTF-8 编码，无需处理
    if info.flag_bits & 0x800:
        return info.filename

    # 获取原始字节：Python 已用 CP437 解码，需编码回去拿到原始字节
    raw = info.filename.encode("cp437", errors="replace")
    for encoding in ("utf-8", "gbk", "gb2312", "big5"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return info.filename


def _is_pdf_entry(name: str) -> bool:
    """判断压缩包内条目是否为 PDF 文件（忽略隐藏文件和 macOS 资源文件）"""
    if "__MACOSX" in name:
        return False
    basename = os.path.basename(name)
    if basename.startswith("."):
        return False
    return basename.lower().endswith(".pdf")


def extract_pdfs_from_archive(archive_bytes: bytes, archive_filename: str) -> list[dict]:
    """从压缩包中提取所有 PDF 文件。

    Returns:
        [{"filename": "压缩包名/内部文件名", "content": bytes}, ...]
    """
    results = []
    lower = archive_filename.lower()

    if lower.endswith(".zip"):
        results = _extract_from_zip(archive_bytes, archive_filename)
    elif lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")):
        results = _extract_from_tar(archive_bytes, archive_filename)

    return results


def _extract_from_zip(data: bytes, archive_name: str) -> list[dict]:
    results = []
    with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            decoded_name = _decode_zip_filename(info)
            if _is_pdf_entry(decoded_name):
                pdf_bytes = zf.read(info.filename)
                display_name = f"{archive_name}/{os.path.basename(decoded_name)}"
                results.append({"filename": display_name, "content": pdf_bytes})
    return results


def _extract_from_tar(data: bytes, archive_name: str) -> list[dict]:
    results = []
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            if _is_pdf_entry(member.name):
                f = tf.extractfile(member)
                if f is not None:
                    pdf_bytes = f.read()
                    display_name = f"{archive_name}/{os.path.basename(member.name)}"
                    results.append({"filename": display_name, "content": pdf_bytes})
    return results
