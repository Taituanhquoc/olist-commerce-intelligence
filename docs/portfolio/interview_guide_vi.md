# Hướng dẫn trình bày project (dành cho Data Analyst Intern/Fresher)

## Elevator pitch (~45 giây)

"Đây là portfolio case study sử dụng dữ liệu Olist 2017–2018. Em kế thừa và ghi nguồn một pipeline phân tích e-commerce mã nguồn mở, rồi phát triển thêm mô-đun Delivery Promise Lab để chuyển kết quả lịch sử thành quyết định vận hành. Mô-đun mới kiểm tra tính nhất quán của dữ liệu tổng hợp, ước lượng tỷ lệ giao trễ có điều chỉnh theo quy mô mẫu, xây mô hình phân bổ ngân sách theo rủi ro và hiển thị các kịch bản chi phí/hiệu quả bằng dashboard HTML tương tác. Một điểm em muốn nhấn mạnh là mô hình không tự cho ra kết quả khả quan: với bộ giả định mẫu, dự án chưa hòa vốn, vì vậy em đề xuất pilot có ngẫu nhiên hóa để đo hiệu quả thực tế." 

## 8 câu nhà tuyển dụng dễ hỏi

**1. Tại sao chọn vấn đề giao trễ?** Vì tác động vận hành có thể đo ở cấp đơn hàng, có phân bố theo địa lý và dễ xây dựng câu hỏi ra quyết định. Khác với tổng hợp doanh thu thuần túy, bài toán buộc phải cân bằng rủi ro, chi phí và số lượng đơn.

**2. Thế nào là một đơn trễ?** Trong pipeline gốc, đơn được giao sau thời điểm hứa giao; chỉ lấy những đơn đã giao. Cần phân biệt định nghĩa theo thời gian với tác động do thay đổi lời hứa ETA.

**3. Tại sao không chọn bang có nhiều đơn trễ nhất?** Vì nhiều đơn trễ có thể chỉ phản ánh bang có số đơn lớn. Phải xét cả late rate, volume, chi phí và khả năng thực hiện can thiệp.

**4. Vì sao Wilson interval?** Để lượng hóa mức bất định của tỷ lệ quan sát khi cỡ mẫu từng bang khác nhau. Đây không phải khoảng tin cậy cho hiệu quả can thiệp.

**5. Vì sao sử dụng smoothing?** Tỷ lệ ở vùng ít đơn có thể dao động mạnh; đẩy tỷ lệ về mức quốc gia với pseudo-count 200 giúp hạn chế cực đoan. Pseudo-count là lựa chọn thiết kế cần kiểm tra độ nhạy, không phải chân lý.

**6. Mày có chứng minh giao trễ làm giảm điểm review không?** Không. Chỉ quan sát thấy quan hệ có ý nghĩa; không thể kết luận nhân quả vì có nhiều biến gây nhiễu. Muốn đo tác động phải thiết kế thí nghiệm/ước lượng nhân quả phù hợp.

**7. R$14.228 là lợi nhuận thực tế à?** Không. Đó là giá trị mô phỏng dựa trên giá trị giả định của một đơn tránh giao trễ (R$150). Lợi ích ròng mẫu lại âm R$772; cần pilot để kiểm chứng.

**8. Mày làm phần nào và phần nào là repo gốc?** Phải trả lời trung thực: repo gốc đã có EDA, Python ETL, SQL warehouse, notebook, Excel và dashboard e-commerce. Phần mở rộng mới là PromiseLab với thuật toán xếp hạng, dữ liệu đối soát, mô phỏng ngân sách, trang tương tác, SQL, notebook, kiểm thử và decision memo. Hãy tự đọc, chạy, chỉnh sửa và giải thích được mã nguồn trước khi nhận là sản phẩm cá nhân.

## 3 gạch đầu dòng CV (chỉ dùng khi đã tự kiểm tra/chạy và hiểu)

- Extended an open-source e-commerce analytics pipeline with a state-level delivery-risk decision module, reconciling 95K+ regional shipment records against national KPIs.
- Applied Wilson confidence intervals and sample-size-aware risk smoothing to rank logistics intervention priorities across 21 Brazilian states.
- Built an interactive scenario dashboard to allocate hypothetical intervention budgets, evaluate break-even thresholds, and communicate model assumptions and limitations.

**Quy tắc:** Không tự ghi Power BI project mới nếu chưa xây bản `.pbix` riêng. Không nói chính mình làm toàn bộ ETL/SQL gốc nếu chỉ tiếp nhận repo. Trước khi phỏng vấn, tự thao tác lại code và các kịch bản, biết chỉ ra nhược điểm của mô hình.
