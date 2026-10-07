# Controle de Almoxarifado — versão aprimorada

Projeto baseado no repositório `raul240/pratica_prova`, com melhorias para a nova atividade.

## Requisitos
- Python 3.10 ou superior.
- Não exige instalação de bibliotecas externas para executar o sistema.
- `python-docx` só é necessário para recriar os documentos; os documentos já estão em `docs/`.

## Como executar no Windows
1. Extraia a pasta ZIP.
2. Abra a pasta `almoxarifado_melhorado` no VS Code.
3. Abra o terminal nessa pasta.
4. Execute `python main.py`.
5. Entre com uma conta de demonstração:
   - Administrador: `admin` / `Admin123!`
   - Operador: `operador` / `Operador123!`

As senhas são de demonstração para ambiente escolar. Altere-as antes de qualquer uso real.

## Funcionalidades
- Autenticação de usuários e papéis `OPERADOR` e `ADMIN`.
- Operador pode consultar, inserir e atualizar; não pode excluir.
- Administrador pode consultar, inserir, atualizar e excluir.
- Estoque atualizado automaticamente nas entradas e saídas.
- Saída maior que o saldo é bloqueada com mensagem clara.
- Movimentações guardam data/hora e usuário responsável.
- Listagem paginada de produtos, com filtro por nome e data de cadastro.
- Relatórios de valor total por categoria, saídas por período, maiores saídas e estoque mínimo/máximo.
- Testes automatizados para a regra de saída.
- Documentação do plano e resultados dos testes em `docs/`.

## Testar
Execute:
```bash
python -m unittest discover -s tests -v
```

Os arquivos em `docs/testes/` são evidências textuais dos cenários executados pelos testes automatizados. Para entregar evidência visual, também é possível tirar capturas do terminal após executar os testes.

## Arquitetura
- `almoxarifado/database.py`: conexão e criação do banco.
- `almoxarifado/security.py`: autenticação e autorização.
- `almoxarifado/service.py`: regras de negócio e persistência.
- `main.py`: interface de terminal.
- `tests/`: testes automatizados.
"# simulado_2" 
