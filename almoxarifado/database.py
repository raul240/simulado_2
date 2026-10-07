import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "almoxarifado.db"
SQL_PATH = ROOT / "banco.sql"

def conectar(db_path=None):
    caminho = str(db_path or DB_PATH)
    db = sqlite3.connect(caminho)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.execute("PRAGMA busy_timeout = 5000")
    return db

def inicializar(db_path=None):
    with conectar(db_path) as db:
        db.executescript(SQL_PATH.read_text(encoding="utf-8"))
        total = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        if total == 0:
            from .security import hash_senha
            db.execute("INSERT INTO usuarios (nome, username, senha_hash, papel) VALUES (?, ?, ?, ?)",
                       ("Administrador do Sistema", "admin", hash_senha("Admin123!"), "ADMIN"))
            db.execute("INSERT INTO usuarios (nome, username, senha_hash, papel) VALUES (?, ?, ?, ?)",
                       ("Operador do Almoxarifado", "operador", hash_senha("Operador123!"), "OPERADOR"))
        total_produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        if total_produtos == 0:
            db.executemany(
                "INSERT INTO produtos (nome, categoria, unidade_medida, quantidade, valor_unitario) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Detergente", "Limpeza geral", "litro", 20, 8.50),
                    ("Desinfetante", "Higienização", "litro", 100, 12.00),
                    ("Saco de lixo", "Descartáveis", "pacote", 0, 15.90),
                ],
            )
