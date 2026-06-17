import type { languages } from "monaco-editor";
export const SIMPLES_KEYWORDS = ["programa","inicio","fim","inteiro","flutuante","vazio","se","entao","senao","fimse","enquanto","fimenquanto","para","de","ate","passo","faca","fimpara","leia","escreva","escreval","e","ou","nao","div","procedimento","retorna"] as const;
export const SIMPLES_OPERATORS = ["<-","+","-","*","/",">","<","=","<>",">=","<="] as const;
export const simplesLanguage: languages.IMonarchLanguage = {
  ignoreCase: true, keywords: SIMPLES_KEYWORDS as unknown as string[], operators: SIMPLES_OPERATORS as unknown as string[], symbols: /[+\-*/<>=!]+/,
  tokenizer: { root: [
    [/\/\/.*$/, "comment"], [/"[^"]*"/, "string"], [/\d+\.\d+/, "number.float"], [/\d+/, "number"], [/<-/, "operator"],
    [/[a-zA-Z_]\w*/, { cases: { "@keywords": "keyword", "@default": "identifier" } }],
    [/@symbols/, { cases: { "@operators": "operator", "@default": "" } }], [/[(),;]/, "delimiter"], [/\s+/, "white"],
  ]},
};
