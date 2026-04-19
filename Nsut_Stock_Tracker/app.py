"""
app.py - Stock Tracker Flask App
Mini Project - NSUT
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from datetime import datetime
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from data_service import fetch_stock, fetch_multiple_stocks, fetch_historical, get_market_summary, AVAILABLE_SYMBOLS
from models import Portfolio

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.secret_key = "stocktracker_nsut_2025"

# ── Simple user database (no real DB needed for demo) ──
USERS = {
    "admin":  "admin123",
    "dhruv":  "nsut2025",
    "shivam": "nsut2025",
    "akshit": "nsut2025",
    "pujeet": "nsut2025",
    "khushal":"nsut2025",
}

# ── In-memory portfolio ──
_portfolio = Portfolio()
_messages  = []

# ── CORS ──
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response

@app.before_request
def preflight():
    if request.method == "OPTIONS":
        return jsonify({}), 200

# ── Helpers ──
def json_response(data, status=200):
    r = jsonify(data); r.status_code = status; return r

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def require_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            return json_response({"error": "Content-Type must be application/json"}, 415)
        return f(*args, **kwargs)
    return decorated

def validate_symbol(symbol):
    if not symbol or not symbol.isalpha(): return False, "Symbol must contain only letters"
    if len(symbol) > 5: return False, "Symbol too long"
    return True, ""

def get_portfolio_items():
    items, total = [], 0.0
    for symbol, qty in _portfolio.holdings.items():
        stock = fetch_stock(symbol)
        if stock:
            val = round(stock.price * qty, 2)
            total += val
            items.append({"symbol": symbol, "name": stock.name, "quantity": qty,
                          "price": stock.price, "change_pct": stock.change_pct, "market_value": val})
    return items, round(total, 2)

def get_market():
    data = get_market_summary()
    return {name: type("I", (), idx)() for name, idx in data["indices"].items()}

# ══════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════

@app.route("/login", methods=["GET"])
def login():
    if "username" in session:
        return redirect(url_for("dashboard"))
    msgs = _messages[:]
    _messages.clear()
    return render_template("login.html", messages=msgs)

@app.route("/login", methods=["POST"])
def login_post():
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    if USERS.get(username) == password:
        session["username"] = username
        return redirect(url_for("dashboard"))
    _messages.append(("Invalid username or password.", "error"))
    return redirect(url_for("login"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    _messages.append(("Logged out successfully.", "success"))
    return redirect(url_for("login"))

# ══════════════════════════════════════════════════
#  MAIN DASHBOARD
# ══════════════════════════════════════════════════

@app.route("/", methods=["GET"])
@login_required
def dashboard():
    global _messages
    all_stocks = [s for s in [fetch_stock(sym) for sym in AVAILABLE_SYMBOLS] if s]
    search_symbol = request.args.get("symbol", "").upper().strip()
    stock = fetch_stock(search_symbol) if search_symbol else None
    portfolio_items, total_value = get_portfolio_items()
    msgs = _messages[:]
    _messages = []
    return render_template("index.html",
        market=get_market(), all_stocks=all_stocks,
        stock=stock, search_symbol=search_symbol or None,
        portfolio=portfolio_items, total_value=total_value,
        messages=msgs, username=session.get("username", ""),
        now=datetime.now().strftime("%d %b %Y  %H:%M"))

@app.route("/portfolio/add", methods=["POST"])
@login_required
def portfolio_add():
    symbol = request.form.get("symbol", "").upper().strip()
    try:    qty = int(request.form.get("quantity", "0"))
    except: qty = 0
    if qty <= 0:
        _messages.append(("Quantity must be a positive number.", "error"))
        return redirect(url_for("dashboard"))
    if not fetch_stock(symbol):
        _messages.append((f'Symbol "{symbol}" not found.', "error"))
        return redirect(url_for("dashboard"))
    _portfolio.add_stock(symbol, qty)
    _messages.append((f"Added {qty} share(s) of {symbol} to your wallet.", "success"))
    return redirect(url_for("dashboard"))

@app.route("/portfolio/remove/<string:symbol>", methods=["POST"])
@login_required
def portfolio_remove(symbol):
    symbol = symbol.upper()
    if symbol in _portfolio.holdings:
        del _portfolio.holdings[symbol]
        _messages.append((f"Removed {symbol} from wallet.", "success"))
    else:
        _messages.append((f"{symbol} not in wallet.", "error"))
    return redirect(url_for("dashboard"))

# ══════════════════════════════════════════════════
#  API ENDPOINTS
# ══════════════════════════════════════════════════

@app.route("/api", methods=["GET"])
def api_info():
    return json_response({"api": "Stock Tracker API", "version": "1.0.0", "status": "running"})

@app.route("/api/market", methods=["GET"])
def api_market():
    return json_response({"success": True, "data": get_market_summary()})

@app.route("/api/stocks", methods=["GET"])
def api_list_stocks():
    return json_response({"success": True, "count": len(AVAILABLE_SYMBOLS), "symbols": AVAILABLE_SYMBOLS})

@app.route("/api/stock/<string:symbol>", methods=["GET"])
def api_get_stock(symbol):
    symbol = symbol.upper()
    valid, err = validate_symbol(symbol)
    if not valid: return json_response({"success": False, "error": err}, 400)
    stock = fetch_stock(symbol)
    if not stock: return json_response({"success": False, "error": f"'{symbol}' not found"}, 404)
    return json_response({"success": True, "data": stock.to_dict()})

@app.route("/api/stocks/batch", methods=["GET"])
def api_batch():
    raw = request.args.get("symbols", "")
    if not raw: return json_response({"success": False, "error": "'symbols' param required"}, 400)
    symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
    results = fetch_multiple_stocks(symbols)
    missing = [s for s in symbols if s not in {r["symbol"] for r in results}]
    return json_response({"success": True, "count": len(results), "data": results, "not_found": missing})

@app.route("/api/stock/<string:symbol>/history", methods=["GET"])
def api_history(symbol):
    symbol = symbol.upper()
    valid, err = validate_symbol(symbol)
    if not valid: return json_response({"success": False, "error": err}, 400)
    period = request.args.get("period", "1mo")
    if period not in {"1wk", "1mo", "3mo", "6mo", "1y"}:
        return json_response({"success": False, "error": "Invalid period"}, 400)
    history = fetch_historical(symbol, period)
    if not history: return json_response({"success": False, "error": f"No data for '{symbol}'"}, 404)
    return json_response({"success": True, "symbol": symbol, "period": period, "count": len(history), "data": history})

@app.route("/api/portfolio", methods=["POST"])
@require_json
def api_portfolio_add():
    body = request.get_json()
    symbol = body.get("symbol", "").upper()
    qty = body.get("quantity", 0)
    if not symbol: return json_response({"success": False, "error": "'symbol' required"}, 400)
    if not isinstance(qty, int) or qty <= 0: return json_response({"success": False, "error": "'quantity' must be positive int"}, 400)
    if not fetch_stock(symbol): return json_response({"success": False, "error": f"'{symbol}' not found"}, 404)
    _portfolio.add_stock(symbol, qty)
    return json_response({"success": True, "message": f"Added {qty} of {symbol}", "portfolio": _portfolio.to_dict()}, 201)

@app.route("/api/portfolio", methods=["GET"])
def api_portfolio_view():
    items, total = get_portfolio_items()
    return json_response({"success": True, "portfolio": items, "total_value": total, "currency": "USD"})

@app.route("/api/portfolio/<string:symbol>", methods=["DELETE"])
def api_portfolio_remove(symbol):
    symbol = symbol.upper()
    if symbol not in _portfolio.holdings:
        return json_response({"success": False, "error": f"'{symbol}' not in portfolio"}, 404)
    del _portfolio.holdings[symbol]
    return json_response({"success": True, "message": f"Removed {symbol}", "portfolio": _portfolio.to_dict()})

@app.errorhandler(404)
def not_found(e): return json_response({"success": False, "error": "Route not found"}, 404)

@app.errorhandler(405)
def method_not_allowed(e): return json_response({"success": False, "error": "Method not allowed"}, 405)

if __name__ == "__main__":
    print("=" * 50)
    print("  Stock Tracker — NSUT Mini Project")
    print("  Web UI : http://localhost:5000")
    print("  Login  : admin / admin123")
    print("=" * 50)
    import os
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
