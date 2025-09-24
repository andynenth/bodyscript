# BodyScript DRY Refactoring Plan

## Overview
This plan addresses critical DRY violations and establishes a sustainable architecture to prevent future technical debt. The refactoring follows a systematic approach with small, actionable tasks that can be completed incrementally without breaking existing functionality.

---

## Phase 1: Foundation & Cleanup (Day 1)
*Estimated Time: 2-3 hours*

### 1.1 Version Control & Backup Management
- [ ] Create a new Git branch: `refactor/eliminate-dry-violations`
- [ ] Delete `/frontend_backup_20250923_125616/` directory entirely
- [ ] Commit deletion with message: "Remove backup directory - use Git for version control"
- [ ] Create `.gitignore` entry for backup directories: `*_backup_*/`
- [ ] Document in README.md: "Use Git branches for backups, not directory copies"

### 1.2 Archive Consolidation
- [ ] Compare `/frontend/archive_gallery/shared/gallery-common.css` with `/frontend/assets/gallery-common.css`
- [ ] Document differences in a temporary file `ARCHIVE_DIFF.md`
- [ ] If archives are outdated, delete entire `/frontend/archive_gallery/` directory
- [ ] If archives have unique features, extract them to `/docs/archived-features.md`
- [ ] Update `.gitignore`: Add `archive_gallery/` if keeping for reference

### 1.3 Create Module Structure
- [ ] Create `/frontend/js/core/` directory for shared modules
- [ ] Create `/frontend/js/config/` directory for configuration
- [ ] Create `/frontend/css/config/` directory for CSS variables
- [ ] Create `/frontend/js/components/` directory for reusable components
- [ ] Add README.md in each directory explaining its purpose

---

## Phase 2: CSS Modularization (Day 1-2)
*Estimated Time: 3-4 hours*

### 2.1 Extract CSS Variables
- [ ] Create `/frontend/css/config/variables.css` with:
  - [ ] Color palette variables
  - [ ] Typography variables
  - [ ] Spacing variables
  - [ ] Border radius variables
  - [ ] Breakpoint variables
  - [ ] Transition duration variables
- [ ] Create `/frontend/css/config/breakpoints.css` with media query mixins
- [ ] Remove duplicate variable definitions from `gallery-common.css`
- [ ] Remove duplicate variable definitions from `gallery.css`
- [ ] Update `main.css` to import `config/variables.css` first

### 2.2 Component Extraction
- [ ] Create `/frontend/css/components/modal.css`
  - [ ] Move all modal styles from `gallery-common.css` (lines 244-300)
  - [ ] Move all modal styles from `gallery.css` (lines 382-449)
  - [ ] Consolidate into single implementation
- [ ] Create `/frontend/css/components/video-card.css`
  - [ ] Extract video card styles
  - [ ] Extract thumbnail styles
  - [ ] Extract hover effects
- [ ] Create `/frontend/css/components/filters.css`
  - [ ] Extract filter button styles
  - [ ] Extract active filter display styles
- [ ] Update `main.css` to import all component CSS files
- [ ] Test each page to ensure styles still work

### 2.3 Remove Duplicate Styles
- [ ] Delete duplicate modal styles from `gallery-common.css`
- [ ] Delete duplicate modal styles from `gallery.css`
- [ ] Delete duplicate filter styles from multiple files
- [ ] Run CSS linter to check for remaining duplicates
- [ ] Document removed duplicates in `REFACTOR_LOG.md`

---

## Phase 3: JavaScript Modularization (Day 2-3)
*Estimated Time: 5-6 hours*

### 3.1 Create Core Modules
- [ ] Create `/frontend/js/core/VideoPlayer.js`
  ```javascript
  export class VideoPlayer {
    constructor(options) { }
    createPreviewElement() { }
    play() { }
    pause() { }
    destroy() { }
  }
  ```
