#!/usr/bin/env python3
"""
Ultra-Minimal Deployment Entry Point - Now Connected to Fast Dashboard
Optimized for <500MB Docker image and single port deployment
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point that starts the fast dashboard"""
    try:
        # Try to run the fast dashboard directly
        print("🚀 Starting Fast Dashboard...")
        from fast_dashboard import app, dashboard
        
        PORT = int(os.environ.get('PORT', 5000))
        print(f"📊 Dashboard running on port {PORT}")
        print(f"🌐 Access: http://localhost:{PORT}")
        
        app.run(host='0.0.0.0', port=PORT, debug=False)
        
    except ImportError as e:
        print(f"❌ Fast dashboard import failed: {e}")
        print("🔄 Falling back to minimal dashboard...")
        run_minimal_dashboard()
    except Exception as e:
        print(f"❌ Dashboard startup failed: {e}")
        print("🔄 Falling back to minimal dashboard...")
        run_minimal_dashboard()

def run_minimal_dashboard():
    """Fallback minimal dashboard"""
    from flask import Flask, jsonify, render_template_string
    
    app = Flask(__name__)
    PORT = int(os.environ.get('PORT', 5000))
    
    MINIMAL_TEMPLATE = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading System - Fallback Mode</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .status { padding: 20px; border-radius: 5px; margin: 20px 0; background: #fff3cd; color: #856404; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Trading System - Fallback Mode</h1>
            <div class="status">
                <strong>⚠️ Running in minimal mode</strong><br>
                The full dashboard is not available. System is operational on port {{ port }}.
            </div>
        </div>
    </body>
    </html>
    """
    
    @app.route('/')
    def home():
        return render_template_string(MINIMAL_TEMPLATE, port=PORT)
    
    @app.route('/health')
    def health():
        return jsonify({"status": "minimal", "port": PORT})
    
    print(f"🔄 Minimal dashboard running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()