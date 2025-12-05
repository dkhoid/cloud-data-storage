from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from minio import Minio
from minio.error import S3Error
import io
import stripe
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS Configuration - Allow all origins for development
CORS(app,
     resources={r"/*": {"origins": "*"}},
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)


# Handle OPTIONS requests for CORS preflight
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response


# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/cloud_storage')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
stripe.api_key = STRIPE_SECRET_KEY

# MinIO Configuration
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'user-files')

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False  # Set True for HTTPS in production
)

# Ensure bucket exists
try:
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        print(f"Created bucket: {MINIO_BUCKET}")
except S3Error as e:
    print(f"MinIO Error: {e}")


# Database connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated


# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'zip', 'doc', 'docx', 'mp4', 'mp3'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ==================== AUTH ENDPOINTS ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not password or not email:
        return jsonify({'error': 'All fields are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if username or email exists
        cur.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
        if cur.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 400

        # Create user
        cur.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s) RETURNING id, username, email, plan, storage_limit, storage_used
                    ''', (username, email, hash_password(password)))

        user = cur.fetchone()
        conn.commit()

        return jsonify({
            'message': 'Registration successful',
            'user': dict(user)
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT id, username, email, plan, storage_limit, storage_used, password_hash
                    FROM users
                    WHERE username = %s
                    ''', (username,))

        user = cur.fetchone()

        if not user or user['password_hash'] != hash_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401

        token = generate_token(user['id'])

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'plan': user['plan'],
                'storage_limit': user['storage_limit'],
                'storage_used': user['storage_used']
            }
        }), 200

    finally:
        cur.close()
        conn.close()


# ==================== FILE ENDPOINTS ====================