- [ ] Create `/frontend/js/core/Modal.js`
  ```javascript
  export class Modal {
    constructor(options) { }
    open(content) { }
    close() { }
    destroy() { }
  }
  ```
- [ ] Create `/frontend/js/core/VideoModal.js`
  ```javascript
  export class VideoModal extends Modal {
    constructor() { }
    playVideo(videoData) { }
  }
  ```
- [ ] Create `/frontend/js/core/FilterManager.js`
  ```javascript
  export class FilterManager {
    constructor(videos, renderCallback) { }
    filterBy(category) { }
    clearFilter() { }
    getActiveFilter() { }
  }
  ```
- [ ] Create `/frontend/js/core/GalleryDataStore.js`
  ```javascript
  export class GalleryDataStore {
    constructor() { }
    async loadFromAPI() { }
    getVideos() { }
    getSampleData() { }
  }
  ```

### 3.2 Extract Hover Preview System
- [ ] Create `/frontend/js/components/VideoHoverPreview.js`
- [ ] Move hover preview logic from `gallery-common.js` (lines 170-300)
- [ ] Convert to ES6 class with proper lifecycle management
- [ ] Add destroy() method for cleanup
- [ ] Export as module

### 3.3 Extract Lazy Loading
- [ ] Create `/frontend/js/utils/LazyLoader.js`
- [ ] Move Intersection Observer logic from `gallery-common.js` (lines 441-475)
- [ ] Make it generic for any lazy-loading needs
- [ ] Add configuration options
- [ ] Export as reusable utility

### 3.4 Extract Touch Support
- [ ] Create `/frontend/js/utils/TouchHandler.js`
- [ ] Move touch support from `gallery-common.js` (lines 478-513)
- [ ] Make it configurable and reusable
- [ ] Add gesture recognition capabilities
- [ ] Export as utility module

---

## Phase 4: Refactor gallery-common.js (Day 3)
*Estimated Time: 4-5 hours*

### 4.1 Convert to ES6 Module
- [ ] Rename `gallery-common.js` to `gallery-common-legacy.js` (backup)
- [ ] Create new `/frontend/js/core/GalleryCore.js` as ES6 module
- [ ] Import all created modules (VideoPlayer, Modal, FilterManager, etc.)
- [ ] Remove duplicate implementations
- [ ] Export a clean API interface

### 4.2 Remove Global Variables
- [ ] Replace `window.GALLERY_VIDEOS` with GalleryDataStore
- [ ] Replace `window.currentVideos` with FilterManager state
- [ ] Replace `window.GalleryCommon` with ES6 exports
- [ ] Update all HTML files to use module imports
- [ ] Test each page for functionality

### 4.3 Create Adapter for Legacy Support
- [ ] Create `/frontend/js/adapters/gallery-common-adapter.js`
- [ ] Provide backward compatibility for existing pages
- [ ] Map old function calls to new module methods
- [ ] Add deprecation warnings in console
- [ ] Document migration path in comments

---

## Phase 5: Refactor gallery-page.js (Day 4)
*Estimated Time: 3-4 hours*

### 5.1 Remove Duplicate Implementations
- [ ] Remove duplicate modal code (lines 149-206)
- [ ] Remove duplicate filter code (lines 63-144)
- [ ] Remove duplicate state management
- [ ] Import shared modules instead

### 5.2 Focus on Terminal-Specific Rendering
- [ ] Keep only `renderTerminalGallery()` function
- [ ] Keep terminal-specific styling logic
- [ ] Keep terminal-specific DOM creation
- [ ] Remove all shared functionality

### 5.3 Use Composition Pattern
- [ ] Import VideoModal from core
- [ ] Import FilterManager from core
- [ ] Import GalleryDataStore from core
- [ ] Compose them together for page functionality
- [ ] Test thoroughly

---

## Phase 6: Python Refactoring (Day 4-5)
*Estimated Time: 6-7 hours*

