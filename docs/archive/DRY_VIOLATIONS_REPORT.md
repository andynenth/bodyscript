# DRY (Don't Repeat Yourself) Violations Report

## Executive Summary

This report identifies significant code duplication and DRY principle violations across the BodyScript project. The analysis covers CSS, JavaScript, HTML, and Python files, revealing multiple areas where code refactoring could improve maintainability and reduce redundancy.

---

## 1. CSS Violations

### 1.1 Duplicate Color Definitions
**Severity: High**
**Files Affected:**
- `frontend/assets/gallery-common.css`
- `frontend/css/pages/gallery.css`
- `frontend/archive_gallery/shared/gallery-common.css`

**Issue:** CSS variables are redefined multiple times across files with identical values:
```css
--text-terminal-green: #27c93f;  /* Defined in multiple places */
--bg-terminal: #1e1e1e;          /* Repeated definition */
--border-secondary: #666666;      /* Duplicated */
```

**Recommendation:** Create a single `variables.css` file and import it everywhere needed.

### 1.2 Modal Styling Duplication
**Severity: High**
**Files Affected:**
- `frontend/assets/gallery-common.css` (lines 244-300)
- `frontend/css/pages/gallery.css` (lines 382-449)

**Issue:** Modal styles are duplicated with nearly identical code:
- `.modal` class defined twice
- `.modal-close` button styles repeated
- `.modal-video` styles duplicated

**Recommendation:** Extract modal styles to `frontend/css/components/modal.css` and reuse.

### 1.3 Border Radius Inconsistency
**Severity: Medium**
**Occurrences:** 30+ instances

**Issue:** `border-radius: 4px` and `border-radius: 8px` are hardcoded throughout:
- No CSS variable for consistent border radius
- Same values repeated in multiple files

**Recommendation:** Define border radius variables:
```css
--radius-small: 4px;
--radius-medium: 8px;
```

### 1.4 Responsive Breakpoints
**Severity: Medium**
**Files Affected:** All CSS files with media queries

**Issue:** Media query breakpoints are hardcoded:
```css
@media (max-width: 768px) { ... }  /* Repeated everywhere */
@media (max-width: 1024px) { ... }
@media (max-width: 640px) { ... }
```

**Recommendation:** Use CSS custom properties or SCSS variables for breakpoints.

---

## 2. JavaScript Violations

### 2.1 Video Preview Logic Duplication
**Severity: High**
**Files Affected:**
- `frontend/assets/gallery-common.js` (lines 170-300)
- `frontend/js/pages/gallery-page.js`

**Issue:** Hover preview functionality is implemented multiple times with similar logic:
- Video element creation
- Play/pause controls
- Timeout handlers

**Recommendation:** Create a reusable `VideoPreview` class or module.

### 2.2 Modal Management Code
**Severity: High**
**Files Affected:**
- `frontend/assets/gallery-common.js` (lines 302-366)
- `frontend/js/pages/gallery-page.js` (lines 149-206)

**Issue:** Full screen modal player implemented twice with nearly identical code:
- Modal creation
- Event handlers (click, ESC key)
- Video control logic

**Recommendation:** Single `VideoModal` module that both files can import.

### 2.3 Filter Implementation
**Severity: Medium**
**Files Affected:**
- `frontend/assets/gallery-common.js` (lines 369-396)
- `frontend/js/pages/gallery-page.js` (lines 60-144)

**Issue:** Filter logic duplicated with slight variations:
- Category filtering
- Active state management
- DOM updates

**Recommendation:** Create a `FilterManager` class for reusable filtering.

### 2.4 Gallery Data Structure
**Severity: Low**
**Files Affected:** Multiple JS files

**Issue:** Sample video data structure repeated:
```javascript
SAMPLE_VIDEOS array defined in multiple places
currentVideos array management duplicated
```

**Recommendation:** Centralize data management in a store or service module.

---

## 3. HTML Violations

### 3.1 Head Section Duplication
**Severity: Medium**
**Files Affected:**
- `frontend/index.html`
- `frontend/upload.html`
- `frontend/admin.html`
- All test HTML files

**Issue:** Common head elements repeated:
```html
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono..." />
<script src="config.js"></script>
<link rel="stylesheet" href="assets/gallery-common.css">
```

**Recommendation:** Use a build tool or server-side includes for common head elements.

### 3.2 Modal Structure
**Severity: Low**
**Files Affected:** Multiple HTML files

