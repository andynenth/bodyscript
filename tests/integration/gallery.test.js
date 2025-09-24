/**
 * Integration tests for Gallery functionality
 * Tests the interaction between core components
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { VideoPlayer } from '@core/VideoPlayer.js';
import { Modal } from '@core/Modal.js';
import { FilterManager } from '@core/FilterManager.js';

describe('Gallery Integration Tests', () => {
  let container;
  let videoPlayer;
  let modal;
  let filterManager;
  let mockData;

  beforeEach(() => {
    // Create test container
    container = createMockContainer();

    // Create instances
    videoPlayer = new VideoPlayer();
    modal = new Modal();
    filterManager = new FilterManager();

    // Mock gallery data
    mockData = [
      {
        id: 1,
        title: 'Research Video 1',
        category: 'research',
        tags: ['body-pose', 'walking'],
        thumbnail: '/api/thumbnails/1.jpg',
        video: '/api/videos/1.mp4',
        duration: 30,
        uploaded: '2023-01-01'
      },
      {
        id: 2,
        title: 'Personal Video 1',
        category: 'personal',
        tags: ['dance', 'movement'],
        thumbnail: '/api/thumbnails/2.jpg',
        video: '/api/videos/2.mp4',
        duration: 45,
        uploaded: '2023-01-02'
      },
      {
        id: 3,
        title: 'Research Video 2',
        category: 'research',
        tags: ['hand-pose', 'gestures'],
        thumbnail: '/api/thumbnails/3.jpg',
        video: '/api/videos/3.mp4',
        duration: 60,
        uploaded: '2023-01-03'
      }
    ];
  });

  afterEach(() => {
    videoPlayer?.destroy();
    modal?.destroy();
    filterManager?.destroy();
  });

  describe('Gallery Initialization and Data Loading', () => {
    it('should load and display gallery items', () => {
      filterManager.setItems(mockData);

      const allItems = filterManager.getAllItems();
      const filteredItems = filterManager.getFilteredItems();

      expect(allItems).toHaveLength(3);
      expect(filteredItems).toHaveLength(3);
      expect(allItems[0].title).toBe('Research Video 1');
      expect(allItems[1].category).toBe('personal');
    });

    it('should calculate category statistics', () => {
      filterManager.setItems(mockData);

      const categories = filterManager.getCategories();
      const counts = filterManager.getCategoryCounts();

      expect(categories).toEqual(['personal', 'research']);
      expect(counts.all).toBe(3);
      expect(counts.research).toBe(2);
      expect(counts.personal).toBe(1);
    });
  });

  describe('Video Player Integration', () => {
    it('should create video element for gallery item', async () => {
      const videoSrc = mockData[0].video;

      await videoPlayer.createPreviewElement(videoSrc, container);

      expect(videoPlayer.video).toBeTruthy();
      expect(videoPlayer.source.src).toBe('http://localhost:8000/api/videos/1.mp4');
      expect(container.contains(videoPlayer.video)).toBe(true);
    });

    it('should handle video preview lifecycle', async () => {
      const videoSrc = mockData[0].video;

      await videoPlayer.createPreviewElement(videoSrc, container);

      // Test show/hide functionality
      videoPlayer.show();
      expect(videoPlayer.video.style.display).toBe('block');

      videoPlayer.hide();
      expect(videoPlayer.video.style.display).toBe('none');

      // Test play/pause functionality
      await videoPlayer.play();
      expect(videoPlayer.video.play).toHaveBeenCalled();
      expect(videoPlayer.video.style.display).toBe('block');

      videoPlayer.pause();
      expect(videoPlayer.video.pause).toHaveBeenCalled();
      expect(videoPlayer.video.style.display).toBe('none');
    });

    it('should handle video switching', async () => {
      // Create initial video
      await videoPlayer.createPreviewElement(mockData[0].video, container);
      const initialSrc = videoPlayer.source.src;

      // Switch to different video
      videoPlayer.setSrc(mockData[1].video);

      expect(videoPlayer.source.src).not.toBe(initialSrc);
      expect(videoPlayer.source.src).toBe('http://localhost:8000/api/videos/2.mp4');
      expect(videoPlayer.video.load).toHaveBeenCalled();
    });
  });

  describe('Modal Integration', () => {
    it('should display video details in modal', () => {
      const item = mockData[0];
      const modalContent = `
        <div class="video-details">
          <h2>${item.title}</h2>
          <p>Category: ${item.category}</p>
          <p>Duration: ${item.duration}s</p>
          <p>Tags: ${item.tags.join(', ')}</p>
        </div>
      `;

      modal.open(modalContent);

      expect(modal.isOpen).toBe(true);
      expect(modal.content.innerHTML).toContain(item.title);
      expect(modal.content.innerHTML).toContain(item.category);
      expect(modal.content.innerHTML).toContain('30s');
    });

    it('should integrate video player in modal', async () => {
      const item = mockData[0];

      // Create modal content with video container
      const modalContent = document.createElement('div');
      modalContent.className = 'modal-video-content';
      modalContent.innerHTML = `
        <h2>${item.title}</h2>
        <div class="video-container" id="modal-video-container"></div>
        <div class="video-info">
          <p>Category: ${item.category}</p>
          <p>Duration: ${item.duration}s</p>
        </div>
      `;

      modal.open(modalContent);

      // Add video player to modal
      const videoContainer = modal.content.querySelector('#modal-video-container');
      await videoPlayer.createPreviewElement(item.video, videoContainer);

      expect(modal.isOpen).toBe(true);
      expect(videoContainer.contains(videoPlayer.video)).toBe(true);
      expect(videoPlayer.source.src).toContain('videos/1.mp4');
    });

    it('should clean up video when modal closes', async () => {
      const item = mockData[0];
      await videoPlayer.createPreviewElement(item.video, container);

      modal.open('<div>Test content</div>');
      await videoPlayer.play();

      // Close modal should pause video
      modal.close();
      videoPlayer.pause();

      expect(modal.isOpen).toBe(false);
      expect(videoPlayer.video.pause).toHaveBeenCalled();
    });
  });

  describe('Filter Integration', () => {
    beforeEach(() => {
      filterManager.setItems(mockData);
    });

    it('should filter gallery items by category', () => {
      const researchItems = filterManager.filterBy('research');

      expect(researchItems).toHaveLength(2);
      expect(researchItems.every(item => item.category === 'research')).toBe(true);
      expect(filterManager.getActiveFilter()).toBe('research');
    });

    it('should search across multiple fields', () => {
      // Search by title
      let results = filterManager.search('Research Video 1');
      expect(results).toHaveLength(1);
      expect(results[0].id).toBe(1);

      // Search by category
      results = filterManager.search('personal');
      expect(results).toHaveLength(1);
      expect(results[0].category).toBe('personal');

      // Search by tag
      results = filterManager.search('dance');
      expect(results).toHaveLength(1);
      expect(results[0].tags).toContain('dance');
    });

    it('should combine filtering and searching', () => {
      // First filter by category
      filterManager.filterBy('research');

      // Then search within filtered results
      const results = filterManager.search('walking');

      expect(results).toHaveLength(1);
      expect(results[0].id).toBe(1);
      expect(results[0].tags).toContain('walking');
    });

    it('should sort filtered results', () => {
      filterManager.filterBy('research');
      filterManager.sortItems('title', 'asc');

      const items = filterManager.getFilteredItems();

      expect(items[0].title).toBe('Research Video 1');
      expect(items[1].title).toBe('Research Video 2');
    });

    it('should handle filter button interactions', () => {
      // Create mock filter buttons
      const buttons = [
        createMockElement('button', { dataset: { filter: 'all' } }),
        createMockElement('button', { dataset: { filter: 'research' } }),
        createMockElement('button', { dataset: { filter: 'personal' } })
      ];

      // Mock classList methods
      buttons.forEach(btn => {
        btn.classList = {
          add: vi.fn(),
          remove: vi.fn()
        };
        btn.addEventListener = vi.fn();
      });

      filterManager.registerFilterButtons(buttons);

      // Simulate clicking research button
      const researchButton = buttons[1];
      const clickHandler = researchButton.addEventListener.mock.calls[0][1];
      const mockEvent = {
        target: { dataset: { filter: 'research' } }
      };

      clickHandler(mockEvent);

      expect(filterManager.getActiveFilter()).toBe('research');
      expect(filterManager.getFilteredItems()).toHaveLength(2);
    });
  });

  describe('Component Event Communication', () => {
    it('should emit and handle filter change events', () => {
      const filterHandler = vi.fn();
      const searchHandler = vi.fn();

      filterManager.on('filterChanged', filterHandler);
      filterManager.on('searchChanged', searchHandler);
      filterManager.setItems(mockData);

      // Test filter change event
      filterManager.filterBy('research');

      expect(filterHandler).toHaveBeenCalledWith({
        filter: 'research',
        items: expect.any(Array)
      });

      // Test search change event
      filterManager.search('Video 1');

      expect(searchHandler).toHaveBeenCalledWith({
        query: 'Video 1',
        items: expect.any(Array)
      });
    });

    it('should coordinate video player and modal events', async () => {
      const modalOpenHandler = vi.fn();
      const modalCloseHandler = vi.fn();

      modal.on('open', modalOpenHandler);
      modal.on('close', modalCloseHandler);

      // Simulate opening modal with video
      modal.open('<div class="video-container"></div>');
      expect(modalOpenHandler).toHaveBeenCalled();

      // Add video to modal
      const videoContainer = modal.content.querySelector('.video-container');
      await videoPlayer.createPreviewElement(mockData[0].video, videoContainer);

      // Simulate closing modal
      modal.close();
      expect(modalCloseHandler).toHaveBeenCalled();

      // Video should be cleaned up when modal closes
      videoPlayer.pause();
      expect(videoPlayer.video.pause).toHaveBeenCalled();
    });
  });

  describe('Error Handling Integration', () => {
    it('should handle video loading errors gracefully', async () => {
      // Mock video creation to fail
      const originalCreateElement = document.createElement;
      document.createElement = vi.fn().mockImplementation((tag) => {
        if (tag === 'video') {
          throw new Error('Video creation failed');
        }
        return originalCreateElement.call(document, tag);
      });

      try {
        await videoPlayer.createPreviewElement('/invalid-video.mp4', container);
      } catch (error) {
        expect(error.message).toBe('Video creation failed');
      }

      expect(videoPlayer.video).toBe(null);

      // Restore original function
      document.createElement = originalCreateElement;
    });

    it('should handle filter operations with invalid data', () => {
      const invalidData = [
        { id: 1 }, // Missing required fields
        { id: 2, title: 'Test' }, // Missing category
        null, // Invalid item
        undefined // Invalid item
      ].filter(Boolean); // Remove null/undefined

      filterManager.setItems(invalidData);

      // Should not throw errors
      expect(() => filterManager.filterBy('test')).not.toThrow();
      expect(() => filterManager.search('test')).not.toThrow();
      expect(() => filterManager.getCategories()).not.toThrow();
    });

    it('should handle modal operations with invalid content', () => {
      // Should handle null content
      expect(() => modal.setContent(null)).not.toThrow();

      // Should handle undefined content
      expect(() => modal.setContent(undefined)).not.toThrow();

      // Should handle non-string, non-element content
      expect(() => modal.setContent(123)).not.toThrow();
    });
  });

  describe('Performance and Memory Management', () => {
    it('should properly clean up all components', () => {
      filterManager.setItems(mockData);
      modal.open('<div>Test content</div>');

      // Add event listeners
      const filterHandler = vi.fn();
      const modalHandler = vi.fn();

      filterManager.on('filterChanged', filterHandler);
      modal.on('open', modalHandler);

      // Destroy all components
      filterManager.destroy();
      modal.destroy();

      // Check that resources are cleaned up
      expect(filterManager.allItems).toHaveLength(0);
      expect(filterManager.listeners.size).toBe(0);
      expect(modal.modal).toBe(null);
      expect(modal.listeners.size).toBe(0);
    });

    it('should handle rapid state changes without memory leaks', async () => {
      filterManager.setItems(mockData);

      // Rapid filter changes
      for (let i = 0; i < 10; i++) {
        filterManager.filterBy(i % 2 === 0 ? 'research' : 'personal');
        filterManager.search(`Video ${i}`);
      }

      // Should maintain consistent state
      expect(filterManager.getAllItems()).toHaveLength(3);

      // Rapid modal open/close
      for (let i = 0; i < 5; i++) {
        modal.open(`<div>Content ${i}</div>`);
        modal.close();
      }

      expect(modal.isOpen).toBe(false);
    });

    it('should handle video player lifecycle properly', async () => {
      // Create and destroy multiple video instances
      for (let i = 0; i < 3; i++) {
        const player = new VideoPlayer();
        await player.createPreviewElement(mockData[i].video, container);

        // Verify creation
        expect(player.video).toBeTruthy();

        // Clean up
        player.destroy();

        // Verify cleanup
        expect(player.video).toBe(null);
      }

      // Container should be clean
      expect(container.children.length).toBe(0);
    });
  });
});