### 6.1 Create Base Classes
- [ ] Create `/cli/src/core/base_detector.py`
  ```python
  class BasePoseDetector(ABC):
      def __init__(self, config)
      @abstractmethod
      def detect_pose(self, frame)
      def get_confidence(self)
  ```
- [ ] Create `/cli/src/core/base_processor.py`
  ```python
  class BaseVideoProcessor(ABC):
      def __init__(self, config)
      @abstractmethod
      def process_video(self, video_path)
      def export_results(self, format)
  ```
- [ ] Create `/cli/src/config/settings.py` with all shared constants

### 6.2 Consolidate Pose Detectors
- [ ] Identify common code in all PoseDetector implementations
- [ ] Move common code to `BasePoseDetector`
- [ ] Update `simple_pose_analyzer.py` to inherit from base
- [ ] Update `research_pose_analyzer.py` to inherit from base
- [ ] Update `creative_pose_analyzer.py` to inherit from base
- [ ] Remove duplicate initialization code
- [ ] Test each analyzer

### 6.3 Consolidate Video Processing
- [ ] Create `/cli/src/core/video_pipeline.py` with shared pipeline
- [ ] Extract common `process_video()` logic
- [ ] Create hooks for customization (pre-process, post-process)
- [ ] Update all 17+ implementations to use base pipeline
- [ ] Remove duplicate error handling
- [ ] Add unit tests

### 6.4 Configuration Management
- [ ] Create `/cli/config.yaml` for all settings
- [ ] Create `/cli/src/config/loader.py` to load config
- [ ] Replace all hardcoded constants
- [ ] Remove duplicate configuration parameters
- [ ] Document all configuration options

---

## Phase 7: Build System Setup (Day 5)
*Estimated Time: 2-3 hours*

### 7.1 JavaScript Build Pipeline
- [ ] Create `/frontend/webpack.config.js` or `/frontend/rollup.config.js`
- [ ] Configure ES6 module bundling
- [ ] Set up CSS concatenation and minification
- [ ] Configure source maps for debugging
- [ ] Add watch mode for development

### 7.2 CSS Processing
- [ ] Set up PostCSS for CSS processing
- [ ] Add autoprefixer for browser compatibility
- [ ] Configure CSS minification
- [ ] Set up CSS purging for unused styles
- [ ] Create build script in package.json

### 7.3 Development Workflow
- [ ] Create `npm run dev` command for development
- [ ] Create `npm run build` command for production
- [ ] Create `npm run lint` for code quality
- [ ] Create `npm run test` for running tests
- [ ] Document commands in README.md

---

## Phase 8: Testing & Validation (Day 6)
*Estimated Time: 4-5 hours*

### 8.1 Unit Tests
- [ ] Create `/frontend/tests/` directory
- [ ] Write tests for VideoPlayer class
- [ ] Write tests for Modal class
- [ ] Write tests for FilterManager class
- [ ] Write tests for GalleryDataStore class
- [ ] Set up Jest or Mocha for JavaScript testing

### 8.2 Python Tests
- [ ] Create `/cli/tests/` directory
- [ ] Write tests for BasePoseDetector
- [ ] Write tests for BaseVideoProcessor
- [ ] Write tests for configuration loader
- [ ] Set up pytest for Python testing

### 8.3 Integration Testing
- [ ] Test gallery page with refactored modules
- [ ] Test upload page functionality
- [ ] Test video processing pipeline
- [ ] Test API endpoints
- [ ] Create automated test suite

### 8.4 Performance Testing
- [ ] Measure page load time before/after refactoring
- [ ] Check bundle sizes
- [ ] Test memory usage in video processing
- [ ] Document performance improvements

---

## Phase 9: Documentation (Day 6)
*Estimated Time: 2-3 hours*

### 9.1 Code Documentation
- [ ] Add JSDoc comments to all JavaScript modules
- [ ] Add docstrings to all Python classes
- [ ] Create type definitions for TypeScript support
- [ ] Generate API documentation

