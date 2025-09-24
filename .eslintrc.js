export default {
  env: {
    browser: true,
    es2022: true,
    node: true,
  },

  extends: [
    'eslint:recommended',
  ],

  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
  },

  globals: {
    // Global variables available in the frontend
    GALLERY_VIDEOS: 'readonly',
    API_BASE_URL: 'readonly',
    __DEV__: 'readonly',
    __PROD__: 'readonly',
  },

  rules: {
    // Code style
    'indent': ['error', 2],
    'quotes': ['error', 'single', { allowTemplateLiterals: true }],
    'semi': ['error', 'always'],
    'comma-dangle': ['error', 'always-multiline'],

    // Best practices
    'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    'no-console': 'warn',
    'no-debugger': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',

    // ES6+ features
    'arrow-spacing': 'error',
    'object-shorthand': 'error',
    'prefer-template': 'error',
    'template-curly-spacing': 'error',

    // Async/await
    'no-async-promise-executor': 'error',
    'require-await': 'warn',

    // Import/export
    'no-duplicate-imports': 'error',

    // Accessibility (basic)
    'no-script-url': 'error',

    // Performance
    'no-loop-func': 'error',
  },

  overrides: [
    {
      files: ['vite.config.js', 'postcss.config.js'],
      env: {
        node: true,
        browser: false,
      },
    },
  ],
};