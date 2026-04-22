import re

import fitz  # PyMuPDF

# ---------- 姓名提取相关常量 ----------

# 简历中常见的字段标签（用于识别 key-value 结构及过滤非姓名行）
_LABEL_KEYWORDS = {
    "姓名", "性别", "年龄", "出生", "生日", "出生日期", "出生年月",
    "籍贯", "民族", "政治面貌", "婚姻", "婚姻状况", "身高", "体重",
    "学历", "学位", "专业", "毕业院校", "毕业学校", "毕业时间", "学校",
    "电话", "手机", "邮箱", "邮件", "微信", "地址", "现居", "现居住地",
    "求职意向", "期望薪资", "期望岗位", "工作年限", "工作经验",
    "个人简历", "简历", "个人信息", "基本信息", "联系方式", "应聘",
    "教育背景", "教育经历", "工作经历", "项目经历", "项目经验",
    "自我评价", "个人优势", "技能特长", "专业技能", "获奖情况",
    "证书", "语言能力", "兴趣爱好",
}

# 将标签集合编译为正则，用于判断一行是否为纯标签
_LABEL_RE = re.compile(
    r"^(" + "|".join(re.escape(k) for k in _LABEL_KEYWORDS) + r")$"
)

# 用于匹配 "姓名：张三" / "姓名: 张三" / "姓名 张三" 格式
_NAME_LABEL_INLINE = re.compile(
    r"(?:姓\s*名|名\s*字)[：:\s]\s*([\u4e00-\u9fff]{2,4})"
)

