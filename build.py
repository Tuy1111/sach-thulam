"""Chuyển file PDF thành ảnh trang cho web lật sách.

Cách dùng:
    python build.py "ten-file.pdf"          # mặc định: file .pdf đầu tiên trong thư mục
    python build.py "ten-file.pdf" --width 1800

Ảnh bìa: đặt ở assets/cover.png (tự thêm bìa + trang lót trước trang 1).
Kết quả: thư mục pages/ (ảnh lớn), thumbs/ (ảnh nhỏ), book.js (thông tin sách).
"""
import argparse
import glob
import json
import os
import shutil
import sys

import pymupdf
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))


def trim_border(img, tol=40):
    """Cắt viền xám/trắng mỏng quanh ảnh (thường do xuất file)."""
    px = img.load()

    def gray(p):
        return max(p) - min(p) < 12  # điểm ảnh không màu

    def line_gray(coords):
        pts = list(coords)
        return sum(gray(px[c]) for c in pts) > len(pts) * 0.9

    W, H = img.size
    t = b = l = r = 0
    while t < tol and line_gray((x, t) for x in range(W)): t += 1
    while b < tol and line_gray((x, H - 1 - b) for x in range(W)): b += 1
    while l < tol and line_gray((l, y) for y in range(H)): l += 1
    while r < tol and line_gray((W - 1 - r, y) for y in range(H)): r += 1
    return img.crop((l, t, W - r, H - b))


def make_cover(src, w, h):
    """Đặt ảnh bìa (bất kỳ tỉ lệ) vào giữa khung trang w x h, kéo dài màu mép ảnh ra phần thừa."""
    img = Image.open(src).convert("RGB")
    img = trim_border(img)
    s = min(w / img.width, h / img.height)
    fg = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (w - fg.width) // 2, (h - fg.height) // 2
    out = Image.new("RGB", (w, h), (120, 14, 18))
    out.paste(fg, (x, y))
    dark = (110, 10, 14)
    blur = ImageFilter.GaussianBlur(w / 60)
    if y > 0:  # phía trên / dưới
        for row, top in ((0, True), (fg.height - 1, False)):
            band_h = y if top else h - y - fg.height
            # lấy trung bình vài hàng mép, làm mượt ngang để không bị sọc
            rows = fg.crop((0, max(0, row - 6), fg.width, min(fg.height, row + 7)))
            edge = (rows.resize((max(1, fg.width // 40), 1), Image.BOX)
                    .resize((fg.width, band_h), Image.BILINEAR))
            # tối dần về phía mép trang
            g = Image.linear_gradient("L").resize((fg.width, band_h))
            if top:
                g = g.transpose(Image.FLIP_TOP_BOTTOM)
            edge = Image.composite(Image.new("RGB", edge.size, dark), edge,
                                   g.point(lambda v: round(v * 0.75)))
            out.paste(edge, (x, 0 if top else y + fg.height))
    if x > 0:  # phía trái / phải
        for col, left in ((0, True), (fg.width - 1, False)):
            band_w = x if left else w - x - fg.width
            edge = fg.crop((col, 0, col + 1, fg.height)).resize((band_w, fg.height), Image.BILINEAR)
            out.paste(edge, (0 if left else x + fg.width, y))
    out = out.filter(blur)
    # dán lại ảnh gốc nét, mép mờ nhẹ để hoà vào nền
    mask = Image.new("L", fg.size, 255)
    d = ImageDraw.Draw(mask)
    f = max(1, round(min(fg.size) * 0.03))
    for i in range(f):
        v = round(255 * (i + 1) / f)
        d.rectangle([i, i, fg.width - 1 - i, fg.height - 1 - i], outline=v)
    out.paste(fg, (x, y), mask)
    return out


def make_endpaper(w, h):
    """Trang lót sau bìa: nền đỏ đậm."""
    top, bot = (150, 20, 24), (95, 8, 12)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        k = y / (h - 1)
        d.line([(0, y), (w, y)], fill=tuple(round(a + (b - a) * k) for a, b in zip(top, bot)))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", nargs="?")
    ap.add_argument("--width", type=int, default=1800, help="chiều rộng ảnh trang (px)")
    ap.add_argument("--quality", type=int, default=85, help="chất lượng JPEG")
    ap.add_argument("--title", default=None)
    ap.add_argument("--cover", default=os.path.join(ROOT, "assets", "cover.png"),
                    help="ảnh bìa trước (mặc định assets/cover.png nếu có); --cover '' để bỏ")
    args = ap.parse_args()

    pdf = args.pdf or (sorted(glob.glob(os.path.join(ROOT, "*.pdf"))) or [None])[0]
    if not pdf:
        sys.exit("Không tìm thấy file PDF.")

    pages_dir = os.path.join(ROOT, "pages")
    thumbs_dir = os.path.join(ROOT, "thumbs")
    for d in (pages_dir, thumbs_dir):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)

    doc = pymupdf.open(pdf)
    first = doc[0].rect
    pages, labels = [], []
    w, h = args.width, round(args.width * first.height / first.width)
    tw, th = 260, round(260 * first.height / first.width)
    if args.cover and os.path.exists(args.cover):
        # Bìa + trang lót (giữ trang 01 ở bên phải như sách in)
        for name, label, im in (("0000a-cover.jpg", "Bìa", make_cover(args.cover, w, h)),
                                ("0000b-lot.jpg", "", make_endpaper(w, h))):
            im.save(os.path.join(pages_dir, name), quality=args.quality)
            im.resize((tw, th), Image.LANCZOS).save(os.path.join(thumbs_dir, name), quality=75)
            pages.append(name)
            labels.append(label)
    for i, page in enumerate(doc):
        name = f"{i + 1:04d}.jpg"
        zoom = args.width / page.rect.width
        page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(
            os.path.join(pages_dir, name), jpg_quality=args.quality)
        tz = 260 / page.rect.width
        page.get_pixmap(matrix=pymupdf.Matrix(tz, tz)).save(
            os.path.join(thumbs_dir, name), jpg_quality=75)
        pages.append(name)
        labels.append(str(i + 1))
        print(f"\r{i + 1}/{doc.page_count}", end="", flush=True)
    print()

    title = args.title or doc.metadata.get("title") or os.path.splitext(os.path.basename(pdf))[0]
    data = {"title": title, "width": round(first.width), "height": round(first.height),
            "pages": pages, "labels": labels}
    # book.js (không phải .json) để mở index.html trực tiếp bằng file:// vẫn chạy được
    with open(os.path.join(ROOT, "book.js"), "w", encoding="utf-8") as f:
        f.write("window.BOOK = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"Xong: {len(pages)} trang -> pages/, thumbs/, book.js")


if __name__ == "__main__":
    main()
