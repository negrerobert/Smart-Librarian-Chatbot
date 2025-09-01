import os
import sys
from pathlib import Path
import uvicorn
from dotenv import load_dotenv


def check_requirements():
    """Check if all required dependencies and configurations are present."""
    print("Checking requirements...")
    print(f"Current directory: {os.getcwd()}")

    # Check if .env file exists
    env_file = Path('.env')
    print(f"Looking for .env file at: {env_file.absolute()}")

    if not env_file.exists():
        print(".env file not found!")
        print(f"Checked path: {env_file.absolute()}")
        print("Please create a .env file with your OPENAI_API_KEY")
        return False
    else:
        print(".env file found!")

    # Load environment variables
    load_dotenv()

    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not found in environment variables")
        print("Please add your OpenAI API key to the .env file")
        return False

    if api_key == 'your_openai_api_key_here' or len(api_key) < 20:
        print("Please replace the placeholder OPENAI_API_KEY with your actual API key")
        print(f"Current key length: {len(api_key)} characters (should be 40+)")
        return False

    # Check if book summaries file exists (try both locations)
    data_file1 = Path('data/book_summaries.txt')
    data_file2 = Path('backend/data/book_summaries.txt')

    if data_file1.exists():
        print(f"Book summaries found at: {data_file1}")
    elif data_file2.exists():
        print(f"Book summaries found at: {data_file2}")
    else:
        print(f"Book summaries file not found!")
        print(f"   Checked: {data_file1}")
        print(f"   Checked: {data_file2}")
        return False

    # Check if backend directory exists
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        return False

    print("All requirements check passed!")
    return True


def main():
    """Main function to run the server."""
    print("Smart Librarian Backend Server")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        print("\nServer cannot start due to missing requirements")
        input("Press Enter to exit...")
        sys.exit(1)

    print("\nStarting server...")
    print("Smart Librarian API will be available at:")
    print("   Local:    http://localhost:8000")
    print("   Network:  http://0.0.0.0:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Health:   http://localhost:8000/health")

    print("\nAPI Endpoints:")
    print("   POST /chat           - Main chat endpoint")
    print("   GET  /books          - List all available books")
    print("   GET  /database/info  - Database information")
    print("   GET  /health         - Health check")

    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Add the project root to Python path so imports work
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))

        # Import and run the FastAPI app
        from backend.api.main import app

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("\nDebug info:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Python path: {sys.path[:3]}...")
        input("Press Enter to exit...")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nServer stopped by user")

    except Exception as e:
        print(f"Server error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()