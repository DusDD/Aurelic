"""
This module intentionally contains dead code to validate the vulture workflow.
Remove this file after verification.
"""

# Unused variable (dead)
DEMO_UNUSED_CONST = 42


# Unused function (dead)
def demo_unused_function() -> int:
    return 123


# Unused class + method (dead)
class DemoUnusedClass:
    def __init__(self) -> None:
        self.value = "unused"

    def demo_unused_method(self) -> str:
        return self.value


# Used code (should NOT be reported as dead)
def demo_used_function() -> str:
    return "I am used"


def _demo_main() -> None:
    # Call used function so vulture sees it as used within the module.
    print(demo_used_function())


if __name__ == "__main__":
    _demo_main()
