"""
Memory Migration Script for Ultron
Migrates JSON-based memories to vector-based ChromaDB storage
"""
import os
import sys
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from ultron_core import VectorMemorySystem, CREATOR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def migrate_memories():
    """Run one-time migration from JSON to vector storage."""
    print("=" * 60)
    print("ULTRON MEMORY MIGRATION UTILITY")
    print(f"Created by {CREATOR['name']}")
    print("=" * 60)
    print()
    
    # Check if old memory file exists
    memory_file = "ultron_memory.json"
    if not os.path.exists(memory_file):
        print(f"❌ No {memory_file} found. Nothing to migrate.")
        print("✓ Vector memory system will initialize with defaults.")
        return
    
    print(f"📄 Found {memory_file}")
    print("🔄 Initializing vector memory system...")
    
    # Initialize vector memory system
    try:
        memory = VectorMemorySystem()
    except Exception as e:
        print(f"❌ Failed to initialize vector memory: {e}")
        print("Make sure ChromaDB and sentence-transformers are installed:")
        print("   pip install chromadb==0.4.22 sentence-transformers==2.3.1")
        return
    
    print("✓ Vector memory system initialized")
    print()
    print("🚀 Starting migration...")
    
    # Run migration
    try:
        memory.migrate_from_json()
        print("✓ Migration completed successfully!")
        print()
        
        # Show summary
        count = memory.collection.count() if memory.collection else 0
        print(f"📊 Total memories in vector store: {count}")
        print(f"💾 Backup saved to: {memory_file}.backup")
        print()
        print("=" * 60)
        print("Migration complete. Ultron's memory is now semantic.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        logging.error(f"Migration error: {e}", exc_info=True)

if __name__ == "__main__":
    migrate_memories()
