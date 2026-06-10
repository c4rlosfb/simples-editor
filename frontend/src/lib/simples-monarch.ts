/**
 * Definição do tokenizer Monarch para a linguagem SIMPLES.
 *
 * Registra syntax highlighting das 27 palavras reservadas, operadores,
 * números, identificadores e strings no Monaco Editor.
 *
 * Referência: PRD §13.1
 */

import type { languages } from "monaco-editor";

export const SIMPLES_KEYWORDS = [
  // Estrutura do programa
  "programa",
  "inicio",
  "fim",

  // Tipos
  "inteiro",
  "flutuante",
  "vazio",

  // Controle de fluxo
  "se",
  "entao",
  "senao",
  "fimse",

  // Laços
  "enquanto",
  "fimenquanto",
  "para",
  "de",
  "ate",
  "passo",
  "faca",
  "fimpara",

  // Entrada / Saída
  "leia",
  "escreva",
  "escreval",

  // Operadores lógicos
  "e",
  "ou",
  "nao",

  // Operador aritmético (divisão inteira)
  "div",

  // Subprogramas (futuro, mas highlight desde já)
  "procedimento",
  "retorna",
] as const;

export const SIMPLES_OPERATORS = [
  "<-",   // atribuição
  "+",
  "-",
  "*",
  "div",  // divisão inteira
  ">",
  "<",
  "=",
  "<>",   // diferente
  ">=",
  "<=",
] as const;

export const simplesLanguage: languages.IMonarchLanguage = {
  ignoreCase: true,

  // Keywords — indexadas pelo Monarch para uso no tokenizer
  keywords: SIMPLES_KEYWORDS as unknown as string[],

  // Operadores — usados no mapeamento de símbolos
  operators: SIMPLES_OPERATORS as unknown as string[],

  // Símbolos que podem ser operadores
  symbols: /[+\-*/<>=!]+/,

  tokenizer: {
    root: [
      // Comentário de linha: // até o fim da linha
      [/\/\/.*$/, "comment"],

      // String entre aspas duplas: "texto"
      [/"[^"]*"/, "string"],

      // Números: flutuante (ex: 3.14) ou inteiro (ex: 42)
      [/\d+\.\d+/, "number.float"],
      [/\d+/, "number"],

      // Operador de atribuição <- (antes do símbolo genérico)
      [/<-/, "operator"],

      // Identificadores e keywords
      [
        /[a-zA-Z_]\w*/,
        {
          cases: {
            "@keywords": "keyword",
            "@default": "identifier",
          },
        },
      ],

      // Símbolos que podem ser operadores
      [
        /@symbols/,
        {
          cases: {
            "@operators": "operator",
            "@default": "",
          },
        },
      ],

      // Delimitadores
      [/[(),;]/, "delimiter"],

      // Espaços em branco
      [/\s+/, "white"],
    ],
  },
};
