from io import BytesIO
from pathlib import Path

import fitz
from PIL import Image


def compress_pdf(pdf_path: str, out_dir: str, dpi: int, img_type: str = "png", method: int = 0, progress_cb=None) -> str:
    source_path = Path(pdf_path)
    target_dir = Path(out_dir) if out_dir else source_path.parent

    merges = []
    first_file = None
    with fitz.open(str(source_path)) as doc:
        total = len(doc)
        if total == 0:
            raise ValueError("PDF为空，无法压缩")

        for i, page in enumerate(doc.pages(), start=0):
            img = page.get_pixmap(dpi=dpi)
            img_bytes = img.pil_tobytes(format=img_type)
            image = Image.open(BytesIO(img_bytes))
            if i == 0:
                first_file = image
            pix: Image.Image = image.quantize(colors=256, method=method).convert('RGB')
            merges.append(pix)

            if progress_cb is not None:
                progress_cb(((i + 1) / total) * 100)

    if first_file is None:
        raise ValueError("无法读取PDF首页")

    out_name = f"{source_path.stem}_in_{dpi}dpi.pdf"
    out_path = target_dir / out_name

    first_file.save(
        str(out_path),
        "pdf",
        save_all=True,
        append_images=merges[1:],
    )
    return str(out_path)
