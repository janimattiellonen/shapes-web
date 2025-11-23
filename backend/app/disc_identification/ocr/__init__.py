"""OCR module for text detection from disc images."""
from .base_ocr import BaseOCR, OCRResult
from .ocr_factory import OCRFactory
from .tesseract_ocr import TesseractOCR
from .easyocr_plugin import EasyOCRPlugin
from .paddleocr_plugin import PaddleOCRPlugin

# Register all OCR plugins
OCRFactory.register_ocr(TesseractOCR)
OCRFactory.register_ocr(EasyOCRPlugin)
OCRFactory.register_ocr(PaddleOCRPlugin)

__all__ = ['BaseOCR', 'OCRResult', 'OCRFactory']
