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