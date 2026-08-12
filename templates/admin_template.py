admin_html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <title>Bida Club - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <link rel="stylesheet" href="/assets/css/admin.css">
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-left">
            <button class="menu-toggle-btn" id="menu-btn" onclick="toggleSidebar()">☰</button>
            <div class="logo-icon">8</div>
            <div>
                <div class="header-title" id="nav-header-title">Bida Club</div>
                <div class="header-sub" id="nav-header-sub">Đẳng cấp từng cú cơ</div>
                <div style="font-size: 11px; color: #8b949e; margin-top: 4px;">📍 3xx Huỳnh Tấn Phát quận 7 HCM &nbsp;|&nbsp; 📞 0396123456</div>
            </div>
        </div>
        <div class="header-right">
            <div class="stats-bar">
                <div class="stat-chip">
                    <span class="dot dot-green" id="status-dot"></span>
                    <span id="status-label">Dang ket noi...</span>
                </div>
                <div class="stat-chip">
                    <span id="event-count">0</span> su kien
                </div>
                <div class="stat-chip" id="role-badge-display" style="font-weight:bold; background:#334155; color:#f8fafc;">
                    👤 Đang kiểm tra...
                </div>
                <div id="clock">--:--:--</div>
            </div>
            <button class="sound-toggle" id="sound-btn" onclick="toggleSound()">
                <span id="sound-icon">&#128264;</span> Am thanh
            </button>
            <button class="sound-toggle" onclick="logout()" style="background:#ef4444; border-color:#b91c1c; margin-left:8px;">
                <span>🔒</span> Đăng xuất
            </button>
        </div>
    </div>

    <div class="status-banner status-connecting" id="status-banner">
        <span id="banner-icon">&#9881;</span>
        <span id="banner-text">Đang kiểm tra kết nối AI Camera Server...</span>
    </div>

    <!-- APP CONTAINER -->
    <div class="app-container">
        <!-- LEFT SIDEBAR -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-section">
                <div class="sidebar-section-title">🎱 QUẢN LÝ BÀN</div>
                <a href="#" class="sidebar-link active" id="filter-all" onclick="setTableFilter('all', this)">📋 Tất cả bàn bida</a>
                <a href="#" class="sidebar-link" id="filter-empty" onclick="setTableFilter('empty', this)">🟢 Danh sách bàn trống</a>
                <a href="#" class="sidebar-link" id="filter-playing" onclick="setTableFilter('playing', this)">🔴 Bàn đang chơi</a>
            </div>
            
            <div class="sidebar-section" style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 20px;">
                <div class="sidebar-section-title">🎥 CÔNG CỤ CAMERA</div>
                <a href="#" class="sidebar-link" onclick="toggleDrawer(true)">⏳ Trích xuất Highlight</a>
            </div>
            
            <div class="sidebar-section" style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 20px;">
                <div class="sidebar-section-title">📦 KHO HÀNG & THỰC ĐƠN</div>
                <a href="#" class="sidebar-link" onclick="openInventoryModal()">📦 Quản lý Kho & Thực đơn</a>
            </div>
            
            <div class="sidebar-section" style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 20px;">
                <div class="sidebar-section-title">📊 BÁO CÁO & LỊCH SỬ</div>
                <a href="#" class="sidebar-link" onclick="openReportModal()">📊 Xuất báo cáo Doanh thu</a>
                <a href="#" class="sidebar-link" onclick="openHistoryModal()">🕰️ Lịch sử Bàn chơi</a>
            </div>
        </div>

        <!-- MAIN CONTENT WRAPPER -->
        <div class="main-content-wrapper">
            <!-- MAIN -->
            <div class="main-content">
                <div class="dashboard-grid">
                    <!-- LEFT COLUMN: TABLES & LIVE CAM FEED -->
                    <div class="dashboard-col">
                        <!-- BILLIARD TABLES SECTION (MỚI) -->
                        <div class="card">
                            <div class="card-header-title">🎱 Danh sách quản lý bàn bida</div>
                            <div class="tables-grid" id="tables-grid">
                                <!-- Danh sách bàn bida load động qua JS -->
                            </div>
                        </div>

                        <!-- LIVE CAMERA FEED GRID 2x2 -->
                        <div class="card">
                            <div class="card-header-title">🎥 Live Camera Streams - Hệ thống giám sát bàn chơi</div>
                            <div class="cameras-grid">
                                <div class="live-stream-container" id="cam-container-1" onclick="toggleCamStream(1)">
                                    <div class="live-tag" style="font-size: 10px; padding: 2px 6px;">Bàn 1</div>
                                    <div class="stream-status-badge status-empty-waiting" id="cam-status-1">BÀN TRỐNG</div>
                                    <img id="live-cam-1" class="live-stream-img" src="" onerror="this.src='https://images.unsplash.com/photo-1544197150-b99a580bb7a8?q=80&w=600&auto=format&fit=crop'" alt="Bàn 1 Cam">
                                    <div class="stream-overlay" id="cam-overlay-1">
                                        <button class="stream-action-btn">▶ Xem Stream</button>
                                    </div>
                                    <div class="hover-action-overlay" id="cam-hover-1">
                                        <button class="stream-action-btn" style="background: rgba(239,68,68,0.25); border-color: rgba(239,68,68,0.4); color: #fca5a5;">⏸ Tắt Stream</button>
                                    </div>
                                </div>
                                <div class="live-stream-container" id="cam-container-2" onclick="toggleCamStream(2)">
                                    <div class="live-tag" style="font-size: 10px; padding: 2px 6px; background: #6366f1;">Bàn 2</div>
                                    <div class="stream-status-badge status-empty-waiting" id="cam-status-2">BÀN TRỐNG</div>
                                    <img id="live-cam-2" class="live-stream-img" src="" onerror="this.src='https://images.unsplash.com/photo-1544197150-b99a580bb7a8?q=80&w=600&auto=format&fit=crop'" alt="Bàn 2 Cam">
                                    <div class="stream-overlay" id="cam-overlay-2">
                                        <button class="stream-action-btn">▶ Xem Stream</button>
                                    </div>
                                    <div class="hover-action-overlay" id="cam-hover-2">
                                        <button class="stream-action-btn" style="background: rgba(239,68,68,0.25); border-color: rgba(239,68,68,0.4); color: #fca5a5;">⏸ Tắt Stream</button>
                                    </div>
                                </div>
                                <div class="live-stream-container" id="cam-container-3" onclick="toggleCamStream(3)">
                                    <div class="live-tag" style="font-size: 10px; padding: 2px 6px; background: #8b5cf6;">Bàn 3</div>
                                    <div class="stream-status-badge status-empty-waiting" id="cam-status-3">BÀN TRỐNG</div>
                                    <img id="live-cam-3" class="live-stream-img" src="" onerror="this.src='https://images.unsplash.com/photo-1544197150-b99a580bb7a8?q=80&w=600&auto=format&fit=crop'" alt="Bàn 3 Cam">
                                    <div class="stream-overlay" id="cam-overlay-3">
                                        <button class="stream-action-btn">▶ Xem Stream</button>
                                    </div>
                                    <div class="hover-action-overlay" id="cam-hover-3">
                                        <button class="stream-action-btn" style="background: rgba(239,68,68,0.25); border-color: rgba(239,68,68,0.4); color: #fca5a5;">⏸ Tắt Stream</button>
                                    </div>
                                </div>
                                <div class="live-stream-container" id="cam-container-4" onclick="toggleCamStream(4)">
                                    <div class="live-tag" style="font-size: 10px; padding: 2px 6px; background: #ec4899;">Bàn 4</div>
                                    <div class="stream-status-badge status-empty-waiting" id="cam-status-4">BÀN TRỐNG</div>
                                    <img id="live-cam-4" class="live-stream-img" src="" onerror="this.src='https://images.unsplash.com/photo-1544197150-b99a580bb7a8?q=80&w=600&auto=format&fit=crop'" alt="Bàn 4 Cam">
                                    <div class="stream-overlay" id="cam-overlay-4">
                                        <button class="stream-action-btn">▶ Xem Stream</button>
                                    </div>
                                    <div class="hover-action-overlay" id="cam-hover-4">
                                        <button class="stream-action-btn" style="background: rgba(239,68,68,0.25); border-color: rgba(239,68,68,0.4); color: #fca5a5;">⏸ Tắt Stream</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: REALTIME ALERTS LOG -->
                    <div class="dashboard-col">
                        <!-- HQ OVERVIEW DASHBOARD PANEL (Chi hien thi cho SUPER_ADMIN) -->
                        <div id="hq-revenue-panel" style="display: none; margin-bottom: 24px; font-family: system-ui, -apple-system, sans-serif;">
                            
                            <!-- Header Banner -->
                            <div class="card" style="padding: 16px 20px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                                <div style="display: flex; align-items: center; gap: 14px;">
                                    <div style="width: 44px; height: 44px; background: #eff6ff; color: #2563eb; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px;">🏪</div>
                                    <div>
                                        <div style="font-size: 18px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px;">
                                            <span>Bida Club</span>
                                        </div>
                                        <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">
                                            Tong quan toan he thong · <span id="hq-store-count-label">3 chi nhanh</span>
                                        </div>
                                    </div>
                                </div>
                                <div style="display: flex; align-items: center; gap: 10px;">
                                    <span style="font-size: 12px; color: #15803d; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 6px 12px; border-radius: 20px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px;">
                                        <span style="width: 8px; height: 8px; background: #22c55e; border-radius: 50%; display: inline-block;"></span>
                                        <span id="hq-sync-status">Dong bo 2 phut truo'c</span>
                                    </span>
                                    <span style="font-size: 12px; color: #475569; background: rgba(255, 255, 255, 0.1); border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 20px; font-weight: 600;">
                                        🔒 Che do chi xem
                                    </span>
                                    <button onclick="loadHQOverviewData()" style="background: var(--primary); color: white; border: none; padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                        🔄 Lam moi
                                    </button>
                                </div>
                            </div>

                            <!-- 4 Metric Cards Grid -->
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 20px;">
                                
                                <!-- Card 1: Doanh thu hom nay -->
                                <div class="card" style="padding: 18px 20px;">
                                    <div style="font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px;">Doanh thu hom nay</div>
                                    <div id="hq-card-today-rev" style="font-size: 26px; font-weight: 800; color: #fff; letter-spacing: -0.5px;">0 ₫</div>
                                    <div style="margin-top: 8px; font-size: 12px;">
                                        <span id="hq-card-today-badge" style="color: #15803d; font-weight: 700; background: rgba(16, 185, 129, 0.15); padding: 2px 6px; border-radius: 4px;">+8% so vo'i hom qua</span>
                                    </div>
                                </div>

                                <!-- Card 2: Doanh thu thang nay -->
                                <div class="card" style="padding: 18px 20px;">
                                    <div style="font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px;">Doanh thu thang nay</div>
                                    <div id="hq-card-month-rev" style="font-size: 26px; font-weight: 800; color: #fff; letter-spacing: -0.5px;">0 ₫</div>
                                    <div style="margin-top: 8px; font-size: 12px;">
                                        <span id="hq-card-month-badge" style="color: #15803d; font-weight: 700; background: rgba(16, 185, 129, 0.15); padding: 2px 6px; border-radius: 4px;">+12% so vo'i thang truo'c</span>
                                    </div>
                                </div>

                                <!-- Card 3: Chi nhanh hoat dong -->
                                <div class="card" style="padding: 18px 20px;">
                                    <div style="font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px;">Chi nhanh hoat dong</div>
                                    <div id="hq-card-active-stores" style="font-size: 26px; font-weight: 800; color: #fff; letter-spacing: -0.5px;">3 / 3</div>
                                    <div style="margin-top: 8px; font-size: 12px; color: #15803d; font-weight: 600;" id="hq-card-stores-sub">Tat ca dang online</div>
                                </div>

                                <!-- Card 4: Ban dang choi -->
                                <div class="card" style="padding: 18px 20px;">
                                    <div style="font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px;">Ban dang choi</div>
                                    <div id="hq-card-tables-playing" style="font-size: 26px; font-weight: 800; color: #fff; letter-spacing: -0.5px;">0 / 0</div>
                                    <div style="margin-top: 8px; font-size: 12px; color: var(--text-muted);">Toan he thong</div>
                                </div>

                            </div>

                            <!-- Section 1: Doanh thu theo chi nhanh — hom nay -->
                            <div class="card" style="padding: 20px; margin-bottom: 20px;">
                                <div style="font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 16px;">
                                    Doanh thu theo chi nhanh — hom nay
                                </div>
                                <div id="hq-bars-container" style="display: flex; flex-direction: column; gap: 14px;">
                                    <div style="color: var(--text-muted); font-size: 13px;">Dang tai du lieu doanh thu...</div>
                                </div>
                            </div>

                            <!-- Section 2: Danh sach chi nhanh -->
                            <div class="card" style="padding: 20px; margin-bottom: 20px;">
                                <div style="font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 16px;">
                                    Danh sach chi nhanh
                                </div>
                                <div style="overflow-x: auto;">
                                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; text-align: left;">
                                        <thead>
                                            <tr style="color: var(--text-muted); border-bottom: 1px solid #e2e8f0;">
                                                <th style="padding: 10px 8px; font-weight: 600;">Chi nhanh</th>
                                                <th style="padding: 10px 8px; font-weight: 600;">Ban hoat dong</th>
                                                <th style="padding: 10px 8px; font-weight: 600;">Doanh thu hom nay</th>
                                                <th style="padding: 10px 8px; font-weight: 600;">Trang thai</th>
                                            </tr>
                                        </thead>
                                        <tbody id="hq-branch-table-body">
                                            <tr><td colspan="4" style="color: var(--text-muted); padding: 12px;">Dang tai danh sach chi nhanh...</td></tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <!-- Action Buttons Bottom -->
                            <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                                <button onclick="openInventoryModal()" style="background: var(--glass-bg); border: 1px solid var(--glass-border); color: var(--text-main); padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                                    🔍 Xem chi tiet chi nhanh
                                </button>
                                <button onclick="openReportModal()" style="background: var(--glass-bg); border: 1px solid var(--glass-border); color: var(--text-main); padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                                    📥 Xuat bao cao
                                </button>
                                <button onclick="alert('He thong dang mo rong. Lien he ky thuat de cap phat chi nhanh moi!')" style="background: var(--glass-bg); border: 1px solid var(--glass-border); color: var(--text-main); padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px;">
                                    ➕ Them chi nhanh
                                </button>
                            </div>

                        </div>
                        <div id="realtime-alerts-container">
                            <div class="section-label">Canh bao realtime</div>
                            <div id="events">
                                <div class="empty-state" id="empty-state">
                                    <div class="empty-icon">&#128247;</div>
                                    <div class="empty-text">Chua co su kien nao</div>
                                    <div class="empty-sub">He thong dang cho AI Camera gui du lieu...</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- RIGHT HIGHLIGHT DRAWER -->
    <div class="drawer-overlay" id="drawer-overlay" onclick="toggleDrawer(false)"></div>
    <div class="drawer" id="highlight-drawer">
        <div class="drawer-header">
            <h3>🎬 Highlight Clip Center</h3>
            <button class="drawer-close" onclick="toggleDrawer(false)">✕</button>
        </div>
        <div class="drawer-body">
            <div class="highlight-desc" style="font-size: 13px; color: #9ca3af; line-height: 1.5; margin-bottom: 20px;">
                Chọn bàn bida bên dưới, sau đó bấm cắt nhanh 30 giây vừa qua.
                Hoặc trích xuất video trong quá khứ qua Cỗ Máy Thời Gian (lưu tối đa 30 phút).
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px;">
                <span style="font-size: 13px; font-weight: 600; color: #a5b4fc;">Chọn bàn cần trích xuất:</span>
                <select id="highlight-table-select" style="background:#1f1b4b; border:1px solid rgba(255,255,255,0.15); border-radius:8px; color:white; padding:8px 12px; font-size:13px; font-weight:700; outline:none; cursor: pointer; width: 100%;">
                    <option value="1">Bàn 1</option>
                    <option value="2">Bàn 2</option>
                    <option value="3">Bàn 3</option>
                    <option value="4">Bàn 4</option>
                </select>
            </div>
            
            <button class="btn btn-highlight" id="clip-btn" onclick="requestSelectedClip()" style="width: 100%; justify-content: center; margin-bottom: 20px;">🎥 Highlight 30s bàn đã chọn</button>

            <!-- TIME MACHINE -->
            <div class="time-machine-container">
                <div class="time-machine-title">⏳ Co May Thoi Gian</div>
                <div class="time-machine-row" style="margin-top: 10px;">
                    <input type="time" id="time-input" class="time-input">
                    <button class="btn btn-download" style="padding: 10px 18px;" id="past-clip-btn" onclick="requestSelectedPastClip()">⌛ Trích xuất</button>
                </div>
            </div>

            <div class="highlight-status" id="clip-status" style="margin-top: 20px; display: none;"></div>
            <div class="clips-list" id="clips-list" style="margin-top: 20px;"></div>
        </div>
    </div>

    <!-- REPORT MODAL -->
    <div class="bill-modal-overlay" id="report-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 90%; max-width: 500px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 24px;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>📊 XUẤT BÁO CÁO DOANH THU</span>
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold; padding: 4px;" onclick="closeReportModal()">✕</span>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 12px; color: white;">
                <div id="report-store-container" style="display: block;">
                    <label style="font-size: 13px; font-weight: 600; color: #a5b4fc; display: block; margin-bottom: 4px;">Chi nhánh <span style="color: #ef4444;">*</span>:</label>
                    <select id="report-store-select" style="width: 100%; height: 40px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 12px; font-size: 14px; outline: none;">
                        <option value="">-- Bắt buộc chọn chi nhánh --</option>
                    </select>
                </div>
                <div>
                    <label style="font-size: 13px; font-weight: 600; color: #a5b4fc; display: block; margin-bottom: 4px;">Từ ngày:</label>
                    <input type="date" id="report-start-date" style="width: 100%; height: 40px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 12px; font-size: 14px; outline: none; color-scheme: dark;">
                </div>
                <div>
                    <label style="font-size: 13px; font-weight: 600; color: #a5b4fc; display: block; margin-bottom: 4px;">Đến ngày:</label>
                    <input type="date" id="report-end-date" style="width: 100%; height: 40px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 12px; font-size: 14px; outline: none; color-scheme: dark;">
                </div>
                <div id="report-error-msg" style="color: #f87171; font-size: 13px; font-weight: 600; display: none; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); padding: 8px 12px; border-radius: 6px;"></div>
            </div>
            
            <button onclick="downloadRevenueReport()" style="margin-top: 8px; height: 44px; border-radius: 8px; border: none; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; font-weight: bold; font-size: 15px; cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">📥 Tải file Excel (.csv)</button>
        </div>
    </div>

    <!-- DETAILED BRANCH REVENUE MODAL -->
    <div class="bill-modal-overlay" id="branch-revenue-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 95%; max-width: 750px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 24px; max-height: 90vh; overflow-y: auto;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>🏢 CHI TIẾT DOANH THU CÁC CHI NHÁNH</span>
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold; padding: 4px;" onclick="closeBranchRevenueDetailModal()">✕</span>
            </div>
            
            <div id="branch-revenue-detail-content" style="color: white; display: flex; flex-direction: column; gap: 14px;">
                <div style="color: #a5b4fc; text-align: center; padding: 20px;">Đang tải thông tin doanh thu chi nhánh...</div>
            </div>
            
            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                <button onclick="closeBranchRevenueDetailModal()" style="padding: 10px 20px; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; font-weight: 600; cursor: pointer;">Đóng</button>
            </div>
        </div>
    </div>

    <!-- HISTORY MODAL -->
    <div class="bill-modal-overlay" id="history-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 95%; max-width: 800px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 24px; max-height: 90vh; overflow-y: auto;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>🕰️ LỊCH SỬ BÀN CHƠI</span>
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold; padding: 4px;" onclick="closeHistoryModal()">✕</span>
            </div>
            
            <!-- DATE RANGE FILTER BAR (Store Manager & Admin Revenue Report) -->
            <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: #c4b5fd; font-weight: 600;">
                        <span>Từ ngày:</span>
                        <input type="date" id="hist-start-date" style="background: rgba(0,0,0,0.5); border: 1px solid rgba(165,180,252,0.4); color: white; border-radius: 6px; padding: 4px 8px; font-size: 12px; outline: none;">
                    </div>
                    <div style="display: flex; align-items: center; gap: 6px; font-size: 12px; color: #c4b5fd; font-weight: 600;">
                        <span>Đến ngày:</span>
                        <input type="date" id="hist-end-date" style="background: rgba(0,0,0,0.5); border: 1px solid rgba(165,180,252,0.4); color: white; border-radius: 6px; padding: 4px 8px; font-size: 12px; outline: none;">
                    </div>
                    <button onclick="filterHistoryByDate()" style="background: linear-gradient(90deg, #6366f1, #8b5cf6); color: white; border: none; padding: 6px 16px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                        🔍 Lọc doanh thu
                    </button>
                </div>
                <!-- Quick Preset Filter Buttons -->
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap;">
                    <span style="font-size: 11px; color: #9ca3af;">Lọc nhanh:</span>
                    <button onclick="setHistPreset('today')" style="background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4); color: #a5b4fc; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600;">Hôm nay</button>
                    <button onclick="setHistPreset('week')" style="background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4); color: #a5b4fc; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600;">Tuần này</button>
                    <button onclick="setHistPreset('month')" style="background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4); color: #a5b4fc; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600;">Tháng này</button>
                    <button onclick="setHistPreset('year')" style="background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4); color: #a5b4fc; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer; font-weight: 600;">Năm nay</button>
                </div>
            </div>

            <!-- Revenue Summary Banner -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; font-size: 12px;">
                <div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="color: #9ca3af; font-size: 10px;">Tiền giờ</div>
                    <div id="hist-sum-play" style="font-weight: 700; color: #a5b4fc; font-size: 14px; margin-top: 2px;">0 ₫</div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="color: #9ca3af; font-size: 10px;">Tiền dịch vụ</div>
                    <div id="hist-sum-service" style="font-weight: 700; color: #a5b4fc; font-size: 14px; margin-top: 2px;">0 ₫</div>
                </div>
                <div style="background: rgba(34,197,94,0.1); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(34,197,94,0.3);">
                    <div style="color: #4ade80; font-size: 10px; font-weight: 600;">TỔNG DOANH THU</div>
                    <div id="hist-sum-total" style="font-weight: 800; color: #4ade80; font-size: 15px; margin-top: 2px;">0 ₫</div>
                </div>
                <div style="background: rgba(255,255,255,0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
                    <div style="color: #9ca3af; font-size: 10px;">Số lượt chơi</div>
                    <div id="hist-sum-count" style="font-weight: 700; color: #fbbf24; font-size: 14px; margin-top: 2px;">0 lượt</div>
                </div>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af;">
                <span>* Chỉ có thể xóa các phiên chơi có thời gian kết thúc quá 48 giờ.</span>
                <button onclick="deleteSelectedHistory()" id="btn-delete-history" class="admin-only" style="padding: 6px 14px; border-radius: 6px; border: none; background: #ef4444; color: white; font-weight: bold; cursor: pointer; transition: background 0.2s; opacity: 0.5;" disabled>🗑️ Xóa đã chọn</button>
            </div>

            <div style="max-height: 400px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #a5b4fc; font-weight: 700;">
                            <th style="padding: 10px 8px; width: 40px; text-align: center;">
                                <input type="checkbox" id="chk-all-history" onclick="toggleAllHistory(this)" style="cursor: pointer;">
                            </th>
                            <th style="padding: 10px 8px;">BÀN</th>
                            <th style="padding: 10px 8px;">GIỜ VÀO</th>
                            <th style="padding: 10px 8px;">GIỜ RA</th>
                            <th style="padding: 10px 8px; text-align: right;">THỜI GIAN</th>
                            <th style="padding: 10px 8px; text-align: right;">TỔNG TIỀN</th>
                            <th style="padding: 10px 8px; text-align: center; width: 80px;">CHI TIẾT</th>
                        </tr>
                    </thead>
                    <tbody id="history-items-body">
                        <!-- History data loaded via JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- INVENTORY MANAGEMENT MODAL -->
    <div class="bill-modal-overlay" id="inventory-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 95%; max-width: 720px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 24px; max-height: 90vh; overflow-y: auto;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>📦 QUẢN LÝ KHO HÀNG & THỰC ĐƠN</span>
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold; padding: 4px;" onclick="closeInventoryModal()">✕</span>
            </div>

            <!-- Tabs Header -->
            <div style="display: flex; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
                <button id="tab-btn-products" onclick="switchInventoryTab('products')" style="padding: 8px 16px; border-radius: 8px; border: none; background: #6366f1; color: white; font-weight: bold; cursor: pointer;">🍔 Quản lý Thực đơn</button>
                <button id="tab-btn-tables" onclick="switchInventoryTab('tables')" style="padding: 8px 16px; border-radius: 8px; border: none; background: transparent; color: #9ca3af; font-weight: bold; cursor: pointer;">🎱 Quản lý Bàn Bida</button>
                <button id="tab-btn-revenue" onclick="switchInventoryTab('revenue')" style="padding: 8px 16px; border-radius: 8px; border: none; background: transparent; color: #9ca3af; font-weight: bold; cursor: pointer;">💰 Doanh Thu Chi Nhánh</button>
            </div>

            <div id="inventory-store-container" style="display: none; margin-bottom: 16px; background: rgba(30,41,59,0.8); padding: 12px; border-radius: 8px; border: 1px solid #f59e0b;">
                <label style="font-size: 13px; font-weight: bold; color: #fbbf24; margin-right: 8px;">🏢 Chọn Chi Nhánh (HQ View):</label>
                <select id="inventory-store-select" onchange="onInventoryStoreChange()" style="height: 36px; background: rgba(0,0,0,0.5); border: 1px solid #f59e0b; color: white; border-radius: 6px; padding: 0 12px; font-size: 13px; font-weight: bold; outline: none;"></select>
            </div>

            <!-- TAB: PRODUCTS -->
            <div id="tab-content-products">
                <!-- Form thêm sản phẩm mới -->
                <div id="form-add-product-container" style="background: rgba(255,255,255,0.04); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 10px;">
                    <div style="font-weight: 700; color: #a5b4fc; font-size: 14px;">➕ Thêm sản phẩm mới</div>
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px;">
                        <input type="text" id="new-prod-name" placeholder="Tên sản phẩm (Sting dâu...)" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                        
                        <input list="cat-list" type="text" id="new-prod-category" placeholder="Danh mục..." style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                        <datalist id="cat-list">
                            <option value="Thức uống">
                            <option value="Đồ ăn">
                            <option value="Thuốc lá">
                            <option value="Dịch vụ khác">
                        </datalist>

                        <input type="number" id="new-prod-price" placeholder="Đơn giá (VNĐ)" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                        <input type="number" id="new-prod-stock" placeholder="Tồn ban đầu" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                    </div>
                    <input type="text" id="new-prod-image" placeholder="Link hình ảnh (Ví dụ: https://... hoặc để trống)" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none; margin-bottom: 4px;">
                    <button onclick="addNewProduct()" class="admin-only" style="height: 36px; border-radius: 6px; border: none; background: linear-gradient(135deg, #10b981, #059669); color: white; font-weight: bold; cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Thêm sản phẩm</button>
                </div>

                <!-- Danh sách sản phẩm hiện tại -->
                <div style="font-size: 13px; color: #d1d5db; margin-top: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="font-weight: 700; color: #fbbf24; font-size: 14px;">Danh sách thực phẩm trong kho:</div>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="saveAllProducts()" class="admin-only" style="background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">💾 Lưu tất cả</button>
                            <button onclick="deleteSelectedProducts()" class="admin-only" style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; border: none; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: bold; cursor: pointer; display: flex; align-items: center; gap: 4px; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">🗑️ Xóa đã chọn</button>
                        </div>
                    </div>

                    <div style="max-height: 280px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #a5b4fc; font-weight: 700;">
                                    <th style="padding: 10px 8px; text-align: center; width: 34px;"><input type="checkbox" id="chk-all-prods" onchange="toggleSelectAllProds(this)" title="Chọn tất cả"></th>
                                    <th style="padding: 10px 8px;">TÊN SẢN PHẨM</th>
                                    <th style="padding: 10px 8px;">DANH MỤC</th>
                                    <th style="padding: 10px 8px;">HÌNH ẢNH</th>
                                    <th style="padding: 10px 8px; text-align: right;">ĐƠN GIÁ (VNĐ)</th>
                                    <th style="padding: 10px 8px; text-align: center;">TỒN KHO</th>
                                    <th style="padding: 10px 8px; text-align: center;">HÀNH ĐỘNG</th>
                                </tr>
                            </thead>
                            <tbody id="inventory-items-body">
                                <!-- Items listed here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB: TABLES -->
            <div id="tab-content-tables" style="display: none;">
                <!-- Form thêm bàn mới -->
                <div id="form-add-table-container" style="background: rgba(255,255,255,0.04); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 10px;">
                    <div style="font-weight: 700; color: #a5b4fc; font-size: 14px;">➕ Thêm Bàn Bida Mới</div>
                    <div style="display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px;">
                        <input type="text" id="new-table-name" placeholder="Tên bàn (VD: Bàn 5 Bida Lỗ)" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                        
                        <select id="new-table-type" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                            <option value="LIP">Bida Líp</option>
                            <option value="3C">Bida 3 Băng</option>
                            <option value="POOL">Bida Lỗ</option>
                        </select>

                        <select id="new-table-tier" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                            <option value="STANDARD">Bàn Thường</option>
                            <option value="VIP">Bàn VIP</option>
                        </select>

                        <input type="number" id="new-table-price" placeholder="Giá/giờ (VNĐ)" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none;">
                    </div>
                    <input type="text" id="new-table-cam" placeholder="Camera ID (0, 1, 2...) hoặc RTSP URL" style="height: 38px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 10px; font-size: 13px; outline: none; margin-bottom: 4px;">
                    <button onclick="addNewAdminTable()" class="admin-only" style="height: 36px; border-radius: 6px; border: none; background: linear-gradient(135deg, #10b981, #059669); color: white; font-weight: bold; cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Thêm Bàn</button>
                </div>

                <!-- Danh sách bàn hiện tại -->
                <div style="font-size: 13px; color: #d1d5db; margin-top: 16px;">
                    <div style="font-weight: 700; color: #fbbf24; margin-bottom: 8px;">Danh sách Bàn Bida trong quán:</div>
                    <div style="max-height: 280px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #a5b4fc; font-weight: 700;">
                                    <th style="padding: 10px 8px;">TÊN BÀN</th>
                                    <th style="padding: 10px 8px;">LOẠI BÀN</th>
                                    <th style="padding: 10px 8px;">TIÊU CHUẨN</th>
                                    <th style="padding: 10px 8px;">CAMERA</th>
                                    <th style="padding: 10px 8px; text-align: right;">GIÁ/GIỜ (VNĐ)</th>
                                    <th style="padding: 10px 8px; text-align: center;">HÀNH ĐỘNG</th>
                                </tr>
                            </thead>
                            <tbody id="inventory-tables-body">
                                <!-- Tables listed here -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- TAB: REVENUE -->
            <div id="tab-content-revenue" style="display: none;">
                <!-- Filter Bar -->
                <div style="background: rgba(255,255,255,0.04); padding: 12px 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 14px; display: flex; flex-direction: column; gap: 10px;">
                    <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                        <span style="font-size: 13px; font-weight: 700; color: #a5b4fc;">Lọc theo mốc:</span>
                        <button id="rev-preset-today" onclick="setAdminRevPreset('today')" style="padding: 5px 12px; border-radius: 6px; border: none; background: #6366f1; color: white; font-weight: bold; font-size: 12px; cursor: pointer;">Hôm nay</button>
                        <button id="rev-preset-week" onclick="setAdminRevPreset('week')" style="padding: 5px 12px; border-radius: 6px; border: none; background: rgba(255,255,255,0.1); color: #cbd5e1; font-weight: bold; font-size: 12px; cursor: pointer;">Tuần này</button>
                        <button id="rev-preset-month" onclick="setAdminRevPreset('month')" style="padding: 5px 12px; border-radius: 6px; border: none; background: rgba(255,255,255,0.1); color: #cbd5e1; font-weight: bold; font-size: 12px; cursor: pointer;">Tháng này</button>
                        <button id="rev-preset-year" onclick="setAdminRevPreset('year')" style="padding: 5px 12px; border-radius: 6px; border: none; background: rgba(255,255,255,0.1); color: #cbd5e1; font-weight: bold; font-size: 12px; cursor: pointer;">Năm nay</button>
                    </div>
                    <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 10px;">
                        <span style="font-size: 12px; color: #cbd5e1; font-weight: 600;">Từ ngày:</span>
                        <input type="date" id="admin-rev-start-date" style="height: 32px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; color: white; padding: 0 8px; font-size: 12px; color-scheme: dark;">
                        <span style="font-size: 12px; color: #cbd5e1; font-weight: 600;">Đến ngày:</span>
                        <input type="date" id="admin-rev-end-date" style="height: 32px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; color: white; padding: 0 8px; font-size: 12px; color-scheme: dark;">
                        <button onclick="filterAdminRevCustom()" style="padding: 6px 14px; border-radius: 6px; border: none; background: linear-gradient(135deg, #10b981, #059669); color: white; font-weight: bold; font-size: 12px; cursor: pointer;">🔍 Lọc ngày</button>
                    </div>
                </div>

                <div id="admin-revenue-summary"></div>
                <div style="font-size: 13px; color: #d1d5db; margin-top: 10px;">
                    <div style="font-weight: 700; color: #fbbf24; margin-bottom: 8px;" id="admin-revenue-list-title">Chi tiết hóa đơn lượt chơi:</div>
                    <div style="max-height: 240px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                            <thead>
                                <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #a5b4fc; font-weight: 700;">
                                    <th style="padding: 10px 8px;">MÃ HĐ</th>
                                    <th style="padding: 10px 8px;">TÊN BÀN</th>
                                    <th style="padding: 10px 8px;">NGÀY GIỜ</th>
                                    <th style="padding: 10px 8px;">THỜI GIAN</th>
                                    <th style="padding: 10px 8px;">TIỀN GIỜ</th>
                                    <th style="padding: 10px 8px;">DỊCH VỤ</th>
                                    <th style="padding: 10px 8px;">TỔNG CỘNG</th>
                                </tr>
                            </thead>
                            <tbody id="admin-revenue-body">
                                <tr><td colspan="7" style="text-align:center; padding:16px; color:#a5b4fc;">Đang tải dữ liệu doanh thu...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                <button onclick="closeInventoryModal()" style="padding: 10px 24px; border-radius: 8px; border: none; background: #4b5563; color: white; font-weight: bold; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#374151'" onmouseout="this.style.background='#4b5563'">Đóng</button>
            </div>
        </div>
    </div>

    <!-- BILL INVOICE MODAL -->
    <div class="bill-modal-overlay" id="bill-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 90%; max-width: 480px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 28px;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>🧾 HÓA ĐƠN THANH TOÁN</span>
                    <span id="bill-table-name" style="font-size: 13px; background: rgba(99,102,241,0.3); color: #a5b4fc; padding: 3px 10px; border-radius: 6px; font-weight:700;">Bàn 1</span>
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold; padding: 4px; transition: color 0.2s;" onclick="closeBillModal()" onmouseover="this.style.color='white'" onmouseout="this.style.color='#9ca3af'">✕</span>
            </div>
            
            <div style="font-size: 13px; color: #d1d5db; display: flex; flex-direction: column; gap: 6px;">
                <div style="display: flex; justify-content: space-between;"><span>Giờ vào:</span> <b id="bill-start-time">--:--</b></div>
                <div id="bill-end-time-row" style="display: flex; justify-content: space-between;"><span>Giờ ra:</span> <b id="bill-end-time">--:--</b></div>
                <div style="display: flex; justify-content: space-between;"><span>Tổng thời gian chơi:</span> <b id="bill-duration">0 phút</b></div>
                <div style="display: flex; justify-content: space-between; color: #86efac; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                    <span>Tiền giờ chơi:</span> <b id="bill-play-fee" style="font-variant-numeric: tabular-nums;">0 VNĐ</b>
                </div>
            </div>
            
            <div style="font-size: 13px; color: #d1d5db;">
                <div style="font-weight: 700; color: #a5b4fc; margin-bottom: 8px;">Chi tiết món gọi (nước ngọt, khô mực...):</div>
                <div style="max-height: 140px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.04);">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #fbbf24; font-weight: 700;">
                                <th style="padding: 4px 0; font-size: 11px;">TÊN MÓN</th>
                                <th style="padding: 4px 8px; text-align: center; font-size: 11px;">SL</th>
                                <th style="padding: 4px 8px; text-align: right; font-size: 11px;">ĐƠN GIÁ</th>
                                <th style="padding: 4px 0; text-align: right; font-size: 11px;">TỔNG TIỀN</th>
                            </tr>
                        </thead>
                        <tbody id="bill-items-body">
                            <!-- Items listed here -->
                        </tbody>
                    </table>
                </div>
                <div style="display: flex; justify-content: space-between; color: #86efac; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px; margin-top: 8px;">
                    <span>Tổng tiền dịch vụ:</span> <b id="bill-service-fee" style="font-variant-numeric: tabular-nums;">0 VNĐ</b>
                </div>
            </div>
            
            <div style="font-size: 20px; font-weight: 800; display: flex; justify-content: space-between; border-top: 2px dashed rgba(255,255,255,0.15); padding-top: 14px; color: #22c55e;">
                <span>TỔNG THANH TOÁN:</span>
                <span id="bill-total-amount" style="font-variant-numeric: tabular-nums;">0 VNĐ</span>
            </div>
            
            <div style="display: flex; gap: 10px; width: 100%;">
                <button class="btn btn-confirm" style="flex: 1; justify-content: center; font-size: 14px; padding: 12px; background: linear-gradient(135deg, #3b82f6, #2563eb);" onclick="printBill()">🖨️ In Bill Tạm Tính</button>
                <button id="bill-confirm-btn" class="btn btn-confirm write-action" style="flex: 1; justify-content: center; font-size: 14px; padding: 12px;" onclick="closeBillModal()">✔️ Xác nhận & Thu tiền</button>
            </div>
        </div>
    </div>

    <!-- POS MODAL -->
    <div id="pos-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); z-index: 2000; align-items: center; justify-content: center; backdrop-filter: blur(4px);">
        <div style="background: #1e1b4b; width: 95%; max-width: 1200px; height: 90vh; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
            <!-- Header -->
            <div style="padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.02);">
                <div style="font-size: 20px; font-weight: bold; color: #34d399;" id="pos-title">🛒 Thu Ngân Gọi Món - Bàn X</div>
                <button onclick="closePosModal()" style="background: transparent; border: none; color: #9ca3af; font-size: 28px; cursor: pointer;">&times;</button>
            </div>
            
            <!-- Body -->
            <div style="display: flex; flex: 1; overflow: hidden;">
                <!-- Left: Menu (70%) -->
                <div style="flex: 7; display: flex; flex-direction: column; border-right: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2);">
                    <div id="pos-categories" style="display: flex; gap: 8px; padding: 16px; overflow-x: auto; border-bottom: 1px solid rgba(255,255,255,0.05); scrollbar-width: none;">
                        <!-- Categories injected here -->
                    </div>
                    <div id="pos-products" style="flex: 1; padding: 16px; overflow-y: auto; display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; align-content: start;">
                        <!-- Products injected here -->
                    </div>
                </div>
                
                <!-- Right: Cart (30%) -->
                <div style="flex: 3; display: flex; flex-direction: column; background: rgba(255,255,255,0.02);">
                    <div style="padding: 16px; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 16px; text-align: center; color: white;">GIỎ HÀNG</div>
                    <div id="pos-cart-items" style="flex: 1; padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;">
                        <!-- Cart items injected here -->
                    </div>
                    <div style="padding: 16px; border-top: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.3);">
                        <div style="display: flex; justify-content: space-between; font-size: 18px; font-weight: bold; margin-bottom: 16px; color: white;">
                            <span>Tổng cộng:</span>
                            <span id="pos-total-price" style="color: #34d399;">0đ</span>
                        </div>
                        <button id="pos-submit-btn" class="write-action" onclick="submitPosOrder()" style="width: 100%; padding: 14px; background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer;">Xác nhận thêm vào Bàn</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- QR CODE MODAL -->
    <div class="bill-modal-overlay" id="qr-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 90%; max-width: 380px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 28px; text-align: center; align-items: center;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; width: 100%; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px;" id="qr-modal-title">
                📷 MÃ QR GỌI MÓN - BÀN X
            </div>
            <div style="background: var(--glass-bg); padding: 12px; border-radius: 12px; display: inline-block; margin: 10px 0;">
                <img id="qr-modal-image" src="" alt="QR Code" style="width: 200px; height: 200px; display: block;">
            </div>
            <p style="font-size: 13px; color: #9ca3af; line-height: 1.5; margin: 0;">
                Khách hàng quét mã này bằng điện thoại để hiển thị thực đơn gọi đồ uống, dịch vụ.
            </p>
            <div style="font-size: 11px; color: #818cf8; word-break: break-all;" id="qr-modal-link">
                Link: http://...
            </div>
            <button class="btn btn-confirm" style="width: 100%; justify-content: center; font-size: 14px; padding: 12px; margin-top: 10px;" onclick="closeQRModal()">Đóng</button>
        </div>
    </div>

    <!-- REJECT TRANSFER CUSTOM MODAL (IMAGE 2 DESIGN) -->
    <div class="custom-confirm-overlay" id="reject-transfer-modal">
        <div class="custom-confirm-card">
            <div class="custom-modal-icon">!</div>
            <div class="custom-modal-title">Từ chối yêu cầu đổi bàn?</div>
            <div class="custom-modal-sub" id="reject-modal-sub">Vui lòng chọn lý do từ chối yêu cầu đổi bàn của khách</div>
            
            <div class="custom-modal-options">
                <label class="custom-modal-radio">
                    <input type="radio" name="reject_reason" value="1" checked onchange="toggleRejectOtherInput()">
                    <span>1 - Tạm thời hết bàn trống</span>
                </label>
                <label class="custom-modal-radio">
                    <input type="radio" name="reject_reason" value="2" onchange="toggleRejectOtherInput()">
                    <span>2 - Bàn đang bảo trì / hỏng</span>
                </label>
                <label class="custom-modal-radio">
                    <input type="radio" name="reject_reason" value="3" onchange="toggleRejectOtherInput()">
                    <span>3 - Lý do khác...</span>
                </label>
                <input type="text" id="reject-other-input" class="custom-modal-input" placeholder="Nhập lý do cụ thể..." style="display: none;">
            </div>

            <div class="custom-modal-btns">
                <button class="btn-custom-confirm" onclick="confirmRejectTransfer()">Đồng ý</button>
                <button class="btn-custom-cancel" onclick="closeRejectTransferModal()">Hủy</button>
            </div>
        </div>
    </div>

    <!-- APPROVE TRANSFER CUSTOM MODAL -->
    <div class="custom-confirm-overlay" id="approve-transfer-modal">
        <div class="custom-confirm-card">
            <div class="custom-modal-icon info">🔄</div>
            <div class="custom-modal-title">Chuyển sang bàn nào?</div>
            <div class="custom-modal-sub" id="approve-modal-sub">Chọn bàn đích để chuyển phiên chơi cho khách</div>
            
            <div style="margin-bottom: 20px; text-align: left;">
                <label style="font-size: 13px; color: var(--text-muted); font-weight: 700; display: block; margin-bottom: 6px;">Danh sách bàn trống khả dụng:</label>
                <select id="transfer-target-select" class="custom-modal-select"></select>
            </div>

            <div class="custom-modal-btns">
                <button class="btn-custom-confirm" onclick="confirmTransferTable()">Đồng ý</button>
                <button class="btn-custom-cancel" onclick="closeTransferModal()">Hủy</button>
            </div>
        </div>
    </div>

    
    <div id="jwt-login-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.85); backdrop-filter:blur(8px); z-index:99999; justify-content:center; align-items:center; font-family:sans-serif;">
        <div style="background:#1e293b; border:1px solid #334155; padding:32px; border-radius:16px; width:380px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.5); text-align:center;">
            <h2 style="color:#f8fafc; margin-top:0; margin-bottom:8px; font-size:22px;">🔒 Đăng Nhập Quản Lý</h2>
            <p style="color:#94a3b8; font-size:13px; margin-bottom:24px;">Hệ thống bảo mật Bida AI theo chi nhánh</p>
            <input id="login-username" onkeydown="if(event.key==='Enter') performLogin()" type="text" placeholder="Tài khoản (ví dụ: admin hoặc manager1)" style="width:100%; padding:12px 16px; background:#0f172a; border:1px solid #334155; border-radius:8px; color:#f8fafc; margin-bottom:12px; box-sizing:border-box; font-size:14px;">
            <input id="login-password" onkeydown="if(event.key==='Enter') performLogin()" type="password" placeholder="Mật khẩu (ví dụ: secret hoặc admin)" style="width:100%; padding:12px 16px; background:#0f172a; border:1px solid #334155; border-radius:8px; color:#f8fafc; margin-bottom:16px; box-sizing:border-box; font-size:14px;">
            <div id="login-error" style="color:#ef4444; font-size:13px; margin-bottom:16px; min-height:18px;"></div>
            <button onclick="performLogin()" style="width:100%; padding:12px; background:linear-gradient(135deg,#3b82f6,#2563eb); color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer; font-size:15px; box-shadow:0 4px 12px rgba(37,99,235,0.3);">Đăng Nhập Ngay</button>
            <div style="margin-top:20px; font-size:12px; color:#64748b; text-align:left; background:#0f172a; padding:10px; border-radius:6px;">
                <b>Tài khoản mẫu:</b><br>
                • Quán 1: <code>manager1</code> / <code>secret</code><br>
                • Trụ sở HQ: <code>admin</code> / <code>secret</code>
            </div>
        </div>
    </div>
    
    
<script src="/assets/js/admin.js"></script>
</body>
</html>"""
