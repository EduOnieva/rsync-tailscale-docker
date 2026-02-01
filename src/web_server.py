#!/usr/bin/env python3
import http.server
import json
import logging
import logging.handlers
import os
import signal
import socketserver
import sys
from datetime import datetime
from typing import Tuple, Optional

# Configuration
LOG_FILE: str = '/config/logs/sync.log'
SERVER_LOG_FILE: str = '/config/logs/web_server.log'
PORT: int = 80
MAX_LOG_SIZE: int = 1024 * 1024  # 1MB
MAX_LOG_BACKUPS: int = 10

# Ensure log directory exists before setting up logging
os.makedirs(os.path.dirname(SERVER_LOG_FILE), exist_ok=True)

# Setup logging with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# File handler with rotation
file_handler = logging.handlers.RotatingFileHandler(
    SERVER_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=MAX_LOG_BACKUPS
)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class EnhancedLogHandler(http.server.SimpleHTTPRequestHandler):
    
    def log_message(self, format: str, *args) -> None:
        '''Override to use our logger'''
        logger.info(f'{self.address_string()} - {format % args}')

    def safe_read_log(self, log_path: str, max_lines: int = 1000) -> str:
        '''Safely read log file with size limits'''
        try:
            if not os.path.exists(log_path):
                return 'Log file not found'
            
            file_size = os.path.getsize(log_path)
            if file_size > MAX_LOG_SIZE:
                # Read only the last part of large files
                with open(log_path, 'rb') as f:
                    f.seek(-MAX_LOG_SIZE, 2)
                    content = f.read().decode('utf-8', errors='ignore')
                    return f'[LOG TRUNCATED - showing last {MAX_LOG_SIZE} bytes]\n{content}'
            else:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if len(lines) > max_lines:
                        truncated_lines = ''.join(lines[-max_lines:])
                        return f'[LOG TRUNCATED - showing last {max_lines} lines]\n{truncated_lines}'
                    return ''.join(lines)
        except Exception as e:
            logger.error(f'Error reading log file {log_path}: {e}')
            return f'Error reading log file: {str(e)}'

    def generate_html_page(self, sync_log: str, load_avg: Tuple[float, float, float]) -> str:
        '''Generate the HTML page with enhanced features'''
        log_size = os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0
        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        css_styles = '''
        body { 
            font-family: 'Monaco', 'Menlo', monospace; margin: 0; 
            background: #0d1117; color: #c9d1d9; 
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: #161b22; padding: 20px; border-radius: 8px; 
            margin-bottom: 20px; border: 1px solid #30363d; 
        }
        h1 { color: #58a6ff; margin: 0; font-size: 2.2em; }
        .controls-status { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 15px; background: #161b22; border: 1px solid #30363d; 
            border-radius: 8px; margin-bottom: 20px; 
        }
        .system-status { color: #7d8590; font-size: 14px; }
        .controls { display: flex; gap: 10px; flex-wrap: wrap; }
        .btn { 
            background: #21262d; color: #f0f6fc; padding: 12px 24px; 
            border: 1px solid #30363d; border-radius: 6px; cursor: pointer; 
            font-family: inherit; font-size: 14px; transition: all 0.2s ease;
        }
        .btn:hover { background: #30363d; }
        .btn.primary { background: #238636; border-color: #2ea043; }
        .btn.primary:hover { background: #2ea043; }
        .btn.warning { background: #bb800a; border-color: #d29922; }
        .btn.warning:hover { background: #d29922; }
        .btn.danger { background: #da3633; border-color: #f85149; }
        .btn.danger:hover { background: #f85149; }
        .log-container { display: grid; grid-template-columns: 1fr; gap: 20px; }
        .log-section { background: #0d1117; border: 1px solid #30363d; border-radius: 8px; }
        .log-section.full-width { grid-column: 1; }
        .log-header { 
            background: #161b22; padding: 15px; border-bottom: 1px solid #30363d; 
            font-weight: bold; 
        }
        .log-content { 
            background: #010409; padding: 20px; max-height: 500px; overflow-y: auto; 
            white-space: pre-wrap; font-size: 13px; line-height: 1.4;
            scrollbar-width: thin; scrollbar-color: #30363d #0d1117;
        }
        .log-content::-webkit-scrollbar { width: 8px; }
        .log-content::-webkit-scrollbar-track { background: #0d1117; }
        .log-content::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
        .timestamp { color: #7d8590; }
        .info { color: #79c0ff; }
        .success { color: #3fb950; }
        .error { color: #f85149; }
        .warning { color: #d29922; }
        @media (max-width: 768px) {
            .log-container { grid-template-columns: 1fr; }
            .controls { flex-direction: column; }
            .btn { width: 100%; }
        }
        '''
        
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <title>📄 Rsync Backup Management</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 Rsync Backup Management</h1>
            <div class="timestamp">Last updated: {last_updated}</div>
        </div>
        
        <div class="controls-status">
            <div class="system-status">
                💾 Load: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f} | 
                📄 Log: {log_size} bytes
            </div>
            <div class="controls">
                <button class="btn primary" onclick="location.reload()">🔄 Refresh</button>
                <button class="btn primary" onclick="runSync()">▶️ Run Sync Now</button>
                <button class="btn warning" onclick="clearLogs()">🗑️ Clear Logs</button>
            </div>
        </div>

        <div class="log-container">
            <div class="log-section full-width">
                <div class="log-header">📋 Sync Logs</div>
                <div class="log-content" id="syncLogs">
                    {sync_log if sync_log.strip() else 'No sync logs yet...'}
                </div>
            </div>
        </div>
    </div>

    <script>
        function apiRequest(endpoint, method = 'GET', data = null) {{
            const options = {{
                method: method,
                headers: {{'Content-Type': 'application/json'}}
            }};
            if (data) options.body = JSON.stringify(data);
            
            return fetch(endpoint, options)
                .then(response => {{
                    if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
                    return response;
                }});
        }}

        function showNotification(message, type = 'info') {{
            const colors = {{
                'success': '#3fb950',
                'error': '#f85149', 
                'warning': '#d29922',
                'info': '#79c0ff'
            }};
            
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed; top: 20px; right: 20px; z-index: 1000;
                background: ${{colors[type] || colors.info}}; color: white; padding: 15px 20px;
                border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                max-width: 300px; word-wrap: break-word;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 4000);
        }}

        function clearLogs() {{
            if (confirm('Are you sure you want to clear all logs?')) {{
                apiRequest('/clear', 'POST')
                .then(() => {{
                    showNotification('Logs cleared successfully!', 'success');
                    setTimeout(() => location.reload(), 1000);
                }})
                .catch(err => showNotification(`Error clearing logs: ${{err.message}}`, 'error'));
            }}
        }}

        function runSync() {{
            if (confirm('Run sync script now? This may take several minutes.')) {{
                showNotification('Sync started! Check logs for progress...', 'info');
                apiRequest('/run', 'POST')
                .then(() => {{
                    setTimeout(() => location.reload(), 2000);
                }})
                .catch(err => showNotification(`Error starting sync: ${{err.message}}`, 'error'));
            }}
        }}
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            if (e.ctrlKey || e.metaKey) {{
                switch(e.key) {{
                    case 'r': e.preventDefault(); location.reload(); break;
                    case 'Enter': e.preventDefault(); runSync(); break;
                }}
            }}
        }});
    </script>
