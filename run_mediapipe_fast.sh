#!/bin/bash
set -e

echo "🚀 FAST MediaPipe Pipeline"
echo "============================================="
echo ""

# Configuration
VIDEO_PATH="${1:-video/dance.mp4}"
MODE="${2:-smart}"  # ultra_fast, fast, smart, or quality

# Extract video name without extension for unique outputs
VIDEO_NAME=$(basename "$VIDEO_PATH" | cut -f 1 -d '.')
FRAMES_DIR="frames_${VIDEO_NAME}"
OUTPUT_CSV="creative_output/${VIDEO_NAME}_${MODE}.csv"
OUTPUT_VIDEO="creative_output/${VIDEO_NAME}_${MODE}.mp4"

echo "📹 Video: $VIDEO_PATH"
echo "⚡ Mode: $MODE"
echo ""

# Processing speeds
if [ "$MODE" = "ultra_fast" ]; then
    echo "Speed: ~10-15 FPS (3 strategies/frame)"
elif [ "$MODE" = "fast" ]; then
    echo "Speed: ~5-8 FPS (6 strategies/frame)"
elif [ "$MODE" = "smart" ]; then
    echo "Speed: ~3-5 FPS (3-12 adaptive strategies/frame)"
else
    echo "Speed: ~0.5-1 FPS (30 strategies/frame)"
fi

echo ""

# Extract frames if needed
if [ ! -d "$FRAMES_DIR" ]; then
    echo "Extracting frames from new video..."
    python extract_frames.py "$VIDEO_PATH" \
        --output "$FRAMES_DIR" \
        --interval 1 \
        --format png \
        --prefix frame
else
    echo "Using existing frames in $FRAMES_DIR"
fi

echo ""
echo "Processing..."

# Run processing
python -c "
from mediapipe_fast_smart import MediaPipeFastSmart
import time

processor = MediaPipeFastSmart(mode='$MODE')

start = time.time()
df = processor.process_video_fast(
    '$FRAMES_DIR',
    '$OUTPUT_CSV'
)
elapsed = time.time() - start

print(f'\n⏱️  Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)')
print(f'📊 Average quality: {df[\"visibility\"].mean():.2%}')
"

# Create video
echo ""
echo "Creating video..."
python create_skeleton_video.py \
    --video "$VIDEO_PATH" \
    --csv "$OUTPUT_CSV" \
    --output "$OUTPUT_VIDEO" \
    --no-info

echo ""
echo "✅ Complete!"
echo "📹 Output: $OUTPUT_VIDEO"
echo ""
echo "To try different speeds:"
echo "  ./run_mediapipe_fast.sh video/dance.mp4 ultra_fast  # Fastest"
echo "  ./run_mediapipe_fast.sh video/dance.mp4 fast       # Fast"
echo "  ./run_mediapipe_fast.sh video/dance.mp4 smart      # Balanced (default)"
echo "  ./run_mediapipe_fast.sh video/dance.mp4 quality    # Best quality"