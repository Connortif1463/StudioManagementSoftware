import readline

class TestCompleter:
    def __init__(self):
        self.options = ["Alice", "Bob", "Charlie", "David", "Eve"]
    
    def complete(self, text, state):
        matches = [opt for opt in self.options if opt.lower().startswith(text.lower())]
        if state < len(matches):
            return matches[state]
        return None

def test():
    completer = TestCompleter()
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    
    result = input("Type a name and press TAB: ")
    print(f"You entered: {result}")

if __name__ == "__main__":
    test()