# Examples

## Basic Usage

```bash
# Convert all GLB files in the current directory
./convert.sh .

# Convert files from a specific folder
./convert.sh ~/Downloads/3d-models

# Specify output folder
./convert.sh ./input ./output
```

## Real-World Scenarios

### iOS App Development
```bash
# Convert AR assets for iOS app
./convert.sh ./Assets/Models ./Assets/USDZ
# Then drag USDZ files into Xcode
```

### Batch E-commerce Product Models
```bash
# Convert 1000+ product models
./convert.sh ./product-catalog ./usdz-catalog
# Upload to CDN for AR Quick Look on website
```

### Game Asset Pipeline
```bash
# Convert GLB exports from Blender to USDZ for Unity
./convert.sh ./exported-models ./unity-assets/USDZ
```

## Directory Structure Example

**Before:**
```
my-project/
├── models/
│   ├── chair.glb
│   ├── table.glb
│   └── lamp.glb
└── convert.sh
```

**After running `./convert.sh models`:**
```
my-project/
├── models/
│   ├── chair.glb
│   ├── table.glb
│   ├── lamp.glb
│   └── usdz_output/
│       ├── chair.usdz
│       ├── table.usdz
│       └── lamp.usdz
└── convert.sh
```

## Testing Converted Files

### On macOS
```bash
# Quick Look preview
qlmanage -p output/model.usdz

# Open in Preview
open output/model.usdz
```

### On iPhone
1. AirDrop the USDZ file to your iPhone
2. Tap to open in AR Quick Look
3. Place in your environment!

### In Web Browser
```html
<!-- Use model-viewer -->
<model-viewer src="model.usdz" 
              ar 
              ar-modes="scene-viewer quick-look"
              camera-controls>
</model-viewer>
```

