export default {
  extends: [
    'stylelint-config-standard',
  ],

  rules: {
    // Allow CSS custom properties (CSS variables)
    'custom-property-empty-line-before': null,
    'declaration-empty-line-before': null,

    // Allow modern CSS features
    'at-rule-no-unknown': [
      true,
      {
        ignoreAtRules: [
          'tailwind',
          'apply',
          'variants',
          'responsive',
          'screen',
          'layer',
        ],
      },
    ],

    // Allow nesting (handled by PostCSS)
    'rule-empty-line-before': [
      'always-multi-line',
      {
        except: ['first-nested'],
        ignore: ['after-comment'],
      },
    ],

    // Be more lenient with selector patterns
    'selector-class-pattern': null,
    'selector-id-pattern': null,

    // Allow vendor prefixes (handled by autoprefixer)
    'property-no-vendor-prefix': null,
    'value-no-vendor-prefix': null,

    // Terminal/ASCII art specific allowances
    'string-quotes': 'single',
    'font-family-no-missing-generic-family-keyword': [
      true,
      {
        ignoreFontFamilies: ['JetBrains Mono', 'Orbitron'],
      },
    ],

    // Color format consistency
    'color-hex-length': 'short',
    'color-hex-case': 'lower',

    // Units and values
    'length-zero-no-unit': true,
    'number-max-precision': 3,

    // Performance
    'no-duplicate-selectors': true,
    'declaration-block-no-redundant-longhand-properties': true,
  },

  ignoreFiles: [
    'node_modules/**/*',
    'dist/**/*',
    '*.min.css',
  ],
};