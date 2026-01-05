from flask import Flask, render_template, redirect, url_for, request, send_file, flash, jsonify, session
from jinja2 import DictLoader
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO, StringIO
from datetime import datetime, date, timedelta
import uuid
from functools import wraps
import csv
import shutil
import hashlib

# Add for charts
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import base64

app = Flask(__name__)
app.secret_key = 'school-management-system-secret-key-2024'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_IMAGE_EXTENSIONS'] = ['PNG', 'JPG', 'JPEG', 'GIF', 'SVG']
app.config['LOGO_FOLDER'] = 'static/logos'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Role-based access control decorator
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page', 'error')
                return redirect(url_for('login'))
            
            if session.get('role') not in roles:
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# Helper function to check allowed file extensions
def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].upper() in app.config['ALLOWED_IMAGE_EXTENSIONS']

# All templates stored in a dictionary
templates = {
    'base.html': '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>School Management System</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
  :root {
    --primary-color: #4361ee;
    --secondary-color: #3f37c9;
    --accent-color: #4cc9f0;
    --success-color: #4ade80;
    --warning-color: #facc15;
    --danger-color: #f87171;
    --dark-color: #1e293b;
    --light-color: #f8fafc;
    --gray-light: #e2e8f0;
    --gray-medium: #94a3b8;
    --sidebar-width-collapsed: 80px;
    --sidebar-width-expanded: 250px;
    --transition-speed: 0.3s;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  body {
    margin: 0;
    background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
    color: var(--dark-color);
    transition: all var(--transition-speed);
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    width: var(--sidebar-width-expanded);
    background: linear-gradient(to bottom, #1e293b, #0f172a);
    display: flex;
    flex-direction: column;
    padding-top: 20px;
    box-shadow: var(--shadow-lg);
    z-index: 1000;
    transition: all var(--transition-speed);
  }

  .sidebar.collapsed {
    width: var(--sidebar-width-collapsed);
  }

  .sidebar-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 10px 5px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 20px;
  }

  .sidebar.collapsed .sidebar-header {
    padding: 15px 5px;
  }

  .sidebar h2 {
    color: white;
    font-size: 1.2rem;
    text-align: center;
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sidebar.collapsed h2 {
    display: none;
  }

  .toggle-btn {
    background: var(--primary-color);
    border: none;
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: all var(--transition-speed);
  }

  .toggle-btn:hover {
    background: #3b5bdb;
    transform: scale(1.05);
  }

  .sidebar a {
    padding: 14px 20px;
    text-decoration: none;
    font-size: 1rem;
    color: white;
    display: flex;
    align-items: center;
    transition: all 0.3s;
    border-left: 4px solid transparent;
    white-space: nowrap;
  }

  .sidebar a i {
    margin-right: 12px;
    font-size: 1.2rem;
    min-width: 24px;
    text-align: center;
  }

  .sidebar.collapsed a span {
    display: none;
  }

  .sidebar.collapsed a {
    justify-content: center;
    padding: 16px 10px;
  }

  .sidebar a:hover {
    background-color: rgba(255,255,255,0.1);
    border-left: 4px solid var(--accent-color);
  }

  .sidebar a.active {
    background-color: rgba(76, 201, 240, 0.2);
    border-left: 4px solid var(--accent-color);
  }

  .content {
    margin-left: var(--sidebar-width-expanded);
    padding: 20px;
    min-height: 100vh;
    transition: all var(--transition-speed);
  }

  .sidebar.collapsed ~ .content {
    margin-left: var(--sidebar-width-collapsed);
  }

  h1 {
    color: var(--dark-color);
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 10px;
    margin-bottom: 20px;
    font-weight: 600;
  }

  .card {
    background: white;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    padding: 24px;
    margin-bottom: 20px;
    transition: transform 0.2s;
  }

  .card:hover {
    transform: translateY(-3px);
    box-shadow: var(--shadow-lg);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    background-color: #fff;
    margin-bottom: 20px;
    box-shadow: var(--shadow-sm);
    border-radius: 8px;
    overflow: hidden;
  }

  th, td {
    padding: 14px 16px;
    border: 1px solid var(--gray-light);
    text-align: left;
  }

  th {
    background-color: #f1f5f9;
    font-weight: 600;
    color: #334155;
  }

  tr:nth-child(even) {
    background-color: #f8fafc;
  }

  tr:hover {
    background-color: #f1f5f9;
  }

  a.button, button.button {
    display: inline-flex;
    align-items: center;
    margin: 5px;
    padding: 10px 20px;
    background-color: var(--primary-color);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: all 0.3s;
    font-size: 14px;
    font-weight: 500;
    gap: 8px;
  }

  a.button:hover, button.button:hover {
    background-color: #3b5bdb;
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  a.button i, button.button i {
    font-size: 1rem;
  }

  a.button.secondary {
    background-color: var(--secondary-color);
  }

  a.button.secondary:hover {
    background-color: #3830a9;
  }

  a.button.danger {
    background-color: var(--danger-color);
  }

  a.button.danger:hover {
    background-color: #ef4444;
  }

  a.button.warning {
    background-color: var(--warning-color);
    color: #1e293b;
  }

  a.button.warning:hover {
    background-color: #eab308;
  }

  form input[type=text], form input[type=number], form input[type=date], form input[type=email], form input[type=tel], form input[type=password], form select, form textarea {
    padding: 12px 15px;
    margin: 8px 0;
    width: 100%;
    box-sizing: border-box;
    border: 2px solid var(--gray-light);
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.3s;
  }

  form input:focus, form select:focus, form textarea:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
  }

  img.passport {
    max-width: 100px;
    max-height: 100px;
    border-radius: 8px;
    border: 2px solid var(--gray-light);
    object-fit: cover;
  }

  .status-present { color: var(--success-color); font-weight: bold; }
  .status-absent { color: var(--danger-color); font-weight: bold; }
  .status-late { color: var(--warning-color); font-weight: bold; }
  .status-excused { color: var(--accent-color); font-weight: bold; }

  .alert {
    padding: 16px 20px;
    margin: 15px 0;
    border-radius: 8px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .alert i {
    font-size: 1.2rem;
  }

  .alert-success {
    background-color: #dcfce7;
    color: #166534;
    border: 1px solid #bbf7d0;
  }

  .alert-error {
    background-color: #fecaca;
    color: #991b1b;
    border: 1px solid #fecaca;
  }

  .alert-warning {
    background-color: #fef3c7;
    color: #92400e;
    border: 1px solid #fde68a;
  }

  .filter-form {
    background-color: #f1f5f9;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-sm);
  }

  .filter-form label {
    display: inline-block;
    margin-right: 10px;
    font-weight: 600;
    margin-bottom: 5px;
    color: #334155;
  }

  .filter-form input, .filter-form select {
    margin-right: 20px;
    margin-bottom: 10px;
    padding: 10px 15px;
  }

  .receipt {
    border: 1px solid var(--gray-light);
    padding: 30px;
    margin: 20px auto;
    background-color: white;
    max-width: 800px;
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
  }

  .receipt-header {
    text-align: center;
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 20px;
    margin-bottom: 30px;
  }

  .receipt-header h2 {
    color: var(--dark-color);
    margin: 0;
  }

  .receipt-details {
    margin: 20px 0;
    width: 100%;
  }

  .receipt-details td {
    padding: 10px 15px;
    vertical-align: top;
  }

  .receipt-details tr:nth-child(even) {
    background-color: #f8fafc;
  }

  .balance {
    font-weight: bold;
    color: #dc2626;
    font-size: 1.1em;
  }

  .paid {
    font-weight: bold;
    color: #16a34a;
    font-size: 1.1em;
  }

  .total-row {
    border-top: 2px solid var(--dark-color);
    font-weight: bold;
    font-size: 1.1em;
  }

  .dashboard-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin: 30px 0;
  }

  .stat-card {
    background: white;
    padding: 24px;
    border-radius: 12px;
    text-align: center;
    box-shadow: var(--shadow-md);
    transition: transform 0.3s;
    border-top: 4px solid var(--primary-color);
  }

  .stat-card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
  }

  .stat-card h3 {
    margin: 0 0 10px 0;
    color: #64748b;
    font-size: 14px;
    text-transform: uppercase;
    font-weight: 600;
  }

  .stat-card .value {
    font-size: 32px;
    font-weight: 700;
    color: var(--primary-color);
  }

  .action-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 20px 0;
  }

  .search-box {
    margin: 20px 0;
    padding: 15px;
    background: white;
    border-radius: 12px;
    box-shadow: var(--shadow-sm);
  }

  .search-box input {
    width: 300px;
    max-width: 100%;
    padding: 12px 15px;
  }

  .print-only {
    display: none;
  }

  @media print {
    .sidebar, .button, .no-print {
      display: none !important;
    }
    .content {
      margin-left: 0 !important;
      padding: 0 !important;
    }
    .print-only {
      display: block;
    }
    .receipt {
      border: none;
      box-shadow: none;
      margin: 0;
      padding: 0;
    }
    .timetable {
      border: none !important;
      box-shadow: none !important;
    }
    .timetable th, .timetable td {
      border: 1px solid #000 !important;
    }
  }

  .form-group {
    margin-bottom: 18px;
  }

  .form-group label {
    display: block;
    margin-bottom: 6px;
    font-weight: 600;
    color: #334155;
  }

  .badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin: 2px;
  }

  .badge-success { background-color: #dcfce7; color: #166534; }
  .badge-warning { background-color: #fef3c7; color: #92400e; }
  .badge-danger { background-color: #fecaca; color: #991b1b; }
  .badge-info { background-color: #dbeafe; color: #1d4ed8; }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--gray-light);
    margin-bottom: 20px;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
  }

  .tab {
    padding: 12px 24px;
    cursor: pointer;
    border: none;
    background: none;
    font-size: 16px;
    color: #64748b;
    font-weight: 500;
    transition: all 0.3s;
  }

  .tab:hover {
    background-color: #f1f5f9;
  }

  .tab.active {
    color: var(--primary-color);
    background-color: #eff6ff;
    border-bottom: 3px solid var(--primary-color);
  }

  .tab-content {
    display: none;
  }

  .tab-content.active {
    display: block;
  }

  .grade-A { color: #22c55e; font-weight: bold; }
  .grade-B { color: #2563eb; font-weight: bold; }
  .grade-C { color: #f59e0b; font-weight: bold; }
  .grade-D { color: #f97316; font-weight: bold; }
  .grade-F { color: #ef4444; font-weight: bold; }

  .report-card {
    border: 1px solid var(--gray-light);
    padding: 30px;
    margin: 20px auto;
    background-color: white;
    max-width: 1000px;
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
  }

  .report-header {
    text-align: center;
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 20px;
    margin-bottom: 30px;
  }

  .performance-summary {
    background: #f1f5f9;
    padding: 20px;
    border-radius: 12px;
    margin: 20px 0;
  }

  /* Timetable Styles */
  .timetable {
    width: 100%;
    border-collapse: separate;
    border-spacing: 4px;
    margin: 20px 0;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-md);
  }

  .timetable th {
    background:skyblue;
    color: white;
    padding: 16px;
    text-align: center;
    font-weight: 600;
    border-radius: 8px 8px 0 0;
  }

  .timetable td {
    padding: 8px;
    border-radius: 8px;
    vertical-align: top;
    height: 120px;
    background-color: #f8fafc;
    position: relative;
  }

  .timetable tr:first-child td {
    border-top: none;
  }

  .timetable .time-slot {
    background: #f1f5f9;
    font-weight: 600;
    text-align: center;
    width: 100px;
    padding: 10px;
    border-radius: 6px;
  }

  .timetable .period {
    border-radius: 8px;
    padding: 10px;
    margin: 3px 0;
    color: white;
    font-weight: 600;
    position: relative;
    min-height: 80px;
    border: 2px solid rgba(255,255, 255, 0.3);
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .timetable .period:hover {
    opacity: 0.95;
    transform: scale(1.02);
    cursor: pointer;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .period-empty {
    background: #f8fafc;
    color: #94a3b8;
    text-align: center;
    padding: 15px;
    border-radius: 8px;
    font-style: italic;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80px;
  }

  .subject-math { background: linear-gradient(135deg, #667eea, #764ba2); }
  .subject-english { background: linear-gradient(135deg, #f093fb, #f5576c); }
  .subject-science { background: linear-gradient(135deg, #4facfe, #00f2fe); }
  .subject-history { background: linear-gradient(135deg, #43e97b, #38f9d7); }
  .subject-geography { background: linear-gradient(135deg, #fa709a, #fee140); }
  .subject-physics { background: linear-gradient(135deg, #30cfd0, #330867); }
  .subject-chemistry { background: linear-gradient(135deg, #a8edea, #fed6e3); }
  .subject-biology { background: linear-gradient(135deg, #5ee7df, #b490ca); }
  .subject-computer { background: linear-gradient(135deg, #d299c2, #fef9d7); }
  .subject-art { background: linear-gradient(135deg, #f6d365, #fda085); }
  .subject-pe { background: linear-gradient(135deg, #a1c4fd, #c2e9fb); }
  .subject-music { background: linear-gradient(135deg, #ffecd2, #fcb69f); }
  .break-period {
    background: repeating-linear-gradient(45deg, #e0e7ff, #e0e7ff 10px, #c7d2fe 10px, #c7d2fe 20px);
    color: #4f46e5;
    text-align: center;
    font-weight: 600;
  }

  .period-details {
    font-size: 11px;
  }

  .period-details .subject {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 5px;
  }

  .period-details .teacher {
    font-size: 11px;
    opacity: 0.9;
  }

  .period-details .room {
    font-size: 10px;
    opacity: 0.85;
    background: rgba(0,0,0,0.2);
    padding: 2px 6px;
    border-radius: 4px;
    display: inline-block;
    margin-top: 3px;
  }

  .timetable-controls {
    background: white;
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 15px;
    align-items: center;
    box-shadow: var(--shadow-sm);
  }

  .timetable-controls select, .timetable-controls input {
    padding: 10px 15px;
    border: 2px solid var(--gray-light);
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.3s;
  }

  .timetable-controls select:focus, .timetable-controls input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.2);
  }

  .color-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin: 20px 0;
    padding: 18px;
    background: white;
    border-radius: 12px;
    box-shadow: var(--shadow-sm);
  }

  .color-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #f8fafc;
    border-radius: 6px;
    border: 1px solid var(--gray-light);
  }

  .color-box {
    width: 20px;
    height: 20px;
    border-radius: 4px;
  }

  .full-width {
    width: 100%;
  }

  .day-header {
    text-align: center;
    background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 10px;
    border-radius: 6px;
    margin-bottom: 5px;
  }

  .timetable-container {
    overflow-x: auto;
  }

  /* Loading animation styles */
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }

  .loading-overlay.show {
    opacity: 1;
    visibility: visible;
  }

  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 5px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .loading-text {
    color: white;
    margin-top: 10px;
    font-size: 16px;
    font-weight: 500;
  }

  /* Chart Styles */
  .chart-container {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    margin: 20px 0;
  }

  .chart-title {
    text-align: center;
    margin-bottom: 20px;
    color: var(--dark-color);
  }

  .chart-img {
    width: 100%;
    max-width: 800px;
    height: auto;
    display: block;
    margin: 0 auto;
    border-radius: 8px;
  }

  .chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 20px;
    margin: 20px 0;
  }

  /* School Logo Styles */
  .logo-container {
    text-align: center;
    margin: 20px 0;
  }

  .school-logo {
    max-width: 200px;
    max-height: 100px;
    object-fit: contain;
  }

  .logo-preview {
    border: 2px dashed var(--gray-light);
    padding: 20px;
    border-radius: 8px;
    margin: 15px 0;
    text-align: center;
  }

  .grading-system-table {
    width: 100%;
    margin: 20px 0;
  }

  .grading-system-table th {
    background: var(--primary-color);
    color: white;
  }

  .grade-color-box {
    width: 20px;
    height: 20px;
    display: inline-block;
    margin-right: 10px;
    border-radius: 4px;
    vertical-align: middle;
  }

  .grade-A-bg { background-color: #22c55e; }
  .grade-B-bg { background-color: #2563eb; }
  .grade-C-bg { background-color: #f59e0b; }
  .grade-D-bg { background-color: #f97316; }
  .grade-F-bg { background-color: #ef4444; }

  .performance-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin: 20px 0;
  }

  .metric-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: var(--shadow-sm);
    text-align: center;
  }

  .metric-value {
    font-size: 24px;
    font-weight: bold;
    color: var(--primary-color);
  }

  .metric-label {
    color: #64748b;
    font-size: 14px;
    margin-top: 5px;
  }

  .subject-performance {
    display: flex;
    align-items: center;
    gap: 15px;
    margin: 10px 0;
    padding: 10px;
    background: #f8fafc;
    border-radius: 6px;
  }

  .subject-name {
    min-width: 150px;
    font-weight: 600;
  }

  .score-bar {
    flex: 1;
    height: 20px;
    background: #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
    position: relative;
  }

  .score-fill {
    height: 100%;
    border-radius: 10px;
    transition: width 0.5s ease;
  }

  .score-text {
    position: absolute;
    right: 10px;
    top: 0;
    line-height: 20px;
    font-size: 12px;
    font-weight: 600;
  }

  /* Login Styles */
  .login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #4361ee, #3a0ca3);
  }

  .login-card {
    background: white;
    padding: 40px;
    border-radius: 16px;
    box-shadow: var(--shadow-lg);
    width: 100%;
    max-width: 400px;
    margin: 20px;
  }

  .login-card h2 {
    text-align: center;
    margin-bottom: 30px;
    color: var(--dark-color);
  }

  .login-logo {
    text-align: center;
    margin-bottom: 30px;
  }

  .login-logo img {
    max-width: 150px;
  }

  .password-toggle {
    position: relative;
  }

  .password-toggle input {
    padding-right: 40px;
  }

  .password-toggle .toggle-icon {
    position: absolute;
    right: 15px;
    top: 50%;
    transform: translateY(-50%);
    cursor: pointer;
    color: var(--gray-medium);
  }

  /* User info in sidebar */
  .user-info {
    padding: 15px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 10px;
  }

  .user-avatar {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: var(--accent-color);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 10px;
    color: white;
    font-size: 20px;
  }

  .user-name {
    color: white;
    font-weight: 600;
    margin-bottom: 5px;
  }

  .user-role {
    color: rgba(255,255,255,0.8);
    font-size: 12px;
    background: rgba(255,255,255,0.1);
    padding: 3px 8px;
    border-radius: 10px;
    display: inline-block;
  }

  /* Medical alert styles */
  .medical-alert {
    background-color: #fef3c7;
    border-left: 4px solid #f59e0b;
    padding: 12px 16px;
    margin: 10px 0;
    border-radius: 4px;
  }

  .medical-alert.danger {
    background-color: #fecaca;
    border-left-color: #ef4444;
  }

  .medical-alert.info {
    background-color: #dbeafe;
    border-left-color: #3b82f6;
  }

  .medical-badge {
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    margin-left: 5px;
  }

  .medical-badge.condition {
    background-color: #fef3c7;
    color: #92400e;
  }

  .medical-badge.emergency {
    background-color: #fee2e2;
    color: #991b1b;
  }

  .medical-badge.allergy {
    background-color: #f0f9ff;
    color: #0369a1;
  }

  /* Login button in sidebar */
  .logout-btn {
    margin-top: auto;
    margin-bottom: 20px;
    padding: 15px 20px;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: white;
    cursor: pointer;
    font-size: 14px;
    text-align: left;
    transition: all 0.3s;
    border-left: 4px solid transparent;
  }

  .logout-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    border-left: 4px solid var(--danger-color);
  }

  .logout-btn i {
    margin-right: 12px;
  }

  /* Profile dropdown */
  .profile-dropdown {
    position: relative;
  }

  .profile-menu {
    position: absolute;
    top: 100%;
    left: 0;
    background: white;
    box-shadow: var(--shadow-lg);
    border-radius: 8px;
    min-width: 200px;
    z-index: 1000;
    display: none;
  }

  .profile-dropdown:hover .profile-menu {
    display: block;
  }

  .profile-menu a {
    padding: 12px 16px;
    color: var(--dark-color);
    text-decoration: none;
    display: block;
    border-bottom: 1px solid var(--gray-light);
  }

  .profile-menu a:hover {
    background: var(--gray-light);
  }

  .profile-menu a:last-child {
    border-bottom: none;
  }
</style>
<script>
  function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this?');
  }

  function toggleTabs(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const tabElement = document.querySelector(`[onclick*="${tabName}"]`);
    if (tabElement) tabElement.classList.add('active');
    const contentElement = document.getElementById(tabName);
    if (contentElement) contentElement.classList.add('active');
  }

  function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
      let match = false;
      const cells = rows[i].getElementsByTagName('td');
      for (let j = 0; j < cells.length; j++) {
        const cell = cells[j];
        if (cell) {
          if (cell.textContent.toUpperCase().indexOf(filter) > -1) {
            match = true;
            break;
          }
        }
      }
      rows[i].style.display = match ? '' : 'none';
    }
  }

  function printReceipt() {
    window.print();
  }

  function generateColor(subject) {
    if (!subject) return '#999999';

    const colorMap = {
      'mathematics': '#667eea',
      'english': '#f5576c',
      'science': '#4facfe',
      'history': '#43e97b',
      'geography': '#fee140',
      'physics': '#30cfd0',
      'chemistry': '#a8edea',
      'biology': '#5ee7df',
      'computer': '#d299c2',
      'art': '#f6d365',
      'physical education': '#a1c4fd',
      'pe': '#a1c4fd',
      'music': '#fcb69f',
      'business': '#c2e9fb',
      'religious': '#fed6e3'
    };

    subject = subject.toLowerCase().trim();
    for (const [key, color] of Object.entries(colorMap)) {
      if (subject.includes(key)) {
        return color;
      }
    }

    // Generate consistent color from subject name
    let hash = 0;
    for (let i = 0; i < subject.length; i++) {
      hash = subject.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = hash % 360;
    return `hsl(${hue}, 70%, 60%)`;
  }

  // Toggle sidebar function
  function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('collapsed');
  }

  // Show loading animation
  function showLoading(text = 'Loading...') {
    const overlay = document.querySelector('.loading-overlay');
    const textElement = overlay.querySelector('.loading-text');
    textElement.textContent = text;
    overlay.classList.add('show');
  }

  // Hide loading animation
  function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    overlay.classList.remove('show');
  }

  // Toggle password visibility
  function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.querySelector(`[onclick="togglePassword('${inputId}')"] i`);
    
    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }

  // Add loading animation to forms on submit
  document.addEventListener('DOMContentLoaded', function() {
    // Add sidebar toggle button
    const sidebar = document.querySelector('.sidebar');
    const sidebarHeader = document.createElement('div');
    sidebarHeader.className = 'sidebar-header';
    sidebarHeader.innerHTML = `
      <button class="toggle-btn" onclick="toggleSidebar()" title="Toggle Sidebar">
        <i class="fas fa-bars"></i>
      </button>
    `;
    sidebar.insertBefore(sidebarHeader, sidebar.firstChild);

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
      const alerts = document.querySelectorAll('.alert');
      alerts.forEach(alert => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.5s';
        setTimeout(() => alert.style.display = 'none', 500);
      });
    }, 5000);

    // Initialize timetable colors
    document.querySelectorAll('.period').forEach(period => {
      const subject = period.getAttribute('data-subject');
      if (subject) {
        const color = generateColor(subject);
        period.style.background = color;
      }
    });

    // Auto-select today in date inputs
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(input => {
      if (!input.value && (input.id.includes('date') || input.name.includes('date'))) {
        input.value = today;
      }
    });

    // Add loading animation to forms
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', function() {
        showLoading('Processing...');
      });
    });

    // Add loading for anchor links that might take time
    document.querySelectorAll('a').forEach(link => {
      if (link.href.includes('add_') || link.href.includes('edit_') || link.href.includes('delete_')) {
        link.addEventListener('click', function() {
          showLoading('Loading...');
          setTimeout(hideLoading, 1000); // Hide after 1 second
        });
      }
    });

    // Update score bars
    updateScoreBars();
  });

  function updateScoreBars() {
    document.querySelectorAll('.subject-performance').forEach(item => {
      const score = parseInt(item.getAttribute('data-score'));
      const grade = item.getAttribute('data-grade');
      const fill = item.querySelector('.score-fill');
      const text = item.querySelector('.score-text');
      
      if (fill && text) {
        fill.style.width = score + '%';
        
        // Set color based on grade
        if (grade === 'A') fill.style.background = '#22c55e';
        else if (grade === 'B') fill.style.background = '#2563eb';
        else if (grade === 'C') fill.style.background = '#f59e0b';
        else if (grade === 'D') fill.style.background = '#f97316';
        else fill.style.background = '#ef4444';
        
        text.textContent = score + '%';
      }
    });
  }

  // Initialize theme on page load
  document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = getCookie('selected_theme');
    if (savedTheme) {
      applyTheme(savedTheme, false); // Don't show confirmation on load
    }

    // Capture all form submissions to show loading
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', function(e) {
        // Only show loading if form action contains specific paths
        const action = form.getAttribute('action') || '';
        if (action.includes('add') || action.includes('edit') || action.includes('delete') || action.includes('process')) {
          showLoading('Processing request...');
        }
      });
    });
  });

  function applyTheme(themeName, showConfirmation = true) {
    const themeColors = {
      'modern-blue': {
        '--primary-color': '#4361ee',
        '--secondary-color': '#3a0ca3',
        '--accent-color': '#4cc9f0',
        '--dark-color': '#1e293b',
        '--light-color': '#f8fafc',
        '--gray-light': '#e2e8f0',
        '--sidebar-bg-start': '#1e293b',
        '--sidebar-bg-end': '#0f172a'
      },
      'elegant-green': {
        '--primary-color': '#2ecc71',
        '--secondary-color': '#27ae60',
        '--accent-color': '#1abc9c',
        '--dark-color': '#1e293b',
        '--light-color': '#f8fafc',
        '--gray-light': '#e2e8f0',
        '--sidebar-bg-start': '#1e293b',
        '--sidebar-bg-end': '#0f172a'
      },
      'sunset-orange': {
        '--primary-color': '#ff7e5f',
        '--secondary-color': '#feb47b',
        '--accent-color': '#f39c12',
        '--dark-color': '#1e293b',
        '--light-color': '#fff5f5',
        '--gray-light': '#f8f9fa',
        '--sidebar-bg-start': '#2c1810',
        '--sidebar-bg-end': '#1e120b'
      },
      'dusk-purple': {
        '--primary-color': '#654ea3',
        '--secondary-color': '#da98b4',
        '--accent-color': '#8e44ad',
        '--dark-color': '#1e293b',
        '--light-color': '#f8f0fc',
        '--gray-light': '#f0e6ff',
        '--sidebar-bg-start': '#2c0f3e',
        '--sidebar-bg-end': '#1c0928'
      },
      'forest-teal': {
        '--primary-color': '#11998e',
        '--secondary-color': '#38ef7d',
        '--accent-color': '#16a085',
        '--dark-color': '#1e293b',
        '--light-color': '#e8f8f5',
        '--gray-light': '#e8f6f3',
        '--sidebar-bg-start': '#0d3632',
        '--sidebar-bg-end': '#0a2824'
      },
      'light-theme': {
        '--primary-color': '#4f46e5',
        '--secondary-color': '#2563eb',
        '--accent-color': '#0ea5e9',
        '--dark-color': '#1f2937',
        '--light-color': '#ffffff',
        '--gray-light': '#e5e7eb',
        '--sidebar-bg-start': '#f9fafb',
        '--sidebar-bg-end': '#f3f4f6',
        '--sidebar-text': '#374151',
        '--sidebar-hover': '#e5e7eb'
      },
      'dark-theme': {
        '--primary-color': '#818cf8',
        '--secondary-color': '#60a5fa',
        '--accent-color': '#38bdf8',
        '--dark-color': '#f9fafb',
        '--light-color': '#111827',
        '--gray-light': '#374151',
        '--sidebar-bg-start': '#1f2937',
        '--sidebar-bg-end': '#111827',
        '--sidebar-text': '#d1d5db',
        '--sidebar-hover': '#374151'
      }
    };

    const colors = themeColors[themeName];
    if (colors) {
      // Apply CSS custom properties
      Object.entries(colors).forEach(([property, value]) => {
        document.documentElement.style.setProperty(property, value);
      });

      // Update sidebar styles for light/dark themes specifically
      const sidebar = document.querySelector('.sidebar');
      if (sidebar) {
        if (themeName === 'light-theme') {
          sidebar.style.background = 'linear-gradient(to bottom, #f9fafb, #f3f4f6)';
          const sidebarLinks = document.querySelectorAll('.sidebar a');
          sidebarLinks.forEach(link => {
            link.style.color = '#374151';
          });
          const sidebarH2 = document.querySelector('.sidebar h2');
          if (sidebarH2) sidebarH2.style.color = '#374151';
          const toggleBtn = document.querySelector('.toggle-btn');
          if (toggleBtn) toggleBtn.style.background = '#4f46e5';
        } else if (themeName === 'dark-theme') {
          sidebar.style.background = 'linear-gradient(to bottom, #1f2937, #111827)';
          const sidebarLinks = document.querySelectorAll('.sidebar a');
          sidebarLinks.forEach(link => {
            link.style.color = '#d1d5db';
          });
          const sidebarH2 = document.querySelector('.sidebar h2');
          if (sidebarH2) sidebarH2.style.color = '#d1d5db';
          const toggleBtn = document.querySelector('.toggle-btn');
          if (toggleBtn) toggleBtn.style.background = '#818cf8';
        } else {
          // Reset to default gradient for other themes
          sidebar.style.background = 'linear-gradient(to bottom, var(--sidebar-bg-start), var(--sidebar-bg-end))';
          const sidebarLinks = document.querySelectorAll('.sidebar a');
          sidebarLinks.forEach(link => {
            link.style.color = 'white';
          });
          const sidebarH2 = document.querySelector('.sidebar h2');
          if (sidebarH2) sidebarH2.style.color = 'white';
          const toggleBtn = document.querySelector('.toggle-btn');
          if (toggleBtn) toggleBtn.style.background = 'var(--primary-color)';
        }
      }

      // Save theme preference in cookie
      setCookie('selected_theme', themeName, 30); // 30 days expiry

      if (showConfirmation) {
        showThemeApplied(themeName);
      }
    }
  }

  function showThemeApplied(themeName) {
    // Create temporary alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.innerHTML = `<i class="fas fa-check-circle"></i> Theme "${themeName}" applied successfully!`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.opacity = '0';
    alertDiv.style.transition = 'opacity 0.5s';

    document.body.appendChild(alertDiv);

    // Fade in
    setTimeout(() => {
      alertDiv.style.opacity = '1';
    }, 10);

    // Remove after some time
    setTimeout(() => {
      alertDiv.style.opacity = '0';
      setTimeout(() => {
        document.body.removeChild(alertDiv);
      }, 500);
    }, 3000);
  }

  function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = name + '=' + value + ';expires=' + expires.toUTCString() + ';path=/';
  }

  function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for(let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
  }
</script>
</head>
<body>
<div class="loading-overlay">
  <div>
    <div class="loading-spinner"></div>
    <div class="loading-text">Loading...</div>
  </div>
</div>

{% if request.endpoint != 'login' %}
<div class="sidebar">
  <div class="user-info">
    <div class="user-avatar">
      <i class="fas fa-user"></i>
    </div>
    <div class="user-name">{{ session.username|default('User') }}</div>
    <div class="user-role">{{ session.role|default('Guest')|title }}</div>
  </div>
  
  <a href="{{ url_for('index') }}" {% if request.endpoint == 'index' %}class="active"{% endif %}>
    <i class="fas fa-tachometer-alt"></i> <span>Dashboard</span>
  </a>
  
  {% if session.role in ['admin', 'teacher'] %}
  <a href="{{ url_for('students') }}" {% if request.endpoint.startswith('student') %}class="active"{% endif %}>
    <i class="fas fa-users"></i> <span>Students</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin'] %}
  <a href="{{ url_for('teachers') }}" {% if request.endpoint.startswith('teacher') %}class="active"{% endif %}>
    <i class="fas fa-chalkboard-teacher"></i> <span>Teachers</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin', 'teacher'] %}
  <a href="{{ url_for('classes') }}" {% if request.endpoint.startswith('classes') or request.endpoint.startswith('class') %}class="active"{% endif %}>
    <i class="fas fa-school"></i> <span>Classes</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin'] %}
  <a href="{{ url_for('fees') }}" {% if request.endpoint.startswith('fee') %}class="active"{% endif %}>
    <i class="fas fa-money-bill-wave"></i> <span>Fees</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin', 'teacher'] %}
  <a href="{{ url_for('attendance') }}" {% if request.endpoint.startswith('attendance') %}class="active"{% endif %}>
    <i class="fas fa-clipboard-list"></i> <span>Attendance</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin', 'teacher'] %}
  <a href="{{ url_for('grades') }}" {% if request.endpoint.startswith('grade') %}class="active"{% endif %}>
    <i class="fas fa-chart-line"></i> <span>Grades</span>
  </a>
  {% endif %}
  
  {% if session.role in ['admin', 'teacher', 'student'] %}
  <a href="{{ url_for('timetable') }}" {% if request.endpoint.startswith('timetable') %}class="active"{% endif %}>
    <i class="fas fa-calendar-alt"></i> <span>Timetable</span>
  </a>
  {% endif %}
  
  {% if session.role == 'admin' %}
  <a href="{{ url_for('settings') }}" {% if request.endpoint.startswith('settings') %}class="active"{% endif %}>
    <i class="fas fa-cog"></i> <span>Settings</span>
  </a>
  <a href="{{ url_for('themes') }}" {% if request.endpoint == 'themes' %}class="active"{% endif %}>
    <i class="fas fa-palette"></i> <span>Themes</span>
  </a>
  <a href="{{ url_for('user_management') }}" {% if request.endpoint.startswith('user_management') %}class="active"{% endif %}>
    <i class="fas fa-user-cog"></i> <span>User Management</span>
  </a>
  {% endif %}
  
  {% if session.role == 'student' %}
  <a href="{{ url_for('student_dashboard') }}" {% if request.endpoint == 'student_dashboard' %}class="active"{% endif %}>
    <i class="fas fa-graduation-cap"></i> <span>My Dashboard</span>
  </a>
  <a href="{{ url_for('student_grades') }}" {% if request.endpoint == 'student_grades' %}class="active"{% endif %}>
    <i class="fas fa-chart-line"></i> <span>My Grades</span>
  </a>
  <a href="{{ url_for('student_attendance') }}" {% if request.endpoint == 'student_attendance' %}class="active"{% endif %}>
    <i class="fas fa-clipboard-list"></i> <span>My Attendance</span>
  </a>
  <a href="{{ url_for('student_fees') }}" {% if request.endpoint == 'student_fees' %}class="active"{% endif %}>
    <i class="fas fa-money-bill-wave"></i> <span>My Fees</span>
  </a>
  {% endif %}
  
  {% if session.role == 'teacher' %}
  <a href="{{ url_for('teacher_dashboard') }}" {% if request.endpoint == 'teacher_dashboard' %}class="active"{% endif %}>
    <i class="fas fa-chalkboard-teacher"></i> <span>Teacher Dashboard</span>
  </a>
  {% endif %}
  
  <button class="logout-btn" onclick="window.location.href='{{ url_for('logout') }}'">
    <i class="fas fa-sign-out-alt"></i> <span>Logout</span>
  </button>
</div>
{% endif %}

<div class="content">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}"><i class="fas fa-info-circle"></i> {{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  {% block content %}{% endblock %}
</div>
</body>
</html>''',

    'login.html': '''{% extends "base.html" %}
{% block content %}
<div class="login-container">
  <div class="login-card">
    <div class="login-logo">
      <h2>School Management System</h2>
    </div>
    
    <h2>Login to Your Account</h2>
    
    <form method="post" action="{{ url_for('login') }}">
      <div class="form-group">
        <label for="username">Username</label>
        <input type="text" id="username" name="username" required placeholder="Enter your username">
      </div>
      
      <div class="form-group">
        <label for="password">Password</label>
        <div class="password-toggle">
          <input type="password" id="password" name="password" required placeholder="Enter your password">
          <span class="toggle-icon" onclick="togglePassword('password')">
            <i class="fas fa-eye"></i>
          </span>
        </div>
      </div>
      
      <div class="form-group">
        <label for="role">Login As</label>
        <select id="role" name="role" required>
          <option value="">Select Role</option>
          <option value="admin">Administrator</option>
          <option value="teacher">Teacher</option>
          <option value="student">Student</option>
        </select>
      </div>
      
      <button type="submit" class="button full-width" style="margin-top: 20px;">
        <i class="fas fa-sign-in-alt"></i> Login
      </button>
      
      <div style="text-align: center; margin-top: 20px; color: #64748b;">
        <p>Default Admin: admin / school123</p>
      </div>
    </form>
  </div>
</div>

<script>
  function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.querySelector(`[onclick="togglePassword('${inputId}')"] i`);
    
    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }
</script>
{% endblock %}''',

    'user_management.html': '''{% extends "base.html" %}
{% block content %}
<h1>User Management</h1>

<div class="tabs">
  <button class="tab active" onclick="toggleTabs('manageUsers')">Manage Users</button>
  <button class="tab" onclick="toggleTabs('addUser')">Add New User</button>
  <button class="tab" onclick="toggleTabs('resetPassword')">Reset Password</button>
</div>

<div id="manageUsers" class="tab-content active">
  <div class="action-buttons">
    <a href="{{ url_for('user_management') }}?role=all" class="button {% if role_filter == 'all' %}active{% endif %}">All Users</a>
    <a href="{{ url_for('user_management') }}?role=student" class="button {% if role_filter == 'student' %}active{% endif %}">Students</a>
    <a href="{{ url_for('user_management') }}?role=teacher" class="button {% if role_filter == 'teacher' %}active{% endif %}">Teachers</a>
    <a href="{{ url_for('user_management') }}?role=admin" class="button {% if role_filter == 'admin' %}active{% endif %}">Admins</a>
  </div>

  <div class="search-box">
    <input type="text" id="userSearch" onkeyup="filterTable('userSearch', 'usersTable')" placeholder="Search users by name, username, or role...">
  </div>

  <table id="usersTable">
    <thead>
      <tr>
        <th>ID</th>
        <th>Username</th>
        <th>Full Name</th>
        <th>Role</th>
        <th>Status</th>
        <th>Last Login</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for user in users %}
      <tr>
        <td>{{ user.id }}</td>
        <td>{{ user.username }}</td>
        <td>{{ user.full_name or 'N/A' }}</td>
        <td>
          {% if user.role == 'admin' %}
            <span class="badge badge-danger">Admin</span>
          {% elif user.role == 'teacher' %}
            <span class="badge badge-warning">Teacher</span>
          {% elif user.role == 'student' %}
            <span class="badge badge-info">Student</span>
          {% endif %}
        </td>
        <td>
          {% if user.is_active %}
            <span class="badge badge-success">Active</span>
          {% else %}
            <span class="badge badge-danger">Inactive</span>
          {% endif %}
        </td>
        <td>{{ user.last_login or 'Never' }}</td>
        <td>{{ user.created_at[:10] }}</td>
        <td>
          <a href="{{ url_for('edit_user', id=user.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
          {% if user.role != 'admin' or user.id != session.user_id %}
          <a href="{{ url_for('toggle_user_status', id=user.id) }}" class="button {% if user.is_active %}danger{% else %}secondary{% endif %}" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('{% if user.is_active %}Deactivate{% else %}Activate{% endif %} this user?')">
            {% if user.is_active %}Deactivate{% else %}Activate{% endif %}
          </a>
          {% endif %}
          {% if user.id != session.user_id %}
          <a href="{{ url_for('reset_user_password', id=user.id) }}" class="button warning" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Reset password for {{ user.username }}? Default password will be set.')">Reset Password</a>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div id="addUser" class="tab-content">
  <div class="card">
    <h3>Add New User</h3>
    <form method="post" action="{{ url_for('add_user') }}">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="form-group">
            <label for="username">Username *</label>
            <input type="text" id="username" name="username" required>
          </div>
          
          <div class="form-group">
            <label for="full_name">Full Name</label>
            <input type="text" id="full_name" name="full_name">
          </div>
          
          <div class="form-group">
            <label for="email">Email</label>
            <input type="email" id="email" name="email">
          </div>
        </div>
        
        <div>
          <div class="form-group">
            <label for="role">Role *</label>
            <select id="role" name="role" required onchange="toggleRoleFields()">
              <option value="">Select Role</option>
              <option value="admin">Administrator</option>
              <option value="teacher">Teacher</option>
              <option value="student">Student</option>
            </select>
          </div>
          
          <div class="form-group" id="studentField" style="display: none;">
            <label for="admission_number">Student Admission Number</label>
            <input type="text" id="admission_number" name="admission_number">
          </div>
          
          <div class="form-group" id="teacherField" style="display: none;">
            <label for="teacher_id">Teacher</label>
            <select id="teacher_id" name="teacher_id">
              <option value="">Select Teacher</option>
              {% for teacher in teachers %}
              <option value="{{ teacher.id }}">{{ teacher.name }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="form-group">
            <label for="is_active">
              <input type="checkbox" id="is_active" name="is_active" checked>
              Active Account
            </label>
          </div>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Add User</button>
        <button type="reset" class="button secondary">Clear</button>
      </div>
    </form>
  </div>
  
  <div class="card">
    <h4>Default Password</h4>
    <p>New users will be created with the default password: <strong>school123</strong></p>
    <p>Users should change their password after first login.</p>
  </div>
</div>

<div id="resetPassword" class="tab-content">
  <div class="card">
    <h3>Reset User Password</h3>
    <form method="post" action="{{ url_for('reset_password_bulk') }}">
      <div class="form-group">
        <label for="user_id">Select User *</label>
        <select id="user_id" name="user_id" required>
          <option value="">Select User</option>
          {% for user in all_users %}
          <option value="{{ user.id }}">{{ user.username }} ({{ user.role }} - {{ user.full_name or 'N/A' }})</option>
          {% endfor %}
        </select>
      </div>
      
      <div class="form-group">
        <label for="new_password">New Password (optional)</label>
        <div class="password-toggle">
          <input type="password" id="new_password" name="new_password" placeholder="Leave blank for default password">
          <span class="toggle-icon" onclick="togglePassword('new_password')">
            <i class="fas fa-eye"></i>
          </span>
        </div>
        <small>If left blank, password will be reset to default: school123</small>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Reset Password</button>
      </div>
    </form>
  </div>
</div>

<script>
  function toggleRoleFields() {
    const role = document.getElementById('role').value;
    document.getElementById('studentField').style.display = role === 'student' ? 'block' : 'none';
    document.getElementById('teacherField').style.display = role === 'teacher' ? 'block' : 'none';
  }
  
  function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.querySelector(`[onclick="togglePassword('${inputId}')"] i`);
    
    if (input.type === 'password') {
      input.type = 'text';
      icon.classList.remove('fa-eye');
      icon.classList.add('fa-eye-slash');
    } else {
      input.type = 'password';
      icon.classList.remove('fa-eye-slash');
      icon.classList.add('fa-eye');
    }
  }
</script>
{% endblock %}''',

    'edit_user.html': '''{% extends "base.html" %}
{% block content %}
<h1>Edit User</h1>
<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="username">Username *</label>
          <input type="text" id="username" name="username" value="{{ user.username }}" required>
        </div>
        
        <div class="form-group">
          <label for="full_name">Full Name</label>
          <input type="text" id="full_name" name="full_name" value="{{ user.full_name or '' }}">
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" name="email" value="{{ user.email or '' }}">
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="role">Role *</label>
          <select id="role" name="role" required>
            <option value="admin" {% if user.role == 'admin' %}selected{% endif %}>Administrator</option>
            <option value="teacher" {% if user.role == 'teacher' %}selected{% endif %}>Teacher</option>
            <option value="student" {% if user.role == 'student' %}selected{% endif %}>Student</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="is_active">
            <input type="checkbox" id="is_active" name="is_active" {% if user.is_active %}checked{% endif %}>
            Active Account
          </label>
        </div>
        
        {% if user.role == 'student' and user.admission_number %}
        <div class="form-group">
          <label>Linked Student</label>
          <input type="text" value="{{ user.admission_number }}" readonly>
        </div>
        {% endif %}
        
        {% if user.role == 'teacher' and user.teacher_name %}
        <div class="form-group">
          <label>Linked Teacher</label>
          <input type="text" value="{{ user.teacher_name }}" readonly>
        </div>
        {% endif %}
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Update User</button>
      <a href="{{ url_for('user_management') }}" class="button secondary">Cancel</a>
    </div>
  </form>
</div>

<div class="card">
  <h3>Account Information</h3>
  <table>
    <tr>
      <th>Created:</th>
      <td>{{ user.created_at[:19] }}</td>
    </tr>
    <tr>
      <th>Last Login:</th>
      <td>{{ user.last_login or 'Never' }}</td>
    </tr>
    <tr>
      <th>Last Updated:</th>
      <td>{{ user.updated_at[:19] if user.updated_at else 'N/A' }}</td>
    </tr>
  </table>
</div>
{% endblock %}''',

    'student_dashboard.html': '''{% extends "base.html" %}
{% block content %}
<h1>Student Dashboard</h1>
<p>Welcome back, {{ student.name }}!</p>

<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Current Class</h3>
    <div class="value">{{ student.class }}</div>
  </div>
  <div class="stat-card">
    <h3>Attendance Rate</h3>
    <div class="value">{{ attendance_rate }}%</div>
  </div>
  <div class="stat-card">
    <h3>Average Grade</h3>
    <div class="value">{{ average_grade }}</div>
  </div>
  <div class="stat-card">
    <h3>Fee Balance</h3>
    <div class="value">{{ fee_balance }}</div>
  </div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 30px;">
  <div class="card">
    <h3>Today's Timetable</h3>
    {% if today_timetable %}
    <table>
      <thead>
        <tr><th>Period</th><th>Subject</th><th>Teacher</th><th>Room</th></tr>
      </thead>
      <tbody>
        {% for entry in today_timetable %}
        <tr>
          <td>Period {{ entry.period }}</td>
          <td>{{ entry.subject }}</td>
          <td>{{ entry.teacher_name or 'N/A' }}</td>
          <td>{{ entry.room or 'N/A' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No classes scheduled for today.</p>
    {% endif %}
  </div>
  
  <div class="card">
    <h3>Recent Grades</h3>
    {% if recent_grades %}
    <table>
      <thead>
        <tr><th>Subject</th><th>Term</th><th>Score</th><th>Grade</th></tr>
      </thead>
      <tbody>
        {% for grade in recent_grades %}
        <tr>
          <td>{{ grade.subject }}</td>
          <td>{{ grade.term }}</td>
          <td>{{ grade.score }}</td>
          <td class="grade-{{ grade.grade }}">{{ grade.grade }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    <a href="{{ url_for('student_grades') }}" class="button" style="margin-top: 10px;">View All Grades</a>
    {% else %}
    <p>No grades recorded yet.</p>
    {% endif %}
  </div>
</div>

<div class="card">
  <h3>Quick Links</h3>
  <div class="action-buttons">
    <a href="{{ url_for('student_grades') }}" class="button">My Grades</a>
    <a href="{{ url_for('student_attendance') }}" class="button secondary">My Attendance</a>
    <a href="{{ url_for('student_fees') }}" class="button">My Fees</a>
    <a href="{{ url_for('timetable') }}?class_filter={{ student.class }}" class="button secondary">Full Timetable</a>
    {% if medical_info %}
    <a href="#medical-info" class="button warning">Medical Information</a>
    {% endif %}
  </div>
</div>

{% if medical_info %}
<div class="card" id="medical-info">
  <h3>Medical Information</h3>
  <div class="medical-alert {% if medical_info.has_condition %}danger{% else %}info{% endif %}">
    <i class="fas fa-heartbeat"></i>
    <strong>Medical Status:</strong>
    {% if medical_info.has_condition %}
    Has Special Medical Condition
    {% else %}
    No Special Medical Conditions
    {% endif %}
  </div>
  
  {% if medical_info.conditions %}
  <div style="margin-top: 15px;">
    <h4>Medical Conditions</h4>
    <p>{{ medical_info.conditions }}</p>
  </div>
  {% endif %}
  
  {% if medical_info.allergies %}
  <div style="margin-top: 15px;">
    <h4>Allergies</h4>
    <p>{{ medical_info.allergies }}</p>
  </div>
  {% endif %}
  
  {% if medical_info.medications %}
  <div style="margin-top: 15px;">
    <h4>Current Medications</h4>
    <p>{{ medical_info.medications }}</p>
  </div>
  {% endif %}
  
  {% if medical_info.emergency_contact_name %}
  <div style="margin-top: 15px;">
    <h4>Emergency Contact</h4>
    <table>
      <tr>
        <th>Name:</th>
        <td>{{ medical_info.emergency_contact_name }}</td>
      </tr>
      <tr>
        <th>Relationship:</th>
        <td>{{ medical_info.emergency_contact_relation }}</td>
      </tr>
      <tr>
        <th>Phone:</th>
        <td>{{ medical_info.emergency_contact_phone }}</td>
      </tr>
      {% if medical_info.emergency_contact_alt_phone %}
      <tr>
        <th>Alternate Phone:</th>
        <td>{{ medical_info.emergency_contact_alt_phone }}</td>
      </tr>
      {% endif %}
    </table>
  </div>
  {% endif %}
</div>
{% endif %}
{% endblock %}''',

    'student_grades.html': '''{% extends "base.html" %}
{% block content %}
<h1>My Grades</h1>

<div class="card">
  <h3>Grade Summary</h3>
  <table>
    <thead>
      <tr>
        <th>Term</th>
        <th>Number of Subjects</th>
        <th>Average Score</th>
        <th>Average Grade</th>
        <th>Position</th>
      </tr>
    </thead>
    <tbody>
      {% for term, data in term_summary.items() %}
      <tr>
        <td>{{ term }}</td>
        <td>{{ data.count }}</td>
        <td>{{ "%.2f"|format(data.average) }}%</td>
        <td class="grade-{{ data.grade }}">{{ data.grade }}</td>
        <td>{{ data.position or 'N/A' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div class="card">
  <h3>All Grades</h3>
  {% if grades %}
  <table>
    <thead>
      <tr>
        <th>Subject</th>
        <th>Term</th>
        <th>Year</th>
        <th>Score</th>
        <th>Grade</th>
        <th>Date Recorded</th>
      </tr>
    </thead>
    <tbody>
      {% for grade in grades %}
      <tr>
        <td>{{ grade.subject }}</td>
        <td>{{ grade.term }}</td>
        <td>{{ grade.year }}</td>
        <td>{{ grade.score }}</td>
        <td class="grade-{{ grade.grade }}">{{ grade.grade }}</td>
        <td>{{ grade.created_at[:10] }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No grades recorded yet.</p>
  {% endif %}
</div>

<div class="card">
  <h3>Subject Performance</h3>
  {% if subject_performance %}
  {% for subject in subject_performance %}
  <div class="subject-performance" data-score="{{ subject.average_score|round }}" data-grade="{{ subject.grade }}">
    <div class="subject-name">{{ subject.name }}</div>
    <div class="score-bar">
      <div class="score-fill" style="width: {{ subject.average_score|round }}%;"></div>
      <div class="score-text">{{ subject.average_score|round }}% ({{ subject.grade }})</div>
    </div>
  </div>
  {% endfor %}
  {% else %}
  <p>No subject performance data available.</p>
  {% endif %}
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    updateScoreBars();
  });
</script>
{% endblock %}''',

    'student_attendance.html': '''{% extends "base.html" %}
{% block content %}
<h1>My Attendance</h1>

<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Present Days</h3>
    <div class="value">{{ attendance_stats.present }}</div>
  </div>
  <div class="stat-card">
    <h3>Absent Days</h3>
    <div class="value">{{ attendance_stats.absent }}</div>
  </div>
  <div class="stat-card">
    <h3>Late Days</h3>
    <div class="value">{{ attendance_stats.late }}</div>
  </div>
  <div class="stat-card">
    <h3>Attendance Rate</h3>
    <div class="value">{{ attendance_stats.rate }}%</div>
  </div>
</div>

<div class="card">
  <h3>Recent Attendance</h3>
  {% if recent_attendance %}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Status</th>
        <th>Remarks</th>
      </tr>
    </thead>
    <tbody>
      {% for record in recent_attendance %}
      <tr>
        <td>{{ record.date }}</td>
        <td>
          {% if record.status == 'Present' %}
            <span class="status-present">Present</span>
          {% elif record.status == 'Absent' %}
            <span class="status-absent">Absent</span>
          {% elif record.status == 'Late' %}
            <span class="status-late">Late</span>
          {% elif record.status == 'Excused' %}
            <span class="status-excused">Excused</span>
          {% endif %}
        </td>
        <td>{{ record.remarks or '-' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No attendance records found.</p>
  {% endif %}
</div>

<div class="card">
  <h3>Monthly Attendance Summary</h3>
  <form method="get" style="display: flex; gap: 10px; margin-bottom: 20px;">
    <input type="month" name="month" value="{{ month }}" onchange="this.form.submit()">
  </form>
  
  {% if monthly_attendance %}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Day</th>
        <th>Status</th>
        <th>Remarks</th>
      </tr>
    </thead>
    <tbody>
      {% for record in monthly_attendance %}
      <tr>
        <td>{{ record.date }}</td>
        <td>{{ record.day_name }}</td>
        <td>
          {% if record.status == 'Present' %}
            <span class="status-present">Present</span>
          {% elif record.status == 'Absent' %}
            <span class="status-absent">Absent</span>
          {% elif record.status == 'Late' %}
            <span class="status-late">Late</span>
          {% elif record.status == 'Excused' %}
            <span class="status-excused">Excused</span>
          {% endif %}
        </td>
        <td>{{ record.remarks or '-' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No attendance records for {{ month }}.</p>
  {% endif %}
</div>
{% endblock %}''',

    'student_fees.html': '''{% extends "base.html" %}
{% block content %}
<h1>My Fees</h1>

<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Total Fee</h3>
    <div class="value">{{ fee_summary.total_fee }}</div>
  </div>
  <div class="stat-card">
    <h3>Total Paid</h3>
    <div class="value">{{ fee_summary.total_paid }}</div>
  </div>
  <div class="stat-card">
    <h3>Balance</h3>
    <div class="value {% if fee_summary.balance > 0 %}balance{% else %}paid{% endif %}">{{ fee_summary.balance }}</div>
  </div>
  <div class="stat-card">
    <h3>Payment Status</h3>
    <div class="value">
      {% if fee_summary.balance <= 0 %}
        <span class="paid">Paid</span>
      {% elif fee_summary.balance < fee_summary.total_fee %}
        <span style="color: #f59e0b;">Partial</span>
      {% else %}
        <span class="balance">Pending</span>
      {% endif %}
    </div>
  </div>
</div>

<div class="card">
  <h3>Fee Structures</h3>
  {% if fee_structures %}
  <table>
    <thead>
      <tr>
        <th>Term</th>
        <th>Year</th>
        <th>Total Amount</th>
        <th>Paid Amount</th>
        <th>Balance</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for fs in fee_structures %}
      <tr>
        <td>{{ fs.term }}</td>
        <td>{{ fs.year }}</td>
        <td>{{ fs.amount }}</td>
        <td class="paid">{{ fs.paid_amount }}</td>
        <td class="{% if fs.balance > 0 %}balance{% else %}paid{% endif %}">{{ fs.balance }}</td>
        <td>
          {% if fs.balance <= 0 %}
            <span class="badge badge-success">Paid</span>
          {% elif fs.paid_amount > 0 %}
            <span class="badge badge-warning">Partial</span>
          {% else %}
            <span class="badge badge-danger">Unpaid</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No fee structures found.</p>
  {% endif %}
</div>

<div class="card">
  <h3>Payment History</h3>
  {% if payments %}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Receipt No</th>
        <th>Term</th>
        <th>Year</th>
        <th>Amount Paid</th>
        <th>Payment Method</th>
        <th>Remarks</th>
      </tr>
    </thead>
    <tbody>
      {% for payment in payments %}
      <tr>
        <td>{{ payment.date_paid }}</td>
        <td>{{ payment.receipt_number }}</td>
        <td>{{ payment.term }}</td>
        <td>{{ payment.year }}</td>
        <td class="paid">{{ payment.amount_paid }}</td>
        <td>{{ payment.payment_method or 'Cash' }}</td>
        <td>{{ payment.remarks or '-' }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No payment history found.</p>
  {% endif %}
</div>
{% endblock %}''',

    'teacher_dashboard.html': '''{% extends "base.html" %}
{% block content %}
<h1>Teacher Dashboard</h1>
<p>Welcome, {{ teacher.name }}!</p>

<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Assigned Classes</h3>
    <div class="value">{{ stats.class_count }}</div>
  </div>
  <div class="stat-card">
    <h3>Total Students</h3>
    <div class="value">{{ stats.student_count }}</div>
  </div>
  <div class="stat-card">
    <h3>Today's Classes</h3>
    <div class="value">{{ stats.today_classes }}</div>
  </div>
  <div class="stat-card">
    <h3>Pending Grades</h3>
    <div class="value">{{ stats.pending_grades }}</div>
  </div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 30px;">
  <div class="card">
    <h3>Today's Schedule</h3>
    {% if today_schedule %}
    <table>
      <thead>
        <tr><th>Time</th><th>Class</th><th>Subject</th><th>Room</th></tr>
      </thead>
      <tbody>
        {% for entry in today_schedule %}
        <tr>
          <td>Period {{ entry.period }}</td>
          <td>{{ entry.class }}</td>
          <td>{{ entry.subject }}</td>
          <td>{{ entry.room or 'N/A' }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No classes scheduled for today.</p>
    {% endif %}
  </div>
  
  <div class="card">
    <h3>My Classes</h3>
    {% if my_classes %}
    <table>
      <thead>
        <tr><th>Class</th><th>Students</th><th>Action</th></tr>
      </thead>
      <tbody>
        {% for cls in my_classes %}
        <tr>
          <td>{{ cls.name }}</td>
          <td>{{ cls.student_count }}</td>
          <td>
            <a href="{{ url_for('attendance') }}?class_filter={{ cls.name }}" class="button" style="padding: 5px 10px; font-size: 12px;">Take Attendance</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No classes assigned yet.</p>
    {% endif %}
  </div>
</div>

<div class="card">
  <h3>Quick Actions</h3>
  <div class="action-buttons">
    <a href="{{ url_for('mark_attendance') }}" class="button">Mark Attendance</a>
    <a href="{{ url_for('add_grade') }}" class="button secondary">Add Grades</a>
    <a href="{{ url_for('timetable') }}" class="button">View Timetable</a>
    <a href="{{ url_for('grades') }}" class="button secondary">View All Grades</a>
  </div>
</div>

<div class="card">
  <h3>Recent Attendance Updates</h3>
  {% if recent_attendance %}
  <table>
    <thead>
      <tr>
        <th>Date</th>
        <th>Class</th>
        <th>Student</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for record in recent_attendance %}
      <tr>
        <td>{{ record.date }}</td>
        <td>{{ record.class }}</td>
        <td>{{ record.student_name }}</td>
        <td>
          {% if record.status == 'Present' %}
            <span class="status-present">Present</span>
          {% elif record.status == 'Absent' %}
            <span class="status-absent">Absent</span>
          {% elif record.status == 'Late' %}
            <span class="status-late">Late</span>
          {% elif record.status == 'Excused' %}
            <span class="status-excused">Excused</span>
          {% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No recent attendance records.</p>
  {% endif %}
</div>
{% endblock %}''',

    'index.html': '''{% extends "base.html" %}
{% block content %}
<h1>Dashboard</h1>
<p>Welcome back, {{ session.username }}!</p>

<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Total Students</h3>
    <div class="value">{{ total_students }}</div>
  </div>
  <div class="stat-card">
    <h3>Total Teachers</h3>
    <div class="value">{{ total_teachers }}</div>
  </div>
  <div class="stat-card">
    <h3>Total Classes</h3>
    <div class="value">{{ total_classes }}</div>
  </div>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 30px;">
  <div class="card">
    <h3>Recent Students</h3>
    {% if recent_students %}
    <table>
      <thead>
        <tr><th>Admission No</th><th>Name</th><th>Class</th><th>Date Added</th></tr>
      </thead>
      <tbody>
        {% for student in recent_students %}
        <tr>
          <td>{{ student.admission_number }}</td>
          <td>{{ student.name }}</td>
          <td>{{ student.class }}</td>
          <td>{{ student.created_at[:10] }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No students found.</p>
    {% endif %}
    <a href="{{ url_for('students') }}" class="button" style="margin-top: 10px;">View All Students</a>
  </div>
  
  <div class="card">
    <h3>Recent Payments</h3>
    {% if recent_payments %}
    <table>
      <thead>
        <tr><th>Receipt No</th><th>Student</th><th>Amount</th><th>Date</th></tr>
      </thead>
      <tbody>
        {% for payment in recent_payments %}
        <tr>
          <td>{{ payment.receipt_number }}</td>
          <td>{{ payment.student_name }}</td>
          <td>{{ payment.amount_paid }}</td>
          <td>{{ payment.date_paid }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No recent payments.</p>
    {% endif %}
    <a href="{{ url_for('fees') }}" class="button" style="margin-top: 10px;">View All Fees</a>
  </div>
</div>

<div class="card">
  <h3>Quick Actions</h3>
  <div class="action-buttons">
    <a href="{{ url_for('add_student') }}" class="button">Add New Student</a>
    <a href="{{ url_for('add_teacher') }}" class="button secondary">Add New Teacher</a>
    <a href="{{ url_for('attendance') }}" class="button">Mark Attendance</a>
    <a href="{{ url_for('add_fee_structure') }}" class="button secondary">Add Fee Structure</a>
    <a href="{{ url_for('timetable') }}" class="button">Manage Timetable</a>
    <a href="{{ url_for('settings') }}" class="button secondary">System Settings</a>
  </div>
</div>
{% endblock %}''',

    'students.html': '''{% extends "base.html" %}
{% block content %}
<h1>Students</h1>

<div class="action-buttons">
  <a href="{{ url_for('add_student') }}" class="button">Add New Student</a>
</div>

<div class="search-box">
  <input type="text" id="studentSearch" onkeyup="filterTable('studentSearch', 'studentsTable')" placeholder="Search students by name, admission number, or class...">
</div>

<table id="studentsTable">
  <thead>
    <tr>
      <th>ID</th>
      <th>Admission No</th>
      <th>Name</th>
      <th>Age</th>
      <th>Class</th>
      <th>Guardian</th>
      <th>Guardian Contacts</th>
      <th>Medical Info</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for student in students %}
    <tr>
      <td>{{ student.id }}</td>
      <td>{{ student.admission_number }}</td>
      <td>{{ student.name }}</td>
      <td>{{ student.age or 'N/A' }}</td>
      <td>{{ student.class or 'N/A' }}</td>
      <td>{{ student.guardian_name or 'N/A' }}</td>
      <td>{{ student.guardian_contacts or 'N/A' }}</td>
      <td>
        {% if student.has_medical_condition %}
          <span class="badge badge-danger">Medical</span>
        {% else %}
          <span class="badge badge-success">Healthy</span>
        {% endif %}
      </td>
      <td>
        <a href="{{ url_for('edit_student', id=student.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
        <a href="{{ url_for('view_medical_info', id=student.id) }}" class="button warning" style="padding: 5px 10px; font-size: 12px;">Medical</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>

<script>
  function filterTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');

    for (let i = 1; i < rows.length; i++) {
      const cells = rows[i].getElementsByTagName('td');
      let match = false;
      
      for (let j = 0; j < cells.length; j++) {
        const cell = cells[j];
        if (cell) {
          if (cell.textContent.toUpperCase().indexOf(filter) > -1) {
            match = true;
            break;
          }
        }
      }
      rows[i].style.display = match ? '' : 'none';
    }
  }
</script>
{% endblock %}''',

    'add_student.html': '''{% extends "base.html" %}
{% block content %}
<h1>Add New Student</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="admission_number">Admission Number *</label>
          <input type="text" id="admission_number" name="admission_number" required>
        </div>
        
        <div class="form-group">
          <label for="name">Full Name *</label>
          <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
          <label for="age">Age</label>
          <input type="number" id="age" name="age" min="1" max="30">
        </div>
        
        <div class="form-group">
          <label for="class">Class *</label>
          <select id="class" name="class" required>
            <option value="">Select Class</option>
            <option value="Form 1">Form 1</option>
            <option value="Form 2">Form 2</option>
            <option value="Form 3">Form 3</option>
            <option value="Form 4">Form 4</option>
            <option value="Form 5">Form 5</option>
            <option value="Form 6">Form 6</option>
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="guardian_name">Guardian Name</label>
          <input type="text" id="guardian_name" name="guardian_name">
        </div>
        
        <div class="form-group">
          <label for="guardian_contacts">Guardian Contacts</label>
          <input type="text" id="guardian_contacts" name="guardian_contacts" placeholder="Phone numbers">
        </div>
        
        <div class="form-group">
          <label for="guardian_email">Guardian Email</label>
          <input type="email" id="guardian_email" name="guardian_email">
        </div>
        
        <div class="form-group">
          <label for="address">Address</label>
          <textarea id="address" name="address" rows="3"></textarea>
        </div>
      </div>
    </div>
    
    <h3>Medical Information</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div>
        <div class="form-group">
          <label for="has_medical_condition">
            <input type="checkbox" id="has_medical_condition" name="has_medical_condition">
            Has Special Medical Condition
          </label>
        </div>
        
        <div class="form-group">
          <label for="medical_conditions">Medical Conditions</label>
          <textarea id="medical_conditions" name="medical_conditions" rows="3" placeholder="Describe any medical conditions"></textarea>
        </div>
        
        <div class="form-group">
          <label for="allergies">Allergies</label>
          <textarea id="allergies" name="allergies" rows="2" placeholder="List any allergies"></textarea>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="medications">Current Medications</label>
          <textarea id="medications" name="medications" rows="2"></textarea>
        </div>
        
        <div class="form-group">
          <label for="blood_type">Blood Type</label>
          <input type="text" id="blood_type" name="blood_type" placeholder="e.g., O+">
        </div>
      </div>
    </div>
    
    <h3>Emergency Contact</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div>
        <div class="form-group">
          <label for="emergency_contact_name">Emergency Contact Name</label>
          <input type="text" id="emergency_contact_name" name="emergency_contact_name">
        </div>
        
        <div class="form-group">
          <label for="emergency_contact_relation">Relationship</label>
          <input type="text" id="emergency_contact_relation" name="emergency_contact_relation" placeholder="e.g., Father, Mother">
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="emergency_contact_phone">Emergency Phone</label>
          <input type="tel" id="emergency_contact_phone" name="emergency_contact_phone">
        </div>
        
        <div class="form-group">
          <label for="emergency_contact_alt_phone">Alternate Phone</label>
          <input type="tel" id="emergency_contact_alt_phone" name="emergency_contact_alt_phone">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Add Student</button>
      <button type="reset" class="button secondary">Clear</button>
    </div>
  </form>
</div>
{% endblock %}''',

    'edit_student.html': '''{% extends "base.html" %}
{% block content %}
<h1>Edit Student</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="admission_number">Admission Number</label>
          <input type="text" id="admission_number" name="admission_number" value="{{ student.admission_number }}" readonly>
        </div>
        
        <div class="form-group">
          <label for="name">Full Name *</label>
          <input type="text" id="name" name="name" value="{{ student.name }}" required>
        </div>
        
        <div class="form-group">
          <label for="age">Age</label>
          <input type="number" id="age" name="age" min="1" max="30" value="{{ student.age or '' }}">
        </div>
        
        <div class="form-group">
          <label for="class">Class *</label>
          <select id="class" name="class" required>
            <option value="">Select Class</option>
            <option value="Form 1" {% if student.class == 'Form 1' %}selected{% endif %}>Form 1</option>
            <option value="Form 2" {% if student.class == 'Form 2' %}selected{% endif %}>Form 2</option>
            <option value="Form 3" {% if student.class == 'Form 3' %}selected{% endif %}>Form 3</option>
            <option value="Form 4" {% if student.class == 'Form 4' %}selected{% endif %}>Form 4</option>
            <option value="Form 5" {% if student.class == 'Form 5' %}selected{% endif %}>Form 5</option>
            <option value="Form 6" {% if student.class == 'Form 6' %}selected{% endif %}>Form 6</option>
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="guardian_name">Guardian Name</label>
          <input type="text" id="guardian_name" name="guardian_name" value="{{ student.guardian_name or '' }}">
        </div>
        
        <div class="form-group">
          <label for="guardian_contacts">Guardian Contacts</label>
          <input type="text" id="guardian_contacts" name="guardian_contacts" value="{{ student.guardian_contacts or '' }}" placeholder="Phone numbers">
        </div>
        
        <div class="form-group">
          <label for="guardian_email">Guardian Email</label>
          <input type="email" id="guardian_email" name="guardian_email" value="{{ student.guardian_email or '' }}">
        </div>
        
        <div class="form-group">
          <label for="address">Address</label>
          <textarea id="address" name="address" rows="3">{{ student.address or '' }}</textarea>
        </div>
      </div>
    </div>
    
    <h3>Medical Information</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div>
        <div class="form-group">
          <label for="has_medical_condition">
            <input type="checkbox" id="has_medical_condition" name="has_medical_condition" {% if student.has_medical_condition %}checked{% endif %}>
            Has Special Medical Condition
          </label>
        </div>
        
        <div class="form-group">
          <label for="medical_conditions">Medical Conditions</label>
          <textarea id="medical_conditions" name="medical_conditions" rows="3">{{ student.medical_conditions or '' }}</textarea>
        </div>
        
        <div class="form-group">
          <label for="allergies">Allergies</label>
          <textarea id="allergies" name="allergies" rows="2">{{ student.allergies or '' }}</textarea>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="medications">Current Medications</label>
          <textarea id="medications" name="medications" rows="2">{{ student.medications or '' }}</textarea>
        </div>
        
        <div class="form-group">
          <label for="blood_type">Blood Type</label>
          <input type="text" id="blood_type" name="blood_type" value="{{ student.blood_type or '' }}">
        </div>
      </div>
    </div>
    
    <h3>Emergency Contact</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
      <div>
        <div class="form-group">
          <label for="emergency_contact_name">Emergency Contact Name</label>
          <input type="text" id="emergency_contact_name" name="emergency_contact_name" value="{{ student.emergency_contact_name or '' }}">
        </div>
        
        <div class="form-group">
          <label for="emergency_contact_relation">Relationship</label>
          <input type="text" id="emergency_contact_relation" name="emergency_contact_relation" value="{{ student.emergency_contact_relation or '' }}">
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="emergency_contact_phone">Emergency Phone</label>
          <input type="tel" id="emergency_contact_phone" name="emergency_contact_phone" value="{{ student.emergency_contact_phone or '' }}">
        </div>
        
        <div class="form-group">
          <label for="emergency_contact_alt_phone">Alternate Phone</label>
          <input type="tel" id="emergency_contact_alt_phone" name="emergency_contact_alt_phone" value="{{ student.emergency_contact_alt_phone or '' }}">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Update Student</button>
      <a href="{{ url_for('students') }}" class="button secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}''',

    'medical_info.html': '''{% extends "base.html" %}
{% block content %}
<h1>Medical Information - {{ student.name }}</h1>

<div class="card">
  <h3>Basic Information</h3>
  <table>
    <tr>
      <th>Admission Number:</th>
      <td>{{ student.admission_number }}</td>
    </tr>
    <tr>
      <th>Name:</th>
      <td>{{ student.name }}</td>
    </tr>
    <tr>
      <th>Class:</th>
      <td>{{ student.class }}</td>
    </tr>
    <tr>
      <th>Age:</th>
      <td>{{ student.age or 'N/A' }}</td>
    </tr>
  </table>
</div>

<div class="card">
  <h3>Medical Status</h3>
  <div class="medical-alert {% if student.has_medical_condition %}danger{% else %}info{% endif %}">
    <i class="fas fa-heartbeat"></i>
    <strong>Medical Condition:</strong>
    {% if student.has_medical_condition %}
    Has Special Medical Condition
    {% else %}
    No Special Medical Conditions
    {% endif %}
  </div>
  
  {% if student.medical_conditions %}
  <div style="margin-top: 15px;">
    <h4>Medical Conditions</h4>
    <p>{{ student.medical_conditions }}</p>
  </div>
  {% endif %}
  
  {% if student.allergies %}
  <div style="margin-top: 15px;">
    <h4>Allergies</h4>
    <p>{{ student.allergies }}</p>
  </div>
  {% endif %}
  
  {% if student.medications %}
  <div style="margin-top: 15px;">
    <h4>Current Medications</h4>
    <p>{{ student.medications }}</p>
  </div>
  {% endif %}
  
  {% if student.blood_type %}
  <div style="margin-top: 15px;">
    <h4>Blood Type</h4>
    <p>{{ student.blood_type }}</p>
  </div>
  {% endif %}
</div>

<div class="card">
  <h3>Emergency Contact</h3>
  {% if student.emergency_contact_name %}
  <table>
    <tr>
      <th>Name:</th>
      <td>{{ student.emergency_contact_name }}</td>
    </tr>
    <tr>
      <th>Relationship:</th>
      <td>{{ student.emergency_contact_relation }}</td>
    </tr>
    <tr>
      <th>Phone:</th>
      <td>{{ student.emergency_contact_phone }}</td>
    </tr>
    {% if student.emergency_contact_alt_phone %}
    <tr>
      <th>Alternate Phone:</th>
      <td>{{ student.emergency_contact_alt_phone }}</td>
    </tr>
    {% endif %}
  </table>
  {% else %}
  <p>No emergency contact information available.</p>
  {% endif %}
</div>

<div class="action-buttons">
  <a href="{{ url_for('edit_student', id=student.id) }}" class="button">Edit Student</a>
  <a href="{{ url_for('students') }}" class="button secondary">Back to Students</a>
</div>
{% endblock %}''',

    'teachers.html': '''{% extends "base.html" %}
{% block content %}
<h1>Teachers</h1>

<div class="action-buttons">
  <a href="{{ url_for('add_teacher') }}" class="button">Add New Teacher</a>
</div>

<table id="teachersTable">
  <thead>
    <tr>
      <th>ID</th>
      <th>Name</th>
      <th>Email</th>
      <th>Phone</th>
      <th>Qualification</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for teacher in teachers %}
    <tr>
      <td>{{ teacher.id }}</td>
      <td>{{ teacher.name }}</td>
      <td>{{ teacher.email or 'N/A' }}</td>
      <td>{{ teacher.phone or 'N/A' }}</td>
      <td>{{ teacher.qualification or 'N/A' }}</td>
      <td>
        <a href="{{ url_for('edit_teacher', id=teacher.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
        <a href="{{ url_for('delete_teacher', id=teacher.id) }}" class="button danger" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Delete this teacher?')">Delete</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}''',

    'add_teacher.html': '''{% extends "base.html" %}
{% block content %}
<h1>Add New Teacher</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="name">Full Name *</label>
          <input type="text" id="name" name="name" required>
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" name="email">
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="phone">Phone</label>
          <input type="tel" id="phone" name="phone">
        </div>
        
        <div class="form-group">
          <label for="qualification">Qualification</label>
          <input type="text" id="qualification" name="qualification" placeholder="e.g., B.Ed, M.Ed">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Add Teacher</button>
      <button type="reset" class="button secondary">Clear</button>
    </div>
  </form>
</div>
{% endblock %}''',

    'edit_teacher.html': '''{% extends "base.html" %}
{% block content %}
<h1>Edit Teacher</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="name">Full Name *</label>
          <input type="text" id="name" name="name" value="{{ teacher.name }}" required>
        </div>
        
        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" id="email" name="email" value="{{ teacher.email or '' }}">
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="phone">Phone</label>
          <input type="tel" id="phone" name="phone" value="{{ teacher.phone or '' }}">
        </div>
        
        <div class="form-group">
          <label for="qualification">Qualification</label>
          <input type="text" id="qualification" name="qualification" value="{{ teacher.qualification or '' }}">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Update Teacher</button>
      <a href="{{ url_for('teachers') }}" class="button secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}''',

    'classes.html': '''{% extends "base.html" %}
{% block content %}
<h1>Classes</h1>

<div class="action-buttons">
  <a href="{{ url_for('add_class') }}" class="button">Add New Class</a>
</div>

<table id="classesTable">
  <thead>
    <tr>
      <th>ID</th>
      <th>Class Name</th>
      <th>Teacher</th>
      <th>Students</th>
      <th>Description</th>
      <th>Actions</th>
    </tr>
  </thead>
  <tbody>
    {% for cls in classes %}
    <tr>
      <td>{{ cls.id }}</td>
      <td>{{ cls.name }}</td>
      <td>{{ cls.teacher_name or 'Not Assigned' }}</td>
      <td>{{ cls.student_count }}</td>
      <td>{{ cls.description or 'N/A' }}</td>
      <td>
        <a href="{{ url_for('edit_class', id=cls.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
        <a href="{{ url_for('delete_class', id=cls.id) }}" class="button danger" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Delete this class?')">Delete</a>
      </td>
    </tr>
    {% endfor %}
  </tbody>
</table>
{% endblock %}''',

    'add_class.html': '''{% extends "base.html" %}
{% block content %}
<h1>Add New Class</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="name">Class Name *</label>
          <input type="text" id="name" name="name" required placeholder="e.g., Form 1A">
        </div>
        
        <div class="form-group">
          <label for="teacher_id">Class Teacher</label>
          <select id="teacher_id" name="teacher_id">
            <option value="">Select Teacher</option>
            {% for teacher in teachers %}
            <option value="{{ teacher.id }}">{{ teacher.name }}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="description">Description</label>
          <textarea id="description" name="description" rows="4" placeholder="Class description..."></textarea>
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Add Class</button>
      <button type="reset" class="button secondary">Clear</button>
    </div>
  </form>
</div>
{% endblock %}''',

    'edit_class.html': '''{% extends "base.html" %}
{% block content %}
<h1>Edit Class</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="name">Class Name *</label>
          <input type="text" id="name" name="name" value="{{ cls.name }}" required>
        </div>
        
        <div class="form-group">
          <label for="teacher_id">Class Teacher</label>
          <select id="teacher_id" name="teacher_id">
            <option value="">Select Teacher</option>
            {% for teacher in teachers %}
            <option value="{{ teacher.id }}" {% if cls.teacher_id == teacher.id %}selected{% endif %}>{{ teacher.name }}</option>
            {% endfor %}
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="description">Description</label>
          <textarea id="description" name="description" rows="4">{{ cls.description or '' }}</textarea>
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Update Class</button>
      <a href="{{ url_for('classes') }}" class="button secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}''',

    'fees.html': '''{% extends "base.html" %}
{% block content %}
<h1>Fee Management</h1>

<div class="tabs">
  <button class="tab active" onclick="toggleTabs('recentPayments')">Recent Payments</button>
  <button class="tab" onclick="toggleTabs('feeStructures')">Fee Structures</button>
  <button class="tab" onclick="toggleTabs('addPayment')">Add Payment</button>
  <button class="tab" onclick="toggleTabs('addStructure')">Add Structure</button>
</div>

<div id="recentPayments" class="tab-content active">
  <div class="card">
    <h3>Recent Fee Payments</h3>
    {% if recent_payments %}
    <table>
      <thead>
        <tr>
          <th>Receipt No</th>
          <th>Student</th>
          <th>Class</th>
          <th>Term</th>
          <th>Year</th>
          <th>Amount Paid</th>
          <th>Balance</th>
          <th>Date</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for payment in recent_payments %}
        <tr>
          <td>{{ payment.receipt_number }}</td>
          <td>{{ payment.student_name }}</td>
          <td>{{ payment.class_name }}</td>
          <td>{{ payment.term }}</td>
          <td>{{ payment.year }}</td>
          <td class="paid">{{ payment.amount_paid }}</td>
          <td class="{% if payment.balance > 0 %}balance{% else %}paid{% endif %}">{{ payment.balance }}</td>
          <td>{{ payment.date_paid }}</td>
          <td>
            <a href="{{ url_for('view_receipt', id=payment.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Receipt</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No recent payments found.</p>
    {% endif %}
  </div>
</div>

<div id="feeStructures" class="tab-content">
  <div class="card">
    <h3>Fee Structures</h3>
    {% if fee_structures %}
    <table>
      <thead>
        <tr>
          <th>Class</th>
          <th>Term</th>
          <th>Year</th>
          <th>Amount</th>
          <th>Due Date</th>
          <th>Description</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for fs in fee_structures %}
        <tr>
          <td>{{ fs.class }}</td>
          <td>{{ fs.term }}</td>
          <td>{{ fs.year }}</td>
          <td>{{ fs.amount }}</td>
          <td>{{ fs.due_date or 'N/A' }}</td>
          <td>{{ fs.description or 'N/A' }}</td>
          <td>
            <a href="{{ url_for('edit_fee_structure', id=fs.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
            <a href="{{ url_for('delete_fee_structure', id=fs.id) }}" class="button danger" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Delete this fee structure?')">Delete</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No fee structures found.</p>
    {% endif %}
  </div>
</div>

<div id="addPayment" class="tab-content">
  <div class="card">
    <h3>Add Fee Payment</h3>
    <form method="post" action="{{ url_for('add_fee_payment') }}">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="form-group">
            <label for="student_id">Student *</label>
            <select id="student_id" name="student_id" required>
              <option value="">Select Student</option>
              {% for student in students %}
              <option value="{{ student.id }}">{{ student.name }} ({{ student.admission_number }}) - {{ student.class }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="form-group">
            <label for="fee_structure_id">Fee Structure *</label>
            <select id="fee_structure_id" name="fee_structure_id" required>
              <option value="">Select Fee Structure</option>
              {% for fs in fee_structures %}
              <option value="{{ fs.id }}">{{ fs.class }} - {{ fs.term }} {{ fs.year }} - {{ fs.amount }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
        
        <div>
          <div class="form-group">
            <label for="amount_paid">Amount Paid *</label>
            <input type="number" id="amount_paid" name="amount_paid" step="0.01" min="0" required>
          </div>
          
          <div class="form-group">
            <label for="payment_method">Payment Method</label>
            <select id="payment_method" name="payment_method">
              <option value="Cash">Cash</option>
              <option value="Bank Transfer">Bank Transfer</option>
              <option value="Mobile Money">Mobile Money</option>
              <option value="Cheque">Cheque</option>
              <option value="Other">Other</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="remarks">Remarks</label>
            <input type="text" id="remarks" name="remarks" placeholder="Payment remarks">
          </div>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Record Payment</button>
        <button type="reset" class="button secondary">Clear</button>
      </div>
    </form>
  </div>
</div>

<div id="addStructure" class="tab-content">
  <div class="card">
    <h3>Add Fee Structure</h3>
    <form method="post" action="{{ url_for('add_fee_structure') }}">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="form-group">
            <label for="class">Class *</label>
            <select id="class" name="class" required>
              <option value="">Select Class</option>
              <option value="Form 1">Form 1</option>
              <option value="Form 2">Form 2</option>
              <option value="Form 3">Form 3</option>
              <option value="Form 4">Form 4</option>
              <option value="Form 5">Form 5</option>
              <option value="Form 6">Form 6</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="term">Term *</label>
            <select id="term" name="term" required>
              <option value="">Select Term</option>
              <option value="Term 1">Term 1</option>
              <option value="Term 2">Term 2</option>
              <option value="Term 3">Term 3</option>
            </select>
          </div>
        </div>
        
        <div>
          <div class="form-group">
            <label for="year">Year *</label>
            <input type="number" id="year" name="year" min="2000" max="2100" value="{{ current_year }}" required>
          </div>
          
          <div class="form-group">
            <label for="amount">Amount *</label>
            <input type="number" id="amount" name="amount" step="0.01" min="0" required>
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label for="description">Description</label>
        <input type="text" id="description" name="description" placeholder="Fee structure description">
      </div>
      
      <div class="form-group">
        <label for="due_date">Due Date</label>
        <input type="date" id="due_date" name="due_date">
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Add Fee Structure</button>
        <button type="reset" class="button secondary">Clear</button>
      </div>
    </form>
  </div>
</div>
{% endblock %}''',

    'attendance.html': '''{% extends "base.html" %}
{% block content %}
<h1>Attendance Management</h1>

<div class="filter-form">
  <form method="get">
    <div style="display: flex; flex-wrap: wrap; gap: 15px; align-items: center;">
      <div>
        <label for="class_filter">Filter by Class:</label>
        <select id="class_filter" name="class_filter" onchange="this.form.submit()">
          <option value="">All Classes</option>
          {% for class_name in class_list %}
          <option value="{{ class_name }}" {% if current_class == class_name %}selected{% endif %}>{{ class_name }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div>
        <label for="date">Select Date:</label>
        <input type="date" id="date" name="date" value="{{ selected_date }}" onchange="this.form.submit()">
      </div>
      
      <div>
        <button type="submit" class="button">Apply Filters</button>
        <a href="{{ url_for('attendance') }}" class="button secondary">Reset</a>
      </div>
    </div>
  </form>
</div>

{% if today_stats %}
<div class="dashboard-stats">
  <div class="stat-card">
    <h3>Present Today</h3>
    <div class="value">{{ today_stats.present or 0 }}</div>
  </div>
  <div class="stat-card">
    <h3>Absent Today</h3>
    <div class="value">{{ today_stats.absent or 0 }}</div>
  </div>
  <div class="stat-card">
    <h3>Late Today</h3>
    <div class="value">{{ today_stats.late or 0 }}</div>
  </div>
  <div class="stat-card">
    <h3>Excused Today</h3>
    <div class="value">{{ today_stats.excused or 0 }}</div>
  </div>
</div>
{% endif %}

<div class="card">
  <h3>Mark Attendance for {{ selected_date }}</h3>
  <form method="post" action="{{ url_for('save_attendance') }}">
    <input type="hidden" name="date" value="{{ selected_date }}">
    {% if current_class %}
    <input type="hidden" name="class_filter" value="{{ current_class }}">
    {% endif %}
    
    <table>
      <thead>
        <tr>
          <th>Admission No</th>
          <th>Name</th>
          <th>Class</th>
          <th>Last 7 Days</th>
          <th>Status</th>
          <th>Remarks</th>
        </tr>
      </thead>
      <tbody>
        {% for student in students %}
        <tr>
          <td>{{ student.admission_number }}</td>
          <td>{{ student.name }}</td>
          <td>{{ student.class }}</td>
          <td>
            {% if student.attendance_summary %}
            P:{{ student.attendance_summary.present }} 
            A:{{ student.attendance_summary.absent }}
            L:{{ student.attendance_summary.late }}
            {% else %}
            No data
            {% endif %}
          </td>
          <td>
            <select name="status_{{ student.id }}">
              <option value="Present" {% if student.status == 'Present' %}selected{% endif %}>Present</option>
              <option value="Absent" {% if student.status == 'Absent' %}selected{% endif %}>Absent</option>
              <option value="Late" {% if student.status == 'Late' %}selected{% endif %}>Late</option>
              <option value="Excused" {% if student.status == 'Excused' %}selected{% endif %}>Excused</option>
            </select>
          </td>
          <td>
            <input type="text" name="remarks_{{ student.id }}" placeholder="Remarks" value="">
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Save Attendance</button>
    </div>
  </form>
</div>
{% endblock %}''',

    'grades.html': '''{% extends "base.html" %}
{% block content %}
<h1>Grades Management</h1>

<div class="action-buttons">
  <a href="{{ url_for('add_grade') }}" class="button">Add New Grade</a>
  <a href="{{ url_for('export_grades') }}" class="button secondary">Export Grades</a>
</div>

<div class="card">
  <h3>Recent Grades</h3>
  {% if recent_grades %}
  <table>
    <thead>
      <tr>
        <th>Student</th>
        <th>Admission No</th>
        <th>Class</th>
        <th>Subject</th>
        <th>Term</th>
        <th>Year</th>
        <th>Score</th>
        <th>Grade</th>
        <th>Remarks</th>
        <th>Date</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for grade in recent_grades %}
      <tr>
        <td>{{ grade.student_name }}</td>
        <td>{{ grade.admission_number }}</td>
        <td>{{ grade.class }}</td>
        <td>{{ grade.subject }}</td>
        <td>{{ grade.term }}</td>
        <td>{{ grade.year }}</td>
        <td>{{ grade.score }}</td>
        <td class="grade-{{ grade.grade }}">{{ grade.grade }}</td>
        <td>{{ grade.remarks or '-' }}</td>
        <td>{{ grade.created_at[:10] }}</td>
        <td>
          <a href="{{ url_for('edit_grade', id=grade.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
          <a href="{{ url_for('delete_grade', id=grade.id) }}" class="button danger" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Delete this grade?')">Delete</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>No grades recorded yet.</p>
  {% endif %}
</div>
{% endblock %}''',

    'add_grade.html': '''{% extends "base.html" %}
{% block content %}
<h1>Add New Grade</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="student_id">Student *</label>
          <select id="student_id" name="student_id" required>
            <option value="">Select Student</option>
            {% for student in students %}
            <option value="{{ student.id }}">{{ student.name }} ({{ student.admission_number }}) - {{ student.class }}</option>
            {% endfor %}
          </select>
        </div>
        
        <div class="form-group">
          <label for="subject">Subject *</label>
          <input type="text" id="subject" name="subject" required placeholder="e.g., Mathematics">
        </div>
        
        <div class="form-group">
          <label for="term">Term *</label>
          <select id="term" name="term" required>
            <option value="">Select Term</option>
            <option value="Term 1">Term 1</option>
            <option value="Term 2">Term 2</option>
            <option value="Term 3">Term 3</option>
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="year">Year *</label>
          <input type="number" id="year" name="year" min="2000" max="2100" value="{{ current_year }}" required>
        </div>
        
        <div class="form-group">
          <label for="score">Score *</label>
          <input type="number" id="score" name="score" min="0" max="100" step="0.01" required placeholder="0-100">
        </div>
        
        <div class="form-group">
          <label for="remarks">Remarks</label>
          <input type="text" id="remarks" name="remarks" placeholder="Grade remarks">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Add Grade</button>
      <button type="reset" class="button secondary">Clear</button>
    </div>
  </form>
</div>

<div class="card">
  <h3>Grading System</h3>
  <table class="grading-system-table">
    <thead>
      <tr>
        <th>Grade</th>
        <th>Score Range</th>
        <th>Color</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="grade-A">A</td>
        <td>{{ grading.min_a }} - {{ grading.max_a }}</td>
        <td><div class="grade-color-box grade-A-bg"></div></td>
      </tr>
      <tr>
        <td class="grade-B">B</td>
        <td>{{ grading.min_b }} - {{ grading.max_b }}</td>
        <td><div class="grade-color-box grade-B-bg"></div></td>
      </tr>
      <tr>
        <td class="grade-C">C</td>
        <td>{{ grading.min_c }} - {{ grading.max_c }}</td>
        <td><div class="grade-color-box grade-C-bg"></div></td>
      </tr>
      <tr>
        <td class="grade-D">D</td>
        <td>{{ grading.min_d }} - {{ grading.max_d }}</td>
        <td><div class="grade-color-box grade-D-bg"></div></td>
      </tr>
      <tr>
        <td class="grade-F">F</td>
        <td>{{ grading.min_f }} - {{ grading.max_f }}</td>
        <td><div class="grade-color-box grade-F-bg"></div></td>
      </tr>
    </tbody>
  </table>
</div>
{% endblock %}''',

    'edit_grade.html': '''{% extends "base.html" %}
{% block content %}
<h1>Edit Grade</h1>

<div class="card">
  <form method="post">
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
      <div>
        <div class="form-group">
          <label for="student_id">Student</label>
          <input type="text" value="{{ grade.student_name }} ({{ grade.admission_number }}) - {{ grade.class }}" readonly>
        </div>
        
        <div class="form-group">
          <label for="subject">Subject *</label>
          <input type="text" id="subject" name="subject" value="{{ grade.subject }}" required>
        </div>
        
        <div class="form-group">
          <label for="term">Term *</label>
          <select id="term" name="term" required>
            <option value="Term 1" {% if grade.term == 'Term 1' %}selected{% endif %}>Term 1</option>
            <option value="Term 2" {% if grade.term == 'Term 2' %}selected{% endif %}>Term 2</option>
            <option value="Term 3" {% if grade.term == 'Term 3' %}selected{% endif %}>Term 3</option>
          </select>
        </div>
      </div>
      
      <div>
        <div class="form-group">
          <label for="year">Year *</label>
          <input type="number" id="year" name="year" min="2000" max="2100" value="{{ grade.year }}" required>
        </div>
        
        <div class="form-group">
          <label for="score">Score *</label>
          <input type="number" id="score" name="score" min="0" max="100" step="0.01" value="{{ grade.score }}" required>
        </div>
        
        <div class="form-group">
          <label for="remarks">Remarks</label>
          <input type="text" id="remarks" name="remarks" value="{{ grade.remarks or '' }}">
        </div>
      </div>
    </div>
    
    <div style="text-align: center; margin-top: 20px;">
      <button type="submit" class="button">Update Grade</button>
      <a href="{{ url_for('grades') }}" class="button secondary">Cancel</a>
    </div>
  </form>
</div>
{% endblock %}''',

    'timetable.html': '''{% extends "base.html" %}
{% block content %}
<h1>Timetable Management</h1>

<div class="tabs">
  <button class="tab active" onclick="toggleTabs('viewTimetable')">View Timetable</button>
  <button class="tab" onclick="toggleTabs('manageTimetable')">Manage Timetable</button>
  <button class="tab" onclick="toggleTabs('addEntry')">Add Entry</button>
</div>

<div id="viewTimetable" class="tab-content active">
  <div class="timetable-controls">
    <div style="display: flex; flex-wrap: wrap; gap: 15px; align-items: center;">
      <div>
        <label for="class_filter">Class:</label>
        <select id="class_filter" onchange="filterTimetable()">
          <option value="">All Classes</option>
          {% for class_name in all_classes %}
          <option value="{{ class_name }}" {% if selected_class == class_name %}selected{% endif %}>{{ class_name }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div>
        <label for="teacher_filter">Teacher:</label>
        <select id="teacher_filter" onchange="filterTimetable()">
          <option value="">All Teachers</option>
          {% for teacher in teachers %}
          <option value="{{ teacher.name }}" {% if selected_teacher == teacher.name %}selected{% endif %}>{{ teacher.name }}</option>
          {% endfor %}
        </select>
      </div>
      
      <div>
        <label for="day_filter">Day:</label>
        <select id="day_filter" onchange="filterTimetable()">
          <option value="">All Days</option>
          <option value="Monday" {% if selected_day == 'Monday' %}selected{% endif %}>Monday</option>
          <option value="Tuesday" {% if selected_day == 'Tuesday' %}selected{% endif %}>Tuesday</option>
          <option value="Wednesday" {% if selected_day == 'Wednesday' %}selected{% endif %}>Wednesday</option>
          <option value="Thursday" {% if selected_day == 'Thursday' %}selected{% endif %}>Thursday</option>
          <option value="Friday" {% if selected_day == 'Friday' %}selected{% endif %}>Friday</option>
          <option value="Saturday" {% if selected_day == 'Saturday' %}selected{% endif %}>Saturday</option>
        </select>
      </div>
    </div>
  </div>

  <div class="color-legend">
    {% for subject in subjects %}
    <div class="color-item">
      <div class="color-box" style="background-color: {{ generate_color(subject) }};"></div>
      <span>{{ subject }}</span>
    </div>
    {% endfor %}
  </div>

  {% if timetable_entries %}
  <div class="timetable-container">
    <table class="timetable">
      <thead>
        <tr>
          <th>Period</th>
          <th>Monday</th>
          <th>Tuesday</th>
          <th>Wednesday</th>
          <th>Thursday</th>
          <th>Friday</th>
          <th>Saturday</th>
        </tr>
      </thead>
      <tbody>
        {% for period in range(1, 9) %}
        <tr>
          <td class="time-slot">Period {{ period }}</td>
          {% for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'] %}
          <td>
            {% set entry = timetable_entries|selectattr('day', 'equalto', day)|selectattr('period', 'equalto', period)|first %}
            {% if entry %}
            <div class="period" data-subject="{{ entry.subject }}" style="background: {{ generate_color(entry.subject) }}">
              <div class="period-details">
                <div class="subject">{{ entry.subject }}</div>
                <div class="teacher">{{ entry.teacher_name or 'N/A' }}</div>
                <div class="room">{{ entry.room or 'N/A' }}</div>
                {% if entry.description %}
                <div style="font-size: 10px; margin-top: 5px;">{{ entry.description }}</div>
                {% endif %}
              </div>
            </div>
            {% else %}
            <div class="period-empty">Free Period</div>
            {% endif %}
          </td>
          {% endfor %}
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% else %}
  <div class="card">
    <p>No timetable entries found for the selected filters.</p>
  </div>
  {% endif %}
</div>

<div id="manageTimetable" class="tab-content">
  <div class="card">
    <h3>All Timetable Entries</h3>
    {% if all_entries %}
    <table>
      <thead>
        <tr>
          <th>Class</th>
          <th>Day</th>
          <th>Period</th>
          <th>Subject</th>
          <th>Teacher</th>
          <th>Room</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for entry in all_entries %}
        <tr>
          <td>{{ entry.class }}</td>
          <td>{{ entry.day }}</td>
          <td>Period {{ entry.period }}</td>
          <td>{{ entry.subject }}</td>
          <td>{{ entry.teacher_name or 'N/A' }}</td>
          <td>{{ entry.room or 'N/A' }}</td>
          <td>
            <a href="{{ url_for('edit_timetable_entry', id=entry.id) }}" class="button" style="padding: 5px 10px; font-size: 12px;">Edit</a>
            <a href="{{ url_for('delete_timetable_entry', id=entry.id) }}" class="button danger" style="padding: 5px 10px; font-size: 12px;" onclick="return confirmDelete('Delete this timetable entry?')">Delete</a>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    {% else %}
    <p>No timetable entries found.</p>
    {% endif %}
  </div>
</div>

<div id="addEntry" class="tab-content">
  <div class="card">
    <h3>Add Timetable Entry</h3>
    <form method="post" action="{{ url_for('add_timetable_entry') }}">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="form-group">
            <label for="class">Class *</label>
            <select id="class" name="class" required>
              <option value="">Select Class</option>
              {% for class_name in all_classes %}
              <option value="{{ class_name }}">{{ class_name }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="form-group">
            <label for="day">Day *</label>
            <select id="day" name="day" required>
              <option value="">Select Day</option>
              <option value="Monday">Monday</option>
              <option value="Tuesday">Tuesday</option>
              <option value="Wednesday">Wednesday</option>
              <option value="Thursday">Thursday</option>
              <option value="Friday">Friday</option>
              <option value="Saturday">Saturday</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="period">Period *</label>
            <select id="period" name="period" required>
              <option value="">Select Period</option>
              {% for i in range(1, 9) %}
              <option value="{{ i }}">Period {{ i }}</option>
              {% endfor %}
            </select>
          </div>
        </div>
        
        <div>
          <div class="form-group">
            <label for="subject">Subject *</label>
            <input type="text" id="subject" name="subject" required placeholder="e.g., Mathematics">
          </div>
          
          <div class="form-group">
            <label for="teacher_id">Teacher</label>
            <select id="teacher_id" name="teacher_id">
              <option value="">Select Teacher</option>
              {% for teacher in teachers %}
              <option value="{{ teacher.id }}">{{ teacher.name }}</option>
              {% endfor %}
            </select>
          </div>
          
          <div class="form-group">
            <label for="room">Room</label>
            <input type="text" id="room" name="room" placeholder="e.g., Room 101">
          </div>
        </div>
      </div>
      
      <div class="form-group">
        <label for="description">Description</label>
        <textarea id="description" name="description" rows="3" placeholder="Optional description"></textarea>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Add Timetable Entry</button>
        <button type="reset" class="button secondary">Clear</button>
      </div>
    </form>
  </div>
</div>

<script>
  function filterTimetable() {
    const classFilter = document.getElementById('class_filter').value;
    const teacherFilter = document.getElementById('teacher_filter').value;
    const dayFilter = document.getElementById('day_filter').value;
    
    let url = '{{ url_for("timetable") }}?';
    if (classFilter) url += 'class_filter=' + encodeURIComponent(classFilter) + '&';
    if (teacherFilter) url += 'teacher=' + encodeURIComponent(teacherFilter) + '&';
    if (dayFilter) url += 'day=' + encodeURIComponent(dayFilter);
    
    window.location.href = url;
  }
</script>
{% endblock %}''',

    'settings.html': '''{% extends "base.html" %}
{% block content %}
<h1>System Settings</h1>

<div class="tabs">
  <button class="tab active" onclick="toggleTabs('schoolSettings')">School Settings</button>
  <button class="tab" onclick="toggleTabs('gradingSystem')">Grading System</button>
  <button class="tab" onclick="toggleTabs('backupRestore')">Backup & Restore</button>
</div>

<div id="schoolSettings" class="tab-content active">
  <div class="card">
    <h3>School Information</h3>
    <form method="post" action="{{ url_for('update_school_settings') }}" enctype="multipart/form-data">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <div class="form-group">
            <label for="school_name">School Name *</label>
            <input type="text" id="school_name" name="school_name" value="{{ settings.school_name }}" required>
          </div>
          
          <div class="form-group">
            <label for="school_address">School Address</label>
            <textarea id="school_address" name="school_address" rows="3">{{ settings.school_address or '' }}</textarea>
          </div>
        </div>
        
        <div>
          <div class="form-group">
            <label for="school_phone">School Phone</label>
            <input type="tel" id="school_phone" name="school_phone" value="{{ settings.school_phone or '' }}">
          </div>
          
          <div class="form-group">
            <label for="school_email">School Email</label>
            <input type="email" id="school_email" name="school_email" value="{{ settings.school_email or '' }}">
          </div>
          
          <div class="form-group">
            <label for="logo">School Logo</label>
            <input type="file" id="logo" name="logo" accept="image/*">
            {% if settings.logo_path and os.path.exists(settings.logo_path) %}
            <div class="logo-preview">
              <img src="{{ url_for('static', filename=settings.logo_path.replace('static/', '')) }}" alt="School Logo" class="school-logo">
              <p>Current Logo</p>
            </div>
            {% endif %}
          </div>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Save Settings</button>
      </div>
    </form>
  </div>
</div>

<div id="gradingSystem" class="tab-content">
  <div class="card">
    <h3>Current Grading System</h3>
    <table class="grading-system-table">
      <thead>
        <tr>
          <th>Grade</th>
          <th>Minimum Score</th>
          <th>Maximum Score</th>
          <th>Color</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="grade-A">A</td>
          <td>{{ default_grading.min_a }}</td>
          <td>{{ default_grading.max_a }}</td>
          <td><div class="grade-color-box grade-A-bg"></div></td>
        </tr>
        <tr>
          <td class="grade-B">B</td>
          <td>{{ default_grading.min_b }}</td>
          <td>{{ default_grading.max_b }}</td>
          <td><div class="grade-color-box grade-B-bg"></div></td>
        </tr>
        <tr>
          <td class="grade-C">C</td>
          <td>{{ default_grading.min_c }}</td>
          <td>{{ default_grading.max_c }}</td>
          <td><div class="grade-color-box grade-C-bg"></div></td>
        </tr>
        <tr>
          <td class="grade-D">D</td>
          <td>{{ default_grading.min_d }}</td>
          <td>{{ default_grading.max_d }}</td>
          <td><div class="grade-color-box grade-D-bg"></div></td>
        </tr>
        <tr>
          <td class="grade-F">F</td>
          <td>{{ default_grading.min_f }}</td>
          <td>{{ default_grading.max_f }}</td>
          <td><div class="grade-color-box grade-F-bg"></div></td>
        </tr>
      </tbody>
    </table>
  </div>
  
  <div class="card">
    <h3>Edit Grading System</h3>
    <form method="post" action="{{ url_for('update_grading_system') }}">
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
        <div class="form-group">
          <label for="min_a">Min A</label>
          <input type="number" id="min_a" name="min_a" min="0" max="100" value="{{ default_grading.min_a }}" required>
        </div>
        <div class="form-group">
          <label for="max_a">Max A</label>
          <input type="number" id="max_a" name="max_a" min="0" max="100" value="{{ default_grading.max_a }}" required>
        </div>
        <div class="form-group">
          <label for="min_b">Min B</label>
          <input type="number" id="min_b" name="min_b" min="0" max="100" value="{{ default_grading.min_b }}" required>
        </div>
        <div class="form-group">
          <label for="max_b">Max B</label>
          <input type="number" id="max_b" name="max_b" min="0" max="100" value="{{ default_grading.max_b }}" required>
        </div>
        <div class="form-group">
          <label for="min_c">Min C</label>
          <input type="number" id="min_c" name="min_c" min="0" max="100" value="{{ default_grading.min_c }}" required>
        </div>
        <div class="form-group">
          <label for="max_c">Max C</label>
          <input type="number" id="max_c" name="max_c" min="0" max="100" value="{{ default_grading.max_c }}" required>
        </div>
        <div class="form-group">
          <label for="min_d">Min D</label>
          <input type="number" id="min_d" name="min_d" min="0" max="100" value="{{ default_grading.min_d }}" required>
        </div>
        <div class="form-group">
          <label for="max_d">Max D</label>
          <input type="number" id="max_d" name="max_d" min="0" max="100" value="{{ default_grading.max_d }}" required>
        </div>
        <div class="form-group">
          <label for="min_f">Min F</label>
          <input type="number" id="min_f" name="min_f" min="0" max="100" value="{{ default_grading.min_f }}" required>
        </div>
        <div class="form-group">
          <label for="max_f">Max F</label>
          <input type="number" id="max_f" name="max_f" min="0" max="100" value="{{ default_grading.max_f }}" required>
        </div>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button">Update Grading System</button>
      </div>
    </form>
  </div>
</div>

<div id="backupRestore" class="tab-content">
  <div class="card">
    <h3>Database Backup</h3>
    <p>Create a backup of the entire database.</p>
    <div class="action-buttons">
      <a href="{{ url_for('backup_database') }}" class="button" onclick="return confirm('Create database backup?')">
        <i class="fas fa-download"></i> Backup Database
      </a>
    </div>
  </div>
  
  <div class="card">
    <h3>Restore Database</h3>
    <p>Warning: This will replace all current data with the backup file.</p>
    <form method="post" action="{{ url_for('restore_database') }}" enctype="multipart/form-data">
      <div class="form-group">
        <label for="backup_file">Select Backup File</label>
        <input type="file" id="backup_file" name="backup_file" accept=".db,.sqlite,.sqlite3" required>
      </div>
      
      <div style="text-align: center; margin-top: 20px;">
        <button type="submit" class="button danger" onclick="return confirm('WARNING: This will overwrite all current data. Continue?')">
          <i class="fas fa-upload"></i> Restore Database
        </button>
      </div>
    </form>
  </div>
</div>
{% endblock %}''',

    'themes.html': '''{% extends "base.html" %}
{% block content %}
<h1>Theme Selection</h1>

<div class="card">
  <h3>Select Theme</h3>
  <p>Choose a theme for the School Management System:</p>
  
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
    <div class="card theme-preview" onclick="applyTheme('modern-blue')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #4361ee, #3a0ca3); border-radius: 8px;"></div>
      <h4>Modern Blue</h4>
      <p>Default blue theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('elegant-green')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #2ecc71, #27ae60); border-radius: 8px;"></div>
      <h4>Elegant Green</h4>
      <p>Fresh green theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('sunset-orange')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #ff7e5f, #feb47b); border-radius: 8px;"></div>
      <h4>Sunset Orange</h4>
      <p>Warm orange theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('dusk-purple')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #654ea3, #da98b4); border-radius: 8px;"></div>
      <h4>Dusk Purple</h4>
      <p>Royal purple theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('forest-teal')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #11998e, #38ef7d); border-radius: 8px;"></div>
      <h4>Forest Teal</h4>
      <p>Nature teal theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('light-theme')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #f9fafb, #f3f4f6); border-radius: 8px;"></div>
      <h4>Light Theme</h4>
      <p>Light mode theme</p>
    </div>
    
    <div class="card theme-preview" onclick="applyTheme('dark-theme')" style="cursor: pointer; text-align: center;">
      <div style="width: 100%; height: 100px; background: linear-gradient(135deg, #1f2937, #111827); border-radius: 8px;"></div>
      <h4>Dark Theme</h4>
      <p>Dark mode theme</p>
    </div>
  </div>
</div>

<div class="card">
  <h3>Current Theme</h3>
  <p>Your current theme preferences are saved in your browser.</p>
  <p>To reset to default theme, clear your browser cookies or select "Modern Blue".</p>
</div>
{% endblock %}''',

    'receipt.html': '''{% extends "base.html" %}
{% block content %}
<div class="receipt">
  <div class="receipt-header">
    <h2>FEE PAYMENT RECEIPT</h2>
    <p>{{ settings.school_name }}</p>
    {% if settings.school_address %}<p>{{ settings.school_address }}</p>{% endif %}
    {% if settings.school_phone %}<p>Tel: {{ settings.school_phone }}</p>{% endif %}
  </div>
  
  <table class="receipt-details">
    <tr>
      <td><strong>Receipt No:</strong></td>
      <td>{{ payment.receipt_number }}</td>
      <td><strong>Date:</strong></td>
      <td>{{ payment.date_paid }}</td>
    </tr>
    <tr>
      <td><strong>Student Name:</strong></td>
      <td>{{ student.name }}</td>
      <td><strong>Admission No:</strong></td>
      <td>{{ student.admission_number }}</td>
    </tr>
    <tr>
      <td><strong>Class:</strong></td>
      <td>{{ student.class }}</td>
      <td><strong>Term:</strong></td>
      <td>{{ payment.term }} {{ payment.year }}</td>
    </tr>
    <tr>
      <td><strong>Total Fee:</strong></td>
      <td>{{ fee_structure.amount }}</td>
      <td><strong>Amount Paid:</strong></td>
      <td class="paid">{{ payment.amount_paid }}</td>
    </tr>
    <tr>
      <td><strong>Previous Balance:</strong></td>
      <td>{{ previous_balance }}</td>
      <td><strong>New Balance:</strong></td>
      <td class="balance">{{ new_balance }}</td>
    </tr>
    <tr>
      <td><strong>Payment Method:</strong></td>
      <td>{{ payment.payment_method or 'Cash' }}</td>
      <td><strong>Transaction ID:</strong></td>
      <td>{{ payment.transaction_id or 'N/A' }}</td>
    </tr>
    {% if payment.remarks %}
    <tr>
      <td><strong>Remarks:</strong></td>
      <td colspan="3">{{ payment.remarks }}</td>
    </tr>
    {% endif %}
  </table>
  
  <div style="text-align: center; margin-top: 40px;">
    <p>_________________________</p>
    <p>Cashier's Signature</p>
  </div>
  
  <div style="text-align: center; margin-top: 20px; font-size: 12px; color: #666;">
    <p>Thank you for your payment!</p>
    <p>Keep this receipt for your records.</p>
  </div>
</div>

<div class="action-buttons no-print">
  <button onclick="printReceipt()" class="button"><i class="fas fa-print"></i> Print Receipt</button>
  <a href="{{ url_for('fees') }}" class="button secondary"><i class="fas fa-arrow-left"></i> Back to Fees</a>
</div>
{% endblock %}''',

    'medical_info.html': '''{% extends "base.html" %}
{% block content %}
<h1>Medical Information - {{ student.name }}</h1>

<div class="card">
  <h3>Basic Information</h3>
  <table>
    <tr>
      <th>Admission Number:</th>
      <td>{{ student.admission_number }}</td>
    </tr>
    <tr>
      <th>Name:</th>
      <td>{{ student.name }}</td>
    </tr>
    <tr>
      <th>Class:</th>
      <td>{{ student.class }}</td>
    </tr>
    <tr>
      <th>Age:</th>
      <td>{{ student.age or 'N/A' }}</td>
    </tr>
  </table>
</div>

<div class="card">
  <h3>Medical Status</h3>
  <div class="medical-alert {% if student.has_medical_condition %}danger{% else %}info{% endif %}">
    <i class="fas fa-heartbeat"></i>
    <strong>Medical Condition:</strong>
    {% if student.has_medical_condition %}
    Has Special Medical Condition
    {% else %}
    No Special Medical Conditions
    {% endif %}
  </div>
  
  {% if student.medical_conditions %}
  <div style="margin-top: 15px;">
    <h4>Medical Conditions</h4>
    <p>{{ student.medical_conditions }}</p>
  </div>
  {% endif %}
  
  {% if student.allergies %}
  <div style="margin-top: 15px;">
    <h4>Allergies</h4>
    <p>{{ student.allergies }}</p>
  </div>
  {% endif %}
  
  {% if student.medications %}
  <div style="margin-top: 15px;">
    <h4>Current Medications</h4>
    <p>{{ student.medications }}</p>
  </div>
  {% endif %}
  
  {% if student.blood_type %}
  <div style="margin-top: 15px;">
    <h4>Blood Type</h4>
    <p>{{ student.blood_type }}</p>
  </div>
  {% endif %}
</div>

<div class="card">
  <h3>Emergency Contact</h3>
  {% if student.emergency_contact_name %}
  <table>
    <tr>
      <th>Name:</th>
      <td>{{ student.emergency_contact_name }}</td>
    </tr>
    <tr>
      <th>Relationship:</th>
      <td>{{ student.emergency_contact_relation }}</td>
    </tr>
    <tr>
      <th>Phone:</th>
      <td>{{ student.emergency_contact_phone }}</td>
    </tr>
    {% if student.emergency_contact_alt_phone %}
    <tr>
      <th>Alternate Phone:</th>
      <td>{{ student.emergency_contact_alt_phone }}</td>
    </tr>
    {% endif %}
  </table>
  {% else %}
  <p>No emergency contact information available.</p>
  {% endif %}
</div>

<div class="action-buttons">
  <a href="{{ url_for('edit_student', id=student.id) }}" class="button">Edit Student</a>
  <a href="{{ url_for('students') }}" class="button secondary">Back to Students</a>
</div>
{% endblock %}'''
}

# Set Jinja loader
app.jinja_loader = DictLoader(templates)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database with enhanced schema
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript('''
    -- Users table for authentication
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
        admission_number TEXT,
        teacher_id INTEGER,
        is_active BOOLEAN DEFAULT 1,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
    );
    
    -- Students table with enhanced fields including medical information
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admission_number TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        age INTEGER,
        class TEXT,
        passport_photo TEXT,
        guardian_name TEXT,
        guardian_contacts TEXT,
        guardian_email TEXT,
        address TEXT,
        
        -- Medical Information Fields
        has_medical_condition BOOLEAN DEFAULT 0,
        medical_conditions TEXT,
        allergies TEXT,
        medications TEXT,
        blood_type TEXT,
        insurance_provider TEXT,
        insurance_policy_number TEXT,
        
        -- Emergency Contact Information
        emergency_contact_name TEXT,
        emergency_contact_relation TEXT,
        emergency_contact_phone TEXT,
        emergency_contact_alt_phone TEXT,
        emergency_contact_email TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Teachers table with enhanced fields
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        qualification TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Subjects table
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    
    -- Teacher subjects junction table
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        teacher_id INTEGER,
        subject_id INTEGER,
        PRIMARY KEY (teacher_id, subject_id),
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    );
    
    -- Classes table
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        teacher_id INTEGER,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id)
    );
    
    -- Fee structures table - FIXED
    CREATE TABLE IF NOT EXISTS fee_structures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class TEXT NOT NULL,
        term TEXT NOT NULL,
        year INTEGER NOT NULL,
        amount REAL NOT NULL DEFAULT 0,
        description TEXT,
        due_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(class, term, year)
    );
    
    -- Fee payments table - FIXED
    CREATE TABLE IF NOT EXISTS fee_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        fee_structure_id INTEGER NOT NULL,
        amount_paid REAL NOT NULL DEFAULT 0,
        date_paid TEXT NOT NULL,
        receipt_number TEXT UNIQUE NOT NULL,
        payment_method TEXT DEFAULT 'Cash',
        transaction_id TEXT,
        reference TEXT,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (fee_structure_id) REFERENCES fee_structures(id) ON DELETE CASCADE
    );
    
    -- Attendance table - FIXED
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    
    -- Grades table
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        term TEXT NOT NULL,
        year INTEGER NOT NULL,
        score REAL NOT NULL,
        grade TEXT,
        remarks TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    
    -- Timetable table - NEW
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class TEXT NOT NULL,
        day TEXT NOT NULL,
        period INTEGER NOT NULL,
        subject TEXT NOT NULL,
        teacher_id INTEGER,
        room TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
    );
    
    -- Grading system table - NEW
    CREATE TABLE IF NOT EXISTS grading_system (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        min_a INTEGER DEFAULT 80,
        max_a INTEGER DEFAULT 100,
        min_b INTEGER DEFAULT 70,
        max_b INTEGER DEFAULT 79,
        min_c INTEGER DEFAULT 60,
        max_c INTEGER DEFAULT 69,
        min_d INTEGER DEFAULT 50,
        max_d INTEGER DEFAULT 59,
        min_f INTEGER DEFAULT 0,
        max_f INTEGER DEFAULT 49,
        is_default BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- School settings table - NEW
    CREATE TABLE IF NOT EXISTS school_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        school_name TEXT DEFAULT 'School Management System',
        school_address TEXT,
        school_phone TEXT,
        school_email TEXT,
        logo_path TEXT DEFAULT 'static/logos/default_logo.png',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_users_admission ON users(admission_number);
    
    CREATE INDEX IF NOT EXISTS idx_students_admission ON students(admission_number);
    CREATE INDEX IF NOT EXISTS idx_students_class ON students(class);
    CREATE INDEX IF NOT EXISTS idx_students_created ON students(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
    CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
    CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance(student_id, date);
    
    CREATE INDEX IF NOT EXISTS idx_fee_payments_receipt ON fee_payments(receipt_number);
    CREATE INDEX IF NOT EXISTS idx_fee_payments_date ON fee_payments(date_paid);
    CREATE INDEX IF NOT EXISTS idx_fee_payments_student ON fee_payments(student_id);
    CREATE INDEX IF NOT EXISTS idx_fee_payments_structure ON fee_payments(fee_structure_id);
    
    CREATE INDEX IF NOT EXISTS idx_fee_structures_class ON fee_structures(class);
    CREATE INDEX IF NOT EXISTS idx_fee_structures_term ON fee_structures(term, year);
    
    CREATE INDEX IF NOT EXISTS idx_grades_student ON grades(student_id);
    CREATE INDEX IF NOT EXISTS idx_grades_subject ON grades(subject);
    CREATE INDEX IF NOT EXISTS idx_grades_term_year ON grades(term, year);
    
    CREATE INDEX IF NOT EXISTS idx_timetable_class ON timetable(class);
    CREATE INDEX IF NOT EXISTS idx_timetable_day ON timetable(day);
    CREATE INDEX IF NOT EXISTS idx_timetable_class_day ON timetable(class, day);
    
    CREATE INDEX IF NOT EXISTS idx_grading_system_default ON grading_system(is_default);
    
    -- Insert default subjects
    INSERT OR IGNORE INTO subjects (name) VALUES 
        ('Mathematics'), ('English'), ('Science'), ('History'), ('Geography'),
        ('Physics'), ('Chemistry'), ('Biology'), ('Business Studies'), ('Computer Studies');
    
    -- Insert default grading system if none exists
    INSERT OR IGNORE INTO grading_system (name, min_a, max_a, min_b, max_b, min_c, max_c, min_d, max_d, min_f, max_f, is_default)
    VALUES ('Default Grading System', 80, 100, 70, 79, 60, 69, 50, 59, 0, 49, 1);
    
    -- Insert default school settings if none exists
    INSERT OR IGNORE INTO school_settings (id, school_name) VALUES (1, 'School Management System');
    ''')

    # Check if admin user exists
    admin_exists = cursor.execute('SELECT id FROM users WHERE username = "admin"').fetchone()
    
    if not admin_exists:
        # Create admin user with correct password hash
        password_hash = generate_password_hash('school123')
        cursor.execute('''
            INSERT INTO users (username, password_hash, full_name, role, is_active) 
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'Administrator', 'admin', 1))
    
    conn.commit()
    conn.close()

# Call init at startup
init_db()

# Helper functions
def generate_receipt_number():
    """Generate a unique receipt number"""
    return f"RCPT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

def calculate_grade(score):
    """Calculate grade based on custom grading system"""
    conn = get_db_connection()
    
    try:
        # Get the default grading system
        grading = conn.execute('''
            SELECT * FROM grading_system WHERE is_default = 1 LIMIT 1
        ''').fetchone()
        
        if not grading:
            # Fallback to default if no grading system found
            if score >= 80:
                return 'A'
            elif score >= 70:
                return 'B'
            elif score >= 60:
                return 'C'
            elif score >= 50:
                return 'D'
            else:
                return 'F'
        
        # Use custom grading system
        score = float(score)
        if score >= grading['min_a'] and score <= grading['max_a']:
            return 'A'
        elif score >= grading['min_b'] and score <= grading['max_b']:
            return 'B'
        elif score >= grading['min_c'] and score <= grading['max_c']:
            return 'C'
        elif score >= grading['min_d'] and score <= grading['max_d']:
            return 'D'
        else:
            return 'F'
            
    except Exception as e:
        print(f"Error calculating grade: {e}")
        # Fallback to simple calculation
        if score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        elif score >= 50:
            return 'D'
        else:
            return 'F'
    finally:
        conn.close()

def calculate_student_balance(student_id, fee_structure_id):
    """Calculate balance for a student's fee structure"""
    conn = get_db_connection()
    
    try:
        # Get total paid for this fee structure
        total_paid_result = conn.execute('''
            SELECT COALESCE(SUM(amount_paid), 0) as total_paid
            FROM fee_payments 
            WHERE student_id = ? AND fee_structure_id = ?
        ''', (student_id, fee_structure_id)).fetchone()
        total_paid = total_paid_result['total_paid'] if total_paid_result else 0
        
        # Get total fee amount
        fee_amount_result = conn.execute('''
            SELECT amount FROM fee_structures WHERE id = ?
        ''', (fee_structure_id,)).fetchone()
        fee_amount = fee_amount_result['amount'] if fee_amount_result else 0
        
        return fee_amount - total_paid
    except Exception as e:
        print(f"Error calculating balance: {e}")
        return 0
    finally:
        conn.close()

def get_total_paid_for_student(student_id):
    """Get total paid by student across all fee structures"""
    conn = get_db_connection()
    try:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount_paid), 0) as total_paid
            FROM fee_payments 
            WHERE student_id = ?
        ''', (student_id,)).fetchone()
        return result['total_paid'] if result else 0
    finally:
        conn.close()

def get_total_fee_for_class(class_name):
    """Get total fee for a class across all terms"""
    conn = get_db_connection()
    try:
        result = conn.execute('''
            SELECT COALESCE(SUM(amount), 0) as total_fee
            FROM fee_structures 
            WHERE class = ?
        ''', (class_name,)).fetchone()
        return result['total_fee'] if result else 0
    finally:
        conn.close()

def generate_color(subject):
    """Generate color for timetable subject"""
    if not subject:
        return '#999999'
    
    color_map = {
        'mathematics': "#d14444",
        'english': "#bb57f5",
        'science': '#4facfe',
        'history': '#43e97b',
        'geography': '#fee140',
        'physics': '#30cfd0',
        'chemistry': '#a8edea',
        'biology': '#5ee7df',
        'computer': '#d299c2',
        'art': '#f6d365',
        'physical education': '#a1c4fd',
        'pe': '#a1c4fd',
        'music': '#fcb69f',
        'business': '#c2e9fb',
        'religious': '#fed6e3'
    }
    
    subject = subject.lower().strip()
    for key, color in color_map.items():
        if key in subject:
            return color
    
    # Generate consistent color from subject name
    hash_val = 0
    for char in subject:
        hash_val = ord(char) + ((hash_val << 5) - hash_val)
    hue = hash_val % 360
    return f'hsl({hue}, 70%, 60%)'

def get_school_settings():
    """Get school settings"""
    conn = get_db_connection()
    try:
        settings = conn.execute('SELECT * FROM school_settings WHERE id = 1').fetchone()
        if not settings:
            # Create default settings
            conn.execute('''
                INSERT INTO school_settings (id, school_name) VALUES (1, 'School Management System')
            ''')
            conn.commit()
            settings = conn.execute('SELECT * FROM school_settings WHERE id = 1').fetchone()
        return dict(settings) if settings else {}
    finally:
        conn.close()

def get_current_user_role():
    """Get current user's role from session"""
    return session.get('role')

def get_current_user_id():
    """Get current user's ID from session"""
    return session.get('user_id')

@app.context_processor
def inject_today():
    return {
        'today': datetime.today().strftime('%Y-%m-%d'),
        'current_time': datetime.now().strftime('%H:%M:%S'),
        'current_year': datetime.now().year,
        'generate_color': generate_color,
        'calculate_grade': calculate_grade,
        'school_settings': get_school_settings(),
        'os': os
    }

# -------- Authentication Routes --------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        user = conn.execute('''
            SELECT * FROM users 
            WHERE username = ? AND role = ? AND is_active = 1
        ''', (username, role)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            # Update last login
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()
            
            # Set session
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            # Redirect based on role
            if role == 'admin':
                return redirect(url_for('index'))
            elif role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif role == 'student':
                return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid username, password, or role', 'error')
        
        conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# -------- User Management Routes --------

@app.route('/user_management')
@login_required
@role_required('admin')
def user_management():
    role_filter = request.args.get('role', 'all')
    
    conn = get_db_connection()
    
    query = '''
        SELECT u.*, s.name as student_name, t.name as teacher_name
        FROM users u
        LEFT JOIN students s ON u.admission_number = s.admission_number
        LEFT JOIN teachers t ON u.teacher_id = t.id
        WHERE u.id != ?
    '''
    params = [session['user_id']]
    
    if role_filter != 'all':
        query += ' AND u.role = ?'
        params.append(role_filter)
    
    query += ' ORDER BY u.role, u.username'
    
    users = conn.execute(query, params).fetchall()
    
    # Get all users for reset password dropdown
    all_users = conn.execute('SELECT id, username, role, full_name FROM users WHERE id != ?', 
                           (session['user_id'],)).fetchall()
    
    # Get all teachers for dropdown
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    
    conn.close()
    
    return render_template('user_management.html', 
                         users=users, 
                         all_users=all_users,
                         teachers=teachers,
                         role_filter=role_filter)

@app.route('/user/add', methods=['POST'])
@login_required
@role_required('admin')
def add_user():
    username = request.form['username']
    full_name = request.form.get('full_name', '')
    email = request.form.get('email', '')
    role = request.form['role']
    admission_number = request.form.get('admission_number', '') if role == 'student' else None
    teacher_id = request.form.get('teacher_id', '') if role == 'teacher' else None
    is_active = 'is_active' in request.form
    
    # Default password
    password_hash = generate_password_hash('school123')
    
    conn = get_db_connection()
    
    try:
        # Check if username already exists
        existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            flash('Username already exists!', 'error')
            return redirect(url_for('user_management'))
        
        # Insert new user
        conn.execute('''
            INSERT INTO users (username, password_hash, full_name, email, role, 
                             admission_number, teacher_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, full_name, email, role, 
              admission_number, teacher_id, 1 if is_active else 0))
        
        conn.commit()
        flash(f'User {username} added successfully! Default password: school123', 'success')
        
    except sqlite3.IntegrityError as e:
        flash(f'Error adding user: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form.get('full_name', '')
        email = request.form.get('email', '')
        role = request.form['role']
        is_active = 'is_active' in request.form
        
        try:
            # Check if username already exists (excluding current user)
            existing = conn.execute('''
                SELECT id FROM users WHERE username = ? AND id != ?
            ''', (username, id)).fetchone()
            
            if existing:
                flash('Username already exists!', 'error')
                return redirect(url_for('edit_user', id=id))
            
            # Update user
            conn.execute('''
                UPDATE users 
                SET username = ?, full_name = ?, email = ?, role = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (username, full_name, email, role, 1 if is_active else 0, id))
            
            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('user_management'))
            
        except Exception as e:
            flash(f'Error updating user: {str(e)}', 'error')
            return redirect(url_for('edit_user', id=id))
    
    # GET request
    user = conn.execute('''
        SELECT u.*, s.name as student_name, t.name as teacher_name
        FROM users u
        LEFT JOIN students s ON u.admission_number = s.admission_number
        LEFT JOIN teachers t ON u.teacher_id = t.id
        WHERE u.id = ?
    ''', (id,)).fetchone()
    
    conn.close()
    
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('user_management'))
    
    return render_template('edit_user.html', user=user)

@app.route('/user/toggle_status/<int:id>')
@login_required
@role_required('admin')
def toggle_user_status(id):
    if id == session['user_id']:
        flash('You cannot deactivate your own account!', 'error')
        return redirect(url_for('user_management'))
    
    conn = get_db_connection()
    
    try:
        user = conn.execute('SELECT is_active FROM users WHERE id = ?', (id,)).fetchone()
        if user:
            new_status = 0 if user['is_active'] else 1
            conn.execute('UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                        (new_status, id))
            conn.commit()
            
            status_text = 'activated' if new_status else 'deactivated'
            flash(f'User {status_text} successfully!', 'success')
    except Exception as e:
        flash(f'Error toggling user status: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

@app.route('/user/reset_password/<int:id>')
@login_required
@role_required('admin')
def reset_user_password(id):
    conn = get_db_connection()
    
    try:
        # Reset to default password
        password_hash = generate_password_hash('school123')
        conn.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (password_hash, id))
        
        conn.commit()
        flash('Password reset to default (school123) successfully!', 'success')
    except Exception as e:
        flash(f'Error resetting password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

@app.route('/user/reset_password_bulk', methods=['POST'])
@login_required
@role_required('admin')
def reset_password_bulk():
    user_id = request.form['user_id']
    new_password = request.form.get('new_password', '')
    
    if not new_password:
        new_password = 'school123'  # Default password
    
    conn = get_db_connection()
    
    try:
        password_hash = generate_password_hash(new_password)
        conn.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (password_hash, user_id))
        
        conn.commit()
        flash(f'Password reset successfully!', 'success')
    except Exception as e:
        flash(f'Error resetting password: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('user_management'))

# -------- Student Dashboard Routes --------

@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    conn = get_db_connection()
    
    # Get student information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if not user or not user['admission_number']:
        flash('Student information not found!', 'error')
        return redirect(url_for('logout'))
    
    student = conn.execute('SELECT * FROM students WHERE admission_number = ?', 
                          (user['admission_number'],)).fetchone()
    
    if not student:
        flash('Student record not found!', 'error')
        return redirect(url_for('logout'))
    
    # Get today's timetable
    today = datetime.today().strftime('%A')
    today_timetable = conn.execute('''
        SELECT t.*, te.name as teacher_name
        FROM timetable t
        LEFT JOIN teachers te ON t.teacher_id = te.id
        WHERE t.class = ? AND t.day = ?
        ORDER BY t.period
    ''', (student['class'], today)).fetchall()
    
    # Get recent grades
    recent_grades = conn.execute('''
        SELECT * FROM grades 
        WHERE student_id = ? 
        ORDER BY created_at DESC 
        LIMIT 5
    ''', (student['id'],)).fetchall()
    
    # Calculate attendance rate
    attendance_records = conn.execute('''
        SELECT status FROM attendance 
        WHERE student_id = ? AND date >= date('now', '-30 days')
    ''', (student['id'],)).fetchall()
    
    if attendance_records:
        present_count = sum(1 for r in attendance_records if r['status'] in ['Present', 'Late'])
        attendance_rate = (present_count / len(attendance_records)) * 100
    else:
        attendance_rate = 0
    
    # Calculate average grade
    grades = conn.execute('SELECT score FROM grades WHERE student_id = ?', (student['id'],)).fetchall()
    if grades:
        average_score = sum(g['score'] for g in grades) / len(grades)
        average_grade = calculate_grade(average_score)
    else:
        average_grade = 'N/A'
    
    # Calculate fee balance
    fee_structures = conn.execute('''
        SELECT fs.*, 
               COALESCE((
                   SELECT SUM(fp.amount_paid) 
                   FROM fee_payments fp 
                   WHERE fp.fee_structure_id = fs.id 
                   AND fp.student_id = ?
               ), 0) as paid_amount
        FROM fee_structures fs
        WHERE fs.class = ?
    ''', (student['id'], student['class'])).fetchall()
    
    total_balance = sum(fs['amount'] - fs['paid_amount'] for fs in fee_structures)
    
    # Get medical information
    medical_info = {
        'has_condition': student['has_medical_condition'],
        'conditions': student['medical_conditions'],
        'allergies': student['allergies'],
        'medications': student['medications'],
        'blood_type': student['blood_type'],
        'emergency_contact_name': student['emergency_contact_name'],
        'emergency_contact_relation': student['emergency_contact_relation'],
        'emergency_contact_phone': student['emergency_contact_phone'],
        'emergency_contact_alt_phone': student['emergency_contact_alt_phone'],
        'emergency_contact_email': student['emergency_contact_email']
    }
    
    conn.close()
    
    return render_template('student_dashboard.html',
                         student=student,
                         today_timetable=today_timetable,
                         recent_grades=recent_grades,
                         attendance_rate=round(attendance_rate, 1),
                         average_grade=average_grade,
                         fee_balance=total_balance,
                         medical_info=medical_info)

@app.route('/student/grades')
@login_required
@role_required('student')
def student_grades():
    conn = get_db_connection()
    
    # Get student information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    student = conn.execute('SELECT * FROM students WHERE admission_number = ?', 
                          (user['admission_number'],)).fetchone()
    
    # Get all grades
    grades = conn.execute('''
        SELECT * FROM grades 
        WHERE student_id = ? 
        ORDER BY year DESC, term, subject
    ''', (student['id'],)).fetchall()
    
    # Calculate term summary
    term_summary = {}
    for grade in grades:
        term_key = f"{grade['year']} {grade['term']}"
        if term_key not in term_summary:
            term_summary[term_key] = {'scores': [], 'grades': []}
        term_summary[term_key]['scores'].append(grade['score'])
        term_summary[term_key]['grades'].append(grade['grade'])
    
    # Calculate averages
    for term, data in term_summary.items():
        data['count'] = len(data['scores'])
        data['average'] = sum(data['scores']) / len(data['scores'])
        data['grade'] = calculate_grade(data['average'])
        # You can add position calculation here if you track class rankings
    
    # Calculate subject performance
    subject_scores = {}
    for grade in grades:
        subject = grade['subject']
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(grade['score'])
    
    subject_performance = []
    for subject, scores in subject_scores.items():
        avg_score = sum(scores) / len(scores)
        subject_performance.append({
            'name': subject,
            'average_score': avg_score,
            'grade': calculate_grade(avg_score)
        })
    
    conn.close()
    
    return render_template('student_grades.html',
                         grades=grades,
                         term_summary=term_summary,
                         subject_performance=sorted(subject_performance, key=lambda x: x['average_score'], reverse=True))

@app.route('/student/attendance')
@login_required
@role_required('student')
def student_attendance():
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    
    conn = get_db_connection()
    
    # Get student information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    student = conn.execute('SELECT * FROM students WHERE admission_number = ?', 
                          (user['admission_number'],)).fetchone()
    
    # Calculate attendance statistics
    all_attendance = conn.execute('''
        SELECT status FROM attendance WHERE student_id = ?
    ''', (student['id'],)).fetchall()
    
    if all_attendance:
        total = len(all_attendance)
        present = sum(1 for r in all_attendance if r['status'] == 'Present')
        absent = sum(1 for r in all_attendance if r['status'] == 'Absent')
        late = sum(1 for r in all_attendance if r['status'] == 'Late')
        excused = sum(1 for r in all_attendance if r['status'] == 'Excused')
        rate = (present + late) / total * 100
    else:
        total = present = absent = late = excused = rate = 0
    
    attendance_stats = {
        'total': total,
        'present': present,
        'absent': absent,
        'late': late,
        'excused': excused,
        'rate': round(rate, 1)
    }
    
    # Get recent attendance
    recent_attendance = conn.execute('''
        SELECT * FROM attendance 
        WHERE student_id = ? 
        ORDER BY date DESC 
        LIMIT 10
    ''', (student['id'],)).fetchall()
    
    # Get monthly attendance
    start_date = f"{month}-01"
    year, mon = map(int, month.split('-'))
    if mon == 12:
        next_month = f"{year+1}-01-01"
    else:
        next_month = f"{year}-{mon+1:02d}-01"
    
    end_date = (datetime.strptime(next_month, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    
    monthly_attendance = conn.execute('''
        SELECT *, strftime('%w', date) as day_of_week
        FROM attendance 
        WHERE student_id = ? AND date BETWEEN ? AND ?
        ORDER BY date
    ''', (student['id'], start_date, end_date)).fetchall()
    
    # Convert day numbers to names
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    for record in monthly_attendance:
        record = dict(record)
        record['day_name'] = day_names[int(record['day_of_week'])]
    
    conn.close()
    
    return render_template('student_attendance.html',
                         attendance_stats=attendance_stats,
                         recent_attendance=recent_attendance,
                         monthly_attendance=monthly_attendance,
                         month=month)

@app.route('/student/fees')
@login_required
@role_required('student')
def student_fees():
    conn = get_db_connection()
    
    # Get student information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    student = conn.execute('SELECT * FROM students WHERE admission_number = ?', 
                          (user['admission_number'],)).fetchone()
    
    # Get fee structures with payments
    fee_structures = conn.execute('''
        SELECT fs.*, 
               COALESCE((
                   SELECT SUM(fp.amount_paid) 
                   FROM fee_payments fp 
                   WHERE fp.fee_structure_id = fs.id 
                   AND fp.student_id = ?
               ), 0) as paid_amount,
               fs.amount - COALESCE((
                   SELECT SUM(fp.amount_paid) 
                   FROM fee_payments fp 
                   WHERE fp.fee_structure_id = fs.id 
                   AND fp.student_id = ?
               ), 0) as balance
        FROM fee_structures fs
        WHERE fs.class = ?
        ORDER BY fs.year DESC, 
                 CASE fs.term 
                     WHEN 'Term 1' THEN 1 
                     WHEN 'Term 2' THEN 2 
                     WHEN 'Term 3' THEN 3 
                 END
    ''', (student['id'], student['id'], student['class'])).fetchall()
    
    # Calculate fee summary
    total_fee = sum(fs['amount'] for fs in fee_structures)
    total_paid = sum(fs['paid_amount'] for fs in fee_structures)
    total_balance = total_fee - total_paid
    
    fee_summary = {
        'total_fee': total_fee,
        'total_paid': total_paid,
        'balance': total_balance
    }
    
    # Get payment history
    payments = conn.execute('''
        SELECT fp.*, fs.term, fs.year
        FROM fee_payments fp
        JOIN fee_structures fs ON fp.fee_structure_id = fs.id
        WHERE fp.student_id = ?
        ORDER BY fp.date_paid DESC
    ''', (student['id'],)).fetchall()
    
    conn.close()
    
    return render_template('student_fees.html',
                         fee_structures=fee_structures,
                         fee_summary=fee_summary,
                         payments=payments)

# -------- Teacher Dashboard Routes --------

@app.route('/teacher/dashboard')
@login_required
@role_required('teacher')
def teacher_dashboard():
    conn = get_db_connection()
    
    # Get teacher information
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if user and user['teacher_id']:
        teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (user['teacher_id'],)).fetchone()
    else:
        # Try to find teacher by name
        teacher = conn.execute('SELECT * FROM teachers WHERE name LIKE ?', 
                              (f"%{user['full_name']}%",)).fetchone()
    
    if not teacher:
        flash('Teacher information not found!', 'error')
        return redirect(url_for('logout'))
    
    # Get today's schedule
    today = datetime.today().strftime('%A')
    today_schedule = conn.execute('''
        SELECT * FROM timetable 
        WHERE teacher_id = ? AND day = ?
        ORDER BY period
    ''', (teacher['id'], today)).fetchall()
    
    # Get assigned classes
    my_classes = conn.execute('''
        SELECT c.*, 
               (SELECT COUNT(*) FROM students s WHERE s.class = c.name) as student_count
        FROM classes c
        WHERE c.teacher_id = ?
        ORDER BY c.name
    ''', (teacher['id'],)).fetchall()
    
    # Get recent attendance marked by this teacher
    recent_attendance = conn.execute('''
        SELECT a.*, s.name as student_name, s.class
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE s.class IN (SELECT name FROM classes WHERE teacher_id = ?)
        ORDER BY a.date DESC
        LIMIT 10
    ''', (teacher['id'],)).fetchall()
    
    # Calculate statistics
    stats = {
        'class_count': len(my_classes),
        'student_count': sum(cls['student_count'] for cls in my_classes),
        'today_classes': len(today_schedule),
        'pending_grades': conn.execute('''
            SELECT COUNT(*) FROM grades 
            WHERE subject IN (SELECT subject FROM timetable WHERE teacher_id = ?)
        ''', (teacher['id'],)).fetchone()[0]
    }
    
    conn.close()
    
    return render_template('teacher_dashboard.html',
                         teacher=teacher,
                         today_schedule=today_schedule,
                         my_classes=my_classes,
                         recent_attendance=recent_attendance,
                         stats=stats)

# -------- Student Routes --------

@app.route('/students')
@login_required
@role_required('admin', 'teacher')
def students():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY class, name').fetchall()
    conn.close()
    return render_template('students.html', students=students)

@app.route('/students/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_student():
    if request.method == 'POST':
        admission_number = request.form['admission_number']
        name = request.form['name']
        age = request.form.get('age')
        class_name = request.form['class']
        guardian_name = request.form.get('guardian_name', '')
        guardian_contacts = request.form.get('guardian_contacts', '')
        guardian_email = request.form.get('guardian_email', '')
        address = request.form.get('address', '')
        
        # Medical Information
        has_medical_condition = 'has_medical_condition' in request.form
        medical_conditions = request.form.get('medical_conditions', '')
        allergies = request.form.get('allergies', '')
        medications = request.form.get('medications', '')
        blood_type = request.form.get('blood_type', '')
        
        # Emergency Contact
        emergency_contact_name = request.form.get('emergency_contact_name', '')
        emergency_contact_relation = request.form.get('emergency_contact_relation', '')
        emergency_contact_phone = request.form.get('emergency_contact_phone', '')
        emergency_contact_alt_phone = request.form.get('emergency_contact_alt_phone', '')
        emergency_contact_email = request.form.get('emergency_contact_email', '')
        
        if age:
            try:
                age = int(age)
            except ValueError:
                age = None
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO students (
                    admission_number, name, age, class, guardian_name, guardian_contacts,
                    guardian_email, address, has_medical_condition, medical_conditions,
                    allergies, medications, blood_type,
                    emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
                    emergency_contact_alt_phone, emergency_contact_email
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                admission_number, name, age, class_name, guardian_name, guardian_contacts,
                guardian_email, address, 1 if has_medical_condition else 0, medical_conditions,
                allergies, medications, blood_type,
                emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
                emergency_contact_alt_phone, emergency_contact_email
            ))
            conn.commit()
            flash('Student added successfully!', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('Admission number already exists!', 'error')
        finally:
            conn.close()
    
    return render_template('add_student.html')

@app.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_student(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        age = request.form.get('age')
        class_name = request.form['class']
        guardian_name = request.form.get('guardian_name', '')
        guardian_contacts = request.form.get('guardian_contacts', '')
        guardian_email = request.form.get('guardian_email', '')
        address = request.form.get('address', '')
        
        # Medical Information
        has_medical_condition = 'has_medical_condition' in request.form
        medical_conditions = request.form.get('medical_conditions', '')
        allergies = request.form.get('allergies', '')
        medications = request.form.get('medications', '')
        blood_type = request.form.get('blood_type', '')
        
        # Emergency Contact
        emergency_contact_name = request.form.get('emergency_contact_name', '')
        emergency_contact_relation = request.form.get('emergency_contact_relation', '')
        emergency_contact_phone = request.form.get('emergency_contact_phone', '')
        emergency_contact_alt_phone = request.form.get('emergency_contact_alt_phone', '')
        emergency_contact_email = request.form.get('emergency_contact_email', '')
        
        if age:
            try:
                age = int(age)
            except ValueError:
                age = None
        
        try:
            conn.execute('''
                UPDATE students 
                SET name = ?, age = ?, class = ?, guardian_name = ?, guardian_contacts = ?,
                    guardian_email = ?, address = ?, has_medical_condition = ?, medical_conditions = ?,
                    allergies = ?, medications = ?, blood_type = ?,
                    emergency_contact_name = ?, emergency_contact_relation = ?,
                    emergency_contact_phone = ?, emergency_contact_alt_phone = ?, emergency_contact_email = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                name, age, class_name, guardian_name, guardian_contacts,
                guardian_email, address, 1 if has_medical_condition else 0, medical_conditions,
                allergies, medications, blood_type,
                emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
                emergency_contact_alt_phone, emergency_contact_email, id
            ))
            conn.commit()
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students'))
        finally:
            conn.close()
    
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    return render_template('edit_student.html', student=student)

@app.route('/student/medical/<int:id>')
@login_required
@role_required('admin', 'teacher')
def view_medical_info(id):
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not student:
        flash('Student not found!', 'error')
        return redirect(url_for('students'))
    
    return render_template('medical_info.html', student=student)

# -------- Teacher Routes --------

@app.route('/teachers')
@login_required
@role_required('admin')
def teachers():
    conn = get_db_connection()
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    conn.close()
    return render_template('teachers.html', teachers=teachers)

@app.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_teacher():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        qualification = request.form.get('qualification', '')
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO teachers (name, email, phone, qualification)
                VALUES (?, ?, ?, ?)
            ''', (name, email, phone, qualification))
            conn.commit()
            flash('Teacher added successfully!', 'success')
            return redirect(url_for('teachers'))
        finally:
            conn.close()
    
    return render_template('add_teacher.html')

@app.route('/teachers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_teacher(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        qualification = request.form.get('qualification', '')
        
        try:
            conn.execute('''
                UPDATE teachers 
                SET name = ?, email = ?, phone = ?, qualification = ?
                WHERE id = ?
            ''', (name, email, phone, qualification, id))
            conn.commit()
            flash('Teacher updated successfully!', 'success')
            return redirect(url_for('teachers'))
        finally:
            conn.close()
    
    teacher = conn.execute('SELECT * FROM teachers WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not teacher:
        flash('Teacher not found!', 'error')
        return redirect(url_for('teachers'))
    
    return render_template('edit_teacher.html', teacher=teacher)

@app.route('/teachers/delete/<int:id>')
@login_required
@role_required('admin')
def delete_teacher(id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM teachers WHERE id = ?', (id,))
        conn.commit()
        flash('Teacher deleted successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete teacher because they have associated records!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('teachers'))

# -------- Class Routes --------

@app.route('/classes')
@login_required
@role_required('admin', 'teacher')
def classes():
    conn = get_db_connection()
    classes = conn.execute('''
        SELECT c.*, t.name as teacher_name
        FROM classes c
        LEFT JOIN teachers t ON c.teacher_id = t.id
        ORDER BY c.name
    ''').fetchall()

    # Convert classes to dictionaries to allow modification
    classes = [dict(cls) for cls in classes]

    # Get student counts for each class
    for cls in classes:
        count = conn.execute('SELECT COUNT(*) FROM students WHERE class = ?',
                           (cls['name'],)).fetchone()[0]
        cls['student_count'] = count
    
    conn.close()
    return render_template('classes.html', classes=classes)

@app.route('/classes/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_class():
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        teacher_id = request.form.get('teacher_id', '')
        description = request.form.get('description', '')
        
        if teacher_id == '':
            teacher_id = None
        
        try:
            conn.execute('''
                INSERT INTO classes (name, teacher_id, description)
                VALUES (?, ?, ?)
            ''', (name, teacher_id, description))
            conn.commit()
            flash('Class added successfully!', 'success')
            return redirect(url_for('classes'))
        except sqlite3.IntegrityError:
            flash('Class name already exists!', 'error')
        finally:
            conn.close()
    
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    conn.close()
    
    return render_template('add_class.html', teachers=teachers)

@app.route('/classes/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_class(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        name = request.form['name']
        teacher_id = request.form.get('teacher_id', '')
        description = request.form.get('description', '')
        
        if teacher_id == '':
            teacher_id = None
        
        try:
            conn.execute('''
                UPDATE classes 
                SET name = ?, teacher_id = ?, description = ?
                WHERE id = ?
            ''', (name, teacher_id, description, id))
            conn.commit()
            flash('Class updated successfully!', 'success')
            return redirect(url_for('classes'))
        except sqlite3.IntegrityError:
            flash('Class name already exists!', 'error')
        finally:
            conn.close()
    
    cls = conn.execute('SELECT * FROM classes WHERE id = ?', (id,)).fetchone()
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    conn.close()
    
    if not cls:
        flash('Class not found!', 'error')
        return redirect(url_for('classes'))
    
    return render_template('edit_class.html', cls=cls, teachers=teachers)

@app.route('/classes/delete/<int:id>')
@login_required
@role_required('admin')
def delete_class(id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM classes WHERE id = ?', (id,))
        conn.commit()
        flash('Class deleted successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Cannot delete class because it has associated students!', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('classes'))

# -------- Index Route --------

@app.route('/')
@login_required
def index():
    if session.get('role') == 'student':
        return redirect(url_for('student_dashboard'))
    elif session.get('role') == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    
    # Admin dashboard
    conn = get_db_connection()

    total_students = conn.execute('SELECT COUNT(*) FROM students').fetchone()[0]
    total_teachers = conn.execute('SELECT COUNT(*) FROM teachers').fetchone()[0]
    total_classes = conn.execute('SELECT COUNT(*) FROM classes').fetchone()[0]

    # Get recent students
    recent_students = conn.execute('''
        SELECT admission_number, name, class, created_at
        FROM students
        ORDER BY created_at DESC
        LIMIT 5
    ''').fetchall()

    # Get recent payments
    recent_payments = conn.execute('''
        SELECT fp.receipt_number, s.name as student_name, fp.amount_paid, fp.date_paid
        FROM fee_payments fp
        JOIN students s ON fp.student_id = s.id
        ORDER BY fp.date_paid DESC
        LIMIT 5
    ''').fetchall()

    conn.close()

    return render_template('index.html',
                         total_students=total_students,
                         total_teachers=total_teachers,
                         total_classes=total_classes,
                         recent_students=recent_students,
                         recent_payments=recent_payments)

# -------- Fee Management Routes --------

@app.route('/fees')
@login_required
@role_required('admin')
def fees():
    conn = get_db_connection()
    
    # Get recent payments
    recent_payments = conn.execute('''
        SELECT fp.*, s.name as student_name, s.admission_number, 
               s.class as class_name, fs.term, fs.year, fs.amount as total_amount,
               (SELECT COALESCE(SUM(fp2.amount_paid), 0) 
                FROM fee_payments fp2 
                WHERE fp2.student_id = fp.student_id 
                AND fp2.fee_structure_id = fp.fee_structure_id) as total_paid,
               fs.amount - (SELECT COALESCE(SUM(fp2.amount_paid), 0) 
                           FROM fee_payments fp2 
                           WHERE fp2.student_id = fp.student_id 
                           AND fp2.fee_structure_id = fp.fee_structure_id) as balance
        FROM fee_payments fp
        JOIN students s ON fp.student_id = s.id
        JOIN fee_structures fs ON fp.fee_structure_id = fs.id
        ORDER BY fp.date_paid DESC
        LIMIT 10
    ''').fetchall()
    
    # Get fee structures
    fee_structures = conn.execute('''
        SELECT * FROM fee_structures 
        ORDER BY year DESC, class, 
               CASE term 
                   WHEN 'Term 1' THEN 1 
                   WHEN 'Term 2' THEN 2 
                   WHEN 'Term 3' THEN 3 
               END
    ''').fetchall()
    
    # Get students for payment form
    students = conn.execute('SELECT id, name, admission_number, class FROM students ORDER BY name').fetchall()
    
    conn.close()
    
    return render_template('fees.html', 
                         recent_payments=recent_payments,
                         fee_structures=fee_structures,
                         students=students)

@app.route('/fees/add_payment', methods=['POST'])
@login_required
@role_required('admin')
def add_fee_payment():
    student_id = request.form['student_id']
    fee_structure_id = request.form['fee_structure_id']
    amount_paid = float(request.form['amount_paid'])
    payment_method = request.form.get('payment_method', 'Cash')
    remarks = request.form.get('remarks', '')
    
    conn = get_db_connection()
    
    try:
        # Generate receipt number
        receipt_number = generate_receipt_number()
        
        # Insert payment
        conn.execute('''
            INSERT INTO fee_payments (student_id, fee_structure_id, amount_paid, date_paid, 
                                     receipt_number, payment_method, remarks)
            VALUES (?, ?, ?, date('now'), ?, ?, ?)
        ''', (student_id, fee_structure_id, amount_paid, receipt_number, payment_method, remarks))
        
        conn.commit()
        flash(f'Payment recorded successfully! Receipt: {receipt_number}', 'success')
    except Exception as e:
        flash(f'Error recording payment: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('fees'))

@app.route('/fees/add_structure', methods=['POST'])
@login_required
@role_required('admin')
def add_fee_structure():
    class_name = request.form['class']
    term = request.form['term']
    year = int(request.form['year'])
    amount = float(request.form['amount'])
    description = request.form.get('description', '')
    due_date = request.form.get('due_date', '')
    
    conn = get_db_connection()
    
    try:
        conn.execute('''
            INSERT INTO fee_structures (class, term, year, amount, description, due_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (class_name, term, year, amount, description, due_date))
        
        conn.commit()
        flash('Fee structure added successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Fee structure for this class, term, and year already exists!', 'error')
    except Exception as e:
        flash(f'Error adding fee structure: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('fees'))

@app.route('/fees/structure/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_fee_structure(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        class_name = request.form['class']
        term = request.form['term']
        year = int(request.form['year'])
        amount = float(request.form['amount'])
        description = request.form.get('description', '')
        due_date = request.form.get('due_date', '')
        
        try:
            conn.execute('''
                UPDATE fee_structures 
                SET class = ?, term = ?, year = ?, amount = ?, description = ?, due_date = ?
                WHERE id = ?
            ''', (class_name, term, year, amount, description, due_date, id))
            
            conn.commit()
            flash('Fee structure updated successfully!', 'success')
            return redirect(url_for('fees'))
        except Exception as e:
            flash(f'Error updating fee structure: {str(e)}', 'error')
        finally:
            conn.close()
    
    fee_structure = conn.execute('SELECT * FROM fee_structures WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if not fee_structure:
        flash('Fee structure not found!', 'error')
        return redirect(url_for('fees'))
    
    return render_template('edit_fee_structure.html', fee_structure=fee_structure)

@app.route('/fees/structure/delete/<int:id>')
@login_required
@role_required('admin')
def delete_fee_structure(id):
    conn = get_db_connection()
    
    try:
        # Check if there are any payments for this structure
        payments = conn.execute('SELECT COUNT(*) FROM fee_payments WHERE fee_structure_id = ?', (id,)).fetchone()[0]
        
        if payments > 0:
            flash('Cannot delete fee structure because there are payments associated with it!', 'error')
        else:
            conn.execute('DELETE FROM fee_structures WHERE id = ?', (id,))
            conn.commit()
            flash('Fee structure deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting fee structure: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('fees'))

@app.route('/fees/receipt/<int:id>')
@login_required
@role_required('admin')
def view_receipt(id):
    conn = get_db_connection()
    
    payment = conn.execute('''
        SELECT fp.*, s.name as student_name, s.admission_number, s.class,
               fs.term, fs.year, fs.amount as total_amount
        FROM fee_payments fp
        JOIN students s ON fp.student_id = s.id
        JOIN fee_structures fs ON fp.fee_structure_id = fs.id
        WHERE fp.id = ?
    ''', (id,)).fetchone()
    
    if not payment:
        flash('Payment not found!', 'error')
        return redirect(url_for('fees'))
    
    # Calculate previous balance
    previous_payments = conn.execute('''
        SELECT COALESCE(SUM(amount_paid), 0) as total_paid
        FROM fee_payments 
        WHERE student_id = ? AND fee_structure_id = ? AND id != ?
    ''', (payment['student_id'], payment['fee_structure_id'], id)).fetchone()
    
    previous_total = previous_payments['total_paid'] if previous_payments else 0
    previous_balance = payment['total_amount'] - previous_total
    
    # Calculate new balance
    new_balance = previous_balance - payment['amount_paid']
    
    fee_structure = {
        'amount': payment['total_amount']
    }
    
    student = {
        'name': payment['student_name'],
        'admission_number': payment['admission_number'],
        'class': payment['class']
    }
    
    conn.close()
    
    return render_template('receipt.html',
                         payment=payment,
                         student=student,
                         fee_structure=fee_structure,
                         previous_balance=previous_balance,
                         new_balance=new_balance)

# -------- Attendance Routes --------

@app.route('/attendance')
@login_required
@role_required('admin', 'teacher')
def attendance():
    class_filter = request.args.get('class_filter', '')
    selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    
    conn = get_db_connection()
    
    # Get students with selected date's attendance
    query = '''
        SELECT s.id, s.admission_number, s.name, s.class, a.status
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id AND a.date = ?
    '''
    params = [selected_date]
    
    if class_filter:
        query += ' WHERE s.class = ?'
        params.append(class_filter)
    
    query += ' ORDER BY s.class, s.name'
    students = conn.execute(query, params).fetchall()
    
    # Get attendance statistics for last 7 days
    week_ago = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')

    # Convert students to dictionaries to allow modification
    students = [dict(student) for student in students]

    for student in students:
        # Get attendance summary for last 7 days
        summary = conn.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
                SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late,
                SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused
            FROM attendance
            WHERE student_id = ? AND date >= ?
        ''', (student['id'], week_ago)).fetchone()

        student['attendance_summary'] = dict(summary) if summary else None
    
    # Get today's statistics
    today_stats = conn.execute('''
        SELECT 
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late,
            SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused
        FROM attendance 
        WHERE date = ?
    ''', (selected_date,)).fetchone()
    
    # Get unique classes for filter
    class_list = [row[0] for row in conn.execute('''
        SELECT DISTINCT class FROM students 
        WHERE class IS NOT NULL AND class != '' 
        ORDER BY class
    ''').fetchall()]
    
    conn.close()
    
    return render_template('attendance.html', 
                         students=students, 
                         class_list=class_list,
                         current_class=class_filter,
                         selected_date=selected_date,
                         today_stats=today_stats)

@app.route('/attendance/save', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def save_attendance():
    date = request.form['date']
    class_filter = request.form.get('class_filter', '')
    
    conn = get_db_connection()
    
    try:
        # Get students for the class
        query = 'SELECT id FROM students'
        params = []
        if class_filter:
            query += ' WHERE class = ?'
            params.append(class_filter)
        
        students = conn.execute(query, params).fetchall()
        
        for student in students:
            student_id = student['id']
            status_key = f'status_{student_id}'
            remarks_key = f'remarks_{student_id}'
            
            if status_key in request.form:
                status = request.form[status_key]
                remarks = request.form.get(remarks_key, '')
                
                # Check if attendance already exists for this date
                existing = conn.execute('''
                    SELECT id FROM attendance WHERE student_id = ? AND date = ?
                ''', (student_id, date)).fetchone()
                
                if existing:
                    # Update existing attendance
                    conn.execute('''
                        UPDATE attendance 
                        SET status = ?, remarks = ?
                        WHERE id = ?
                    ''', (status, remarks, existing['id']))
                else:
                    # Insert new attendance
                    conn.execute('''
                        INSERT INTO attendance (student_id, date, status, remarks)
                        VALUES (?, ?, ?, ?)
                    ''', (student_id, date, status, remarks))
        
        conn.commit()
        flash('Attendance saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving attendance: {str(e)}', 'error')
    finally:
        conn.close()
    
    redirect_url = url_for('attendance', date=date)
    if class_filter:
        redirect_url += f'&class_filter={class_filter}'
    
    return redirect(redirect_url)

# -------- Grade Routes --------

@app.route('/grades')
@login_required
@role_required('admin', 'teacher')
def grades():
    conn = get_db_connection()
    recent_grades = conn.execute('''
        SELECT g.*, s.name as student_name, s.admission_number, s.class
        FROM grades g
        JOIN students s ON g.student_id = s.id
        ORDER BY g.created_at DESC
        LIMIT 20
    ''').fetchall()
    conn.close()
    return render_template('grades.html', recent_grades=recent_grades)

@app.route('/grades/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def add_grade():
    conn = get_db_connection()
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        subject = request.form['subject']
        term = request.form['term']
        year = int(request.form['year'])
        score = float(request.form['score'])
        remarks = request.form.get('remarks', '')
        
        # Calculate grade
        grade = calculate_grade(score)
        
        try:
            conn.execute('''
                INSERT INTO grades (student_id, subject, term, year, score, grade, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, subject, term, year, score, grade, remarks))
            
            conn.commit()
            flash('Grade added successfully!', 'success')
            return redirect(url_for('grades'))
        except Exception as e:
            flash(f'Error adding grade: {str(e)}', 'error')
        finally:
            conn.close()
    
    students = conn.execute('SELECT id, name, admission_number, class FROM students ORDER BY name').fetchall()
    grading = conn.execute('SELECT * FROM grading_system WHERE is_default = 1').fetchone()
    
    conn.close()
    
    return render_template('add_grade.html', students=students, grading=grading)

@app.route('/grades/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_grade(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        subject = request.form['subject']
        term = request.form['term']
        year = int(request.form['year'])
        score = float(request.form['score'])
        remarks = request.form.get('remarks', '')
        
        # Calculate grade
        grade = calculate_grade(score)
        
        try:
            conn.execute('''
                UPDATE grades 
                SET subject = ?, term = ?, year = ?, score = ?, grade = ?, remarks = ?
                WHERE id = ?
            ''', (subject, term, year, score, grade, remarks, id))
            
            conn.commit()
            flash('Grade updated successfully!', 'success')
            return redirect(url_for('grades'))
        except Exception as e:
            flash(f'Error updating grade: {str(e)}', 'error')
        finally:
            conn.close()
    
    grade = conn.execute('''
        SELECT g.*, s.name as student_name, s.admission_number, s.class
        FROM grades g
        JOIN students s ON g.student_id = s.id
        WHERE g.id = ?
    ''', (id,)).fetchone()
    
    conn.close()
    
    if not grade:
        flash('Grade not found!', 'error')
        return redirect(url_for('grades'))
    
    return render_template('edit_grade.html', grade=grade)

@app.route('/grades/delete/<int:id>')
@login_required
@role_required('admin', 'teacher')
def delete_grade(id):
    conn = get_db_connection()
    
    try:
        conn.execute('DELETE FROM grades WHERE id = ?', (id,))
        conn.commit()
        flash('Grade deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting grade: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('grades'))

# -------- Timetable Routes --------

@app.route('/timetable')
@login_required
def timetable():
    # All roles can access timetable
    selected_class = request.args.get('class_filter', '')
    selected_teacher = request.args.get('teacher', '')
    selected_day = request.args.get('day', '')
    
    conn = get_db_connection()
    
    # Get all classes for dropdown
    all_classes = [row[0] for row in conn.execute('''
        SELECT DISTINCT class FROM students 
        WHERE class IS NOT NULL AND class != '' 
        UNION
        SELECT DISTINCT class FROM timetable
        ORDER BY class
    ''').fetchall()]
    
    # Get all teachers
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    
    # Get all subjects for color legend
    subjects = [row[0] for row in conn.execute('''
        SELECT DISTINCT subject FROM timetable ORDER BY subject
    ''').fetchall()]
    
    # Get timetable entries with filters
    query = '''
        SELECT t.*, te.name as teacher_name
        FROM timetable t
        LEFT JOIN teachers te ON t.teacher_id = te.id
        WHERE 1=1
    '''
    params = []
    
    if selected_class:
        query += ' AND t.class = ?'
        params.append(selected_class)
    
    if selected_teacher:
        query += ' AND te.name = ?'
        params.append(selected_teacher)
    
    if selected_day:
        query += ' AND t.day = ?'
        params.append(selected_day)
    
    query += ' ORDER BY t.day, t.period'
    timetable_entries = conn.execute(query, params).fetchall()
    
    # Get all entries for management tab
    all_entries = conn.execute('''
        SELECT t.*, te.name as teacher_name
        FROM timetable t
        LEFT JOIN teachers te ON t.teacher_id = te.id
        ORDER BY t.class, t.day, t.period
    ''').fetchall()
    
    conn.close()
    
    return render_template('timetable.html',
                         all_classes=all_classes,
                         teachers=teachers,
                         subjects=subjects,
                         selected_class=selected_class,
                         selected_teacher=selected_teacher,
                         selected_day=selected_day,
                         timetable_entries=timetable_entries,
                         all_entries=all_entries)

@app.route('/timetable/add', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def add_timetable_entry():
    class_name = request.form['class']
    day = request.form['day']
    period = int(request.form['period'])
    subject = request.form['subject']
    teacher_id = request.form.get('teacher_id', '')
    room = request.form.get('room', '')
    description = request.form.get('description', '')
    
    if teacher_id == '':
        teacher_id = None
    
    conn = get_db_connection()
    
    try:
        conn.execute('''
            INSERT INTO timetable (class, day, period, subject, teacher_id, room, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (class_name, day, period, subject, teacher_id, room, description))
        
        conn.commit()
        flash('Timetable entry added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding timetable entry: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('timetable'))

@app.route('/timetable/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'teacher')
def edit_timetable_entry(id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        class_name = request.form['class']
        day = request.form['day']
        period = int(request.form['period'])
        subject = request.form['subject']
        teacher_id = request.form.get('teacher_id', '')
        room = request.form.get('room', '')
        description = request.form.get('description', '')
        
        if teacher_id == '':
            teacher_id = None
        
        try:
            conn.execute('''
                UPDATE timetable 
                SET class = ?, day = ?, period = ?, subject = ?, teacher_id = ?, room = ?, description = ?
                WHERE id = ?
            ''', (class_name, day, period, subject, teacher_id, room, description, id))
            
            conn.commit()
            flash('Timetable entry updated successfully!', 'success')
            return redirect(url_for('timetable'))
        except Exception as e:
            flash(f'Error updating timetable entry: {str(e)}', 'error')
        finally:
            conn.close()
    
    entry = conn.execute('SELECT * FROM timetable WHERE id = ?', (id,)).fetchone()
    teachers = conn.execute('SELECT * FROM teachers ORDER BY name').fetchall()
    
    conn.close()
    
    if not entry:
        flash('Timetable entry not found!', 'error')
        return redirect(url_for('timetable'))
    
    return render_template('edit_timetable_entry.html', entry=entry, teachers=teachers)

@app.route('/timetable/delete/<int:id>')
@login_required
@role_required('admin', 'teacher')
def delete_timetable_entry(id):
    conn = get_db_connection()
    
    try:
        conn.execute('DELETE FROM timetable WHERE id = ?', (id,))
        conn.commit()
        flash('Timetable entry deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting timetable entry: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('timetable'))

# -------- Settings Routes --------

@app.route('/settings')
@login_required
@role_required('admin')
def settings():
    conn = get_db_connection()
    
    # Get school settings
    settings = conn.execute('SELECT * FROM school_settings WHERE id = 1').fetchone()
    
    # Get grading systems
    grading_systems = conn.execute('SELECT * FROM grading_system ORDER BY is_default DESC, name').fetchall()
    
    # Get default grading system
    default_grading = conn.execute('SELECT * FROM grading_system WHERE is_default = 1').fetchone()
    if not default_grading and grading_systems:
        default_grading = grading_systems[0]
    
    conn.close()
    
    return render_template('settings.html',
                         settings=dict(settings) if settings else {},
                         grading_systems=grading_systems,
                         default_grading=dict(default_grading) if default_grading else {})

@app.route('/settings/update', methods=['POST'])
@login_required
@role_required('admin')
def update_school_settings():
    school_name = request.form['school_name']
    school_address = request.form.get('school_address', '')
    school_phone = request.form.get('school_phone', '')
    school_email = request.form.get('school_email', '')
    
    conn = get_db_connection()
    
    try:
        conn.execute('''
            UPDATE school_settings 
            SET school_name = ?, school_address = ?, school_phone = ?, school_email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (school_name, school_address, school_phone, school_email))
        
        # Handle logo upload
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename != '':
                filename = secure_filename(logo.filename)
                logo_path = os.path.join(app.config['LOGO_FOLDER'], filename)
                logo.save(logo_path)
                
                # Update logo path in database
                conn.execute('UPDATE school_settings SET logo_path = ? WHERE id = 1', (logo_path,))
        
        conn.commit()
        flash('School settings updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating settings: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('settings'))

@app.route('/settings/grading/update', methods=['POST'])
@login_required
@role_required('admin')
def update_grading_system():
    min_a = int(request.form['min_a'])
    max_a = int(request.form['max_a'])
    min_b = int(request.form['min_b'])
    max_b = int(request.form['max_b'])
    min_c = int(request.form['min_c'])
    max_c = int(request.form['max_c'])
    min_d = int(request.form['min_d'])
    max_d = int(request.form['max_d'])
    min_f = int(request.form['min_f'])
    max_f = int(request.form['max_f'])
    
    conn = get_db_connection()
    
    try:
        # Update the default grading system
        conn.execute('''
            UPDATE grading_system 
            SET min_a = ?, max_a = ?, min_b = ?, max_b = ?, 
                min_c = ?, max_c = ?, min_d = ?, max_d = ?, 
                min_f = ?, max_f = ?
            WHERE is_default = 1
        ''', (min_a, max_a, min_b, max_b, min_c, max_c, min_d, max_d, min_f, max_f))
        
        conn.commit()
        flash('Grading system updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating grading system: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('settings'))

@app.route('/settings/backup')
@login_required
@role_required('admin')
def backup_database():
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'school_backup_{timestamp}.db')
    
    try:
        # Copy the database file
        shutil.copy2('school.db', backup_file)
        flash(f'Database backup created successfully: {backup_file}', 'success')
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

@app.route('/settings/restore', methods=['POST'])
@login_required
@role_required('admin')
def restore_database():
    if 'backup_file' not in request.files:
        flash('No backup file selected!', 'error')
        return redirect(url_for('settings'))
    
    backup_file = request.files['backup_file']
    
    if backup_file.filename == '':
        flash('No backup file selected!', 'error')
        return redirect(url_for('settings'))
    
    try:
        # Save the backup file
        backup_path = 'school_backup_restore.db'
        backup_file.save(backup_path)
        
        # Verify it's a valid SQLite database
        test_conn = sqlite3.connect(backup_path)
        test_conn.execute('SELECT 1')
        test_conn.close()
        
        # Replace the current database
        os.replace(backup_path, 'school.db')
        
        # Reinitialize the database to ensure schema is correct
        init_db()
        
        flash('Database restored successfully!', 'success')
    except Exception as e:
        flash(f'Error restoring database: {str(e)}', 'error')
    
    return redirect(url_for('settings'))

# -------- Themes Route --------

@app.route('/themes')
@login_required
@role_required('admin')
def themes():
    return render_template('themes.html')

# -------- Export Routes --------

@app.route('/export/students')
@login_required
@role_required('admin')
def export_students():
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students ORDER BY class, name').fetchall()
    conn.close()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['ID', 'Admission Number', 'Name', 'Age', 'Class', 'Guardian Name', 
                     'Guardian Contacts', 'Guardian Email', 'Address', 'Medical Conditions',
                     'Allergies', 'Emergency Contact', 'Emergency Phone'])
    
    # Write data
    for student in students:
        writer.writerow([
            student['id'],
            student['admission_number'],
            student['name'],
            student['age'] or '',
            student['class'] or '',
            student['guardian_name'] or '',
            student['guardian_contacts'] or '',
            student['guardian_email'] or '',
            student['address'] or '',
            student['medical_conditions'] or '',
            student['allergies'] or '',
            student['emergency_contact_name'] or '',
            student['emergency_contact_phone'] or ''
        ])
    
    output.seek(0)
    
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'students_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route('/export/grades')
@login_required
@role_required('admin', 'teacher')
def export_grades():
    conn = get_db_connection()
    grades = conn.execute('''
        SELECT g.*, s.name as student_name, s.admission_number, s.class
        FROM grades g
        JOIN students s ON g.student_id = s.id
        ORDER BY g.year DESC, g.term, s.class, s.name
    ''').fetchall()
    conn.close()
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Student Name', 'Admission Number', 'Class', 'Subject', 'Term', 
                     'Year', 'Score', 'Grade', 'Remarks', 'Date Recorded'])
    
    # Write data
    for grade in grades:
        writer.writerow([
            grade['student_name'],
            grade['admission_number'],
            grade['class'],
            grade['subject'],
            grade['term'],
            grade['year'],
            grade['score'],
            grade['grade'],
            grade['remarks'] or '',
            grade['created_at'][:10] if grade['created_at'] else ''
        ])
    
    output.seek(0)
    
    return send_file(
        BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'grades_export_{datetime.now().strftime("%Y%m%d")}.csv'
    )

# -------- Run Application --------

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOGO_FOLDER'], exist_ok=True)
    os.makedirs('backups', exist_ok=True)
    
    # Initialize database
    init_db()
    
    print("=" * 60)
    print("School Management System with Authentication")
    print("=" * 60)
    print("\nFeatures:")
    print("1. Complete Authentication System with Roles (Admin, Teacher, Student)")
    print("2. User Management - Create/Edit/Deactivate users")
    print("3. Student Medical Information with Emergency Contacts")
    print("4. Role-Based Access Control")
    print("5. Student Dashboard with Personal Information")
    print("6. Teacher Dashboard with Assigned Classes")
    print("7. Fee Management with Receipt Generation")
    print("8. Attendance Tracking")
    print("9. Grade Management")
    print("10. Timetable Management")
    print("11. School Settings and Themes")
    print("\nDefault Login Credentials:")
    print("- Username: admin")
    print("- Password: school123")
    print("- Role: admin")
    print("\nAccess the system at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)