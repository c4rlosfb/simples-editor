import type { languages } from 'monaco-editor'

export const simplesLanguage: languages.IMonarchLanguage = {
  defaultToken: 'invalid',

  keywords: [
    'programa', 'inicio', 'fim',
    'inteiro', 'flutuante', 'vazio',
    'se', 'entao', 'senao', 'fimse',
    'enquanto', 'fimenquanto',
    'para', 'de', 'ate', 'passo', 'faca', 'fimpara',
    'leia', 'escreva', 'escreval',
    'e', 'ou', 'nao',
    'div',
    'procedimento', 'retorna',
  ],

  typeKeywords: ['inteiro', 'flutuante', 'vazio'],

  operators: [
    ':=', '=', '<>', '<', '>', '<=', '>=',
    '+', '-', '*', '/', 'div',
    'e', 'ou', 'nao',
  ],

  symbols: /[=<>+\-*/:=]+/,
  escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,

  tokenizer: {
    root: [
      // Comments: { ... }
      [/[\{][^}]*[\}]/, 'comment'],

      // Strings: "..."
      [/"([^"\\]|\\.)*"/, 'string'],

      // Numbers (integers and floats)
      [/\d+\.\d*([eE][+-]?\d+)?/, 'number.float'],
      [/\d+/, 'number'],

      // Identifiers and keywords
      [
        /[a-zA-Z_áéíóúàèìòùâêîôûãõçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ][a-zA-Z0-9_áéíóúàèìòùâêîôûãõçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÃÕÇ]*/,
        {
          cases: {
            '@keywords': 'keyword',
            '@typeKeywords': 'type',
            '@default': 'identifier',
          },
        },
      ],

      // Whitespace
      { include: '@whitespace' },

      // Delimiters
      [/[(),;:]/, 'delimiter'],

      // Operators
      [/@symbols/, { cases: { '@operators': 'operator', '@default': '' } }],
    ],

    whitespace: [
      [/[ \t\r\n]+/, 'white'],
    ],
  },
}

export const simplesLanguageConfig: languages.LanguageConfiguration = {
  comments: {
    blockComment: ['{', '}'],
  },
  brackets: [
    ['(', ')'],
  ],
  autoClosingPairs: [
    { open: '"', close: '"', notIn: ['string'] },
    { open: '(', close: ')' },
    { open: '{', close: '}' },
  ],
  surroundingPairs: [
    { open: '"', close: '"' },
    { open: '(', close: ')' },
    { open: '{', close: '}' },
  ],
}
