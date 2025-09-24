/**
 * Unit tests for VideoPlayer class
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { VideoPlayer } from '@core/VideoPlayer.js';

describe('VideoPlayer', () => {
  let player;
  let container;

  beforeEach(() => {
    container = createMockContainer();
    player = new VideoPlayer();
  });

  afterEach(() => {
    if (player) {
      player.destroy();
    }
  });

  describe('constructor', () => {
    it('should create instance with default options', () => {
      expect(player.options.muted).toBe(true);
      expect(player.options.loop).toBe(true);
      expect(player.options.playsInline).toBe(true);
      expect(player.options.preload).toBe('auto');
    });

    it('should merge custom options', () => {
      const customPlayer = new VideoPlayer({
        muted: false,
        loop: false,
        customProp: 'test'
      });

      expect(customPlayer.options.muted).toBe(false);
      expect(customPlayer.options.loop).toBe(false);
      expect(customPlayer.options.playsInline).toBe(true); // default
      expect(customPlayer.options.customProp).toBe('test');

      customPlayer.destroy();
    });

    it('should initialize properties correctly', () => {
      expect(player.video).toBe(null);
      expect(player.source).toBe(null);
      expect(player.container).toBe(null);
      expect(player.isCreating).toBe(false);
      expect(player.listeners).toBeInstanceOf(Map);
    });
  });

  describe('createPreviewElement', () => {
    it('should create video element with correct properties', async () => {
      const src = '/api/test-video.mp4';

      await player.createPreviewElement(src, container);

      expect(player.video).toBeTruthy();
      expect(player.video.tagName).toBe('VIDEO');
      expect(player.video.className).toBe('preview-video');
      expect(player.video.muted).toBe(true);
      expect(player.video.loop).toBe(true);
      expect(player.video.playsInline).toBe(true);
      expect(container.contains(player.video)).toBe(true);
    });

    it('should create source element with resolved URL', async () => {
      const src = '/api/test-video.mp4';

      await player.createPreviewElement(src, container);

      expect(player.source).toBeTruthy();
      expect(player.source.tagName).toBe('SOURCE');
      expect(player.source.src).toBe('http://localhost:8000/api/test-video.mp4');
      expect(player.source.type).toBe('video/mp4');
      expect(player.video.contains(player.source)).toBe(true);
    });

    it('should apply correct styles to video element', async () => {
      const src = '/api/test-video.mp4';

      await player.createPreviewElement(src, container);

      const styles = player.video.style;
      expect(styles.display).toBe('none');
      expect(styles.position).toBe('absolute');
      expect(styles.top).toBe('0px');
      expect(styles.left).toBe('0px');
      expect(styles.width).toBe('100%');
      expect(styles.height).toBe('100%');
      expect(styles.objectFit).toBe('cover');
      expect(styles.zIndex).toBe('10');
    });

    it('should return existing video if already created', async () => {
      const src = '/api/test-video.mp4';

      const video1 = await player.createPreviewElement(src, container);
      const video2 = await player.createPreviewElement(src, container);

      expect(video1).toBe(video2);
      expect(video1).toBe(player.video);
    });

    it('should prevent concurrent creation', async () => {
      const src = '/api/test-video.mp4';

      const promise1 = player.createPreviewElement(src, container);
      const promise2 = player.createPreviewElement(src, container);

      const [video1, video2] = await Promise.all([promise1, promise2]);
      expect(video1).toBe(video2);
    });

    it('should handle creation errors', async () => {
      const originalCreateElement = document.createElement;
      document.createElement = vi.fn().mockImplementation((tag) => {
        if (tag === 'video') {
          throw new Error('Video creation failed');
        }
        return originalCreateElement.call(document, tag);
      });

      await expect(player.createPreviewElement('/test.mp4', container))
        .rejects.toThrow('Video creation failed');

      expect(player.isCreating).toBe(false);
      expect(player.video).toBe(null);

      document.createElement = originalCreateElement;
    });
  });

  describe('URL resolution', () => {
    it('should resolve API URLs correctly', () => {
      const url = player._resolveVideoUrl('/api/video.mp4');
      expect(url).toBe('http://localhost:8000/api/video.mp4');
    });

    it('should not modify non-API URLs', () => {
      const url = player._resolveVideoUrl('https://example.com/video.mp4');
      expect(url).toBe('https://example.com/video.mp4');
    });

    it('should handle empty URLs', () => {
      const url = player._resolveVideoUrl('');
      expect(url).toBe('');
    });

    it('should handle null/undefined URLs', () => {
      expect(player._resolveVideoUrl(null)).toBe('');
      expect(player._resolveVideoUrl(undefined)).toBe('');
    });
  });

  describe('playback controls', () => {
    beforeEach(async () => {
      await player.createPreviewElement('/api/test.mp4', container);
    });

    describe('play', () => {
      it('should play video and show element', async () => {
        await player.play();

        expect(player.video.style.display).toBe('block');
        expect(player.video.currentTime).toBe(0);
        expect(player.video.play).toHaveBeenCalled();
      });

      it('should throw error if video not created', async () => {
        const emptyPlayer = new VideoPlayer();

        await expect(emptyPlayer.play())
          .rejects.toThrow('Video element not created');

        emptyPlayer.destroy();
      });

      it('should handle play errors', async () => {
        player.video.play = vi.fn().mockRejectedValue(new Error('Play failed'));

        await expect(player.play()).rejects.toThrow('Play failed');
        expect(player.video.style.display).toBe('none');
      });
    });

    describe('pause', () => {
      it('should pause video and hide element', () => {
        player.pause();

        expect(player.video.pause).toHaveBeenCalled();
        expect(player.video.currentTime).toBe(0);
        expect(player.video.style.display).toBe('none');
      });

      it('should handle pause when video not created', () => {
        const emptyPlayer = new VideoPlayer();

        expect(() => emptyPlayer.pause()).not.toThrow();

        emptyPlayer.destroy();
      });
    });

    describe('show/hide', () => {
      it('should show video element', () => {
        player.show();
        expect(player.video.style.display).toBe('block');
      });

      it('should hide video element', () => {
        player.hide();
        expect(player.video.style.display).toBe('none');
      });
    });
  });

  describe('source management', () => {
    beforeEach(async () => {
      await player.createPreviewElement('/api/test.mp4', container);
    });

    it('should update video source', () => {
      const newSrc = '/api/new-video.mp4';

      player.setSrc(newSrc);

      expect(player.source.src).toBe('http://localhost:8000/api/new-video.mp4');
      expect(player.video.load).toHaveBeenCalled();
    });

    it('should handle setSrc when video not created', () => {
      const emptyPlayer = new VideoPlayer();

      expect(() => emptyPlayer.setSrc('/test.mp4')).not.toThrow();

      emptyPlayer.destroy();
    });
  });

  describe('event handling', () => {
    beforeEach(async () => {
      await player.createPreviewElement('/api/test.mp4', container);
    });

    it('should add event listeners', () => {
      const handler = vi.fn();
      const addEventListenerSpy = vi.spyOn(player.video, 'addEventListener');

      player.on('loadstart', handler);

      expect(addEventListenerSpy).toHaveBeenCalledWith('loadstart', handler);
      expect(player.listeners.get('loadstart')).toContain(handler);
    });

    it('should remove event listeners', () => {
      const handler = vi.fn();
      const removeEventListenerSpy = vi.spyOn(player.video, 'removeEventListener');

      player.on('loadstart', handler);
      player.off('loadstart', handler);

      expect(removeEventListenerSpy).toHaveBeenCalledWith('loadstart', handler);
      expect(player.listeners.get('loadstart')).not.toContain(handler);
    });

    it('should track multiple handlers for same event', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      player.on('loadstart', handler1);
      player.on('loadstart', handler2);

      const handlers = player.listeners.get('loadstart');
      expect(handlers).toContain(handler1);
      expect(handlers).toContain(handler2);
      expect(handlers.length).toBe(2);
    });

    it('should handle event operations when video not created', () => {
      const emptyPlayer = new VideoPlayer();

      expect(() => emptyPlayer.on('loadstart', vi.fn())).not.toThrow();
      expect(() => emptyPlayer.off('loadstart', vi.fn())).not.toThrow();

      emptyPlayer.destroy();
    });
  });

  describe('state queries', () => {
    beforeEach(async () => {
      await player.createPreviewElement('/api/test.mp4', container);
    });

    it('should return playing state', () => {
      player.video.paused = false;
      player.video.ended = false;
      expect(player.isPlaying()).toBe(true);

      player.video.paused = true;
      expect(player.isPlaying()).toBe(false);

      player.video.paused = false;
      player.video.ended = true;
      expect(player.isPlaying()).toBe(false);
    });

    it('should return video element', () => {
      expect(player.getElement()).toBe(player.video);
    });

    it('should return duration', () => {
      player.video.duration = 120;
      expect(player.getDuration()).toBe(120);
    });

    it('should return current time', () => {
      player.video.currentTime = 45;
      expect(player.getCurrentTime()).toBe(45);
    });

    it('should handle state queries when video not created', () => {
      const emptyPlayer = new VideoPlayer();

      expect(emptyPlayer.isPlaying()).toBe(false);
      expect(emptyPlayer.getElement()).toBe(null);
      expect(emptyPlayer.getDuration()).toBe(0);
      expect(emptyPlayer.getCurrentTime()).toBe(0);

      emptyPlayer.destroy();
    });
  });

  describe('time control', () => {
    beforeEach(async () => {
      await player.createPreviewElement('/api/test.mp4', container);
    });

    it('should set current time', () => {
      player.setCurrentTime(30);
      expect(player.video.currentTime).toBe(30);
    });

    it('should handle setCurrentTime when video not created', () => {
      const emptyPlayer = new VideoPlayer();

      expect(() => emptyPlayer.setCurrentTime(30)).not.toThrow();

      emptyPlayer.destroy();
    });
  });

  describe('destroy', () => {
    it('should clean up all resources', async () => {
      await player.createPreviewElement('/api/test.mp4', container);

      const handler = vi.fn();
      player.on('loadstart', handler);

      const videoElement = player.video;
      const removeEventListenerSpy = vi.spyOn(videoElement, 'removeEventListener');

      player.destroy();

      expect(player.video).toBe(null);
      expect(player.source).toBe(null);
      expect(player.container).toBe(null);
      expect(player.isCreating).toBe(false);
      expect(player.listeners.size).toBe(0);
      expect(removeEventListenerSpy).toHaveBeenCalledWith('loadstart', handler);
      expect(container.contains(videoElement)).toBe(false);
    });

    it('should handle destroy when video not created', () => {
      expect(() => player.destroy()).not.toThrow();
    });

    it('should pause video before destroying', async () => {
      await player.createPreviewElement('/api/test.mp4', container);

      const pauseSpy = vi.spyOn(player, 'pause');

      player.destroy();

      expect(pauseSpy).toHaveBeenCalled();
    });
  });
});