"""Code generation test definitions."""

CODING_TESTS = [
    {
        "id": "code_palindrome",
        "desc": "Palindrome check function",
        "prompt": "Write a Python function `is_palindrome(s)` that returns True if s is a palindrome, ignoring case and non-alphanumeric characters. Only return the function, no explanation.",
        "test_code": """
result = is_palindrome
assert result("racecar") == True
assert result("A man a plan a canal Panama") == True
assert result("hello") == False
assert result("Was it a car or a cat I saw") == True
assert result("") == True
assert result("a") == True
print("PASS")
""",
    },
    {
        "id": "code_fibonacci",
        "desc": "Fibonacci with memoization",
        "prompt": "Write a Python function `fibonacci(n)` that returns the nth Fibonacci number (0-indexed: fib(0)=0, fib(1)=1). Use memoization or DP. Only return the function.",
        "test_code": """
result = fibonacci
assert result(0) == 0
assert result(1) == 1
assert result(2) == 1
assert result(10) == 55
assert result(20) == 6765
print("PASS")
""",
    },
    {
        "id": "code_two_sum",
        "desc": "Two Sum (classic)",
        "prompt": "Write a Python function `two_sum(nums, target)` that returns the indices of two numbers that add up to target. Assume exactly one solution exists. Only return the function.",
        "test_code": """
result = two_sum
assert sorted(result([2,7,11,15], 9)) == [0,1]
assert sorted(result([3,2,4], 6)) == [1,2]
assert sorted(result([3,3], 6)) == [0,1]
print("PASS")
""",
    },
    {
        "id": "code_valid_brackets",
        "desc": "Valid bracket matching",
        "prompt": "Write a Python function `is_valid(s)` that returns True if the string of parentheses, brackets, and braces is balanced. Only return the function.",
        "test_code": """
result = is_valid
assert result("()[]{}") == True
assert result("([{}])") == True
assert result("([)]") == False
assert result("{[") == False
assert result("") == True
assert result("))") == False
print("PASS")
""",
    },
    {
        "id": "code_flatten",
        "desc": "Flatten nested list",
        "prompt": "Write a Python function `flatten(lst)` that recursively flattens a nested list of any depth. Only return the function.",
        "test_code": """
result = flatten
assert result([1,[2,[3,[4]],5]]) == [1,2,3,4,5]
assert result([]) == []
assert result([[1,2],[3,4]]) == [1,2,3,4]
assert result([1,2,3]) == [1,2,3]
print("PASS")
""",
    },
    {
        "id": "code_longest_consecutive",
        "desc": "Longest consecutive sequence — O(n)",
        "prompt": "Write a Python function `longest_consecutive(nums)` that returns the length of the longest consecutive sequence in an unsorted list. Must run in O(n). Only return the function.",
        "test_code": """
result = longest_consecutive
assert result([100,4,200,1,3,2]) == 4
assert result([0,3,7,2,5,8,4,6,0,1]) == 9
assert result([]) == 0
assert result([1]) == 1
print("PASS")
""",
    },
    {
        "id": "code_group_anagrams",
        "desc": "Group anagrams",
        "prompt": "Write a Python function `group_anagrams(strs)` that groups anagrams together. Return a list of groups (each group is a sorted list of strings). The groups can be in any order. No type annotations. Only return the function, no explanation.",
        "test_code": """
result = group_anagrams
out = result(["eat","tea","tan","ate","nat","bat"])
out = [sorted(g) for g in out]
out.sort()
assert out == [["ate","eat","tea"],["bat"],["nat","tan"]]
print("PASS")
""",
    },
    {
        "id": "code_binary_search",
        "desc": "Binary search",
        "prompt": "Write a Python function `binary_search(arr, target)` that returns the index of target in a sorted list, or -1 if not found. Only return the function.",
        "test_code": """
result = binary_search
assert result([1,3,5,7,9], 5) == 2
assert result([1,3,5,7,9], 6) == -1
assert result([], 1) == -1
assert result([1], 1) == 0
assert result([1,2,3,4,5], 1) == 0
assert result([1,2,3,4,5], 5) == 4
print("PASS")
""",
    },
    {
        "id": "code_roman_numerals",
        "desc": "Integer to Roman numeral",
        "prompt": "Write a Python function `int_to_roman(num)` that converts an integer (1–3999) to its Roman numeral representation. Only return the function.",
        "test_code": """
result = int_to_roman
assert result(3)    == "III"
assert result(4)    == "IV"
assert result(9)    == "IX"
assert result(58)   == "LVIII"
assert result(1994) == "MCMXCIV"
assert result(3999) == "MMMCMXCIX"
print("PASS")
""",
    },
    {
        "id": "code_lru_cache",
        "desc": "LRU Cache implementation",
        "prompt": """Implement an LRU Cache class in Python:

class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key: int) -> int: ...   # return -1 if not found
    def put(self, key: int, value: int) -> None: ...

Only return the class definition.""",
        "test_code": """
cache = LRUCache(2)
cache.put(1, 1)
cache.put(2, 2)
assert cache.get(1) == 1
cache.put(3, 3)
assert cache.get(2) == -1
cache.put(4, 4)
assert cache.get(1) == -1
assert cache.get(3) == 3
assert cache.get(4) == 4
print("PASS")
""",
    },
    {
        "id": "code_merge_intervals",
        "desc": "Merge overlapping intervals",
        "prompt": "Write a Python function `merge_intervals(intervals)` that takes a list of [start, end] intervals and merges all overlapping intervals. Return the merged list sorted by start. Only return the function.",
        "test_code": """
result = merge_intervals
assert result([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert result([[1,4],[4,5]]) == [[1,5]]
assert result([[1,4],[0,4]]) == [[0,4]]
assert result([]) == []
assert result([[1,2]]) == [[1,2]]
assert result([[1,4],[2,3]]) == [[1,4]]
print("PASS")
""",
    },
    {
        "id": "code_matrix_rotate",
        "desc": "Rotate matrix 90 degrees clockwise in-place",
        "prompt": "Write a Python function `rotate_matrix(matrix)` that rotates an NxN matrix 90 degrees clockwise in-place and returns it. Only return the function.",
        "test_code": """
result = rotate_matrix
m1 = [[1,2,3],[4,5,6],[7,8,9]]
assert result(m1) == [[7,4,1],[8,5,2],[9,6,3]]
m2 = [[1,2],[3,4]]
assert result(m2) == [[3,1],[4,2]]
m3 = [[1]]
assert result(m3) == [[1]]
print("PASS")
""",
    },
    {
        "id": "code_trie",
        "desc": "Trie (prefix tree) implementation",
        "prompt": """Implement a Trie class in Python:

class Trie:
    def __init__(self): ...
    def insert(self, word: str) -> None: ...
    def search(self, word: str) -> bool: ...
    def starts_with(self, prefix: str) -> bool: ...

Only return the class definition.""",
        "test_code": """
t = Trie()
t.insert("apple")
assert t.search("apple") == True
assert t.search("app") == False
assert t.starts_with("app") == True
t.insert("app")
assert t.search("app") == True
assert t.search("banana") == False
t.insert("banana")
assert t.search("banana") == True
assert t.starts_with("ban") == True
assert t.starts_with("xyz") == False
print("PASS")
""",
    },
    {
        "id": "code_max_subarray",
        "desc": "Maximum subarray sum (Kadane's algorithm)",
        "prompt": "Write a Python function `max_subarray(nums)` that returns the maximum sum of a contiguous subarray. The input list will have at least one element. Only return the function.",
        "test_code": """
result = max_subarray
assert result([-2,1,-3,4,-1,2,1,-5,4]) == 6
assert result([1]) == 1
assert result([-1]) == -1
assert result([5,4,-1,7,8]) == 23
assert result([-2,-1]) == -1
assert result([-1,0,-2]) == 0
print("PASS")
""",
    },
    {
        "id": "code_word_frequency",
        "desc": "Top K frequent words",
        "prompt": "Write a Python function `top_k_words(text, k)` that returns the k most frequent words in the text, sorted by frequency descending then alphabetically. Words are lowercased. Ignore punctuation. Only return the function.",
        "test_code": """
result = top_k_words
assert result("the cat sat on the mat the cat", 2) == ["the", "cat"]
assert result("a b c a b a", 1) == ["a"]
assert result("hello world hello", 2) == ["hello", "world"]
assert result("Foo foo FOO bar", 1) == ["foo"]
assert result("b a b a c", 2) == ["a", "b"]
print("PASS")
""",
    },
]
