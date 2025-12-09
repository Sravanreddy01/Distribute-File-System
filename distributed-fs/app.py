from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import time
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

# In-memory storage
files_storage = []
nodes_status = [True, True, True]
storage_used = 0.0
replication_factor = 3
system_logs = []

def generate_checksum(filename, size):
    return hashlib.sha256(f"{filename}{size}{time.time()}".encode()).hexdigest()[:10]

def add_log(message, level='info'):
    system_logs.append({
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'level': level
    })
    if len(system_logs) > 100:
        system_logs.pop(0)

# Serve HTML pages
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/dashboard')
def dashboard():
    return send_from_directory('static', 'dashboard.html')

@app.route('/upload')
def upload_page():
    return send_from_directory('static', 'upload.html')

@app.route('/files')
def files_page():
    return send_from_directory('static', 'files.html')

@app.route('/nodes')
def nodes_page():
    return send_from_directory('static', 'nodes.html')

@app.route('/monitor')
def monitor_page():
    return send_from_directory('static', 'monitor.html')

# API Routes
@app.route('/api/status', methods=['GET'])
def get_status():
    active_nodes = sum(nodes_status)
    return jsonify({
        'success': True,
        'data': {
            'nodes': [
                {'id': 0, 'name': 'Master Node', 'status': 'ONLINE'},
                {'id': 1, 'name': 'Storage Node 1', 'status': 'ONLINE' if nodes_status[0] else 'OFFLINE'},
                {'id': 2, 'name': 'Storage Node 2', 'status': 'ONLINE' if nodes_status[1] else 'OFFLINE'},
                {'id': 3, 'name': 'Storage Node 3', 'status': 'ONLINE' if nodes_status[2] else 'OFFLINE'}
            ],
            'file_count': len(files_storage),
            'storage_used': round(storage_used, 2),
            'replication_factor': replication_factor,
            'active_nodes': active_nodes,
            'health': 'healthy' if active_nodes >= 2 else 'degraded'
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global storage_used
    
    data = request.get_json()
    filename = data.get('filename')
    size = float(data.get('size', 0))
    
    if not filename or size <= 0:
        return jsonify({'success': False, 'error': 'Invalid filename or size'}), 400
    
    chunks = max(1, int(size / 64))
    checksum = generate_checksum(filename, size)
    active_nodes = [i+1 for i, status in enumerate(nodes_status) if status]
    
    file_data = {
        'id': len(files_storage) + 1,
        'name': filename,
        'size': size,
        'checksum': checksum,
        'chunks': chunks,
        'replicas': active_nodes,
        'uploaded_at': datetime.now().isoformat(),
        'status': 'healthy' if len(active_nodes) >= 2 else 'degraded'
    }
    
    files_storage.append(file_data)
    storage_used += size
    add_log(f"File uploaded: {filename} ({size:.2f} MB)", 'success')
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'data': file_data
    })

@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify({
        'success': True,
        'data': {
            'files': files_storage,
            'total': len(files_storage)
        }
    })

@app.route('/api/files/<int:file_id>', methods=['GET'])
def get_file(file_id):
    file_data = next((f for f in files_storage if f['id'] == file_id), None)
    
    if not file_data:
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    return jsonify({
        'success': True,
        'data': file_data
    })

@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    file_data = next((f for f in files_storage if f['id'] == file_id), None)
    
    if not file_data:
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    add_log(f"File downloaded: {file_data['name']}", 'info')
    
    return jsonify({
        'success': True,
        'message': 'Download initiated',
        'data': {
            'filename': file_data['name'],
            'size': file_data['size'],
            'checksum': file_data['checksum'],
            'chunks': file_data['chunks']
        }
    })

@app.route('/api/verify', methods=['POST'])
def verify_integrity():
    results = []
    
    for file_data in files_storage:
        active_replicas = sum(1 for node in file_data['replicas'] if nodes_status[node-1])
        status = 'healthy' if active_replicas >= 2 else 'degraded'
        
        results.append({
            'filename': file_data['name'],
            'checksum': file_data['checksum'],
            'replicas': active_replicas,
            'status': status
        })
    
    add_log(f"Integrity check completed: {len(results)} files verified", 'success')
    
    return jsonify({
        'success': True,
        'message': f'Verified {len(results)} files',
        'data': results
    })

@app.route('/api/nodes/<int:node_id>/toggle', methods=['POST'])
def toggle_node(node_id):
    global nodes_status
    
    if node_id < 1 or node_id > 3:
        return jsonify({'success': False, 'error': 'Invalid node ID'}), 400
    
    nodes_status[node_id - 1] = not nodes_status[node_id - 1]
    new_status = 'ONLINE' if nodes_status[node_id - 1] else 'OFFLINE'
    
    for file_data in files_storage:
        active_replicas = sum(1 for node in file_data['replicas'] if nodes_status[node-1])
        file_data['status'] = 'healthy' if active_replicas >= 2 else 'degraded'
    
    add_log(f"Node {node_id} is now {new_status}", 'warning' if new_status == 'OFFLINE' else 'success')
    
    return jsonify({
        'success': True,
        'message': f'Node {node_id} is now {new_status}',
        'data': {
            'node_id': node_id,
            'status': new_status,
            'active_nodes': sum(nodes_status)
        }
    })

@app.route('/api/replication', methods=['GET'])
def check_replication():
    replication_data = []
    
    for file_data in files_storage:
        active_replicas = sum(1 for node in file_data['replicas'] if nodes_status[node-1])
        
        replication_data.append({
            'filename': file_data['name'],
            'total_replicas': len(file_data['replicas']),
            'active_replicas': active_replicas,
            'status': file_data['status']
        })
    
    return jsonify({
        'success': True,
        'data': {
            'files': replication_data,
            'active_nodes': sum(nodes_status)
        }
    })

@app.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    global storage_used
    
    file_data = next((f for f in files_storage if f['id'] == file_id), None)
    
    if not file_data:
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    storage_used -= file_data['size']
    files_storage.remove(file_data)
    add_log(f"File deleted: {file_data['name']}", 'warning')
    
    return jsonify({
        'success': True,
        'message': f'File {file_data["name"]} deleted successfully'
    })

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify({
        'success': True,
        'data': list(reversed(system_logs[-50:]))
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    total_chunks = sum(f['chunks'] for f in files_storage)
    avg_file_size = storage_used / len(files_storage) if files_storage else 0
    
    return jsonify({
        'success': True,
        'data': {
            'total_files': len(files_storage),
            'total_storage': round(storage_used, 2),
            'total_chunks': total_chunks,
            'avg_file_size': round(avg_file_size, 2),
            'active_nodes': sum(nodes_status),
            'replication_factor': replication_factor
        }
    })

@app.route('/api/reset', methods=['POST'])
def reset_system():
    global files_storage, storage_used, nodes_status
    
    files_storage = []
    storage_used = 0.0
    nodes_status = [True, True, True]
    add_log("System reset", 'warning')
    
    return jsonify({
        'success': True,
        'message': 'System reset successfully'
    })

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("=" * 60)
    print("🚀 DistributedFS Backend Server")
    print("=" * 60)
    print("Server running on: http://localhost:5000")
    print("\nAvailable Pages:")
    print("  http://localhost:5000/           - Landing Page")
    print("  http://localhost:5000/dashboard  - Main Dashboard")
    print("  http://localhost:5000/upload     - Upload Files")
    print("  http://localhost:5000/files      - File Management")
    print("  http://localhost:5000/nodes      - Node Management")
    print("  http://localhost:5000/monitor    - System Monitor")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)