# 英文 "Name: First Last" 格式（单行匹配，避免跨行）
_NAME_LABEL_EN = re.compile(
    r"(?:name)[：:\s]\s*([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2})\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# 简历开头常见的标题行，需跳过
_HEADER_RE = re.compile(
    r"^(个人简历|简历|resume|curriculum\s*vitae|cv|个人信息|基本信息|联系方式|求职意向|应聘)",
    re.IGNORECASE,
)


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """从 PDF 字节流中提取文本内容"""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()


def _is_label_or_noise(text: str) -> bool:
    """判断文本是否为字段标签或常见噪声词"""
    clean = text.strip()
    if _LABEL_RE.match(clean):
        return True
    if _HEADER_RE.match(clean):
        return True
    # 含数字（电话、日期等）
    if re.search(r"\d", clean):
        return True
    # 含 @（邮箱）
    if "@" in clean:
        return True
    return False


# ---------- 文件名提取姓名 ----------

# 简历文件名中常见的干扰词，需要剔除
_FILENAME_NOISE_WORDS = {
    "简历", "履历", "求职", "应聘", "简介",
    "个人简历", "个人", "信息",
    "resume", "cv",
    "更新", "最新", "正式", "定稿",
}

# 机构/公司名特征词（segment 包含这些词则不是人名）
_ORG_INDICATORS = {
    "股份", "科技", "公司", "集团", "有限", "控股", "实业", "工业",
    "网络", "技术", "咨询", "服务", "传媒", "教育", "医疗", "金融",
    "银行", "证券", "保险", "投资", "地产", "建设", "药业", "生物",
    "电子", "通信", "软件", "互联网", "商贸", "置业", "智能",
    "大学", "学院", "学校", "研究院", "研究所",
    "媒体", "平台", "电商", "企业", "物流", "快递",
    "汽车", "能源", "环保", "化工", "航空", "交通",
}

# 岗位/职位名特征词
_JOB_INDICATORS = {
    "工程师", "开发", "经理", "总监", "主管", "设计师", "分析师",
    "架构师", "运维", "测试", "产品", "运营", "助理", "实习",
    "专员", "顾问", "算法", "前端", "后端", "全栈", "数据",
    "研发", "技术员", "程序员", "负责人", "总裁", "副总",
}

# 文件名中常见的分隔符
_FILENAME_SEPARATORS = re.compile(r"[-_\s·•、。，．（）()\[\]]+")


def _is_likely_person_name(text: str) -> bool:
    """判断 2-4 个汉字的文本是否像人名（而非公司名或职位名）"""
    for indicator in _ORG_INDICATORS:
        if indicator in text:
            return False
    for indicator in _JOB_INDICATORS:
        if indicator in text:
            return False
    return True


def extract_name_from_filename(filename: str) -> str | None:
    """从简历文件名中提取候选人姓名。

    常见命名模式：
    - 张三-Java开发-北京大学.pdf
    - 李四_简历.pdf
    - 王五简历.pdf
    - 简历-赵六.pdf
    - John Smith Resume.pdf
    """
    import os
    # 去掉路径前缀和扩展名
    basename = os.path.basename(filename)
    name_part = os.path.splitext(basename)[0]

    # 如果是压缩包提取的文件，取最后一段
    if "/" in name_part:
        name_part = name_part.rsplit("/", 1)[-1]

    # 按分隔符拆分
    segments = [s.strip() for s in _FILENAME_SEPARATORS.split(name_part) if s.strip()]

    # 提取候选中文姓名 segment
    def _clean_seg(seg):
        cleaned = seg.strip()
        for noise in _FILENAME_NOISE_WORDS:
            cleaned = cleaned.replace(noise, "")
        return cleaned.strip()

    # 第一轮：优先匹配 2-3 字中文名（高置信度人名）
    for seg in segments:
        cleaned = _clean_seg(seg)
        if cleaned and re.fullmatch(r"[\u4e00-\u9fff]{2,3}", cleaned) and _is_likely_person_name(cleaned):
            return cleaned

    # 第二轮：尝试 4 字中文名（如 欧阳修文），但需通过过滤
    for seg in segments:
        cleaned = _clean_seg(seg)
        if cleaned and re.fullmatch(r"[\u4e00-\u9fff]{4}", cleaned) and _is_likely_person_name(cleaned):
            return cleaned

    # 再尝试找英文姓名：先将相邻的英文 segment 合并（因为空格作为分隔符已拆分）
    en_parts = []
    for seg in segments:
        cleaned = seg.strip()
        if cleaned.lower() in _FILENAME_NOISE_WORDS:
            # 如果有累积的英文部分，先尝试匹配
            if en_parts:
                candidate = " ".join(en_parts)
                m = re.fullmatch(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}", candidate)
                if m:
                    return m.group()
                en_parts = []
            continue
        if re.fullmatch(r"[A-Za-z]+", cleaned):
            en_parts.append(cleaned)
        else:
            if en_parts:
                candidate = " ".join(en_parts)
                m = re.fullmatch(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}", candidate)
                if m:
                    return m.group()
                en_parts = []

    # 检查尾部累积
    if en_parts:
        candidate = " ".join(en_parts)
        m = re.fullmatch(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}", candidate)
        if m:
            return m.group()

    return None


def extract_candidate_name(filename: str, text: str | None = None) -> str | None:
    """统一的姓名提取入口：优先从文件名提取，失败时兜底用文本提取"""
    name = extract_name_from_filename(filename)
    if name:
        return name
    if text:
        return _extract_name_from_text(text)
    return None


def _extract_name_from_text(text: str) -> str | None:
    """从简历文本中提取候选人姓名（兜底策略）。

    提取策略（按优先级）：
    1. 在前 15 行中查找显式 "姓名：XXX" 标签模式（同行 key:value）
    2. 查找 "姓名" 标签后紧跟的下一行作为姓名值（表格式 PDF 常见）
    3. 查找 "Name: XXX" 英文标签模式
    4. 兜底：在前 5 行中寻找独立的纯中文姓名行或纯英文姓名行
       （需排除字段标签、地名等噪声）

    Returns:
        提取到的姓名字符串，失败时返回 None
    """
    if not text:
        return None

    lines = text.strip().split("\n")
    # 取前 15 行用于标签匹配
    head_lines = lines[:15]
    head_text = "\n".join(head_lines)

    # ---- 策略 1：同行 "姓名：XXX" ----
    m = _NAME_LABEL_INLINE.search(head_text)
    if m:
        return m.group(1)

    # ---- 策略 2：表格式 "姓名\n张三" ----
    for i, line in enumerate(head_lines):
        stripped = line.strip()
        if re.fullmatch(r"姓\s*名", stripped):
            # 往下找第一个非空行作为姓名值
            for j in range(i + 1, min(i + 3, len(head_lines))):
                val = head_lines[j].strip()
                if not val:
                    continue
                if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", val) and not _is_label_or_noise(val):
                    return val
                break

    # ---- 策略 3：英文 "Name: XXX" ----
    m = _NAME_LABEL_EN.search(head_text)
    if m:
        return m.group(1)

    # ---- 策略 4：兜底 - 前 5 行中寻找独立姓名行 ----
    # 跟踪上一行是否为标签（标签后的值行不一定是姓名，如 "籍贯\n安徽"）
    prev_is_label = False
    for line in lines[:5]:
        stripped = line.strip()
        if not stripped:
            prev_is_label = False
            continue
        if _is_label_or_noise(stripped):
            prev_is_label = True
            continue
        if len(stripped) > 20:
            prev_is_label = False
            continue

        # 如果上一行是标签且不是 "姓名"，跳过（防止匹配标签的值，如"籍贯"后的"安徽"）
        if prev_is_label:
            prev_is_label = False
            continue

        # 纯中文姓名行（2-4 汉字）
        if re.fullmatch(r"[\u4e00-\u9fff]{2,4}", stripped):
            return stripped

        # 纯英文姓名行
        m = re.fullmatch(r"[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,2}", stripped)
        if m:
            return m.group()

        prev_is_label = False

    return None
