#!/usr/bin/env python3
"""
Blender GLB to USDZ Batch Converter
Converts multiple GLB files to USDZ format using Blender's USD export
"""
import bpy
import os
import sys
from pathlib import Path

__version__ = "1.0.0"

def clear_scene():
    """Clear all objects and data from the current scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Clear orphan data blocks
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)
    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)
    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)

def convert_glb_to_usdz(glb_path, usdz_path):
    """
    Convert a single GLB file to USDZ format
    
    Args:
        glb_path: Path to input GLB file
        usdz_path: Path to output USDZ file
    
    Returns:
        bool: True if conversion successful, False otherwise
    """
    try:
        # Clear the scene
        clear_scene()
        
        # Import GLB file
        bpy.ops.import_scene.gltf(filepath=str(glb_path))
        
        # Export as USDZ (Universal Scene Description)
        bpy.ops.wm.usd_export(
            filepath=str(usdz_path),
            export_materials=True,
            export_uvmaps=True,
            export_normals=True,
            use_instancing=True,
            evaluation_mode='RENDER'
        )
        
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Main conversion function"""
    # Get input and output directories from command line arguments
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
        if len(argv) < 1:
            print("Usage: blender --background --python glb_to_usdz.py -- <input_dir> [output_dir]")
            sys.exit(1)
        input_dir = Path(argv[0])
        output_dir = Path(argv[1]) if len(argv) > 1 else input_dir / "usdz_output"
    else:
        print("Error: No input directory specified")
        print("Usage: blender --background --python glb_to_usdz.py -- <input_dir> [output_dir]")
        sys.exit(1)
    
    # Validate input directory
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all GLB files
    glb_files = list(input_dir.glob("*.glb")) + list(input_dir.glob("*.GLB"))
    
    if not glb_files:
        print(f"No GLB files found in {input_dir}")
        sys.exit(1)
    
    # Print header
    print("=" * 60)
    print(f"GLB to USDZ Batch Converter v{__version__}")
    print("=" * 60)
    print(f"Input:  {input_dir}")
    print(f"Output: {output_dir}")
    print(f"Found {len(glb_files)} GLB file(s)")
    print("=" * 60)
    print()
    
    # Convert each file
    success_count = 0
    fail_count = 0
    
    for i, glb_file in enumerate(glb_files, 1):
        usdz_path = output_dir / f"{glb_file.stem}.usdz"
        
        # Skip if already exists
        if usdz_path.exists():
            print(f"[{i}/{len(glb_files)}] {glb_file.name} - Already exists, skipping")
            success_count += 1
            continue
        
        print(f"[{i}/{len(glb_files)}] Converting: {glb_file.name}")
        
        if convert_glb_to_usdz(glb_file, usdz_path):
            size = usdz_path.stat().st_size / 1024 / 1024
            print(f"  ✓ Success! ({size:.1f} MB)")
            success_count += 1
        else:
            print(f"  ✗ Failed!")
            fail_count += 1
        print()
    
    # Print summary
    print("=" * 60)
    print(f"Conversion Complete!")
    print(f"✓ Success: {success_count}")
    print(f"✗ Failed: {fail_count}")
    print(f"Output folder: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()

