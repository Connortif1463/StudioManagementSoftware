# test_completer.py

import sys
from pathlib import Path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from studio_manager.cli.prompts import setup_completion, get_candidates_from_history
from studio_manager.data.history import ProjectHistory

history = ProjectHistory()

# Test candidates
print("Candidates:", get_candidates_from_history('engineer', history))

# Setup completer
from studio_manager.cli.prompts import CustomCompleter
import readline

candidates = get_candidates_from_history('engineer', history)
completer = CustomCompleter(candidates)
readline.set_completer(completer.complete)

print("\nType something and press TAB to test completion:")
print("(Type 'c' and press TAB to see if 'connor' completes)")
test = input("Test: ")