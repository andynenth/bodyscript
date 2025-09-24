export default {
  plugins: {
    // Import support for @import statements
    'postcss-import': {
      // Allow imports from node_modules and relative paths
      path: ['node_modules', 'frontend/css'],
    },

    // CSS nesting support (modern CSS nesting syntax)
    'postcss-nesting': {},

    // Modern CSS features with browser compatibility
    'postcss-preset-env': {
      // Use stage 2 features (widely supported)
      stage: 2,
      features: {
        // Enable specific features
        'custom-properties': true,
        'custom-media-queries': true,
        'custom-selectors': true,
        'nesting-rules': true,
      },
      // Autoprefixer is included in preset-env
      autoprefixer: {
        grid: 'autoplace',
        flexbox: 'no-2009',
      },
    },

    // Minify CSS in production
    ...(process.env.NODE_ENV === 'production' ? {
      'cssnano': {
        preset: [
          'default',
          {
            // Preserve CSS custom properties
            reduceIdents: false,
            zindex: false,
            mergeIdents: false,
            discardUnused: false,
            // Optimize for readability
            colormin: false,
            minifyFontValues: false,
          },
        ],
      },
    } : {}),
  },
};