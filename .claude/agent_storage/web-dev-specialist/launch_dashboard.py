#!/usr/bin/env python3
"""
R2D2 Multi-Agent Dashboard Launcher
Orchestrates the complete dashboard system startup
"""

import os
import sys
import time
import signal
import logging
import subprocess
import threading
import webbrowser
from pathlib import Path
import argparse
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DashboardLauncher:
    """Launches and manages the R2D2 dashboard system"""

    def __init__(self, config_file=None):
        self.base_path = Path(__file__).parent
        self.config = self.load_config(config_file)
        self.processes = {}
        self.running = False

    def load_config(self, config_file=None):
        """Load dashboard configuration"""
        default_config = {
            "websocket_server": {
                "host": "0.0.0.0",
                "port": 8765,
                "auto_start": True
            },
            "web_server": {
                "host": "0.0.0.0",
                "port": 8080,
                "auto_start": True,
                "open_browser": True
            },
            "system_monitor": {
                "auto_start": True,
                "monitoring_interval": 5
            },
            "dashboard": {
                "title": "R2D2 Multi-Agent Dashboard",
                "theme": "dark",
                "auto_refresh": True,
                "refresh_interval": 5000
            },
            "security": {
                "allowed_hosts": ["localhost", "127.0.0.1", "0.0.0.0"],
                "enable_authentication": False
            }
        }

        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    for key, value in user_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
            except Exception as e:
                logger.error(f"Error loading config file: {e}")

        return default_config

    def create_web_server(self):
        """Create a simple HTTP server for the dashboard"""
        web_server_script = self.base_path / "web_server.py"

        web_server_content = f'''#!/usr/bin/env python3
"""
Simple HTTP server for R2D2 Dashboard
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

class DashboardHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        os.chdir(Path(__file__).parent)
        super().__init__(*args, **kwargs)

    def end_headers(self):
        # Add CORS headers for WebSocket connection
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def guess_type(self, path):
        # Ensure correct MIME types
        mimetype = super().guess_type(path)
        if path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.css'):
            return 'text/css'
        elif path.endswith('.html'):
            return 'text/html'
        return mimetype

def main():
    host = "{self.config['web_server']['host']}"
    port = {self.config['web_server']['port']}

    with socketserver.TCPServer((host, port), DashboardHTTPRequestHandler) as httpd:
        print(f"Dashboard HTTP server started at http://{{host}}:{{port}}")
        print(f"Serving files from: {{Path(__file__).parent}}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\\nHTTP server stopped")

if __name__ == "__main__":
    main()
'''

        with open(web_server_script, 'w') as f:
            f.write(web_server_content)

        os.chmod(web_server_script, 0o755)
        return web_server_script

    def start_websocket_server(self):
        """Start the WebSocket server"""
        try:
            websocket_script = self.base_path / "websocket_server.py"

            if not websocket_script.exists():
                logger.error("WebSocket server script not found")
                return False

            logger.info("Starting WebSocket server...")
            process = subprocess.Popen(
                [sys.executable, str(websocket_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes['websocket'] = process
            logger.info(f"WebSocket server started (PID: {{process.pid}})")
            return True

        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {{e}}")
            return False

    def start_web_server(self):
        """Start the HTTP server"""
        try:
            web_server_script = self.create_web_server()

            logger.info("Starting HTTP server...")
            process = subprocess.Popen(
                [sys.executable, str(web_server_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes['web'] = process
            logger.info(f"HTTP server started (PID: {{process.pid}})")
            return True

        except Exception as e:
            logger.error(f"Failed to start HTTP server: {{e}}")
            return False

    def start_system_monitor(self):
        """Start the system monitor"""
        try:
            monitor_script = self.base_path / "r2d2_system_monitor.py"

            if not monitor_script.exists():
                logger.warning("System monitor script not found, skipping")
                return True

            logger.info("Starting system monitor...")
            process = subprocess.Popen(
                [sys.executable, str(monitor_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            self.processes['monitor'] = process
            logger.info(f"System monitor started (PID: {{process.pid}})")
            return True

        except Exception as e:
            logger.error(f"Failed to start system monitor: {{e}}")
            return False

    def open_dashboard_browser(self):
        """Open the dashboard in the default browser"""
        if self.config['web_server']['open_browser']:
            try:
                host = self.config['web_server']['host']
                port = self.config['web_server']['port']

                # Use localhost for browser if host is 0.0.0.0
                if host == '0.0.0.0':
                    host = 'localhost'

                url = f"http://{{host}}:{{port}}/r2d2_agent_dashboard.html"

                # Wait a moment for servers to start
                time.sleep(2)

                logger.info(f"Opening dashboard in browser: {{url}}")
                webbrowser.open(url)

            except Exception as e:
                logger.error(f"Failed to open browser: {{e}}")

    def check_dependencies(self):
        """Check for required dependencies"""
        required_files = [
            'r2d2_agent_dashboard.html',
            'dashboard_styles.css',
            'dashboard_script.js',
            'websocket_server.py'
        ]

        missing_files = []
        for file in required_files:
            if not (self.base_path / file).exists():
                missing_files.append(file)

        if missing_files:
            logger.error(f"Missing required files: {{', '.join(missing_files)}}")
            return False

        # Check Python dependencies
        try:
            import websockets
            import psutil
        except ImportError as e:
            logger.error(f"Missing Python dependency: {{e}}")
            logger.info("Install with: pip install websockets psutil")
            return False

        return True

    def create_desktop_shortcut(self):
        """Create a desktop shortcut for easy access"""
        try:
            desktop_path = Path.home() / "Desktop"
            if not desktop_path.exists():
                desktop_path = Path.home()

            shortcut_content = f'''[Desktop Entry]
Name=R2D2 Dashboard
Comment=R2D2 Multi-Agent Monitoring Dashboard
Exec={sys.executable} {self.base_path / "launch_dashboard.py"}
Icon={self.base_path / "r2d2_icon.png"}
Terminal=true
Type=Application
Categories=Development;Monitoring;
'''

            shortcut_path = desktop_path / "R2D2_Dashboard.desktop"
            with open(shortcut_path, 'w') as f:
                f.write(shortcut_content)

            os.chmod(shortcut_path, 0o755)
            logger.info(f"Desktop shortcut created: {{shortcut_path}}")

        except Exception as e:
            logger.error(f"Failed to create desktop shortcut: {{e}}")

    def start_dashboard(self):
        """Start the complete dashboard system"""
        logger.info("R2D2 Multi-Agent Dashboard Launcher")
        logger.info("=" * 50)

        # Check dependencies
        if not self.check_dependencies():
            logger.error("Dependency check failed. Exiting.")
            return False

        # Create necessary directories
        (Path.home() / "r2ai" / "screenshots").mkdir(parents=True, exist_ok=True)
        (Path.home() / "r2ai" / "logs").mkdir(parents=True, exist_ok=True)

        self.running = True
        startup_success = True

        # Start WebSocket server
        if self.config['websocket_server']['auto_start']:
            if not self.start_websocket_server():
                startup_success = False

        # Start HTTP server
        if self.config['web_server']['auto_start']:
            if not self.start_web_server():
                startup_success = False

        # Start system monitor
        if self.config['system_monitor']['auto_start']:
            if not self.start_system_monitor():
                startup_success = False

        if not startup_success:
            logger.error("Some components failed to start")
            self.stop_dashboard()
            return False

        # Open browser
        threading.Timer(3.0, self.open_dashboard_browser).start()

        logger.info("Dashboard system started successfully!")
        logger.info(f"Dashboard URL: http://localhost:{{self.config['web_server']['port']}}/r2d2_agent_dashboard.html")
        logger.info(f"WebSocket URL: ws://localhost:{{self.config['websocket_server']['port']}}")
        logger.info("Press Ctrl+C to stop the dashboard")

        return True

    def stop_dashboard(self):
        """Stop all dashboard components"""
        logger.info("Stopping dashboard system...")

        self.running = False

        for name, process in self.processes.items():
            try:
                logger.info(f"Stopping {{name}} server...")
                process.terminate()

                # Wait for graceful shutdown
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {{name}} server...")
                    process.kill()

            except Exception as e:
                logger.error(f"Error stopping {{name}} server: {{e}}")

        logger.info("Dashboard system stopped")

    def monitor_processes(self):
        """Monitor running processes and restart if needed"""
        while self.running:
            try:
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"{{name}} server has stopped unexpectedly")

                        # Attempt restart
                        if name == 'websocket' and self.config['websocket_server']['auto_start']:
                            logger.info(f"Restarting {{name}} server...")
                            if self.start_websocket_server():
                                logger.info(f"{{name}} server restarted successfully")
                            else:
                                logger.error(f"Failed to restart {{name}} server")

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in process monitoring: {{e}}")
                time.sleep(10)

    def run(self):
        """Main run loop"""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            self.stop_dashboard()
            sys.exit(0)

        # Set up signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start dashboard
        if not self.start_dashboard():
            return 1

        # Start process monitoring
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_dashboard()

        return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='R2D2 Multi-Agent Dashboard Launcher')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--create-shortcut', action='store_true', help='Create desktop shortcut')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies only')

    args = parser.parse_args()

    launcher = DashboardLauncher(args.config)

    if args.create_shortcut:
        launcher.create_desktop_shortcut()
        return 0

    if args.check_deps:
        if launcher.check_dependencies():
            print("All dependencies satisfied")
            return 0
        else:
            print("Missing dependencies")
            return 1

    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())