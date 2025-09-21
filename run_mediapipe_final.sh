#!/bin/bash
set -e  # Exit on error

echo "🎯 FINAL OPTIMIZED MediaPipe PIPELINE"
echo "============================================="
echo "Maximum quality MediaPipe-only pose detection"
echo ""

# Configuration
VIDEO_PATH="${1:-video/dance.mp4}"
FRAMES_DIR="frames_complete_analysis"
OUTPUT_CSV="creative_output/mediapipe_final_full.csv"
OUTPUT_VIDEO="creative_output/mediapipe_final_full.mp4"

# Check if video exists
if [ ! -f "$VIDEO_PATH" ]; then
    echo "❌ Error: Video not found at $VIDEO_PATH"
    echo "Usage: ./run_mediapipe_final.sh [video_path]"
    exit 1
fi

echo "📹 Input video: $VIDEO_PATH"
echo ""

# Step 1: Extract frames if needed
echo "📸 Step 1: Checking frames..."
echo "-------------------------------------------"

if [ -d "$FRAMES_DIR" ]; then
    FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/frame_*.png 2>/dev/null | wc -l)
    if [ $FRAME_COUNT -gt 0 ]; then
        echo "✅ Using existing frames: $FRAME_COUNT frames found"
    else
        echo "Extracting frames..."
        python extract_frames.py "$VIDEO_PATH" \
            --output "$FRAMES_DIR" \
            --interval 1 \
            --format png \
            --prefix frame
    fi
else
    echo "Creating frames directory and extracting..."
    mkdir -p "$FRAMES_DIR"
    python extract_frames.py "$VIDEO_PATH" \
        --output "$FRAMES_DIR" \
        --interval 1 \
        --format png \
        --prefix frame
fi

echo ""

# Step 2: Run final optimized MediaPipe detection
echo "🔬 Step 2: Running FINAL MediaPipe detection..."
echo "-------------------------------------------"
echo "This will:"
echo "  • Test 30 strategies per frame (10 preprocessing × 3 models)"
echo "  • Use anatomical scoring"
echo "  • Apply temporal smoothing"
echo "  • May take 5-10 minutes for full video"
echo ""

python -c "
from mediapipe_final_optimized import MediaPipeFinalOptimized
import time

print('Starting full video processing...')
start_time = time.time()

processor = MediaPipeFinalOptimized()
df = processor.process_video_final(
    '$FRAMES_DIR',
    '$OUTPUT_CSV',
    sample_only=False  # Process ALL frames
)

elapsed = time.time() - start_time
print(f'\nProcessing completed in {elapsed/60:.1f} minutes')
print(f'Average: {elapsed/len(df[\"frame_id\"].unique()):.2f} seconds per frame')
"

if [ $? -ne 0 ]; then
    echo "❌ Detection failed"
    exit 1
fi

echo ""

# Step 3: Create skeleton overlay video
echo "🎬 Step 3: Creating skeleton overlay video..."
echo "-------------------------------------------"

python create_skeleton_video.py \
    --video "$VIDEO_PATH" \
    --csv "$OUTPUT_CSV" \
    --output "$OUTPUT_VIDEO"

if [ $? -ne 0 ]; then
    echo "❌ Video creation failed"
    exit 1
fi

echo ""

# Step 4: Generate quality report
echo "📊 Step 4: Generating quality report..."
echo "-------------------------------------------"

python -c "
import pandas as pd
import numpy as np

# Load results
df = pd.read_csv('$OUTPUT_CSV')

print('FINAL QUALITY REPORT')
print('='*50)

# Overall statistics
total_frames = df['frame_id'].nunique()
total_landmarks = len(df)
avg_visibility = df['visibility'].mean()

print(f'Frames processed: {total_frames}')
print(f'Total landmarks: {total_landmarks}')
print(f'Average visibility: {avg_visibility:.2%}')

# Strategy distribution
if 'strategy' in df.columns:
    print('\nTop strategies used:')
    strategies = df.groupby('frame_id')['strategy'].first().value_counts()
    for strategy, count in strategies.head(5).items():
        base_strategy = strategy.split('_')[0]
        print(f'  {base_strategy:15s}: {count:3d} frames ({count/total_frames*100:.1f}%)')

# Quality breakdown
high_conf = (df['visibility'] > 0.8).sum()
med_conf = ((df['visibility'] > 0.5) & (df['visibility'] <= 0.8)).sum()
low_conf = (df['visibility'] <= 0.5).sum()

print(f'\nConfidence distribution:')
print(f'  High (>80%):   {high_conf:6d} ({high_conf/total_landmarks*100:.1f}%)')
print(f'  Medium (50-80%): {med_conf:6d} ({med_conf/total_landmarks*100:.1f}%)')
print(f'  Low (<50%):    {low_conf:6d} ({low_conf/total_landmarks*100:.1f}%)')

# Frame quality
print(f'\nPer-frame quality:')
frame_quality = df.groupby('frame_id')['visibility'].mean()
excellent = (frame_quality > 0.8).sum()
good = ((frame_quality > 0.6) & (frame_quality <= 0.8)).sum()
poor = (frame_quality <= 0.6).sum()

print(f'  Excellent (>80%): {excellent} frames')
print(f'  Good (60-80%):    {good} frames')
print(f'  Poor (<60%):      {poor} frames')

# Problem frames
print(f'\nMost challenging frames:')
worst_frames = frame_quality.nsmallest(5)
for frame_id, score in worst_frames.items():
    print(f'  Frame {frame_id:3d}: {score:.2%} visibility')
"

echo ""

# Step 5: Extract sample frames for validation
echo "📸 Step 5: Creating validation frames..."
echo "-------------------------------------------"

mkdir -p frames_validation_final

for frame in 0 3 50 100 200 300 400; do
    python extract_frames.py "$OUTPUT_VIDEO" \
        --output frames_validation_final \
        --start $frame --end $((frame + 1)) \
        --prefix "final_frame${frame}" \
        2>/dev/null || true
done

echo "✅ Validation frames saved to frames_validation_final/"

echo ""
echo "============================================="
echo "✅ FINAL MediaPipe PIPELINE COMPLETE!"
echo "============================================="
echo ""
echo "📁 Output files:"
echo "  • Pose data: $OUTPUT_CSV"
echo "  • Skeleton video: $OUTPUT_VIDEO"
echo "  • Validation frames: frames_validation_final/"
echo ""
echo "🎯 This represents the BEST possible MediaPipe results with:"
echo "  ✓ 30 detection strategies per frame"
echo "  ✓ Anatomical constraint validation"
echo "  ✓ Temporal smoothing"
echo "  ✓ Optimized model selection"
echo ""
echo "💡 To view the video:"
echo "  open $OUTPUT_VIDEO"
echo ""
echo "📊 To compare with other methods:"
echo "  • Original 4-strategy: creative_output/true_every_frame_optimized.mp4"
echo "  • This final version: $OUTPUT_VIDEO"
echo ""
echo "============================================="