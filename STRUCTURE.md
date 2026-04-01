# Repository Structure

```
glb-to-usdz-blender/
├── README.md              # Main documentation
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
├── EXAMPLES.md           # Usage examples
├── glb_to_usdz.py        # Main conversion script
└── convert.sh            # Convenience runner script
```

## File Descriptions

### glb_to_usdz.py
The main Python script that runs inside Blender. Contains all the conversion logic:
- Scene clearing functions
- GLB import
- USDZ export with proper settings
- Batch processing logic
- Error handling

### convert.sh
Bash wrapper script that:
- Finds Blender installation automatically
- Validates inputs
- Provides user-friendly interface
- Handles cross-platform paths

### README.md
Comprehensive documentation including:
- Features and use cases
- Installation instructions
- Usage examples
- Troubleshooting guide
- Platform-specific commands

### EXAMPLES.md
Real-world usage scenarios:
- iOS app development
- E-commerce product models
- Game asset pipelines
- Testing converted files

### LICENSE
MIT License for open-source distribution

### .gitignore
Prevents committing:
- Python cache files
- 3D model files (GLB/USDZ)
- Output directories
- IDE configs

## How It Works

1. User runs `convert.sh input_folder`
2. Script finds Blender installation
3. Launches Blender in background mode
4. Runs `glb_to_usdz.py` with arguments
5. Script processes all GLB files
6. Outputs USDZ files to specified directory

