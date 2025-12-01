"""
Setup Script for Content Intelligence Pipeline
Initializes database, ChromaDB, and validates configuration
"""
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import db
from stages import stage4_rag_setup
from dotenv import load_dotenv


def check_env_vars():
    """Check if required environment variables are set"""
    print("Checking environment variables...")
    
    load_dotenv()
    
    required_vars = {
        'GEMINI_API_KEY': 'Google Gemini API Key',
        'SERPAPI_KEY': 'SerpAPI Key (optional for keyword research)',
        'JINA_API_KEY': 'Jina AI Reader API Key (optional, will fallback to Trafilatura)'
    }
    
    missing = []
    optional_missing = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the key for security
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print(f"  ✓ {var}: {masked}")
        else:
            if var in ['SERPAPI_KEY', 'JINA_API_KEY']:
                optional_missing.append(f"  ⚠ {var}: Not set ({description})")
            else:
                missing.append(f"  ✗ {var}: Not set ({description})")
    
    if missing:
        print("\nMissing required environment variables:")
        for msg in missing:
            print(msg)
        print("\nPlease create a .env file with required keys.")
        print("See .env.example for template.")
        return False
    
    if optional_missing:
        print("\nOptional environment variables not set:")
        for msg in optional_missing:
            print(msg)
        print("Pipeline will use fallback methods where applicable.")
    
    print("\n✓ Environment variables OK")
    return True


def create_directories():
    """Create necessary data directories"""
    print("\nCreating data directories...")
    
    base_dir = Path(__file__).parent / 'data'
    
    dirs = [
        base_dir,
        base_dir / 'extractions',
        base_dir / 'drafts',
        base_dir / 'outputs',
        base_dir / 'fingerprints',
        base_dir / 'sendmarc_blogs',
        base_dir / 'chromadb'
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")
    
    print("✓ Directories created")


def init_database():
    """Initialize SQLite database"""
    print("\nInitializing database...")
    
    try:
        db.init_database()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False


def init_brand_voice_db():
    """Initialize brand voice database"""
    print("\nInitializing brand voice database...")
    
    try:
        result = stage4_rag_setup.run()
        
        if result['success']:
            print(f"✓ Brand voice database initialized")
            print(f"  Chunks added: {result['chunks_added']}")
            
            if result['chunks_added'] == 0:
                print("\n⚠ Note: No Sendmarc blog content found.")
                print(f"  To populate with actual content, place markdown files in:")
                print(f"  {result['source_directory']}")
                print(f"  Then run: python setup.py --populate-rag")
        else:
            print(f"✗ Brand voice initialization failed: {result.get('error')}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Brand voice initialization failed: {e}")
        return False


def create_sample_env():
    """Create sample .env file if it doesn't exist"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        return
    
    print("\nCreating .env file from template...")
    
    example_path = Path(__file__).parent / '.env.example'
    
    if example_path.exists():
        with open(example_path, 'r') as f:
            content = f.read()
        
        with open(env_path, 'w') as f:
            f.write(content)
        
        print(f"✓ Created {env_path}")
        print("  Please edit this file and add your API keys.")
    else:
        print("⚠ .env.example not found, skipping .env creation")


def run_tests():
    """Run basic tests to validate setup"""
    print("\nRunning validation tests...")
    
    # Test imports
    try:
        from utils.llm_client import GeminiClient
        from utils.validation import validate_url
        print("  ✓ Module imports OK")
    except Exception as e:
        print(f"  ✗ Module import failed: {e}")
        return False
    
    # Test URL validation
    try:
        assert validate_url("https://example.com/blog")
        assert not validate_url("not-a-url")
        print("  ✓ URL validation OK")
    except Exception as e:
        print(f"  ✗ URL validation failed: {e}")
        return False
    
    # Test database connection
    try:
        pipelines = db.list_pipelines(limit=1)
        print("  ✓ Database connection OK")
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False
    
    print("✓ All validation tests passed")
    return True


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Content Intelligence Pipeline')
    parser.add_argument('--skip-env-check', action='store_true', help='Skip environment variable check')
    parser.add_argument('--populate-rag', action='store_true', help='Populate RAG database from sendmarc_blogs/')
    parser.add_argument('--test', action='store_true', help='Run validation tests only')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Content Intelligence Pipeline - Setup")
    print("="*60)
    
    if args.test:
        run_tests()
        return
    
    # Create .env if needed
    create_sample_env()
    
    # Check environment variables
    if not args.skip_env_check:
        if not check_env_vars():
            print("\n⚠ Setup incomplete: Missing required environment variables")
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Initialize database
    if not init_database():
        print("\n✗ Setup failed at database initialization")
        sys.exit(1)
    
    # Initialize brand voice database
    if not init_brand_voice_db():
        print("\n⚠ Setup completed with warnings: Brand voice database initialization failed")
        print("  You can retry later with: python setup.py --populate-rag")
    
    # Run tests
    if not run_tests():
        print("\n⚠ Setup completed with warnings: Some validation tests failed")
    
    print("\n" + "="*60)
    print("✓ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Review and edit .env with your API keys (if not done)")
    print("  2. (Optional) Add Sendmarc blog content to data/sendmarc_blogs/")
    print("  3. Run a test pipeline:")
    print("     python main.py --url <competitor-url>")
    print("  4. Or launch the dashboard:")
    print("     streamlit run dashboard/app.py")
    print()


if __name__ == '__main__':
    main()

