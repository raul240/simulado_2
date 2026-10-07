Evidências dos testes automatizados

Os arquivos cenario1.txt, cenario2.txt e cenario3.txt registram o cenário, os dados usados, o resultado esperado e a conclusão dos testes automatizados. Eles foram gerados para documentar os testes do projeto.

Para gerar evidência visual adicional, abra um terminal na raiz do projeto e execute:
python -m unittest discover -s tests -v
Faça uma captura de tela do resultado no terminal e salve como docs/testes/cenario1.png, docs/testes/cenario2.png e docs/testes/cenario3.png. Não renomeie uma captura de outro cenário para fingir que ela foi executada.