### 9.2 Architecture Documentation
- [ ] Create `/docs/architecture.md` with system overview
- [ ] Create `/docs/modules.md` documenting all modules
- [ ] Create `/docs/migration-guide.md` for legacy code updates
- [ ] Update main README.md with new structure

### 9.3 Developer Guidelines
- [ ] Create `/docs/contributing.md` with coding standards
- [ ] Document the DRY principle enforcement
- [ ] Create pull request template with DRY checklist
- [ ] Add pre-commit hooks for duplicate detection

---

## Phase 10: Deployment & Monitoring (Day 7)
*Estimated Time: 2-3 hours*

### 10.1 Gradual Rollout
- [ ] Deploy to staging environment
- [ ] Run full test suite on staging
- [ ] Monitor for JavaScript errors
- [ ] Check browser compatibility
- [ ] Get team feedback

### 10.2 Production Deployment
- [ ] Create rollback plan
- [ ] Deploy during low-traffic period
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Document deployment process

### 10.3 Post-Deployment
- [ ] Monitor for 24 hours
- [ ] Address any immediate issues
- [ ] Schedule team retrospective
- [ ] Plan next refactoring phase
- [ ] Close refactoring branch

---

## Success Metrics

### Code Quality Metrics
- **Before**: 800+ duplicate JS lines, 500+ duplicate CSS lines
- **Target**: <50 duplicate lines total
- **Measurement**: Use code analysis tools

### File Size Metrics
- **Before**: Measure total bundle size
- **Target**: 40-50% reduction
- **Measurement**: Build output analysis

### Maintenance Metrics
- **Before**: Changes require updates in 3+ places
- **Target**: Single source of truth for each feature
- **Measurement**: Track time for feature updates

### Performance Metrics
- **Page Load Time**: Target 20% improvement
- **Memory Usage**: Target 30% reduction
- **Processing Speed**: Maintain or improve

---

## Risk Mitigation

### Rollback Strategy
1. Keep `gallery-common-legacy.js` for 30 days
2. Feature flag for new/old implementation
3. Git tags at each phase completion
4. Database backups before Python changes

### Testing Strategy
1. Automated tests before each phase
2. Manual QA checklist
3. Staging environment validation
4. Gradual production rollout

### Communication Plan
1. Daily progress updates
2. Blocker escalation process
3. Team code reviews at phase boundaries
4. Documentation updates in real-time

---

## Long-term Maintenance

### Prevention Strategies
1. **Code Reviews**: Mandatory DRY principle check
2. **Linting Rules**: Configure ESLint/Pylint for duplicate detection
3. **CI/CD Pipeline**: Automated duplicate detection
4. **Architecture Decisions**: Document and enforce module boundaries
5. **Regular Audits**: Quarterly DRY violation reports

### Monitoring Tools
- SonarQube for code quality
- Bundle analyzer for JavaScript
- Coverage reports for test completeness
- Performance monitoring dashboard

### Team Training
1. DRY principle workshop
2. Module architecture training
3. Best practices documentation
4. Pair programming sessions

---

## Timeline Summary

- **Day 1**: Foundation & Cleanup + CSS Start (5-6 hours)
- **Day 2**: CSS Completion + JS Modules Start (5-6 hours)
- **Day 3**: JS Modules Completion + gallery-common refactor (5-6 hours)
- **Day 4**: gallery-page refactor + Python Start (5-6 hours)
- **Day 5**: Python Completion + Build System (5-6 hours)
- **Day 6**: Testing + Documentation (6-7 hours)
- **Day 7**: Deployment + Monitoring (2-3 hours)

**Total Estimated Time**: 35-40 hours (5-7 working days)

---

## Notes

- Each checkbox represents 15-30 minutes of work
- Complete phases sequentially to avoid conflicts
- Commit after each major checkbox
- Run tests after each phase
- Document blockers immediately
- Ask for help if stuck for >30 minutes

This plan ensures systematic elimination of technical debt while maintaining system stability throughout the refactoring process.