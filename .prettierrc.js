export default {
  // Basic formatting
  semi: true,
  singleQuote: true,
  quoteProps: 'as-needed',
  trailingComma: 'all',

  // Indentation
  tabWidth: 2,
  useTabs: false,

  // Line length
  printWidth: 80,

  // Bracket spacing
  bracketSpacing: true,
  bracketSameLine: false,

  // Arrow functions
  arrowParens: 'avoid',

  // HTML/CSS specific
  htmlWhitespaceSensitivity: 'css',

  // File type overrides
  overrides: [
    {
      files: '*.html',
      options: {
        printWidth: 120,
      },
    },
    {
      files: '*.css',
      options: {
        printWidth: 100,
      },
    },
    {
      files: '*.md',
      options: {
        printWidth: 100,
        proseWrap: 'preserve',
      },
    },
  ],
};