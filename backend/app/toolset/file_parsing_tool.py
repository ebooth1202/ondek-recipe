from .base_imports import *


class FileParsingTool:
    """Tool for parsing recipe files"""

    def __init__(self):
        self.name = "parse_recipe_file"
        self.description = "Parse uploaded files to extract recipe information"

    def execute(self, file_content: bytes, filename: str, file_type: str, file_extension: str) -> Optional[Dict]:
        """Parse recipe information from various file types"""
        try:
            logger.info(f"Parsing file: {filename}, type: {file_type}")

            extracted_text = ""

            if file_type == "application/pdf" or file_extension == ".pdf":
                extracted_text = self._extract_text_from_pdf(file_content)
            elif file_type.startswith("image/") or file_extension.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                extracted_text = self._extract_text_from_image(file_content)
            elif file_type == "text/csv" or file_extension == ".csv":
                extracted_text = self._extract_text_from_csv(file_content)
            elif file_type.startswith("text/") or file_extension in [".txt", ".md"]:
                extracted_text = file_content.decode('utf-8', errors='ignore')
            else:
                try:
                    extracted_text = file_content.decode('utf-8', errors='ignore')
                except:
                    raise ValueError(f"Unsupported file type: {file_type}")

            if not extracted_text.strip():
                logger.warning(f"No text could be extracted from {filename}")
                return None

            return {
                "file_name": filename,
                "file_type": file_type,
                "parsed_text": extracted_text,
                "confidence": 0.8 if len(extracted_text) > 100 else 0.3
            }

        except Exception as e:
            logger.error(f"Error parsing file {filename}: {e}")
            return None

    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            return "PDF parsing not implemented yet"
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _extract_text_from_image(self, file_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            return "Image OCR not implemented yet"
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""

    def _extract_text_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file"""
        try:
            csv_text = file_content.decode('utf-8', errors='ignore')
            csv_file = io.StringIO(csv_text)

            reader = csv.DictReader(csv_file)
            rows = list(reader)

            if not rows:
                return csv_text

            headers = rows[0].keys() if rows else []
            recipe_columns = ['name', 'title', 'recipe', 'ingredients', 'instructions', 'directions', 'steps']

            has_recipe_data = any(
                any(col.lower() in header.lower() for col in recipe_columns)
                for header in headers
            )

            if has_recipe_data:
                formatted_text = "Recipe Data from CSV:\n\n"
                for i, row in enumerate(rows, 1):
                    formatted_text += f"Recipe {i}:\n"
                    for key, value in row.items():
                        if value and value.strip():
                            formatted_text += f"{key}: {value}\n"
                    formatted_text += "\n"
                return formatted_text
            else:
                return csv_text

        except Exception as e:
            logger.error(f"Error extracting text from CSV: {e}")
            return file_content.decode('utf-8', errors='ignore')