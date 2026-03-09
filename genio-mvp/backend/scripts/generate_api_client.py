"""
API Client Generator
Generates TypeScript client from OpenAPI schema
"""
import json
import subprocess
from pathlib import Path


def generate_typescript_client():
    """Generate TypeScript client using openapi-generator."""
    
    # Ensure openapi.json exists
    openapi_path = Path("openapi.json")
    if not openapi_path.exists():
        print("Generating OpenAPI schema...")
        # Would need to run the app and export schema
        # For now, assume it exists
    
    output_dir = Path("../../frontend/src/generated")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run openapi-generator
    cmd = [
        "npx", "@openapitools/openapi-generator-cli", "generate",
        "-i", str(openapi_path),
        "-g", "typescript-axios",
        "-o", str(output_dir),
        "--additional-properties=",
        "supportsES6=true,",
        "npmName=genio-api-client,",
        "withInterfaces=true"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ TypeScript client generated in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating client: {e}")
    except FileNotFoundError:
        print("⚠️  openapi-generator not found. Install with:")
        print("   npm install -g @openapitools/openapi-generator-cli")


def generate_python_client():
    """Generate Python client using openapi-generator."""
    
    openapi_path = Path("openapi.json")
    output_dir = Path("../python-client")
    
    cmd = [
        "npx", "@openapitools/openapi-generator-cli", "generate",
        "-i", str(openapi_path),
        "-g", "python",
        "-o", str(output_dir),
        "--additional-properties=",
        "packageName=genio_api_client,",
        "projectName=genio-api-client"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Python client generated in {output_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating client: {e}")


if __name__ == "__main__":
    print("🚀 Generating API clients...")
    generate_typescript_client()
    generate_python_client()
    print("\n✨ Done!")
