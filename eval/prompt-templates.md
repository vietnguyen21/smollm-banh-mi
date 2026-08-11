# Prompt Templates - Tạo MCQ Tiếng Việt cho Eval

Dùng để nhờ AI (web interface) sinh câu hỏi trắc nghiệm tiếng Việt.
Mỗi lần chạy thay `{DOMAIN}` bằng một trong: `History`, `Culture`, `Society`, `Lifestyle`, `Geography`.
Mỗi domain cần ~50 câu (tổng ~250 câu).

---

## Template gốc

```
Bạn là một chuyên gia tạo dữ liệu trắc nghiệm tiếng Việt chất lượng cao cho việc huấn luyện mô hình ngôn ngữ.

Nhiệm vụ: Tạo chính xác 50 câu hỏi trắc nghiệm (MCQ) về chủ đề: {DOMAIN}

Yêu cầu nghiêm ngặt:
1. Mỗi câu hỏi phải có đáp án đúng rõ ràng, không mơ hồ.
2. Đúng 4 lựa chọn (options), trong đó chỉ 1 lựa chọn đúng.
3. 3 lựa chọn sai phải hợp lý, "nhiễu" tốt (giống đúng, không quá vô lý).
4. Câu hỏi bằng tiếng Việt tự nhiên, phù hợp người Việt bình thường, KHÔNG quá chuyên sâu.
5. Nội dung chính xác về mặt sự thật.

Đầu ra: Chỉ trả về một mảng JSON hợp lệ, không có văn bản khác, không giải thích.

Đúng theo cấu trúc sau:
{
  "id": <số tăng dần bắt đầu từ 1>,
  "question": "<câu hỏi>",
  "domain": "{DOMAIN}",
  "options": ["<lựa chọn 1>", "<lựa chọn 2>", "<lựa chọn 3>", "<lựa chọn 4>"],
  "true_answers": "<đáp án đúng>"
}

Day la mot vi du 
{
    "id":1,
    "questions":"Trong phong tục ăn uống truyền thống của người Việt, loại gia vị nào thường được dùng làm nước chấm chính gắn liền với bữa cơm hàng ngày?",
    "domains":"culture",
    "options":["Mù tạt","Nước mắm","Xì dầu đậm đặc","Sốt mayonnaise"],
    "true_answers":"Nước mắm"
}

Trả về như thế này (một mảng):
[
  { "id": 1, "question": "...", "domain": "...", "options": ["...","...","...","..."], "true_answers": "..." },
  { "id": 2, "question": "...", "domain": "...", "options": ["...","...","...","..."], "true_answers": "..." }
]

Hãy tạo 50 câu về chủ đề: {DOMAIN}
```

---

## Lưu ý khi dùng

- Nếu AI bỏ dở (chỉ trả vài câu), đổi số lượng xuống **10–20 câu/lần** rồi chạy nhiều lần, sau đó gộp lại.
- Khi gộp từ nhiều lần tạo, **đánh số lại `id` từ 1..50** cho mỗi domain để tránh trùng.
- `domain` phải là tên chuẩn: `History`, `Culture`, `Society`, `Lifestyle`, `Geography`.

## Schema chuẩn (khớp eval/validation_structure.md)

```
{
  "id": int,
  "question": string,
  "domain": string,       # History | Culture | Society | Lifestyle | Geography
  "options": [4 strings],
  "true_answers": string
}
```
