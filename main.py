from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from database.banco_de_dados import init_db
from database.session_manager import (
    generate_session_id, hash_session_id, save_session, get_session,
    delete_session, get_session_count, clean_expired_sessions,
    is_ip_blocked, increment_failed_attempts
)
from config import SESSION_EXPIRATION_MINUTES, MAX_SESSIONS_BEFORE_REUSE

app = Flask(__name__)

# 🔹 Inicializa o banco de dados
init_db()

# 🔹 Rota para gerar uma nova sessão
@app.route("/nova_sessao", methods=["POST"])
def nova_sessao():
    ip_address = request.remote_addr

    # Verifica se o IP está bloqueado
    if is_ip_blocked(ip_address):
        return jsonify({"erro": "IP bloqueado devido a muitas tentativas falhas"}), 403

    # Verifica se o limite de sessões foi atingido
    if get_session_count() >= MAX_SESSIONS_BEFORE_REUSE:
        return jsonify({"erro": "Limite máximo de sessões atingido"}), 429

    # Gera uma nova sessão
    session_id = generate_session_id()
    hashed_id = hash_session_id(session_id)
    expiration_time = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRATION_MINUTES)

    save_session(session_id, None, expiration_time, ip_address=ip_address)

    return jsonify({"session_id": session_id})

# 🔹 Rota para validar a senha digitada pelo usuário
@app.route("/validar_senha", methods=["POST"])
def validar_senha():
    data = request.json
    session_id = data.get("session_id")
    senha_digitada = data.get("senha")

    if not session_id or not senha_digitada:
        return jsonify({"erro": "Sessão ou senha ausente"}), 400

    hashed_id = hash_session_id(session_id)
    session = get_session(hashed_id)

    if not session:
        return jsonify({"erro": "Sessão inválida ou expirada"}), 403

    # Aqui você adicionaria a lógica de validação da senha
    senha_correta = "1234"  # Exemplo (isso deve vir do banco)
    
    if senha_digitada == senha_correta:
        delete_session(hashed_id)
        return jsonify({"mensagem": "Senha correta! Acesso permitido."})
    
    # Incrementa tentativas de falha e bloqueia IP se necessário
    increment_failed_attempts(hashed_id, session["ip_address"])

    return jsonify({"erro": "Senha incorreta"}), 401

# 🔹 Rota para limpar sessões expiradas
@app.route("/limpar_sessoes", methods=["POST"])
def limpar_sessoes():
    clean_expired_sessions()
    return jsonify({"mensagem": "Sessões expiradas removidas"}), 200

# 🔹 Inicia o servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
