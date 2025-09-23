# Frontend Test Checklist

## Current Working Features (Baseline)

### Upload Page Features
- [ ] **File Selection**
  - [ ] Click "SELECT FILE" button works
  - [ ] Drag and drop file works
  - [ ] File validation shows errors for invalid files
  - [ ] File validation accepts MP4/MOV/AVI
  - [ ] File size limit (50MB) enforced
  - [ ] Duration limit (15 seconds) shown

- [ ] **File Display**
  - [ ] Selected file info shows (name, size)
  - [ ] REMOVE button clears selection
  - [ ] Can reselect file after removing
  - [ ] File details toggle works

- [ ] **Processing**
  - [ ] "Execute Pose Detection" button enables with file
  - [ ] Upload progress bar animates (ASCII style)
  - [ ] Progress percentage updates
  - [ ] Status messages display correctly
  - [ ] Frame counter shows during processing

- [ ] **Results**
  - [ ] Video player shows processed video
  - [ ] Play button overlay visible on hover (desktop)
  - [ ] Click video opens modal player
  - [ ] Modal close button works (X button)
  - [ ] ESC key closes modal

- [ ] **Downloads**
  - [ ] DOWNLOAD VIDEO button works
  - [ ] DOWNLOAD POSE DATA button works (shows as POSE DATA on mobile)
  - [ ] PROCESS ANOTHER button resets page

### Mobile Specific (< 768px)
- [ ] Progress bar is 30 characters (not 50)
- [ ] Buttons stack vertically
- [ ] Button text is 16px (no zoom)
- [ ] Terminal dots (red/yellow/green) hidden
- [ ] Status badge appears under file info
- [ ] Remove button appears under file name
- [ ] Touch targets >= 44px
- [ ] No horizontal scrolling
- [ ] Body padding reduced (0.5rem)

### Gallery Page Features
- [ ] Video cards display correctly
- [ ] Category filters work
- [ ] Video hover effects work (desktop)
- [ ] Stats display (views, accuracy)
- [ ] Upload button navigates to upload page

### Performance Metrics
- [ ] Page load time: _______ seconds
- [ ] Time to interactive: _______ seconds
- [ ] Console errors: _______ (should be 0)
- [ ] Failed network requests: _______ (should be 0)

### Cross-Browser Testing
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Chrome
- [ ] Mobile Safari

## Test After Each Phase

### Phase Completed: _____________
### Date/Time: _____________
### Tester: _____________

**All features still working?** Yes / No
**New issues found:** _________________________________
**Notes:** ___________________________________________