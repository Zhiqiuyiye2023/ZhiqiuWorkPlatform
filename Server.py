"""
知秋工作平台 - 支持手机访问的API服务器
"""
import logging
import os
import socket
import threading
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import yaml
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from pyngrok import ngrok

# 配置日志
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 基础配置
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'C:\\Server'  # 指定共享位置

# 设置数据库目录
app.config['DATABASE_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database')

# 确保数据库目录存在
os.makedirs(app.config['DATABASE_PATH'], exist_ok=True)

# 配置 SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.config['DATABASE_PATH'], 'users.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 获取本机IP地址
def get_local_ip():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        print(f"获取本机IP失败: {e}")
        return "localhost"

# 服务器URL配置
SERVER_URLS = {
    'local': f'http://{get_local_ip()}:5000',
    'localhost': 'http://localhost:5000'
}

# 使用英文输出，避免中文乱码
print("="*50)
print("ZhiQiu Work Platform Server Started:")
for name, url in SERVER_URLS.items():
    print(f"{name}: {url}")
print("="*50)

# 数据模型
class User(db.Model):
    """用户数据模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    machine_code = db.Column(db.String(120), unique=True, nullable=False)
    machine_code_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=False)
    api_calls = db.Column(db.Integer, default=0)
    last_api_call = db.Column(db.DateTime)
    shells = db.Column(db.Integer, default=2000)
    register_time = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, default=datetime.now)

    def check_password(self, password):
        """检查密码是否正确"""
        return self.password == password

    def check_shells(self, amount=10):
        """检查用户是否有足够的贝壳"""
        if self.is_admin:
            return True
        return self.shells >= amount

    def use_shells(self, amount=10):
        """使用贝壳"""
        if self.is_admin:
            return True
        if self.check_shells(amount):
            self.shells -= amount
            db.session.commit()
            return True
        return False

    def __repr__(self):
        return f'<User {self.username}>'

# 在线用户管理
online_users = {}

# 添加请求计数器和锁
class RequestCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.count += 1
            return self.count
    
    def decrement(self):
        with self.lock:
            self.count -= 1
            return self.count

request_counter = RequestCounter()

# 清理过期用户
def cleanup_online_users():
    """清理超过15分钟未活动的用户"""
    current_time = datetime.now()
    expired_users = []
    for username, last_active in online_users.items():
        if current_time - last_active > timedelta(minutes=15):
            expired_users.append(username)
    
    for username in expired_users:
        online_users.pop(username, None)

# 清理过期客户端记录
def cleanup_expired_clients():
    """清理超过15分钟未活动的客户端，将其状态设置为离线"""
    import json
    import os
    from datetime import datetime, timedelta
    
    records_file = 'client_records.json'
    if not os.path.exists(records_file):
        return
    
    try:
        with open(records_file, 'r', encoding='utf-8') as f:
            records = json.load(f)
        
        current_time = datetime.now()
        updated = False
        
        for record in records:
            if record.get('status') == 'online':
                # 检查最后连接时间
                last_connect_str = record.get('last_connect_time')
                if last_connect_str:
                    try:
                        last_connect = datetime.strptime(last_connect_str, '%Y-%m-%d %H:%M:%S')
                        if current_time - last_connect > timedelta(minutes=15):
                            record['status'] = 'offline'
                            updated = True
                    except Exception:
                        pass
        
        if updated:
            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"清理过期客户端记录失败: {str(e)}")

# 获取在线用户数
def get_online_users_count():
    """获取在线用户数"""
    cleanup_online_users()
    cleanup_expired_clients()
    return len(online_users)

# 更新用户活动时间
def update_user_activity():
    """更新用户活动时间"""
    if 'username' in session:
        username = session['username']
        online_users[username] = datetime.now()
        # 更新数据库中的在线状态
        try:
            user = User.query.filter_by(username=username).first()
            if user:
                user.is_online = True
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新用户活动状态失败: {str(e)}")

# 在每个请求之前更新用户活动时间
@app.before_request
def before_request():
    if request.endpoint not in ['static']:
        update_user_activity()

# 装饰器
@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/healthcheck')
def healthcheck():
    """健康检查"""
    return jsonify({"status": "ok", "message": "知秋工作平台运行正常"})

# API路由
@app.route('/api/v1/healthcheck')
def api_healthcheck():
    """API健康检查"""
    return jsonify({"status": "ok", "message": "知秋工作平台API运行正常"})

@app.route('/api/v1/online_users')
def api_online_users():
    """获取在线用户数"""
    cleanup_online_users()
    return jsonify({
        'count': len(online_users),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/project_info')
def api_project_info():
    """获取项目信息"""
    # 从version.json文件中读取版本信息
    import json
    import os
    
    # 获取version.json文件的路径
    version_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'version.json')
    
    # 根据请求来源选择正确的服务器URL
    if 'external' in SERVER_URLS and request.host.endswith('.ngrok-free.app'):
        base_url = SERVER_URLS['external']
    else:
        base_url = SERVER_URLS['local']
    
    try:
        with open(version_file_path, 'r', encoding='utf-8') as f:
            project_info = json.load(f)
        
        # 添加下载链接
        project_info['download_url'] = f"{base_url}/api/v1/download_update"
    except Exception as e:
        # 如果读取失败，使用默认值
        project_info = {
            "version": "1.0.3",
            "name": "知秋工作平台",
            "description": "知秋工作平台是一个功能强大的桌面应用程序",
            "update_log": "1. 修复了一些已知bug\n2. 优化了性能\n3. 新增了一些功能",
            "update_time": datetime.now().isoformat(),
            "download_url": f"{base_url}/api/v1/download_update"
        }
    
    return jsonify(project_info)

@app.route('/api/v1/client/report', methods=['POST'])
def api_client_report():
    """处理客户端信息上报"""
    import json
    import os
    
    try:
        # 获取客户端上报的信息
        client_info = request.json
        
        if not client_info:
            return jsonify({"error": "缺少客户端信息"}), 400
        
        # 保存客户端记录
        import os
        records_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_records.json')
        
        # 加载现有记录
        if os.path.exists(records_file):
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        else:
            records = []
        
        # 检查是否已存在相同MAC地址或IP的记录
        existing_record = None
        for record in records:
            # 优先使用MAC地址匹配，因为MAC地址更稳定
            # 排除'未知MAC地址'的情况，避免所有无MAC地址的客户端被视为同一个
            if (record.get('mac_address') and client_info.get('mac_address') and 
                record.get('mac_address') != '未知MAC地址' and 
                client_info.get('mac_address') != '未知MAC地址' and 
                record.get('mac_address') == client_info.get('mac_address')):
                existing_record = record
                break
            # 如果没有有效的MAC地址，再使用IP地址匹配
            elif record.get('ip') == client_info.get('ip'):
                existing_record = record
                break
        
        if existing_record:
            # 更新现有记录
            # 保留初次连接时间
            first_connect_time = existing_record.get('connect_time', client_info.get('connect_time'))
            # 保留连接次数，只在上线时递增
            current_connect_count = existing_record.get('connect_count', 0)
            # 只有当客户端状态为online时才增加连接次数
            if client_info.get('status') == 'online':
                new_connect_count = current_connect_count + 1
            else:
                new_connect_count = current_connect_count
            # 先更新所有字段
            existing_record.update(client_info)
            # 再设置保留的字段，确保不会被覆盖
            existing_record['connect_time'] = first_connect_time
            existing_record['connect_count'] = new_connect_count
            # 确保状态正确
            existing_record['status'] = client_info.get('status', 'offline')
        else:
            # 添加新记录
            records.append(client_info)
        
        # 保存记录
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        return jsonify({"status": "ok", "message": "客户端信息上报成功"}), 200
        
    except Exception as e:
        logger.error(f"处理客户端上报失败: {str(e)}")
        return jsonify({"error": f"处理客户端上报失败: {str(e)}"}), 500

@app.route('/api/v1/server_files_info')
def api_server_files_info():
    """获取服务器上的安装文件信息"""
    import os
    import glob
    import hashlib
    
    # 获取dist目录路径 - 修正路径计算
    server_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(server_dir, 'dist')
    
    files_info = []
    
    try:
        # 遍历dist目录下的所有文件
        for file_path in glob.glob(os.path.join(dist_dir, '**', '*'), recursive=True):
            if os.path.isfile(file_path):
                # 计算文件MD5
                with open(file_path, 'rb') as f:
                    md5_hash = hashlib.md5()
                    while chunk := f.read(4096):
                        md5_hash.update(chunk)
                    md5 = md5_hash.hexdigest()
                
                # 获取文件相对路径（相对于dist目录）
                rel_path = os.path.relpath(file_path, dist_dir)
                
                # 获取文件名
                file_name = os.path.basename(file_path)
                
                # 获取文件大小
                file_size = os.path.getsize(file_path)
                
                # 获取文件修改时间
                modify_time = os.path.getmtime(file_path)
                
                # 提取文件名中的版本号
                version = ""
                if file_name.startswith('知秋工作平台v'):
                    # 从文件名中提取版本号，如"知秋工作平台v1.1.0.exe" -> "1.1.0"
                    version = file_name.split('v')[1].split('.exe')[0]
                
                files_info.append({
                    "file_path": rel_path,
                    "file_name": file_name,
                    "size": file_size,
                    "md5": md5,
                    "modify_time": modify_time,
                    "version": version
                })
    except Exception as e:
        return jsonify({"error": f"获取服务器文件信息失败: {str(e)}"}), 500
    
    return jsonify({
        "files": files_info,
        "total_files": len(files_info)
    })

@app.route('/api/v1/download_update')
def api_download_update():
    """下载更新包"""
    # 这里应该返回实际的更新包文件
    # 暂时返回一个简单的文本文件作为示例
    from flask import send_file
    import tempfile
    
    # 创建一个临时文件作为示例更新包
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.zip', delete=False)
    temp_file.write('这是一个示例更新包')
    temp_file.close()
    
    return send_file(temp_file.name, as_attachment=True, download_name='update.zip')

@app.route('/api/v1/messages/unread', methods=['GET'])
def api_get_unread_messages():
    """获取客户端未读消息"""
    import json
    import os
    
    try:
        # 获取客户端标识（使用MAC地址或IP地址）
        client_id = request.args.get('client_id')
        if not client_id:
            return jsonify({"error": "缺少客户端标识"}), 400
        
        # 加载消息文件（使用项目根目录）
        project_root = os.path.dirname(os.path.abspath(__file__))
        messages_file = os.path.join(project_root, 'messages.json')
        if not os.path.exists(messages_file):
            return jsonify({"messages": []}), 200
        
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
        
        # 获取客户端的未读消息
        client_messages = messages_data.get(client_id, {}).get('messages', [])
        unread_messages = [msg for msg in client_messages if not msg.get('read', False)]
        
        return jsonify({"messages": unread_messages}), 200
        
    except Exception as e:
        logger.error(f"获取未读消息失败: {str(e)}")
        return jsonify({"error": f"获取未读消息失败: {str(e)}"}), 500

@app.route('/api/v1/messages/read', methods=['POST'])
def api_mark_message_read():
    """标记消息已读"""
    import json
    import os
    
    try:
        # 获取请求数据
        data = request.json
        client_id = data.get('client_id')
        message_id = data.get('message_id')
        
        if not client_id or not message_id:
            return jsonify({"error": "缺少客户端标识或消息ID"}), 400
        
        # 加载消息文件（使用项目根目录）
        project_root = os.path.dirname(os.path.abspath(__file__))
        messages_file = os.path.join(project_root, 'messages.json')
        if not os.path.exists(messages_file):
            return jsonify({"error": "消息文件不存在"}), 404
        
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
        
        # 标记消息已读
        if client_id in messages_data:
            messages = messages_data[client_id].get('messages', [])
            for msg in messages:
                if msg.get('id') == message_id:
                    msg['read'] = True
                    break
            
            # 保存更新后的消息
            with open(messages_file, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)
            
            return jsonify({"status": "ok", "message": "消息已标记为已读"}), 200
        else:
            return jsonify({"error": "客户端不存在"}), 404
        
    except Exception as e:
        logger.error(f"标记消息已读失败: {str(e)}")
        return jsonify({"error": f"标记消息已读失败: {str(e)}"}), 500

@app.route('/api/v1/messages/send', methods=['POST'])
def api_send_message():
    """发送消息到客户端"""
    import json
    import os
    import uuid
    from datetime import datetime
    
    try:
        # 获取请求数据
        data = request.json
        client_ids = data.get('client_ids', [])
        title = data.get('title')
        content = data.get('content')
        
        if not client_ids or not title or not content:
            return jsonify({"error": "缺少客户端ID、标题或内容"}), 400
        
        # 加载消息文件（使用项目根目录）
        project_root = os.path.dirname(os.path.abspath(__file__))
        messages_file = os.path.join(project_root, 'messages.json')
        if os.path.exists(messages_file):
            with open(messages_file, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)
        else:
            messages_data = {}
        
        # 为每个客户端创建消息
        sent_count = 0
        for client_id in client_ids:
            # 确保客户端消息列表存在
            if client_id not in messages_data:
                messages_data[client_id] = {'messages': []}
            
            # 创建消息
            message = {
                'id': str(uuid.uuid4()),
                'title': title,
                'content': content,
                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'read': False
            }
            
            # 添加消息
            messages_data[client_id]['messages'].append(message)
            sent_count += 1
        
        # 保存消息
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({"status": "ok", "message": f"已成功发送消息到 {sent_count} 个客户端"}), 200
        
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")
        return jsonify({"error": f"发送消息失败: {str(e)}"}), 500

@app.route('/dist/<path:filename>')
def dist_file(filename):
    """提供dist目录下的文件下载"""
    from flask import send_from_directory, abort
    import os
    import glob
    
    # 获取dist目录路径 - 修正路径计算
    server_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(server_dir, 'dist')
    
    # 检查直接路径是否存在
    file_path = os.path.join(dist_dir, filename)
    if os.path.exists(file_path):
        return send_from_directory(dist_dir, filename, as_attachment=False)
    
    # 如果直接路径不存在，尝试在子目录中查找文件
    # 递归查找dist目录下所有匹配的文件
    found_files = glob.glob(os.path.join(dist_dir, '**', filename), recursive=True)
    if found_files:
        # 使用找到的第一个文件
        actual_file_path = found_files[0]
        # 获取相对于dist目录的路径
        rel_path = os.path.relpath(actual_file_path, dist_dir)
        return send_from_directory(dist_dir, rel_path, as_attachment=False)
    
    # 文件不存在
    abort(404)

# 基础HTML模板
@app.route('/templates/index.html')
def template_index():
    """首页模板"""
    return render_template('index.html')

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # 启动ngrok，创建公网隧道 - 仅在环境变量或配置中启用时启动
    enable_ngrok = os.environ.get('ENABLE_NGROK', 'true').lower() == 'true'
    
    if enable_ngrok:
        try:
            # 检查并停止所有已运行的ngrok进程，解决免费账户只能运行1个会话的限制
            import psutil
            import time
            
            print("Checking for existing ngrok processes...")
            
            # 第一次终止尝试：正常终止
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    proc_cmdline = proc.info['cmdline'] or []
                    
                    # 更全面的ngrok进程检测：检查进程名或命令行中包含ngrok
                    if proc_name in ['ngrok.exe', 'ngrok'] or 'ngrok' in ' '.join(proc_cmdline).lower():
                        print(f"Stopping existing ngrok process: PID {proc.info['pid']}, Name: {proc_name}")
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 等待2秒让进程有时间终止
            time.sleep(2)
            
            # 第二次终止尝试：强制终止仍在运行的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    proc_cmdline = proc.info['cmdline'] or []
                    
                    if proc_name in ['ngrok.exe', 'ngrok'] or 'ngrok' in ' '.join(proc_cmdline).lower():
                        print(f"Force killing stubborn ngrok process: PID {proc.info['pid']}")
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # 等待1秒确保所有进程都已终止
            time.sleep(1)
            
            # 验证所有ngrok进程都已终止
            remaining_ngrok = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    proc_cmdline = proc.info['cmdline'] or []
                    if proc_name in ['ngrok.exe', 'ngrok'] or 'ngrok' in ' '.join(proc_cmdline).lower():
                        remaining_ngrok.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if remaining_ngrok:
                print(f"Warning: Some ngrok processes could not be terminated: {remaining_ngrok}")
            else:
                print("All existing ngrok processes have been stopped successfully")
            
            # 清除pyngrok缓存，确保使用新的会话
            import shutil
            import tempfile
            pyngrok_dir = os.path.join(tempfile.gettempdir(), 'pyngrok')
            if os.path.exists(pyngrok_dir):
                print(f"Clearing pyngrok cache: {pyngrok_dir}")
                shutil.rmtree(pyngrok_dir, ignore_errors=True)
            
            # 设置ngrok认证令牌（使用项目中已有的令牌）
            ngrok.set_auth_token("2tIyYEOILqUgk1Aigitv9Vx8p8Z_25CFQReTuhXfeZaFKCtUk")
            
            # 配置固定域名
            fixed_domain = "bream-guided-poodle.ngrok-free.app"
            tunnel = ngrok.connect(5000, proto="http", url=f"https://{fixed_domain}")
            public_url = tunnel.public_url
            print("="*50)
            print(f"Public URL: {public_url}")
            print("="*50)
            
            # 将公网地址添加到SERVER_URLS配置
            SERVER_URLS['external'] = public_url
            
            # Write public URL to temporary file for main.py to read
            try:
                with open('ngrok_url.txt', 'w') as f:
                    f.write(public_url)
            except Exception as e:
                print(f"Failed to write ngrok URL to file: {e}")
            
        except Exception as e:
            print(f"Failed to start ngrok: {e}")
            print("Only local access is supported")
            # If ngrok fails to start, delete the temporary file if it exists
            try:
                if os.path.exists('ngrok_url.txt'):
                    os.remove('ngrok_url.txt')
            except Exception as e:
                print(f"Failed to delete ngrok URL file: {e}")
    else:
        print("ngrok tunnel is disabled, only local access is supported")
    
    # 启动定期清理客户端状态的线程
def start_cleanup_thread():
    """启动定期清理客户端状态的线程"""
    import threading
    import time
    
    def cleanup_task():
        while True:
            try:
                cleanup_expired_clients()
            except Exception as e:
                logger.error(f"定期清理客户端状态失败: {str(e)}")
            # 每60秒清理一次
            time.sleep(60)
    
    cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("定期清理客户端状态的线程已启动")

# 启动定期清理线程
start_cleanup_thread()

# 启动Flask服务器
app.run(host='0.0.0.0', port=5000, debug=False)