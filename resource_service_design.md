# Resource Service Design

## 1. Mục đích
Resource Service là service chịu trách nhiệm quản lý các tài nguyên vận hành của chuỗi club bida, bao gồm:
- sản phẩm và tồn kho
- bàn bida
- cơ, bi và các vật dụng đi kèm bàn
- phòng / khu vực
- thiết bị và camera
- cấu hình giá, trạng thái, và tài nguyên vận hành

---

## 2. Vai trò của Resource Service
Resource Service có trách nhiệm:
- lưu trữ thông tin tài nguyên của từng club
- cung cấp dữ liệu cho các service khác như Session, Billing, Order, Customer
- quản lý trạng thái hoạt động của bàn, phòng, thiết bị
- hỗ trợ điều phối vận hành tại từng chi nhánh

---

## 3. Các bounded context chính
### 3.1 Product Management
Quản lý các mặt hàng phục vụ khách hàng:
- đồ uống
- đồ ăn
- thuốc lá
- dịch vụ khác

Các thuộc tính chính:
- id
- name
- category
- price
- stock
- status
- club_id
- image_url

### 3.2 Table Management
Quản lý bàn bida:
- bàn thường / bàn VIP
- trạng thái: EMPTY, PLAYING, MAINTENANCE
- giá thuê theo giờ
- camera_id / camera_url
- khu vực / phòng

### 3.3 Table Accessories Management
Quản lý các vật dụng đi kèm bàn bida như:
- cơ
- bi
- bàn chờ / giá đỡ
- dụng cụ phụ trợ

Các thuộc tính chính:
- id
- club_id
- name
- type
- quantity_available
- condition
- status
- assigned_table_id

### 3.4 Area / Room Management
Quản lý phòng hoặc khu vực trong club:
- khu vực chính
- khu vực VIP
- khu vực riêng

### 3.5 Equipment Management
Quản lý thiết bị và tài nguyên vật lý:
- camera
- máy in
- thiết bị âm thanh
- thiết bị hỗ trợ vận hành

### 3.6 Resource Configuration
Quản lý cấu hình của tài nguyên:
- giá theo giờ từng bàn
- giá dịch vụ
- trạng thái mặc định
- quy định hoạt động

---

## 4. Mô hình dữ liệu đề xuất

### 4.1 Product
```text
Product
- id: int
- club_id: int
- name: string
- category: string
- price: decimal
- stock: int
- image_url: string
- status: string
- created_at: datetime
```

### 4.2 Table
```text
Table
- id: int
- club_id: int
- name: string
- area_id: int|null
- table_type: string
- table_tier: string
- price_per_hour: decimal
- camera_url: string
- current_status: string
- created_at: datetime
```

### 4.3 TableAccessory
```text
TableAccessory
- id: int
- club_id: int
- name: string
- type: string
- quantity_available: int
- condition: string
- status: string
- assigned_table_id: int|null
- created_at: datetime
```

### 4.4 Area
```text
Area
- id: int
- club_id: int
- name: string
- description: string
- status: string
```

### 4.5 Equipment
```text
Equipment
- id: int
- club_id: int
- name: string
- type: string
- status: string
- location: string
```

### 4.6 ResourceConfig
```text
ResourceConfig
- id: int
- club_id: int
- key: string
- value: string
- description: string
```

---
