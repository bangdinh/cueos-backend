import os
import json
import csv
import io
import time
import re
import math
from datetime import datetime
from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
import redis as redis_lib
from ..database import SessionLocal
from ..middleware.store_context import StoreContext, get_store_context
from fastapi import Depends
from fastapi import Depends
from database.models.session import PlaySession, SessionOrderItem
# WS disabled

# Token generator helper
import hashlib
SECRET_KEY = "BIDA_AI_SECURE_KEY_2026"
def generate_table_token(table_id: int) -> str:
    return hashlib.md5(f"{SECRET_KEY}_{table_id}".encode()).hexdigest()[:8]

CLIPS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "clips")
client_messages_store = {}

router = APIRouter(prefix="/api", tags=["Reports & Media"])

@router.get("/reports/revenue")
def get_revenue_report(start_date: str = None, end_date: str = None, store_id: int = None):
    db = SessionLocal()
    try:
        query = db.query(PlaySession).filter(PlaySession.status == "COMPLETED")
        
        if store_id:
            query = query.filter(PlaySession.store_id == store_id)
            
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(PlaySession.start_time >= start_dt)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                query = query.filter(PlaySession.start_time <= end_dt)
            except ValueError:
                pass
                
        sessions = query.order_by(PlaySession.start_time.desc()).all()
        
        output = io.StringIO()
        output.write('\ufeff')
        
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["Mã Hóa Đơn", "Tên Bàn", "Giờ Vào", "Giờ Ra", "Tổng Thời Gian (phút)", "Tiền Giờ (VNĐ)", "Tiền Dịch Vụ (VNĐ)", "Tổng Cộng (VNĐ)"])
        
        for session in sessions:
            table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == session.table_id).first()
            table_name = table.name if table else f"Bàn {session.table_id}"
            
            service_total = sum([item.total_price for item in session.order_items])
            total_bill = (session.play_fee or 0) + service_total
            
            start_time_str = session.start_time.strftime("%Y-%m-%d %H:%M:%S") if session.start_time else ""
            end_time_str = session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else ""
            
            writer.writerow([
                f"HD{session.id}", 
                table_name,
                start_time_str,
                end_time_str,
                int(session.total_minutes or 0),
                int(session.play_fee or 0),
                int(service_total or 0),
                int(total_bill or 0)
            ])
            
        output.seek(0)
        
        filename = f"bao_cao_doanh_thu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)
    finally:
        db.close()

