# CSS Configuration

This directory contains CSS variables, mixins, and configuration used throughout the stylesheets.

## Files

- **variables.css** - CSS custom properties for colors, typography, spacing, etc.
- **breakpoints.css** - Responsive breakpoint definitions
- **animations.css** - Reusable animation keyframes
- **mixins.css** - Common CSS patterns (if using PostCSS)

## Usage

Import at the beginning of main.css or any CSS file that needs variables:

```css
@import './config/variables.css';
@import './config/breakpoints.css';
```

## Variable Naming Convention

- **Colors**: `--color-{name}` or `--{context}-color-{name}`
- **Spacing**: `--spacing-{size}`
- **Typography**: `--font-{name}`, `--text-{size}`
- **Borders**: `--border-{property}`
- **Transitions**: `--transition-{speed}`
- **Breakpoints**: `--breakpoint-{name}`

## Guidelines

- Define all variables in one place
- Use semantic naming (e.g., `--color-primary` not `--blue`)
- Document color palette and design decisions
- Keep specificity low