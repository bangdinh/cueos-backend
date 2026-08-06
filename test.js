
        var eventsDiv = document.getElementById("events");
        var emptyState = document.getElementById("empty-state");
        var statusDot = document.getElementById("status-dot");
        var statusLabel = document.getElementById("status-label");
        var statusBanner = document.getElementById("status-banner");
        var bannerIcon = document.getElementById("banner-icon");
        var bannerText = document.getElementById("banner-text");
        var clockEl = document.getElementById("clock");
        var eventCountEl = document.getElementById("event-count");
        var soundBtn = document.getElementById("sound-btn");
        var tablesGrid = document.getElementById("tables-grid");
        
        var currentCamTableId = 1;

        var pollCount = 0;
        var eventCount = 0;
        var lastImage = "";
        var soundEnabled = true;
        var audioCtx = null;
        
        var tablesLocalData = [];
        var currentTableFilter = "all"; // all, empty, playing
        var streamStates = {}; // key: tableId, value: true/false (stream status)

        function syncStreamStates(tables) {
            tables.forEach(function(t) {
                var container = document.getElementById("cam-container-" + t.id);
                var statusBadge = document.getElementById("cam-status-" + t.id);
                
                if (container && statusBadge) {
                    // 1. Phân biệt màu sắc viền và badge bàn trống / bàn hoạt động
                    if (t.current_status === "PLAYING") {
                        container.className = "live-stream-container active-table";
                        statusBadge.className = "stream-status-badge status-active-playing";
                        statusBadge.textContent = "ĐANG CHƠI";
                        
                        // Tự động bật stream khi bàn chuyển trạng thái từ trống sang có khách chơi
                        if (streamStates[t.id] === undefined) {
                            streamStates[t.id] = true;
                        }
                    } else {
                        container.className = "live-stream-container empty-table";
                        statusBadge.className = "stream-status-badge status-empty-waiting";
                        statusBadge.textContent = "BÀN TRỐNG";
                        
                        // Bàn trống thì mặc định tắt stream để tiết kiệm băng thông mạng & CPU
                        if (streamStates[t.id] === undefined) {
                            streamStates[t.id] = false;
                        }
                    }
                    
                    // 2. Đồng bộ trạng thái stream (Hiển thị overlay đen và đổi nút)
                    var overlay = document.getElementById("cam-overlay-" + t.id);
                    var hoverOverlay = document.getElementById("cam-hover-" + t.id);
                    
                    if (streamStates[t.id]) {
                        if (overlay) overlay.className = "stream-overlay hidden";
                        if (hoverOverlay) hoverOverlay.style.display = "flex";
                    } else {
                        if (overlay) overlay.className = "stream-overlay";
                        if (hoverOverlay) hoverOverlay.style.display = "none";
                        
                        // Xóa thuộc tính src của thẻ img để trình duyệt ngừng call API live
                        var liveImg = document.getElementById("live-cam-" + t.id);
                        if (liveImg && !liveImg.src.includes("photo-1544197150-b99a580bb7a8")) {
                            liveImg.removeAttribute("src");
                        }
                    }
                }
            });
        }

        function toggleCamStream(tableId) {
            // Ngăn sự kiện click bọt (stopPropagation) nếu cần
            if (window.event) window.event.stopPropagation();
            
            streamStates[tableId] = !streamStates[tableId];
            syncStreamStates(tablesLocalData);
        }

        function toggleSidebar() {
            var sidebar = document.getElementById("sidebar");
            if (sidebar) {
                sidebar.classList.toggle("collapsed");
            }
        }

        function toggleDrawer(isOpen) {
            var drawer = document.getElementById("highlight-drawer");
            var overlay = document.getElementById("drawer-overlay");
            if (drawer && overlay) {
                if (isOpen) {
                    drawer.classList.add("open");
                    overlay.classList.add("open");
                    overlay.style.display = "block";
                } else {
                    drawer.classList.remove("open");
                    overlay.classList.remove("open");
                    setTimeout(function() {
                        if (!drawer.classList.contains("open")) {
                            overlay.style.display = "none";
                        }
                    }, 300);
                }
            }
        }

        function setTableFilter(filterType, element) {
            currentTableFilter = filterType;
            
            // Xoa active class khoi tat ca link
            var links = document.querySelectorAll(".sidebar-link");
            links.forEach(function(link) {
                link.classList.remove("active");
            });
            
            // Them active class cho link vua bam
            if (element) {
                element.classList.add("active");
            }
            
            // Render lai grid voi filter moi
            renderTablesGrid(tablesLocalData);
        }

        // === CLOCK ===
        function updateClock() {
            var now = new Date();
            var h = now.getHours();
            var m = now.getMinutes();
            var s = now.getSeconds();
            clockEl.textContent = (h < 10 ? "0" + h : h) + ":" + (m < 10 ? "0" + m : m) + ":" + (s < 10 ? "0" + s : s);
        }
        setInterval(updateClock, 1000);
        updateClock();

        // === LIVE CAM REFRESH ===
        // Chỉ refresh ảnh của các camera đang ở trạng thái Bật Stream (streamStates[id] = true)
        setInterval(function() {
            for (var id = 1; id <= 4; id++) {
                if (streamStates[id]) {
                    var liveImg = document.getElementById("live-cam-" + id);
                    if (liveImg) {
                        liveImg.src = "/api/live/" + id + "?t=" + Date.now();
                    }
                }
            }
        }, 1500);

        // === SOUND ===
        function toggleSound() {
            soundEnabled = !soundEnabled;
            soundBtn.className = soundEnabled ? "sound-toggle active" : "sound-toggle";
            document.getElementById("sound-icon").innerHTML = soundEnabled ? "&#128264;" : "&#128263;";
        }
        soundBtn.className = "sound-toggle active";

        function playAlert() {
            if (!soundEnabled) return;
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                var o1 = audioCtx.createOscillator();
                var g1 = audioCtx.createGain();
                o1.connect(g1); g1.connect(audioCtx.destination);
                o1.type = "sine"; o1.frequency.value = 880;
                g1.gain.setValueAtTime(0.3, audioCtx.currentTime);
                g1.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.5);
                o1.start(audioCtx.currentTime); o1.stop(audioCtx.currentTime + 0.5);
                
                var o2 = audioCtx.createOscillator();
                var g2 = audioCtx.createGain();
                o2.connect(g2); g2.connect(audioCtx.destination);
                o2.type = "sine"; o2.frequency.value = 1100;
                g2.gain.setValueAtTime(0.3, audioCtx.currentTime + 0.15);
                g2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.65);
                o2.start(audioCtx.currentTime + 0.15); o2.stop(audioCtx.currentTime + 0.65);
            } catch(e) {}
        }
        
        function playOrderAlert() {
            if (!soundEnabled) return;
            try {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                var freqs = [523.25, 659.25, 783.99, 1046.50];
                var startTime = audioCtx.currentTime;
                freqs.forEach(function(f, i) {
                    var o = audioCtx.createOscillator();
                    var g = audioCtx.createGain();
                    o.connect(g); g.connect(audioCtx.destination);
                    o.type = "sine"; 
                    o.frequency.value = f;
                    g.gain.setValueAtTime(0.4, startTime + i * 0.15);
                    g.gain.exponentialRampToValueAtTime(0.001, startTime + i * 0.15 + 0.3);
                    o.start(startTime + i * 0.15); 
                    o.stop(startTime + i * 0.15 + 0.3);
                });
            } catch(e) {}
        }

        // === HISTORY MODAL LOGIC ===
        function openHistoryModal() {
            document.getElementById('history-modal').style.display = 'flex';
            loadHistory();
        }

        function closeHistoryModal() {
            document.getElementById('history-modal').style.display = 'none';
        }

        function loadHistory() {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/history', true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var history = JSON.parse(xhr.responseText);
                    var tbody = document.getElementById('history-items-body');
                    tbody.innerHTML = '';
                    history.forEach(function(h) {
                        var canDeleteAttr = h.can_delete ? "data-candelete='true'" : "data-candelete='false' disabled";
                        var chkHtml = '<input type="checkbox" class="chk-history" value="' + h.id + '" ' + canDeleteAttr + ' onchange="updateHistoryDeleteBtn()">';
                        
                        var tr = document.createElement('tr');
                        tr.style.borderBottom = "1px solid rgba(255,255,255,0.06)";
                        tr.innerHTML = `
                            <td style="padding: 10px 8px; text-align: center;">${chkHtml}</td>
                            <td style="padding: 10px 8px;">${h.table_name}</td>
                            <td style="padding: 10px 8px;">${new Date(h.start_time).toLocaleString('vi-VN')}</td>
                            <td style="padding: 10px 8px;">${new Date(h.end_time).toLocaleString('vi-VN')}</td>
                            <td style="padding: 10px 8px; text-align: right;">${h.total_minutes} phút</td>
                            <td style="padding: 10px 8px; text-align: right; color: #86efac; font-weight: bold;">${h.total_bill.toLocaleString('vi-VN')} đ</td>
                            <td style="padding: 10px 8px; text-align: center;">
                                <button onclick="toggleHistoryDetail(${h.id})" style="padding: 4px 8px; background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.4); color: #a5b4fc; border-radius: 4px; cursor: pointer;">Chi tiết ⬇</button>
                            </td>
                        `;
                        if (!h.can_delete) {
                            tr.style.opacity = "0.6";
                        }
                        
                        var itemsHtml = h.items.map(function(item) {
                            return `<tr><td style="padding: 4px 8px;">${item.item_name}</td><td style="padding: 4px 8px; text-align: center;">${item.quantity}</td><td style="padding: 4px 8px; text-align: right;">${item.total_price.toLocaleString('vi-VN')} đ</td></tr>`;
                        }).join("");
                        
                        var detailTr = document.createElement('tr');
                        detailTr.id = 'history-detail-' + h.id;
                        detailTr.style.display = 'none';
                        detailTr.innerHTML = `
                            <td colspan="7" style="padding: 10px 24px; background: rgba(0,0,0,0.3); border-bottom: 1px solid rgba(255,255,255,0.06);">
                                <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px;">Tiền giờ: <b style="color: white;">${h.play_fee.toLocaleString('vi-VN')} đ</b></div>
                                <table style="width: 100%; border-collapse: collapse; font-size: 11px;">
                                    <tr style="color: #fbbf24; border-bottom: 1px dashed rgba(255,255,255,0.1);">
                                        <th style="padding: 4px 8px; text-align: left;">Món ăn / Dịch vụ</th>
                                        <th style="padding: 4px 8px;">SL</th>
                                        <th style="padding: 4px 8px; text-align: right;">Thành tiền</th>
                                    </tr>
                                    ${itemsHtml || '<tr><td colspan="3" style="padding: 4px 8px; text-align: center; color: #6b7280;">Không gọi thêm món</td></tr>'}
                                </table>
                            </td>
                        `;
                        
                        tbody.appendChild(tr);
                        tbody.appendChild(detailTr);
                    });
                    updateHistoryDeleteBtn();
                }
            };
            xhr.send();
        }

        function toggleHistoryDetail(id) {
            var tr = document.getElementById('history-detail-' + id);
            if (tr) {
                tr.style.display = tr.style.display === 'none' ? 'table-row' : 'none';
            }
        }

        function toggleAllHistory(source) {
            var checkboxes = document.querySelectorAll('.chk-history:not([disabled])');
            for (var i = 0; i < checkboxes.length; i++) {
                checkboxes[i].checked = source.checked;
            }
            updateHistoryDeleteBtn();
        }

        function updateHistoryDeleteBtn() {
            var checkboxes = document.querySelectorAll('.chk-history:checked');
            var btn = document.getElementById('btn-delete-history');
            if (checkboxes.length > 0) {
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.textContent = '🗑️ Xóa đã chọn (' + checkboxes.length + ')';
            } else {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.textContent = '🗑️ Xóa đã chọn';
            }
        }

        function deleteSelectedHistory() {
            var checkboxes = document.querySelectorAll('.chk-history:checked');
            var ids = Array.from(checkboxes).map(function(c) { return parseInt(c.value); });
            if (ids.length === 0) return;
            
            if (!confirm('Bạn có chắc chắn muốn xóa ' + ids.length + ' phiên chơi này? Hành động này không thể hoàn tác.')) return;
            
            var xhr = new XMLHttpRequest();
            xhr.open('DELETE', '/api/history', true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onload = function() {
                if (xhr.status === 200) {
                    alert('Đã xóa thành công!');
                    document.getElementById('chk-all-history').checked = false;
                    loadHistory();
                } else {
                    alert('Lỗi khi xóa: ' + xhr.responseText);
                }
            };
            xhr.send(JSON.stringify({ session_ids: ids }));
        }

        // === LOAD TABLES DATA ===
        function loadTables(callback) {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/tables?_" + Date.now(), true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var tables = JSON.parse(xhr.responseText);
                    tablesLocalData = tables;
                    renderTablesGrid(tables);
                    syncStreamStates(tables); // Cập nhật trạng thái bật/tắt camera
                    if (typeof callback === 'function') callback();
                }
            };
            xhr.send();
        }

        // Luu tru trang thai form dang mo va cac gia tri input de khong bi reset khi loadTables
        var openForms = {}; 
        var formSelectedItems = {};
        var formQuantities = {};

        function renderTablesGrid(tables) {
            tablesGrid.innerHTML = "";
            
            // Bo loc trang thai ban choi
            var filteredTables = tables.filter(function(t) {
                if (currentTableFilter === "empty") {
                    return t.current_status !== "PLAYING";
                } else if (currentTableFilter === "playing") {
                    return t.current_status === "PLAYING";
                }
                return true; // "all"
            });
            
            if (filteredTables.length === 0) {
                tablesGrid.innerHTML = "<div style='grid-column: span 2; text-align: center; padding: 40px; color: #8b949e; font-size: 13px; font-weight: 500;'>Không có bàn nào phù hợp với bộ lọc hiện tại.</div>";
                return;
            }
            
            filteredTables.forEach(function(t) {
                var card = document.createElement("div");
                card.className = t.current_status === "PLAYING" ? "table-card playing" : "table-card";
                
                // Header card
                var header = document.createElement("div");
                header.className = "table-card-header";
                
                var nameSpan = document.createElement("span");
                nameSpan.className = "table-name";
                nameSpan.innerHTML = t.name;
                
                var badgesDiv = document.createElement("div");
                badgesDiv.className = "table-badges";
                
                var tierBadge = document.createElement("span");
                tierBadge.className = t.table_tier === "VIP" ? "badge-vip" : "badge-std";
                tierBadge.textContent = t.table_tier === "VIP" ? "VIP" : "Thường";
                
                var typeBadge = document.createElement("span");
                typeBadge.className = "badge-type";
                typeBadge.textContent = t.table_type === "LIP" ? "Líp" : "Phăng 3C";
                
                badgesDiv.appendChild(tierBadge);
                badgesDiv.appendChild(typeBadge);
                header.appendChild(nameSpan);
                header.appendChild(badgesDiv);
                card.appendChild(header);
                
                // Status label
                var statusDiv = document.createElement("div");
                statusDiv.style.fontSize = "13px";
                statusDiv.innerHTML = "Trạng thái: " + 
                    (t.current_status === "PLAYING" 
                        ? "<span class='table-status-label status-playing'>● Đang chơi</span>" 
                        : "<span class='table-status-label status-empty'>● Bàn trống</span>");
                card.appendChild(statusDiv);
                
                // Table details (Ghi bill & Thoi gian choi)
                var details = document.createElement("div");
                details.className = "table-details";
                
                if (t.current_status === "PLAYING" && t.active_session) {
                    details.style.cursor = "pointer";
                    details.title = "Nhấn để xem chi tiết hóa đơn";
                    details.addEventListener("click", function() { viewActiveBill(t.id); });
                    
                    var startTime = new Date(t.active_session.start_time);
                    var hour = startTime.getHours();
                    var min = startTime.getMinutes();
                    var timeStr = (hour < 10 ? "0" + hour : hour) + ":" + (min < 10 ? "0" + min : min);
                    
                    // Tinh nhanh tien va gio theo realtime
                    var diffMs = new Date() - startTime;
                    var diffSecs = Math.max(0, Math.floor(diffMs / 1000));
                    var diffMins = Math.floor(diffSecs / 60);
                    var diffHours = Math.floor(diffMins / 60);
                    var minsLeft = diffMins % 60;
                    
                    var durationText = diffHours > 0 ? diffHours + "h " + minsLeft + "m" : diffMins + "m";
                    
                    // Tinh tien gio
                    var playFee = Math.ceil((diffMins / 60) * t.price_per_hour);
                    
                    // Tinh tien dich vu mon an nuoc uong
                    var serviceTotal = 0;
                    var itemsText = "";
                    if (t.active_session.order_items && t.active_session.order_items.length > 0) {
                        t.active_session.order_items.forEach(function(item) {
                            serviceTotal += item.total_price;
                        });
                        itemsText = "<div style='color: #818cf8; margin-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 4px;'>Đồ gọi thêm: " + 
                            t.active_session.order_items.map(function(i){return i.item_name + " x" + i.quantity;}).join(", ") + "</div>";
                    }
                    
                    var totalBill = playFee + serviceTotal;
                    
                    details.innerHTML = 
                        "<div>Vào lúc: <b>" + timeStr + "</b></div>" +
                        "<div>Đã chơi: <b style='color: #fbbf24;'>" + durationText + "</b></div>" +
                        "<div>Tiền giờ: <b>" + playFee.toLocaleString("vi-VN") + " đ</b></div>" +
                        "<div>Tiền dịch vụ: <b>" + serviceTotal.toLocaleString("vi-VN") + " đ</b></div>" +
                        "<div style='border-top: 1px solid rgba(255,255,255,0.1); padding-top:4px; margin-top:2px; color: #86efac; font-weight:700;'>TỔNG BILL: " + totalBill.toLocaleString("vi-VN") + " đ</div>" +
                        itemsText;
                } else {
                    details.innerHTML = 
                        "<div>Đơn giá: <b>" + t.price_per_hour.toLocaleString("vi-VN") + " VNĐ/h</b></div>" +
                        "<div style='color: #6b7280;'>Sẵn sàng đón khách mới</div>";
                }
                card.appendChild(details);
                
                // Button Actions
                var btnGroup = document.createElement("div");
                btnGroup.className = "order-btn-group";
                
                if (t.current_status === "PLAYING") {
                    // Nut Them mon
                    var btnAdd = document.createElement("button");
                    btnAdd.className = "btn btn-highlight btn-small";
                    btnAdd.innerHTML = "➕ Thêm món";
                    btnAdd.addEventListener("click", function() {
                        showAddItemForm(t.id);
                    });
                    btnGroup.appendChild(btnAdd);
                    
                    // Nut Thanh toan
                    var btnStop = document.createElement("button");
                    btnStop.className = "btn btn-confirm btn-small";
                    btnStop.innerHTML = "🔴 Thanh toán";
                    btnStop.addEventListener("click", function() {
                        checkoutSession(t.id);
                    });
                    btnGroup.appendChild(btnStop);
                    
                    // Nut In Bill Tạm Tính
                    var btnPrintTemp = document.createElement("button");
                    btnPrintTemp.className = "btn btn-dismiss btn-small";
                    btnPrintTemp.style.cssText = "background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.3); color: #a5b4fc;";
                    btnPrintTemp.innerHTML = "🖨️ In Tạm Tính";
                    btnPrintTemp.addEventListener("click", function(e) {
                        e.stopPropagation();
                        viewActiveBill(t.id, true);
                    });
                    btnGroup.appendChild(btnPrintTemp);
                    
                    // Nut Chuyen ban
                    var btnTransfer = document.createElement("button");
                    btnTransfer.className = "btn btn-dismiss btn-small";
                    btnTransfer.style.cssText = "background: rgba(14, 165, 233, 0.15); border-color: rgba(14, 165, 233, 0.3); color: #7dd3fc;";
                    btnTransfer.innerHTML = "🔄 Chuyển bàn";
                    btnTransfer.addEventListener("click", function(e) {
                        e.stopPropagation();
                        showTransferModal(t.id);
                    });
                    btnGroup.appendChild(btnTransfer);
                } else {
                    // Nut Bat dau choi
                    var btnStart = document.createElement("button");
                    btnStart.className = "btn btn-confirm btn-small";
                    btnStart.style.background = "linear-gradient(135deg, #6366f1, #4f46e5)";
                    btnStart.innerHTML = "🟢 Bắt đầu chơi";
                    btnStart.addEventListener("click", function() {
                        startSession(t.id);
                    });
                    btnGroup.appendChild(btnStart);
                }
                
                // Nut ma QR
                var btnQR = document.createElement("button");
                btnQR.className = "btn btn-dismiss btn-small";
                btnQR.style.cssText = "background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.25); color: #fbbf24;";
                btnQR.innerHTML = "📷 Mã QR";
                btnQR.addEventListener("click", function() {
                    showTableQRModal(t.id, t.name, t.qr_token);
                });
                btnGroup.appendChild(btnQR);
                
                card.appendChild(btnGroup);
                
                // Nút Mở Giao Diện POS (chỉ hiện khi bàn đang chơi)
                if (t.current_status === "PLAYING") {
                    var btnPos = document.createElement("button");
                    btnPos.className = "btn btn-primary btn-small";
                    btnPos.style.cssText = "background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #34d399; width: 100%; margin-top: 8px; font-weight: bold;";
                    btnPos.innerHTML = "🛒 Thu ngân gọi món";
                    btnPos.addEventListener("click", function() {
                        openPosModal(t.id, t.name);
                    });
                    card.appendChild(btnPos);
                }
                
                tablesGrid.appendChild(card);
            });
        }
        


        function requestSelectedClip() {
            var tableSelect = document.getElementById("highlight-table-select");
            if (tableSelect) {
                requestClip(parseInt(tableSelect.value));
            }
        }
        function requestSelectedPastClip() {
            var tableSelect = document.getElementById("highlight-table-select");
            if (tableSelect) {
                requestPastClip(parseInt(tableSelect.value));
            }
        }

        // === START SESSION API ===
        function startSession(tableId) {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/start/" + tableId, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    loadTables();
                } else {
                    var errMsg = "Không thể bắt đầu phiên chơi!";
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res && res.message) errMsg = res.message;
                    } catch(e) {}
                    alert(errMsg);
                }
            };
            xhr.send();
        }



        // === TRANSFER TABLE ===
        function showTransferModal(fromTableId, requestedType) {
            var emptyTables = tablesLocalData.filter(function(t) { return t.current_status === "EMPTY"; });
            
            var typeName = "";
            if (requestedType) {
                emptyTables = emptyTables.filter(function(t) { return t.table_type === requestedType; });
                if (requestedType === "LIP") typeName = "Líp";
                else if (requestedType === "3C") typeName = "3 Băng";
                else if (requestedType === "POOL") typeName = "Lỗ";
                
                if (emptyTables.length === 0) {
                    alert("Hiện tại không có bàn " + typeName + " nào trống để chuyển. Đã tự động báo cho khách!");
                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", "/api/client-notify/" + fromTableId, true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.send(JSON.stringify({ message: "Tạm thời hết bàn " + typeName + ", mong quý khách thông cảm!", type: "error" }));
                    return;
                }
            } else {
                if (emptyTables.length === 0) {
                    alert("Hiện tại không có bàn nào trống để chuyển. Đã tự động báo cho khách!");
                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", "/api/client-notify/" + fromTableId, true);
                    xhr.setRequestHeader("Content-Type", "application/json");
                    xhr.send(JSON.stringify({ message: "Tạm thời hết bàn, mong quý khách thông cảm!", type: "error" }));
                    return;
                }
            }
            
            var nl = String.fromCharCode(10);
            var options = emptyTables.map(function(t) { return t.id + " - " + t.name + " (" + t.table_type + ")"; }).join(nl);
            
            var promptMsg = "Chuyển bàn gốc ID: " + fromTableId + nl;
            if (typeName) promptMsg += "Yêu cầu: Đổi sang bàn " + typeName + nl;
            promptMsg += "Danh sách bàn trống:" + nl + options + nl + nl + "Nhập ID bàn đích (ví dụ: " + emptyTables[0].id + "):";
            
            var targetId = prompt(promptMsg);
            
            if (targetId) {
                var toTableId = parseInt(targetId);
                var toTable = emptyTables.find(function(t) { return t.id === toTableId; });
                if (!toTable) {
                    alert("ID bàn đích không hợp lệ hoặc bàn đang không trống!");
                    return;
                }
                transferTable(fromTableId, toTableId);
            }
        }

        function showRejectTransferModal(tableId) {
            var nl = String.fromCharCode(10);
            var reasonCode = prompt("Từ chối yêu cầu đổi bàn (Bàn " + tableId + ")" + nl +
                                    "Chọn lý do:" + nl +
                                    "1 - Hết bàn" + nl +
                                    "2 - Bàn hỏng" + nl +
                                    "3 - Khác (nhập lý do cụ thể)" + nl +
                                    "Nhập 1, 2 hoặc 3:");
            if (!reasonCode) return;
            
            var reason = reasonCode;
            if (reasonCode === "1") reason = "Hết bàn, mong quý khách thông cảm!";
            else if (reasonCode === "2") reason = "Bàn đang hỏng, mong quý khách thông cảm!";
            else if (reasonCode === "3") {
                reason = prompt("Nhập lý do từ chối:");
                if (!reason) return;
            }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/client-notify/" + tableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.send(JSON.stringify({
                message: "Yêu cầu đổi bàn đã bị từ chối. Lý do: " + reason,
                type: "error"
            }));
            alert("Đã gửi thông báo từ chối tới khách!");
        }
        
        function transferTable(fromTableId, toTableId) {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/transfer/" + fromTableId + "/" + toTableId, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    alert("Chuyển bàn thành công!");
                    loadTables();
                } else {
                    var res = JSON.parse(xhr.responseText || "{}");
                    alert("Lỗi chuyển bàn: " + (res.message || xhr.statusText));
                }
            };
            xhr.send();
        }

        function checkoutSession(tableId) {
            Swal.fire({
                title: 'Xác nhận thanh toán?',
                text: "Bạn có chắc chắn muốn tính tiền và thanh toán hóa đơn cho bàn này?",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#10b981',
                cancelButtonColor: '#ef4444',
                confirmButtonText: 'Đồng ý',
                cancelButtonText: 'Hủy'
            }).then((result) => {
                if (result.isConfirmed) {
                    var xhr = new XMLHttpRequest();
                    xhr.open("POST", "/api/session/stop/" + tableId, true);
                    xhr.onload = function() {
                        if (xhr.status === 200) {
                            var res = JSON.parse(xhr.responseText);
                            var bill = res.bill || res;
                            Swal.fire({
                                title: 'Thanh toán thành công!',
                                text: 'Bạn có muốn in hóa đơn (Bill) giấy cho khách không?',
                                icon: 'success',
                                showCancelButton: true,
                                confirmButtonColor: '#10b981',
                                cancelButtonColor: '#6b7280',
                                confirmButtonText: '🖨️ In Hóa Đơn',
                                cancelButtonText: 'Không in'
                            }).then((printResult) => {
                                if (printResult.isConfirmed) {
                                    currentBillToPrint = bill;
                                    printBill(); 
                                }
                                loadTables();
                            });
                        } else {
                            Swal.fire('Lỗi!', 'Không thể thanh toán!', 'error');
                        }
                    };
                    xhr.send();
                }
            });
        }

        // === VIEW ACTIVE BILL PREVIEW ===
        function viewActiveBill(tableId, silentPrint = false) {
            var t = tablesLocalData.find(function(item) { return item.id === tableId; });
            if (!t || t.current_status !== "PLAYING" || !t.active_session) return;
            
            var startTime = new Date(t.active_session.start_time);
            var endTime = new Date();
            var diffMs = endTime - startTime;
            var diffMins = Math.max(0, Math.floor(diffMs / 60000));
            
            var playFee = Math.ceil((diffMins / 60) * t.price_per_hour);
            
            var itemsList = [];
            var serviceTotal = 0;
            if (t.active_session.order_items && t.active_session.order_items.length > 0) {
                t.active_session.order_items.forEach(function(item) {
                    serviceTotal += item.total_price;
                    itemsList.push({
                        id: item.id,
                        item_name: item.item_name,
                        quantity: item.quantity,
                        price: item.price,
                        total_price: item.total_price
                    });
                });
            }
            
            var totalBill = playFee + serviceTotal;
            
            var tempBill = {
                table_id: t.id,
                table_name: t.name,
                start_time: t.active_session.start_time,
                end_time: endTime.toISOString(),
                total_minutes: diffMins,
                play_fee: playFee,
                items: itemsList,
                service_total: serviceTotal,
                total_bill: totalBill,
                is_preview: true
            };
            
            if (silentPrint) {
                currentBillToPrint = tempBill;
                printBill();
            } else {
                showBillInvoice(tempBill);
            }
        }

        // === SHOW BILL MODAL INVOICE ===
        function showBillInvoice(bill) {
            document.getElementById("bill-table-name").textContent = bill.table_name;
            
            var start = new Date(bill.start_time);
            var end = new Date(bill.end_time);
            
            document.getElementById("bill-start-time").textContent = start.toLocaleString('vi-VN');
            document.getElementById("bill-end-time").textContent = end.toLocaleString('vi-VN');
            
            var endTimeRow = document.getElementById("bill-end-time-row");
            if (endTimeRow) {
                endTimeRow.style.display = bill.is_preview ? "none" : "flex";
            }
            
            document.getElementById("bill-duration").textContent = bill.total_minutes + " phút";
            document.getElementById("bill-play-fee").textContent = Math.ceil(bill.play_fee).toLocaleString("vi-VN") + " VNĐ";
            
            var itemsBody = document.getElementById("bill-items-body");
            itemsBody.innerHTML = "";
            
            if (bill.items && bill.items.length > 0) {
                bill.items.forEach(function(item) {
                    var itemName = item.item_name || item.name || "";
                    var itemPrice = item.price || (item.quantity ? item.total_price / item.quantity : 0);
                    var tr = document.createElement("tr");
                    tr.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
                    
                    var actionsHtml = "";
                    if (bill.is_preview && item.id && bill.table_id) {
                        var safeName = itemName.replace(/'/g, "\\'").replace(/"/g, '&quot;');
                        actionsHtml = 
                            "<span style='float:right; display:inline-flex; align-items:center; gap:4px; margin-left:8px;'>" +
                                "<button onclick='updateBillItemQty(" + item.id + ", " + (item.quantity - 1) + ", " + bill.table_id + ")' style='background:#374151; color:white; border:none; border-radius:4px; width:22px; height:22px; cursor:pointer; font-weight:bold; display:inline-flex; align-items:center; justify-content:center;' title='Giảm 1'>-</button>" +
                                "<button onclick='updateBillItemQty(" + item.id + ", " + (item.quantity + 1) + ", " + bill.table_id + ")' style='background:#374151; color:white; border:none; border-radius:4px; width:22px; height:22px; cursor:pointer; font-weight:bold; display:inline-flex; align-items:center; justify-content:center;' title='Tăng 1'>+</button>" +
                                "<button onclick='deleteBillItem(" + item.id + ", " + bill.table_id + ", \"" + safeName + "\")' style='background:#ef4444; color:white; border:none; border-radius:4px; padding:2px 6px; cursor:pointer; font-size:11px;' title='Xóa món'>🗑️</button>" +
                            "</span>";
                    }
                    
                    tr.innerHTML = 
                        "<td style='padding: 6px 0; color: #e5e7eb;'>" + itemName + actionsHtml + "</td>" +
                        "<td style='padding: 6px 8px; text-align: center; font-weight: 600; color: #fbbf24;'>" + item.quantity + "</td>" +
                        "<td style='padding: 6px 8px; text-align: right; font-variant-numeric: tabular-nums;'>" + Math.ceil(itemPrice).toLocaleString("vi-VN") + " đ</td>" +
                        "<td style='padding: 6px 0; text-align: right; font-weight: 700; color: white; font-variant-numeric: tabular-nums;'>" + Math.ceil(item.total_price).toLocaleString("vi-VN") + " đ</td>";
                    itemsBody.appendChild(tr);
                });
            } else {
                itemsBody.innerHTML = "<tr><td colspan='4' style='color:#6b7280; font-size:12px; padding: 12px 0; text-align: center;'>Không gọi đồ ăn nước uống</td></tr>";
            }
            
            document.getElementById("bill-service-fee").textContent = Math.ceil(bill.service_total).toLocaleString("vi-VN") + " VNĐ";
            document.getElementById("bill-total-amount").textContent = Math.ceil(bill.total_bill).toLocaleString("vi-VN") + " VNĐ";
            
            currentBillToPrint = bill;
            var modalConfirmBtn = document.getElementById("bill-confirm-btn");
            if (modalConfirmBtn) {
                if (bill.is_preview) {
                    modalConfirmBtn.innerHTML = "Đóng";
                    modalConfirmBtn.style.background = "#4b5563";
                } else {
                    modalConfirmBtn.innerHTML = "🖨️ In & Hoàn tất";
                    modalConfirmBtn.style.background = "linear-gradient(135deg, #10b981, #059669)";
                }
            }

            document.getElementById("bill-modal").style.display = "flex";
            playAlert();
        }

        function updateBillItemQty(itemId, newQty, tableId) {
            if (newQty <= 0) {
                if (!confirm("Bạn có chắc muốn xóa món này khỏi hóa đơn?")) return;
            }
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/item/" + itemId + "/update", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                if (xhr.status === 200) {
                    loadTables(function() {
                        viewActiveBill(tableId);
                    });
                } else {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        swal("Lỗi", res.message || "Không thể cập nhật số lượng", "error");
                    } catch(e) {
                        swal("Lỗi", "Không thể cập nhật số lượng", "error");
                    }
                }
            };
            xhr.send(JSON.stringify({ quantity: newQty }));
        }

        function deleteBillItem(itemId, tableId, itemName) {
            if (!confirm("Bạn có chắc muốn xóa món '" + itemName + "' khỏi hóa đơn?")) return;
            var xhr = new XMLHttpRequest();
            xhr.open("DELETE", "/api/session/item/" + itemId, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    loadTables(function() {
                        viewActiveBill(tableId);
                    });
                } else {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        swal("Lỗi", res.message || "Không thể xóa món", "error");
                    } catch(e) {
                        swal("Lỗi", "Không thể xóa món", "error");
                    }
                }
            };
            xhr.send();
        }

        var currentBillToPrint = null;
        function printBill() {
            if (!currentBillToPrint) return;
            var bill = currentBillToPrint;
            var itemsHtml = "";
            if (bill.items && bill.items.length > 0) {
                bill.items.forEach(function(item) {
                    var itemName = item.item_name || item.name || "";
                    var itemPrice = item.price || (item.quantity ? item.total_price / item.quantity : 0);
                    itemsHtml += "<tr>" +
                        "<td>" + itemName + "</td>" +
                        "<td style='text-align:center;'>" + item.quantity + "</td>" +
                        "<td style='text-align:right;'>" + Math.ceil(itemPrice).toLocaleString("vi-VN") + "</td>" +
                        "<td style='text-align:right;'>" + Math.ceil(item.total_price).toLocaleString("vi-VN") + "</td>" +
                    "</tr>";
                });
            } else {
                itemsHtml = "<tr><td colspan='4' style='text-align:center;'>Không gọi dịch vụ</td></tr>";
            }
            
            var sTime = new Date(bill.start_time).toLocaleString('vi-VN');
            var eTime = bill.is_preview ? "--:--" : new Date(bill.end_time).toLocaleString('vi-VN');
            var printTime = new Date().toLocaleString('vi-VN');
            
            var html = "<html><head><title>In Hóa Đơn</title>" +
                "<style>" +
                "@media print { @page { margin: 0; } body { margin: 5mm; } }" +
                "body { font-family: 'Courier New', Courier, monospace; font-size: 13px; width: 300px; margin: 0 auto; color: black; background: white; }" +
                "h2 { text-align: center; margin: 0 0 5px 0; font-size: 20px; font-weight: bold; text-transform: uppercase; }" +
                ".header { text-align: center; margin-bottom: 15px; }" +
                ".header p { margin: 3px 0; font-size: 13px; }" +
                ".divider { border-bottom: 1px dashed #000; margin: 10px 0; }" +
                "table { width: 100%; border-collapse: collapse; margin-bottom: 10px; }" +
                "th { padding: 4px 0; border-bottom: 1px dashed #000; font-weight: bold; font-size: 12px; }" +
                "td { padding: 4px 0; font-size: 13px; border-bottom: 1px dashed #eee; }" +
                ".flex-row { display: flex; justify-content: space-between; margin-bottom: 4px; }" +
                ".total-row { display: flex; justify-content: space-between; font-weight: bold; font-size: 16px; margin-top: 5px; border-top: 1px solid #000; padding-top: 5px; }" +
                ".footer { text-align: center; margin-top: 15px; font-size: 12px; }" +
                ".footer p { margin: 3px 0; }" +
                "</style></head><body>" +
                "<div class='header'>" +
                "<h2>BIDA CLUB</h2>" +
                "<p>3xx Huỳnh Tấn Phát, Quận 7, HCM</p>" +
                "<p>SĐT: 0396 123 456</p>" +
                "<p>Mã hóa đơn: " + (bill.is_preview ? "Tạm Tính" : "HD-" + Date.now().toString().slice(-6)) + "</p>" +
                "</div>" +
                
                "<div class='divider'></div>" +
                "<div class='flex-row'><span>Bàn:</span> <strong>" + bill.table_name + "</strong></div>" +
                "<div class='flex-row'><span>Vào:</span> <span>" + sTime + "</span></div>" +
                "<div class='flex-row'><span>Ra:</span> <span>" + eTime + "</span></div>" +
                "<div class='flex-row'><span>Tổng thời gian:</span> <span>" + bill.total_minutes + " phút</span></div>" +
                "<div class='flex-row'><span>Đơn giá giờ:</span> <span>" + (bill.total_minutes > 0 ? Math.round((bill.play_fee / bill.total_minutes) * 60).toLocaleString("vi-VN") : "0") + " VNĐ</span></div>" +
                "<div class='divider'></div>" +
                
                "<table>" +
                "<tr><th style='text-align:left;'>Món</th><th style='text-align:center;'>SL</th><th style='text-align:right;'>Đ.Giá</th><th style='text-align:right;'>T.Tiền</th></tr>" +
                itemsHtml +
                "</table>" +
                
                "<div class='flex-row'><span>Tiền giờ chơi:</span> <span>" + Math.ceil(bill.play_fee).toLocaleString("vi-VN") + " VNĐ</span></div>" +
                "<div class='flex-row'><span>Tiền dịch vụ:</span> <span>" + Math.ceil(bill.service_total).toLocaleString("vi-VN") + " VNĐ</span></div>" +
                "<div class='total-row'><span>TỔNG CỘNG:</span> <span>" + Math.ceil(bill.total_bill).toLocaleString("vi-VN") + " VNĐ</span></div>" +
                
                "<div class='divider'></div>" +
                "<div class='flex-row' style='margin-bottom: 8px;'><span>Phương thức:</span> <span>Tiền mặt / CK</span></div>" +
                "<div class='flex-row'><span>SĐT Khách:</span> <span>...................</span></div>" +
                "<div class='flex-row'><span>Ghi chú:</span> <span>...................</span></div>" +
                "<div class='divider'></div>" +
                
                "<div style='text-align:center; margin-top: 10px;'>" +
                "<p style='font-size:12px; margin-bottom: 2px; font-weight:bold;'>Quét QR thanh toán</p>" +
                "<img src='https://img.vietqr.io/image/970436-0396123456-compact2.png?amount=" + Math.ceil(bill.total_bill) + "&accountName=BIDA CLUB' style='width: 120px; height: 120px;'/>" +
                "</div>" +
                
                "<div class='footer'>" +
                "<p><strong>WIFI: Bida club</strong></p>" +
                "<p>Pass: bidaclubxincamon</p>" +
                "<p>----------------------</p>" +
                "<p>Thu ngân: Admin</p>" +
                "<p>In lúc: " + printTime + "</p>" +
                "<p style='font-style: italic; margin-top: 8px; font-weight: bold;'>Cảm ơn quý khách!</p>" +
                "</div>" +
                "</div>" +
                "</body></html>";

            var iframe = document.getElementById("print-iframe");
            if (!iframe) {
                iframe = document.createElement("iframe");
                iframe.id = "print-iframe";
                iframe.style.position = "absolute";
                iframe.style.width = "0px";
                iframe.style.height = "0px";
                iframe.style.border = "none";
                document.body.appendChild(iframe);
            }
            var doc = iframe.contentWindow.document;
            doc.open();
            doc.write(html);
            doc.close();
            
            setTimeout(() => {
                iframe.contentWindow.focus();
                iframe.contentWindow.print();
            }, 500);
        }

        function closeBillModal() {
            document.getElementById("bill-modal").style.display = "none";
        }

        // === REPORT FUNCTIONS ===
        function openReportModal() {
            document.getElementById("report-modal").style.display = "flex";
            
            // Set default date to today
            var today = new Date().toISOString().split('T')[0];
            document.getElementById("report-start-date").value = today;
            document.getElementById("report-end-date").value = today;
        }

        function closeReportModal() {
            document.getElementById("report-modal").style.display = "none";
        }
        
        function downloadRevenueReport() {
            var startDate = document.getElementById("report-start-date").value;
            var endDate = document.getElementById("report-end-date").value;
            var url = "/api/reports/revenue";
            var params = [];
            if (startDate) params.push("start_date=" + startDate);
            if (endDate) params.push("end_date=" + endDate);
            
            if (params.length > 0) {
                url += "?" + params.join("&");
            }
            
            window.location.href = url;
            closeReportModal();
        }

        // === INVENTORY MANAGEMENT FUNCTIONS ===
        function openInventoryModal() {
            document.getElementById("inventory-modal").style.display = "flex";
            loadInventoryList();
        }

        function closeInventoryModal() {
            document.getElementById("inventory-modal").style.display = "none";
        }

        function loadInventoryList() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/products", true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var prods = JSON.parse(xhr.responseText);
                    var tbody = document.getElementById("inventory-items-body");
                    tbody.innerHTML = "";
                    
                    if (prods.length === 0) {
                        tbody.innerHTML = "<tr><td colspan='5' style='color:#6b7280; padding:12px; text-align:center;'>Chưa có sản phẩm nào</td></tr>";
                        return;
                    }
                    
                    prods.forEach(function(p) {
                        var tr = document.createElement("tr");
                        tr.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
                        tr.innerHTML = 
                            "<td style='padding: 10px 8px; font-weight:600; color:white;'>" + p.name + "</td>" +
                            "<td style='padding: 10px 8px; color:#a5b4fc;'>" + p.category + "</td>" +
                            "<td style='padding: 10px 8px;'><input type='text' id='prod-img-" + p.id + "' value='" + (p.image_url || '') + "' placeholder='Link ảnh...' style='width:90px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; padding:0 4px; font-size:11px; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; text-align:right;'><input type='number' id='prod-price-" + p.id + "' value='" + p.price + "' style='width:90px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:#86efac; text-align:right; padding-right:4px; font-weight:700; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; text-align:center;'><input type='number' id='prod-stock-" + p.id + "' value='" + p.stock + "' style='width:70px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; text-align:center; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; text-align:center; display:flex; justify-content:center; gap:6px;'>" +
                                "<button onclick='updateProduct(" + p.id + ")' style='background:#10b981; color:white; border:none; padding:4px 10px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:bold;'>Lưu</button>" +
                                "<button onclick='deleteProduct(" + p.id + ")' style='background:#ef4444; color:white; border:none; padding:4px 10px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:bold;'>Xóa</button>" +
                            "</td>";
                        tbody.appendChild(tr);
                    });
                }
            };
            xhr.send();
        }

        function addNewProduct() {
            var name = document.getElementById("new-prod-name").value.trim();
            var category = document.getElementById("new-prod-category").value;
            var price = parseFloat(document.getElementById("new-prod-price").value || 0);
            var stock = parseInt(document.getElementById("new-prod-stock").value || 0);
            var image_url = document.getElementById("new-prod-image").value.trim();
            
            if (!name) {
                alert("Vui lòng nhập tên sản phẩm!");
                return;
            }
            if (price < 1000) {
                alert("Đơn giá sản phẩm phải từ 1000 VNĐ trở lên!");
                return;
            }
            if (stock < 0) {
                alert("Số lượng tồn kho không được âm!");
                return;
            }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/products/add", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert(res.message);
                    document.getElementById("new-prod-name").value = "";
                    document.getElementById("new-prod-price").value = "";
                    document.getElementById("new-prod-stock").value = "";
                    loadInventoryList();
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send(JSON.stringify({ name: name, category: category, price: price, stock: stock, image_url: image_url }));
        }

        function updateProduct(id) {
            var price = parseFloat(document.getElementById("prod-price-" + id).value || 0);
            var stock = parseInt(document.getElementById("prod-stock-" + id).value || 0);
            var image_url = document.getElementById("prod-img-" + id).value.trim();
            
            if (price < 1000) {
                alert("Đơn giá sản phẩm phải từ 1000 VNĐ trở lên!");
                return;
            }
            if (stock < 0) {
                alert("Số lượng tồn kho không được âm!");
                return;
            }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/products/update", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert("Cập nhật thành công!");
                    loadInventoryList();
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send(JSON.stringify({ id: id, price: price, stock: stock, image_url: image_url }));
        }

        function deleteProduct(id) {
            if (!confirm("Bạn có chắc muốn xóa sản phẩm này khỏi thực đơn?")) return;
            
            var xhr = new XMLHttpRequest();
            xhr.open("DELETE", "/api/products/delete/" + id, true);
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert(res.message);
                    loadInventoryList();
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send();
        }

        function switchInventoryTab(tabName) {
            document.getElementById('tab-content-products').style.display = tabName === 'products' ? 'block' : 'none';
            document.getElementById('tab-content-tables').style.display = tabName === 'tables' ? 'block' : 'none';
            
            var btnProd = document.getElementById('tab-btn-products');
            var btnTables = document.getElementById('tab-btn-tables');
            
            if (tabName === 'products') {
                btnProd.style.background = '#6366f1';
                btnProd.style.color = 'white';
                btnTables.style.background = 'transparent';
                btnTables.style.color = '#9ca3af';
                loadInventoryList();
            } else {
                btnTables.style.background = '#6366f1';
                btnTables.style.color = 'white';
                btnProd.style.background = 'transparent';
                btnProd.style.color = '#9ca3af';
                loadAdminTables();
            }
        }

        function loadAdminTables() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/tables", true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var tables = JSON.parse(xhr.responseText);
                    var tbody = document.getElementById("inventory-tables-body");
                    if (!tbody) return;
                    tbody.innerHTML = "";
                    
                    if (tables.length === 0) {
                        tbody.innerHTML = "<tr><td colspan='6' style='color:#6b7280; padding:12px; text-align:center;'>Chưa có bàn bida nào</td></tr>";
                        return;
                    }
                    
                    tables.forEach(function(t) {
                        var tr = document.createElement("tr");
                        tr.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
                        tr.innerHTML = 
                            "<td style='padding: 10px 8px; font-weight:600; color:white;'><input type='text' id='adm-table-name-" + t.id + "' value='" + t.name + "' style='width:120px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; padding:0 6px; font-size:12px; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; color:#a5b4fc;'>" + 
                                "<select id='adm-table-type-" + t.id + "' style='height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; font-size:11px; outline:none;'>" +
                                    "<option value='LIP' " + (t.table_type === 'LIP' ? 'selected' : '') + ">Líp</option>" +
                                    "<option value='3C' " + (t.table_type === '3C' ? 'selected' : '') + ">3 Băng</option>" +
                                    "<option value='POOL' " + (t.table_type === 'POOL' ? 'selected' : '') + ">Lỗ</option>" +
                                "</select>" +
                            "</td>" +
                            "<td style='padding: 10px 8px;'>" +
                                "<select id='adm-table-tier-" + t.id + "' style='height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; font-size:11px; outline:none;'>" +
                                    "<option value='STANDARD' " + (t.table_tier === 'STANDARD' ? 'selected' : '') + ">Thường</option>" +
                                    "<option value='VIP' " + (t.table_tier === 'VIP' ? 'selected' : '') + ">VIP</option>" +
                                "</select>" +
                            "</td>" +
                            "<td style='padding: 10px 8px;'><input type='text' id='adm-table-cam-" + t.id + "' value='" + (t.camera_url || '') + "' placeholder='Cam ID' style='width:70px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:white; padding:0 4px; font-size:11px; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; text-align:right;'><input type='number' id='adm-table-price-" + t.id + "' value='" + t.price_per_hour + "' style='width:90px; height:28px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:4px; color:#86efac; text-align:right; padding-right:4px; font-weight:700; outline:none;'></td>" +
                            "<td style='padding: 10px 8px; text-align:center; display:flex; justify-content:center; gap:6px;'>" +
                                "<button onclick='updateAdminTable(" + t.id + ")' style='background:#10b981; color:white; border:none; padding:4px 10px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:bold;'>Lưu</button>" +
                                "<button onclick='deleteAdminTable(" + t.id + ")' style='background:#ef4444; color:white; border:none; padding:4px 10px; border-radius:4px; font-size:11px; cursor:pointer; font-weight:bold;'>Xóa</button>" +
                            "</td>";
                        tbody.appendChild(tr);
                    });
                }
            };
            xhr.send();
        }

        function addNewAdminTable() {
            var name = document.getElementById("new-table-name").value.trim();
            var type = document.getElementById("new-table-type").value;
            var tier = document.getElementById("new-table-tier").value;
            var price = parseFloat(document.getElementById("new-table-price").value || 50000);
            var cam = document.getElementById("new-table-cam").value.trim();
            
            if (!name) {
                alert("Vui lòng nhập tên bàn!");
                return;
            }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/admin/tables/add", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert(res.message);
                    document.getElementById("new-table-name").value = "";
                    document.getElementById("new-table-price").value = "";
                    document.getElementById("new-table-cam").value = "";
                    loadAdminTables();
                    loadTables(); // Reload main dashboard tables
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send(JSON.stringify({ name: name, table_type: type, table_tier: tier, price_per_hour: price, camera_url: cam }));
        }

        function updateAdminTable(id) {
            var name = document.getElementById("adm-table-name-" + id).value.trim();
            var type = document.getElementById("adm-table-type-" + id).value;
            var tier = document.getElementById("adm-table-tier-" + id).value;
            var price = parseFloat(document.getElementById("adm-table-price-" + id).value || 50000);
            var cam = document.getElementById("adm-table-cam-" + id).value.trim();
            
            if (!name) {
                alert("Tên bàn không được trống!");
                return;
            }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/admin/tables/update", true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert(res.message);
                    loadAdminTables();
                    loadTables(); // Reload main dashboard tables
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send(JSON.stringify({ id: id, name: name, table_type: type, table_tier: tier, price_per_hour: price, camera_url: cam }));
        }

        function deleteAdminTable(id) {
            if (!confirm("Bạn có chắc chắn muốn xóa bàn này khỏi hệ thống?")) return;
            
            var xhr = new XMLHttpRequest();
            xhr.open("DELETE", "/api/admin/tables/" + id, true);
            xhr.onload = function() {
                var res = JSON.parse(xhr.responseText);
                if (xhr.status === 200) {
                    alert(res.message);
                    loadAdminTables();
                    loadTables(); // Reload main dashboard tables
                } else {
                    alert("Lỗi: " + res.message);
                }
            };
            xhr.send();
        }

        function showTableQRModal(tableId, tableName, token) {
            var qrTitle = document.getElementById("qr-modal-title");
            var qrImg = document.getElementById("qr-modal-image");
            var qrLink = document.getElementById("qr-modal-link");
            var targetUrl = window.location.origin + "/menu/" + tableId + "/" + token;
            
            qrTitle.textContent = "📷 MÃ QR GỌI MÓN - " + tableName;
            qrLink.textContent = targetUrl;
            qrImg.src = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + encodeURIComponent(targetUrl);
            document.getElementById("qr-modal").style.display = "flex";
        }
        
        function closeQRModal() {
            document.getElementById("qr-modal").style.display = "none";
        }

        function approveCustomerOrder(card, tableId, items) {
            var btns = card.querySelectorAll("button");
            for (var i = 0; i < btns.length; i++) { btns[i].disabled = true; }
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/add-items/" + tableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var resolvedEl = document.createElement("div");
                    resolvedEl.className = "event-resolved resolved-confirmed";
                    resolvedEl.textContent = "Đã duyệt món & thêm vào Bill";
                    card.style.borderLeftColor = "#22c55e";
                    
                    var actionsDiv = card.querySelector(".event-actions");
                    if (actionsDiv) actionsDiv.style.display = "none";
                    card.appendChild(resolvedEl);
                    loadTables();
                } else {
                    alert("Lỗi duyệt món: " + xhr.statusText);
                    for (var i = 0; i < btns.length; i++) { btns[i].disabled = false; }
                }
            };
            xhr.send(JSON.stringify({ items: items }));
        }

        // === HANDLE ACTION ===
        function handleAction(card, action) {
            var btns = card.querySelectorAll("button");
            for (var i = 0; i < btns.length; i++) { btns[i].disabled = true; }

            var resolvedEl = document.createElement("div");
            resolvedEl.className = "event-resolved";

            if (action === "confirm") {
                resolvedEl.className += " resolved-confirmed";
                // Neu la event Khach Order thi ghi la Da phuc vu xong
                var badgeEl = card.querySelector(".event-badge");
                if (badgeEl && badgeEl.textContent === "KHÁCH ORDER") {
                    resolvedEl.textContent = "ĐÃ PHỤC VỤ XONG";
                } else {
                    resolvedEl.textContent = "DA XAC NHAN - Nhan vien dang phuc vu";
                }
                card.style.borderLeftColor = "#22c55e";
            } else {
                resolvedEl.className += " resolved-dismissed";
                resolvedEl.textContent = "DA BO QUA - Canh bao gia";
                card.style.opacity = "0.5";
            }

            var actionsDiv = card.querySelector(".event-actions");
            if (actionsDiv) actionsDiv.style.display = "none";
            card.appendChild(resolvedEl);
        }

        var lastEventId = "";

        // === RENDER EVENT ===
        function renderEvent(data) {
            if (!data || !data.event_type) return;
            // Bo qua cac tin nhan khach vay tay goi mon bang AI Camera
            if (data.event_type === "HAND_RAISED") return;
            // De-duplicate bang unique event ID de tranh spam polling
            if (data.id) {
                if (data.id === lastEventId) return;
                lastEventId = data.id;
            } else {
                if (data.image && data.image === lastImage) return;
                lastImage = data.image || "";
            }

            if (emptyState) { emptyState.style.display = "none"; }

            eventCount++;
            eventCountEl.textContent = eventCount;

            // Load lai du lieu ban khi co hoat dong tu AI
            loadTables();

            var card = document.createElement("div");
            card.className = "event-card";
            if (data.event_type === "HAND_RAISED") {
                card.className += " urgent";
            } else if (data.event_type === "CUSTOMER_ORDER") {
                card.style.borderLeftColor = "#f59e0b";
            }

            // Header
            var header = document.createElement("div");
            header.className = "event-header";

            var badge = document.createElement("span");
            badge.className = "event-badge";
            if (data.event_type === "HAND_RAISED") {
                badge.className += " badge-hand";
                badge.textContent = "KHACH VAY TAY";
            } else if (data.event_type === "CUSTOMER_ORDER") {
                badge.className += " badge-hand";
                badge.style.background = "#f59e0b";
                badge.textContent = "KHÁCH ORDER";
            } else if (data.event_type === "TABLE_EMPTY" || data.event_type === "TABLE_ACTIVE") {
                badge.style.display = "none";
            } else {
                badge.className += " badge-motion";
                badge.textContent = data.event_type;
            }

            var timeEl = document.createElement("span");
            timeEl.className = "event-time";
            timeEl.textContent = new Date().toLocaleTimeString();

            header.appendChild(badge);
            header.appendChild(timeEl);
            card.appendChild(header);

            // Message
            var msg = document.createElement("div");
            msg.className = "event-message";
            msg.textContent = data.message || ("Su kien: " + data.event_type + " tai Ban " + data.table_id);
            card.appendChild(msg);

            // Hien thi so dien thoai khach
            if (data.event_type === "CUSTOMER_ORDER" && data.phone) {
                var phoneDiv = document.createElement("div");
                phoneDiv.style.cssText = "margin-top: 4px; font-size: 13px; color: #86efac; font-weight: 700;";
                phoneDiv.innerHTML = "📞 SĐT khách: <span style='font-family: monospace;'>" + data.phone + "</span>";
                card.appendChild(phoneDiv);
            }

            // Ghi chu yeu cau cua khach
            if (data.event_type === "CUSTOMER_ORDER" && data.note) {
                var noteDiv = document.createElement("div");
                noteDiv.style.cssText = "margin-top: 6px; font-size: 13px; color: #fcd34d; font-weight: 600; padding: 6px 10px; background: rgba(245, 158, 11, 0.1); border-left: 3px solid #fbbf24; border-radius: 4px;";
                noteDiv.textContent = "📝 Ghi chú: " + data.note;
                card.appendChild(noteDiv);
            }

            // Customer Order items list inside card
            if (data.event_type === "CUSTOMER_ORDER" && data.items && data.items.length > 0) {
                var hasPaidItem = data.items.some(function(i) { return i.price > 0; });
                var listTitle = hasPaidItem ? "<b>Đồ khách đặt (Đã tự động thêm vào Bill):</b>" : "<b>Khách đã yêu cầu:</b>";
                var itemsDiv = document.createElement("div");
                itemsDiv.style.cssText = "margin: 10px 0; padding: 10px 14px; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; font-size: 13px; color: #e5e7eb;";
                var listHtml = listTitle + "<ul style='margin-left: 20px; margin-top: 4px; display: flex; flex-direction: column; gap: 4px;'>";
                data.items.forEach(function(item) {
                    if (item.price > 0) {
                        listHtml += "<li>" + item.item_name + " x" + item.quantity + " (" + Math.ceil(item.price * item.quantity).toLocaleString("vi-VN") + " đ)</li>";
                    } else {
                        listHtml += "<li style='color: #fbbf24;'>" + item.item_name + "</li>";
                    }
                });
                listHtml += "</ul>";
                itemsDiv.innerHTML = listHtml;
                card.appendChild(itemsDiv);
            }

            // Play statistics section in card
            if (data.date || data.play_time || data.total_fee) {
                var statsContainer = document.createElement("div");
                statsContainer.style.cssText = "margin-bottom: 14px; padding: 10px 14px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; font-size: 12px; color: #8b949e; line-height: 1.5; display: flex; flex-direction: column; gap: 4px;";
                
                if (data.date) {
                    statsContainer.innerHTML += "<div>Ngày tạo: <b style='color: white;'>" + data.date + "</b></div>";
                }
                if (data.play_time) {
                    statsContainer.innerHTML += "<div>Thời gian đã chơi: <b style='color: #fbbf24;'>" + data.play_time + "</b></div>";
                }
                if (data.total_fee) {
                    statsContainer.innerHTML += "<div>Tổng tiền chơi hiện tại: <b style='color: #22c55e;'>" + data.total_fee + "</b></div>";
                }
                card.appendChild(statsContainer);
            }

            // Image
            if (data.image) {
                var img = document.createElement("img");
                img.className = "event-image";
                img.src = data.image;
                img.alt = "AI Camera Capture";
                card.appendChild(img);
            }

            // Action buttons for both AI alerts and Customer Orders
            if (data.image || data.event_type === "CUSTOMER_ORDER") {
                var actions = document.createElement("div");
                actions.className = "event-actions";

                if (data.event_type === "CUSTOMER_ORDER") {
                    var isTransferRequest = false;
                    var requestedType = null;
                    if (data.items && data.items.length > 0) {
                        data.items.forEach(function(i) {
                            if (i.item_name && i.item_name.startsWith("Đổi sang bàn")) {
                                isTransferRequest = true;
                                if (i.item_name.includes("Líp")) requestedType = "LIP";
                                else if (i.item_name.includes("Băng")) requestedType = "3C";
                                else if (i.item_name.includes("Lỗ")) requestedType = "POOL";
                            }
                        });
                    }

                    if (isTransferRequest) {
                        var btnApprove = document.createElement("button");
                        btnApprove.className = "btn btn-confirm";
                        btnApprove.style.background = "linear-gradient(135deg, #10b981, #059669)";
                        btnApprove.style.flex = "1";
                        btnApprove.innerHTML = "&#10004; Xác nhận";
                        btnApprove.addEventListener("click", function() {
                            showTransferModal(data.table_id, requestedType);
                            handleAction(card, "confirm");
                        });

                        var btnReject = document.createElement("button");
                        btnReject.className = "btn btn-dismiss";
                        btnReject.style.flex = "1";
                        btnReject.innerHTML = "&#10008; Từ chối";
                        btnReject.addEventListener("click", function() {
                            showRejectTransferModal(data.table_id);
                            handleAction(card, "dismiss");
                        });

                        actions.appendChild(btnApprove);
                        actions.appendChild(btnReject);
                    } else {
                        var btnApprove = document.createElement("button");
                        btnApprove.className = "btn btn-confirm";
                        btnApprove.style.background = "linear-gradient(135deg, #10b981, #059669)";
                        btnApprove.style.flex = "1";
                        btnApprove.innerHTML = "&#10004; Xác nhận đã phục vụ";
                        btnApprove.addEventListener("click", function() {
                            handleAction(card, "confirm");
                        });
                        actions.appendChild(btnApprove);
                    }
                } else {
                    var btnConfirm = document.createElement("button");
                    btnConfirm.className = "btn btn-confirm";
                    btnConfirm.innerHTML = "&#10004; Chay ra phuc vu";
                    btnConfirm.addEventListener("click", function() {
                        handleAction(card, "confirm");
                    });

                    var btnDismiss = document.createElement("button");
                    btnDismiss.className = "btn btn-dismiss";
                    btnDismiss.innerHTML = "&#10006; Bo qua (Bao gia)";
                    btnDismiss.addEventListener("click", function() {
                        handleAction(card, "dismiss");
                    });

                    actions.appendChild(btnConfirm);
                    actions.appendChild(btnDismiss);
                }

                actions.style.cssText = "display: flex; gap: 8px; margin-top: 10px;";
                card.appendChild(actions);
                if (data.event_type === "CUSTOMER_ORDER") {
                    playOrderAlert();
                } else {
                    playAlert();
                }
            }

            eventsDiv.insertBefore(card, eventsDiv.firstChild);
        }

        // === POLLING ===
        function pollServer() {
            pollCount++;
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/poll?_=" + Date.now(), true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    statusDot.className = "dot dot-green";
                    statusLabel.textContent = "Dang hoat dong";
                    statusBanner.className = "status-banner status-connected";
                    bannerIcon.innerHTML = "&#9889;";
                    bannerText.textContent = "He thong dang hoat dong - AI Camera dang giam sat (Poll #" + pollCount + ")";

                    try {
                        var data = JSON.parse(xhr.responseText);
                        if (data && data.event_type) {
                            renderEvent(data);
                        }
                    } catch(e) {}
                } else {
                    statusDot.className = "dot dot-red";
                    statusLabel.textContent = "Loi ket noi";
                    statusBanner.className = "status-banner status-error";
                    bannerIcon.innerHTML = "&#9888;";
                    bannerText.textContent = "Loi HTTP " + xhr.status + " - Khong the ket noi toi Server";
                }
            };
            xhr.onerror = function() {
                statusDot.className = "dot dot-red";
                statusLabel.textContent = "Mat ket noi";
                statusBanner.className = "status-banner status-error";
                bannerIcon.innerHTML = "&#9888;";
                bannerText.textContent = "Khong the ket noi toi Server. Hay tai lai trang.";
            };
            xhr.send();
        }

        setInterval(pollServer, 2000);
        pollServer();

        // === HIGHLIGHT CLIP FUNCTIONS ===
        var clipStatusDiv = document.getElementById("clip-status");
        var clipBtn = document.getElementById("clip-btn");
        var clipsListDiv = document.getElementById("clips-list");
        var timeInput = document.getElementById("time-input");
        var pastClipBtn = document.getElementById("past-clip-btn");

        // Dien gio hien tai lam goi y cho Time Machine
        var now = new Date();
        var currentHours = now.getHours();
        var currentMinutes = now.getMinutes();
        timeInput.value = (currentHours < 10 ? "0" + currentHours : currentHours) + ":" + (currentMinutes < 10 ? "0" + currentMinutes : currentMinutes);

        function requestClip(tableId) {
            clipBtn.disabled = true;
            clipBtn.textContent = "Dang xu ly...";
            clipStatusDiv.style.display = "block";
            clipStatusDiv.className = "highlight-status highlight-processing";
            clipStatusDiv.textContent = "AI dang cat 30 giay gan nhat thanh video... Vui long doi 5-10 giay.";

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/clip/" + tableId, true);
            xhr.onload = function() {
                var checkCount = 0;
                var checkInterval = setInterval(function() {
                    checkCount++;
                    var xhr2 = new XMLHttpRequest();
                    xhr2.open("GET", "/api/clip-status/" + tableId + "?_=" + Date.now(), true);
                    xhr2.onload = function() {
                        if (xhr2.status === 200) {
                            var result = JSON.parse(xhr2.responseText);
                            if (result.status === "ready") {
                                clearInterval(checkInterval);
                                clipStatusDiv.className = "highlight-status highlight-ready";
                                clipStatusDiv.innerHTML = "";

                                var readyText = document.createElement("span");
                                readyText.textContent = "Clip 30s da san sang! ";
                                clipStatusDiv.appendChild(readyText);

                                var downloadLink = document.createElement("a");
                                downloadLink.href = result.url;
                                downloadLink.download = result.filename;
                                downloadLink.className = "btn btn-download";
                                downloadLink.style.display = "inline-flex";
                                downloadLink.style.marginLeft = "10px";
                                downloadLink.style.padding = "6px 14px";
                                downloadLink.style.fontSize = "12px";
                                downloadLink.innerHTML = "&#11015; Tai ve MP4";
                                clipStatusDiv.appendChild(downloadLink);

                                clipBtn.disabled = false;
                                clipBtn.innerHTML = "🎥 Highlight 30s bàn đã chọn";
                                loadClips();
                                playAlert();
                            }
                        }
                    };
                    xhr2.send();

                    if (checkCount > 30) {
                        clearInterval(checkInterval);
                        clipStatusDiv.className = "highlight-status highlight-processing";
                        clipStatusDiv.textContent = "Qua lau - Hay thu lai.";
                        clipBtn.disabled = false;
                        clipBtn.innerHTML = "🎥 Highlight 30s bàn đã chọn";
                    }
                }, 1000);
            };
            xhr.send();
        }

        // Trich xuat clip tu Time Machine trong qua khu
        function requestPastClip(tableId) {
            var selectedTime = timeInput.value;
            if (!selectedTime) {
                alert("Vui long chon thoi gian can lay highlight!");
                return;
            }

            pastClipBtn.disabled = true;
            pastClipBtn.textContent = "Dang lay...";
            clipStatusDiv.style.display = "block";
            clipStatusDiv.className = "highlight-status highlight-processing";
            clipStatusDiv.textContent = "Co may thoi gian dang tim kiem va trich xuat video luc " + selectedTime + "...";

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/highlight-past/" + tableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                pastClipBtn.disabled = false;
                pastClipBtn.innerHTML = "⌛ Trích xuất clip";

                if (xhr.status === 200) {
                    var result = JSON.parse(xhr.responseText);
                    clipStatusDiv.className = "highlight-status highlight-ready";
                    clipStatusDiv.innerHTML = "";

                    var readyText = document.createElement("span");
                    readyText.textContent = "Highlight luc " + selectedTime + " da san sang! ";
                    clipStatusDiv.appendChild(readyText);

                    var downloadLink = document.createElement("a");
                    downloadLink.href = result.url;
                    downloadLink.download = result.filename;
                    downloadLink.className = "btn btn-download";
                    downloadLink.style.display = "inline-flex";
                    downloadLink.style.marginLeft = "10px";
                    downloadLink.style.padding = "6px 14px";
                    downloadLink.style.fontSize = "12px";
                    downloadLink.innerHTML = "&#11015; Tai video " + selectedTime;
                    clipStatusDiv.appendChild(downloadLink);

                    loadClips();
                    playAlert();
                } else {
                    var errorMsg = "Khong tim thay video luu tru cho thoi gian nay!";
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res && res.message) errorMsg = res.message;
                    } catch(e) {}
                    
                    clipStatusDiv.className = "highlight-status highlight-processing";
                    clipStatusDiv.style.background = "rgba(239,68,68,0.15)";
                    clipStatusDiv.style.borderColor = "rgba(239,68,68,0.3)";
                    clipStatusDiv.style.color = "#fca5a5";
                    clipStatusDiv.textContent = "❌ " + errorMsg;
                }
            };
            xhr.onerror = function() {
                pastClipBtn.disabled = false;
                pastClipBtn.innerHTML = "⌛ Trích xuất clip";
                clipStatusDiv.className = "highlight-status highlight-processing";
                clipStatusDiv.textContent = "Loi ket noi toi Server.";
            };
            xhr.send(JSON.stringify({ "time": selectedTime }));
        }

        // Xoa clip highlight
        function deleteClip(filename) {
            var xhr = new XMLHttpRequest();
            xhr.open("DELETE", "/api/clip/" + filename, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    loadClips();
                } else {
                    alert("Khong the xoa clip!");
                }
            };
            xhr.send();
        }

        function loadClips() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/clips?_=" + Date.now(), true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var clips = JSON.parse(xhr.responseText);
                    clipsListDiv.innerHTML = "";
                    if (clips.length === 0) return;

                    var title = document.createElement("div");
                    title.style.cssText = "font-size:12px; font-weight:600; color:#8b949e; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;";
                    title.textContent = "Clip da luu";
                    clipsListDiv.appendChild(title);

                    for (var i = 0; i < clips.length && i < 5; i++) {
                        var item = document.createElement("div");
                        item.className = "clip-item";

                        var nameSpan = document.createElement("span");
                        nameSpan.className = "clip-item-name";
                        nameSpan.textContent = clips[i].filename;
                        item.appendChild(nameSpan);

                        var rightDiv = document.createElement("div");
                        rightDiv.style.display = "flex";
                        rightDiv.style.alignItems = "center";
                        rightDiv.style.gap = "10px";

                        var sizeSpan = document.createElement("span");
                        sizeSpan.className = "clip-item-size";
                        sizeSpan.textContent = clips[i].size_mb + " MB";
                        rightDiv.appendChild(sizeSpan);

                        // Nut download
                        var dlBtn = document.createElement("a");
                        dlBtn.href = clips[i].url;
                        dlBtn.download = clips[i].filename;
                        dlBtn.className = "btn btn-download";
                        dlBtn.style.padding = "4px 12px";
                        dlBtn.style.fontSize = "11px";
                        dlBtn.style.borderRadius = "6px";
                        dlBtn.innerHTML = "&#11015; Tai";
                        rightDiv.appendChild(dlBtn);

                        // Nut xoa clip
                        var delBtn = document.createElement("button");
                        delBtn.className = "btn btn-dismiss";
                        delBtn.style.padding = "4px 12px";
                        delBtn.style.fontSize = "11px";
                        delBtn.style.borderRadius = "6px";
                        delBtn.style.marginLeft = "2px";
                        delBtn.innerHTML = "&#128465; Xoa";
                        delBtn.setAttribute("data-filename", clips[i].filename);
                        delBtn.addEventListener("click", function() {
                            var fname = this.getAttribute("data-filename");
                            if (confirm("Ban co chac muon xoa clip: " + fname + "?")) {
                                deleteClip(fname);
                            }
                        });
                        rightDiv.appendChild(delBtn);

                        item.appendChild(rightDiv);
                        clipsListDiv.appendChild(item);
                    }
                }
            };
            xhr.send();
        }

        // === POS MODAL LOGIC ===
        var posProducts = [];
        var posCart = {}; // { id: { name, price, qty, img } }
        var posCurrentTableId = null;

        function openPosModal(tableId, tableName) {
            posCurrentTableId = tableId;
            document.getElementById("pos-title").textContent = "🛒 Thu Ngân Gọi Món - Bàn " + tableName;
            document.getElementById("pos-modal").style.display = "flex";
            posCart = {};
            renderPosCart();
            
            if (posProducts.length === 0) {
                fetchPosProducts();
            } else {
                renderPosCategories();
            }
        }

        function closePosModal() {
            document.getElementById("pos-modal").style.display = "none";
        }

        function fetchPosProducts() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/products", true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    posProducts = JSON.parse(xhr.responseText);
                    
                    // Thêm một số dịch vụ mặc định vào cuối danh sách sản phẩm
                    posProducts.push({id: "svc_lo", name: "Lấy lơ", category: "Yêu cầu nghiệp vụ", price: 0, image_url: ""});
                    posProducts.push({id: "svc_xep", name: "Xếp bi", category: "Yêu cầu nghiệp vụ", price: 0, image_url: ""});
                    posProducts.push({id: "svc_quet", name: "Quét bàn", category: "Yêu cầu nghiệp vụ", price: 0, image_url: ""});
                    
                    renderPosCategories();
                }
            };
            xhr.send();
        }

        function renderPosCategories() {
            var catContainer = document.getElementById("pos-categories");
            catContainer.innerHTML = "";
            
            var categories = ["Tất cả"];
            posProducts.forEach(function(p) {
                if (p.category && categories.indexOf(p.category) === -1) {
                    categories.push(p.category);
                }
            });
            
            categories.forEach(function(cat, index) {
                var btn = document.createElement("button");
                btn.className = "cat-btn" + (index === 0 ? " active" : "");
                btn.style.cssText = "padding: 8px 16px; border-radius: 8px; border: none; background: " + (index === 0 ? "#10b981" : "rgba(255,255,255,0.1)") + "; color: white; cursor: pointer; white-space: nowrap; font-weight: bold;";
                btn.textContent = cat;
                btn.onclick = function() {
                    var btns = catContainer.querySelectorAll("button");
                    for (var i = 0; i < btns.length; i++) {
                        btns[i].style.background = "rgba(255,255,255,0.1)";
                    }
                    btn.style.background = "#10b981";
                    renderPosProducts(cat);
                };
                catContainer.appendChild(btn);
            });
            
            renderPosProducts("Tất cả");
        }

        function renderPosProducts(category) {
            var prodContainer = document.getElementById("pos-products");
            prodContainer.innerHTML = "";
            
            posProducts.forEach(function(p) {
                if (category !== "Tất cả" && p.category !== category) return;
                
                var card = document.createElement("div");
                card.style.cssText = "background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; cursor: pointer; display: flex; flex-direction: column; gap: 8px; transition: transform 0.2s, background 0.2s;";
                card.onmouseover = function() { this.style.transform = "translateY(-2px)"; this.style.background = "rgba(255,255,255,0.08)"; };
                card.onmouseout = function() { this.style.transform = "translateY(0)"; this.style.background = "rgba(255,255,255,0.05)"; };
                card.onclick = function() { addToPosCart(p); };
                
                var imgHtml = p.image_url ? "<img src='" + p.image_url + "' onerror='this.style.display=\"none\"' style='width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 8px;'>" : "<div style='width: 100%; aspect-ratio: 1; background: rgba(0,0,0,0.3); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: rgba(255,255,255,0.2);'>🍸</div>";
                
                card.innerHTML = imgHtml + 
                    "<div style='font-weight: 600; font-size: 14px; color: white; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;'>" + p.name + "</div>" +
                    "<div style='color: #34d399; font-weight: bold; font-size: 13px;'>" + p.price.toLocaleString("vi-VN") + "đ</div>";
                    
                prodContainer.appendChild(card);
            });
        }

        function addToPosCart(p) {
            if (posCart[p.id]) {
                posCart[p.id].qty += 1;
            } else {
                posCart[p.id] = { id: p.id, name: p.name, price: p.price, qty: 1 };
            }
            renderPosCart();
        }

        window.updatePosCartQty = function(id, delta) {
            if (posCart[id]) {
                posCart[id].qty += delta;
                if (posCart[id].qty <= 0) {
                    delete posCart[id];
                }
                renderPosCart();
            }
        };

        function renderPosCart() {
            var cartContainer = document.getElementById("pos-cart-items");
            cartContainer.innerHTML = "";
            var total = 0;
            var hasItems = false;
            
            var keys = Object.keys(posCart);
            for (var i = 0; i < keys.length; i++) {
                hasItems = true;
                var item = posCart[keys[i]];
                var itemTotal = item.price * item.qty;
                total += itemTotal;
                
                var row = document.createElement("div");
                row.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px;";
                
                row.innerHTML = 
                    "<div style='flex: 1; display: flex; flex-direction: column; gap: 4px;'>" +
                        "<div style='font-weight: bold; font-size: 13px; color: white;'>" + item.name + "</div>" +
                        "<div style='color: #9ca3af; font-size: 12px;'>" + item.price.toLocaleString("vi-VN") + "đ</div>" +
                    "</div>" +
                    "<div style='display: flex; align-items: center; gap: 8px; background: rgba(255,255,255,0.1); border-radius: 6px; padding: 2px;'>" +
                        "<button onclick='updatePosCartQty(\"" + item.id + "\", -1)' style='background: transparent; border: none; color: white; width: 24px; height: 24px; cursor: pointer; font-weight: bold;'>-</button>" +
                        "<span style='font-weight: bold; font-size: 13px; min-width: 16px; text-align: center; color: white;'>" + item.qty + "</span>" +
                        "<button onclick='updatePosCartQty(\"" + item.id + "\", 1)' style='background: transparent; border: none; color: white; width: 24px; height: 24px; cursor: pointer; font-weight: bold;'>+</button>" +
                    "</div>";
                    
                cartContainer.appendChild(row);
            }
            
            if (!hasItems) {
                cartContainer.innerHTML = "<div style='text-align: center; color: #6b7280; font-style: italic; margin-top: 20px;'>Chưa có món nào</div>";
            }
            
            document.getElementById("pos-total-price").textContent = total.toLocaleString("vi-VN") + "đ";
        }

        function submitPosOrder() {
            var itemsList = [];
            var keys = Object.keys(posCart);
            for (var i = 0; i < keys.length; i++) {
                var item = posCart[keys[i]];
                itemsList.push({ name: item.name, qty: item.qty, price: item.price });
            }
            
            if (itemsList.length === 0) {
                alert("Giỏ hàng trống!");
                return;
            }
            
            var btn = document.getElementById("pos-submit-btn");
            btn.textContent = "Đang gửi...";
            btn.disabled = true;
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/add-items/" + posCurrentTableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                btn.textContent = "Xác nhận thêm vào Bàn";
                btn.disabled = false;
                if (xhr.status === 200) {
                    closePosModal();
                    loadTables(); // Refresh dashboard
                } else {
                    var errMsg = "Lỗi khi gọi món!";
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res && res.message) errMsg = res.message;
                    } catch(e) {}
                    alert(errMsg);
                }
            };
            xhr.send(JSON.stringify({ items: itemsList }));
        }

        // Load ban dau
        loadClips();
        loadTables();
        
        // Polling trang thai ban moi 3s de cap nhat thoi gian choi lien tuc
        setInterval(loadTables, 3000);
    