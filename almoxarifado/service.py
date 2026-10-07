from datetime import datetime
from .database import conectar
from .security import exigir_papel

ESTOQUE_MAXIMO = 100

def _auditar(db, usuario_id, acao, entidade, entidade_id=None, detalhes=""):
    db.execute(
        "INSERT INTO auditoria (usuario_id, acao, entidade, entidade_id, data_hora, detalhes) VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, acao, entidade, entidade_id, datetime.now().astimezone().isoformat(timespec="seconds"), detalhes)
    )

def listar_produtos(usuario, pagina=1, por_pagina=5, nome=None, data=None):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    if pagina < 1 or por_pagina < 1:
        raise ValueError("Página e quantidade por página devem ser positivas.")
    filtros, parametros = [], []
    if nome:
        filtros.append("nome LIKE ?")
        parametros.append(f"%{nome.strip()}%")
    if data:
        datetime.strptime(data, "%Y-%m-%d")
        filtros.append("date(criado_em) = date(?)")
        parametros.append(data)
    where = (" WHERE " + " AND ".join(filtros)) if filtros else ""
    with conectar() as db:
        total = db.execute("SELECT COUNT(*) FROM produtos" + where, parametros).fetchone()[0]
        itens = db.execute(
            "SELECT id, nome, categoria, unidade_medida, quantidade, valor_unitario, criado_em "
            "FROM produtos" + where + " ORDER BY nome LIMIT ? OFFSET ?",
            [*parametros, por_pagina, (pagina - 1) * por_pagina]
        ).fetchall()
    return {"itens": [dict(x) for x in itens], "pagina": pagina, "por_pagina": por_pagina,
            "total": total, "total_paginas": (total + por_pagina - 1) // por_pagina}

def cadastrar_produto(usuario, nome, categoria, unidade_medida, quantidade, valor_unitario):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    nome, categoria, unidade_medida = nome.strip(), categoria.strip(), unidade_medida.strip()
    if not nome or not categoria or not unidade_medida:
        raise ValueError("Nome, categoria e unidade de medida são obrigatórios.")
    if not isinstance(quantidade, int) or not 0 <= quantidade <= ESTOQUE_MAXIMO:
        raise ValueError("A quantidade deve estar entre 0 e 100.")
    if valor_unitario <= 0:
        raise ValueError("O valor unitário deve ser maior que zero.")
    with conectar() as db:
        cur = db.execute(
            "INSERT INTO produtos (nome, categoria, unidade_medida, quantidade, valor_unitario) VALUES (?, ?, ?, ?, ?)",
            (nome, categoria, unidade_medida, quantidade, valor_unitario)
        )
        produto_id = cur.lastrowid
        _auditar(db, usuario["id"], "INSERIR", "produto", produto_id, nome)
        return produto_id

def atualizar_produto(usuario, produto_id, nome=None, categoria=None, unidade_medida=None, valor_unitario=None):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    with conectar() as db:
        produto = db.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            raise ValueError("Produto não encontrado.")
        novos = {
            "nome": (nome.strip() if nome is not None else produto["nome"]),
            "categoria": (categoria.strip() if categoria is not None else produto["categoria"]),
            "unidade_medida": (unidade_medida.strip() if unidade_medida is not None else produto["unidade_medida"]),
            "valor_unitario": (valor_unitario if valor_unitario is not None else produto["valor_unitario"]),
        }
        if not novos["nome"] or not novos["categoria"] or not novos["unidade_medida"]:
            raise ValueError("Nome, categoria e unidade de medida são obrigatórios.")
        if novos["valor_unitario"] <= 0:
            raise ValueError("O valor unitário deve ser maior que zero.")
        db.execute("UPDATE produtos SET nome=?, categoria=?, unidade_medida=?, valor_unitario=? WHERE id=?",
                   (novos["nome"], novos["categoria"], novos["unidade_medida"], novos["valor_unitario"], produto_id))
        _auditar(db, usuario["id"], "ATUALIZAR", "produto", produto_id, novos["nome"])

def excluir_produto(usuario, produto_id):
    exigir_papel(usuario, "ADMIN")
    with conectar() as db:
        row = db.execute("SELECT nome FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not row:
            raise ValueError("Produto não encontrado.")
        try:
            db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        except Exception as exc:
            raise ValueError("Não é possível excluir: existem movimentações vinculadas a este produto.") from exc
        _auditar(db, usuario["id"], "EXCLUIR", "produto", produto_id, row["nome"])

def registrar_entrada(usuario, produto_id, quantidade):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    if not isinstance(quantidade, int) or quantidade <= 0:
        raise ValueError("A quantidade de entrada deve ser um inteiro positivo.")
    with conectar() as db:
        produto = db.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            raise ValueError("Produto não encontrado.")
        novo_saldo = produto["quantidade"] + quantidade
        if novo_saldo > ESTOQUE_MAXIMO:
            raise ValueError(f"Entrada não permitida: limite de estoque é {ESTOQUE_MAXIMO}. Atual: {produto['quantidade']}. Solicitado: {quantidade}.")
        agora = datetime.now().astimezone().isoformat(timespec="seconds")
        db.execute("INSERT INTO entradas (produto_id, quantidade, data_movimentacao, usuario_id) VALUES (?, ?, ?, ?)",
                   (produto_id, quantidade, agora, usuario["id"]))
        db.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (novo_saldo, produto_id))
        _auditar(db, usuario["id"], "ENTRADA", "produto", produto_id, f"quantidade={quantidade}; saldo={novo_saldo}")
    return novo_saldo

def registrar_saida(usuario, produto_id, quantidade):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    if not isinstance(quantidade, int) or quantidade <= 0:
        raise ValueError("A quantidade de saída deve ser um inteiro positivo.")
    with conectar() as db:
        produto = db.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if not produto:
            raise ValueError("Produto não encontrado.")
        saldo = produto["quantidade"]
        if quantidade > saldo:
            raise ValueError(f"Saída não permitida: estoque insuficiente. Disponível: {saldo}. Solicitado: {quantidade}.")
        agora = datetime.now().astimezone().isoformat(timespec="seconds")
        db.execute("INSERT INTO saidas (produto_id, quantidade, data_movimentacao, usuario_id) VALUES (?, ?, ?, ?)",
                   (produto_id, quantidade, agora, usuario["id"]))
        novo_saldo = saldo - quantidade
        db.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (novo_saldo, produto_id))
        _auditar(db, usuario["id"], "SAIDA", "produto", produto_id, f"quantidade={quantidade}; saldo={novo_saldo}")
    return novo_saldo

