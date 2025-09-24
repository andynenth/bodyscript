/**
 * Unit tests for Modal class
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Modal } from '@core/Modal.js';

describe('Modal', () => {
  let modal;

  beforeEach(() => {
    modal = new Modal();
  });

  afterEach(() => {
    if (modal) {
      modal.destroy();
    }
  });

  describe('constructor', () => {
    it('should create instance with default options', () => {
      expect(modal.options.className).toBe('modal');
      expect(modal.options.closeOnOverlayClick).toBe(true);
      expect(modal.options.closeOnEscape).toBe(true);
      expect(modal.options.animated).toBe(true);
    });

    it('should merge custom options', () => {
      const customModal = new Modal({
        className: 'custom-modal',
        closeOnOverlayClick: false,
        customOption: 'test'
      });

      expect(customModal.options.className).toBe('custom-modal');
      expect(customModal.options.closeOnOverlayClick).toBe(false);
      expect(customModal.options.closeOnEscape).toBe(true); // default
      expect(customModal.options.customOption).toBe('test');

      customModal.destroy();
    });

    it('should initialize properties correctly', () => {
      expect(modal.isOpen).toBe(false);
      expect(modal.listeners).toBeInstanceOf(Map);
      expect(modal.content).toBe(null);
    });

    it('should create modal DOM structure', () => {
      expect(modal.modal).toBeTruthy();
      expect(modal.modal.tagName).toBe('DIV');
      expect(modal.modal.className).toBe('modal');
      expect(document.body.contains(modal.modal)).toBe(true);
    });

    it('should create close button', () => {
      expect(modal.closeButton).toBeTruthy();
      expect(modal.closeButton.tagName).toBe('BUTTON');
      expect(modal.closeButton.className).toBe('modal-close');
      expect(modal.closeButton.innerHTML).toBe('×');
      expect(modal.modal.contains(modal.closeButton)).toBe(true);
    });
  });

  describe('opening and closing', () => {
    it('should open modal', () => {
      modal.open();

      expect(modal.isOpen).toBe(true);
      expect(modal.modal.classList.contains('active')).toBe(true);
    });

    it('should close modal', () => {
      modal.open();
      modal.close();

      expect(modal.isOpen).toBe(false);
      expect(modal.modal.classList.contains('active')).toBe(false);
    });

    it('should not open if already open', () => {
      modal.open();
      const initialState = modal.isOpen;

      modal.open();

      expect(modal.isOpen).toBe(initialState);
      expect(modal.isOpen).toBe(true);
    });

    it('should not close if already closed', () => {
      expect(modal.isOpen).toBe(false);

      modal.close();

      expect(modal.isOpen).toBe(false);
    });

    it('should toggle open/closed state', () => {
      expect(modal.isOpen).toBe(false);

      modal.toggle();
      expect(modal.isOpen).toBe(true);

      modal.toggle();
      expect(modal.isOpen).toBe(false);
    });

    it('should provide isModalOpen method', () => {
      expect(modal.isModalOpen()).toBe(false);

      modal.open();
      expect(modal.isModalOpen()).toBe(true);

      modal.close();
      expect(modal.isModalOpen()).toBe(false);
    });

    it('should provide show/hide aliases', () => {
      modal.show();
      expect(modal.isOpen).toBe(true);

      modal.hide();
      expect(modal.isOpen).toBe(false);
    });
  });

  describe('content management', () => {
    it('should set string content', () => {
      const content = '<p>Test content</p>';

      modal.setContent(content);

      expect(modal.content).toBeTruthy();
      expect(modal.content.tagName).toBe('DIV');
      expect(modal.content.className).toBe('modal-content');
      expect(modal.content.innerHTML).toBe(content);
      expect(modal.modal.contains(modal.content)).toBe(true);
    });

    it('should set HTML element content', () => {
      const element = document.createElement('div');
      element.id = 'test-content';
      element.textContent = 'Test element';

      modal.setContent(element);

      expect(modal.content).toBe(element);
      expect(modal.modal.contains(element)).toBe(true);
    });

    it('should replace existing content', () => {
      const content1 = '<p>First content</p>';
      const content2 = '<p>Second content</p>';

      modal.setContent(content1);
      const firstContent = modal.content;

      modal.setContent(content2);

      expect(modal.content).not.toBe(firstContent);
      expect(modal.content.innerHTML).toBe(content2);
      expect(modal.modal.contains(firstContent)).toBe(false);
    });

    it('should get content', () => {
      const element = document.createElement('div');

      modal.setContent(element);

      expect(modal.getContent()).toBe(element);
      expect(modal.getContent()).toBe(modal.content);
    });

    it('should open with content', () => {
      const content = '<p>Test content</p>';

      modal.open(content);

      expect(modal.isOpen).toBe(true);
      expect(modal.content.innerHTML).toBe(content);
    });
  });

  describe('event handling', () => {
    it('should handle escape key when enabled', () => {
      const escapeModal = new Modal({ closeOnEscape: true });
      escapeModal.open();

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);

      expect(escapeModal.isOpen).toBe(false);
      escapeModal.destroy();
    });

    it('should not handle escape key when disabled', () => {
      const noEscapeModal = new Modal({ closeOnEscape: false });
      noEscapeModal.open();

      const event = new KeyboardEvent('keydown', { key: 'Escape' });
      document.dispatchEvent(event);

      expect(noEscapeModal.isOpen).toBe(true);
      noEscapeModal.destroy();
    });

    it('should handle overlay click when enabled', () => {
      const overlayModal = new Modal({ closeOnOverlayClick: true });
      overlayModal.open();

      const event = new MouseEvent('click', { bubbles: true });
      Object.defineProperty(event, 'target', {
        value: overlayModal.modal,
        enumerable: true
      });

      overlayModal.modal.dispatchEvent(event);

      expect(overlayModal.isOpen).toBe(false);
      overlayModal.destroy();
    });

    it('should not close on content click', () => {
      const content = document.createElement('div');
      modal.setContent(content);
      modal.open();

      const event = new MouseEvent('click', { bubbles: true });
      Object.defineProperty(event, 'target', {
        value: content,
        enumerable: true
      });

      modal.modal.dispatchEvent(event);

      expect(modal.isOpen).toBe(true);
    });

    it('should handle close button click', () => {
      modal.open();

      modal.closeButton.click();

      expect(modal.isOpen).toBe(false);
    });
  });

  describe('custom events', () => {
    it('should emit open event', () => {
      const openHandler = vi.fn();
      modal.on('open', openHandler);

      modal.open();

      expect(openHandler).toHaveBeenCalled();
    });

    it('should emit close event', () => {
      const closeHandler = vi.fn();
      modal.on('close', closeHandler);

      modal.open();
      modal.close();

      expect(closeHandler).toHaveBeenCalled();
    });

    it('should add multiple event listeners', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      modal.on('open', handler1);
      modal.on('open', handler2);

      modal.open();

      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
    });

    it('should remove event listeners', () => {
      const handler = vi.fn();

      modal.on('open', handler);
      modal.off('open', handler);

      modal.open();

      expect(handler).not.toHaveBeenCalled();
    });

    it('should handle removing non-existent listeners', () => {
      const handler = vi.fn();

      expect(() => modal.off('nonexistent', handler)).not.toThrow();
      expect(() => modal.off('open', handler)).not.toThrow();
    });
  });

  describe('close button management', () => {
    it('should set close button text', () => {
      modal.setCloseButtonText('Close');

      expect(modal.closeButton.innerHTML).toBe('Close');
    });

    it('should hide close button', () => {
      modal.hideCloseButton();

      expect(modal.closeButton.style.display).toBe('none');
    });

    it('should show close button', () => {
      modal.hideCloseButton();
      modal.showCloseButton();

      expect(modal.closeButton.style.display).toBe('');
    });
  });

  describe('element access', () => {
    it('should return modal element', () => {
      expect(modal.getElement()).toBe(modal.modal);
    });
  });

  describe('cleanup and destruction', () => {
    it('should clean up all resources on destroy', () => {
      const handler = vi.fn();
      modal.on('open', handler);
      modal.open();

      const modalElement = modal.modal;
      const closeButton = modal.closeButton;

      modal.destroy();

      expect(modal.modal).toBe(null);
      expect(modal.closeButton).toBe(null);
      expect(modal.content).toBe(null);
      expect(modal.isOpen).toBe(false);
      expect(modal.listeners.size).toBe(0);
      expect(document.body.contains(modalElement)).toBe(false);
    });

    it('should close modal before destroying if open', () => {
      modal.open();
      const closeSpy = vi.spyOn(modal, 'close');

      modal.destroy();

      expect(closeSpy).toHaveBeenCalled();
    });

    it('should remove event listeners on destroy', () => {
      modal.open();

      // Add listeners that would normally be cleaned up
      const escapeListener = document.querySelector('[data-testid="escape-listener"]');
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

      modal.destroy();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', modal._handleEscape);
    });
  });

  describe('event listener cleanup', () => {
    it('should properly clean up escape key listener', () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener');

      modal.open();
      modal.close();

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', modal._handleEscape);
    });

    it('should not add escape listener if disabled', () => {
      const noEscapeModal = new Modal({ closeOnEscape: false });
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener');

      noEscapeModal.open();

      expect(addEventListenerSpy).not.toHaveBeenCalledWith('keydown', noEscapeModal._handleEscape);
      noEscapeModal.destroy();
    });
  });

  describe('edge cases', () => {
    it('should handle multiple rapid open/close calls', () => {
      modal.open();
      modal.close();
      modal.open();
      modal.close();

      expect(modal.isOpen).toBe(false);
    });

    it('should handle setting null content', () => {
      modal.setContent('initial content');
      modal.setContent(null);

      // Should not crash, content should be cleared
      expect(modal.content).toBe(null);
    });

    it('should handle setting undefined content', () => {
      modal.setContent('initial content');

      expect(() => modal.setContent(undefined)).not.toThrow();
    });
  });
});