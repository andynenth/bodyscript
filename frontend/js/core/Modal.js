/**
 * Modal - Base modal implementation
 * Provides modal window functionality with overlay, close handling, and lifecycle management
 */

export class Modal {
  constructor(options = {}) {
    this.options = {
      className: 'modal',
      closeOnOverlayClick: true,
      closeOnEscape: true,
      animated: true,
      ...options
    };

    this.modal = null;
    this.closeButton = null;
    this.content = null;
    this.isOpen = false;
    this.listeners = new Map();

    this._handleEscape = this._handleEscape.bind(this);
    this._handleOverlayClick = this._handleOverlayClick.bind(this);
    this._handleCloseClick = this._handleCloseClick.bind(this);

    this._createModal();
  }

  /**
   * Create modal DOM structure
   * @private
   */
  _createModal() {
    // Create modal container
    this.modal = document.createElement('div');
    this.modal.className = this.options.className;

    // Create close button
    this.closeButton = document.createElement('button');
    this.closeButton.className = 'modal-close';
    this.closeButton.innerHTML = '×';
    this.closeButton.addEventListener('click', this._handleCloseClick);

    // Add to modal
    this.modal.appendChild(this.closeButton);

    // Add overlay click handler
    if (this.options.closeOnOverlayClick) {
      this.modal.addEventListener('click', this._handleOverlayClick);
    }

    // Add to body
    document.body.appendChild(this.modal);
  }

  /**
   * Open modal with content
   * @param {HTMLElement|string} content - Content to display
   */
  open(content) {
    if (this.isOpen) return;

    // Set content
    if (content) {
      this.setContent(content);
    }

    // Show modal
    this.modal.classList.add('active');
    this.isOpen = true;

    // Add escape key listener
    if (this.options.closeOnEscape) {
      document.addEventListener('keydown', this._handleEscape);
    }

    // Emit open event
    this._emit('open');
  }

  /**
   * Close modal
   */
  close() {
    if (!this.isOpen) return;

    // Hide modal
    this.modal.classList.remove('active');
    this.isOpen = false;

    // Remove escape key listener
    document.removeEventListener('keydown', this._handleEscape);

    // Emit close event
    this._emit('close');
  }

  /**
   * Set modal content
   * @param {HTMLElement|string} content - Content to set
   */
  setContent(content) {
    // Clear existing content (except close button)
    if (this.content) {
      this.content.remove();
    }

    // Add new content
    if (typeof content === 'string') {
      const div = document.createElement('div');
      div.className = 'modal-content';
      div.innerHTML = content;
      this.content = div;
    } else if (content instanceof HTMLElement) {
      this.content = content;
    }

    if (this.content) {
      this.modal.appendChild(this.content);
    }
  }

  /**
   * Get modal content
   * @returns {HTMLElement|null}
   */
  getContent() {
    return this.content;
  }

  /**
   * Toggle modal open/closed
   */
  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  /**
   * Check if modal is open
   * @returns {boolean}
   */
  isModalOpen() {
    return this.isOpen;
  }

  /**
   * Add event listener
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(handler);
  }

  /**
   * Remove event listener
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  off(event, handler) {
    if (!this.listeners.has(event)) return;

    const handlers = this.listeners.get(event);
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }

  /**
   * Emit event
   * @private
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  _emit(event, data) {
    if (!this.listeners.has(event)) return;

    this.listeners.get(event).forEach(handler => {
      handler(data);
    });
  }

  /**
   * Handle escape key press
   * @private
   * @param {KeyboardEvent} e - Keyboard event
   */
  _handleEscape(e) {
    if (e.key === 'Escape') {
      this.close();
    }
  }

  /**
   * Handle overlay click
   * @private
   * @param {MouseEvent} e - Mouse event
   */
  _handleOverlayClick(e) {
    if (e.target === this.modal) {
      this.close();
    }
  }

  /**
   * Handle close button click
   * @private
   */
  _handleCloseClick() {
    this.close();
  }

  /**
   * Show modal (alias for open)
   */
  show() {
    this.open();
  }

  /**
   * Hide modal (alias for close)
   */
  hide() {
    this.close();
  }

  /**
   * Destroy modal and clean up
   */
  destroy() {
    // Close if open
    if (this.isOpen) {
      this.close();
    }

    // Remove event listeners
    this.closeButton?.removeEventListener('click', this._handleCloseClick);
    this.modal?.removeEventListener('click', this._handleOverlayClick);
    document.removeEventListener('keydown', this._handleEscape);

    // Clear listeners
    this.listeners.clear();

    // Remove from DOM
    this.modal?.remove();

    // Clear references
    this.modal = null;
    this.closeButton = null;
    this.content = null;
  }

  /**
   * Get modal element
   * @returns {HTMLElement|null}
   */
  getElement() {
    return this.modal;
  }

  /**
   * Set close button text
   * @param {string} text - Button text
   */
  setCloseButtonText(text) {
    if (this.closeButton) {
      this.closeButton.innerHTML = text;
    }
  }

  /**
   * Hide close button
   */
  hideCloseButton() {
    if (this.closeButton) {
      this.closeButton.style.display = 'none';
    }
  }

  /**
   * Show close button
   */
  showCloseButton() {
    if (this.closeButton) {
      this.closeButton.style.display = '';
    }
  }
}