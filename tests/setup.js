/**
 * Test setup file for Vitest
 * Sets up DOM environment and global mocks
 */

import { vi } from 'vitest';

// Mock global window properties
Object.defineProperty(window, 'API_URL', {
  writable: true,
  value: 'http://localhost:8000'
});

// Mock console methods to reduce noise during tests
const originalConsole = { ...console };
beforeEach(() => {
  console.error = vi.fn();
  console.warn = vi.fn();
  console.log = vi.fn();
});

afterEach(() => {
  Object.assign(console, originalConsole);
  vi.clearAllMocks();
  // Clean up DOM after each test
  document.body.innerHTML = '';
});

// Mock HTMLVideoElement methods that aren't implemented in jsdom
Object.defineProperty(HTMLVideoElement.prototype, 'play', {
  writable: true,
  value: vi.fn().mockImplementation(function() {
    this.paused = false;
    this.currentTime = 0;
    return Promise.resolve();
  })
});

Object.defineProperty(HTMLVideoElement.prototype, 'pause', {
  writable: true,
  value: vi.fn().mockImplementation(function() {
    this.paused = true;
  })
});

Object.defineProperty(HTMLVideoElement.prototype, 'load', {
  writable: true,
  value: vi.fn()
});

// Mock video properties
Object.defineProperty(HTMLVideoElement.prototype, 'duration', {
  writable: true,
  value: 10
});

Object.defineProperty(HTMLVideoElement.prototype, 'currentTime', {
  writable: true,
  value: 0
});

Object.defineProperty(HTMLVideoElement.prototype, 'paused', {
  writable: true,
  value: true
});

Object.defineProperty(HTMLVideoElement.prototype, 'ended', {
  writable: true,
  value: false
});

// Global test utilities
global.createMockElement = (tagName, properties = {}) => {
  const element = document.createElement(tagName);
  Object.assign(element, properties);
  return element;
};

global.createMockContainer = () => {
  const container = document.createElement('div');
  container.className = 'test-container';
  document.body.appendChild(container);
  return container;
};

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  callback
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
  callback
}));