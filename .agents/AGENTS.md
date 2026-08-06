# Quy trình Phát triển Phần mềm & Quản lý Git Version

Áp dụng quy trình Custom Trunk-based Development. Bất cứ khi nào Agent được yêu cầu tạo nhánh, commit hoặc push code, Agent PHẢI tuân thủ nghiêm ngặt các quy tắc sau:

## 1. Mô hình Nhánh (Branching Model)
- **master (production)** → **stage (UAT/regression)** → **dev (tích hợp)** → nhánh tạm (`feature/bugfix/hotfix/refactor/chore/spike`).
- **Tuyệt đối KHÔNG** push trực tiếp vào `master`, `stage`, hoặc `dev`.
- Mọi thay đổi đều phải đi qua Merge Request (MR).

## 2. Quy tắc Đặt tên Nhánh (Branch Naming)
- **Format**: `<type>/<jira-key>-<brief-3-words>`
- **Types hợp lệ**: `feature`, `bugfix`, `hotfix`, `refactor`, `chore`, `spike`.
- **Ví dụ**: `feature/B2B-123-notification-device-token`

## 3. Quy định Commit (Conventional Commits)
- Đảm bảo thói quen commit hằng ngày (tối thiểu 1 commit/ngày khi đang code dở).
- **Format bắt buộc**: `[<jira-key>] <type>(<scope>): <summary>`
- **CẤM** sử dụng các câu lệnh commit mơ hồ như: `"fix bug"`, `"wip"`, `"update"`, `"done"`.

## 4. Vòng đời của 1 Tính năng (Feature) mới
1. Nhận task trên Jira.
2. Checkout nhánh mới (thường tách ra từ `master`).
3. Code & commit liên tục hằng ngày.
4. Tạo MR gộp vào nhánh `dev`.
5. Chờ Review code và QA thực hiện smoke test trên môi trường `dev`.

## 5. Quy định Promote, Release & Hotfix
- **Quy trình Promote**: `dev` → `stage` (cần Tech Lead tạo MR, QA pass) → `master` (QA + PO/BA + Tech Lead xác nhận, có release note & rollback plan).
- **Hotfix Production (Khẩn cấp)**: Checkout nhánh trực tiếp từ `master`. Sau khi merge vào `master` thành công, **bắt buộc** phải back-merge ngược trở lại `stage` và `dev`.
- **Versioning**: Tuân thủ chuẩn Semantic Versioning (`MAJOR.MINOR.PATCH`). Tag phiên bản chỉ được tạo trên nhánh `master`.

## 6. Bảo mật & Database Migrations (The Red Rules)
- **Tuyệt đối KHÔNG** commit các thông tin bảo mật, secret keys hoặc file `.env` lên Git.
- Ghi rõ ràng quá trình migration hoặc rollback plan trong Merge Request nếu có thay đổi về cấu trúc Database.
