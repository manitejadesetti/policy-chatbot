from unstructured.partition.pdf import partition_pdf


class FileParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def parse(self) -> str:
        if self.file_path.endswith(".pdf"):
            return self._parse_pdf()
        elif self.file_path.endswith(".txt"):
            return self._parse_txt()
        else:
            raise ValueError(f"Unsupported file type for '{self.file_path}'.")

    def _parse_pdf(self) -> str:
        # Placeholder for PDF parsing logic
        # In a real implementation, you would use a library like PyPDF2 or pdfminer.six
        return "Parsed content from PDF."

    def _parse_txt(self) -> str:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise ValueError(f"Failed to read text file: {e}")
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        

class UnstructuredDataParser(FileParser):
    def __init__(self, file_path: str):
        super().__init__(file_path)

    def parse(self) -> str:
        if self.file_path.endswith(".pdf"):
            try:
                elements =  partition_pdf(self.file_path)
                return elements
            except Exception as e:
                raise ValueError(f"Failed to parse PDF with unstructured library: {e}")
        else:
            return super().parse()
        
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        chunks = []        
        current_chunk = ""
        for el in text:
            if len(current_chunk) + len(el.text) < 1000:
                current_chunk += "\n" + el.text
            else:
                chunks.append(current_chunk)
                current_chunk = el.text
        if current_chunk:
            chunks.append(current_chunk)
        return chunks


