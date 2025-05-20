"""
PDF深度解析系統 - 支援掃描件與文字型PDF混合處理
版本：2.1.0
核心技術：PDFMiner + Tesseract OCR + 多模態分析
"""

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Tuple

import pdf2image
import pytesseract
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar, LTFigure, LTTextContainer, LTPage

# 設定Tesseract路徑
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# 設定Poppler路徑
os.environ['POPPLER_PATH'] = '/opt/homebrew/Cellar/poppler/25.05.0/bin'

# 設定OCR配置
OCR_CONFIG = '--psm 6 --oem 1 -c preserve_interword_spaces=1 -l chi_tra'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PDFProParser")

class TextCleaner:
    """文本清理與組織工具"""

    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本內容"""
        # 保留中文、標點符號和基本空格
        text = re.sub(r'[^\u4e00-\u9fff\s.,，。！？：；""''（）()、；：""''【】《》]', '', text)
        # 合併多個空格
        text = re.sub(r'\s+', ' ', text)
        # 移除頁碼和頁眉頁腳
        text = re.sub(r'\d+\s*頁', '', text)
        # 清理行首行尾空白
        text = text.strip()
        return text

    @staticmethod
    def organize_content(text: str) -> List[str]:
        """組織文本內容為段落"""
        # 按中文標點符號分割
        sentences = re.split(r'([。！？])', text)
        # 重新組合句子和標點
        sentences = [''.join(i) for i in zip(sentences[::2], sentences[1::2] + [''])]
        # 過濾空句子並清理
        sentences = [TextCleaner.clean_text(s) for s in sentences if s.strip()]

        # 合併短句
        paragraphs = []
        current_para = []

        for sentence in sentences:
            if len(sentence) < 15:  # 調整短句長度閾值
                current_para.append(sentence)
            else:
                if current_para:
                    paragraphs.append(''.join(current_para))
                    current_para = []
                paragraphs.append(sentence)

        if current_para:
            paragraphs.append(''.join(current_para))

        return [p for p in paragraphs if p.strip()]

class PDFStructureAnalyzer:
    """PDF多模態分析引擎"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._validate_system_dependencies()
        self._validate_pdf()

    def _validate_system_dependencies(self):
        """檢查必要系統組件"""
        if not Path(pytesseract.pytesseract.tesseract_cmd).exists():
            raise EnvironmentError("Tesseract OCR未正確安裝")
        if not os.environ.get("POPPLER_PATH", ""):
            logger.warning("建議設定POPPLER_PATH環境變數以提升pdf2image效能")

    def _validate_pdf(self):
        """基礎PDF驗證"""
        if not self.file_path.exists():
            raise FileNotFoundError(f"檔案不存在: {self.file_path}")
        if self.file_path.suffix.lower() != '.pdf':
            raise ValueError("僅支援PDF檔案格式")

    def _ocr_page(self, page_image) -> str:
        """執行OCR辨識"""
        try:
            # 使用優化的OCR配置
            text = pytesseract.image_to_string(
                page_image,
                lang='chi_tra+eng',  # 繁體中文+英文多語系支援
                config=OCR_CONFIG
            )
            return TextCleaner.clean_text(text)
        except pytesseract.TesseractError as e:
            logger.error(f"OCR辨識失敗: {str(e)}")
            return ""

    def _extract_text_blocks(self, page: LTPage) -> List[Dict]:
        """提取文本區塊與佈局資訊"""
        text_blocks = []
        for element in page:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if text:
                    block = {
                        "type": "text",
                        "content": TextCleaner.clean_text(text),
                        "bbox": self._normalize_bbox(element.bbox, page.height),
                        "fonts": list({(char.fontname, char.size) for char in element if isinstance(char, LTChar)})
                    }
                    text_blocks.append(block)
            elif isinstance(element, LTFigure):
                text_blocks.append({
                    "type": "figure",
                    "bbox": self._normalize_bbox(element.bbox, page.height)
                })
        return text_blocks

    def _normalize_bbox(self, bbox: Tuple[float, float, float, float], page_height: float) -> Tuple[float, ...]:
        """座標系統標準化 (左下角原點)"""
        return (
            round(bbox[0], 2),
            round(page_height - bbox[3], 2),
            round(bbox[2], 2),
            round(page_height - bbox[1], 2)
        )

    def hybrid_parse(self) -> Dict:
        """混合模式解析引擎"""
        result = {
            "metadata": {
                "file_size": self.file_path.stat().st_size,
                "file_hash": self._generate_file_hash()
            },
            "pages": []
        }

        try:
            # 第一階段：PDFMiner解析
            with open(self.file_path, 'rb') as f:
                for page_num, page_layout in enumerate(extract_pages(f), 1):
                    page_data = {
                        "page": page_num,
                        "text_blocks": self._extract_text_blocks(page_layout),
                        "ocr_content": []
                    }
                    result["pages"].append(page_data)

            # 第二階段：OCR補強
            with ThreadPoolExecutor() as executor:
                images = pdf2image.convert_from_path(
                    self.file_path,
                    dpi=400,  # 提高DPI以獲得更清晰的圖像
                    grayscale=False,  # 保持彩色以獲取更多細節
                    thread_count=4
                )
                ocr_results = list(executor.map(self._ocr_page, images))

            for page_data, ocr_text in zip(result["pages"], ocr_results):
                # 檢查是否有任何非空的文本區塊
                has_text_content = any(
                    block.get("type") == "text" and block.get("content", "").strip()
                    for block in page_data["text_blocks"]
                )

                if not has_text_content and ocr_text:
                    # 組織OCR結果為段落
                    paragraphs = TextCleaner.organize_content(ocr_text)
                    if paragraphs:
                        page_data["ocr_content"] = [{
                            "type": "ocr_text",
                            "content": paragraphs,
                            "confidence": 95.0
                        }]

            return result

        except Exception as e:
            logger.error(f"解析流程異常: {str(e)}")
            raise

    def _generate_file_hash(self) -> str:
        """產生檔案識別碼"""
        import hashlib
        with open(self.file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

def export_report(result: Dict, output_path: str) -> None:
    """產生結構化報告"""
    # 輸出JSON文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 輸出TXT文件
    txt_path = output_path.rsplit('.', 1)[0] + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("《東坡黃州詞》\n\n")

        for page in result["pages"]:
            # 處理文本塊
            text_blocks = []
            for block in page["text_blocks"]:
                if block["type"] == "text" and block["content"].strip():
                    text_blocks.append(block["content"])

            # 處理OCR內容
            for ocr_block in page["ocr_content"]:
                if ocr_block["type"] == "ocr_text":
                    text_blocks.extend(ocr_block["content"])

            # 清理和組織文本
            if text_blocks:
                # 合併所有文本
                combined_text = " ".join(text_blocks)
                # 使用TextCleaner組織內容
                paragraphs = TextCleaner.organize_content(combined_text)

                # 寫入段落
                for para in paragraphs:
                    if para.strip():
                        f.write(para + "\n\n")

        logger.info(f"文本內容已保存至 {txt_path}")

def main():
    """命令行介面"""
    import argparse
    parser = argparse.ArgumentParser(description='專業級PDF解析工具')
    parser.add_argument('input_pdf', help='輸入PDF檔案路徑')
    parser.add_argument('-o', '--output', help='輸出JSON檔案路徑', default='output.json')
    args = parser.parse_args()

    try:
        analyzer = PDFStructureAnalyzer(args.input_pdf)
        result = analyzer.hybrid_parse()
        export_report(result, args.output)
        logger.info(f"解析完成，結果已儲存至 {args.output}")
    except Exception as e:
        logger.error(f"執行失敗: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
