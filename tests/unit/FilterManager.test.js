/**
 * Unit tests for FilterManager class
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { FilterManager } from '@core/FilterManager.js';

describe('FilterManager', () => {
  let filterManager;
  let mockItems;
  let renderCallback;

  beforeEach(() => {
    renderCallback = vi.fn();
    filterManager = new FilterManager({
      renderCallback
    });

    mockItems = [
      { id: 1, title: 'Item 1', category: 'work', tags: ['javascript', 'web'] },
      { id: 2, title: 'Item 2', category: 'personal', tags: ['react', 'frontend'] },
      { id: 3, title: 'Item 3', category: 'work', tags: ['backend', 'api'] },
      { id: 4, title: 'Item 4', category: 'hobby', tags: ['game', 'unity'] },
      { id: 5, title: 'Item 5', category: 'personal', tags: ['mobile', 'ios'] }
    ];
  });

  afterEach(() => {
    if (filterManager) {
      filterManager.destroy();
    }
  });

  describe('constructor', () => {
    it('should create instance with default options', () => {
      expect(filterManager.options.defaultFilter).toBe('all');
      expect(filterManager.options.renderCallback).toBe(renderCallback);
    });

    it('should merge custom options', () => {
      const customFilterManager = new FilterManager({
        defaultFilter: 'work',
        customOption: 'test'
      });

      expect(customFilterManager.options.defaultFilter).toBe('work');
      expect(customFilterManager.options.customOption).toBe('test');

      customFilterManager.destroy();
    });

    it('should initialize properties correctly', () => {
      expect(filterManager.allItems).toEqual([]);
      expect(filterManager.filteredItems).toEqual([]);
      expect(filterManager.activeFilter).toBe('all');
      expect(filterManager.activeCategory).toBe(null);
      expect(filterManager.filterButtons).toEqual([]);
      expect(filterManager.listeners).toBeInstanceOf(Map);
    });
  });

  describe('item management', () => {
    it('should set items', () => {
      filterManager.setItems(mockItems);

      expect(filterManager.allItems).toEqual(mockItems);
      expect(filterManager.filteredItems).toEqual(mockItems);
    });

    it('should emit itemsChanged event when setting items', () => {
      const handler = vi.fn();
      filterManager.on('itemsChanged', handler);

      filterManager.setItems(mockItems);

      expect(handler).toHaveBeenCalledWith(mockItems);
    });

    it('should get all items', () => {
      filterManager.setItems(mockItems);

      const items = filterManager.getAllItems();

      expect(items).toEqual(mockItems);
      expect(items).not.toBe(mockItems); // Should return a copy
    });

    it('should get filtered items', () => {
      filterManager.setItems(mockItems);

      const items = filterManager.getFilteredItems();

      expect(items).toEqual(mockItems);
      expect(items).not.toBe(mockItems); // Should return a copy
    });
  });

  describe('filtering', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);
    });

    it('should filter by all', () => {
      const result = filterManager.filterBy('all');

      expect(result).toEqual(mockItems);
      expect(filterManager.activeFilter).toBe('all');
      expect(filterManager.activeCategory).toBe(null);
    });

    it('should filter by specific category', () => {
      const result = filterManager.filterBy('work');

      const expectedItems = mockItems.filter(item => item.category === 'work');
      expect(result).toEqual(expectedItems);
      expect(filterManager.activeFilter).toBe('work');
      expect(filterManager.activeCategory).toBe(null);
    });

    it('should call render callback when filtering', () => {
      filterManager.filterBy('work');

      const expectedItems = mockItems.filter(item => item.category === 'work');
      expect(renderCallback).toHaveBeenCalledWith(expectedItems);
    });

    it('should emit filterChanged event', () => {
      const handler = vi.fn();
      filterManager.on('filterChanged', handler);

      const result = filterManager.filterBy('work');

      expect(handler).toHaveBeenCalledWith({
        filter: 'work',
        items: result
      });
    });

    it('should filter by category (from tags)', () => {
      const result = filterManager.filterByCategory('personal');

      const expectedItems = mockItems.filter(item => item.category === 'personal');
      expect(result).toEqual(expectedItems);
      expect(filterManager.activeFilter).toBe('personal');
      expect(filterManager.activeCategory).toBe('personal');
    });

    it('should emit categoryFilterChanged event', () => {
      const handler = vi.fn();
      filterManager.on('categoryFilterChanged', handler);

      const result = filterManager.filterByCategory('personal');

      expect(handler).toHaveBeenCalledWith({
        category: 'personal',
        items: result
      });
    });

    it('should clear filters', () => {
      filterManager.filterBy('work');
      filterManager.clearFilter();

      expect(filterManager.activeFilter).toBe('all');
      expect(filterManager.activeCategory).toBe(null);
      expect(filterManager.filteredItems).toEqual(mockItems);
    });

    it('should emit filterCleared event', () => {
      const handler = vi.fn();
      filterManager.on('filterCleared', handler);

      filterManager.filterBy('work');
      filterManager.clearFilter();

      expect(handler).toHaveBeenCalledWith({
        items: mockItems
      });
    });
  });

  describe('state getters', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);
    });

    it('should get active filter', () => {
      expect(filterManager.getActiveFilter()).toBe('all');

      filterManager.filterBy('work');
      expect(filterManager.getActiveFilter()).toBe('work');
    });

    it('should get active category', () => {
      expect(filterManager.getActiveCategory()).toBe(null);

      filterManager.filterByCategory('personal');
      expect(filterManager.getActiveCategory()).toBe('personal');
    });
  });

  describe('filter button management', () => {
    let buttons;

    beforeEach(() => {
      filterManager.setItems(mockItems);

      // Create mock buttons
      buttons = [
        createMockElement('button', { dataset: { filter: 'all' } }),
        createMockElement('button', { dataset: { filter: 'work' } }),
        createMockElement('button', { dataset: { filter: 'personal' } })
      ];

      buttons.forEach(btn => {
        btn.addEventListener = vi.fn();
        btn.classList = {
          add: vi.fn(),
          remove: vi.fn()
        };
      });
    });

    it('should register filter buttons', () => {
      filterManager.registerFilterButtons(buttons);

      expect(filterManager.filterButtons).toEqual(buttons);
      buttons.forEach(btn => {
        expect(btn.addEventListener).toHaveBeenCalledWith('click', expect.any(Function));
      });
    });

    it('should handle button click events', () => {
      filterManager.registerFilterButtons(buttons);

      // Simulate click on work button
      const workButton = buttons[1];
      const clickHandler = workButton.addEventListener.mock.calls[0][1];
      const mockEvent = {
        target: { dataset: { filter: 'work' } }
      };

      clickHandler(mockEvent);

      expect(filterManager.activeFilter).toBe('work');
    });

    it('should update button states when filtering', () => {
      filterManager.registerFilterButtons(buttons);

      filterManager.filterBy('work');

      // Check that work button gets active class
      expect(buttons[1].classList.add).toHaveBeenCalledWith('active');
      // Check that other buttons have active class removed
      expect(buttons[0].classList.remove).toHaveBeenCalledWith('active');
      expect(buttons[2].classList.remove).toHaveBeenCalledWith('active');
    });
  });

  describe('search functionality', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);
    });

    it('should search by title', () => {
      const result = filterManager.search('Item 1');

      expect(result).toEqual([mockItems[0]]);
    });

    it('should search by category', () => {
      const result = filterManager.search('work');

      const expectedItems = mockItems.filter(item => item.category === 'work');
      expect(result).toEqual(expectedItems);
    });

    it('should search by tags', () => {
      const result = filterManager.search('javascript');

      expect(result).toEqual([mockItems[0]]);
    });

    it('should be case insensitive', () => {
      const result = filterManager.search('WORK');

      const expectedItems = mockItems.filter(item => item.category === 'work');
      expect(result).toEqual(expectedItems);
    });

    it('should return filtered items if query is empty', () => {
      filterManager.filterBy('work');
      const result = filterManager.search('');

      const expectedItems = mockItems.filter(item => item.category === 'work');
      expect(result).toEqual(expectedItems);
    });

    it('should combine search with active filter', () => {
      filterManager.filterBy('work');
      const result = filterManager.search('Item 1');

      expect(result).toEqual([mockItems[0]]);
    });

    it('should emit searchChanged event', () => {
      const handler = vi.fn();
      filterManager.on('searchChanged', handler);

      const result = filterManager.search('javascript');

      expect(handler).toHaveBeenCalledWith({
        query: 'javascript',
        items: result
      });
    });
  });

  describe('sorting functionality', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);
    });

    it('should sort by string field ascending', () => {
      filterManager.sortItems('title', 'asc');

      const expectedOrder = mockItems.sort((a, b) => a.title.localeCompare(b.title));
      expect(filterManager.filteredItems).toEqual(expectedOrder);
    });

    it('should sort by string field descending', () => {
      filterManager.sortItems('title', 'desc');

      const expectedOrder = mockItems.sort((a, b) => b.title.localeCompare(a.title));
      expect(filterManager.filteredItems).toEqual(expectedOrder);
    });

    it('should sort by numeric field', () => {
      filterManager.sortItems('id', 'desc');

      const expectedOrder = mockItems.sort((a, b) => b.id - a.id);
      expect(filterManager.filteredItems).toEqual(expectedOrder);
    });

    it('should emit sortChanged event', () => {
      const handler = vi.fn();
      filterManager.on('sortChanged', handler);

      filterManager.sortItems('title', 'asc');

      expect(handler).toHaveBeenCalledWith({
        sortBy: 'title',
        order: 'asc',
        items: filterManager.filteredItems
      });
    });
  });

  describe('category analysis', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);
    });

    it('should get unique categories', () => {
      const categories = filterManager.getCategories();

      expect(categories).toEqual(['hobby', 'personal', 'work']);
    });

    it('should get category counts', () => {
      const counts = filterManager.getCategoryCounts();

      expect(counts).toEqual({
        all: 5,
        work: 2,
        personal: 2,
        hobby: 1
      });
    });
  });

  describe('active filter UI', () => {
    beforeEach(() => {
      filterManager.setItems(mockItems);

      // Mock DOM elements
      const nav = document.createElement('nav');
      nav.className = 'terminal-nav';
      document.body.appendChild(nav);
    });

    it('should show active filter indicator', () => {
      filterManager.filterByCategory('work');

      const activeFilter = document.getElementById('activeFilter');
      expect(activeFilter).toBeTruthy();
      expect(activeFilter.classList.contains('show')).toBe(true);

      const filterTag = document.getElementById('filterTag');
      expect(filterTag.textContent).toBe('#work');
    });

    it('should hide active filter indicator', () => {
      filterManager.filterByCategory('work');
      filterManager.clearFilter();

      const activeFilter = document.getElementById('activeFilter');
      if (activeFilter) {
        expect(activeFilter.classList.contains('show')).toBe(false);
      }
    });

    it('should handle clear button click', () => {
      filterManager.filterByCategory('work');

      const clearButton = document.querySelector('.clear-filter');
      expect(clearButton).toBeTruthy();

      clearButton.click();

      expect(filterManager.activeFilter).toBe('all');
      expect(filterManager.activeCategory).toBe(null);
    });
  });

  describe('event handling', () => {
    it('should add event listeners', () => {
      const handler = vi.fn();

      filterManager.on('test', handler);

      expect(filterManager.listeners.get('test')).toContain(handler);
    });

    it('should remove event listeners', () => {
      const handler = vi.fn();

      filterManager.on('test', handler);
      filterManager.off('test', handler);

      expect(filterManager.listeners.get('test')).not.toContain(handler);
    });

    it('should handle multiple listeners for same event', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      filterManager.on('test', handler1);
      filterManager.on('test', handler2);

      filterManager._emit('test', 'data');

      expect(handler1).toHaveBeenCalledWith('data');
      expect(handler2).toHaveBeenCalledWith('data');
    });

    it('should handle removing non-existent listeners', () => {
      expect(() => filterManager.off('nonexistent', vi.fn())).not.toThrow();
    });
  });

  describe('destruction and cleanup', () => {
    it('should clean up all resources', () => {
      filterManager.setItems(mockItems);

      // Add some buttons
      const buttons = [
        createMockElement('button', { dataset: { filter: 'all' } }),
        createMockElement('button', { dataset: { filter: 'work' } })
      ];

      buttons.forEach(btn => {
        btn.replaceWith = vi.fn();
      });

      filterManager.registerFilterButtons(buttons);

      // Add event listeners
      const handler = vi.fn();
      filterManager.on('test', handler);

      filterManager.destroy();

      expect(filterManager.allItems).toEqual([]);
      expect(filterManager.filteredItems).toEqual([]);
      expect(filterManager.filterButtons).toEqual([]);
      expect(filterManager.listeners.size).toBe(0);

      // Check buttons were replaced (event listeners removed)
      buttons.forEach(btn => {
        expect(btn.replaceWith).toHaveBeenCalled();
      });
    });

    it('should remove active filter element on destroy', () => {
      filterManager.setItems(mockItems);

      // Create nav element for active filter
      const nav = document.createElement('nav');
      nav.className = 'terminal-nav';
      document.body.appendChild(nav);

      filterManager.filterByCategory('work');

      const activeFilter = document.getElementById('activeFilter');
      expect(activeFilter).toBeTruthy();

      filterManager.destroy();

      expect(document.getElementById('activeFilter')).toBe(null);
    });
  });

  describe('edge cases', () => {
    it('should handle filtering with no items', () => {
      const result = filterManager.filterBy('work');

      expect(result).toEqual([]);
    });

    it('should handle search with no items', () => {
      const result = filterManager.search('test');

      expect(result).toEqual([]);
    });

    it('should handle items without required properties', () => {
      const incompleteItems = [
        { id: 1 }, // no title, category, tags
        { id: 2, title: 'Item 2' }, // no category, tags
        { id: 3, title: 'Item 3', category: 'work' } // no tags
      ];

      filterManager.setItems(incompleteItems);

      expect(() => filterManager.search('test')).not.toThrow();
      expect(() => filterManager.filterBy('work')).not.toThrow();
      expect(() => filterManager.getCategories()).not.toThrow();
    });

    it('should handle null/undefined render callback', () => {
      const noCallbackFilter = new FilterManager({ renderCallback: null });
      noCallbackFilter.setItems(mockItems);

      expect(() => noCallbackFilter.filterBy('all')).not.toThrow();

      noCallbackFilter.destroy();
    });
  });
});