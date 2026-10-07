import hashlib
import hmac
import os
from .database import conectar

ITERATIONS = 240_000

def hash_senha(senha: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, ITERATIONS)
    return f"{salt.hex()}:{digest.hex()}"

def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        salt_hex, digest_hex = senha_hash.split(":", 1)
        atual = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), bytes.fromhex(salt_hex), ITERATIONS)
        return hmac.compare_digest(atual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def autenticar(username: str, senha: str):
    with conectar() as db:
        row = db.execute(
            "SELECT id, nome, username, senha_hash, papel, ativo FROM usuarios WHERE username = ?",
            (username.strip(),)
        ).fetchone()
    if not row or not row["ativo"] or not verificar_senha(senha, row["senha_hash"]):
        return None
    return {"id": row["id"], "nome": row["nome"], "username": row["username"], "papel": row["papel"]}

def exigir_papel(usuario, *papeis):
    if not usuario or usuario["papel"] not in papeis:
        raise PermissionError("Acesso negado: seu perfil não possui permissão para esta operação.")
