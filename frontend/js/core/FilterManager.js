/**
 * FilterManager - Manages filtering logic for galleries
 * Handles category filtering, active filters, and state management
 */

export class FilterManager {
  constructor(options = {}) {
    this.options = {
      defaultFilter: 'all',
      renderCallback: null,
      ...options
    };

    this.allItems = [];
    this.filteredItems = [];
    this.activeFilter = this.options.defaultFilter;
    this.activeCategory = null;
    this.filterButtons = [];
    this.listeners = new Map();
  }

  /**
   * Initialize with items
   * @param {Array} items - Array of items to filter
   */
  setItems(items) {
    this.allItems = [...items];
    this.filteredItems = [...items];
    this._emit('itemsChanged', this.filteredItems);
  }

  /**
   * Get all items
   * @returns {Array}
   */
  getAllItems() {
    return [...this.allItems];
  }

  /**
   * Get filtered items
   * @returns {Array}
   */
  getFilteredItems() {
    return [...this.filteredItems];
  }

  /**
   * Filter items by category
   * @param {string} filter - Filter category
   * @returns {Array} Filtered items
   */
  filterBy(filter) {
    this.activeFilter = filter;
    this.activeCategory = null;  // Clear category filter

    if (filter === 'all') {
      this.filteredItems = [...this.allItems];
    } else {
      this.filteredItems = this.allItems.filter(item =>
        item.category === filter
      );
    }

    // Update button states
    this._updateButtonStates();

    // Trigger render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(this.filteredItems);
    }

    // Emit event
    this._emit('filterChanged', {
      filter: this.activeFilter,
      items: this.filteredItems
    });

    return this.filteredItems;
  }

  /**
   * Filter by specific category (from tags)
   * @param {string} category - Category name
   * @returns {Array} Filtered items
   */
  filterByCategory(category) {
    this.activeCategory = category;
    this.activeFilter = category;

    this.filteredItems = this.allItems.filter(item =>
      item.category === category
    );

    // Update UI
    this._showActiveFilter(category);
    this._updateButtonStates();

    // Trigger render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(this.filteredItems);
    }

    // Emit event
    this._emit('categoryFilterChanged', {
      category: this.activeCategory,
      items: this.filteredItems
    });

    return this.filteredItems;
  }

  /**
   * Clear all filters
   */
  clearFilter() {
    this.activeFilter = 'all';
    this.activeCategory = null;
    this.filteredItems = [...this.allItems];

    // Update UI
    this._hideActiveFilter();
    this._updateButtonStates();

    // Trigger render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(this.filteredItems);
    }

    // Emit event
    this._emit('filterCleared', {
      items: this.filteredItems
    });
  }

  /**
   * Get active filter
   * @returns {string}
   */
  getActiveFilter() {
    return this.activeFilter;
  }

  /**
   * Get active category
   * @returns {string|null}
   */
  getActiveCategory() {
    return this.activeCategory;
  }

  /**
   * Register filter buttons
   * @param {NodeList|Array} buttons - Filter button elements
   */
  registerFilterButtons(buttons) {
    this.filterButtons = Array.from(buttons);

    this.filterButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const filter = e.target.dataset.filter;
        if (filter) {
          this.filterBy(filter);
        }
      });
    });
  }

  /**
   * Update filter button states
   * @private
   */
  _updateButtonStates() {
    this.filterButtons.forEach(btn => {
      const filter = btn.dataset.filter;

      if (filter === this.activeFilter ||
          (this.activeCategory && filter === this.activeCategory)) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });
  }

  /**
   * Show active filter indicator
   * @private
   * @param {string} category - Category name
   */
  _showActiveFilter(category) {
    let activeFilter = document.getElementById('activeFilter');

    if (!activeFilter) {
      activeFilter = document.createElement('div');
      activeFilter.id = 'activeFilter';
      activeFilter.className = 'active-filter';
      activeFilter.innerHTML = `
        Filtering by: <span id="filterTag"></span>
        <button class="clear-filter">Clear</button>
      `;

      // Add clear handler
      const clearBtn = activeFilter.querySelector('.clear-filter');
      clearBtn.addEventListener('click', () => this.clearFilter());

      // Insert into page
      const nav = document.querySelector('.terminal-nav');
      if (nav) {
        nav.parentElement.insertBefore(activeFilter, nav.nextSibling);
      }
    }

    const filterTag = document.getElementById('filterTag');
    if (filterTag) {
      filterTag.textContent = `#${category}`;
    }

    activeFilter.classList.add('show');
  }

  /**
   * Hide active filter indicator
   * @private
   */
  _hideActiveFilter() {
    const activeFilter = document.getElementById('activeFilter');
    if (activeFilter) {
      activeFilter.classList.remove('show');
    }
  }

  /**
   * Search items
   * @param {string} query - Search query
   * @returns {Array} Filtered items
   */
  search(query) {
    if (!query) {
      return this.filterBy(this.activeFilter);
    }

    const searchTerm = query.toLowerCase();
    const baseItems = this.activeFilter === 'all'
      ? this.allItems
      : this.allItems.filter(item => item.category === this.activeFilter);

    this.filteredItems = baseItems.filter(item => {
      const title = (item.title || '').toLowerCase();
      const category = (item.category || '').toLowerCase();
      const tags = (item.tags || []).map(t => t.toLowerCase());

      return title.includes(searchTerm) ||
             category.includes(searchTerm) ||
             tags.some(tag => tag.includes(searchTerm));
    });

    // Trigger render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(this.filteredItems);
    }

    // Emit event
    this._emit('searchChanged', {
      query,
      items: this.filteredItems
    });

    return this.filteredItems;
  }

  /**
   * Sort items
   * @param {string} sortBy - Sort field
   * @param {string} order - Sort order (asc/desc)
   */
  sortItems(sortBy, order = 'asc') {
    const multiplier = order === 'desc' ? -1 : 1;

    this.filteredItems.sort((a, b) => {
      const aVal = a[sortBy];
      const bVal = b[sortBy];

      if (typeof aVal === 'string') {
        return aVal.localeCompare(bVal) * multiplier;
      }

      return (aVal - bVal) * multiplier;
    });

    // Trigger render callback
    if (this.options.renderCallback) {
      this.options.renderCallback(this.filteredItems);
    }

    // Emit event
    this._emit('sortChanged', {
      sortBy,
      order,
      items: this.filteredItems
    });
  }

  /**
   * Get available categories
   * @returns {Array} Unique categories
   */
  getCategories() {
    const categories = new Set();
    this.allItems.forEach(item => {
      if (item.category) {
        categories.add(item.category);
      }
    });
    return Array.from(categories).sort();
  }

  /**
   * Get item count by category
   * @returns {Object} Category counts
   */
  getCategoryCounts() {
    const counts = {};
    counts.all = this.allItems.length;

    this.allItems.forEach(item => {
      if (item.category) {
        counts[item.category] = (counts[item.category] || 0) + 1;
      }
    });

    return counts;
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
   * Destroy and clean up
   */
  destroy() {
    // Remove button event listeners
    this.filterButtons.forEach(btn => {
      btn.replaceWith(btn.cloneNode(true));
    });

    // Clear arrays
    this.allItems = [];
    this.filteredItems = [];
    this.filterButtons = [];

    // Clear listeners
    this.listeners.clear();

    // Remove active filter element
    const activeFilter = document.getElementById('activeFilter');
    if (activeFilter) {
      activeFilter.remove();
    }
  }
}