"""OCR engine for extracting text from images and scanned PDF pages."""

import logging

logger = logging.getLogger(__name__)


class OCREngine:
    """OCR engine using pytesseract for text extraction."""

    def __init__(self) -> None:
        """Initialize the OCR engine."""
        try:
            import pytesseract
            self._pytesseract = pytesseract
        except ImportError:
            logger.warning("pytesseract not installed, OCR will be unavailable")
            self._pytesseract = None

    def extract_text(self, image_path: str, language: str = "eng+ara") -> str:
        """Extract text from an image file.

        Args:
            image_path: Path to the image file.
            language: Tesseract language codes (e.g., 'eng+ara').

        Returns:
            Extracted text string.
        """
        if self._pytesseract is None:
            logger.error("pytesseract is not available")
            return ""

        try:
            from PIL import Image
            img = Image.open(image_path)
            img = self._preprocess_image(img)
            text = self._pytesseract.image_to_string(img, lang=language)
            confidence = self._get_confidence(img, language)
            logger.info("OCR extraction complete (confidence: %.1f%%)", confidence)
            return text
        except Exception as e:
            logger.error("OCR extraction failed for %s: %s", image_path, e)
            return ""

    def extract_from_pdf_page(self, page_image: object, language: str = "eng+ara") -> str:
        """Extract text from a PDF page image (PIL Image).

        Args:
            page_image: PIL Image object of the page.
            language: Tesseract language codes.

        Returns:
            Extracted text string.
        """
        if self._pytesseract is None:
            logger.error("pytesseract is not available")
            return ""

        try:
            img = self._preprocess_image(page_image)
            text = self._pytesseract.image_to_string(img, lang=language)
            return text
        except Exception as e:
            logger.error("OCR extraction from PDF page failed: %s", e)
            return ""

    def _preprocess_image(self, img: object) -> object:
        """Preprocess image for better OCR results.

        Applies grayscale conversion, thresholding, and denoising.

        Args:
            img: PIL Image object.

        Returns:
            Preprocessed PIL Image.
        """
        try:
            from PIL import ImageFilter

            if hasattr(img, "mode") and img.mode != "L":  # type: ignore[union-attr]
                img = img.convert("L")  # type: ignore[union-attr]

            img = img.point(lambda x: 0 if x < 128 else 255)  # type: ignore[union-attr]
            img = img.filter(ImageFilter.MedianFilter(size=3))  # type: ignore[union-attr]

            return img
        except Exception as e:
            logger.warning("Image preprocessing failed, using original: %s", e)
            return img

    def _get_confidence(self, img: object, language: str) -> float:
        """Get OCR confidence score for an image.

        Args:
            img: PIL Image object.
            language: Tesseract language codes.

        Returns:
            Average confidence score (0-100).
        """
        try:
            data = self._pytesseract.image_to_data(  # type: ignore[union-attr]
                img, lang=language, output_type=self._pytesseract.Output.DICT  # type: ignore[union-attr]
            )
            confidences = [int(c) for c in data["conf"] if int(c) > 0]
            return sum(confidences) / len(confidences) if confidences else 0.0
        except Exception:
            return 0.0