def total_por_categoria(usuario):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    with conectar() as db:
        return [dict(x) for x in db.execute(
            "SELECT categoria, SUM(valor_total) AS valor_total FROM vw_estoque GROUP BY categoria ORDER BY categoria"
        ).fetchall()]

def listar_saidas(usuario, data_inicial=None, data_final=None):
    exigir_papel(usuario, "OPERADOR", "ADMIN")
    if data_inicial:
        datetime.strptime(data_inicial, "%Y-%m-%d")
    if data_final:
        datetime.strptime(data_final, "%Y-%m-%d")
    sql = """SELECT s.id, p.nome, s.quantidade, s.data_movimentacao, u.username AS responsavel
             FROM saidas s JOIN produtos p ON p.id=s.produto_id JOIN usuarios u ON u.id=s.usuario_id"""
    filtros, params = [], []
    if data_inicial:
        filtros.append("date(s.data_movimentacao) >= date(?)"); params.append(data_inicial)
    if data_final:
        filtros.append("date(s.data_movimentacao) <= date(?)"); params.append(data_final)
    if filtros:
        sql += " WHERE " + " AND ".join(filtros)
    sql += " ORDER BY s.data_movimentacao DESC"
    with conectar() as db:
        return [dict(x) for x in db.execute(sql, params).fetchall()]

def auditoria_usuario(usuario, limite=50):
    exigir_papel(usuario, "ADMIN")
    with conectar() as db:
        return [dict(x) for x in db.execute(
            """SELECT a.data_hora, u.username, a.acao, a.entidade, a.entidade_id, a.detalhes
               FROM auditoria a JOIN usuarios u ON u.id=a.usuario_id ORDER BY a.id DESC LIMIT ?""",
            (limite,)
        ).fetchall()]
