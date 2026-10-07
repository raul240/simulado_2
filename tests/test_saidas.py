import tempfile
import unittest
from pathlib import Path

from almoxarifado.database import inicializar, conectar
from almoxarifado import service

class TestSaidas(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "teste.db"
        inicializar(self.db_path)
        self.admin = {"id": 1, "nome": "Admin", "username": "admin", "papel": "ADMIN"}
        self.operador = {"id": 2, "nome": "Operador", "username": "operador", "papel": "OPERADOR"}
        with conectar(self.db_path) as db:
            db.execute("UPDATE produtos SET quantidade=10 WHERE id=1")

    def tearDown(self):
        self.temp.cleanup()

    def _saldo(self):
        with conectar(self.db_path) as db:
            return db.execute("SELECT quantidade FROM produtos WHERE id=1").fetchone()[0]

    def test_cenario1_bloqueia_saida_maior_que_saldo(self):
        with self.assertRaisesRegex(ValueError, "estoque insuficiente"):
            self._registrar_saida(11)
        self.assertEqual(self._saldo(), 10)
        with conectar(self.db_path) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM saidas").fetchone()[0], 0)

    def test_cenario2_registra_saida_menor_ou_igual_ao_saldo(self):
        novo_saldo = self._registrar_saida(4)
        self.assertEqual(novo_saldo, 6)
        self.assertEqual(self._saldo(), 6)
        with conectar(self.db_path) as db:
            row = db.execute("SELECT quantidade, usuario_id, data_movimentacao FROM saidas").fetchone()
            self.assertEqual(row["quantidade"], 4)
            self.assertEqual(row["usuario_id"], 2)
            self.assertTrue(row["data_movimentacao"])

    def test_cenario3_saida_igual_ao_saldo_deixa_zero(self):
        novo_saldo = self._registrar_saida(10)
        self.assertEqual(novo_saldo, 0)
        self.assertEqual(self._saldo(), 0)

    def test_operador_nao_pode_excluir(self):
        with self.assertRaises(PermissionError):
            service.excluir_produto(self.operador, 1)

    def _registrar_saida(self, quantidade):
        # service usa o caminho padrão; trocar temporariamente o DB global para o arquivo de teste.
        import almoxarifado.database as database
        original = database.DB_PATH
        database.DB_PATH = self.db_path
        try:
            return service.registrar_saida(self.operador, 1, quantidade)
        finally:
            database.DB_PATH = original

if __name__ == "__main__":
    unittest.main()
