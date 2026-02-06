# Hệ thống Web Quản lý & Phân phối Bất động sản (Django + PostGIS)
# <img width="2542" height="1187" alt="image" src="https://github.com/user-attachments/assets/a45dd238-533a-4c54-ad22-182ec54edf2b" />

## Giới thiệu & mục tiêu
- Ứng dụng quản lý danh mục BĐS, agent môi giới, lead và tiện ích xung quanh; hỗ trợ tìm kiếm theo khoảng cách và tự động phân phối lead cho agent gần nhất.
- Sử dụng GIS (PostGIS + GeoDjango) để:
  - Lưu trữ toạ độ chuẩn WGS84 (SRID 4326, PointField geography=True).
  - Tính khoảng cách địa lý (Distance + D(km=...)) cho Nearby Search, Amenity Search và phân phối lead.

## Kiến trúc MVT trong Django
- **Models (ORM):** `accounts.Agent`, `properties.Property`, `properties.Amenity`, `leads.Lead`, `leads.Appointment`.
- **Views (Controller):**
  - `core.views.home`
  - `properties.views.property_list/detail/nearby_search/amenity_search`
  - `leads.views.lead_form`
- **Templates (View):** trong thư mục `templates/` kế thừa `base.html`.
- **URL router:** `realestate/urls.py` include tới `core`, `properties`, `leads` (namespaces).

## Yêu cầu môi trường
- Python 3.11+ khuyến nghị.
- PostgreSQL 14+/PostGIS 3+ (có extension `postgis`).
- GDAL/GEOS đã cài trong hệ thống để GeoDjango hoạt động.

## Cài đặt & cấu hình
1. Clone project và tạo virtualenv.
2. Cài dependency:
   ```bash
   pip install -r requirements.txt
   ```
3. Tạo database PostGIS:
   ```sql
   CREATE DATABASE realestate;
   \c realestate;
   CREATE EXTENSION postgis;
   ```
4. Tạo file `.env` từ mẫu:
   ```bash
   cp .env.example .env
   ```
   Sửa các biến:
   - `SECRET_KEY`: chuỗi bí mật của Django.
   - `DEBUG`: true/false.
   - `DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT`
   - `ALLOWED_HOSTS`: ví dụ `localhost,127.0.0.1`.
5. Chạy migrate:
   ```bash
   python manage.py migrate
   ```
6. Tạo tài khoản admin:
   ```bash
   python manage.py createsuperuser
   ```
7. Seed dữ liệu demo:
   ```bash
   python manage.py seed_demo_data
   ```
8. Chạy server:
   ```bash
   python manage.py runserver
   ```

## Hướng dẫn sử dụng web (templates)
- **Home** `/` : tổng quan số liệu.
- **Property list** `/properties/` : lọc theo loại (apartment/house/land), giá min/max, diện tích min/max.
- **Property detail** `/properties/<id>/` : thông tin chi tiết, link quay lại.
- **Nearby Search** `/properties/nearby/search/?lat=21.0285&lng=105.8542&radius=5&type=house`  
  Nhập lat/lng & bán kính (km) để xem BĐS trong vùng, sắp xếp theo khoảng cách, hiển thị km.
- **Lead Form** `/leads/lead-form/` : nhập tên, sđt, budget, lat/lng mong muốn; hệ thống tạo Lead và tự gán agent gần nhất, hiển thị tên agent + khoảng cách.
- **Amenity Search** `/properties/amenities/search/?lat=21.0285&lng=105.8542&radius=3&amenity_type=park` : trả danh sách tiện ích gần.

## Django Admin (CRUD)
- Truy cập `/admin/` đăng nhập với superuser.
- Quản lý:
  - `Property` (có list_display: title, type, price, area, agent)
  - `Agent` (name, phone, email)
  - `Lead` (name, phone, budget, assigned_agent)
  - `Amenity` (name, amenity_type)
  - `Appointment` (lead, property, agent, scheduled_at)
  - Đã cấu hình `search_fields`, `list_filter` hợp lý; dùng `OSMGeoAdmin` cho trường Point.

## GIS Tools (service layer)
File `core/gis_tools.py`:
- `tool_nearby_properties(lat, lng, radius_km, filters)`  
  - **Input:** lat, lng (float), radius_km (float), filters {property_type, price_min, price_max, area_min, area_max}.  
  - **Output:** QuerySet Property đã annotate `distance` (km), sắp xếp tăng dần, lọc trong bán kính bằng `location__distance_lte` với `D(km=radius)`.
- `tool_assign_lead_to_nearest_agent(lead_location: Point)`  
  - **Input:** GeoDjango Point (SRID 4326).  
  - **Output:** tuple (agent gần nhất, distance_km) hoặc (None, None) nếu không có agent.
- `tool_amenities_within_radius(lat, lng, radius_km, amenity_type)`  
  - **Input:** lat, lng, radius_km, amenity_type optional.  
  - **Output:** QuerySet Amenity annotate distance, order by distance.

## Cấu trúc thư mục
```
manage.py
realestate/           # settings, urls, wsgi/asgi
accounts/             # Agent model + admin + migrations
properties/           # Property, Amenity + views/urls/admin + migrations
leads/                # Lead, Appointment + views/urls/admin + migrations
core/                 # home view, GIS tools, seed command
templates/            # base.html, core/, properties/, leads/
static/css/styles.css
requirements.txt
.env.example
```

## Troubleshooting
- **psycopg2 / libpq lỗi:** đảm bảo đã cài `libpq-dev`/`postgresql-client` và `pip install psycopg2-binary`.
- **Missing postgis extension:** chạy `CREATE EXTENSION postgis;` trong DB; kiểm tra quyền.
- **GDAL/GEOS not found:** cài gói hệ thống (`gdal-bin libgdal-dev libgeos-dev` tùy OS) rồi cài lại môi trường.
- **SRID lỗi hoặc phép đo không chính xác:** đảm bảo các PointField dùng `geography=True, srid=4326` và dữ liệu lat/lng (không phải lng/lat).

## Demo lat/lng gợi ý (Hà Nội)
- Hoàn Kiếm: lat `21.0285`, lng `105.8542`
- Cầu Giấy: lat `21.0333`, lng `105.7899`
- Dùng radius 3–5 km để thấy kết quả seed.

## Ghi chú
- Không lưu mật khẩu/secret trong repo; dùng `.env`.
- Có thể thêm screenshot vào thư mục `docs/` (đặt tên `home.png`, `property-list.png`, ...).



# <img width="2523" height="634" alt="image" src="https://github.com/user-attachments/assets/5be08eff-0145-4736-b45d-8db3c4416fbf" />
# <img width="2523" height="634" alt="image" src="https://github.com/user-attachments/assets/cd680ba1-f421-4e8b-9f23-00bfdd21e98a" />
# <img width="2523" height="825" alt="image" src="https://github.com/user-attachments/assets/4eac4faf-1713-4512-981a-a2118e73cdb3" />


