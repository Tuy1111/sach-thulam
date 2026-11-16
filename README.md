# Web lật sách từ PDF

## Xem sách
- Mở thẳng `index.html` bằng trình duyệt (nháy đúp), hoặc chạy server: `python -m http.server 8000` rồi vào http://localhost:8000

## Đổi sang file PDF khác
1. Chép file PDF vào thư mục này (cần `pip install pymupdf`).
2. Chạy: `python build.py "ten-file.pdf" --title "Tên sách"`
   - `--width 2400` nếu muốn ảnh nét hơn (nặng hơn).
3. Mở lại `index.html`.

## Ảnh bìa
- Ảnh bìa nằm ở `assets/cover.png`. Đổi ảnh khác thì thay file này rồi chạy lại `build.py`.
- Ảnh bìa tỉ lệ nào cũng được: script tự đặt vào giữa trang và kéo dài màu nền cho kín.
- Sau bìa có 1 trang lót màu đỏ để trang 01 vẫn nằm bên phải như sách in.
- Không muốn bìa: `python build.py --cover ""`

## Đưa lên mạng
Chỉ cần tải lên các mục sau (không cần file PDF gốc):
`index.html`, `book.js`, `vendor/`, `pages/`, `thumbs/`
Dùng được với GitHub Pages, Netlify, Vercel, hoặc bất kỳ hosting tĩnh nào.

## Thao tác
- Lật trang: bấm/kéo góc trang, vuốt (điện thoại), phím ← →, hoặc nút ◀ ▶
- Home / End: trang đầu / cuối · gõ số trang rồi Enter để nhảy trang
- ☰ danh sách trang · 🔍 hoặc nháy đúp / phím Z để phóng to (lăn chuột để zoom, kéo để di chuyển, Esc để đóng)
- F: toàn màn hình · 🔊 bật/tắt tiếng lật trang
- Đường link tự nhớ trang đang xem (`#p=51`), có thể gửi cho người khác.
