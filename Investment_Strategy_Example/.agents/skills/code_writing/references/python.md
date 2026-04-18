## Python Code Guidelines

### PEP 8
All code must abide with all the following lightly customized PEP 8 guidelines.

* Use 4 spaces per indentation level.
* Continuation lines should align wrapped elements vertically inside parentheses, brackets, or braces, or use a hanging indent with no arguments on the first line and further indentation to distinguish the continued lines.
* Limit all code lines to 99 characters. For docstrings and comments, limit line length to 92 characters.
* Use Python’s implicit line continuation inside parentheses, brackets, or braces instead of backslashes.
* Break before a binary operator, not after.

* Surround top-level function and class definitions with two blank lines.
* Surround method definitions inside a class with a single blank line.
* Use extra blank lines (sparingly) to separate related functions or logical groups.
* Blank lines may be omitted between a group of related one-liners.
* Use blank lines sparingly within functions to indicate logical sections.

* UTF-8 should be used for code in the core Python distribution, without an encoding declaration.
* Use non-ASCII characters sparingly (e.g., to denote places or human names).

* Imports should be on separate lines.
* Imports should be at the top of the file after comments and docstrings and before module globals and constants.
* Group imports in this order: Standard library imports; Related third-party imports; Local application/library specific imports.
* Put a blank line between each group of imports.
* Use absolute imports everywhere apart from test fixtures.
* When importing a class from a module, it is usually fine to spell `from module import Class`; if this causes name clashes, import the module instead and use qualified names.
* Avoid wildcard imports, except when republishing an internal interface as part of a public API. 

* Module-level “dunders” (e.g. __all__, __author__, __version__) should be placed after the module docstring but before any import statements (except from __future__ imports). 

* When a string contains a quote character, use the other style (single vs double quotes) to avoid backslashes.
* For triple-quoted strings, always use double quotes. 

* Avoid extraneous and trailing whitespace.
* Always surround these binary operators with a single space on both sides: `=, +=, ==, <, >, !=, <=, >=, in, not in, is, is not, and, or, not`.
* When multiple operators with different priorities are used, add whitespace around operators with the lowest priority as needed, but never more than one space.
* Function annotations should use proper spacing around : and the -> arrow.
* Do not use spaces around the = in keyword arguments or default parameter values unless an annotation is present.
* Compound statements (multiple statements on one line) should not be used.
* Single-clause inline if, for, or while statements are forbidden.

* Trailing commas required in a one-element tuple.
* In lists/tuples with multiple values on separate lines, use trailing commas with closing brackets on their own line.
* Avoid trailing commas on the same line as the closing delimiter except for singleton tuples.

* Always keep comments up-to-date.
* Comments should be complete sentences, with the first word capitalized (unless it is an identifier).
* Use one or two spaces after sentence-ending periods in multi-sentence comments.
* Write comments in English unless absolutely certain they will never be read by non-native speakers.
* Block comments apply to successive code and are indented at the same level.
* Each line starts with # and a single space (unless it is indented text inside the comment).
* Separate paragraphs inside a block comment with a line containing a single #.
* Use inline comments sparingly, and they must be separated from code by at least two spaces and start with a # and a single space.

* Write docstrings for all modules, functions, classes, and methods.
* Multiline docstrings should have the closing """ on its own line.
* One-liner docstrings keep the closing """ on the same line.

* Names visible as public API should reflect usage, not implementation.
* Leading/trailing underscores (_name, name_, __name, __name__) have semantic meaning. 
* Never use l, O, or I as single-character variable names.
* Package/Module Names: Short, all lowercase; underscores allowed for readability; avoid underscores in packages if possible.
* Class Names: Use the CapWords convention; function naming may be used when primary use is as a callable.
* Type Variable Names: Use CapWords preferring short names with optional _co/_contra suffixes for variance.
* Exception Names: Follow class naming conventions; use suffix Error for error exceptions.
* Function and Variable Names: Lowercase with underscores.
* Function/Method Arguments: Use self for instance methods, cls for class methods; append underscore for clashes with reserved keywords.
* Method Names/Instance Variables: Lowercase with underscores; use one leading underscore for non-public, double leading underscores for name mangling.
* Constants: Defined at module level, all uppercase with underscores separating words. 

* Use __all__ to explicitly declare public API names; `__all__ = []` means no public API.
* Write code that does not disadvantage other Python implementations (e.g., PyPy, Jython).
* Avoid reliance on CPython-specific optimizations (e.g., in-place string concatenation).
* Comparisons to singletons like None must use `is` or `is not`.
* Prefer `if foo is not None` over `if not foo is None`.
* Always use a def statement instead of assigning a lambda to a name.
* Derive exceptions from Exception (not BaseException).
* Use exception chaining appropriately with `raise X from Y`.
* When catching exceptions, specify specific exceptions instead of bare except: clauses except in special cleanup/logging cases.
* For OS errors, prefer explicit exception hierarchy over inspecting errno.
* Use context managers (with) for resource cleanup; prefer explicit context-acquiring functions/methods.
* Be consistent with return statements; if any return a value, others should return an expression or explicitly return None.
* Use ''.startswith() and ''.endswith() instead of string slicing to check for prefixes or suffixes.
* Object type comparisons should always use isinstance() instead of comparing types directly.
* For sequences, (strings, lists, tuples), use the fact that empty sequences are false.
* Don’t compare boolean values to True or False using `==`.
* Avoid using return, break, or continue inside a finally block if the control flow would exit the finally suite.

* Function annotations should follow PEP 484 syntax for compatibility and clarity.
* Variable annotations (PEP 526) must follow spacing rules analogous to function annotations.

### Additional Requirements
* Import aliases are forbidden.
* `from module import x` is only allowed for Local application/library specific imports. All other standard library and third party libraries must import the module itself and use qualified names for any module contents.
* EXTREMELY IMPORTANT: Nested/inner functions (i.e. one function defined inside another function or method) are ABSOLUTELY FORBIDDEN. Never declare a function inside another function or method.
* Always use meaningful variable names, and avoid any variable names with less than 3 characters.
* Avoid reassigning new values to existing variables, as each variaable models a distinct concept, and preserving the full trace of intermediate objects simplifies debugging.
* Add precise type-hints to all function parameters and returns.
* Use the Numpy format for docstrings, unless the project is already predominantly using another format, in which case use that one.
* Do not include the parameter and return types in the docstrings when the function is already type-hinted.
* Never use implicit string concatenation by leaving only whitespace between strings. Always use the `join` method instead.
