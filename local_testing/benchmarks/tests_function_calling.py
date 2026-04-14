"""Function calling test definitions."""

FUNCTION_CALLING_TESTS = [
    # ── Simple: pick the right function ─────────────────────────────────────
    {
        "id": "fc_simple_weather",
        "desc": "Simple single call — correct function + argument",
        "messages": [{"role": "user", "content": "What's the weather in Tokyo right now?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                            "units": {"type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius"}
                        },
                        "required": ["city"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get current stock price by ticker",
                    "parameters": {
                        "type": "object",
                        "properties": {"ticker": {"type": "string"}},
                        "required": ["ticker"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "get_weather"
            and "tokyo" in str(calls[0]["args"].get("city", "")).lower()
        ),
    },
    {
        "id": "fc_simple_stock",
        "desc": "Simple single call — stock not weather",
        "messages": [{"role": "user", "content": "What's the current AAPL stock price?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get current stock price",
                    "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "get_stock_price"
            and "aapl" in str(calls[0]["args"].get("ticker", "")).lower()
        ),
    },
    # ── Argument extraction ──────────────────────────────────────────────────
    {
        "id": "fc_args_email",
        "desc": "Argument extraction from natural language",
        "messages": [{"role": "user", "content": "Send an email to alice@example.com with subject 'Project Update' saying the deadline has moved to Friday."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to":      {"type": "string"},
                            "subject": {"type": "string"},
                            "body":    {"type": "string"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "send_email"
            and "alice@example.com" in str(calls[0]["args"].get("to", ""))
            and len(calls[0]["args"].get("body", "")) > 5
        ),
    },
    {
        "id": "fc_args_search",
        "desc": "Correct argument types and values",
        "messages": [{"role": "user", "content": "Search for Python tutorials for beginners, limit to 5 results."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query":  {"type": "string"},
                            "limit":  {"type": "integer", "description": "Max results"},
                        },
                        "required": ["query"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "web_search"
            and "python" in str(calls[0]["args"].get("query", "")).lower()
        ),
    },
    # ── Negative: should NOT call any function ───────────────────────────────
    {
        "id": "fc_negative_math",
        "desc": "Negative case — answer directly, don't call a function",
        "messages": [{"role": "user", "content": "What is 2 + 2?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Evaluate a mathematical expression",
                    "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}
                }
            }
        ],
        "check": lambda calls: len(calls) == 0,
    },
    {
        "id": "fc_negative_explanation",
        "desc": "Negative case — conceptual question, no tool needed",
        "messages": [{"role": "user", "content": "Can you explain how recursion works? Answer in plain text only, do not execute any code."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "run_code",
                    "description": "Execute Python code",
                    "parameters": {"type": "object", "properties": {"code": {"type": "string"}}, "required": ["code"]}
                }
            }
        ],
        "check": lambda calls: len(calls) == 0,
    },
    # ── Parallel calls ───────────────────────────────────────────────────────
    {
        "id": "fc_parallel_weather",
        "desc": "Parallel calls — weather for two cities",
        "messages": [{"role": "user", "content": "What's the weather in both London and Paris right now?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 2
            and all(c["name"] == "get_weather" for c in calls)
            and any("london" in str(c["args"].get("city", "")).lower() for c in calls)
            and any("paris"  in str(c["args"].get("city", "")).lower() for c in calls)
        ),
    },
    {
        "id": "fc_parallel_mixed",
        "desc": "Parallel calls — mixed functions",
        "messages": [{"role": "user", "content": "Get me the weather in Berlin and also the current TSLA stock price."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get stock price",
                    "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}
                }
            }
        ],
        "check": lambda calls: (
            any(c["name"] == "get_weather"   and "berlin" in str(c["args"].get("city", "")).lower() for c in calls)
            and any(c["name"] == "get_stock_price" and "tsla" in str(c["args"].get("ticker", "")).lower() for c in calls)
        ),
    },
    # ── Relevance ────────────────────────────────────────────────────────────
    {
        "id": "fc_relevance_no_match",
        "desc": "Relevance — none of the available tools fit the request",
        "messages": [{"role": "user", "content": "Write me a haiku about autumn leaves."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email",
                    "parameters": {
                        "type": "object",
                        "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
                        "required": ["to", "subject", "body"]
                    }
                }
            }
        ],
        "check": lambda calls: len(calls) == 0,
    },
    {
        "id": "fc_enum_validation",
        "desc": "Enum argument — correct value from constrained set",
        "messages": [{"role": "user", "content": "Get the weather in Sydney in Fahrenheit."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city":  {"type": "string"},
                            "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                        },
                        "required": ["city", "units"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "get_weather"
            and "sydney" in str(calls[0]["args"].get("city", "")).lower()
            and calls[0]["args"].get("units") == "fahrenheit"
        ),
    },
    # ── Nested / complex arguments ──────────────────────────────────────────
    {
        "id": "fc_nested_args",
        "desc": "Nested object arguments — schedule a meeting",
        "messages": [{"role": "user", "content": "Schedule a meeting titled 'Sprint Review' on 2026-04-15 from 2pm to 3pm with alice@example.com and bob@example.com."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "create_event",
                    "description": "Create a calendar event",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "date": {"type": "string", "description": "ISO date (YYYY-MM-DD)"},
                            "start_time": {"type": "string", "description": "HH:MM 24h format"},
                            "end_time": {"type": "string", "description": "HH:MM 24h format"},
                            "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of email addresses"}
                        },
                        "required": ["title", "date", "start_time", "end_time", "attendees"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "create_event"
            and "sprint" in str(calls[0]["args"].get("title", "")).lower()
            and "2026-04-15" in str(calls[0]["args"].get("date", ""))
            and isinstance(calls[0]["args"].get("attendees"), list)
            and len(calls[0]["args"].get("attendees", [])) == 2
        ),
    },
    # ── Three-way parallel ──────────────────────────────────────────────────
    {
        "id": "fc_parallel_triple",
        "desc": "Parallel calls — three cities at once",
        "messages": [{"role": "user", "content": "What's the weather in Tokyo, New York, and London?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {
                        "type": "object",
                        "properties": {"city": {"type": "string"}},
                        "required": ["city"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 3
            and all(c["name"] == "get_weather" for c in calls)
            and any("tokyo"    in str(c["args"].get("city", "")).lower() for c in calls)
            and any("new york" in str(c["args"].get("city", "")).lower() or "new_york" in str(c["args"].get("city", "")).lower() for c in calls)
            and any("london"   in str(c["args"].get("city", "")).lower() for c in calls)
        ),
    },
    # ── Choose from many tools ──────────────────────────────────────────────
    {
        "id": "fc_many_tools_select",
        "desc": "Select correct tool from 5 options",
        "messages": [{"role": "user", "content": "Translate 'hello world' from English to Spanish."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email",
                    "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "body"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "translate_text",
                    "description": "Translate text between languages",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "source_lang": {"type": "string"},
                            "target_lang": {"type": "string"}
                        },
                        "required": ["text", "source_lang", "target_lang"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web",
                    "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculator",
                    "description": "Evaluate a math expression",
                    "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "translate_text"
            and "hello" in str(calls[0]["args"].get("text", "")).lower()
            and ("spanish" in str(calls[0]["args"].get("target_lang", "")).lower() or "es" in str(calls[0]["args"].get("target_lang", "")).lower())
        ),
    },
    # ── Optional params — should only fill what's given ─────────────────────
    {
        "id": "fc_optional_params",
        "desc": "Optional params — only fill what's mentioned",
        "messages": [{"role": "user", "content": "Search for 'machine learning' articles."}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "search_articles",
                    "description": "Search for articles",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "category": {"type": "string", "description": "Filter by category"},
                            "sort_by": {"type": "string", "enum": ["relevance", "date"], "description": "Sort order"},
                            "limit": {"type": "integer", "description": "Max results to return"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ],
        "check": lambda calls: (
            len(calls) >= 1
            and calls[0]["name"] == "search_articles"
            and "machine learning" in str(calls[0]["args"].get("query", "")).lower()
        ),
    },
    # ── Negative: ambiguous request, should clarify not guess ───────────────
    {
        "id": "fc_negative_ambiguous",
        "desc": "Negative case — ambiguous request, should not call",
        "messages": [{"role": "user", "content": "What should I do today?"}],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather for a city",
                    "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_calendar_events",
                    "description": "Get calendar events for a date",
                    "parameters": {"type": "object", "properties": {"date": {"type": "string"}}, "required": ["date"]}
                }
            }
        ],
        "check": lambda calls: len(calls) == 0,
    },
]
