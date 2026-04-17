# GeoEstate / WebGIS Real Estate Platform

Ứng dụng web quản lý, tìm kiếm và phân tích bất động sản xây bằng **Django + GeoDjango + PostGIS**.

Project hiện đã vượt mức demo CRUD cơ bản và có các khối chức năng chính:
- quản lý bất động sản, môi giới, lead và tiện ích lân cận
- tìm kiếm theo bản đồ, bán kính và khu vực
- dashboard thống kê
- wishlist / compare
- auth + role + permission nền
- import CSV
- seed dữ liệu TP.HCM nhìn thật hơn
- gallery ảnh property + media upload

---

## 1. Tính năng hiện có

### Bất động sản
- Danh sách bất động sản với:
  - search keyword
  - filter theo loại hình
  - filter theo giá / diện tích
  - filter theo trạng thái tin
  - sort theo giá / diện tích / mới nhất
  - pagination
- Trang chi tiết bất động sản với:
  - gallery ảnh
  - thông tin môi giới
  - điểm vị trí (location score)
  - map hiển thị vị trí
  - tiện ích lân cận
  - đề xuất bất động sản tương tự

### GIS / bản đồ
- Bản đồ Leaflet trên trang list
- Marker clustering
- Heatmap cơ bản
- Search theo vùng map (`bbox`)
- Nearby Search theo:
  - vị trí hiện tại
  - địa điểm cụ thể
  - preset location
- Amenity Search theo:
  - vị trí hiện tại
  - địa điểm cụ thể
  - preset location

### CRM / vận hành
- Lead form
- Tự động gán lead cho môi giới gần nhất
- Dashboard thống kê:
  - tổng số property
  - active / sold / hidden
  - featured
  - lead / alert / agent
  - giá và diện tích trung bình theo loại
- Changelog cơ bản cho property
- Import property từ CSV trong admin

### Người dùng
- Đăng ký
- Đăng nhập
- Đăng xuất
- Hồ sơ người dùng
- Role nền:
  - user
  - agent
  - admin
- Permission cơ bản:
  - guest bị chặn các route yêu cầu login
  - dashboard giới hạn theo role
  - agent chỉ thấy dữ liệu liên quan khi có `linked_agent`

### Tương tác người dùng
- Wishlist
- Compare tối đa 3 property
- Saved alert nền cơ bản qua lead form (`alert_enabled`)

---

## 2. Kiến trúc chính

### Apps
- `core/`
  - home view
  - GIS helper tools
- `accounts/`
  - `Agent`
  - `UserProfile`
  - auth / role / permission
- `properties/`
  - `Property`
  - `Amenity`
  - `PropertyImage`
  - `PropertyChangeLog`
  - property list/detail/search/map logic
- `leads/`
  - `Lead`
  - `Appointment`
  - dashboard + lead handling
- `realestate/`
  - settings / urls / wsgi / asgi

### Stack
- Python / Django
- GeoDjango + PostGIS
- Leaflet + Leaflet MarkerCluster + Leaflet Heat
- Bootstrap Icons / custom templates

---

## 3. Cấu hình môi trường

### Yêu cầu
- Python 3.11+
- PostgreSQL + PostGIS
- GDAL / GEOS cho GeoDjango

### Cài dependency
```bash
pip install -r requirements.txt
```

### Lưu ý
`requirements.txt` hiện có thêm:
- `Pillow` cho upload ảnh property

---

## 4. Database & migrate

### Tạo database PostGIS
Ví dụ:
```sql
CREATE DATABASE realestate;
\c realestate;
CREATE EXTENSION postgis;
```

### Chạy migrate
```bash
python manage.py migrate
```

### Tạo admin
```bash
python manage.py createsuperuser
```

---

## 5. Chạy project

```bash
python manage.py runserver
```

Project mặc định sẽ chạy tại:
```text
http://127.0.0.1:8000/
```

---

## 6. Seed dữ liệu thật hơn

Project có command seed dữ liệu TP.HCM nhìn thật hơn:

```bash
python manage.py seed_realistic_data
```

Nếu muốn xóa dữ liệu cũ rồi seed lại sạch:

```bash
python manage.py seed_realistic_data --reset
```

Có thể custom số lượng:

```bash
python manage.py seed_realistic_data --reset --properties 50 --agents 8 --amenities 60 --leads 20
```

### Seed hiện tạo
- agent tên Việt + email + phone
- amenity theo khu vực TP.HCM
- property với địa chỉ / giá / diện tích / trạng thái hợp lý hơn
- lead mẫu
- ảnh minh họa sample cho property
- featured property được set tự động

---

## 7. Media / ảnh

### Đã cấu hình
- `MEDIA_URL = "/media/"`
- `MEDIA_ROOT = BASE_DIR / "media"`
- dev server phục vụ media khi `DEBUG=True`

### Property images
Model:
- `PropertyImage`
  - `image`
  - `caption`
  - `is_primary`
  - `sort_order`

### Admin
- upload ảnh trực tiếp trong admin property bằng inline

---

## 8. Các route quan trọng

### Công khai
- `/`
- `/properties/`
- `/properties/<id>/`
- `/properties/nearby/search/`
- `/properties/amenities/search/`
- `/accounts/login/`
- `/accounts/register/`

### Cần login
- `/properties/wishlist/`
- `/properties/compare/`
- `/leads/lead-form/`
- `/accounts/profile/`

### Giới hạn theo role
- `/leads/dashboard/`
  - agent / admin

### Admin
- `/admin/`

---

## 9. Auth & permission

### Auth
- Django auth chuẩn
- register/login/logout/profile

### Role model
`accounts.UserProfile`
- `user`
- `agent`
- `admin`
- có thể link sang `Agent`

### Permission hiện có
- guest bị redirect về login ở các route yêu cầu auth
- user thường không vào dashboard role-based
- agent nếu có `linked_agent` sẽ bị giới hạn dữ liệu theo agent đó

---

## 10. GIS helper chính

File: `core/gis_tools.py`

### Có các hàm chính
- `tool_nearby_properties(...)`
- `tool_amenities_within_radius(...)`
- `tool_assign_lead_to_nearest_agent(...)`
- `tool_location_score(...)`
- `tool_similar_properties(...)`

---

## 11. Thư mục quan trọng

```text
manage.py
realestate/
accounts/
properties/
leads/
core/
templates/
media/
requirements.txt
README.md
```

---

## 12. Trạng thái hiện tại

Project hiện ở mức **MVP khá đầy đủ**, phù hợp để:
- demo môn học / đồ án
- tiếp tục polish UI/UX
- mở rộng API
- thêm upload ảnh thật / cloud storage
- thêm notification thật
- thêm phân quyền sâu hơn

---

## 13. Việc nên làm tiếp

Nếu muốn nâng cấp tiếp, ưu tiên hợp lý là:
1. polish UI/UX toàn site
2. test role agent/admin thật bằng account thực
3. thêm API (DRF)
4. thêm notification thật
5. thêm permission sâu hơn cho CRUD theo owner/agent
6. tối ưu import CSV và validation

---

## 14. Ghi chú

- Nếu có thay đổi lớn về feature, nhớ cập nhật lại README này.
- Nếu chạy trên máy mới, hãy kiểm tra đủ:
  - PostGIS
  - GDAL / GEOS
  - Pillow
  - migrate
  - seed data
