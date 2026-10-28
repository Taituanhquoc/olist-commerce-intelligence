# HƯỚNG DẪN SỬ DỤNG PORTFOLIO OLIST

**Bước 1 — Xem thành quả:** Mở `promise_lab/index.html` trong Chrome hoặc Edge để thấy dashboard mô phỏng phân bổ ngân sách. Thử điều chỉnh 5 thanh điều khiển, đặc biệt là `Pilot budget`, `Relative reduction in lateness` và `Value of one late delivery avoided`.

**Bước 2 — Xem code mới:** Mở `src/promise_lab.py`, đọc `tests/test_promise_lab.py`, `sql/04_delivery_promise_lab.sql`, và `notebooks/05_delivery_promise_lab.ipynb`. Chạy lại một số tham số và đối chiếu số liệu với dashboard.

**Bước 3 — Xem phần gốc:** Mở `dashboard/index.html` để xem báo cáo tổng quan Olist. Những file gốc (bao gồm Excel và notebook 01–04) đến từ repo nguồn, không phải tự viết mới.

**Bước 4 — Tự kiểm tra (Python đã cài trên máy):**

```powershell
cd "duong-dan-den-thu-muc-project"
python -m src.promise_lab
python -m src.promise_lab_dashboard
pip install pytest
python -m pytest -q tests/test_promise_lab.py
```

**Bước 5 — Đưa lên GitHub:** Tạo repo mới với tên gợi ý `olist-commerce-intelligence-promise-lab`, tải toàn bộ nội dung trong ZIP lên, rồi đặt GitHub Pages ở `Settings → Pages → Deploy from a branch → main /docs`. Trang `docs/index.html` là dashboard mới. Link công khai sẽ chỉ hoạt động sau khi bạn tự bật Pages.

**Bước 6 — Đưa vào CV:** Đọc `docs/portfolio/interview_guide_vi.md`, tập trả lời 8 câu phản biện. Chỉ viết những gì bạn đã tự chạy, hiểu và có thể trình bày; nhớ ghi rõ repo gốc tại `NOTICE.md`.

**Lưu ý quan trọng:** Phiên bản ZIP chứa sẵn dữ liệu tổng hợp và dashboard, **không chứa raw CSV Olist**. Để chạy lại toàn bộ pipeline gốc cần tải dữ liệu qua lệnh trong README gốc và cài đầy đủ dependencies. Chưa có file Power BI `.pbix` do bạn tự xây, chỉ có hướng dẫn và DAX tham khảo. Các con số lợi ích của PromiseLab là giả định kinh doanh chứ không phải kết quả thực tế.
