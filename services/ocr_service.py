import pdfplumber
import pytesseract
from PIL import Image
import os
from config import TESSERACT_CMD

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

class OCRService:
    """Service for extracting text from PDF and image files"""
    
    @staticmethod
    def extract_text(file_path, file_type):
        """
        Extract text from a file based on its type
        
        Args:
            file_path: Path to the file
            file_type: Type of file (pdf, jpg, png)
        
        Returns:
            str: Extracted text
        """
        try:
            if file_type.lower() == 'pdf':
                return OCRService._extract_from_pdf(file_path)
            elif file_type.lower() in ['jpg', 'jpeg', 'png']:
                return OCRService._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    @staticmethod
    def _extract_from_pdf(file_path):
        """Extract text from PDF using pdfplumber"""
        text_content = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
            return '\n\n'.join(text_content)
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    @staticmethod
    def _extract_from_image(file_path):
        """Extract text from image using pytesseract"""
        try:
            image = Image.open(file_path)
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            raise Exception(f"Image OCR failed: {str(e)}")
    
    @staticmethod
    def is_ocr_available():
        """Check if OCR tools are available"""
        try:
            # Check if tesseract is available
            pytesseract.get_tesseract_version()
            return True
        except:
            return False