</body>
</html>'''

    def do_GET(self):
        try:
            if self.path == "/" or self.path == "/logs":
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                
                # Read log files
                sync_log = self.safe_read_log(LOG_FILE)
                
                # Get system info
                try:
                    load_avg = os.getloadavg()
                except:
                    load_avg = (0, 0, 0)
                
                html = self.generate_html_page(sync_log, load_avg)
                self.wfile.write(html.encode('utf-8'))
                
            elif self.path == "/api/status":
                # JSON API endpoint for status
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                status = {
                    "timestamp": datetime.now().isoformat(),
                    "log_exists": os.path.exists(LOG_FILE),
                    "log_size": os.path.getsize(LOG_FILE) if os.path.exists(LOG_FILE) else 0,
                    "server_uptime": "online"
                }
                self.wfile.write(json.dumps(status).encode())
                
            elif self.path == "/favicon.ico":
                # Simple SVG favicon with document icon
                self.send_response(200)
                self.send_header('Content-type', 'image/svg+xml')
                self.send_header('Cache-Control', 'max-age=86400')  # Cache for 24 hours
                self.end_headers()
                
                svg_favicon = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
                    <rect width="32" height="32" fill="#161b22"/>
                    <rect x="8" y="6" width="16" height="20" rx="1" fill="#58a6ff" stroke="#30363d"/>
                    <line x1="10" y1="10" x2="22" y2="10" stroke="#161b22" stroke-width="1"/>
                    <line x1="10" y1="13" x2="22" y2="13" stroke="#161b22" stroke-width="1"/>
                    <line x1="10" y1="16" x2="18" y2="16" stroke="#161b22" stroke-width="1"/>
                </svg>'''
                self.wfile.write(svg_favicon.encode())
            else:
                self.send_error(404, "Not found")
        except Exception as e:
            logger.error(f"Error in GET request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")

    def do_POST(self) -> None:
        try:
            if self.path == '/clear':
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, 'w') as f:
                        f.write(f'[{timestamp}] [INFO] Logs cleared via web interface\n')
                
                if os.path.exists(SERVER_LOG_FILE):
                    with open(SERVER_LOG_FILE, 'w') as f:
                        f.write(f'[{timestamp}] [INFO] Server logs cleared via web interface\n')
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
                logger.info('Logs cleared via web interface')
                
            elif self.path == "/run":
                try:
                    # Run sync script in background like the working web_server.py
                    os.system('/bin/bash /src/sync_script.sh >> /config/logs/sync.log 2>&1 &')
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "started"}).encode())
                    logger.info("Sync script started via web interface")
                    
                except Exception as e:
                    logger.error(f"Failed to start sync script: {e}")
                    self.send_error(500, f"Failed to start sync: {str(e)}")
                    
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            logger.error(f"Error in POST request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")

def signal_handler(sig: int, frame) -> None:
    logger.info('Received shutdown signal')
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Ensure log directory exists
        os.makedirs(os.path.dirname(SERVER_LOG_FILE), exist_ok=True)
        
        # Try to bind to port 80, fall back to 8080 if permission denied
        try:
            httpd = socketserver.TCPServer(('', PORT), EnhancedLogHandler)
        except PermissionError:
            logger.warning(f'Permission denied for port {PORT}, trying port 8080')
            PORT = 8080
            httpd = socketserver.TCPServer(('', PORT), EnhancedLogHandler)
        
        with httpd:
            logger.info(f'Enhanced web server running on port {PORT}')
            httpd.serve_forever()
            
    except Exception as e:
        logger.error(f'Failed to start web server: {e}')
        sys.exit(1)