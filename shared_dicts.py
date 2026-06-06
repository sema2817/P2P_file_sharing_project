import json
import os
import threading

file_lock = threading.Lock()

IP_TO_USER_FILE = "ip_to_username.json"
USER_TO_IP_FILE = "username_to_ip.json"
CONTENT_DICT_FILE = "content_dict.json"

def _load_file(filename):
    if not os.path.exists(filename):
        return {}
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save_file(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        pass 


def update_ip_to_username(ip, username):
    with file_lock:
        data = _load_file(IP_TO_USER_FILE)
        data[ip] = username
        _save_file(IP_TO_USER_FILE, data)

def get_username_by_ip(ip):
    with file_lock:
        data = _load_file(IP_TO_USER_FILE)
        return data.get(ip, ip)

def update_username_to_ip(username, ip):
    with file_lock:
        data = _load_file(USER_TO_IP_FILE)
        data[username] = ip
        _save_file(USER_TO_IP_FILE, data)

def get_ip_by_username(username):
    with file_lock:
        data = _load_file(USER_TO_IP_FILE)
        return data.get(username, None)

def update_content_dict(chunks, username):
    with file_lock:
        data = _load_file(CONTENT_DICT_FILE)
        for chunk in chunks:
            if chunk not in data:
                data[chunk] = []
            if username not in data[chunk]:
                data[chunk].append(username)
        _save_file(CONTENT_DICT_FILE, data)

def get_content_dict():
    with file_lock:
        return _load_file(CONTENT_DICT_FILE)

def clear_content_dict():
    with file_lock:
        _save_file(CONTENT_DICT_FILE, {})
