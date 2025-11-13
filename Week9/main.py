from flask import Flask, request, jsonify, Blueprint, abort, g, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hmac, hashlib, json, os, uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///payments_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(64), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)          
    amount_cents = db.Column(db.Integer, nullable=True)
    currency = db.Column(db.String(8), nullable=True)
    status = db.Column(db.String(32), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    metadata = db.Column(db.Text, nullable=True) 
    idempotency_key = db.Column(db.String(128), nullable=True, index=True)
    raw_request = db.Column(db.Text, nullable=True)

    def to_dict_v1(self):
        return {
            "payment_id": self.payment_id,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

    def to_dict_v2(self):
        return {
            "payment_id": self.payment_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status,
            "metadata": json.loads(self.metadata) if self.metadata else {},
            "created_at": self.created_at.isoformat()
        }

with app.app_context():
    db.create_all()

VALID_API_KEYS = {"demo-key-v1": "v1-client", "demo-key-v2": "v2-client"}

def require_api_key():
    key = request.headers.get("X-API-KEY")
    if not key or key not in VALID_API_KEYS:
        abort(401, "Missing or invalid X-API-KEY")
    g.client_id = VALID_API_KEYS[key]

bp_v1 = Blueprint('v1', __name__, url_prefix='/api/v1')

@bp_v1.before_request
def before_v1():
    require_api_key()
    announce_date = "2025-11-13"
    sunset_date = "2026-05-13"
    pass

@bp_v1.route('/payments', methods=['POST'])
def v1_create_payment():
    """
    v1 endpoint: create payment
    body: { "amount": 12.34 }
    Response: { payment_id, amount, status }
    """
    data = request.get_json(force=True)
    if not data or 'amount' not in data:
        return jsonify({"error": "amount required in body"}), 400
    try:
        amount = float(data['amount'])
    except Exception:
        return jsonify({"error": "invalid amount format"}), 400

    payment = Payment(
        payment_id = str(uuid.uuid4()),
        amount = amount,
        status = "completed",
        raw_request = json.dumps(data)
    )
    db.session.add(payment)
    db.session.commit()
    resp = jsonify(payment.to_dict_v1())
    resp.headers['Warning'] = '299 - "API v1 is deprecated; upgrade to /api/v2"'
    resp.headers['Deprecation'] = 'true'
    resp.headers['Sunset'] = '2026-05-13'
    return resp, 201

@bp_v1.route('/payments/<payment_id>', methods=['GET'])
def v1_get_payment(payment_id):
    payment = Payment.query.filter_by(payment_id=payment_id).first()
    if not payment:
        return jsonify({"error": "not found"}), 404
    resp = jsonify(payment.to_dict_v1())
    resp.headers['Warning'] = '299 - "API v1 is deprecated; upgrade to /api/v2"'
    resp.headers['Deprecation'] = 'true'
    resp.headers['Sunset'] = '2026-05-13'
    return resp

@bp_v1.route('/webhook', methods=['POST'])
def v1_webhook():
    payload = request.get_json(force=True)
    print("[v1 webhook] received:", payload)
    return jsonify({"ok": True}), 200

app.register_blueprint(bp_v1)



bp_v2 = Blueprint('v2', __name__, url_prefix='/api/v2')

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "supersecret-demo")

def compute_signature(body_bytes: bytes, secret: str):
    return hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()

@bp_v2.before_request
def before_v2():
    require_api_key()
    pass

@bp_v2.route('/payments', methods=['POST'])
def v2_create_payment():
    """
    v2 endpoint: create payment with idempotency and cents-based amount
    Headers:
      - Idempotency-Key: optional, string (recommended)
    Body:
      {
         "amount_cents": 1234,   # integer
         "currency": "USD",
         "metadata": { "order_id": "abc123" }
      }
    Response:
      {
         "payment_id": "...",
         "amount_cents": 1234,
         "currency": "USD",
         "status": "pending"
      }
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "json body required"}), 400

    # validation
    if 'amount_cents' not in data:
        if 'amount' in data:
            try:
                amount_float = float(data['amount'])
                amount_cents = int(round(amount_float * 100))
                warning_msg = "Using deprecated 'amount' float field. Use amount_cents (integer) instead."
            except:
                return jsonify({"error": "invalid amount"}), 400
        else:
            return jsonify({"error": "amount_cents required"}), 400
    else:
        try:
            amount_cents = int(data['amount_cents'])
            warning_msg = None
        except:
            return jsonify({"error": "amount_cents must be integer"}), 400

    currency = data.get('currency', 'USD')
    metadata = data.get('metadata', {})

    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key:
        existing = Payment.query.filter_by(idempotency_key=idempotency_key, client_id=getattr(g, 'client_id', None)).first()
        if existing:
            resp = jsonify(existing.to_dict_v2())
            if warning_msg:
                resp.headers['Warning'] = f'199 - "{warning_msg}"'
            return resp, 200

    # create payment row
    payment = Payment(
        payment_id = str(uuid.uuid4()),
        amount = (amount_cents / 100.0),
        amount_cents = amount_cents,
        currency = currency,
        status = "pending",  
        metadata = json.dumps(metadata),
        idempotency_key = idempotency_key,
        raw_request = json.dumps(data)
    )
    db.session.add(payment)
    db.session.commit()

    payment.status = "completed"
    db.session.commit()

    resp = jsonify(payment.to_dict_v2())
    if warning_msg:
        resp.headers['Warning'] = f'199 - "{warning_msg}"'
    resp.headers['X-API-Version'] = 'v2'
    return resp, 201

@bp_v2.route('/payments/<payment_id>', methods=['GET'])
def v2_get_payment(payment_id):
    payment = Payment.query.filter_by(payment_id=payment_id).first()
    if not payment:
        return jsonify({"error": "not found"}), 404
    resp = jsonify(payment.to_dict_v2())
    resp.headers['X-API-Version'] = 'v2'
    return resp

@bp_v2.route('/payments', methods=['GET'])
def v2_list_payments():
    page = max(1, int(request.args.get('page', 1)))
    page_size = min(100, int(request.args.get('page_size', 20)))
    q = Payment.query.order_by(Payment.created_at.desc())
    items = q.offset((page-1)*page_size).limit(page_size).all()
    return jsonify({
        "page": page,
        "page_size": page_size,
        "items": [p.to_dict_v2() for p in items]
    })

@bp_v2.route('/webhook', methods=['POST'])
def v2_webhook():
    body = request.get_data()
    signature = request.headers.get('X-Signature')
    computed = compute_signature(body, WEBHOOK_SECRET)
    if not signature or not hmac.compare_digest(signature, computed):
        return jsonify({"error": "invalid signature"}), 403
    payload = request.get_json(force=True)
    print("[v2 webhook] verified:", payload)
    return jsonify({"ok": True}), 200

app.register_blueprint(bp_v2)

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
