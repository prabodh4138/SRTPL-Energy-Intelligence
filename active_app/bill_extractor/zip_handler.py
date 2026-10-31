import io
import os
import zipfile
from typing import List, Union, Any


class NamedBytesIO(io.BytesIO):
    """
    BytesIO wrapper that preserves original filename for Streamlit and PDF parsers.
    """
    def __init__(self, initial_bytes: bytes, name: str):
        super().__init__(initial_bytes)
        self.name = name

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-compatible accessor for backward compatibility."""
        if key in ("name", "filename"):
            return self.name
        if key in ("bytes", "content", "raw_bytes"):
            return self.getvalue()
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None:
            raise KeyError(key)
        return val


def extract_pdfs_from_inputs(inputs: Any) -> List[Any]:
    """
    Normalizes any input (single file, list of files, paths, or ZIP archives)
    into a flat list of processable PDF file-like objects or path strings.

    Supports:
      - .pdf files (direct pass-through)
      - .zip files (recursively unpacks all contained PDFs in-memory)
    """
    if inputs is None:
        return []

    if not isinstance(inputs, (list, tuple)):
        items = [inputs]
    else:
        items = list(inputs)

    result_pdfs = []

    for item in items:
        # Determine filename
        filename = getattr(item, "name", None) or (str(item) if isinstance(item, (str, os.PathLike)) else "")
        fname_lower = filename.lower()

        # CASE 1: ZIP Archive
        if fname_lower.endswith(".zip"):
            try:
                if isinstance(item, (str, os.PathLike)):
                    with zipfile.ZipFile(item, "r") as zf:
                        _extract_from_zip(zf, result_pdfs)
                else:
                    if hasattr(item, "seek"):
                        item.seek(0)
                    zip_bytes = item.read() if hasattr(item, "read") else item
                    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
                        _extract_from_zip(zf, result_pdfs)
            except Exception as e:
                # Corrupt or unreadable zip; skip safely
                pass

        # CASE 2: PDF Document
        elif fname_lower.endswith(".pdf"):
            result_pdfs.append(item)

    return result_pdfs


def _extract_from_zip(zf: zipfile.ZipFile, accumulator: List[Any]):
    for entry in zf.namelist():
        entry_lower = entry.lower()
        if entry_lower.endswith(".pdf") and not entry_lower.startswith("__macosx") and not os.path.basename(entry).startswith("."):
            raw_pdf_bytes = zf.read(entry)
            clean_name = os.path.basename(entry)
            named_stream = NamedBytesIO(raw_pdf_bytes, name=clean_name)
            accumulator.append(named_stream)
