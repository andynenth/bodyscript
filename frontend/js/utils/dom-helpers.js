// DOM helper utilities

export function $(selector) {
  return document.querySelector(selector);
}

export function $$(selector) {
  return document.querySelectorAll(selector);
}

export function show(element) {
  if (!element) return;
  element.style.display = 'block';
}

export function hide(element) {
  if (!element) return;
  element.style.display = 'none';
}

export function addClass(element, className) {
  if (!element) return;
  element.classList.add(className);
}

export function removeClass(element, className) {
  if (!element) return;
  element.classList.remove(className);
}

export function toggleClass(element, className) {
  if (!element) return;
  element.classList.toggle(className);
}

export function hasClass(element, className) {
  if (!element) return false;
  return element.classList.contains(className);
}

export function setText(element, text) {
  if (!element) return;
  element.textContent = text;
}

export function setHTML(element, html) {
  if (!element) return;
  element.innerHTML = html;
}

export function createElement(tag, className = '', content = '') {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content) element.textContent = content;
  return element;
}

export function scrollToBottom(element) {
  if (!element) return;
  element.scrollTop = element.scrollHeight;
}