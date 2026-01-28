/**
 * WLanguage (WinDev/WebDev) syntax configuration for Monaco Editor
 */

import type * as Monaco from "monaco-editor";

export const wlanguageConfig: Monaco.languages.LanguageConfiguration = {
  comments: {
    lineComment: "//",
    blockComment: ["/*", "*/"],
  },
  brackets: [
    ["{", "}"],
    ["[", "]"],
    ["(", ")"],
  ],
  autoClosingPairs: [
    { open: "{", close: "}" },
    { open: "[", close: "]" },
    { open: "(", close: ")" },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
  surroundingPairs: [
    { open: "{", close: "}" },
    { open: "[", close: "]" },
    { open: "(", close: ")" },
    { open: '"', close: '"' },
    { open: "'", close: "'" },
  ],
  folding: {
    markers: {
      start: /^\s*(PROCEDURE|IF|FOR|WHILE|SWITCH|LOOP)\b/i,
      end: /^\s*END\b/i,
    },
  },
};

export const wlanguageTokensProvider: Monaco.languages.IMonarchLanguage = {
  defaultToken: "",
  ignoreCase: true,

  keywords: [
    "PROCEDURE",
    "END",
    "IF",
    "THEN",
    "ELSE",
    "ELSIF",
    "FOR",
    "TO",
    "STEP",
    "WHILE",
    "SWITCH",
    "CASE",
    "DEFAULT",
    "OTHER CASE",
    "RETURN",
    "RESULT",
    "LOCAL",
    "GLOBAL",
    "CONSTANT",
    "TRUE",
    "FALSE",
    "NULL",
    "Null",
    "BREAK",
    "CONTINUE",
    "LOOP",
    "IN",
    "OF",
    "NOT",
    "AND",
    "OR",
    "DO",
    "EACH",
    "INTERNAL",
    "PRIVATE",
    "PUBLIC",
    "PROTECTED",
    "STATIC",
    "NEW",
  ],

  typeKeywords: [
    "string",
    "chaîne",
    "int",
    "entier",
    "real",
    "réel",
    "boolean",
    "booléen",
    "date",
    "datetime",
    "variant",
    "array",
    "buffer",
    "numeric",
    "numérique",
    "currency",
    "monétaire",
    "duration",
    "durée",
  ],

  operators: [
    "=",
    ">",
    "<",
    "!",
    "~",
    "?",
    ":",
    "==",
    "<=",
    ">=",
    "!=",
    "<>",
    "&&",
    "||",
    "++",
    "--",
    "+",
    "-",
    "*",
    "/",
    "&",
    "|",
    "^",
    "%",
    "<<",
    ">>",
    "+=",
    "-=",
    "*=",
    "/=",
    "..",
  ],

  symbols: /[=><!~?:&|+\-*\/\^%]+/,

  escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,

  tokenizer: {
    root: [
      // Identifiers and keywords
      [
        /[a-z_$][\w$]*/,
        {
          cases: {
            "@typeKeywords": "type.identifier",
            "@keywords": "keyword",
            "@default": "identifier",
          },
        },
      ],

      // Whitespace
      { include: "@whitespace" },

      // Delimiters and operators
      [/[{}()\[\]]/, "@brackets"],
      [/[<>](?!@symbols)/, "@brackets"],
      [
        /@symbols/,
        {
          cases: {
            "@operators": "operator",
            "@default": "",
          },
        },
      ],

      // Numbers
      [/\d*\.\d+([eE][\-+]?\d+)?/, "number.float"],
      [/0[xX][0-9a-fA-F]+/, "number.hex"],
      [/\d+/, "number"],

      // Delimiter: after number because of .\d floats
      [/[;,.]/, "delimiter"],

      // Strings
      [/"([^"\\]|\\.)*$/, "string.invalid"], // non-terminated string
      [/"/, { token: "string.quote", bracket: "@open", next: "@string" }],
      [/'([^'\\]|\\.)*$/, "string.invalid"], // non-terminated string
      [/'/, { token: "string.quote", bracket: "@open", next: "@stringSingle" }],
    ],

    comment: [
      [/[^\/*]+/, "comment"],
      [/\/\*/, "comment", "@push"],
      ["\\*/", "comment", "@pop"],
      [/[\/*]/, "comment"],
    ],

    string: [
      [/[^\\"]+/, "string"],
      [/@escapes/, "string.escape"],
      [/\\./, "string.escape.invalid"],
      [/"/, { token: "string.quote", bracket: "@close", next: "@pop" }],
    ],

    stringSingle: [
      [/[^\\']+/, "string"],
      [/@escapes/, "string.escape"],
      [/\\./, "string.escape.invalid"],
      [/'/, { token: "string.quote", bracket: "@close", next: "@pop" }],
    ],

    whitespace: [
      [/[ \t\r\n]+/, "white"],
      [/\/\*/, "comment", "@comment"],
      [/\/\/.*$/, "comment"],
    ],
  },
};

/**
 * Register WLanguage with Monaco Editor
 */
export function registerWLanguage(monaco: typeof Monaco): void {
  // Check if already registered
  const languages = monaco.languages.getLanguages();
  if (languages.some((lang) => lang.id === "wlanguage")) {
    return;
  }

  monaco.languages.register({
    id: "wlanguage",
    extensions: [".wwh", ".wdg", ".wdc", ".wde", ".wdw"],
    aliases: ["WLanguage", "windev", "webdev"],
  });

  monaco.languages.setMonarchTokensProvider("wlanguage", wlanguageTokensProvider);
  monaco.languages.setLanguageConfiguration("wlanguage", wlanguageConfig);
}
