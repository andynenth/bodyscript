#!/bin/bash
set -e  # Exit on error

echo "🎯 TRUE FRAME-BY-FRAME ANALYSIS PIPELINE"
echo "============================================="
echo "Individual optimization for EVERY frame with NO assumptions"
echo ""

# Configuration
VIDEO_PATH="${1:-video/dance.mp4}"
FRAMES_DIR="frames_complete_analysis"
OUTPUT_CSV="creative_output/true_every_frame_optimized.csv"
OUTPUT_VIDEO="creative_output/true_every_frame_optimized.mp4"

# Check if video exists
if [ ! -f "$VIDEO_PATH" ]; then
    echo "❌ Error: Video not found at $VIDEO_PATH"
    echo "Usage: ./run_true_frame_analysis.sh [video_path]"
    exit 1
fi

echo "📹 Input video: $VIDEO_PATH"
echo ""

# Step 1: Extract ALL frames as PNG images
echo "📸 Step 1: Extracting all frames from video..."
echo "-------------------------------------------"

if [ -d "$FRAMES_DIR" ]; then
    FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/frame_*.png 2>/dev/null | wc -l)
    if [ $FRAME_COUNT -gt 0 ]; then
        echo "⚠️  Frames already extracted: $FRAME_COUNT frames found"
        read -p "Do you want to re-extract frames? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Removing existing frames..."
            rm -rf "$FRAMES_DIR"
            mkdir -p "$FRAMES_DIR"
            EXTRACT_FRAMES=true
        else
            echo "Using existing frames..."
            EXTRACT_FRAMES=false
        fi
    else
        mkdir -p "$FRAMES_DIR"
        EXTRACT_FRAMES=true
    fi
else
    mkdir -p "$FRAMES_DIR"
    EXTRACT_FRAMES=true
fi

if [ "$EXTRACT_FRAMES" = true ]; then
    echo "Extracting frames (this may take a minute)..."
    python extract_frames.py "$VIDEO_PATH" \
        --output "$FRAMES_DIR" \
        --interval 1 \
        --format png \
        --prefix frame

    if [ $? -ne 0 ]; then
        echo "❌ Frame extraction failed"
        exit 1
    fi

    FRAME_COUNT=$(ls -1 "$FRAMES_DIR"/frame_*.png | wc -l)
    echo "✅ Extracted $FRAME_COUNT frames to $FRAMES_DIR/"
fi

echo ""

# Step 2: Run TRUE frame-by-frame analysis
echo "🔬 Step 2: Running TRUE frame-by-frame analysis..."
echo "-------------------------------------------"
echo "This will analyze EACH frame independently with:"
echo "  • 4 strategies per frame (original, blurred, enhanced, mirrored)"
echo "  • NO temporal assumptions or tracking"
echo "  • Best strategy selected per frame based on visibility"
echo ""

# Check if analysis already exists
if [ -f "$OUTPUT_CSV" ]; then
    echo "⚠️  Analysis results already exist: $OUTPUT_CSV"
    read -p "Do you want to re-analyze? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing analysis..."
        SKIP_ANALYSIS=true
    else
        echo "Re-analyzing all frames..."
        rm -f "$OUTPUT_CSV"
        SKIP_ANALYSIS=false
    fi
else
    SKIP_ANALYSIS=false
fi

if [ "$SKIP_ANALYSIS" = false ]; then
    python true_every_frame_analysis.py

    if [ $? -ne 0 ]; then
        echo "❌ Frame analysis failed"
        exit 1
    fi
fi

# Step 3: Verify analysis results
echo ""
echo "📊 Step 3: Verifying analysis results..."
echo "-------------------------------------------"

python -c "
import pandas as pd
import sys

