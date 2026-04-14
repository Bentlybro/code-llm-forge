"""Reasoning test definitions."""

REASONING_TESTS = [
    {
        "id": "reason_balls",
        "desc": "Balance scale puzzle (2 weighings)",
        "prompt": "You have 8 balls, one of which is heavier than the rest. Using a balance scale, what is the minimum number of weighings needed to guarantee finding the heavy ball? Answer with just the number.",
        "check": lambda r: "2" in r,
    },
    {
        "id": "reason_fence",
        "desc": "Optimization — maximize fenced area",
        "prompt": "A farmer has 120 meters of fencing to enclose 3 sides of a rectangle (4th side is a wall). What are the optimal dimensions? Answer in this exact format: width=X, length=Y",
        "check": lambda r: "30" in r and "60" in r,
    },
    {
        "id": "reason_coins",
        "desc": "Classic logic — counterfeit coin",
        "prompt": "I have 3 coins. One is fake and lighter. I have one weighing on a balance scale. Can I always find the fake coin? Answer yes or no and explain in one sentence.",
        "check": lambda r: "yes" in r.lower(),
    },
    {
        "id": "reason_gsm_apples",
        "desc": "Word problem — arithmetic",
        "prompt": "Sarah has 3 times as many apples as Tom. Tom has 4 more apples than Lisa. Lisa has 6 apples. How many apples does Sarah have? Answer with just the number.",
        "check": lambda r: "30" in r,
    },
    {
        "id": "reason_gsm_train",
        "desc": "Word problem — distance/rate/time",
        "prompt": "A train leaves Station A at 60 km/h. Another train leaves Station B (300 km away) toward Station A at 90 km/h. They start at the same time. How many minutes until they meet? Answer with just the number.",
        "check": lambda r: "120" in r,
    },
    {
        "id": "reason_code_trace",
        "desc": "Code tracing — what does this print?",
        "prompt": """What does this Python code print? Answer with just the output.

def mystery(n):
    if n <= 1:
        return n
    return mystery(n-1) + mystery(n-2)

print(mystery(7))""",
        "check": lambda r: "13" in r,
    },
    {
        "id": "reason_code_trace2",
        "desc": "Code tracing — list comprehension",
        "prompt": """What does this Python code print? Answer with just the output.

nums = [1, 2, 3, 4, 5]
result = [x**2 for x in nums if x % 2 != 0]
print(result)""",
        "check": lambda r: "[1, 9, 25]" in r,
    },
    {
        "id": "reason_logic",
        "desc": "Logic puzzle — deduction",
        "prompt": "All cats are mammals. All mammals are animals. Whiskers is a cat. Is Whiskers an animal? Answer yes or no.",
        "check": lambda r: r.strip().lower().startswith("yes") or "yes" in r.lower()[:20],
    },
    {
        "id": "reason_probability",
        "desc": "Probability — basic",
        "prompt": "A bag has 3 red balls and 2 blue balls. You draw one ball. What is the probability it is red? Express as a fraction in simplest form.",
        "check": lambda r: "3/5" in r,
    },
    {
        "id": "reason_big_o",
        "desc": "Algorithm complexity",
        "prompt": "What is the time complexity of binary search on a sorted array of n elements? Answer with just the Big-O notation.",
        "check": lambda r: "o(log" in r.lower() or "log n" in r.lower() or "log(n)" in r.lower(),
    },
    {
        "id": "reason_multi_step",
        "desc": "Multi-step arithmetic word problem",
        "prompt": "A store sells apples for $2 each and oranges for $3 each. Maria buys 4 apples and 5 oranges. She pays with a $50 bill. How much change does she get? Answer with just the dollar amount.",
        "check": lambda r: "27" in r,
    },
    {
        "id": "reason_spatial",
        "desc": "Spatial reasoning — directions",
        "prompt": "You face north. You turn right. You turn right again. You turn left. What direction are you facing? Answer with just the cardinal direction.",
        "check": lambda r: "east" in r.lower(),
    },
    {
        "id": "reason_code_trace3",
        "desc": "Code tracing — dictionary manipulation",
        "prompt": """What does this Python code print? Answer with just the output.

d = {}
for i, c in enumerate("hello"):
    d[c] = d.get(c, 0) + i
print(sorted(d.items()))""",
        # Output: [('e', 1), ('h', 0), ('l', 5), ('o', 4)]
        "check": lambda r: "'h'" in r and "'e'" in r and "'l'" in r and "'o'" in r and "5" in r,
    },
    {
        "id": "reason_sequence",
        "desc": "Pattern recognition — number sequence",
        "prompt": "What is the next number in this sequence: 2, 6, 12, 20, 30, ? Answer with just the number.",
        "check": lambda r: "42" in r,
    },
    {
        "id": "reason_constraint",
        "desc": "Constraint satisfaction — scheduling",
        "prompt": "Alice must present before Bob. Bob must present before Carol. Dave must present before Alice. What is the earliest position Carol can present (1st, 2nd, 3rd, or 4th)? Answer with just the ordinal like '3rd'.",
        "check": lambda r: "4th" in r.lower() or ("4" in r and "3rd" not in r.lower() and "2nd" not in r.lower() and "1st" not in r.lower()),
    },
]
