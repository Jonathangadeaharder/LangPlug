"""Check if backend server is running and using new code"""
import requests
import sys

print("=" * 80)
print("BACKEND HEALTH CHECK")
print("=" * 80)

# Check if backend is running
print("\n1. Checking if backend is running...")
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    if response.status_code == 200:
        print("[GOOD] Backend is running")
    else:
        print(f"[WARN] Backend returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("[POOR] Backend is NOT running!")
    print("\nYou need to start the backend server:")
    print("  cd Backend")
    print("  powershell.exe -Command '. api_venv/Scripts/activate; python main.py'")
    sys.exit(1)
except Exception as e:
    print(f"[POOR] Error connecting to backend: {e}")
    sys.exit(1)

# Check if new code is loaded
print("\n2. Checking if backend has new vocabulary_builder code...")
print("   (This tests if the module was reloaded with proper name filtering)")

import asyncio
from services.processing.filtering.vocabulary_builder import VocabularyBuilderService
from services.filterservice.interface import FilteredWord, WordStatus

async def test():
    builder = VocabularyBuilderService()

    # Test proper name filtering
    proper_name = FilteredWord(
        text='Berlin',
        start_time=0.0,
        end_time=1.0,
        status=WordStatus.ACTIVE,
        metadata={}
    )

    common_word = FilteredWord(
        text='trauriger',
        start_time=0.0,
        end_time=1.0,
        status=WordStatus.ACTIVE,
        metadata={}
    )

    # This should filter out Berlin but include trauriger
    words = await builder.build_vocabulary_words([proper_name, common_word], 'de', return_dict=True)

    if len(words) == 1 and words[0]['word'] == 'trauriger':
        print("[GOOD] Proper name filtering is working!")

        if words[0]['lemma'] == 'traurig':
            print("[GOOD] spaCy lemmatization is working correctly!")
            return True
        else:
            print(f"[POOR] Wrong lemma: '{words[0]['lemma']}' (expected 'traurig')")
            print("       Backend may have cached old lemma data")
            return False
    else:
        print(f"[POOR] Expected 1 word, got {len(words)}")
        if len(words) > 1:
            print(f"       Words: {[w['word'] for w in words]}")
            print("       Proper name filtering may not be working")
        return False

result = asyncio.run(test())

if result:
    print("\n" + "=" * 80)
    print("BACKEND IS USING NEW CODE CORRECTLY")
    print("=" * 80)
    print("\nThe problem must be:")
    print("  1. Browser cache - try HARD REFRESH: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)")
    print("  2. Frontend cached state - try closing ALL tabs and reopening")
    print("  3. Old processing results being displayed - select a DIFFERENT time range")
else:
    print("\n" + "=" * 80)
    print("BACKEND IS STILL USING OLD CODE OR HAS CACHED DATA")
    print("=" * 80)
    print("\nTo fix:")
    print("  1. STOP the backend server (Ctrl+C)")
    print("  2. Clear Python cache: find . -type d -name '__pycache__' -exec rm -rf {} +")
    print("  3. START the backend server again")

print("\n" + "=" * 80)
