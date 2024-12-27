from embedding_text import PDFEmbedder

# Singleton instance
_pdf_embedder = None

def get_embedder():
    """Get or create PDFEmbedder instance."""
    global _pdf_embedder
    if _pdf_embedder is None:
        _pdf_embedder = PDFEmbedder()
    return _pdf_embedder