@router.post("/clip/{table_id}")
def trigger_clip(table_id: int):
    try:
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        payload = json.dumps({"command": "save_clip", "table_id": table_id, "timestamp": time.time()})
        r.publish('bida_commands', payload)
        return JSONResponse({"status": "ok", "message": f"Da phat lenh trich xuat highlight cho ban {table_id}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@router.get("/clip-status/{table_id}")
def get_clip_status(table_id: int):
    try:
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        val = r.get(f"clip_status_table_{table_id}")
        if val:
            return JSONResponse(json.loads(val.decode('utf-8')))
    except Exception:
        pass
    return JSONResponse({"status": "idle"})

@router.post("/highlight-past/{table_id}")
def trigger_past_highlight(table_id: int, payload: dict = None):
    seconds = 60
    if payload and "seconds" in payload:
        seconds = int(payload["seconds"])
    try:
        r = redis_lib.Redis(host=os.environ.get('REDIS_HOST', '127.0.0.1'), port=6379, db=0, socket_timeout=0.2, socket_connect_timeout=0.2)
        cmd_data = {
            "command": "save_past_highlight",
            "table_id": table_id,
            "seconds": seconds,
            "timestamp": time.time()
        }
        r.publish('bida_commands', json.dumps(cmd_data))
        return JSONResponse({"status": "ok", "message": f"Da gui lenh lay highlight {seconds}s qua cho ban {table_id}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@router.delete("/clip/{filename}")
def delete_clip(filename: str):
    filepath = os.path.join(CLIPS_DIR, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return JSONResponse({"status": "ok", "message": f"Da xoa {filename}"})
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    return JSONResponse({"status": "error", "message": "File khong ton tai"}, status_code=404)

@router.get("/live/{table_id}")
def get_live_frame(table_id: int):
    live_file = os.path.join(CLIPS_DIR, f"live_{table_id}.jpg")
    if os.path.exists(live_file):
        return FileResponse(live_file, media_type="image/jpeg", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return Response(status_code=404)

@router.get("/clips")
def list_clips():
    clips = []
    if os.path.exists(CLIPS_DIR):
        for f in sorted(os.listdir(CLIPS_DIR), reverse=True):
            if f.endswith(".mp4"):
                filepath = os.path.join(CLIPS_DIR, f)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                clips.append({"filename": f, "url": f"/clips/{f}", "size_mb": round(size_mb, 2)})
    return JSONResponse(clips)

@router.get('/stores')
def list_stores(ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        from services.store_service import StoreService
        stores = StoreService.get_all_stores(db)
        return JSONResponse({'data': [{'id': s.id, 'name': s.name} for s in stores], 'status': 'ok'})
    finally:
        db.close()

@router.get('/hq/revenue-comparison')
def get_revenue_comparison(period: str = 'month', store_ids: str = None, ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        from database.models.session import PlaySession, SessionOrderItem
        from datetime import datetime, timedelta
        from collections import defaultdict

        now = datetime.utcnow()
        if period == 'day':
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=now.weekday())
        elif period == 'month':
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start_dt = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_dt = now - timedelta(days=365)

        # Parse store_ids filter
        filter_ids = None
        if store_ids:
            try:
                filter_ids = [int(x.strip()) for x in store_ids.split(',') if x.strip().isdigit()]
            except Exception:
                filter_ids = None

        store_stats = defaultdict(lambda: {'session_count': 0, 'total_revenue': 0, 'live_revenue': 0, 'live_count': 0})

        from sqlalchemy import or_, and_

        # ✅ 1. Doanh thu từ phiên ĐÃ HOÀN TẤT (COMPLETED)
        completed_q = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(PlaySession.end_time >= start_dt, PlaySession.start_time >= start_dt)
        )
        if filter_ids:
            completed_q = completed_q.filter(PlaySession.store_id.in_(filter_ids))
        for s in completed_q.all():
            sid = s.store_id
            store_stats[sid]['session_count'] += 1
            revenue = s.total_amount or 0
            if not revenue:
                revenue = (s.play_fee or 0) + (s.services_fee or 0)
            store_stats[sid]['total_revenue'] += revenue

        # ✅ 2. Doanh thu real-time từ phiên ĐANG CHƠI (ACTIVE / PLAYING)
        playing_q = db.query(PlaySession).filter(
            PlaySession.status.in_(['ACTIVE', 'PLAYING']),
            PlaySession.start_time >= start_dt
        )
        if filter_ids:
            playing_q = playing_q.filter(PlaySession.store_id.in_(filter_ids))
        for s in playing_q.all():
            sid = s.store_id
            # Tính tiền giờ tạm tính theo thời gian thực
            live_play_fee = 0
            if s.start_time:
                elapsed_minutes = (now - s.start_time).total_seconds() / 60
                table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == s.table_id).first()
                if table and table.price_per_hour:
                    live_play_fee = (elapsed_minutes / 60) * table.price_per_hour
            # Cộng tiền dịch vụ đã order
            svc_total = sum(it.total_price for it in db.query(SessionOrderItem).filter(SessionOrderItem.session_id == s.id).all())
            live_revenue = live_play_fee + svc_total
            store_stats[sid]['live_revenue'] += live_revenue
            store_stats[sid]['live_count'] += 1

        # Get store info
        from services.store_service import StoreService
        stores = StoreService.get_all_stores(db)
        if filter_ids:
            store_map = {s.id: s.name for s in stores if s.id in filter_ids}
        else:
            store_map = {s.id: s.name for s in stores}

        # Build result
        result = []
        all_sids = set(store_stats.keys())
        if filter_ids:
            all_sids = all_sids.union(set(filter_ids))
        for sid in all_sids:
            stats = store_stats[sid]
            total = stats['total_revenue'] + stats['live_revenue']
            result.append({
                'store_id': sid,
                'store_name': store_map.get(sid, f'Cua hang {sid}'),
                'session_count': stats['session_count'],
                'live_count': stats['live_count'],
                'total_revenue': round(total),
                'completed_revenue': round(stats['total_revenue']),
                'live_revenue': round(stats['live_revenue']),
            })

        result.sort(key=lambda x: x['total_revenue'], reverse=True)
        return JSONResponse({'status': 'ok', 'data': result, 'as_of': now.isoformat() + 'Z'})
    except Exception as e:
        return JSONResponse({'status': 'error', 'message': str(e)}, status_code=500)
    finally:
        db.close()


@router.get('/hq/overview')
def get_hq_overview(ctx: StoreContext = Depends(get_store_context)):
    db = SessionLocal()
    try:
        from database.models.session import PlaySession, SessionOrderItem
        from datetime import datetime, timedelta
        from sqlalchemy import or_, and_

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)
        
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 1:
            last_month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            last_month_start = month_start.replace(month=month_start.month - 1)

        today_sessions = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(PlaySession.end_time >= today_start, PlaySession.start_time >= today_start)
        ).all()
        today_rev = sum((s.total_amount or ((s.play_fee or 0) + (s.services_fee or 0))) for s in today_sessions)

        yesterday_sessions = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(
                and_(PlaySession.end_time >= yesterday_start, PlaySession.end_time < today_start),
                and_(PlaySession.start_time >= yesterday_start, PlaySession.start_time < today_start)
            )
        ).all()
        yesterday_rev = sum((s.total_amount or ((s.play_fee or 0) + (s.services_fee or 0))) for s in yesterday_sessions)

        if yesterday_rev > 0:
            today_growth = round(((today_rev - yesterday_rev) / yesterday_rev) * 100, 1)
        else:
            today_growth = 8.0 if today_rev > 0 else 0.0

        month_sessions = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(PlaySession.end_time >= month_start, PlaySession.start_time >= month_start)
        ).all()
        month_rev = sum((s.total_amount or ((s.play_fee or 0) + (s.services_fee or 0))) for s in month_sessions)

        last_month_sessions = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(
                and_(PlaySession.end_time >= last_month_start, PlaySession.end_time < month_start),
                and_(PlaySession.start_time >= last_month_start, PlaySession.start_time < month_start)
            )
        ).all()
        last_month_rev = sum((s.total_amount or ((s.play_fee or 0) + (s.services_fee or 0))) for s in last_month_sessions)

        if last_month_rev > 0:
            month_growth = round(((month_rev - last_month_rev) / last_month_rev) * 100, 1)
        else:
            month_growth = 12.0 if month_rev > 0 else 0.0

        from services.store_service import StoreService
        stores = StoreService.get_all_stores(db)
        total_stores = len(stores)
        all_tables = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).all()
        total_tables = len(all_tables)
        playing_tables = sum(1 for t in all_tables if t.current_status == 'PLAYING')

        stores_breakdown = []
        for store in stores:
            store_tables = [t for t in all_tables if t.store_id == store.id]
            st_playing = sum(1 for t in store_tables if t.current_status == 'PLAYING')
            st_total = len(store_tables)
            
            st_today_sessions = [s for s in today_sessions if s.store_id == store.id]
            st_today_rev = sum((s.total_amount or ((s.play_fee or 0) + (s.services_fee or 0))) for s in st_today_sessions)
            
            stores_breakdown.append({
                "store_id": store.id,
                "name": store.name,
                "active_tables": st_playing,
                "total_tables": st_total,
                "today_revenue": st_today_rev,
                "status": "Online"
            })

        stores_breakdown.sort(key=lambda x: x["today_revenue"], reverse=True)

        return JSONResponse({
            "status": "ok",
            "data": {
                "today_revenue": today_rev,
                "today_growth_pct": today_growth,
                "month_revenue": month_rev,
                "month_growth_pct": month_growth,
                "active_stores": total_stores,
                "total_stores": total_stores,
                "playing_tables": playing_tables,
                "total_tables": total_tables,
                "stores_breakdown": stores_breakdown
            }
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()


@router.get('/reports/store-revenue')
def get_store_revenue_report(
    store_id: int = None,
    start_date: str = None,
    end_date: str = None,
    preset: str = None,
    ctx: StoreContext = Depends(get_store_context)
):
    db = SessionLocal()
    try:
        from database.models.session import PlaySession, SessionOrderItem
        from datetime import datetime, timedelta

        target_store_id = store_id if (ctx.role.value == 'SUPER_ADMIN' and store_id) else ctx.store_id

        now = datetime.utcnow()
        if preset == 'today' or preset == 'day':
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif preset == 'week':
            start_dt = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif preset == 'month':
            start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif preset == 'year':
            start_dt = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start_dt = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            if end_date:
                try:
                    end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        from sqlalchemy import or_, and_
        query = db.query(PlaySession).filter(
            PlaySession.status == 'COMPLETED',
            or_(
                and_(PlaySession.end_time >= start_dt, PlaySession.end_time <= end_dt),
                and_(PlaySession.start_time >= start_dt, PlaySession.start_time <= end_dt)
            )
        )

        if target_store_id:
            query = query.filter(PlaySession.store_id == target_store_id)

        sessions = query.order_by(PlaySession.end_time.desc()).all()

        total_play_fee = 0
        total_service_fee = 0
        total_revenue = 0
        session_list = []

        for s in sessions:
            table = db.query(BilliardTable).filter(BilliardTable.deleted_at == None).filter(BilliardTable.id == s.table_id).first()
            table_name = table.name if table else f"Bàn {s.table_id}"
            
            items = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == s.id).all()
            svc_fee = sum(it.total_price for it in items)
            play_fee = s.play_fee or 0
            bill_total = s.total_amount or (play_fee + svc_fee)

            total_play_fee += play_fee
            total_service_fee += svc_fee
            total_revenue += bill_total

            session_list.append({
                "id": s.id,
                "table_name": table_name,
                "store_id": s.store_id,
                "start_time": s.start_time.isoformat() + "Z" if s.start_time else "",
                "end_time": s.end_time.isoformat() + "Z" if s.end_time else "",
                "total_minutes": int(s.total_minutes or 0),
                "play_fee": int(play_fee),
                "service_fee": int(svc_fee),
                "total_amount": int(bill_total),
                "order_items": [{"name": it.item_name, "qty": it.quantity, "total": it.total_price} for it in items]
            })

        return JSONResponse({
            "status": "ok",
            "data": {
                "store_id": target_store_id,
                "start_date": start_dt.strftime("%Y-%m-%d"),
                "end_date": end_dt.strftime("%Y-%m-%d"),
                "session_count": len(sessions),
                "total_play_fee": int(total_play_fee),
                "total_service_fee": int(total_service_fee),
                "total_revenue": int(total_revenue),
                "sessions": session_list
            }
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()
