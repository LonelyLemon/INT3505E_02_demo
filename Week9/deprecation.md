# Deprecation Notice — API Version v1

## 🧾 Tổng quan
Phiên bản **v1** của API đã được **deprecated**.  
Vui lòng chuyển sang **API version v2** (file `app_v2.py`).

- **Ngày công bố Deprecation:** 14/11/2025  
- **Ngày gỡ hoàn toàn (Sunset Date):** 14/02/2026  

---

## ⚙️ Lý do và điểm cải tiến
API v2 ra đời nhằm:
- Hỗ trợ endpoint mới `/v2/users/me` để lấy thông tin người dùng hiện tại.
- Thêm **pagination** cho `/v2/books` qua query params `page` và `per_page`.
- Thêm **idempotency key** cho `/v2/payments` để tránh xử lý giao dịch trùng lặp.
- Bổ sung **refresh token revocation** nhằm tăng tính bảo mật.
- Chuẩn hóa header cảnh báo `Deprecation` và `Sunset`.

---

## 🔁 So sánh endpoint v1 → v2

| v1 Endpoint | v2 Endpoint | Thay đổi chính |
|--------------|--------------|----------------|
| `/v1/users/signup` | `/v2/users/signup` | Thêm kiểm tra mật khẩu tối thiểu 6 ký tự |
| `/v1/users/login` | `/v2/users/login` | Thêm refresh token blocklist |
| `/v1/users/refresh` | `/v2/users/refresh` | Refresh token phải hợp lệ và chưa bị revoke |
| `/v1/books` | `/v2/books` | Thêm phân trang (`page`, `per_page`) |
| `/v1/payments` | `/v2/payments` | Hỗ trợ header `Idempotency-Key` để tránh double charge |
| *(mới)* | `/v2/users/me` | Endpoint mới lấy thông tin user hiện tại |

---

## 🧩 Header cảnh báo Deprecation

Mọi response từ **v1** nên chứa các header sau:

```
Deprecation: true
Sunset: 2026-02-14
```

Khi client gọi vào `/v1/*`, server có thể trả thêm JSON cảnh báo:

```json
{
  "msg": "v1 is deprecated. Please migrate to /v2 endpoints. Sunset date: 2026-02-14."
}
```

---

## 🚀 Hướng dẫn Migration

1. Cập nhật base path API từ `/v1/...` sang `/v2/...`.
2. Đảm bảo mật khẩu hợp lệ (≥ 6 ký tự khi signup).
3. Nếu sử dụng `/payments`, thêm header `Idempotency-Key` (UUID) cho mỗi request thanh toán.
4. Sử dụng `/v2/users/me` để truy xuất thông tin user hiện tại.
5. Kiểm tra lại xử lý refresh token (do v2 có token revocation).

---

## 🧠 Ghi chú dành cho developers
- **Không nên triển khai hệ thống mới dựa trên v1.**
- **v1 sẽ dừng hoạt động hoàn toàn sau ngày 14/02/2026.**
- Vui lòng báo cáo bug hoặc vấn đề tương thích qua kênh nội bộ.

---

© 2025 API Team — Flask JWT Payment Demo
