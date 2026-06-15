"""Fix keywords in generate_demo.py for PR #58."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("generate_demo.py", encoding="utf-8") as f:
    content = f.read()

# Scene 3 - fix code_lines
old = (
    '        code_lines = [\n'
    '            "programa exemplo;",\n'
    '            "declare",\n'
    '            "    x: inteiro;",\n'
    '            "    y: inteiro;",\n'
    '            "inicio",\n'
    '            \'    escreva("Digite um numero: ");\',\n'
    '            "    leia(x);",\n'
    '            "    y := x * 2;",\n'
    '            \'    escreva("Dobro: ", y);\',\n'
    '            "fimprog.",\n'
    '        ]'
)
new = (
    '        code_lines = [\n'
    '            "programa exemplo;",\n'
    '            "    x: inteiro;",\n'
    '            "    y: inteiro;",\n'
    '            "inicio",\n'
    '            \'    escreva("Digite um numero: ");\',\n'
    '            "    leia(x);",\n'
    '            "    y <- x * 2;",\n'
    '            \'    escreva("Dobro: ", y);\',\n'
    '            "fim.",\n'
    '        ]'
)
assert old in content, "SCENE3 not found!"
content = content.replace(old, new)
print("Scene 3: OK")

# Scene 4 keywords
old = '"27 palavras reservadas", "programa, declare, inicio, fimprog,\ninteiro, real, caracter, leia, escreva,\nse, entao, senao, fimse, enquanto,\nfimenquanto, repita, ate, para, faca,\ne, ou, nao, verdadeiro, falso, inicio_partes,\ndeclare_partes, registros"'
new = '"23 palavras reservadas", "programa, inicio, fim,\ninteiro, flutuante, vazio, leia, escreva,\nse, entao, senao, fimse, enquanto,\nfimenquanto, ate, para, faca,\ne, ou, nao, verdadeiro, falso, inicio_partes,\ndeclare_partes, registros"'
assert old in content, "KEYWORDS not found!"
content = content.replace(old, new)
print("Scene 4 keywords: OK")

# Scene 4 types
old = '"Tipos de Dados", "inteiro, real, caracter\nSuporta vetores e registros"'
new = '"Tipos de Dados", "inteiro, flutuante, vazio\nSuporta vetores e registros"'
assert old in content, "TYPES not found!"
content = content.replace(old, new)
print("Scene 4 types: OK")

# Scene 4 flow
old = '"Controle de Fluxo", "se...entao...senao\nenquanto...faca\nrepita...ate\npara...faca"'
new = '"Controle de Fluxo", "se...entao...senao\nenquanto...faca\nate\npara...faca"'
assert old in content, "FLOW not found!"
content = content.replace(old, new)
print("Scene 4 flow: OK")

# Scene 6
old = (
    '        code = [\n'
    '            "programa soma;",\n'
    '            "declare",\n'
    '            "    a, b, soma: inteiro;",\n'
    '            "inicio",\n'
    '            \'    escreva("Valor de a: ");\',\n'
    '            "    leia(a);",\n'
    '            \'    escreva("Valor de b: ");\',\n'
    '            "    leia(b);",\n'
    '            "    soma := a + b;",\n'
    '            \'    escreva("Soma: ", soma);\',\n'
    '            "fimprog.",\n'
    '        ]'
)
new = (
    '        code = [\n'
    '            "programa soma;",\n'
    '            "    a, b, soma: inteiro;",\n'
    '            "inicio",\n'
    '            \'    escreva("Valor de a: ");\',\n'
    '            "    leia(a);",\n'
    '            \'    escreva("Valor de b: ");\',\n'
    '            "    leia(b);",\n'
    '            "    soma <- a + b;",\n'
    '            \'    escreva("Soma: ", soma);\',\n'
    '            "fim.",\n'
    '        ]'
)
assert old in content, "SCENE6 not found!"
content = content.replace(old, new)
print("Scene 6: OK")

with open("generate_demo.py", "w", encoding="utf-8") as f:
    f.write(content)
print("ALL FIXES APPLIED SUCCESSFULLY!")
