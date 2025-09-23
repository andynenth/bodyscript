# Mobile UI/UX Fix Plan for upload.html

## 📱 Mobile Responsive Design Fixes

### 1. Video Player Sizing (Mobile)
- [ ] Add media query for screens < 768px
- [ ] Set video player `max-width: 280px` on mobile
- [ ] Set video player `width: 100%` for responsiveness
- [ ] Add `aspect-ratio: 16/9` to maintain proportions
- [ ] Center video player with `margin: 0 auto`
- [ ] Add static play icon overlay for mobile (always visible)
- [ ] Reduce video container padding on mobile

### 2. Button Layout (Mobile)
- [ ] Create media query for button-group at < 768px
- [ ] Change button-group to `flex-direction: column`
- [ ] Set each button to `width: 100%`
- [ ] Add `margin-bottom: 0.75rem` between buttons
- [ ] Set `min-height: 48px` for all buttons (touch target)
- [ ] Increase button font-size to `16px` on mobile
- [ ] Ensure button text doesn't wrap
- [ ] Test touch targets are at least 44x44px

### 3. General Spacing & Padding
- [ ] Add media query for terminal-container padding on mobile
- [ ] Set `padding: 1rem` for terminal-body on mobile
- [ ] Add `margin-bottom: 1.5rem` between major sections
- [ ] Reduce terminal-window border-radius on mobile
- [ ] Add horizontal padding to prevent edge touching

### 4. System Requirements Section
- [ ] Add class to hide system-info when results show
- [ ] Add JavaScript to toggle visibility after processing
- [ ] Ensure smooth transition when hiding
- [ ] Test visibility toggle on process completion

### 5. File Info Card (Mobile)
- [ ] Check if file-info overflows on mobile
- [ ] Ensure status badge doesn't wrap text
- [ ] Add `white-space: nowrap` to status badge
- [ ] Reduce padding inside file-info on mobile
- [ ] Test file name truncation for long names
- [ ] Ensure file details are readable

### 6. Typography & Readability
- [ ] Set base font size to 16px on mobile (prevent zoom)
- [ ] Increase file-name font to 16px on mobile
- [ ] Increase file-details font to 14px minimum
- [ ] Ensure all interactive elements use 16px+
- [ ] Test readability without zooming

### 7. Processing Section (Mobile)
- [ ] Reduce progress bar width on mobile if needed
- [ ] Ensure progress percentage is visible
- [ ] Stack processing info vertically if cramped
- [ ] Hide frame counter if it causes overflow

### 8. Drop Zone (Mobile)
- [ ] Reduce ASCII art size on mobile
- [ ] Ensure drop zone is tappable
- [ ] Increase "SELECT FILE" button size
- [ ] Test file selection on mobile browsers

### 9. Results Section
- [ ] Hide processing animation after completion
- [ ] Ensure results section has proper spacing
- [ ] Test scroll behavior to results

### 10. Testing & Validation
- [ ] Test on iPhone SE (375px width)
- [ ] Test on iPhone 12 (390px width)
- [ ] Test on Android devices (360px width)
- [ ] Test on tablet (768px width)
- [ ] Validate touch targets are accessible
- [ ] Check for horizontal scrolling issues
- [ ] Test in both portrait and landscape

## 📝 Implementation Order

### Phase 1: Critical Fixes (Must Do First)
1. Video player sizing
2. Button stacking and sizing
3. Base font size fixes

### Phase 2: Layout Improvements
4. Section spacing
5. File info card adjustments
6. Hide unnecessary sections

### Phase 3: Polish
7. Typography fine-tuning
8. Animation adjustments
9. Final testing

## 🎯 Success Criteria
- [ ] No horizontal scrolling on mobile
- [ ] All buttons easily tappable
- [ ] Text readable without zooming
- [ ] Video player appropriately sized
- [ ] Clean, organized layout on small screens
- [ ] Smooth transitions between states

## 📐 Breakpoints to Test
- 320px (iPhone SE 1st gen)
- 375px (iPhone SE 2nd gen, iPhone X/11/12 mini)
- 390px (iPhone 12/13/14)
- 414px (iPhone Plus models)
- 768px (iPad, tablet breakpoint)

## 🔍 Common Issues to Watch For
- Text getting cut off
- Buttons overlapping
- Status badge wrapping
- File name overflow
- Touch targets too small
- Z-index conflicts with overlays

## ✅ Definition of Done
- All checkboxes marked complete
- Tested on 3+ real devices
- No console errors
- Lighthouse mobile score > 90
- User can complete full flow on mobile without issues