**Issue:** Modal HTML structure repeated:
```html
<div class="modal">
  <button class="modal-close">×</button>
  <video class="modal-video" controls>
    <source src="" type="video/mp4">
  </video>
</div>
```

**Recommendation:** Dynamically create modals via JavaScript when needed.

---

## 4. Python Violations

### 4.1 PoseDetector Class Duplication
**Severity: High**
**Files Affected:**
- `archive_old/core/pose_detector.py`
- Multiple processor files in `cli/src/processors/`

**Issue:** Core pose detection logic reimplemented multiple times:
- Initialization parameters repeated
- Similar detection confidence handling
- Duplicated result structures

**Recommendation:** Single base `PoseDetector` class with inheritance for variations.

### 4.2 Video Processing Functions
**Severity: High**
**Occurrences:** 17+ implementations

**Issue:** `process_video()` function implemented in:
- `process_data_videos.py`
- `cli/src/processors/simple_pose_analyzer.py`
- `cli/src/processors/research_pose_analyzer.py`
- `cli/src/processors/creative_pose_analyzer.py`
- `backend/app.py`
- `backend/process_wrapper.py`
- Multiple experiment files

**Recommendation:** Create abstract base class with common video processing pipeline.

### 4.3 Configuration Parameters
**Severity: Medium**
**Files Affected:** All Python processors

**Issue:** Configuration constants repeated:
```python
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
MODEL_COMPLEXITY = 1
```

**Recommendation:** Single configuration module imported everywhere.

### 4.4 Error Handling Patterns
**Severity: Low**
**Files Affected:** Multiple Python files

**Issue:** Similar try-catch blocks for MediaPipe operations repeated throughout.

**Recommendation:** Decorator or context manager for common error handling.

---

## 5. Cross-File Duplication

### 5.1 Backup Files
**Severity: Critical**
**Files Affected:**
- `frontend_backup_20250923_125616/` directory
- `frontend/` directory

**Issue:** Entire frontend directory is duplicated as backup, doubling maintenance burden.

**Recommendation:** Remove backup directories, use Git for version control.

### 5.2 Archive Duplication
**Severity: High**
**Files Affected:**
- `frontend/archive_gallery/shared/`
- `frontend/assets/`

**Issue:** `gallery-common.css` and `gallery-common.js` exist in multiple locations with similar content.

**Recommendation:** Single source of truth for shared assets.

---

## 6. Priority Refactoring Recommendations

### High Priority (Immediate Action Required)
1. **Remove backup directories** - Use version control instead
2. **Consolidate modal code** - Single implementation for all modals
3. **Unify PoseDetector classes** - One base class with extensions
4. **Merge duplicate CSS files** - Single source for common styles

### Medium Priority (Next Sprint)
1. **Extract CSS variables** - Central variables file
2. **Create reusable JS modules** - VideoPreview, FilterManager, etc.
3. **Standardize video processing** - Base class for processors
4. **Configuration management** - Single config module

### Low Priority (Future Improvement)
1. **HTML templating** - Reduce head section duplication
2. **Error handling patterns** - Decorators for common patterns
3. **Build system** - Consider webpack/rollup for asset management

---

## 7. Metrics Summary

- **Total Duplicate CSS Lines:** ~500+ lines
- **Total Duplicate JS Lines:** ~800+ lines
- **Total Duplicate Python Functions:** 17+ implementations
- **Duplicate Files:** 15+ files in backup/archive directories
- **Estimated Reduction Potential:** 40-50% of current codebase

---

## 8. Impact Analysis

### Current Impact
- **Maintenance Overhead:** Changes require updates in multiple places
- **Bug Risk:** Fixes may not be applied to all duplicates
- **Development Speed:** Slower due to redundant code
- **File Size:** Larger bundle sizes affecting load times

### Post-Refactoring Benefits
- **Reduced Maintenance:** Single point of change
- **Consistency:** Uniform behavior across application
- **Performance:** Smaller file sizes, better caching
- **Developer Experience:** Clearer code organization

---

## Conclusion

The BodyScript project contains significant DRY violations that impact maintainability and development efficiency. The most critical issues are:

1. **Duplicate backup/archive directories** consuming space and causing confusion
2. **Modal and video preview code** duplicated across multiple files
3. **Python video processing** logic repeated with slight variations
4. **CSS variables and styles** defined multiple times

Addressing these violations through systematic refactoring will significantly improve code quality, reduce bugs, and accelerate future development. Priority should be given to removing duplicate directories and consolidating the most frequently used components (modals, video processing, CSS variables).