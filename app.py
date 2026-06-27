#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import re
import urllib.parse
import mimetypes
import subprocess
import webbrowser
import threading

PORT = 5050
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_current_theme():
    # Read the active theme from the wallbash.conf file
    path = os.path.expanduser('~/.config/hypr/themes/wallbash.conf')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find $HYDE_THEME=Theme Name
                match = re.search(r'^\s*\$HYDE_THEME\s*=\s*(.+)$', content, re.MULTILINE)
                if match:
                    return match.group(1).strip()
                # Fallback to comment representation
                match = re.search(r'#\s*HyDE\s*Theme:\s*(.+)$', content, re.MULTILINE)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"Error parsing theme: {e}")
    
    # Try reading from config.toml as a fallback
    toml_path = os.path.expanduser('~/.config/hyde/config.toml')
    if os.path.exists(toml_path):
        try:
            with open(toml_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'theme\s*=\s*["\'](.+)["\']', content)
                if match:
                    return match.group(1).strip()
        except Exception as e:
            print(f"Error parsing config.toml: {e}")
            
    return "Default"

def get_wallpapers_dir(theme_name):
    return os.path.expanduser(f'~/.config/hyde/themes/{theme_name}/wallpapers')

class WallpaperManagerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default request logging to keep console clean
        pass

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # API: Status and Wallpaper list
        if path == '/api/status':
            theme = get_current_theme()
            wallpapers_dir = get_wallpapers_dir(theme)
            wallpapers = []
            if os.path.exists(wallpapers_dir):
                try:
                    wallpapers = [f for f in os.listdir(wallpapers_dir) 
                                  if os.path.isfile(os.path.join(wallpapers_dir, f)) and 
                                  f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))]
                    # Sort them
                    wallpapers.sort()
                except Exception as e:
                    print(f"Error listing wallpapers: {e}")
            
            # Find which wallpaper is currently set (via the wall.set symlink in the theme folder)
            active_wallpaper = None
            theme_dir = os.path.expanduser(f'~/.config/hyde/themes/{theme}')
            wall_set_path = os.path.join(theme_dir, 'wall.set')
            if os.path.exists(wall_set_path) and os.path.islink(wall_set_path):
                try:
                    real_path = os.readlink(wall_set_path)
                    active_wallpaper = os.path.basename(real_path)
                except Exception as e:
                    print(f"Error reading wall.set symlink: {e}")

            response_data = {
                "theme": theme,
                "wallpapers_dir": wallpapers_dir,
                "wallpapers": wallpapers,
                "active_wallpaper": active_wallpaper
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        # API: Serve a specific wallpaper image
        elif path.startswith('/api/wallpaper/'):
            theme = get_current_theme()
            wallpapers_dir = get_wallpapers_dir(theme)
            filename = urllib.parse.unquote(path[len('/api/wallpaper/'):])
            filepath = os.path.join(wallpapers_dir, filename)

            if os.path.exists(filepath) and os.path.commonpath([wallpapers_dir, filepath]) == wallpapers_dir:
                mime_type, _ = mimetypes.guess_type(filepath)
                self.send_response(200)
                self.send_header('Content-Type', mime_type or 'image/png')
                self.send_header('Cache-Control', 'max-age=3600')
                self.end_headers()
                with open(filepath, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Wallpaper file not found")
            return

        # Serve Frontend Static Files
        if path == '/' or path == '/index.html':
            filepath = os.path.join(WORKSPACE_DIR, 'index.html')
            mime_type = 'text/html'
        elif path == '/style.css':
            filepath = os.path.join(WORKSPACE_DIR, 'style.css')
            mime_type = 'text/css'
        elif path == '/script.js':
            filepath = os.path.join(WORKSPACE_DIR, 'script.js')
            mime_type = 'application/javascript'
        else:
            self.send_error(404, "File not found")
            return

        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.end_headers()
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Static file not found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        # Handle preflight requests or simple options
        if self.path == '/api/upload':
            theme = get_current_theme()
            wallpapers_dir = get_wallpapers_dir(theme)
            os.makedirs(wallpapers_dir, exist_ok=True)

            content_length = int(self.headers.get('Content-Length', 0))
            filename = urllib.parse.unquote(self.headers.get('X-File-Name', 'wallpaper.png'))
            
            # Sanitize filename
            filename = os.path.basename(filename)
            target_path = os.path.join(wallpapers_dir, filename)

            try:
                # Read raw binary data directly
                file_data = self.rfile.read(content_length)
                with open(target_path, 'wb') as f:
                    f.write(file_data)

                # Optional: trigger cache generation for this new wallpaper
                hyde_cache_script = os.path.expanduser('~/.local/lib/hyde/swwwallcache.sh')
                if os.path.exists(hyde_cache_script):
                    subprocess.Popen([hyde_cache_script, '-c', theme], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Wallpaper uploaded successfully!"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        elif path == '/api/set':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                filename = data.get('filename')
                if not filename:
                    raise ValueError("Filename is required")
                
                theme = get_current_theme()
                wallpapers_dir = get_wallpapers_dir(theme)
                filepath = os.path.join(wallpapers_dir, filename)

                if os.path.exists(filepath):
                    # Call hyde-shell to apply the wallpaper
                    # /home/anas/.local/bin/hyde-shell wallpaper -S --select filepath
                    shell_cmd = ['/home/anas/.local/bin/hyde-shell', 'wallpaper', '-S', '--select', filepath]
                    result = subprocess.run(shell_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "success", "message": "Wallpaper applied!"}).encode('utf-8'))
                    else:
                        raise RuntimeError(f"hyde-shell failed: {result.stderr or result.stdout}")
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Wallpaper file not found"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        elif path == '/api/delete':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                filename = data.get('filename')
                if not filename:
                    raise ValueError("Filename is required")

                theme = get_current_theme()
                wallpapers_dir = get_wallpapers_dir(theme)
                filepath = os.path.join(wallpapers_dir, filename)

                if os.path.exists(filepath) and os.path.commonpath([wallpapers_dir, filepath]) == wallpapers_dir:
                    os.remove(filepath)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "message": "Wallpaper deleted!"}).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Wallpaper not found or access denied"}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

        self.send_error(404)

def run_server():
    Handler = WallpaperManagerHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"=== HyDE Wallpaper Manager Server Running ===")
        print(f"URL: http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        
        # Open browser in a separate thread
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.shutdown()

if __name__ == '__main__':
    run_server()
