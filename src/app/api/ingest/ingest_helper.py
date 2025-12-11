from pathlib import Path
from llama_index.core.schema import Document
from llama_index.core.readers import StringIterableReader
from llama_index.core.readers.base import BaseReader
from llama_index.core.readers.json import JSONReader

def _try_loading_included_file_formats() -> dict[str, type[BaseReader]]:
    try:
        from llama_index.readers.file.docs import (  # type: ignore
            DocxReader,
            HWPReader,
            PDFReader,
        )
        from llama_index.readers.file.epub import EpubReader  # type: ignore
        from llama_index.readers.file.image import ImageReader  # type: ignore
        from llama_index.readers.file.ipynb import IPYNBReader  # type: ignore
        from llama_index.readers.file.markdown import MarkdownReader  # type: ignore
        from llama_index.readers.file.mbox import MboxReader  # type: ignore
        from llama_index.readers.file.slides import PptxReader  # type: ignore
        from llama_index.readers.file.tabular import PandasCSVReader  # type: ignore
        from llama_index.readers.file.flat import FlatReader
        from llama_index.readers.file.video_audio import (  # type: ignore
            VideoAudioReader,
        )
    except ImportError as e:
        raise ImportError("`llama-index-readers-file` package not found") from e

    default_file_reader_cls: dict[str, type[BaseReader]] = {
        ".hwp": HWPReader,
        ".pdf": PDFReader,
        ".docx": DocxReader,
        ".pptx": PptxReader,
        ".ppt": PptxReader,
        ".pptm": PptxReader,
        ".jpg": ImageReader,
        ".png": ImageReader,
        ".jpeg": ImageReader,
        ".mp3": VideoAudioReader,
        ".mp4": VideoAudioReader,
        ".csv": PandasCSVReader,
        ".epub": EpubReader,
        ".md": MarkdownReader,
        ".mbox": MboxReader,
        ".ipynb": IPYNBReader,
        ".txt": FlatReader,
        ".log": FlatReader,
        ".ini": FlatReader,
    }
    return default_file_reader_cls

# Patching the default file reader to support other file types
FILE_READER_CLS = _try_loading_included_file_formats()
FILE_READER_CLS.update(
    {
        ".json": JSONReader,
    }
)

class IngestionHelper:

    @staticmethod
    def transform_file_into_documents(
        file_name: str, file_data: Path
    ) -> list[Document]:
        documents = IngestionHelper._load_file_to_documents(file_name, file_data)
        for document in documents:
            document.metadata["file_name"] = file_name
        IngestionHelper._exclude_metadata(documents)
        return documents
    
    @staticmethod
    def _load_file_to_documents(file_name: str, file_data: Path) -> list[Document]:
        extension = Path(file_name).suffix
        reader_cls = FILE_READER_CLS.get(extension)
        if reader_cls is None:
            # Read as a plain text
            string_reader = StringIterableReader()
            raw_docs = string_reader.load_data([file_data.read_text()])
        else:
            raw_docs = reader_cls().load_data(file_data)

        cleaned_docs = []
        for doc in raw_docs:
            # 清理文本中的 \u0000 空字符
            clean_text = doc.text.replace("\u0000", "")
            # 创建新的 Document 对象（保留原 metadata 和其他属性）
            cleaned_doc = Document(
                text=clean_text,  # LlamaIndex Document 支持通过构造函数赋值 text
                metadata=doc.metadata.copy(),
                doc_id=doc.doc_id,
                embedding=doc.embedding,
                excluded_embed_metadata_keys=doc.excluded_embed_metadata_keys,
                excluded_llm_metadata_keys=doc.excluded_llm_metadata_keys,
                relationships=doc.relationships.copy() if doc.relationships else {}
            )
            cleaned_docs.append(cleaned_doc)

        return cleaned_docs

    @staticmethod
    def _exclude_metadata(documents: list[Document]) -> None:

        for document in documents:
            document.metadata["doc_id"] = document.doc_id
            # We don't want the Embeddings search to receive this metadata
            document.excluded_embed_metadata_keys = ["doc_id"]
            # We don't want the LLM to receive these metadata in the context
            document.excluded_llm_metadata_keys = ["file_name", "doc_id", "page_label"]