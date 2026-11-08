
import os
import secrets
import requests
import sys
from pathlib import Path
import json
from datetime import timedelta

from flask import Flask, redirect, request, session, render_template, jsonify
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from modules.admin import service as AdminService
from modules.economy import service as EconomyService
from modules.jobs import service as JobsService
from modules.fun import service as FunService
from modules.investments import service as InvestmentsService
from modules.items import service as ItemsService

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

REDIRECT_URI = "http://127.0.0.1:5000/callback"

ROOT_DIR = Path(__file__).resolve().parent.parent

ECONOMY_PATH = ROOT_DIR / "modules/economy/economy.json"

# ECONOMIA Campos permitidos em cada categoria
ECONOMY_GROUPS = {
    "geral": [
        "items_price_coefficient",
        "aura_coefficient"
    ],
    "privados": [
        "private_salary_coefficient",
        "private_salary_parity_base",
        "private_salary_parity"
    ],
    "bolsa": [
        "money_assistance_value",
        "money_assistance_variance",
        "money_assistance_maxmoney"
    ],
    "tax_rent": [
        "tax_rent",
        "tax_minrent"
    ],
    "tax_item": [
        "tax_item",
        "tax_minitem"
    ],
    "tax_pix": [
        "tax_pix",
        "tax_minpix"
    ],
    "tax_dep": [
        "tax_dep",
        "tax_mindep"
    ],
    "tax_saldo": [
        "tax_saldo",
        "tax_minsaldo",
        "tax_saldofactor",
        "tax_saldomax"
    ]
}

# ECONOMIA Campos que representam porcentagens
PERCENT_FIELDS = {
    "money_assistance_variance",
    "tax_rent",
    "tax_item",
    "tax_pix",
    "tax_dep",
    "tax_saldo",
    "tax_saldomax"
}

JSON_FILES = {
    "jobs": "modules/jobs/jobs.json",
    "items": "modules/items/items.json",
    "investments": "modules/investments/investments.json",
    "wordle": "modules/fun/wordle.json",
    "economy": "modules/economy/economy.json",
    "betting": "modules/betting/betting.json",
    "admins": "modules/admin/admins.json"
}
def check_perm_owner():
    user = session.get("user")
    return user is not None and user["id"] in AdminService.load_admins(int_converter=False).get("owner")

def check_perm_economy():
    user = session.get("user")
    return user is not None and user["id"] in AdminService.load_admins(int_converter=False).get("economy")

@app.route("/")
def home():
    user = session.get("user")
    return render_template("index.html", user=user)

@app.route("/conta")
def conta():
    user = session.get("user")
    if not user: return "Faça login primeiro", 401

    user_id = int(user["id"])
    user_money = EconomyService.get_user_money(user_id)
    user_bank = EconomyService.get_user_bank(user_id)
    user_job = JobsService.get_user_job(user_id)
    user_data = {
        "money": user_money,
        "bank": user_bank,
        "job": user_job
    }
    return render_template("conta.html", user=user, user_data=user_data)

@app.route("/admin")
def admin():
    if not check_perm_economy() and not check_perm_owner(): return "GET OUT", 403

    return render_template("admin.html")

@app.route("/economia")
def economia():
    if not check_perm_economy():
        return "GET OUT", 403

    with open(ECONOMY_PATH, "r", encoding="utf-8") as f:
        economy_data = json.load(f)

    return render_template("economia.html", economy=economy_data)

@app.route("/economia/salvar", methods=["POST"])
def salvar_economia():
    if not check_perm_economy():
        return jsonify({"error": "GET OUT"}), 403

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Dados inválidos!"}), 400

    group = data.get("group")
    values = data.get("values")

    if group not in ECONOMY_GROUPS or not isinstance(values, dict):
        return jsonify({"error": "Categoria inválida!"}), 400

    allowed_fields = ECONOMY_GROUPS[group]

    # Não permite modificar campos fora da categoria selecionada
    if set(values.keys()) != set(allowed_fields):
        return jsonify({"error": "Campos inválidos!"}), 400

    try:
        with open(ECONOMY_PATH, "r", encoding="utf-8") as f:
            economy_data = json.load(f)

        for key, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return jsonify({"error": f"Valor inválido: {key}"}), 400

            if key in PERCENT_FIELDS and not 0 <= value <= 1:
                return jsonify({
                    "error": f"{key}: o valor deve estar entre 0 e 1."
                }), 400

            if value < 0:
                return jsonify({
                    "error": f"{key}: não pode ser negativo."
                }), 400

        # Validação específica do imposto PSE
        if group == "tax_saldo":
            if values["tax_saldomax"] < values["tax_saldo"]:
                return jsonify({
                    "error": "A taxa máxima não pode ser menor que a taxa inicial."
                }), 400

        economy_data.update(values)

        temp_path = ECONOMY_PATH.with_suffix(".tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(economy_data, f, ensure_ascii=False, indent=4)

        temp_path.replace(ECONOMY_PATH)
        EconomyService.economy = EconomyService.load_economy()
        return jsonify({"success": True})

    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return jsonify({"error": "Não foi possível salvar a economia."}), 500
    
@app.route("/editor_json")
def editor_json():
    if not check_perm_owner(): return "GET OUT", 403

    return render_template("editor_json.html", files=JSON_FILES)

@app.route("/editor_json/json/<filename>", methods=["GET", "POST"])
def edit_json(filename):
    if not check_perm_owner():
        return jsonify({"error": "GET OUT"}), 403

    if filename not in JSON_FILES:
        return jsonify({"error": "Arquivo não encontrado!"}), 404

    file_path = ROOT_DIR / JSON_FILES[filename]

    if request.method == "GET":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return jsonify(data)

        except (OSError, json.JSONDecodeError):
            return jsonify({"error": "Não foi possível ler o JSON."}), 500

    if request.method == "POST":
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "JSON inválido!"}), 400

        try:
            content = json.dumps(data, ensure_ascii=False, indent=4)

            temp_path = file_path.with_suffix(".tmp") # fazer arquivo temporario

            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(content)

            temp_path.replace(file_path)

            EconomyService.economy = EconomyService.load_economy()
            FunService.wordle = FunService.load_wordle()
            InvestmentsService.market = InvestmentsService.load_market()
            ItemsService.items = ItemsService.load_items()
            JobsService.jobs = JobsService.load_jobs()
            return jsonify({"success": True})
        except (OSError, TypeError, ValueError):
            return jsonify({"error": "Erro ao salvar o arquivo."}), 500
    
@app.route("/login")
def login():
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    url = "https://discord.com/oauth2/authorize"

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
        "state": state
    }

    from urllib.parse import urlencode

    return redirect(url + "?" + urlencode(params))

@app.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state or state != session.pop("oauth_state", None):
        return "Login inválido!", 400

    # Pedir pelo access token
    response = requests.post(
        "https://discord.com/api/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    response.raise_for_status()
    token = response.json()["access_token"]

    # Buscar informacoes do usuario
    user_response = requests.get("https://discord.com/api/v10/users/@me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    user_response.raise_for_status()

    user = user_response.json()

    session.permanent = True
    session["user"] = {
        "id": user["id"],
        "username": user["username"],
        "avatar": user.get("avatar")
    }

    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
