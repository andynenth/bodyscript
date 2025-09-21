#!/bin/bash
set -e  # Exit on error

echo "🎬 Running BEST Skeleton Detection Pipeline"
echo "============================================="
echo "This reproduces the dance_skeleton_fixed_final.mp4 approach"
echo ""

# Check if video exists
if [ ! -f "video/dance.mp4" ]; then
    echo "❌ Error: video/dance.mp4 not found"
    exit 1
fi

# Step 1: Run the Python script that handles everything
echo "🚀 Starting best skeleton video creation..."
python create_best_skeleton_video.py --video video/dance.mp4

# Step 2: Optional - Create optimized version
read -p "Do you want to create an optimized version with smoothing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🎨 Creating optimized version..."
    python create_skeleton_video_optimized.py \
        --csv creative_output/dance_poses_best_clean.csv \
        --output creative_output/dance_skeleton_best_optimized.mp4 \
        --preset smooth \
        --smoothing 10
fi

# Step 3: Extract validation frames
echo ""
echo "📸 Extracting validation frames..."
mkdir -p frames_validation

# Extract key frames for validation
python extract_frames.py creative_output/dance_skeleton_best.mp4 \
    --output frames_validation \
    --start 3 --end 4 \
    --prefix best_frame3

python extract_frames.py creative_output/dance_skeleton_best.mp4 \
    --output frames_validation \
    --start 50 --end 51 \
    --prefix best_frame50

echo ""
echo "============================================="
echo "✅ PIPELINE COMPLETE!"
echo "============================================="
echo ""
echo "📁 Output files:"
echo "  • Main video: creative_output/dance_skeleton_best.mp4"
echo "  • Clean data: creative_output/dance_poses_best_clean.csv"
echo "  • Validation frames: frames_validation/best_frame*.png"
echo ""
echo "🎯 This pipeline:"
echo "  ✓ Handles rotation/profile detection"
echo "  ✓ Fixes fast motion tracking"
echo "  ✓ Applies comprehensive reprocessing"
echo "  ✓ Cleans data automatically"
echo ""
echo "💡 To run again: ./run_best_pipeline.sh"
echo "============================================="