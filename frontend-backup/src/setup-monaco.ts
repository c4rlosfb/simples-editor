import * as monaco from 'monaco-editor'
import { simplesLanguage, simplesLanguageConfig } from './simples-language'
import { simplesDarkTheme } from './simples-theme'

// Register the SIMPLES language
monaco.languages.register({ id: 'simples' })

// Set the monarch tokenizer
monaco.languages.setMonarchTokensProvider('simples', simplesLanguage)

// Set language configuration (comments, brackets, auto-closing)
monaco.languages.setLanguageConfiguration('simples', simplesLanguageConfig)

// Define the dark theme
monaco.editor.defineTheme('simples-dark', simplesDarkTheme)
