from app.services.file_parser import UnstructuredDataParser
from app.services.rag_service import RAGService


class PDFProcessor:

    def __init__(self, pdf_path, rag_service: RAGService):
        self.pdf_path = pdf_path
        self.rag_service = rag_service
        self.pdf_parser = UnstructuredDataParser(pdf_path)



    def process_pdf(self):
        text = self.pdf_parser.parse()
        chunks = self.pdf_parser.chunk_text(text)
        self.rag_service.embed_and_store(chunks)
        # Placeholder for additional processing logic
        return {"message": "PDF processed successfully"}
    