// Formatting helper utilities

export function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

export function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function formatNumber(num) {
  return new Intl.NumberFormat().format(num);
}

export function formatPercent(value, decimals = 1) {
  return value.toFixed(decimals) + '%';
}

export function truncateString(str, maxLength) {
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength - 3) + '...';
}

export function formatDate(date) {
  const d = new Date(date);
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
}

export function generateProgressBar(progress, barLength = 50) {
  const filled = Math.floor((progress / 100) * barLength);
  const empty = barLength - filled;
  return '[' + '█'.repeat(filled) + '░'.repeat(empty) + ']';
}