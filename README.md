DistributedFS – Distributed File Storage System
A lightweight Distributed File System built using Flask (Python) for backend and modern HTML/CSS/JS
for frontend.
The system simulates file distribution, replication, node monitoring, integrity checks, and analytics.
FEATURES
• File Upload (drag & drop + manual)
• Dashboard with system stats
• File management (search, delete, verify)
• Node monitoring + toggle system
• System monitor charts & logs
TECH STACK
Backend: Python, Flask, Flask-CORS
Frontend: HTML5, CSS3, JavaScript
PROJECT STRUCTURE
distributed-fs/
├── app.py                    # Flask Backend 
├── static/
│   ├── index.html           # Landing Page 
│   ├── dashboard.html       # Main Dashboard 
│   ├── upload.html          # Upload Page 
│   ├── files.html           # File Management 
│   ├── nodes.html           # Node Management 
│   └── monitor.html         # System Monitor
■■■ README.md
HOW TO RUN
1. pip install flask flask-cors
2. python app.py
3. Open http://localhost:5000
API ENDPOINTS
• GET /api/status
• POST /api/upload
• GET /api/files
• GET /api/files/
• DELETE /api/files/
• GET /api/download/
• POST /api/verify
• POST /api/nodes//toggle
• GET /api/replication
REVISION TRACKING SUMMARY
• Repository created for project
• 7+ meaningful commits maintained
• Feature branches used
• Merged after testing
Developer: Putta Sravan Kumar Reddy
