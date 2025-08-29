from typing import List
from PIL import Image
import pytesseract
import cv2
import re

def ocr_lines(image_path: str) -> List[str]:
    if not (Image and pytesseract):
        raise RuntimeError("Pillow + pytesseract required for mockup OCR.")
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    entries = []
    for i in range(len(data["text"])):
        txt = (data["text"][i] or "").strip()
        if not txt: continue
        entries.append({"page": data["page_num"][i], "para": data["par_num"][i], "line": data["line_num"][i],
                        "left": data["left"][i], "top": data["top"][i], "text": txt})
    entries.sort(key=lambda e: (e["page"], e["para"], e["line"], e["left"]))
    joined, buf = [], []
    if entries:
        cur = (entries[0]["page"], entries[0]["para"], entries[0]["line"])
        for e in entries:
            key = (e["page"], e["para"], e["line"])
            if key != cur: joined.append(" ".join(buf)); buf=[]; cur=key
            buf.append(e["text"])
        if buf: joined.append(" ".join(buf))
    return [re.sub(r"\s+"," ", l).strip() for l in joined if l.strip()]
