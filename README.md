# GLB to USDZ Batch Converter

<div align="center">

![Blender](https://img.shields.io/badge/Blender-3.0%2B-orange?logo=blender)
![Python](https://img.shields.io/badge/Python-3.7%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

**A powerful batch converter that transforms GLB 3D models to USDZ format using Blender**

Perfect for iOS AR Quick Look, Apple Vision Pro, and Reality Composer

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Examples](#examples)

</div>

---

## ✨ Features

- 🚀 **Batch Processing** - Convert 100+ files in one go
- 🎨 **Preserves Materials** - Keeps textures, materials, and UV maps intact
- 🔧 **Zero Configuration** - Works out of the box
- 📱 **iOS Ready** - Perfect for AR Quick Look on iPhone/iPad
- 🎯 **Cross-Platform** - Works on macOS, Linux, and Windows
- ⚡ **Fast** - Leverages Blender's powerful USD export
- 🆓 **Free & Open Source** - No API limits, no costs

## 📋 Requirements

- **Blender 3.0 or higher** ([Download here](https://www.blender.org/download/))
- **Python 3.7+** (usually comes with Blender)
- **Bash** (for the convenience script) or run Python directly

## 🚀 Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/glb-to-usdz-blender.git
cd glb-to-usdz-blender

# Make the script executable (macOS/Linux)
chmod +x convert.sh
```

That's it! No dependencies to install.

## 📖 Usage

### Option 1: Using the Convenience Script (Easiest)

```bash
# Convert all GLB files in a directory
./convert.sh /path/to/glb/files

# Specify custom output directory
./convert.sh /path/to/glb/files /path/to/output
```

### Option 2: Direct Blender Command

```bash
# macOS
/Applications/Blender.app/Contents/MacOS/Blender --background --python glb_to_usdz.py -- input_dir [output_dir]

# Linux
blender --background --python glb_to_usdz.py -- input_dir [output_dir]

# Windows
"C:\Program Files\Blender Foundation\Blender\blender.exe" --background --python glb_to_usdz.py -- input_dir [output_dir]
```

## API Mode

This project can also run as an HTTP service so another backend can upload a GLB file, trigger conversion, then download the generated USDZ file.

### Install API dependencies

```bash
pip install -r requirements.txt
```

### Start the API

```bash
# Optional: set Blender path explicitly if it is not on PATH
export BLENDER_PATH=/path/to/blender

# Run the service
python api_server.py
```

On Windows PowerShell:

```powershell
$env:BLENDER_PATH="C:\Program Files\Blender Foundation\Blender\blender.exe"
python .\api_server.py
```

### Run with Docker

The repository now includes a Docker image that installs Blender and runs the API service inside the container.

```bash
docker build -t glb-to-usdz-api .
docker run --rm -p 8000:8000 glb-to-usdz-api
```

If you want converted files to survive container restarts before they are downloaded, mount the storage folder:

```bash
docker run --rm -p 8000:8000 -v $(pwd)/storage:/app/storage glb-to-usdz-api
```

On Windows PowerShell:

```powershell
docker build -t glb-to-usdz-api .
docker run --rm -p 8000:8000 -v "${PWD}\storage:/app/storage" glb-to-usdz-api
```

### API endpoints

`POST /convert`
- Content type: `multipart/form-data`
- File field name: `uploaded_file`
- Response:

```json
{
  "OutputPath": "chair_a1b2c3.usdz",
  "FileName": "chair_a1b2c3.usdz",
  "DownloadUrl": "/download/chair_a1b2c3.usdz"
}
```

`GET /download/{outputPath}`
- Downloads the converted USDZ file.
- The file is deleted automatically after the response is sent successfully.

### Integration with your .NET backend

The API is intentionally compatible with this flow:

1. Upload the GLB file to `POST /convert` using field name `uploaded_file`
2. Read `OutputPath` from the JSON response
3. Download the file from `GET /download/{OutputPath}`

Suggested app settings:

```json
{
  "ConvertUsdz": {
    "BaseUrl": "http://localhost:8000",
    "ApiConvert": "/convert",
    "ApiDownload": "/download/{0}"
  }
}
```

## 💡 Examples

### Basic Conversion

```bash
./convert.sh ./models
```

This will:
- Find all `.glb` files in `./models`
- Convert them to USDZ
- Save output to `./models/usdz_output`

### Custom Output Directory

```bash
./convert.sh ./downloaded_models ./converted_usdz
```

### Real-World Example

```bash
# Convert 100+ AR models for iOS app
./convert.sh ~/Projects/AR-App/models ~/Projects/AR-App/assets/usdz

# Output:
# ✅ Found Blender: /Applications/Blender.app/Contents/MacOS/Blender
# Input directory: ~/Projects/AR-App/models
# Output directory: ~/Projects/AR-App/assets/usdz
# Found 102 GLB file(s)
# [1/102] Converting: model_001.glb
#   ✓ Success! (2.3 MB)
# ...
# ✓ Success: 102
# ✗ Failed: 0
```

## 📱 Testing on iPhone

After conversion:

1. Open Finder and navigate to your output folder
2. Select any `.usdz` file
3. AirDrop to your iPhone
4. Tap the file to view in **AR Quick Look**! 🎉

## 🎯 Use Cases

- 📱 **iOS AR Applications** - AR Quick Look, ARKit
- 🥽 **Apple Vision Pro** - Native spatial content
- 🎨 **Reality Composer** - Import USDZ for AR experiences
- 🌐 **Web AR** - Use with model-viewer or AR.js
- 🎮 **Game Development** - Unity, Unreal Engine USD support

## ⚙️ How It Works

1. **Import** - Blender imports GLB using the glTF 2.0 importer
2. **Process** - Preserves meshes, materials, textures, UV maps, and normals
3. **Export** - Exports using Blender's USD exporter as USDZ format
4. **Optimize** - Applies instancing and render evaluation for best quality

## 🔧 Advanced Options

Want to customize the conversion? Edit `glb_to_usdz.py` and modify the `bpy.ops.wm.usd_export()` parameters:

```python
bpy.ops.wm.usd_export(
    filepath=str(usdz_path),
    export_materials=True,      # Include materials
    export_uvmaps=True,          # Include UV coordinates
    export_normals=True,         # Include normals
    use_instancing=True,         # Optimize file size
    evaluation_mode='RENDER'     # Use render quality
)
```

## 🐛 Troubleshooting

### "Blender not found"
- Make sure Blender is installed
- On macOS, install to `/Applications/Blender.app`
- Or specify path manually in the error message instructions

### "No GLB files found"
- Check that your input directory contains `.glb` files
- File extensions are case-insensitive (`.glb` or `.GLB` work)

### Conversion fails
- Ensure you have write permissions to the output directory
- Check that GLB files are valid (try opening in Blender GUI first)
- Review Blender console output for specific errors

## 📊 Performance

Tested on MacBook Pro M1:
- **Single file**: ~50-200ms per file
- **100 files**: ~2-3 minutes total
- **Output size**: Similar to input GLB size

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests
- 📖 Improve documentation

## 📄 License

MIT License - feel free to use in personal and commercial projects!

## 🙏 Acknowledgments

- Built with [Blender](https://www.blender.org/) - Amazing open-source 3D software
- Uses Pixar's [USD](https://openusd.org/) format
- Inspired by the glTF and AR development communities

## ⭐ Star History

If this tool helped you, consider giving it a star! ⭐

---

<div align="center">

**Made with ❤️ for the 3D and AR community**

[Report Bug](https://github.com/yourusername/glb-to-usdz-blender/issues) · [Request Feature](https://github.com/yourusername/glb-to-usdz-blender/issues)

</div>

