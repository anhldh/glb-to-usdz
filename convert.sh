#!/bin/bash
# GLB to USDZ Batch Converter Runner Script

set -e

echo "🎨 GLB to USDZ Batch Converter"
echo "======================================"
echo ""

# Find Blender executable
BLENDER_PATH=""

if [ -f "/Applications/Blender.app/Contents/MacOS/Blender" ]; then
    BLENDER_PATH="/Applications/Blender.app/Contents/MacOS/Blender"
elif [ -f "/Applications/Blender/Blender.app/Contents/MacOS/Blender" ]; then
    BLENDER_PATH="/Applications/Blender/Blender.app/Contents/MacOS/Blender"
elif command -v blender &> /dev/null; then
    BLENDER_PATH="blender"
else
    echo "❌ Blender not found!"
    echo ""
    echo "Please install Blender from: https://www.blender.org/download/"
    echo ""
    echo "Or specify the path manually:"
    echo "  /path/to/Blender.app/Contents/MacOS/Blender --background --python glb_to_usdz.py -- <input_dir> [output_dir]"
    exit 1
fi

echo "✅ Found Blender: $BLENDER_PATH"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_directory> [output_directory]"
    echo ""
    echo "Examples:"
    echo "  $0 ./models"
    echo "  $0 ./glb_files ./usdz_output"
    echo ""
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="${2:-$INPUT_DIR/usdz_output}"

if [ ! -d "$INPUT_DIR" ]; then
    echo "❌ Error: Input directory does not exist: $INPUT_DIR"
    exit 1
fi

echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Starting conversion..."
echo "======================================"
echo ""

# Run Blender in background mode
"$BLENDER_PATH" --background --python "$SCRIPT_DIR/glb_to_usdz.py" -- "$INPUT_DIR" "$OUTPUT_DIR"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "======================================"
    echo "✅ Done! Check your USDZ files in:"
    echo "   $OUTPUT_DIR"
    echo "======================================"
else
    echo "======================================"
    echo "❌ Conversion failed with exit code: $EXIT_CODE"
    echo "======================================"
fi

exit $EXIT_CODE

