# Terminal-Style Gallery & Upload

## Features

### Gallery Page (`index.html`)
- **Terminal window** chrome with classic red/yellow/green dots
- **Command-line interface** showing `./bodyscript showcase --filter=all`
- **ASCII art logo** in terminal style
- **Green terminal glow** effects on hover
- **5-column grid** of videos (responsive)
- **Detection accuracy** shown as ASCII progress bars
- **Typing effect** for command prompt
- **Filter buttons** styled as terminal commands: `[ALL]`, `[DANCE]`, etc.

### Upload Page (`upload.html`)
- **Full terminal interface** with command prompt
- **ASCII art drop zone** with cat art
- **Terminal-style output** showing processing steps
- **ASCII progress bars** during upload: `[████████░░░░░░░░]`
- **Command-line feedback** with color-coded messages:
  - Green `[OK]` for success
  - Yellow `[WARNING]` for warnings
  - Red `[ERROR]` for errors
- **File analysis** displayed as terminal output
- **Animated spinner** using ASCII characters `| / - \`
- **Processing simulation** with realistic terminal feedback

## Terminal Aesthetic Elements

### Color Scheme
```css
--text-terminal-green: #27c93f  /* Classic terminal green */
--bg-terminal: #1e1e1e          /* Dark terminal background */
--border-secondary: #666666      /* Subtle borders */
```

### Typography
- **Font**: JetBrains Mono (monospace)
- **Text effects**: Blinking cursor, typing animation
- **ASCII elements**: Progress bars, borders, logos

### Interactive Elements
1. **Hover Effects**: Green glow on cards and buttons
2. **Drag & Drop**: Terminal responds with status messages
3. **Processing**: Live terminal output simulation
4. **Error Handling**: Color-coded terminal messages

## Usage

### View Gallery
```bash
open frontend/gallery/option1-terminal/index.html
```

### Upload Demo
1. Click `[> TRY DEMO]` button in gallery
2. Drag & drop video file or click `[SELECT FILE]`
3. Watch terminal output as file is analyzed
4. Click `[EXECUTE POSE DETECTION]`
5. View ASCII progress bars and processing steps
6. Download results when complete

## Terminal Commands Simulated

```bash
$ ./bodyscript upload --mode=interactive
Initializing upload module...
[OK] MediaPipe loaded
[OK] OpenCV initialized
[OK] Ready for video upload
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> Analyzing file: dance.mp4
[OK] File loaded: dance.mp4
    Size: 5.2 MB
    Duration: 0:12
    Resolution: 1920x1080

[STARTING] Pose detection pipeline
[OK] Step 1/5 complete
[OK] Step 2/5 complete
[OK] Step 3/5 complete
[OK] Step 4/5 complete
[OK] Step 5/5 complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[COMPLETE] Processing finished successfully
> Output files ready for download
```

## Customization

### Change Terminal Colors
Edit the CSS variables in the `<style>` section:
```css
--text-terminal-green: #00ff00;  /* Brighter green */
--text-terminal-green: #39ff14;  /* Neon green */
--text-terminal-green: #7fff00;  /* Chartreuse */
```

### Modify ASCII Art
The drop zone ASCII art can be customized in the HTML:
```html
<pre class="ascii-art">
    /* Your custom ASCII art here */
</pre>
```

### Adjust Typing Speed
Change the timeout in the typing animation:
```javascript
setTimeout(typeCommand, 50); // Adjust milliseconds
```

## Browser Support
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (may need webkit prefixes)
- Mobile: Responsive, touch-friendly

## Performance
- Lightweight: No external dependencies except fonts
- Fast animations: CSS transforms and transitions
- Optimized: Lazy loading for videos
- Accessible: Semantic HTML structure