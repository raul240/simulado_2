from getpass import getpass
from almoxarifado.database import inicializar
from almoxarifado.security import autenticar, exigir_papel
from almoxarifado import service

def ler_int(mensagem, minimo=1):
    while True:
        try:
            n = int(input(mensagem))
            if n < minimo:
                print(f"Informe um número maior ou igual a {minimo}.")
                continue
            return n
        except ValueError:
            print("Digite um número inteiro válido.")

def executar():
    inicializar()
    print("=== CONTROLE DE ALMOXARIFADO ===")
    usuario = None
    for _ in range(3):
        login = input("Usuário: ").strip()
        senha = getpass("Senha: ")
        usuario = autenticar(login, senha)
        if usuario:
            break
        print("Usuário ou senha inválidos.")
    if not usuario:
        print("Número máximo de tentativas atingido.")
        return

    print(f"Bem-vindo(a), {usuario['nome']} — perfil: {usuario['papel']}")
    while True:
        print("""
1 - Listar produtos (paginado)
2 - Valor total por categoria
3 - Cadastrar produto
4 - Atualizar produto
5 - Registrar entrada
6 - Registrar saída
7 - Listar saídas por período
8 - Excluir produto (ADMIN)
9 - Consultar auditoria (ADMIN)
0 - Sair""")
        opcao = input("Opção: ").strip()
        try:
            if opcao == "1":
                nome = input("Filtro por nome (Enter para ignorar): ").strip() or None
                data = input("Data de cadastro AAAA-MM-DD (Enter para ignorar): ").strip() or None
                pagina = ler_int("Página: ", 1)
                resultado = service.listar_produtos(usuario, pagina=pagina, por_pagina=5, nome=nome, data=data)
                print(f"Página {resultado['pagina']}/{resultado['total_paginas']} — total: {resultado['total']}")
                for p in resultado["itens"]:
                    print(f"#{p['id']} {p['nome']} | {p['categoria']} | estoque={p['quantidade']} | R$ {p['valor_unitario']:.2f}")
            elif opcao == "2":
                for item in service.total_por_categoria(usuario):
                    print(f"{item['categoria']}: R$ {item['valor_total']:.2f}")
            elif opcao == "3":
                nome = input("Nome: ")
                categoria = input("Categoria: ")
                unidade = input("Unidade de medida: ")
                quantidade = ler_int("Quantidade inicial (1 a 100; para 0 digite 0): ", 0)
                valor = float(input("Valor unitário: R$ ").replace(",", "."))
                pid = service.cadastrar_produto(usuario, nome, categoria, unidade, quantidade, valor)
                print(f"Produto cadastrado com ID {pid}.")
            elif opcao == "4":
                pid = ler_int("ID do produto: ")
                nome = input("Novo nome (Enter mantém): ") or None
                categoria = input("Nova categoria (Enter mantém): ") or None
                unidade = input("Nova unidade (Enter mantém): ") or None
                valor_txt = input("Novo valor (Enter mantém): ").strip()
                valor = float(valor_txt.replace(",", ".")) if valor_txt else None
                service.atualizar_produto(usuario, pid, nome, categoria, unidade, valor)
                print("Produto atualizado.")
            elif opcao == "5":
                pid = ler_int("ID do produto: ")
                qtd = ler_int("Quantidade de entrada: ")
                print(f"Entrada registrada. Novo saldo: {service.registrar_entrada(usuario, pid, qtd)}")
            elif opcao == "6":
                pid = ler_int("ID do produto: ")
                qtd = ler_int("Quantidade de saída: ")
                print(f"Saída registrada. Novo saldo: {service.registrar_saida(usuario, pid, qtd)}")
            elif opcao == "7":
                inicio = input("Data inicial AAAA-MM-DD (Enter ignora): ").strip() or None
                fim = input("Data final AAAA-MM-DD (Enter ignora): ").strip() or None
                for s in service.listar_saidas(usuario, inicio, fim):
                    print(f"{s['data_movimentacao']} | {s['nome']} | qtd={s['quantidade']} | responsável={s['responsavel']}")
            elif opcao == "8":
                exigir_papel(usuario, "ADMIN")
                pid = ler_int("ID do produto a excluir: ")
                service.excluir_produto(usuario, pid)
                print("Produto excluído.")
            elif opcao == "9":
                for a in service.auditoria_usuario(usuario):
                    print(f"{a['data_hora']} | {a['username']} | {a['acao']} | {a['entidade']}#{a['entidade_id']} | {a['detalhes']}")
            elif opcao == "0":
                print("Sistema encerrado.")
                break
            else:
                print("Opção inválida.")
        except (ValueError, PermissionError) as exc:
            print(f"Erro: {exc}")

if __name__ == "__main__":
    executar()
