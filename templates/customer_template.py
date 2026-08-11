
customer_menu_html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bida Club - Bàn {table_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; -webkit-tap-highlight-color: transparent; }
        
        body {
            background: linear-gradient(135deg, #0f0c29 0%, #1e1b4b 40%, #111827 100%);
            color: #f3f4f6;
            min-height: 100vh;
            padding-bottom: 140px;
        }

        /* === HEADER === */
        header {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 16px 24px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-inner {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .logo-box {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: 800;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
        }

        .brand-title {
            font-size: 20px;
            font-weight: 800;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .table-badge-header {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: #000;
            font-weight: 800;
            font-size: 13px;
            padding: 2px 10px;
            border-radius: 20px;
        }

        .brand-sub {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 2px;
        }

        .play-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(251, 191, 36, 0.12);
            border: 1px solid rgba(251, 191, 36, 0.3);
            color: #fbbf24;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
        }

        /* === MAIN LAYOUT === */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Top Banner Grid */
        .top-banner-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }

        @media (min-width: 850px) {
            .top-banner-grid {
                grid-template-columns: 1.2fr 0.8fr;
            }
        }

        .pills-column {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .pill-banner {
            display: flex;
            align-items: center;
            border-radius: 16px;
            padding: 10px 16px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            transition: transform 0.2s;
        }

        .pill-banner:hover {
            transform: translateX(4px);
            background: rgba(255, 255, 255, 0.06);
        }

        .pill-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-right: 12px;
            flex-shrink: 0;
        }

        .pill-title {
            font-weight: 700;
            font-size: 13px;
            color: #fff;
        }

        .pill-desc {
            font-size: 11px;
            color: #9ca3af;
            margin-top: 1px;
        }

        .promo-banner-box {
            border-radius: 20px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            background: rgba(255, 255, 255, 0.02);
            min-height: 180px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .promo-banner-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        /* Order History Box */
        .history-box {
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 16px;
            padding: 14px 18px;
            margin-bottom: 24px;
            display: none;
        }

        .history-title {
            font-size: 14px;
            font-weight: 700;
            color: #a5b4fc;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .history-item {
            font-size: 13px;
            color: #e0e7ff;
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
        }

        /* Category Tabs */
        .category-tabs {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding-bottom: 8px;
            margin-bottom: 20px;
            scrollbar-width: none;
        }

        .category-tabs::-webkit-scrollbar { display: none; }

        .cat-btn {
            flex-shrink: 0;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #9ca3af;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.25s;
            white-space: nowrap;
        }

        .cat-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
        }

        .cat-btn.active {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white;
            border-color: transparent;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4);
            transform: scale(1.03);
        }

        /* Grid Layout for Products */
        .section-header {
            font-size: 15px;
            font-weight: 800;
            color: #a5b4fc;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin: 24px 0 14px 0;
            display: flex;
            align-items: center;
            gap: 8px;
            border-left: 4px solid #6366f1;
            padding-left: 10px;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
            margin-bottom: 20px;
        }

        @media (min-width: 500px) {
            .product-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (min-width: 768px) {
            .product-grid {
                grid-template-columns: repeat(4, 1fr);
            }
        }

        @media (min-width: 1024px) {
            .product-grid {
                grid-template-columns: repeat(5, 1fr);
            }
        }

        .prod-card {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 12px;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 8px;
            position: relative;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
        }

        .prod-card:hover {
            transform: translateY(-3px);
            background: rgba(255, 255, 255, 0.07);
            border-color: rgba(99, 102, 241, 0.3);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        .prod-card:active {
            transform: scale(0.97);
        }

        .prod-card.selected {
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.12);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
        }

        .prod-img-box {
            width: 100%;
            aspect-ratio: 1;
            border-radius: 12px;
            background: rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            color: rgba(255, 255, 255, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
            position: relative;
        }

        .prod-img-box img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .prod-name {
            font-weight: 700;
            font-size: 14px;
            color: #fff;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.3;
            min-height: 36px;
        }

        .prod-price {
            color: #34d399;
            font-weight: 800;
            font-size: 14px;
        }

        .prod-stock {
            font-size: 11px;
            color: #9ca3af;
            font-weight: 500;
        }

        .prod-stock.out {
            color: #f87171;
        }

        .badge-count {
            position: absolute;
            top: -6px;
            right: -6px;
            background: #10b981;
            color: #000;
            font-weight: 800;
            font-size: 13px;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 10px rgba(16, 185, 129, 0.6);
            border: 2px solid #0f0c29;
            z-index: 5;
        }

        /* Circle Stepper Controls */
        .circle-stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-top: 6px;
            padding: 2px 4px;
        }
        .btn-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 1px solid rgba(255, 255, 255, 0.35);
            background: rgba(255, 255, 255, 0.05);
            color: #ffffff;
            font-size: 18px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
        }
        .btn-circle:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.2);
            border-color: #ffffff;
            transform: scale(1.08);
        }
        .btn-circle:active:not(:disabled) {
            transform: scale(0.92);
        }
        .btn-circle:disabled {
            opacity: 0.25;
            border-color: rgba(255, 255, 255, 0.15);
            cursor: not-allowed;
        }
        .circle-qty-num {
            font-size: 16px;
            font-weight: 800;
            color: #ffffff;
            min-width: 24px;
            text-align: center;
        }
        .circle-qty-input {
            width: 36px;
            height: 30px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 8px;
            color: #ffffff;
            font-size: 15px;
            font-weight: 800;
            text-align: center;
            outline: none;
            -moz-appearance: textfield;
            transition: border-color 0.2s;
        }
        .circle-qty-input::-webkit-inner-spin-button,
        .circle-qty-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        .circle-qty-input:focus {
            border-color: #10b981;
            background: rgba(16, 185, 129, 0.15);
        }

        /* Service Cards (Dashed Grid Design) */
        .service-section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 16px;
            font-weight: 800;
            color: #a5b4fc;
            margin: 28px 0 14px 0;
            border-left: 4px solid #6366f1;
            padding-left: 10px;
        }

        .service-count-tag {
            font-size: 13px;
            color: #9ca3af;
            font-weight: 600;
        }

        .service-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }

        .service-dashed-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px dashed rgba(255, 255, 255, 0.25);
            border-radius: 14px;
            padding: 14px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            user-select: none;
            min-height: 52px;
        }

        .service-dashed-card:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(255, 255, 255, 0.4);
        }

        .service-dashed-card.active {
            background: rgba(16, 185, 129, 0.12);
            border: 1.5px solid #10b981;
            box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
        }

        .service-title-text {
            font-weight: 700;
            font-size: 14px;
            color: #ffffff;
        }

        .service-radio-circle {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            border: 1.5px solid rgba(255, 255, 255, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            flex-shrink: 0;
        }

        .service-dashed-card.active .service-radio-circle {
            border-color: #10b981;
            background: #10b981;
            color: #000;
            font-weight: 800;
            font-size: 13px;
        }

        /* Cart Form Section */
        .cart-form-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 20px;
            margin-top: 28px;
            backdrop-filter: blur(10px);
        }

        .form-title {
            font-size: 16px;
            font-weight: 800;
            color: #a5b4fc;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .cart-items-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 16px;
        }

        .cart-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.25);
            padding: 10px 14px;
            border-radius: 12px;
        }

        .cart-row-name {
            font-weight: 600;
            font-size: 14px;
            color: #fff;
        }

        .cart-ctrls {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 4px 8px;
        }

        .cart-btn-sm {
            background: none;
            border: none;
            color: #fff;
            font-size: 16px;
            font-weight: bold;
            width: 24px;
            height: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .cart-qty-num {
            font-size: 14px;
            font-weight: 700;
            color: #fff;
            min-width: 18px;
            text-align: center;
        }

        .input-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
            margin-top: 12px;
        }

        @media (min-width: 600px) {
            .input-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        .input-field {
            width: 100%;
            height: 46px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: white;
            padding: 0 14px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .input-field:focus {
            border-color: #6366f1;
        }

        /* Sticky Bottom Bar */
        .bottom-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(15, 12, 41, 0.95);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding: 14px 20px;
            z-index: 100;
            box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.5);
        }

        .bar-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }

        .total-box {
            display: flex;
            flex-direction: column;
        }

        .total-lbl {
            font-size: 11px;
            color: #9ca3af;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .total-val {
            font-size: 20px;
            font-weight: 800;
            color: #34d399;
        }

        .btn-order {
            flex: 1;
            max-width: 400px;
            height: 50px;
            border-radius: 14px;
            border: none;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            font-size: 16px;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
            transition: all 0.25s;
        }

        .btn-order:not(:disabled):hover {
            box-shadow: 0 6px 25px rgba(16, 185, 129, 0.6);
            transform: translateY(-2px);
        }

        .btn-order:not(:disabled):active {
            transform: scale(0.98);
        }

        .btn-order:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            background: #374151;
            box-shadow: none;
        }

        /* Overlay Modal */
        .overlay-modal {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 12, 41, 0.8);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 20px;
            z-index: 200;
            backdrop-filter: blur(12px);
        }

        .overlay-card {
            background: linear-gradient(145deg, #1e1b4b, #0f0c29);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 24px;
            padding: 28px 24px;
            max-width: 400px;
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
            animation: modalPop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        @keyframes modalPop {
            0% { transform: scale(0.85); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }

        .overlay-icon {
            font-size: 48px;
            color: #10b981;
            margin-bottom: 10px;
        }

        .btn-modal-action {
            width: 100%;
            max-width: 180px;
            height: 44px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.12);
            color: white;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            margin-top: 18px;
            flex: none;
        }

        .btn-modal-action:hover {
            background: rgba(255, 255, 255, 0.25);
            border-color: rgba(255, 255, 255, 0.4);
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <header>
        <div class="header-inner">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <div class="header-brand">
                    <div class="logo-box">🎱</div>
                    <div>
                        <div class="brand-title">
                            Bida Club
                            <span class="table-badge-header">{table_name}</span>
                        </div>
                        <div class="brand-sub">📍 3xx Huỳnh Tấn Phát, Q7 HCM &nbsp;|&nbsp; 📞 0396123456</div>
                    </div>
                </div>

                <!-- POSITION 2: NOTIFICATION BELL BUTTON -->
                <button id="notif-bell-btn" onclick="openNotifDrawer()" class="notif-bell-btn" title="Thông báo phiên chơi">
                    🔔 <span id="notif-count-badge" class="notif-count-badge" style="display: none;">0</span>
                </button>
            </div>
            
            <div class="play-badge" id="play-time-display" style="margin-top: 10px; width: fit-content;">
                🕒 Đã chơi: <span id="play-duration">--</span> (Từ <span id="play-start-time">--</span>)
            </div>
        </div>
    </header>

    <div class="main-container">
        <!-- TOP BANNERS GRID -->
        <div class="top-banner-grid">
            <div class="pills-column">
                <div class="pill-banner">
                    <div class="pill-icon">🍵</div>
                    <div>
                        <div class="pill-title">Miễn phí trà đá, khăn lạnh</div>
                        <div class="pill-desc">Phục vụ tận bàn, giữ xe & máy lạnh</div>
                    </div>
                </div>
                <div class="pill-banner">
                    <div class="pill-icon">🎱</div>
                    <div>
                        <div class="pill-title">Mượn phụ kiện miễn phí</div>
                        <div class="pill-desc">Cơ mộc, cơ carbon, bao tay, lơ cao cấp</div>
                    </div>
                </div>
                <div class="pill-banner">
                    <div class="pill-icon">🧋</div>
                    <div>
                        <div class="pill-title">Mang đồ ăn/thức uống ngoài</div>
                        <div class="pill-desc">Thoải mái sử dụng (phụ thu 5k nếu bày bừa)</div>
                    </div>
                </div>
                <div class="pill-banner">
                    <div class="pill-icon">💲</div>
                    <div>
                        <div class="pill-title">Bảng giá giờ chơi minh bạch</div>
                        <div class="pill-desc">Pool / Libre: 29k-39k/h &nbsp;|&nbsp; 3B: 39k-49k/h</div>
                    </div>
                </div>
                <div class="pill-banner">
                    <div class="pill-icon">🏪</div>
                    <div>
                        <div class="pill-title">Mở cửa 24/7 xuyên lễ tết</div>
                        <div class="pill-desc">Máy lạnh phà phà, sau 22h xin gọi NV mở cửa</div>
                    </div>
                </div>
                <div class="pill-banner">
                    <div class="pill-icon">📶</div>
                    <div>
                        <div class="pill-title">Wifi tốc độ cao miễn phí</div>
                        <div class="pill-desc">Mật khẩu: bidaclub8888 (kết nối tự động)</div>
                    </div>
                </div>
            </div>
            
            <div class="promo-banner-box">
                <img src="/assets/promo.png" alt="Bida Club Promo" onerror="this.parentElement.style.display='none'">
            </div>
        </div>

        <!-- ORDER HISTORY -->
        <div class="history-box" id="order-history-section">
            <div class="history-title">📜 Các món bàn bạn đã đặt trước đó:</div>
            <div id="order-history-list"></div>
        </div>

        <!-- CATEGORY TABS -->
        <div class="category-tabs" id="category-tabs"></div>

        <!-- MENU GRID CONTAINER -->
        <div id="menu-items-container"></div>

        <!-- CART & CUSTOMER INFO -->
        <div class="cart-form-box">
            <div class="form-title">🛒 Giỏ hàng đã chọn & Thông tin người nhận</div>
            <div class="cart-items-list" id="cart-summary-list"></div>
            
            <div class="input-grid">
                <input type="text" id="order-name" class="input-field" placeholder="👤 Tên người nhận (Tùy chọn khi gọi yêu cầu nghiệp vụ)">
                <input type="tel" id="order-phone" class="input-field" placeholder="📞 Số điện thoại nhận đồ (Không bắt buộc)">
            </div>
            <textarea id="order-note" class="input-field" style="height: 60px; padding: 10px; resize: none; margin-top: 12px;" placeholder="📝 Ghi chú yêu cầu (Ví dụ: Sting ít đá, Mực chín kỹ...)"></textarea>
        </div>
    </div>

    <!-- STICKY BOTTOM BAR -->
    <div class="bottom-bar">
        <div class="bar-container">
            <div class="total-box">
                <span class="total-lbl">Tổng tạm tính</span>
                <span class="total-val" id="total-amount">0đ</span>
            </div>
            <button class="btn-order" id="submit-order-btn" onclick="submitOrder()" disabled>
                🛒 Gửi yêu cầu gọi món
            </button>
        </div>
    </div>

    <!-- SUCCESS OVERLAY -->
    <div class="overlay-modal" id="success-overlay">
        <div class="overlay-card">
            <div class="overlay-icon">✔️</div>
            <h2 style="font-weight: 800; color: #fbbf24; font-size: 22px;">Gửi yêu cầu thành công!</h2>
            <p style="color: #9ca3af; font-size: 14px; margin-top: 8px;">Nhân viên đã nhận được order và đang chuẩn bị đồ phục vụ bạn.</p>
            <button class="btn-modal-action" onclick="resetMenu()">Tiếp tục gọi món</button>
        </div>
    </div>

    <!-- NOTIFY OVERLAY -->
    <div class="overlay-modal" id="notify-overlay">
        <div class="overlay-card">
            <div class="overlay-icon" id="notify-icon">🔔</div>
            <h2 style="font-weight: 800; color: #60a5fa; font-size: 20px;" id="notify-title">Thông báo</h2>
            <p style="color: #e5e7eb; font-size: 14px; margin-top: 6px;" id="notify-msg"></p>
            <button class="btn-modal-action" onclick="closeNotify()">Đóng</button>
        </div>
    </div>

    <script>
        var tableId = {table_id};
        var qrToken = "{qr_token}";
        var inventoryStock = {inventory_stock_json};
        
        var activeStartTime = "{active_start_time}";
        if (activeStartTime && activeStartTime !== "None") {
            var startTime = new Date(activeStartTime);
            var minText = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            document.getElementById("play-start-time").textContent = minText;
            
            function updatePlayTime() {
                var diffMs = new Date() - startTime;
                var diffMins = Math.max(0, Math.floor(diffMs / 60000));
                var diffHours = Math.floor(diffMins / 60);
                var minsLeft = diffMins % 60;
                var text = diffHours > 0 ? diffHours + "h " + minsLeft + "m" : diffMins + "m";
                document.getElementById("play-duration").textContent = text;
            }
            updatePlayTime();
            setInterval(updatePlayTime, 30000);
        } else {
            document.getElementById("play-time-display").innerHTML = "⚠️ Bàn chưa kích hoạt chơi!";
            document.getElementById("play-time-display").style.color = "#ef4444";
        }

        var savedPhone = localStorage.getItem("customer_phone");
        if (savedPhone) {
            document.getElementById("order-phone").value = savedPhone;
        }

        var menuItems = {dynamic_menu_json};
        var orderQty = {};
        window.otherReqText = "";
        window.saveOtherReq = function(val) { 
            window.otherReqText = val; 
            updateTotal(); 
        };

        var categories = ["Thức uống", "Đồ ăn", "Thuốc lá", "Dịch vụ khác", "Yêu cầu nghiệp vụ"];
        var activeCategory = "all";

        function renderCategories() {
            var container = document.getElementById("category-tabs");
            if (!container) return;
            container.innerHTML = "";
            
            var allBtn = document.createElement("button");
            allBtn.className = "cat-btn " + (activeCategory === "all" ? "active" : "");
            allBtn.onclick = function() { filterCategory("all"); };
            allBtn.textContent = "✨ Tất cả";
            container.appendChild(allBtn);
            
            categories.forEach(function(cat) {
                var icon = "🍹 ";
                if (cat === "Đồ ăn") icon = "🍔 ";
                else if (cat === "Thuốc lá") icon = "🚬 ";
                else if (cat === "Dịch vụ khác") icon = "❄️ ";
                else if (cat === "Yêu cầu nghiệp vụ") icon = "🛎️ ";
                
                var btn = document.createElement("button");
                btn.className = "cat-btn " + (activeCategory === cat ? "active" : "");
                btn.onclick = function() { filterCategory(cat); };
                btn.textContent = icon + cat;
                container.appendChild(btn);
            });
        }

        function filterCategory(cat) {
            activeCategory = cat;
            renderCategories();
            renderMenu();
        }

        function toggleProductQty(name, stock) {
            var current = orderQty[name] || 0;
            if (current >= stock) {
                orderQty[name] = 0;
            } else {
                orderQty[name] = current + 1;
            }
            renderMenu();
        }

        function adjustItemQty(name, delta, stock) {
            var current = orderQty[name] || 0;
            var nextVal = current + delta;
            if (nextVal < 0) nextVal = 0;
            if (nextVal > stock) nextVal = stock;
            orderQty[name] = nextVal;
            renderMenu();
        }

        function renderMenu() {
            var container = document.getElementById("menu-items-container");
            container.innerHTML = "";
            
            categories.forEach(function(cat) {
                if (activeCategory !== "all" && activeCategory.trim().normalize("NFC") !== cat.trim().normalize("NFC")) return;
                var catItems = menuItems.filter(function(item) { return (item.category || "").trim().normalize("NFC") === cat.trim().normalize("NFC"); });
                if (catItems.length === 0) return;
                
                if (cat === "Yêu cầu nghiệp vụ") {
                    // Header with title on left and item count on right
                    var serviceHeader = document.createElement("div");
                    serviceHeader.className = "service-section-header";
                    
                    var titleSpan = document.createElement("span");
                    titleSpan.textContent = "🛎️ Yêu cầu nghiệp vụ";
                    serviceHeader.appendChild(titleSpan);
                    
                    var countTag = document.createElement("span");
                    countTag.className = "service-count-tag";
                    countTag.textContent = catItems.length + " mục";
                    serviceHeader.appendChild(countTag);
                    
                    container.appendChild(serviceHeader);
                    
                    // 2-Column Grid of dashed-border service cards
                    var serviceGrid = document.createElement("div");
                    serviceGrid.className = "service-grid";
                    
                    var otherReqSelected = false;
                    
                    catItems.forEach(function(item) {
                        orderQty[item.name] = orderQty[item.name] || 0;
                        var isSelected = orderQty[item.name] > 0;
                        if (item.name === "Yêu cầu khác" && isSelected) otherReqSelected = true;
                        
                        var card = document.createElement("div");
                        card.className = "service-dashed-card " + (isSelected ? "active" : "");
                        card.onclick = function() {
                            orderQty[item.name] = isSelected ? 0 : 1;
                            renderMenu();
                        };
                        
                        var nameSpan = document.createElement("span");
                        nameSpan.className = "service-title-text";
                        nameSpan.textContent = item.name;
                        card.appendChild(nameSpan);
                        
                        var circle = document.createElement("div");
                        circle.className = "service-radio-circle";
                        if (isSelected) {
                            circle.textContent = "✓";
                        }
                        card.appendChild(circle);
                        
                        serviceGrid.appendChild(card);
                    });
                    
                    container.appendChild(serviceGrid);
                    
                    if (otherReqSelected) {
                        var input = document.createElement("input");
                        input.type = "text";
                        input.className = "input-field";
                        input.placeholder = "Nhập nội dung yêu cầu cụ thể...";
                        input.value = window.otherReqText;
                        input.style.marginBottom = "16px";
                        input.oninput = function() { window.saveOtherReq(this.value); };
                        container.appendChild(input);
                    }
                } else {
                    var catHeader = document.createElement("div");
                    catHeader.className = "section-header";
                    var icon = "🍹 Thức uống";
                    if (cat === "Đồ ăn") icon = "🍔 Đồ ăn";
                    else if (cat === "Thuốc lá") icon = "🚬 Thuốc lá";
                    else if (cat === "Dịch vụ khác") icon = "❄️ Dịch vụ khác";
                    catHeader.textContent = icon;
                    container.appendChild(catHeader);

                    var grid = document.createElement("div");
                    grid.className = "product-grid";
                    
                    catItems.forEach(function(item) {
                        orderQty[item.name] = orderQty[item.name] || 0;
                        var currentStock = item.stock !== undefined ? item.stock : (inventoryStock[item.name] || 0);
                        var count = orderQty[item.name];
                        var isSelected = count > 0;
                        
                        var card = document.createElement("div");
                        card.className = "prod-card " + (isSelected ? "selected" : "");
                        card.onclick = function() {
                            if (currentStock <= 0) return;
                            if (count === 0) adjustItemQty(item.name, 1, currentStock);
                        };
                        
                        if (isSelected) {
                            var badge = document.createElement("div");
                            badge.className = "badge-count";
                            badge.textContent = count;
                            card.appendChild(badge);
                        }
                        
                        var imgBox = document.createElement("div");
                        imgBox.className = "prod-img-box";
                        if (item.image_url) {
                            var img = document.createElement("img");
                            img.src = item.image_url;
                            img.onerror = function() { this.style.display = "none"; };
                            imgBox.appendChild(img);
                        } else {
                            var emoji = "🍹";
                            if (cat === "Đồ ăn") emoji = "🍔";
                            else if (cat === "Thuốc lá") emoji = "🚬";
                            else if (cat === "Dịch vụ khác") emoji = "❄️";
                            imgBox.textContent = emoji;
                        }
                        card.appendChild(imgBox);
                        
                        var nameDiv = document.createElement("div");
                        nameDiv.className = "prod-name";
                        nameDiv.textContent = item.name;
                        card.appendChild(nameDiv);
                        
                        var priceDiv = document.createElement("div");
                        priceDiv.className = "prod-price";
                        priceDiv.textContent = item.price.toLocaleString("vi-VN") + "đ";
                        card.appendChild(priceDiv);
                        
                        var stockDiv = document.createElement("div");
                        stockDiv.className = "prod-stock " + (currentStock <= 0 ? "out" : "");
                        stockDiv.textContent = currentStock > 0 ? ("Còn: " + currentStock) : "Hết hàng";
                        card.appendChild(stockDiv);
                        
                        // Circular Stepper controls (- 0 +) directly on each card
                        var stepper = document.createElement("div");
                        stepper.className = "circle-stepper";
                        
                        var btnM = document.createElement("button");
                        btnM.className = "btn-circle";
                        btnM.textContent = "-";
                        btnM.disabled = (count <= 0);
                        btnM.onclick = function(e) {
                            e.stopPropagation();
                            adjustItemQty(item.name, -1, currentStock);
                        };
                        stepper.appendChild(btnM);
                        
                        var num = document.createElement("input");
                        num.type = "number";
                        num.className = "circle-qty-input";
                        num.value = count;
                        num.min = 0;
                        num.max = currentStock;
                        num.onclick = function(e) { e.stopPropagation(); };
                        num.onchange = function(e) {
                            e.stopPropagation();
                            var val = parseInt(this.value);
                            if (isNaN(val) || val < 0) val = 0;
                            if (val > currentStock) {
                                val = currentStock;
                                this.value = val;
                            }
                            orderQty[item.name] = val;
                            renderMenu();
                        };
                        num.oninput = function(e) {
                            e.stopPropagation();
                        };
                        stepper.appendChild(num);
                        
                        var btnP = document.createElement("button");
                        btnP.className = "btn-circle";
                        btnP.textContent = "+";
                        btnP.disabled = (currentStock <= 0 || count >= currentStock);
                        btnP.onclick = function(e) {
                            e.stopPropagation();
                            adjustItemQty(item.name, 1, currentStock);
                        };
                        stepper.appendChild(btnP);
                        
                        card.appendChild(stepper);
                        
                        grid.appendChild(card);
                    });
                    
                    container.appendChild(grid);
                }
            });
            
            updateTotal();
        }

        function updateTotal() {
            var cartList = document.getElementById("cart-summary-list");
            if (cartList) cartList.innerHTML = "";
            
            var total = 0;
            var itemCount = 0;
            
            menuItems.forEach(function(item) {
                var qty = orderQty[item.name] || 0;
                if (qty > 0) {
                    itemCount += qty;
                    var itemTotal = item.price * qty;
                    total += itemTotal;
                    
                    if (cartList) {
                        var row = document.createElement("div");
                        row.className = "cart-row";
                        
                        var nameDiv = document.createElement("div");
                        nameDiv.className = "cart-row-name";
                        nameDiv.textContent = item.name + (item.price > 0 ? " (" + item.price.toLocaleString("vi-VN") + "đ)" : "");
                        row.appendChild(nameDiv);
                        
                        if (item.category === "Yêu cầu nghiệp vụ") {
                            var tag = document.createElement("span");
                            tag.style.cssText = "font-size: 12px; color: #fbbf24; font-weight: 700;";
                            tag.textContent = "Đã chọn ✓";
                            row.appendChild(tag);
                        } else {
                            var currentStock = item.stock !== undefined ? item.stock : (inventoryStock[item.name] || 0);
                            
                            var ctrls = document.createElement("div");
                            ctrls.className = "circle-stepper";
                            ctrls.style.width = "auto";
                            ctrls.style.gap = "8px";
                            ctrls.style.marginTop = "0";
                            
                            var btnM = document.createElement("button");
                            btnM.className = "btn-circle";
                            btnM.style.width = "28px";
                            btnM.style.height = "28px";
                            btnM.style.fontSize = "15px";
                            btnM.textContent = "-";
                            btnM.onclick = function(e) {
                                e.stopPropagation();
                                adjustItemQty(item.name, -1, currentStock);
                            };
                            ctrls.appendChild(btnM);
                            
                            var num = document.createElement("input");
                            num.type = "number";
                            num.className = "circle-qty-input";
                            num.style.width = "32px";
                            num.style.height = "26px";
                            num.style.fontSize = "13px";
                            num.value = qty;
                            num.min = 0;
                            num.max = currentStock;
                            num.onclick = function(e) { e.stopPropagation(); };
                            num.onchange = function(e) {
                                e.stopPropagation();
                                var val = parseInt(this.value);
                                if (isNaN(val) || val < 0) val = 0;
                                if (val > currentStock) val = currentStock;
                                orderQty[item.name] = val;
                                renderMenu();
                            };
                            ctrls.appendChild(num);
                            
                            var btnP = document.createElement("button");
                            btnP.className = "btn-circle";
                            btnP.style.width = "28px";
                            btnP.style.height = "28px";
                            btnP.style.fontSize = "15px";
                            btnP.textContent = "+";
                            btnP.disabled = (currentStock <= 0 || qty >= currentStock);
                            btnP.onclick = function(e) {
                                e.stopPropagation();
                                adjustItemQty(item.name, 1, currentStock);
                            };
                            ctrls.appendChild(btnP);
                            
                            row.appendChild(ctrls);
                        }
                        
                        cartList.appendChild(row);
                    }
                }
            });
            
            if (cartList && itemCount === 0) {
                cartList.innerHTML = "<div style='text-align: center; color: #6b7280; font-size: 13px; font-style: italic; padding: 10px 0;'>Chưa chọn món nào (Nhấp vào món ở trên để chọn)</div>";
            }
            
            document.getElementById("total-amount").textContent = total.toLocaleString("vi-VN") + "đ";
            var btn = document.getElementById("submit-order-btn");
            if (btn) {
                btn.disabled = (itemCount === 0);
            }
        }


        // === SESSION-SCOPED NOTIFICATIONS ===
        var activeStartTime = "{active_start_time}";
        var notifStorageKey = "cust_notifs_table_" + tableId + "_" + activeStartTime;

        // Auto-cleanup old notifications from previous play sessions
        try {
            for (var key in localStorage) {
                if (key && key.startsWith("cust_notifs_table_" + tableId + "_") && key !== notifStorageKey) {
                    localStorage.removeItem(key);
                }
            }
        } catch(e) {}

        function getNotifs() {
            try {
                var stored = localStorage.getItem(notifStorageKey);
                return stored ? JSON.parse(stored) : [];
            } catch(e) { return []; }
        }

        function saveNotifs(notifArray) {
            try {
                localStorage.setItem(notifStorageKey, JSON.stringify(notifArray));
            } catch(e) {}
            renderNotifBadge();
        }

        function addNotification(msg, type, timeStr) {
            var notifs = getNotifs();
            
            // Deduplicate: ignore if identical message was logged as the most recent notification
            if (notifs.length > 0 && notifs[0].message === msg) {
                return;
            }

            var now = new Date();
            var timeFormatted = timeStr || ((now.getHours() < 10 ? "0" + now.getHours() : now.getHours()) + ":" + (now.getMinutes() < 10 ? "0" + now.getMinutes() : now.getMinutes()));
            
            notifs.unshift({
                id: "notif_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4),
                message: msg,
                type: type || "info",
                time: timeFormatted,
                read: false
            });
            saveNotifs(notifs);
        }

        function renderNotifBadge() {
            var notifs = getNotifs();
            var unreadCount = notifs.filter(function(n) { return !n.read; }).length;
            var badgeEl = document.getElementById("notif-count-badge");
            if (badgeEl) {
                if (unreadCount > 0) {
                    badgeEl.textContent = unreadCount;
                    badgeEl.style.display = "inline-block";
                } else {
                    badgeEl.style.display = "none";
                }
            }
        }

        function openNotifDrawer() {
            var notifs = getNotifs();
            notifs.forEach(function(n) { n.read = true; });
            saveNotifs(notifs);

            var container = document.getElementById("notif-list-container");
            if (!container) return;
            container.innerHTML = "";

            if (notifs.length === 0) {
                container.innerHTML = "<div style='text-align: center; padding: 30px 10px; color: #9ca3af; font-size: 13px; font-style: italic;'>Chưa có thông báo nào trong phiên chơi này.</div>";
            } else {
                notifs.forEach(function(n) {
                    var card = document.createElement("div");
                    var bg = "rgba(255,255,255,0.04)";
                    var border = "rgba(255,255,255,0.08)";
                    var icon = "🔔";

                    if (n.type === "error") {
                        bg = "rgba(239, 68, 68, 0.1)";
                        border = "rgba(239, 68, 68, 0.3)";
                        icon = "❌";
                    } else if (n.type === "success" || n.type === "redirect") {
                        bg = "rgba(16, 185, 129, 0.1)";
                        border = "rgba(16, 185, 129, 0.3)";
                        icon = "🎉";
                    }

                    card.style.cssText = "background: " + bg + "; border: 1px solid " + border + "; padding: 12px 14px; border-radius: 12px; display: flex; flex-direction: column; gap: 4px;";
                    card.innerHTML = 
                        "<div style='display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #9ca3af;'>" +
                            "<span>" + icon + " Thông báo</span>" +
                            "<span>" + n.time + "</span>" +
                        "</div>" +
                        "<div style='font-size: 13px; color: #ffffff; font-weight: 600; line-height: 1.4;'>" + n.message + "</div>";
                    container.appendChild(card);
                });
            }

            document.getElementById("notif-drawer-modal").style.display = "flex";
        }

        function closeNotifDrawer() {
            document.getElementById("notif-drawer-modal").style.display = "none";
        }

        function clearNotifs() {
            saveNotifs([]);
            openNotifDrawer();
        }
        
        // Initial badge check
        setTimeout(renderNotifBadge, 500);

        var lastReceivedMsg = "";
        var lastReceivedTime = 0;

        function pollClientMessages() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/client-poll/" + tableId, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res.has_message && res.data) {
                            var msgData = res.data;
                            var now = Date.now();
                            if (msgData.message === lastReceivedMsg && (now - lastReceivedTime) < 10000) {
                                return;
                            }
                            lastReceivedMsg = msgData.message;
                            lastReceivedTime = now;

                            var icon = msgData.type === "error" ? "❌" : "🎉";
                            showNotify(msgData.message, icon);
                            if (typeof addNotification === "function") {
                                addNotification(msgData.message, msgData.type);
                            }
                            if (msgData.type === "redirect" && msgData.redirect_url) {
                                setTimeout(function() {
                                    window.location.href = msgData.redirect_url;
                                }, 2500);
                            }
                        }
                    } catch(e) {}
                }
            };
            xhr.send();
        }
        setInterval(pollClientMessages, 10000);
        setTimeout(pollClientMessages, 1000);

        function submitOrder() {
            var name = document.getElementById("order-name").value.trim();
            var phone = document.getElementById("order-phone").value.trim();
            var note = document.getElementById("order-note").value.trim();
            
            localStorage.setItem("customer_phone", phone);
            
            var itemsList = [];
            var hasOnlyServices = true;
            
            menuItems.forEach(function(item) {
                var qty = orderQty[item.name] || 0;
                if (qty > 0) {
                    if (item.category !== "Yêu cầu nghiệp vụ") {
                        hasOnlyServices = false;
                    }
                    var customNote = (item.name === "Yêu cầu khác" && window.otherReqText) ? window.otherReqText : "";
                    itemsList.push({
                        item_name: item.name,
                        name: item.name,
                        quantity: qty,
                        qty: qty,
                        price: item.price,
                        category: item.category,
                        note: customNote
                    });
                }
            });
            
            if (itemsList.length === 0) {
                showNotify("Vui lòng chọn ít nhất 1 món hoặc dịch vụ!", "⚠️");
                return;
            }
            
            if (!hasOnlyServices && !name) {
                showNotify("Vui lòng điền tên người nhận khi gọi đồ ăn / thức uống!", "⚠️");
                return;
            }
            
            var btn = document.getElementById("submit-order-btn");
            btn.disabled = true;
            btn.textContent = "⏳ Đang gửi yêu cầu...";
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/customer-order/" + tableId + "/" + qrToken, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                btn.disabled = false;
                btn.textContent = "🛒 Gửi yêu cầu gọi món";
                if (xhr.status === 200) {
                    document.getElementById("success-overlay").style.display = "flex";
                    if (typeof addNotification === "function") {
                        addNotification("Đã gửi yêu cầu thành công! Nhân viên đang chuẩn bị đồ.", "success");
                    }
                } else {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        showNotify(res.message || "Gửi order thất bại! Vui lòng thử lại.", "❌");
                    } catch(e) {
                        showNotify("Gửi order thất bại (Mã " + xhr.status + "). Vui lòng thử lại!", "❌");
                    }
                }
            };
            xhr.onerror = function() {
                btn.disabled = false;
                btn.textContent = "🛒 Gửi yêu cầu gọi món";
                showNotify("Lỗi kết nối mạng! Vui lòng thử lại.", "❌");
            };
            xhr.send(JSON.stringify({
                customer_name: name,
                customer_phone: phone,
                phone: phone,
                note: note,
                items: itemsList
            }));
        }

        function resetMenu() {
            orderQty = {};
            window.otherReqText = "";
            document.getElementById("order-note").value = "";
            document.getElementById("success-overlay").style.display = "none";
            renderMenu();
        }

        function showNotify(msg, icon) {
            document.getElementById("notify-icon").textContent = icon || "🔔";
            document.getElementById("notify-msg").textContent = msg;
            document.getElementById("notify-overlay").style.display = "flex";
        }

        function closeNotify() {
            document.getElementById("notify-overlay").style.display = "none";
        }

        // Render History
        var orderHistory = {order_history_json};
        if (orderHistory && orderHistory.length > 0) {
            var hBox = document.getElementById("order-history-section");
            var hList = document.getElementById("order-history-list");
            if (hBox && hList) {
                hBox.style.display = "block";
                orderHistory.forEach(function(h) {
                    var itemDiv = document.createElement("div");
                    itemDiv.className = "history-item";
                    itemDiv.innerHTML = "<span>" + h.name + " x" + h.qty + "</span><span style='color: #34d399; font-weight: 700;'>" + h.total.toLocaleString("vi-VN") + "đ</span>";
                    hList.appendChild(itemDiv);
                });
            }
        }

        renderCategories();
        renderMenu();
    </script>

    <!-- NOTIFICATION DRAWER MODAL -->
    <div class="overlay-modal" id="notif-drawer-modal">
        <div class="overlay-card" style="max-width: 440px; text-align: left; align-items: stretch; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 12px; margin-bottom: 14px;">
                <div style="font-size: 16px; font-weight: 800; color: #fbbf24; display: flex; align-items: center; gap: 8px;">
                    🔔 Thông Báo Phiên Chơi
                </div>
                <span style="cursor: pointer; color: #9ca3af; font-size: 20px; font-weight: bold;" onclick="closeNotifDrawer()">✕</span>
            </div>
            
            <div id="notif-list-container" style="max-height: 350px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; padding-right: 4px;">
                <!-- Notifications list -->
            </div>

            <div style="display: flex; gap: 10px; margin-top: 16px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px;">
                <button onclick="clearNotifs()" style="flex: 1; height: 38px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.06); color: #d1d5db; font-size: 12px; font-weight: 600; cursor: pointer;">🗑️ Xóa tất cả</button>
                <button onclick="closeNotifDrawer()" style="flex: 1; height: 38px; border-radius: 10px; border: none; background: #6366f1; color: white; font-size: 12px; font-weight: 700; cursor: pointer;">Đóng</button>
            </div>
        </div>
    </div>

</body>
</html>"""
