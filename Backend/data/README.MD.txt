# Backend/data Directory

## Overview

This directory contains vocabulary data files, database scripts, and runtime data for LangPlug.

## Directory Structure

### Files that SHOULD be in git:
- `*.csv` - Vocabulary files (A1_vokabeln.csv, A2_vokabeln.csv, B1_vokabeln.csv, B2_vokabeln.csv)
- `*.py` - Database import/export/verification scripts
- `*.txt`, `*.md` - Documentation files
- `.gitkeep` - Preserves directory structure

### Files/Directories that should NOT be in git:
- `langplug.db`, `*.db` - SQLite databases (runtime data)
- `*/` - User data subdirectories (UUID directories, numeric user IDs)
- `*.log` - Log files

## Cleanup Instructions

### Remove User Data Directories

User data directories (game sessions, language preferences) should NEVER be committed:

```bash
# From Backend/data/
rm -rf */                  # Remove all subdirectories (user data)
git rm -r */ 2>/dev/null   # Remove from git if already tracked
```

### Clean Up Log Files

```bash
# From Backend/data/
rm -f *.log vocabulary_import.log
```

### Reset Database to Clean State

```bash
# From Backend/data/
rm -f langplug.db langplug.db.backup vocabulary.db
# Database will be recreated on next server start
```

## .gitignore Protection

The following patterns in `.gitignore` prevent accidental commits:

```
data/*/                    # Exclude all user data subdirectories
!data/*.csv                # But keep CSV files
!data/*.py                 # But keep Python scripts
!data/*.txt                # But keep text files
!data/*.md                 # But keep markdown files
```

## Vocabulary Data LAWS

### Data Quality Rules:
- Every first col entry is a single word
- for example "zum Beispiel" is not valid it has to be "zum" one entry and "Beispiel" another entry
- Warnung/Achtung is also not just a single word and needs two entries
- Let X,Y be in A1,A1,B1,B2,C1 (e.g. B1>A1 since the level is harder)
then that always implies x in A1 implies x not in B1 (no redundancy)
- each german word has to be in base form (lemma)
- no proper names or other non vocabulary words -> filter these out
- Make sure the Spanish translation is valid
- Only use file read and file edit tools, no scripts or other things. Do everything manually
- No duplicates
- groß kleinschreibung muss korrekt sein

## Maintenance

### Before Committing:
1. Check for user data: `ls -la` (should see no UUID or numeric directories)
2. Check git status: `git status` (should not show user data files)
3. If user data exists: Run cleanup commands above

### Regular Cleanup:
- User data accumulates during development/testing
- Clean periodically to avoid bloating disk space
- Never commit personal user data (privacy violation)
