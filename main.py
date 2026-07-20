from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
import json
import shutil
import math
from datetime import datetime
import redis as redis_lib
from api.redis_listener import start_redis_listener_thread
from api.websocket_server import websocket_manager
from database.database import init_db, SessionLocal
from database.crud import seed_initial_tables, seed_initial_products
from database.models import BilliardTable, PlaySession, SessionOrderItem, Product

CLIPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips")
ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "archive")

os.makedirs(CLIPS_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    seed_initial_tables(db)
    seed_initial_products(db)
    db.close()
    loop = asyncio.get_running_loop()
    start_redis_listener_thread(loop)
    yield

app = FastAPI(lifespan=lifespan)

# Mount thu muc clips de phuc vu file MP4 va anh live
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")
os.makedirs("assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <title>Bida Club - Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            overflow-x: hidden;
        }

        /* === HEADER === */
        .header {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding: 16px 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .logo-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            box-shadow: 0 4px 15px rgba(99,102,241,0.4);
        }

        .header-title {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(90deg, #c4b5fd, #818cf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .header-sub {
            font-size: 12px;
            color: #9ca3af;
            font-weight: 400;
        }

        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }

        /* === STATS BAR === */
        .stats-bar {
            display: flex;
            gap: 16px;
            align-items: center;
        }

        .stat-chip {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
        }

        .stat-chip .dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            animation: pulse-dot 2s infinite;
        }

        .dot-green { background: #22c55e; box-shadow: 0 0 8px #22c55e; }
        .dot-red { background: #ef4444; box-shadow: 0 0 8px #ef4444; }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(0.8); }
        }

        #clock {
            font-size: 14px;
            font-weight: 600;
            color: #a5b4fc;
            font-variant-numeric: tabular-nums;
        }

        /* === STATUS BANNER === */
        .status-banner {
            margin: 20px 30px 0;
            padding: 14px 24px;
            border-radius: 14px;
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.5s ease;
        }

        .status-connecting {
            background: rgba(59,130,246,0.15);
            border: 1px solid rgba(59,130,246,0.3);
            color: #93c5fd;
        }

        .status-connected {
            background: rgba(34,197,94,0.15);
            border: 1px solid rgba(34,197,94,0.3);
            color: #86efac;
        }

        .status-error {
            background: rgba(239,68,68,0.15);
            border: 1px solid rgba(239,68,68,0.3);
            color: #fca5a5;
        }

        /* === MAIN CONTENT (2-COLUMN GRID) === */
        .main-content {
            padding: 20px 30px;
            max-width: 1600px;
            margin: 0 auto;
        }

        .dashboard-grid {
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 30px;
        }

        .dashboard-col {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        .section-label {
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #8b949e;
            margin-bottom: 8px;
        }

        /* === TABLES GRID === */
        .tables-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }

        .cameras-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .table-card {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            transition: all 0.3s ease;
        }

        .table-card.playing {
            border-color: rgba(99,102,241,0.4);
            background: rgba(99,102,241,0.04);
            box-shadow: 0 8px 30px rgba(99,102,241,0.1);
        }

        .table-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .table-name {
            font-size: 17px;
            font-weight: 800;
            color: white;
        }

        .table-badges {
            display: flex;
            gap: 6px;
        }

        .badge-vip {
            background: linear-gradient(135deg, #fbbf24, #d97706);
            color: #1e1b4b;
            font-size: 10px;
            font-weight: 800;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .badge-std {
            background: rgba(255,255,255,0.1);
            color: #e5e7eb;
            font-size: 10px;
            font-weight: 600;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .badge-type {
            background: rgba(99,102,241,0.2);
            color: #a5b4fc;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .table-status-label {
            font-size: 12px;
            font-weight: 700;
        }

        .status-empty { color: #9ca3af; }
        .status-playing { color: #86efac; animation: pulse-text 2s infinite; }

        @keyframes pulse-text {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .table-details {
            font-size: 12px;
            color: #9ca3af;
            line-height: 1.6;
            background: rgba(0,0,0,0.25);
            padding: 12px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
            border: 1px solid rgba(255,255,255,0.03);
        }

        .order-btn-group {
            display: flex;
            gap: 8px;
            margin-top: 4px;
            flex-wrap: wrap;
        }

        /* === CARD BASE === */
        .card {
            background: rgba(255,255,255,0.04);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }

        .card-header-title {
            font-size: 16px;
            font-weight: 700;
            color: #c4b5fd;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* === LIVE CAM STYLING === */
        .live-stream-container {
            position: relative;
            width: 100%;
            aspect-ratio: 16/9;
            background: #000;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .live-stream-img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .live-tag {
            position: absolute;
            top: 12px;
            left: 12px;
            background: #ef4444;
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            animation: blink 1.5s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* === HIGHLIGHT STYLING === */
        .highlight-desc {
            font-size: 13px;
            color: #9ca3af;
            margin-bottom: 16px;
            line-height: 1.5;
        }

        .highlight-status {
            font-size: 13px;
            font-weight: 600;
            padding: 10px 16px;
            border-radius: 10px;
            margin-top: 12px;
            display: none;
        }

        .highlight-processing {
            background: rgba(59,130,246,0.15);
            color: #93c5fd;
            border: 1px solid rgba(59,130,246,0.3);
        }

        .highlight-ready {
            background: rgba(34,197,94,0.15);
            color: #86efac;
            border: 1px solid rgba(34,197,94,0.3);
        }

        .clips-list {
            margin-top: 16px;
        }

        .clip-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: rgba(255,255,255,0.04);
            border-radius: 10px;
            margin-bottom: 8px;
            font-size: 13px;
        }

        .clip-item-name {
            color: #e5e7eb;
            font-weight: 500;
        }

        .clip-item-size {
            color: #8b949e;
            font-size: 12px;
        }

        /* === EVENT CARDS === */
        .event-card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            animation: slideIn 0.4s ease-out;
            transition: all 0.3s ease;
        }

        .event-card:hover {
            background: rgba(255,255,255,0.08);
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }

        .event-card.urgent {
            border-left: 4px solid #f59e0b;
            box-shadow: 0 0 20px rgba(245,158,11,0.15);
        }

        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px) scale(0.97); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .event-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .event-badge {
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 4px 10px;
            border-radius: 6px;
        }

        .badge-hand {
            background: rgba(245,158,11,0.2);
            color: #fbbf24;
            border: 1px solid rgba(245,158,11,0.3);
        }

        .badge-motion {
            background: rgba(59,130,246,0.2);
            color: #93c5fd;
            border: 1px solid rgba(59,130,246,0.3);
        }

        .event-time {
            font-size: 12px;
            color: #8b949e;
            font-variant-numeric: tabular-nums;
        }

        .event-message {
            font-size: 15px;
            font-weight: 500;
            color: #e5e7eb;
            margin-bottom: 14px;
            line-height: 1.5;
        }

        .event-image {
            width: 100%;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 16px;
        }

        .event-actions {
            display: flex;
            gap: 10px;
        }

        /* === BUTTONS === */
        .btn {
            border: none;
            padding: 10px 22px;
            border-radius: 10px;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .btn-confirm {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            box-shadow: 0 4px 12px rgba(34,197,94,0.3);
        }

        .btn-confirm:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(34,197,94,0.4); }

        .btn-dismiss {
            background: rgba(239,68,68,0.15);
            color: #fca5a5;
            border: 1px solid rgba(239,68,68,0.2);
        }

        .btn-dismiss:hover { background: rgba(239,68,68,0.25); transform: translateY(-2px); }

        .btn-highlight {
            background: linear-gradient(135deg, #8b5cf6, #6366f1);
            color: white;
            box-shadow: 0 4px 12px rgba(99,102,241,0.3);
        }

        .btn-highlight:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(99,102,241,0.4); }

        .btn-download {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            box-shadow: 0 4px 12px rgba(245,158,11,0.3);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-download:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(245,158,11,0.4); }

        .btn-small {
            padding: 6px 12px !important;
            font-size: 11px !important;
            border-radius: 6px !important;
        }

        .btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            transform: none !important;
        }

        .event-resolved {
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
            padding: 6px 12px;
            border-radius: 8px;
            display: inline-block;
        }

        .resolved-confirmed {
            background: rgba(34,197,94,0.15);
            color: #86efac;
        }

        .resolved-dismissed {
            background: rgba(239,68,68,0.15);
            color: #fca5a5;
        }

        /* === TIME MACHINE STYLING === */
        .time-machine-container {
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 20px;
            margin-top: 20px;
        }

        .time-machine-title {
            font-size: 14px;
            font-weight: 700;
            color: #a5b4fc;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .time-machine-row {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .time-input {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: white;
            padding: 9px 12px;
            font-family: inherit;
            font-size: 13px;
            outline: none;
            flex: 1;
        }

        /* === EMPTY STATE === */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #6b7280;
        }

        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
            opacity: 0.5;
        }

        .empty-text {
            font-size: 15px;
            font-weight: 500;
        }

        .empty-sub {
            font-size: 13px;
            margin-top: 6px;
            color: #4b5563;
        }

        /* === SOUND TOGGLE === */
        .sound-toggle {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 10px;
            padding: 8px 14px;
            color: #e0e0e0;
            font-family: 'Inter', sans-serif;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .sound-toggle:hover { background: rgba(255,255,255,0.12); }
        .sound-toggle.active { background: rgba(99,102,241,0.2); border-color: rgba(99,102,241,0.4); color: #a5b4fc; }

        /* === HAMBURGER BUTTON === */
        .menu-toggle-btn {
            background: none;
            border: none;
            color: #c4b5fd;
            font-size: 26px;
            cursor: pointer;
            padding: 4px 10px;
            border-radius: 8px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
        }

        .menu-toggle-btn:hover {
            background: rgba(255,255,255,0.08);
            color: white;
        }

        /* === LAYOUT WITH SIDEBAR === */
        .app-container {
            display: flex;
            min-height: calc(100vh - 75px);
            position: relative;
        }

        .sidebar {
            width: 260px;
            background: rgba(15,12,41,0.6);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border-right: 1px solid rgba(255,255,255,0.08);
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            gap: 24px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 90;
        }

        .sidebar.collapsed {
            width: 0;
            padding: 30px 0;
            overflow: hidden;
            border-right: none;
            opacity: 0;
            pointer-events: none;
        }

        .sidebar-section {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .sidebar-section-title {
            font-size: 11px;
            font-weight: 700;
            color: #8b949e;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
            padding-left: 12px;
        }

        .sidebar-link {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #9ca3af;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            padding: 12px 16px;
            border-radius: 12px;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        .sidebar-link:hover {
            background: rgba(255,255,255,0.06);
            color: white;
        }

        .sidebar-link.active {
            background: rgba(99,102,241,0.15);
            border: 1px solid rgba(99,102,241,0.3);
            color: #a5b4fc;
        }

        /* === MAIN CONTENT WRAPPER === */
        .main-content-wrapper {
            flex: 1;
            padding: 24px 30px;
            transition: all 0.3s ease;
            overflow-x: hidden;
        }

        /* === RIGHT DRAWER (NGĂN KÉO TRƯỢT) === */
        .drawer {
            position: fixed;
            top: 0;
            right: 0;
            width: 385px;
            height: 100%;
            background: #0f0c29;
            background: linear-gradient(to bottom, #14113c, #0d0a21);
            border-left: 1px solid rgba(255,255,255,0.12);
            box-shadow: -10px 0 40px rgba(0,0,0,0.6);
            z-index: 1100;
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
        }

        .drawer.open {
            transform: translateX(0);
        }

        .drawer-header {
            padding: 24px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .drawer-header h3 {
            font-size: 16px;
            font-weight: 800;
            color: #fbbf24;
            margin: 0;
        }

        .drawer-close {
            background: none;
            border: none;
            color: #9ca3af;
            font-size: 22px;
            cursor: pointer;
            padding: 4px;
            transition: color 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .drawer-close:hover {
            color: white;
        }

        .drawer-body {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
        }

        .drawer-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.6);
            backdrop-filter: blur(4px);
            z-index: 1050;
            display: none;
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .drawer-overlay.open {
            display: block;
            opacity: 1;
        }

        /* === LIVE CAMERA STREAMS GRID & STATE === */
        .live-stream-container {
            position: relative;
            cursor: pointer;
            overflow: hidden;
            border-radius: 12px;
            border: 2px solid rgba(255,255,255,0.08);
            transition: all 0.3s ease;
        }

        .live-stream-container.active-table {
            border-color: rgba(34,197,94,0.45);
            box-shadow: 0 0 15px rgba(34,197,94,0.15);
        }

        .live-stream-container.empty-table {
            border-color: rgba(156,163,175,0.15);
        }

        .stream-status-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            z-index: 10;
            letter-spacing: 0.5px;
        }

        .status-active-playing {
            background: rgba(34,197,94,0.25);
            color: #4ade80;
            border: 1px solid rgba(34,197,94,0.35);
        }

        .status-empty-waiting {
            background: rgba(156,163,175,0.15);
            color: #d1d5db;
            border: 1px solid rgba(156,163,175,0.25);
        }

        .stream-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15,23,42,0.85);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 12px;
            z-index: 5;
            transition: all 0.3s ease;
        }

        .stream-overlay.hidden {
            opacity: 0;
            pointer-events: none;
        }

        .stream-action-btn {
            background: rgba(99,102,241,0.2);
            border: 1px solid rgba(99,102,241,0.4);
            color: #a5b4fc;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            transition: all 0.2s;
            cursor: pointer;
        }

        .stream-action-btn:hover {
            background: rgba(99,102,241,0.35);
            color: white;
        }

        /* Hover overlay on live stream */
        .live-stream-container:hover .hover-action-overlay {
            opacity: 1;
        }

        .hover-action-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 4;
        }

        /* === RESPONSIVE === */
        @media (max-width: 1024px) {
            .dashboard-grid { grid-template-columns: 1fr; }
            .sidebar { position: fixed; top: 75px; left: 0; height: calc(100vh - 75px); transform: translateX(-100%); }
            .sidebar.collapsed { transform: translateX(0); width: 260px; opacity: 1; pointer-events: auto; padding: 30px 20px; }
        }

        @media (max-width: 768px) {
            .header { padding: 12px 16px; flex-direction: column; gap: 12px; }
            .main-content { padding: 16px; }
            .stats-bar { flex-wrap: wrap; justify-content: center; }
            .status-banner { margin: 12px 16px 0; }
            .event-actions { flex-direction: column; }
            .btn { justify-content: center; }
            .drawer { width: 100%; }
        }
    </style>
</head>
<body>
    <!-- HEADER -->
    <div class="header">
        <div class="header-left">
            <button class="menu-toggle-btn" id="menu-btn" onclick="toggleSidebar()">☰</button>
            <div class="logo-icon">8</div>
            <div>
                <div class="header-title">Bida Club</div>
                <div class="header-sub">Đẳng cấp từng cú cơ</div>
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
                <div id="clock">--:--:--</div>
            </div>
            <button class="sound-toggle" id="sound-btn" onclick="toggleSound()">
                <span id="sound-icon">&#128264;</span> Am thanh
            </button>
        </div>
    </div>

    <!-- STATUS BANNER -->
    <div class="status-banner status-connecting" id="status-banner">
        <span id="banner-icon">&#9881;</span>
        <span id="banner-text">Dang khoi tao ket noi toi AI Camera Server...</span>
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
                <div class="sidebar-section-title">📊 BÁO CÁO</div>
                <a href="#" class="sidebar-link" onclick="openReportModal()">📊 Xuất báo cáo Doanh thu</a>
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
                <div>
                    <label style="font-size: 13px; font-weight: 600; color: #a5b4fc; display: block; margin-bottom: 4px;">Từ ngày:</label>
                    <input type="date" id="report-start-date" style="width: 100%; height: 40px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 12px; font-size: 14px; outline: none; color-scheme: dark;">
                </div>
                <div>
                    <label style="font-size: 13px; font-weight: 600; color: #a5b4fc; display: block; margin-bottom: 4px;">Đến ngày:</label>
                    <input type="date" id="report-end-date" style="width: 100%; height: 40px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: white; padding: 0 12px; font-size: 14px; outline: none; color-scheme: dark;">
                </div>
            </div>
            
            <button onclick="downloadRevenueReport()" style="margin-top: 8px; height: 44px; border-radius: 8px; border: none; background: linear-gradient(135deg, #2563eb, #1d4ed8); color: white; font-weight: bold; font-size: 15px; cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">📥 Tải file Excel (.csv)</button>
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

            <!-- Form thêm sản phẩm mới -->
            <div style="background: rgba(255,255,255,0.04); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); display: flex; flex-direction: column; gap: 10px;">
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
                <button onclick="addNewProduct()" style="height: 36px; border-radius: 6px; border: none; background: linear-gradient(135deg, #10b981, #059669); color: white; font-weight: bold; cursor: pointer; transition: opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">Thêm sản phẩm</button>
            </div>

            <!-- Danh sách sản phẩm hiện tại -->
            <div style="font-size: 13px; color: #d1d5db;">
                <div style="font-weight: 700; color: #fbbf24; margin-bottom: 8px;">Danh sách thực phẩm trong kho:</div>
                <div style="max-height: 280px; overflow-y: auto; background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);">
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
                        <thead>
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #a5b4fc; font-weight: 700;">
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
                <button id="bill-confirm-btn" class="btn btn-confirm" style="flex: 1; justify-content: center; font-size: 14px; padding: 12px;" onclick="closeBillModal()">✔️ Xác nhận & Thu tiền</button>
            </div>
        </div>
    </div>

    <!-- QR CODE MODAL -->
    <div class="bill-modal-overlay" id="qr-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(8px); z-index: 1000; align-items: center; justify-content: center;">
        <div class="card" style="width: 90%; max-width: 380px; background: #1e1b4b; border: 1px solid rgba(255,255,255,0.15); display: flex; flex-direction: column; gap: 16px; padding: 28px; text-align: center; align-items: center;">
            <div style="font-size: 18px; font-weight: 800; color: #fbbf24; width: 100%; border-bottom: 2px dashed rgba(255,255,255,0.15); padding-bottom: 12px;" id="qr-modal-title">
                📷 MÃ QR GỌI MÓN - BÀN X
            </div>
            <div style="background: white; padding: 12px; border-radius: 12px; display: inline-block; margin: 10px 0;">
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

    <script>
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
        }, 200);

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

        // === LOAD TABLES DATA ===
        function loadTables() {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "/api/tables?_" + Date.now(), true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var tables = JSON.parse(xhr.responseText);
                    tablesLocalData = tables;
                    renderTablesGrid(tables);
                    syncStreamStates(tables); // Cập nhật trạng thái bật/tắt camera
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
                    showTableQRModal(t.id, t.name);
                });
                btnGroup.appendChild(btnQR);
                
                card.appendChild(btnGroup);
                
                // Inline Add Item Form
                var addForm = document.createElement("div");
                addForm.id = "add-item-form-" + t.id;
                addForm.style.cssText = "display: " + (openForms[t.id] ? "flex" : "none") + "; flex-direction: column; gap: 8px; margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.08);";
                
                var formRow = document.createElement("div");
                formRow.style.display = "flex";
                formRow.style.gap = "6px";
                
                var select = document.createElement("select");
                select.id = "item-select-" + t.id;
                select.style.cssText = "background:#1f1b4b; border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:white; padding:4px; font-size:12px; flex:2; outline:none;";
                
                // Luu gia tri da chon vao cache khi thay doi de khong bi mat
                select.addEventListener("change", function() {
                    formSelectedItems[t.id] = this.value;
                });
                
                var menuItems = [
                    {name: "Sting dâu", price: 15000},
                    {name: "Coca Cola", price: 15000},
                    {name: "Bò húc", price: 20000},
                    {name: "Khô mực nướng", price: 50000},
                    {name: "Đậu phộng rang", price: 15000},
                    {name: "Khăn lạnh", price: 5000}
                ];
                
                menuItems.forEach(function(item) {
                    var opt = document.createElement("option");
                    opt.value = item.name + "|" + item.price;
                    opt.textContent = item.name + " - " + (item.price/1000) + "k";
                    select.appendChild(opt);
                });
                
                // Phuc hoi lai gia tri da chon tu truoc do
                if (formSelectedItems[t.id]) {
                    select.value = formSelectedItems[t.id];
                }
                
                var qtyInput = document.createElement("input");
                qtyInput.type = "number";
                qtyInput.id = "item-qty-" + t.id;
                qtyInput.value = formQuantities[t.id] || "1";
                qtyInput.min = "1";
                qtyInput.style.cssText = "background:#1f1b4b; border:1px solid rgba(255,255,255,0.1); border-radius:6px; color:white; padding:4px; font-size:12px; width:45px; text-align:center;";
                
                qtyInput.addEventListener("input", function() {
                    formQuantities[t.id] = this.value;
                });
                
                formRow.appendChild(select);
                formRow.appendChild(qtyInput);
                addForm.appendChild(formRow);
                
                var subBtn = document.createElement("button");
                subBtn.className = "btn btn-confirm btn-small";
                subBtn.style.justifyContent = "center";
                subBtn.style.padding = "4px";
                subBtn.textContent = "Xác nhận thêm";
                subBtn.addEventListener("click", function() {
                    submitAddItem(t.id);
                });
                
                addForm.appendChild(subBtn);
                card.appendChild(addForm);
                
                tablesGrid.appendChild(card);
            });
        }
        
        function showAddItemForm(tableId) {
            var formEl = document.getElementById("add-item-form-" + tableId);
            if (formEl) {
                var isNone = formEl.style.display === "none";
                formEl.style.display = isNone ? "flex" : "none";
                openForms[tableId] = isNone;
                
                // Pre-fill cache de khoi tao gia tri neu chua co
                if (isNone) {
                    var select = document.getElementById("item-select-" + tableId);
                    var qty = document.getElementById("item-qty-" + tableId);
                    if (select) formSelectedItems[tableId] = select.value;
                    if (qty) formQuantities[tableId] = qty.value;
                }
            }
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

        // === SUBMIT ADD ITEM TO SESSION ===
        function submitAddItem(tableId) {
            var select = document.getElementById("item-select-" + tableId);
            var qtyInput = document.getElementById("item-qty-" + tableId);
            
            if (!select || !qtyInput) return;
            
            var parts = select.value.split("|");
            var name = parts[0];
            var price = parseFloat(parts[1]);
            var qty = parseInt(qtyInput.value);
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/add-item/" + tableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                if (xhr.status === 200) {
                    // Reset cache sau khi them thanh cong
                    openForms[tableId] = false;
                    delete formSelectedItems[tableId];
                    delete formQuantities[tableId];
                    loadTables();
                } else {
                    var errMsg = "Không thể thêm món!";
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res && res.message) errMsg = res.message;
                    } catch(e) {}
                    alert(errMsg);
                }
            };
            xhr.send(JSON.stringify({
                "item_name": name,
                "quantity": qty,
                "price": price
            }));
        }

        // === CHECKOUT SESSION (STOP) ===
        function checkoutSession(tableId) {
            if (!confirm("Bạn có chắc chắn muốn tính tiền và thanh toán hóa đơn cho bàn này?")) return;
            
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/session/stop/" + tableId, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    var bill = JSON.parse(xhr.responseText);
                    showBillInvoice(bill);
                    printBill(); // In tự động khi thanh toán toàn bộ
                    loadTables();
                } else {
                    alert("Không thể thanh toán!");
                }
            };
            xhr.send();
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
                        item_name: item.item_name,
                        quantity: item.quantity,
                        price: item.price,
                        total_price: item.total_price
                    });
                });
            }
            
            var totalBill = playFee + serviceTotal;
            
            var tempBill = {
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
            
            document.getElementById("bill-start-time").textContent = start.toLocaleTimeString();
            document.getElementById("bill-end-time").textContent = end.toLocaleTimeString();
            
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
                    var tr = document.createElement("tr");
                    tr.style.borderBottom = "1px solid rgba(255,255,255,0.04)";
                    tr.innerHTML = 
                        "<td style='padding: 6px 0; color: #e5e7eb;'>" + item.item_name + "</td>" +
                        "<td style='padding: 6px 8px; text-align: center; font-weight: 600; color: #fbbf24;'>" + item.quantity + "</td>" +
                        "<td style='padding: 6px 8px; text-align: right; font-variant-numeric: tabular-nums;'>" + Math.ceil(item.price).toLocaleString("vi-VN") + " đ</td>" +
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

        var currentBillToPrint = null;
        function printBill() {
            if (!currentBillToPrint) return;
            var bill = currentBillToPrint;
            var printWin = window.open("", "_blank");
            var itemsHtml = "";
            if (bill.items && bill.items.length > 0) {
                bill.items.forEach(function(item) {
                    itemsHtml += "<tr>" +
                        "<td>" + item.item_name + "</td>" +
                        "<td style='text-align:center;'>" + item.quantity + "</td>" +
                        "<td style='text-align:right;'>" + Math.ceil(item.price).toLocaleString("vi-VN") + "</td>" +
                        "<td style='text-align:right;'>" + Math.ceil(item.total_price).toLocaleString("vi-VN") + "</td>" +
                    "</tr>";
                });
            } else {
                itemsHtml = "<tr><td colspan='4' style='text-align:center;'>Không gọi dịch vụ</td></tr>";
            }
            
            var sTime = new Date(bill.start_time).toLocaleTimeString('vi-VN');
            var eTime = bill.is_preview ? "--:--" : new Date(bill.end_time).toLocaleTimeString('vi-VN');
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
                "</body></html>";

            printWin.document.write(html);
            printWin.document.close();
            printWin.focus();
            setTimeout(() => { printWin.print(); printWin.close(); }, 500);
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

        function showTableQRModal(tableId, tableName) {
            var qrTitle = document.getElementById("qr-modal-title");
            var qrImg = document.getElementById("qr-modal-image");
            var qrLink = document.getElementById("qr-modal-link");
            var targetUrl = window.location.origin + "/menu/" + tableId;
            
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
                    var btnApprove = document.createElement("button");
                    btnApprove.className = "btn btn-confirm";
                    btnApprove.style.background = "linear-gradient(135deg, #10b981, #059669)";
                    btnApprove.style.flex = "1";
                    btnApprove.innerHTML = "&#10004; Xác nhận đã phục vụ";
                    btnApprove.addEventListener("click", function() {
                        handleAction(card, "confirm");
                    });

                    actions.appendChild(btnApprove);
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

        // Load ban dau
        loadClips();
        loadTables();
        
        // Polling trang thai ban moi 3s de cap nhat thoi gian choi lien tuc
        setInterval(loadTables, 3000);
    </script>
</body>
</html>"""

@app.get("/api/inventory")
async def get_inventory():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        stock_dict = {p.name: p.stock for p in products}
        return JSONResponse(stock_dict)
    finally:
        db.close()

@app.get("/api/products")
async def list_products():
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id).all()
        return JSONResponse([
            {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock, "category": p.category, "image_url": p.image_url or ""}
            for p in products
        ])
    finally:
        db.close()

@app.post("/api/products/add")
async def add_product(payload: dict):
    name = payload.get("name", "").strip()
    price = float(payload.get("price", 0))
    stock = int(payload.get("stock", 0))
    category = payload.get("category", "").strip()
    image_url = payload.get("image_url", "").strip()
    
    if not name or price < 1000 or stock < 0 or not category:
        return JSONResponse({"status": "error", "message": "Đơn giá phải từ 1000 VNĐ trở lên và tồn kho không được âm"}, status_code=400)
        
    db = SessionLocal()
    try:
        exists = db.query(Product).filter(Product.name == name).first()
        if exists:
            return JSONResponse({"status": "error", "message": f"Sản phẩm {name} đã tồn tại!"}, status_code=400)
            
        new_prod = Product(name=name, price=price, stock=stock, category=category, image_url=image_url)
        db.add(new_prod)
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Đã thêm sản phẩm {name}!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/products/update")
async def update_product(payload: dict):
    prod_id = int(payload.get("id"))
    price = float(payload.get("price", 0))
    stock = int(payload.get("stock", 0))
    image_url = payload.get("image_url", "").strip()
    
    if price < 1000 or stock < 0:
        return JSONResponse({"status": "error", "message": "Đơn giá phải từ 1000 VNĐ trở lên và tồn kho không được âm!"}, status_code=400)
        
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id).first()
        if not product:
            return JSONResponse({"status": "error", "message": "Sản phẩm không tồn tại"}, status_code=404)
            
        product.price = price
        product.stock = stock
        product.image_url = image_url
        db.commit()
        return JSONResponse({"status": "ok", "message": "Đã cập nhật sản phẩm!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.delete("/api/products/delete/{prod_id}")
async def delete_product(prod_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == prod_id).first()
        if not product:
            return JSONResponse({"status": "error", "message": "Sản phẩm không tồn tại"}, status_code=404)
            
        db.delete(product)
        db.commit()
        return JSONResponse({"status": "ok", "message": "Đã xóa sản phẩm!"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

import csv
import io
from fastapi.responses import StreamingResponse

@app.get("/api/reports/revenue")
async def get_revenue_report(start_date: str = None, end_date: str = None):
    db = SessionLocal()
    try:
        query = db.query(PlaySession).filter(PlaySession.status == "COMPLETED")
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(PlaySession.start_time >= start_dt)
            except ValueError:
                pass
                
        if end_date:
            try:
                # Include the whole end date
                end_dt = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                query = query.filter(PlaySession.start_time <= end_dt)
            except ValueError:
                pass
                
        sessions = query.order_by(PlaySession.start_time.desc()).all()
        
        output = io.StringIO()
        output.write('\ufeff') # Add BOM so Excel opens it with UTF-8 correctly
        
        # Use semicolon (;) which is standard for Excel in Vietnam/Europe regions
        writer = csv.writer(output, delimiter=';')
        writer.writerow(["Mã Hóa Đơn", "Tên Bàn", "Giờ Vào", "Giờ Ra", "Tổng Thời Gian (phút)", "Tiền Giờ (VNĐ)", "Tiền Dịch Vụ (VNĐ)", "Tổng Cộng (VNĐ)"])
        
        for session in sessions:
            table = db.query(BilliardTable).filter(BilliardTable.id == session.table_id).first()
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


@app.get("/")
async def get():
    return HTMLResponse(html)

customer_menu_html = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bida Club - Bàn {table_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
        body { background: #0d0a21; color: #f3f4f6; padding: 16px; min-height: 100vh; display: flex; flex-direction: column; }
        header { text-align: center; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed rgba(255,255,255,0.15); }
        .title { font-size: 22px; font-weight: 800; color: #fbbf24; }
        .subtitle { font-size: 13px; color: #9ca3af; margin-top: 4px; }
        
        .menu-list { display: flex; flex-direction: column; gap: 12px; }
        .menu-item { background: #1e1b4b; border: 1px solid rgba(255,255,255,0.06); padding: 14px; border-radius: 14px; display: flex; justify-content: space-between; align-items: center; transition: border-color 0.2s; }
        .item-info { display: flex; flex-direction: column; gap: 4px; }
        .item-name { font-size: 16px; font-weight: 600; color: white; }
        .item-price { font-size: 14px; color: #86efac; font-weight: 600; }
        
        .qty-container { display: flex; align-items: center; gap: 14px; }
        .btn-qty { width: 32px; height: 32px; border-radius: 10px; border: none; background: rgba(255,255,255,0.08); color: white; font-size: 18px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background 0.2s; }
        .btn-qty:active { background: rgba(255,255,255,0.2); }
        .btn-qty:disabled { opacity: 0.3; cursor: not-allowed; }
        .qty-val { font-size: 16px; font-weight: bold; width: 40px; text-align: center; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: white; border-radius: 6px; padding: 4px 0; outline: none; }
        .qty-val::-webkit-inner-spin-button, .qty-val::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        
        .sticky-footer { position: fixed; bottom: 0; left: 0; width: 100%; padding: 16px; background: rgba(13,10,33,0.9); backdrop-filter: blur(12px); border-top: 1px solid rgba(255,255,255,0.08); z-index: 100; }
        .btn-submit { width: 100%; height: 50px; border-radius: 14px; border: none; background: linear-gradient(135deg, #22c55e, #16a34a); color: white; font-size: 16px; font-weight: 700; cursor: pointer; box-shadow: 0 4px 15px rgba(34,197,94,0.3); display: flex; align-items: center; justify-content: center; gap: 8px; transition: transform 0.2s; }
        .btn-submit:active { transform: scale(0.98); }
        .btn-submit:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; background: #374151; }

        .success-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(13,10,33,0.95); display: none; align-items: center; justify-content: center; flex-direction: column; gap: 16px; padding: 24px; text-align: center; z-index: 200; }
        .success-icon { font-size: 64px; color: #22c55e; animation: pop 0.4s ease; }
        @keyframes pop { 0% { transform: scale(0.5); } 100% { transform: scale(1); } }
        
        /* Banner Styles */
        .top-content { display: grid; grid-template-columns: 1fr; gap: 24px; max-width: 1000px; margin: 0 auto 20px auto; align-items: stretch; }
        .info-section { width: 100%; max-width: 500px; margin: 0 auto; }
        .promo-image { display: none; width: 100%; border-radius: 24px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .promo-image img { width: 100%; height: 100%; object-fit: cover; display: block; filter: brightness(0.85); }
        
        @media (min-width: 850px) {
            .top-content { grid-template-columns: 1fr 1fr; }
            .promo-image { display: block; }
        }
        
        .pill-banner { display: flex; align-items: center; border-radius: 99px; margin-bottom: 8px; padding: 6px 16px 6px 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); background-color: #1e1b4b; border: 2px solid white; position: relative; overflow: hidden; }
        
        .pill-blue { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .pill-black { background: linear-gradient(90deg, #111827 0%, #374151 100%); }
        .pill-green { background: linear-gradient(90deg, #15803d 0%, #22c55e 100%); }
        
        .pill-icon { width: 44px; height: 44px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; margin-right: 12px; flex-shrink: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.2); border: 2px solid rgba(255,255,255,0.4); text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        .pill-content { display: flex; flex-direction: column; justify-content: center; flex: 1; }
        .pill-title { font-weight: 800; font-size: 14px; color: white; text-transform: uppercase; line-height: 1.2; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
        .pill-desc { font-size: 10.5px; color: rgba(255,255,255,0.95); font-weight: 500; line-height: 1.25; margin-top: 2px; }
    </style>
</head>
<body>
    <header>
        <div class="title">🎱 Bida Club - {table_name}</div>
        <div class="subtitle">Đẳng cấp từng cú cơ</div>
        <div style="font-size: 11px; color: #9ca3af; margin-top: 4px;">📍 3xx Huỳnh Tấn Phát quận 7 HCM &nbsp;|&nbsp; 📞 0396123456</div>
        <div class="subtitle" id="play-time-display" style="color: #fbbf24; font-weight: 600; margin-top: 6px;">
            🕒 Đã chơi: <span id="play-duration">--</span> (Từ <span id="play-start-time">--</span>)
        </div>
    </header>
    <div class="top-content">
        <div class="info-section">
            <div class="pill-banner pill-blue">
            <div class="pill-icon">🛡️</div>
            <div class="pill-content">
                <div class="pill-title">Miễn phí: Trà đá, khăn lạnh</div>
                <div class="pill-desc">Giữ xe, máy lạnh</div>
            </div>
        </div>
        
        <div class="pill-banner pill-black">
            <div class="pill-icon">🎱</div>
            <div class="pill-content">
                <div class="pill-title">Mượn miễn phí</div>
                <div class="pill-desc">Cơ mộc, cơ carbon, găng tay</div>
            </div>
        </div>
        
        <div class="pill-banner pill-green">
            <div class="pill-icon">🧋</div>
            <div class="pill-content">
                <div class="pill-title">Mang đồ ăn thức uống ngoài</div>
                <div class="pill-desc">Phụ thu 5k với món chính hoặc bày bừa</div>
            </div>
        </div>
        
        <div class="pill-banner pill-blue">
            <div class="pill-icon">⏱️</div>
            <div class="pill-content">
                <div class="pill-title">Không phí ẩn</div>
                <div class="pill-desc">Không phí ẩn, giá tốt cố định</div>
            </div>
        </div>
        
        <div class="pill-banner pill-black">
            <div class="pill-icon">🤝</div>
            <div class="pill-content">
                <div class="pill-title">Hỗ trợ xếp bi</div>
                <div class="pill-desc">Nếu bàn đông, NV hỗ trợ không kịp, quý khách hoan hỉ nhé ^^</div>
            </div>
        </div>
        
        <div class="pill-banner pill-green">
            <div class="pill-icon">🏪</div>
            <div class="pill-content">
                <div class="pill-title">24/24, 20+ chi nhánh</div>
                <div class="pill-desc">Mở xuyên lễ. Sau 22h hoặc trước 6h xin gọi NV mở cửa</div>
            </div>
        </div>
        
        <div class="pill-banner pill-green">
            <div class="pill-icon">💲</div>
            <div class="pill-content">
                <div class="pill-title">Bảng giá giờ chơi</div>
                <div class="pill-desc">Pool/Libre: 29k-39k/h &nbsp;|&nbsp; 3C: 39k-49k/h</div>
            </div>
        </div>
        </div>
        <div class="promo-image">
            <img src="/assets/promo.png" alt="Bida Club" />
        </div>
    </div>

    <div id="order-history-section" style="display: none; margin-bottom: 20px; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.3); border-radius: 12px; padding: 14px;">
        <div style="font-size: 14px; font-weight: 700; color: #a5b4fc; margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
            📜 Các món đã đặt trước đó:
        </div>
        <div id="order-history-list" style="font-size: 14px; color: #e5e7eb; display: flex; flex-direction: column; gap: 6px;">
        </div>
    </div>

    <div class="category-tabs" id="category-tabs" style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 8px; margin-bottom: 16px; margin-top: 4px; scrollbar-width: none;">
        <!-- Rendered by JS -->
    </div>
    <style>
        .category-tabs::-webkit-scrollbar { display: none; }
        .cat-btn { flex-shrink: 0; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); color: #9ca3af; padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; white-space: nowrap; }
        .cat-btn.active { background: #6366f1; color: white; border-color: #6366f1; }
    </style>

    <div class="menu-list" id="menu-items-container">
        <!-- Load items here dynamically via Javascript -->
    </div>
    
    <div style="margin-top: 24px; padding: 14px; background: #1e1b4b; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 24px;">
        <div style="font-size: 14px; font-weight: 600; color: #86efac; margin-bottom: 8px;">📞 Số điện thoại nhận đồ (Bắt buộc):</div>
        <input type="tel" id="order-phone" placeholder="Nhập SĐT Việt Nam (ví dụ: 0912345678)" style="width: 100%; height: 44px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; padding: 0 12px; font-size: 14px; outline: none;">
    </div>
    
    <div style="margin-top: 0px; padding: 14px; background: #1e1b4b; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 100px;">
        <div style="font-size: 14px; font-weight: 600; color: #a5b4fc; margin-bottom: 8px;">📝 Ghi chú yêu cầu thêm:</div>
        <textarea id="order-note" placeholder="Ví dụ: Sting ít đá, Mực nướng chín kỹ..." style="width: 100%; height: 60px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; color: white; padding: 8px; font-size: 13px; resize: none; outline: none;"></textarea>
    </div>

    <div class="sticky-footer">
        <button class="btn-submit" id="submit-order-btn" onclick="submitOrder()" disabled>
            🛒 Gửi yêu cầu gọi món (Tổng: <span id="total-amount">0 VNĐ</span>)
        </button>
    </div>

    <div class="success-overlay" id="success-overlay">
        <div class="success-icon">✔️</div>
        <h2 style="font-weight: 800; color: #fbbf24; font-size: 22px;">Gửi yêu cầu thành công!</h2>
        <p style="color: #9ca3af; font-size: 14px; margin-top: 8px;">Nhân viên đã nhận được order và đang chuẩn bị đồ dùng phục vụ bạn.</p>
        <button class="btn-submit" style="margin-top: 24px; max-width: 200px; background: rgba(255,255,255,0.08); box-shadow: none;" onclick="resetMenu()">Tiếp tục gọi món</button>
    </div>

    <script>
        var tableId = {table_id};
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

        // Load SDT tu localStorage neu co
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

        var categories = ["Thức uống", "Đồ ăn", "Thuốc lá", "Yêu cầu nghiệp vụ", "Dịch vụ khác"];
        var activeCategory = "all";

        function renderCategories() {
            var tabsContainer = document.getElementById("category-tabs");
            if (!tabsContainer) return;
            tabsContainer.innerHTML = "";
            
            var allBtn = document.createElement("button");
            allBtn.className = "cat-btn " + (activeCategory === "all" ? "active" : "");
            allBtn.onclick = function() { filterCategory("all"); };
            allBtn.textContent = "Tất cả";
            tabsContainer.appendChild(allBtn);
            
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
                tabsContainer.appendChild(btn);
            });
        }

        function filterCategory(cat) {
            activeCategory = cat;
            renderCategories();
            renderMenu();
        }

        function renderMenu() {
            var container = document.getElementById("menu-items-container");
            container.innerHTML = "";
            
            categories.forEach(function(cat) {
                if (activeCategory !== "all" && activeCategory.trim().normalize("NFC") !== cat.trim().normalize("NFC")) return;
                var catItems = menuItems.filter(function(item) { return (item.category || "").trim().normalize("NFC") === cat.trim().normalize("NFC"); });
                if (catItems.length === 0) return;
                
                var catHeader = document.createElement("div");
                catHeader.style.cssText = "font-size: 15px; font-weight: 800; color: #a5b4fc; text-transform: uppercase; margin-top: 18px; margin-bottom: 8px; letter-spacing: 0.5px; border-left: 3px solid #6366f1; padding-left: 8px;";
                var icon = "🍹 Thức uống";
                if (cat === "Đồ ăn") icon = "🍔 Đồ ăn";
                else if (cat === "Thuốc lá") icon = "🚬 Thuốc lá";
                else if (cat === "Dịch vụ khác") icon = "❄️ Dịch vụ khác";
                else if (cat === "Yêu cầu nghiệp vụ") icon = "🛎️ Yêu cầu nghiệp vụ";
                catHeader.textContent = icon;
                container.appendChild(catHeader);
                
                catItems.forEach(function(item, idx) {
                    try {
                        orderQty[item.name] = orderQty[item.name] || 0;
                        var currentStock = inventoryStock[item.name] || 0;
                        
                        var card = document.createElement("div");
                        card.className = "menu-item";
                        
                        var info = document.createElement("div");
                        info.className = "item-info";
                        
                        if (item.category === "Yêu cầu nghiệp vụ") {
                            info.innerHTML = "<span class='item-name' style='font-size: 15px;'>" + item.name + "</span>";
                            if (item.name === "Yêu cầu khác") {
                                info.innerHTML += "<input type='text' maxlength='250' placeholder='Nhập nội dung yêu cầu (tối đa 250 ký tự)...' style='margin-top: 8px; padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.3); color: white; width: 100%; font-size: 14px;' value='" + window.otherReqText.replace(/'/g, "&#39;") + "' onchange='window.saveOtherReq(this.value)' onkeyup='window.saveOtherReq(this.value)'>";
                            }
                            var qtyDiv = document.createElement("div");
                            qtyDiv.className = "qty-container";
                            var isSelected = orderQty[item.name] > 0;
                            var toggleBtn = document.createElement("button");
                            toggleBtn.className = "btn-submit";
                            toggleBtn.style.cssText = isSelected ? "width: auto; padding: 6px 14px; height: 34px; font-size: 13px; background: #fbbf24; color: #000; box-shadow: none;" : "width: auto; padding: 6px 14px; height: 34px; font-size: 13px; background: transparent; border: 1px solid rgba(255,255,255,0.3); box-shadow: none; color: white;";
                            toggleBtn.textContent = isSelected ? "Đã chọn ✓" : "Chọn";
                            toggleBtn.onclick = function() {
                                orderQty[item.name] = isSelected ? 0 : 1;
                                renderMenu();
                            };
                            qtyDiv.appendChild(toggleBtn);
                        } else {
                            var stockVal = item.stock !== undefined ? item.stock : currentStock;
                            var stockLabel = stockVal > 0 ? (" (Còn: " + stockVal + ")") : " (Hết hàng)";
                            var stockColor = stockVal > 0 ? "#9ca3af" : "#ef4444";
                            
                            var imgHtml = item.image_url ? "<img src='" + item.image_url + "' onerror='this.remove()' style='width: 48px; height: 48px; object-fit: cover; border-radius: 8px; margin-right: 12px; border: 1px solid rgba(255,255,255,0.1);'>" : "";
                            
                            info.style.display = "flex";
                            info.style.flexDirection = "row";
                            info.style.alignItems = "center";
                            
                            info.innerHTML = imgHtml + "<div style='display: flex; flex-direction: column; justify-content: center;'><span class='item-name'>" + item.name + "</span>" +
                                             "<span class='item-price'>" + item.price.toLocaleString("vi-VN") + " đ <span style='font-size:12px; color:" + stockColor + "; font-weight:normal;'>" + stockLabel + "</span></span></div>";
                            
                            var qtyDiv = document.createElement("div");
                            qtyDiv.className = "qty-container";
                            
                            var isMinusDisabled = (orderQty[item.name] === 0);
                            var isPlusDisabled = (orderQty[item.name] >= currentStock);
                            
                            var minusBtn = document.createElement("button");
                            minusBtn.className = "btn-qty";
                            minusBtn.textContent = "-";
                            minusBtn.disabled = isMinusDisabled;
                            minusBtn.style.opacity = isMinusDisabled ? "0.3" : "1";
                            minusBtn.addEventListener("click", function() { adjustQty(item.name, -1); });
                            
                            var qtySpan = document.createElement("input");
                            qtySpan.type = "number";
                            qtySpan.className = "qty-val";
                            qtySpan.value = orderQty[item.name];
                            qtySpan.min = 0;
                            qtySpan.max = currentStock;
                            
                            qtySpan.addEventListener("change", function(e) {
                                var val = parseInt(e.target.value) || 0;
                                if (val > currentStock) {
                                    alert("Rất tiếc! Số lượng bạn nhập (" + val + ") vượt quá tồn kho (chỉ còn " + currentStock + "). Vui lòng nhập lại!");
                                    val = 0;
                                } else if (val < 0) {
                                    val = 0;
                                }
                                orderQty[item.name] = val;
                                renderMenu();
                            });
                            
                            var plusBtn = document.createElement("button");
                            plusBtn.className = "btn-qty";
                            plusBtn.textContent = "+";
                            plusBtn.disabled = isPlusDisabled;
                            plusBtn.style.opacity = isPlusDisabled ? "0.3" : "1";
                            plusBtn.addEventListener("click", function() { adjustQty(item.name, 1); });
                            
                            qtyDiv.appendChild(minusBtn);
                            qtyDiv.appendChild(qtySpan);
                            qtyDiv.appendChild(plusBtn);
                        }
                        
                        card.appendChild(info);
                        card.appendChild(qtyDiv);
                        container.appendChild(card);
                    } catch (err) {
                        console.error("Error rendering item: " + item.name, err);
                    }
                });
            });
            updateTotal();
        }

        function adjustQty(name, val) {
            var currentStock = inventoryStock[name] || 0;
            var target = (orderQty[name] || 0) + val;
            orderQty[name] = Math.max(0, Math.min(currentStock, target));
            renderMenu();
        }

        function updateTotal() {
            var totalQty = 0;
            var totalMoney = 0;
            for (var name in orderQty) {
                var qty = orderQty[name];
                if (qty > 0) {
                    totalQty += qty;
                    var item = menuItems.find(function(it) { return it.name === name; });
                    if (item) {
                        totalMoney += qty * item.price;
                    }
                }
            }
            if (window.otherReqText && window.otherReqText.trim() !== "") {
                totalQty += 1;
            }
            document.getElementById("total-amount").textContent = totalMoney.toLocaleString("vi-VN") + " VNĐ";
            document.getElementById("submit-order-btn").disabled = (totalQty === 0);
        }

        function submitOrder() {
            var phone = document.getElementById("order-phone").value.trim();
            var phoneRegex = /^(0|\+84|84)(3|5|7|8|9)[0-9]{8}$/;
            if (!phone || !phoneRegex.test(phone)) {
                alert("Vui lòng nhập số điện thoại di động Việt Nam hợp lệ (ví dụ: 0912345678, 84912345678 hoặc +84912345678) để đặt món!");
                document.getElementById("order-phone").focus();
                return;
            }

            var itemsList = [];
            menuItems.forEach(function(item) {
                var qty = orderQty[item.name] || 0;
                var isOtherReq = (item.name === "Yêu cầu khác" && window.otherReqText.trim() !== "");
                
                if (qty > 0 || isOtherReq) {
                    var finalName = item.name;
                    if (isOtherReq) {
                        finalName = "Yêu cầu khác: " + window.otherReqText.trim();
                        qty = 1;
                    }
                    itemsList.push({
                        item_name: finalName,
                        quantity: qty,
                        price: item.price
                    });
                }
            });

            var note = document.getElementById("order-note").value;
            var btn = document.getElementById("submit-order-btn");
            btn.disabled = true;
            btn.textContent = "Đang gửi...";

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/api/customer-order/" + tableId, true);
            xhr.setRequestHeader("Content-Type", "application/json");
            xhr.onload = function() {
                if (xhr.status === 200) {
                    localStorage.setItem("customer_phone", phone);
                    document.getElementById("success-overlay").style.display = "flex";
                    try {
                        var actx = new (window.AudioContext || window.webkitAudioContext)();
                        var o = actx.createOscillator();
                        var g = actx.createGain();
                        o.connect(g); g.connect(actx.destination);
                        o.type = "sine"; o.frequency.value = 1046.50;
                        g.gain.setValueAtTime(0.2, actx.currentTime);
                        g.gain.exponentialRampToValueAtTime(0.001, actx.currentTime + 0.4);
                        o.start(actx.currentTime); o.stop(actx.currentTime + 0.4);
                    } catch(e) {}
                } else {
                    var err = JSON.parse(xhr.responseText);
                    alert("Lỗi: " + err.message);
                    btn.disabled = false;
                    btn.textContent = "🛒 Gửi yêu cầu gọi món";
                }
            };
            xhr.send(JSON.stringify({ items: itemsList, note: note, phone: phone }));
        }

        function resetMenu() {
            var btn = document.getElementById("submit-order-btn");
            btn.disabled = true;
            btn.textContent = "🛒 Gửi yêu cầu gọi món";
            window.location.reload();
        }

        renderCategories();
        renderMenu();

        var orderHistory = {order_history_json};
        var historySection = document.getElementById("order-history-section");
        if (orderHistory && orderHistory.length > 0) {
            historySection.style.display = "block";
            var hHtml = "";
            orderHistory.forEach(function(h) {
                hHtml += "<div style='display: flex; justify-content: space-between;'><span style='font-weight: 600;'><span style='color: #fbbf24;'>" + h.qty + "x</span> " + h.name + "</span><b style='color: white; font-variant-numeric: tabular-nums;'>" + h.total.toLocaleString("vi-VN") + " đ</b></div>";
            });
            document.getElementById("order-history-list").innerHTML = hHtml;
        }
    </script>
</body>
</html>"""

@app.get("/menu/{table_id}")
async def customer_menu(table_id: int):
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return HTMLResponse(content="<h1>Bàn không tồn tại</h1>", status_code=404)
            
        import json
        products = db.query(Product).all()
        stock_json = json.dumps({p.name: p.stock for p in products})
        
        # Load db products
        db_products = []
        for p in products:
            db_products.append({
                "name": p.name,
                "price": p.price,
                "category": p.category,
                "image_url": getattr(p, "image_url", ""),
                "stock": p.stock
            })
            
        # Append fixed service requests
        db_products.extend([
            { "name": "Lấy lơ", "price": 0, "category": "Yêu cầu nghiệp vụ" },
            { "name": "Xếp bi", "price": 0, "category": "Yêu cầu nghiệp vụ" },
            { "name": "Quét bàn", "price": 0, "category": "Yêu cầu nghiệp vụ" },
            { "name": "Yêu cầu khác", "price": 0, "category": "Yêu cầu nghiệp vụ" }
        ])
        dynamic_menu_json = json.dumps(db_products)
        
        # Lấy thời gian chơi của bàn
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        active_start_time = "None"
        ordered_items = []
        if active_session:
            active_start_time = active_session.start_time.isoformat() + "Z"
            items_db = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == active_session.id).all()
            for item in items_db:
                ordered_items.append({
                    "name": item.item_name,
                    "qty": item.quantity,
                    "total": item.total_price
                })
            
        rendered_html = customer_menu_html.replace("{table_id}", str(table_id))\
                                          .replace("{table_name}", table.name)\
                                          .replace("{inventory_stock_json}", stock_json)\
                                          .replace("{dynamic_menu_json}", dynamic_menu_json)\
                                          .replace("{active_start_time}", active_start_time)\
                                          .replace("{order_history_json}", json.dumps(ordered_items))
        return HTMLResponse(content=rendered_html)
    finally:
        db.close()

@app.post("/api/customer-order/{table_id}")
async def customer_order(table_id: int, payload: dict):
    items = payload.get("items", [])
    note = payload.get("note", "").strip()
    phone = payload.get("phone", "").strip()
    if not items:
        return JSONResponse({"status": "error", "message": "Giỏ hàng trống"}, status_code=400)
        
    import re
    try:
        import datetime
        with open("phone_debug.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now()}] Table: {table_id}, Phone: {repr(phone)}, Note: {repr(note)}\n")
    except Exception:
        pass
        
    if not phone or not re.match(r"^(0|\+84|84)[35789]\d{8}$", phone):
        return JSONResponse({"status": "error", "message": "Số điện thoại Việt Nam không hợp lệ (hỗ trợ định dạng 09..., 84..., +84...)!"}, status_code=400)
        
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Bàn không tồn tại"}, status_code=404)
        if table.current_status != "PLAYING":
            return JSONResponse({"status": "error", "message": "Bàn chưa được bắt đầu tính giờ chơi. Vui lòng báo nhân viên bật bàn trước!"}, status_code=400)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bật chơi. Vui lòng báo nhân viên bật bàn trước!"}, status_code=400)
            
        # 1. Tu dong nap luon vao hoa don va tru ton kho
        for item in items:
            item_name = item.get("item_name", "").strip()
            quantity = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            
            if not item_name or quantity <= 0 or price < 0:
                continue
                
            is_service = price == 0 and (item_name in ["Lấy lơ", "Xếp bi", "Quét bàn"] or item_name.startswith("Yêu cầu khác"))
            if is_service:
                continue  # Bỏ qua lưu vào CSDL, giữ nguyên trong list items để gửi thông báo

            # Khau tru ton kho tu SQL database
            product = db.query(Product).filter(Product.name == item_name).first()
            if not product:
                return JSONResponse({"status": "error", "message": f"Món {item_name} không tồn tại!"}, status_code=400)
                
            if quantity > product.stock:
                return JSONResponse({"status": "error", "message": f"Món {item_name} không đủ tồn kho (chỉ còn {product.stock} sản phẩm)!"}, status_code=400)
                
            product.stock -= quantity
                
            # Kiem tra trung lap trong bill
            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == active_session.id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=active_session.id,
                    product_id=product.id,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
                
        db.commit()
        
        # 2. Gui canh bao realtime de phuc vu
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        import time
        has_paid_item = any(float(item.get("price", 0)) > 0 for item in items)
        message_text = f"Khách {table.name} vừa gọi đồ (Đã tự động thêm vào Bill)!" if has_paid_item else f"Khách {table.name} đã yêu cầu:"
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "CUSTOMER_ORDER",
            "message": message_text,
            "items": items,
            "note": note,
            "phone": phone
        }
        r.set('latest_ai_event', json.dumps(event_data))
        response_msg = "Đã tự động ghi nhận và thêm món vào hóa đơn bàn!" if has_paid_item else "Đã gửi yêu cầu đến nhân viên!"
        return JSONResponse({"status": "ok", "message": response_msg})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/session/add-items/{table_id}")
async def add_multiple_items_to_session(table_id: int, payload: dict):
    items = payload.get("items", [])
    if not items:
        return JSONResponse({"status": "error", "message": "Danh sách món trống"}, status_code=400)
        
    db = SessionLocal()
    try:
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Bàn chưa được bật chơi"}, status_code=400)
            
        for item in items:
            item_name = item.get("item_name", "").strip()
            quantity = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            
            if not item_name or quantity <= 0 or price < 0:
                continue
                
            # Khấu trừ tồn kho
            product = db.query(Product).filter(Product.name == item_name).first()
            if product:
                if quantity > product.stock:
                    return JSONResponse({"status": "error", "message": f"Món {item_name} không đủ tồn kho (chỉ còn {product.stock} sản phẩm)!"}, status_code=400)
                product.stock -= quantity
                
            # Kiểm tra trùng lặp
            existing_item = db.query(SessionOrderItem).filter(
                SessionOrderItem.session_id == active_session.id,
                SessionOrderItem.item_name == item_name
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
                existing_item.total_price = existing_item.quantity * existing_item.price
            else:
                new_item = SessionOrderItem(
                    session_id=active_session.id,
                    product_id=product.id if product else None,
                    item_name=item_name,
                    quantity=quantity,
                    price=price,
                    total_price=quantity * price
                )
                db.add(new_item)
                
        db.commit()
        return JSONResponse({"status": "ok", "message": "Đã phê duyệt và thêm món vào hóa đơn"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.get("/api/poll")
async def poll_events():
    try:
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        data = r.get("latest_ai_event")
        if data:
            return HTMLResponse(content=data.decode('utf-8'), media_type="application/json")
    except Exception:
        pass
    return HTMLResponse(content="{}", media_type="application/json")

@app.get("/api/tables")
async def list_tables():
    """Liet ke tat ca ban bida kem voi phien choi hien tai va order items"""
    db = SessionLocal()
    try:
        tables = db.query(BilliardTable).order_by(BilliardTable.id).all()
        result = []
        for t in tables:
            active_session = db.query(PlaySession).filter(
                PlaySession.table_id == t.id, 
                PlaySession.status == "ACTIVE"
            ).first()
            
            session_data = None
            if active_session:
                items = db.query(SessionOrderItem).filter(
                    SessionOrderItem.session_id == active_session.id
                ).all()
                items_list = []
                for item in items:
                    items_list.append({
                        "id": item.id,
                        "item_name": item.item_name,
                        "quantity": item.quantity,
                        "price": item.price,
                        "total_price": item.total_price
                    })
                
                session_data = {
                    "id": active_session.id,
                    "start_time": active_session.start_time.isoformat() + "Z",
                    "order_items": items_list
                }
                
            result.append({
                "id": t.id,
                "name": t.name,
                "camera_url": t.camera_url,
                "current_status": t.current_status,
                "price_per_hour": t.price_per_hour,
                "table_tier": t.table_tier,
                "table_type": t.table_type,
                "active_session": session_data
            })
        return JSONResponse(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/session/start/{table_id}")
async def start_session(table_id: int):
    """Nhan vien bat dau bam start de tinh gio va mo ban"""
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
        if table.current_status == "PLAYING":
            return JSONResponse({"status": "error", "message": "Ban dang choi roi"}, status_code=400)
            
        table.current_status = "PLAYING"
        new_session = PlaySession(table_id=table_id)
        db.add(new_session)
        db.commit()
        
        # Phat tin hieu Redis
        import time
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "TABLE_ACTIVE",
            "message": f"Nhan vien da bat dau tinh gio cho {table.name}."
        }
        r.set('latest_ai_event', json.dumps(event_data))
        
        return JSONResponse({"status": "ok", "message": f"Da bat dau tinh gio {table.name}"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/session/add-item/{table_id}")
async def add_item_to_session(table_id: int, payload: dict):
    """Goi nuoc, do an nhe vao ban bida"""
    item_name = payload.get("item_name", "").strip()
    quantity = int(payload.get("quantity", 1))
    price = float(payload.get("price", 0))
    
    if not item_name or quantity <= 0 or price < 0:
        return JSONResponse({"status": "error", "message": "Du lieu mon an khong hop le"}, status_code=400)
        
    db = SessionLocal()
    try:
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Ban chua duoc bat tinh gio"}, status_code=400)
            
        # Kiem tra xem mon da duoc goi trong phien choi nay chua
        existing_item = db.query(SessionOrderItem).filter(
            SessionOrderItem.session_id == active_session.id,
            SessionOrderItem.item_name == item_name
        ).first()
        
        if existing_item:
            existing_item.quantity += quantity
            existing_item.total_price = existing_item.quantity * existing_item.price
        else:
            new_item = SessionOrderItem(
                session_id=active_session.id,
                item_name=item_name,
                quantity=quantity,
                price=price,
                total_price=quantity * price
            )
            db.add(new_item)
            
        db.commit()
        return JSONResponse({"status": "ok", "message": f"Da them mon vao ban"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/session/stop/{table_id}")
async def stop_session(table_id: int):
    """Dung choi, chot gio, tinh tong bill dien nuoc va gio choi"""
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
            
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id,
            PlaySession.status == "ACTIVE"
        ).first()
        
        if not active_session:
            return JSONResponse({"status": "error", "message": "Ban khong co phien choi nao dang hoat dong"}, status_code=400)
            
        end_time = datetime.utcnow()
        active_session.end_time = end_time
        diff = end_time - active_session.start_time
        total_minutes = math.ceil(diff.total_seconds() / 60)
        active_session.total_minutes = total_minutes
        
        play_fee = (total_minutes / 60) * table.price_per_hour
        active_session.play_fee = play_fee
        active_session.status = "COMPLETED"
        table.current_status = "EMPTY"
        
        # Doc danh sach mon
        items = db.query(SessionOrderItem).filter(SessionOrderItem.session_id == active_session.id).all()
        items_detail = []
        service_total = 0.0
        for item in items:
            items_detail.append({
                "item_name": item.item_name,
                "quantity": item.quantity,
                "price": item.price,
                "total_price": item.total_price
            })
            service_total += item.total_price
            
        total_bill = play_fee + service_total
        db.commit()
        
        # Phat tin hieu sang Redis
        import time
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "TABLE_EMPTY",
            "message": f"Nhan vien da thanh toan cho {table.name}. Tong bill: {int(total_bill):,} d."
        }
        r.set('latest_ai_event', json.dumps(event_data))
        
        return JSONResponse({
            "status": "ok",
            "table_name": table.name,
            "start_time": active_session.start_time.isoformat() + "Z",
            "end_time": end_time.isoformat() + "Z",
            "total_minutes": total_minutes,
            "play_fee": play_fee,
            "items": items_detail,
            "service_total": service_total,
            "total_bill": total_bill
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.get("/api/table-status/{table_id}")
async def get_table_status(table_id: int):
    """Kiem tra trang thai ban"""
    db = SessionLocal()
    try:
        table = db.query(BilliardTable).filter(BilliardTable.id == table_id).first()
        if not table:
            return JSONResponse({"status": "error", "message": "Khong tim thay ban"}, status_code=404)
        
        active_session = db.query(PlaySession).filter(
            PlaySession.table_id == table_id, 
            PlaySession.status == "ACTIVE"
        ).first()
        
        if active_session:
            start_iso = active_session.start_time.isoformat() + "Z"
            return JSONResponse({
                "status": "PLAYING",
                "start_time": start_iso,
                "table_name": table.name
            })
        else:
            return JSONResponse({
                "status": "EMPTY",
                "table_name": table.name
            })
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        db.close()

@app.post("/api/clip/{table_id}")
async def request_clip(table_id: int):
    """Nhan vien bam nut -> Gui lenh cat clip cho Worker"""
    try:
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        r.set(f"clip_request_{table_id}", "1")
        return JSONResponse({"status": "ok", "message": f"Dang cat clip cho Ban {table_id}..."})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/clip-status/{table_id}")
async def clip_status(table_id: int):
    """Kiem tra clip da san sang tai ve chua"""
    try:
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        clip_name = r.get(f"clip_ready_{table_id}")
        if clip_name:
            filename = clip_name.decode('utf-8')
            filepath = os.path.join(CLIPS_DIR, filename)
            if os.path.exists(filepath):
                r.delete(f"clip_ready_{table_id}")
                return JSONResponse({"status": "ready", "url": f"/clips/{filename}", "filename": filename})
        return JSONResponse({"status": "processing"})
    except Exception:
        return JSONResponse({"status": "processing"})

@app.post("/api/highlight-past/{table_id}")
async def request_past_highlight(table_id: int, payload: dict):
    """Trich xuat clip tu kho luu tru theo phut trong qua khu (Time Machine)"""
    time_str = payload.get("time", "").replace(":", "").strip() # VD: "14:30" -> "1430"
    if not time_str or len(time_str) != 4 or not time_str.isdigit():
        return JSONResponse({"status": "error", "message": "Dinh dang thoi gian khong hop le. Vi du: 14:30"}, status_code=400)
        
    archive_filename = f"ban{table_id}_{time_str}.mp4"
    archive_filepath = os.path.join(ARCHIVE_DIR, archive_filename)
    
    if not os.path.exists(archive_filepath):
        return JSONResponse({
            "status": "error", 
            "message": f"Khong tim thay video luc {payload.get('time')}. He thong chi luu 30 phut gan nhat!"
        }, status_code=404)
        
    # Copy sang thu muc clips de san sang download
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_filename = f"past_highlight_ban{table_id}_{time_str}_{timestamp}.mp4"
    dest_filepath = os.path.join(CLIPS_DIR, dest_filename)
    
    try:
        shutil.copy(archive_filepath, dest_filepath)
        size_mb = os.path.getsize(dest_filepath) / (1024 * 1024)
        
        # Phat su kien de hien len danh sach thong bao
        import time
        event_data = {
            "id": f"evt_{time.time()}",
            "table_id": table_id,
            "event_type": "CLIP_READY",
            "confidence": 1.0,
            "message": f"Clip Highlight luc {payload.get('time')} Ban {table_id} da san sang!",
            "clip_url": f"/clips/{dest_filename}",
            "image": ""
        }
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        r.set('latest_ai_event', json.dumps(event_data))
        
        return JSONResponse({
            "status": "ready",
            "url": f"/clips/{dest_filename}",
            "filename": dest_filename,
            "size_mb": round(size_mb, 2)
        })
    except Exception as e:
        return JSONResponse({"status": "error", "message": f"Loi copy video: {str(e)}"}, status_code=500)

@app.delete("/api/clip/{filename}")
async def delete_clip(filename: str):
    """Xoa file clip highlight"""
    filepath = os.path.join(CLIPS_DIR, filename)
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return JSONResponse({"status": "ok", "message": f"Da xoa clip {filename}"})
        except Exception as e:
            return JSONResponse({"status": "error", "message": f"Loi khi xoa file: {str(e)}"}, status_code=500)
    return JSONResponse({"status": "error", "message": "File khong ton tai"}, status_code=404)

@app.get("/api/live/{table_id}")
async def get_live_frame(table_id: int):
    """Doc raw JPEG bytes tu Redis va serve truc tiep len web (tranh file locking tren Windows)"""
    try:
        r = redis_lib.Redis(host='localhost', port=6379, db=0)
        img_data = r.get(f"live_frame_{table_id}")
        if img_data:
            return Response(content=img_data, media_type="image/jpeg")
    except Exception:
        pass
    return Response(status_code=404)

@app.get("/api/clips")
async def list_clips():
    """Liet ke tat ca clip da luu"""
    clips = []
    for f in sorted(os.listdir(CLIPS_DIR), reverse=True):
        if f.endswith(".mp4"):
            filepath = os.path.join(CLIPS_DIR, f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            clips.append({"filename": f, "url": f"/clips/{f}", "size_mb": round(size_mb, 2)})
    return JSONResponse(clips)

@app.websocket("/ws/admin")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
# Trigger reload to initialize MySQL db