try:
    # Load results
    df = pd.read_csv('$OUTPUT_CSV')

    # Statistics
    total_frames = df['frame_id'].nunique()
    total_landmarks = len(df)
    avg_visibility = df['visibility'].mean()

    print(f'Analysis Statistics:')
    print(f'  • Frames analyzed: {total_frames}')
    print(f'  • Total landmarks: {total_landmarks}')
    print(f'  • Average visibility: {avg_visibility:.2%}')

    # Strategy distribution
    if 'strategy' in df.columns:
        print(f'')
        print(f'Strategy Usage:')
        strategies = df.groupby('strategy')['frame_id'].nunique()
        for strategy, count in strategies.items():
            print(f'  • {strategy:10s}: {count:3d} frames ({count/total_frames*100:.1f}%)')

    # Quality check
    high_conf = (df['visibility'] > 0.7).sum()
    print(f'')
    print(f'Quality Metrics:')
    print(f'  • High confidence landmarks (>70%): {high_conf}/{total_landmarks} ({high_conf/total_landmarks*100:.1f}%)')

    # Sample frame quality
    print(f'')
    print(f'Sample Frame Quality:')
    for frame_id in [0, 3, 50, 100, total_frames-1]:
        if frame_id < total_frames:
            frame_data = df[df['frame_id'] == frame_id]
            if not frame_data.empty:
                vis = frame_data['visibility'].mean()
                strategy = frame_data.iloc[0]['strategy'] if 'strategy' in frame_data else 'unknown'
                print(f'  • Frame {frame_id:3d}: {vis:.1%} visibility ({strategy})')

except Exception as e:
    print(f'❌ Error verifying results: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Results verification failed"
    exit 1
fi

# Step 4: Create skeleton overlay video
echo ""
echo "🎬 Step 4: Creating skeleton overlay video..."
echo "-------------------------------------------"

if [ -f "$OUTPUT_VIDEO" ]; then
    echo "⚠️  Video already exists: $OUTPUT_VIDEO"
    read -p "Do you want to recreate it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing video..."
        SKIP_VIDEO=true
    else
        echo "Recreating video..."
        rm -f "$OUTPUT_VIDEO"
        SKIP_VIDEO=false
    fi
else
    SKIP_VIDEO=false
fi

if [ "$SKIP_VIDEO" = false ]; then
    python create_skeleton_video.py \
        --video "$VIDEO_PATH" \
        --csv "$OUTPUT_CSV" \
        --output "$OUTPUT_VIDEO"

    if [ $? -ne 0 ]; then
        echo "❌ Video creation failed"
        exit 1
    fi
fi

# Step 5: Extract validation frames
echo ""
echo "📸 Step 5: Creating validation frames..."
echo "-------------------------------------------"

VALIDATION_DIR="frames_validation_true"
mkdir -p "$VALIDATION_DIR"

# Extract key frames for comparison
for frame in 0 3 50 100 200 400; do
    if [ -f "$FRAMES_DIR/frame_$(printf "%04d" $frame).png" ]; then
        python extract_frames.py "$OUTPUT_VIDEO" \
            --output "$VALIDATION_DIR" \
            --start $frame --end $((frame + 1)) \
            --prefix "true_frame${frame}" \
            2>/dev/null
    fi
done

echo "✅ Validation frames saved to $VALIDATION_DIR/"

# Step 6: Final report
echo ""
echo "============================================="
echo "✅ TRUE FRAME-BY-FRAME PIPELINE COMPLETE!"
echo "============================================="
echo ""
echo "📁 Output files:"
echo "  • Extracted frames: $FRAMES_DIR/ ($(ls -1 $FRAMES_DIR/frame_*.png | wc -l) frames)"
echo "  • Analysis results: $OUTPUT_CSV"
echo "  • Skeleton video: $OUTPUT_VIDEO"
echo "  • Validation frames: $VALIDATION_DIR/"
echo ""
echo "🎯 Key characteristics of this approach:"
echo "  ✓ EVERY frame analyzed independently"
echo "  ✓ 4 strategies tested per frame"
echo "  ✓ NO temporal assumptions or tracking"
echo "  ✓ Optimal strategy selected per frame"
echo "  ✓ Static image mode (no video context)"
echo ""
echo "💡 This is the ONLY pipeline that:"
echo "  • Processes frames as individual images"
echo "  • Makes zero assumptions about temporal continuity"
echo "  • Selects best strategy for each frame independently"
echo ""
echo "📊 To compare with other pipelines:"
echo "  • Standard: ./run_pipeline.sh"
echo "  • Advanced: ./run_pipeline_advanced.sh"
echo "  • Optimized: ./run_optimized_pipeline.sh"
echo "  • This method: ./run_true_frame_analysis.sh"
echo ""
echo "============================================="