@app.route('/api/upload', methods=['POST'])
@token_required
def upload_file(current_user_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check storage limit
        cur.execute('SELECT storage_used, storage_limit FROM users WHERE id = %s', (current_user_id,))
        user = cur.fetchone()

        file_data = file.read()
        file_size = len(file_data)

        if user['storage_used'] + file_size > user['storage_limit']:
            return jsonify({'error': 'Storage limit exceeded'}), 413

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        minio_object_name = f"{current_user_id}/{timestamp}_{original_filename}"

        # Upload to MinIO
        minio_client.put_object(
            MINIO_BUCKET,
            minio_object_name,
            io.BytesIO(file_data),
            length=file_size,
            content_type=file.content_type
        )

        # Save to database
        cur.execute('''
                    INSERT INTO files (user_id, filename, original_filename, file_size,
                                       mime_type, minio_object_name)
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, filename, file_size, upload_date
                    ''', (current_user_id, original_filename, original_filename,
                          file_size, file.content_type, minio_object_name))

        file_record = cur.fetchone()

        # Update storage used
        cur.execute('''
                    UPDATE users
                    SET storage_used = storage_used + %s
                    WHERE id = %s
                    ''', (file_size, current_user_id))

        # Record usage history
        cur.execute('''
                    INSERT INTO usage_history (user_id, date, storage_used)
                    VALUES (%s, CURRENT_DATE, %s) ON CONFLICT (user_id, date) 
            DO
                    UPDATE SET storage_used = %s
                    ''', (current_user_id, user['storage_used'] + file_size, user['storage_used'] + file_size))

        conn.commit()

        return jsonify({
            'message': 'Upload successful',
            'file': dict(file_record)
        }), 201

    except S3Error as e:
        conn.rollback()
        return jsonify({'error': f'MinIO error: {str(e)}'}), 500
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/files', methods=['GET'])
@token_required
def get_files(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT id,
                           filename,
                           original_filename,
                           file_size,
                           mime_type,
                           upload_date,
                           is_public,
                           public_url
                    FROM files
                    WHERE user_id = %s
                    ORDER BY upload_date DESC
                    ''', (current_user_id,))

        files = cur.fetchall()

        return jsonify({
            'files': [dict(f) for f in files]
        }), 200

    finally:
        cur.close()
        conn.close()


@app.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    # Get token from Authorization header or query parameter
    token = request.headers.get('Authorization')
    if not token:
        token = request.args.get('token')

    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        if token.startswith('Bearer '):
            token = token[7:]
        data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        current_user_id = data['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT minio_object_name, original_filename, mime_type
                    FROM files
                    WHERE id = %s
                      AND user_id = %s
                    ''', (file_id, current_user_id))

        file_record = cur.fetchone()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        # Get file from MinIO
        response = minio_client.get_object(MINIO_BUCKET, file_record['minio_object_name'])
        file_data = response.read()

        # Update last accessed
        cur.execute('UPDATE files SET last_accessed = CURRENT_TIMESTAMP WHERE id = %s', (file_id,))
        conn.commit()

        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=file_record['original_filename'],
            mimetype=file_record['mime_type']
        )

    except S3Error as e:
        return jsonify({'error': f'MinIO error: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/delete/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(current_user_id, file_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT minio_object_name, file_size
                    FROM files
                    WHERE id = %s
                      AND user_id = %s
                    ''', (file_id, current_user_id))

        file_record = cur.fetchone()

        if not file_record:
            return jsonify({'error': 'File not found'}), 404

        # Delete from MinIO
        minio_client.remove_object(MINIO_BUCKET, file_record['minio_object_name'])

        # Delete from database
        cur.execute('DELETE FROM files WHERE id = %s', (file_id,))

        # Update storage used
        cur.execute('''
                    UPDATE users
                    SET storage_used = storage_used - %s
                    WHERE id = %s
                    ''', (file_record['file_size'], current_user_id))

        conn.commit()

        return jsonify({'message': 'File deleted successfully'}), 200

    except S3Error as e:
        conn.rollback()
        return jsonify({'error': f'MinIO error: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


# ==================== USER & BILLING ENDPOINTS ====================

@app.route('/api/user/info', methods=['GET'])
@token_required
def get_user_info(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT id,
                           username,
                           email,
                           plan,
                           storage_limit,
                           storage_used,
                           subscription_status,
                           subscription_end_date,
                           created_at
                    FROM users
                    WHERE id = %s
                    ''', (current_user_id,))

        user = cur.fetchone()

        # Get file count
        cur.execute('SELECT COUNT(*) as file_count FROM files WHERE user_id = %s', (current_user_id,))
        file_count = cur.fetchone()['file_count']

        return jsonify({
            'user': dict(user),
            'file_count': file_count,
            'storage_used_mb': round(user['storage_used'] / (1024 * 1024), 2),
            'storage_limit_mb': round(user['storage_limit'] / (1024 * 1024), 2),
            'storage_percentage': round((user['storage_used'] / user['storage_limit']) * 100, 2)
        }), 200

    finally:
        cur.close()
        conn.close()


@app.route('/api/pricing', methods=['GET'])
def get_pricing():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('SELECT * FROM pricing_plans WHERE is_active = TRUE ORDER BY price_monthly')
        plans = cur.fetchall()

        return jsonify({
            'plans': [dict(p) for p in plans]
        }), 200

    finally:
        cur.close()
        conn.close()


@app.route('/api/upgrade', methods=['POST'])
@token_required
def upgrade_plan(current_user_id):
    data = request.json
    plan_name = data.get('plan')
    billing_cycle = data.get('billing_cycle', 'monthly')  # monthly or yearly

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get plan details
        cur.execute('SELECT * FROM pricing_plans WHERE name = %s', (plan_name,))
        plan = cur.fetchone()

        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400

        amount = plan['price_monthly'] if billing_cycle == 'monthly' else plan['price_yearly']

        # In production, create Stripe payment intent here
        # For now, simulate successful payment

        # Update user plan
        cur.execute('''
                    UPDATE users
                    SET plan                  = %s,
                        storage_limit         = %s,
                        subscription_status   = 'active',
                        subscription_end_date = CURRENT_TIMESTAMP + INTERVAL '30 days'
                    WHERE id = %s
                    ''', (plan_name, plan['storage_limit'], current_user_id))

        # Record transaction
        cur.execute('''
                    INSERT INTO transactions (user_id, amount, description, status, transaction_type)
                    VALUES (%s, %s, %s, %s, %s)
                    ''', (current_user_id, amount, f'Upgrade to {plan_name}', 'completed', 'subscription'))

        conn.commit()

        return jsonify({
            'message': f'Successfully upgraded to {plan_name}',
            'plan': dict(plan)
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/api/transactions', methods=['GET'])
@token_required
def get_transactions(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT *
                    FROM transactions
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    ''', (current_user_id,))

        transactions = cur.fetchall()

        return jsonify({
            'transactions': [dict(t) for t in transactions]
        }), 200

    finally:
        cur.close()
        conn.close()


@app.route('/api/usage/history', methods=['GET'])
@token_required
def get_usage_history(current_user_id):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''
                    SELECT date, storage_used, bandwidth_used
                    FROM usage_history
                    WHERE user_id = %s
                    ORDER BY date DESC
                        LIMIT 30
                    ''', (current_user_id,))

        usage = cur.fetchall()

        return jsonify({
            'usage_history': [dict(u) for u in usage]
        }), 200

    finally:
        cur.close()
        conn.close()


# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    # In production, add admin authentication
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Total users
        cur.execute('SELECT COUNT(*) as total_users FROM users')
        total_users = cur.fetchone()['total_users']

        # Total storage used
        cur.execute('SELECT SUM(storage_used) as total_storage FROM users')
        total_storage = cur.fetchone()['total_storage'] or 0

        # Total files
        cur.execute('SELECT COUNT(*) as total_files FROM files')
        total_files = cur.fetchone()['total_files']

        # Revenue
        cur.execute('SELECT SUM(amount) as total_revenue FROM transactions WHERE status = %s', ('completed',))
        total_revenue = cur.fetchone()['total_revenue'] or 0

        return jsonify({
            'stats': {
                'total_users': total_users,
                'total_storage_gb': round(total_storage / (1024 ** 3), 2),
                'total_files': total_files,
                'total_revenue': float(total_revenue)
            }
        }), 200

    finally:
        cur.close()
        conn.close()


@app.route('/')
def home():
    return jsonify({
        'message': 'Cloud Storage API v2.0',
        'features': [
            'JWT Authentication',
            'MinIO Object Storage',
            'PostgreSQL Database',
            'Billing & Subscriptions',
            'Usage Tracking'
        ]
    })


if __name__ == '__main__':
    print("=" * 50)
    print("Cloud Storage Backend Starting...")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True, use_reloader=False)
