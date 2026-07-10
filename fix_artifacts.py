#!/usr/bin/env python3
"""Fix template artifacts and duplicates in app/questions.json."""

import json
import re
import random
from collections import Counter

random.seed(42)

# STEP 1: Load
with open("app/questions.json", "r") as f:
    questions = json.load(f)
print(f"Loaded {len(questions)} questions")

# STEP 2: Strip markers
def strip_markers(text):
    text = re.sub(r"\s*\(variation\s*\d+\)\s*$", "", text)
    text = re.sub(r"\s*\(variation_\d+\)\s*$", "", text)
    text = re.sub(r"\s*\(Scenario\s*\d+\)", "", text)
    text = re.sub(r"\s*\(scenario\s*\d+\)", "", text)
    text = re.sub(r"\s*\[context\s*\d+\]", "", text)
    text = re.sub(r"\s*\[scenario\s*\d+\]", "", text)
    return text.strip()

all_patterns = (
    r"\(variation\s*\d+\)|\(variation_\d+\)"
    r"|\(Scenario\s*\d+\)|\(scenario\s*\d+\)"
    r"|\[context\s*\d+\]|\[scenario\s*\d+\]"
)
affected_count = sum(1 for q in questions if re.search(all_patterns, q["question_text"]))
print(f"Questions with template markers: {affected_count}")

# STEP 3: Clean and deduplicate
seen = {}
kept = []
removed = []
for q in questions:
    cleaned_text = strip_markers(q["question_text"])
    if cleaned_text in seen:
        removed.append(q)
    else:
        seen[cleaned_text] = True
        q["question_text"] = cleaned_text
        kept.append(q)

print(f"Removed {len(removed)} duplicate questions")
print(f"Remaining: {len(kept)} unique questions")

# STEP 4: Calculate needs
remaining_answers = Counter(q["correct_answer"] for q in kept)
print(f"Remaining answer distribution: {dict(sorted(remaining_answers.items()))}")
target_per_answer = 2500
needed_per_answer = {}
for ans in "ABCD":
    needed_per_answer[ans] = target_per_answer - remaining_answers.get(ans, 0)
total_needed = sum(needed_per_answer.values())
print(f"Need to generate {total_needed} replacement questions")
print(f"Per answer: {needed_per_answer}")
removed_topics = Counter(q["topic"] for q in removed)
print(f"Removed by topic: {dict(sorted(removed_topics.items(), key=lambda x: -x[1]))}")

# STEP 5: Generate replacement questions using parameterized templates
# Each topic has template functions that generate unique questions

def make_q(question_text, option_a, option_b, option_c, option_d, correct_answer, topic):
    return {
        "question_text": question_text,
        "option_a": option_a,
        "option_b": option_b,
        "option_c": option_c,
        "option_d": option_d,
        "correct_answer": correct_answer,
        "difficulty": "advanced",
        "topic": topic,
    }

# Topic allocation
topic_alloc = {}
allocated = 0
topics_sorted = sorted(removed_topics.items(), key=lambda x: -x[1])
for i, (topic, count) in enumerate(topics_sorted):
    if i == len(topics_sorted) - 1:
        topic_alloc[topic] = total_needed - allocated
    else:
        alloc = round(count / len(removed) * total_needed)
        topic_alloc[topic] = alloc
        allocated += alloc

print(f"Topic allocation: {topic_alloc}")

# ---- PYTHON ADVANCED QUESTION GENERATORS ----

def gen_python_advanced(n):
    """Generate n unique python_advanced questions."""
    questions_pool = []

    # Template 1: What does __slots__ prevent?
    slot_vars = [
        ("x", "y"), ("name", "age"), ("width", "height"), ("key", "value"),
        ("first", "last"), ("host", "port"), ("lat", "lng"), ("start", "end"),
        ("min_val", "max_val"), ("src", "dst"), ("left", "right"), ("row", "col"),
    ]
    for v1, v2 in slot_vars:
        q = f"What is the output of this code?\n\nclass Compact:\n    __slots__ = ('{v1}', '{v2}')\n\nobj = Compact()\nobj.{v1} = 1\nobj.{v2} = 2\ntry:\n    obj.z = 3\n    print('success')\nexcept AttributeError:\n    print('no dynamic attrs')"
        questions_pool.append(make_q(q, "no dynamic attrs", "success", "TypeError", "None", "A", "python_advanced"))

    # Template 2: MRO resolution
    method_returns = [
        ("greet", "hello"), ("process", "done"), ("validate", "valid"),
        ("execute", "ok"), ("compute", "result"), ("transform", "transformed"),
        ("render", "html"), ("serialize", "json"), ("parse", "parsed"),
        ("connect", "connected"), ("fetch", "data"), ("build", "built"),
    ]
    for method, ret in method_returns:
        q = f"What is the output of this code?\n\nclass A:\n    def {method}(self): return 'A'\nclass B(A):\n    def {method}(self): return '{ret}'\nclass C(A):\n    def {method}(self): return 'C'\nclass D(B, C):\n    pass\n\nprint(D().{method}())"
        questions_pool.append(make_q(q, ret, "C", "A", "TypeError", "A", "python_advanced"))

    # Template 3: Descriptor with validation
    types_and_vals = [
        ("int", "42", "str"), ("float", "3.14", "int"), ("str", "'hello'", "int"),
        ("list", "[1,2]", "str"), ("dict", "{'a':1}", "list"), ("tuple", "(1,2)", "dict"),
        ("bool", "True", "str"), ("set", "{1,2,3}", "list"),
    ]
    for typ, val, wrong in types_and_vals:
        q = f"What is the output of this code?\n\nclass TypeCheck:\n    def __set_name__(self, owner, name):\n        self.name = name\n    def __set__(self, obj, value):\n        if not isinstance(value, {typ}):\n            raise TypeError(f'{{self.name}} must be {typ}')\n        obj.__dict__[self.name] = value\n    def __get__(self, obj, objtype=None):\n        return obj.__dict__.get(self.name)\n\nclass Config:\n    val = TypeCheck()\n\nc = Config()\nc.val = {val}\nprint(type(c.val).__name__)"
        questions_pool.append(make_q(q, typ, wrong, "None", "TypeError", "A", "python_advanced"))

    # Template 4: dataclass field factories
    factory_types = [
        ("list", "[]", "append('x')", "1"),
        ("dict", "{}", "update({'k': 'v'})", "1"),
        ("set", "set()", "add(1)", "1"),
    ]
    for ftype, empty, mutation, expected_len in factory_types:
        q = f"What is the output of this code?\n\nfrom dataclasses import dataclass, field\n\n@dataclass\nclass Container:\n    items: {ftype} = field(default_factory={ftype})\n\na = Container()\nb = Container()\na.items.{mutation}\nprint(len(b.items))"
        questions_pool.append(make_q(q, "0", expected_len, "TypeError", "AttributeError", "A", "python_advanced"))

    # Template 5: functools.reduce
    reduce_ops = [
        ("lambda a, b: a + b", "[1, 2, 3, 4, 5]", "15"),
        ("lambda a, b: a * b", "[1, 2, 3, 4]", "24"),
        ("lambda a, b: a + b", "['a', 'b', 'c']", "abc"),
        ("lambda a, b: max(a, b)", "[3, 1, 4, 1, 5]", "5"),
        ("lambda a, b: a if a > b else b", "[10, 20, 5, 30]", "30"),
    ]
    for op, data, result in reduce_ops:
        q = f"What is the output of this code?\n\nfrom functools import reduce\n\nresult = reduce({op}, {data})\nprint(result)"
        questions_pool.append(make_q(q, str(result), "TypeError", "None", "0", "A", "python_advanced"))

    # Template 6: __new__ vs __init__
    new_scenarios = [
        ("42", "42"), ("'hello'", "hello"), ("100", "100"),
        ("True", "True"), ("3.14", "3.14"),
    ]
    for val, expected in new_scenarios:
        q = f"What is the output of this code?\n\nclass Cached:\n    _cache = {{}}\n    def __new__(cls, value):\n        if value not in cls._cache:\n            obj = super().__new__(cls)\n            obj._value = value\n            cls._cache[value] = obj\n        return cls._cache[value]\n    @property\n    def value(self):\n        return self._value\n\na = Cached({val})\nb = Cached({val})\nprint(a is b)"
        questions_pool.append(make_q(q, "True", "False", "None", "TypeError", "A", "python_advanced"))

    # Template 7: ABC abstract methods
    abstract_methods = [
        ("area", "Shape"), ("connect", "Database"), ("send", "Transport"),
        ("execute", "Command"), ("render", "View"), ("validate", "Schema"),
        ("encode", "Codec"), ("transform", "Pipeline"), ("dispatch", "Router"),
    ]
    for method, cls_name in abstract_methods:
        q = f"What is the output of this code?\n\nfrom abc import ABC, abstractmethod\n\nclass {cls_name}(ABC):\n    @abstractmethod\n    def {method}(self):\n        pass\n\nclass Concrete({cls_name}):\n    def {method}(self):\n        return '{method}_done'\n\ntry:\n    base = {cls_name}()\n    print('instantiated')\nexcept TypeError:\n    obj = Concrete()\n    print(obj.{method}())"
        questions_pool.append(make_q(q, f"{method}_done", "instantiated", "TypeError", "None", "A", "python_advanced"))

    # Template 8: Protocol classes
    protocol_methods = [
        ("__len__", "Sizeable", "[1,2,3]", "True"),
        ("__iter__", "Iterable", "(1,2,3)", "True"),
        ("__contains__", "Container", "{1,2,3}", "True"),
    ]
    for method, proto_name, instance, expected in protocol_methods:
        q = f"What is the output of this code?\n\nfrom typing import runtime_checkable, Protocol\n\n@runtime_checkable\nclass {proto_name}(Protocol):\n    def {method}(self, *args): ...\n\nprint(isinstance({instance}, {proto_name}))"
        questions_pool.append(make_q(q, expected, "False", "TypeError", "None", "A", "python_advanced"))

    # Template 9: contextlib patterns
    ctx_names = [
        "resource", "connection", "session", "lock", "timer",
        "transaction", "scope", "context", "handler", "manager",
    ]
    for name in ctx_names:
        q = f"What is the output of this code?\n\nimport contextlib\n\n@contextlib.contextmanager\ndef managed_{name}():\n    print('acquire')\n    try:\n        yield '{name}_handle'\n    finally:\n        print('release')\n\nwith managed_{name}() as h:\n    print(h)"
        questions_pool.append(make_q(q, f"acquire\\n{name}_handle\\nrelease", f"{name}_handle\\nacquire\\nrelease", "acquire\\nrelease", "TypeError", "A", "python_advanced"))

    # Template 10: itertools advanced
    itertools_scenarios = [
        ("chain([1,2], [3,4])", "[1, 2, 3, 4]", "[1, 2]", "[[1,2],[3,4]]"),
        ("chain.from_iterable([[1,2],[3,4]])", "[1, 2, 3, 4]", "[[1,2],[3,4]]", "[1, 2]"),
        ("islice(range(100), 3)", "[0, 1, 2]", "[97, 98, 99]", "range(0, 3)"),
        ("takewhile(lambda x: x < 4, [1,2,3,4,5])", "[1, 2, 3]", "[1, 2, 3, 4, 5]", "[]"),
        ("dropwhile(lambda x: x < 4, [1,2,3,4,5])", "[4, 5]", "[1, 2, 3]", "[]"),
        ("compress('ABCDE', [1,0,1,0,1])", "['A', 'C', 'E']", "['B', 'D']", "['A', 'B', 'C', 'D', 'E']"),
        ("starmap(pow, [(2,3),(3,2),(10,2)])", "[8, 9, 100]", "[6, 6, 20]", "TypeError"),
    ]
    for expr, correct, wrong1, wrong2 in itertools_scenarios:
        q = f"What is the output of this code?\n\nfrom itertools import *\n\nresult = list({expr})\nprint(result)"
        questions_pool.append(make_q(q, correct, wrong1, wrong2, "None", "A", "python_advanced"))

    # Template 11: cached_property vs property
    prop_names = [
        "data", "config", "result", "matrix", "graph",
        "tree", "index", "cache", "buffer", "state",
    ]
    for prop in prop_names:
        q = f"What is the output of this code?\n\nfrom functools import cached_property\n\nclass Loader:\n    def __init__(self):\n        self.calls = 0\n    @cached_property\n    def {prop}(self):\n        self.calls += 1\n        return f'{prop}_{{self.calls}}'\n\nobj = Loader()\n_ = obj.{prop}\n_ = obj.{prop}\nprint(obj.{prop})"
        questions_pool.append(make_q(q, f"{prop}_1", f"{prop}_3", f"{prop}_2", "None", "A", "python_advanced"))

    # Template 12: singledispatch
    dispatch_types = [
        ("int", "42", "integer: 42"),
        ("str", "'hello'", "string: hello"),
        ("list", "[1,2]", "list: 2"),
        ("float", "3.14", "float: 3.14"),
    ]
    for typ, val, expected in dispatch_types:
        label = expected.split(":")[0]
        q = f"What is the output of this code?\n\nfrom functools import singledispatch\n\n@singledispatch\ndef handle(value):\n    return f'unknown: {{value}}'\n\n@handle.register({typ})\ndef _(value):\n    return f'{label}: {{value}}'\n\nprint(handle({val}))"
        questions_pool.append(make_q(q, expected, f"unknown: {val}", "TypeError", "None", "A", "python_advanced"))

    # Template 13: weakref
    weakref_classes = ["Node", "Widget", "Handler", "Session", "Cache", "Buffer"]
    for cls in weakref_classes:
        q = f"What is the output of this code?\n\nimport weakref\n\nclass {cls}:\n    def __init__(self, name):\n        self.name = name\n\nobj = {cls}('test')\nweak = weakref.ref(obj)\nprint(weak().name)\ndel obj\nprint(weak())"
        questions_pool.append(make_q(q, "test\\nNone", "test\\ntest", "ReferenceError", "TypeError", "A", "python_advanced"))

    # Template 14: lru_cache
    cache_sizes = [2, 4, 8, 16, 32, 64, 128, 256]
    for size in cache_sizes:
        q = f"What is the output of this code?\n\nfrom functools import lru_cache\n\ncall_count = 0\n\n@lru_cache(maxsize={size})\ndef compute(x):\n    global call_count\n    call_count += 1\n    return x * x\n\ncompute(3)\ncompute(3)\ncompute(3)\nprint(call_count)"
        questions_pool.append(make_q(q, "1", "3", "0", f"{size}", "A", "python_advanced"))

    # Template 15: partial application
    partial_ops = [
        ("multiply", "a * b", "3", "12", "a=4"),
        ("add_offset", "a + b", "10", "15", "a=5"),
        ("power", "a ** b", "2", "8", "a=3"),
        ("divide", "a / b", "2", "5.0", "a=10"),
        ("modulo", "a % b", "3", "1", "a=7"),
    ]
    for name, expr, partial_val, expected, call_arg in partial_ops:
        q = f"What is the output of this code?\n\nfrom functools import partial\n\ndef {name}(a, b):\n    return {expr}\n\nfixed = partial({name}, b={partial_val})\nprint(fixed({call_arg.split('=')[1]}))"
        questions_pool.append(make_q(q, expected, "TypeError", "None", "0", "A", "python_advanced"))

    # Template 16: dataclass ordering and comparison
    dc_fields = [
        ("priority", "int", "3, 1, 2", "1"),
        ("score", "float", "3.5, 1.2, 2.8", "1.2"),
        ("rank", "int", "10, 5, 8", "5"),
    ]
    for field, ftype, vals, expected_first in dc_fields:
        v_list = vals.split(", ")
        q = f"What is the output of this code?\n\nfrom dataclasses import dataclass\n\n@dataclass(order=True)\nclass Item:\n    {field}: {ftype}\n    name: str = ''\n\nitems = [Item({v_list[0]}), Item({v_list[1]}), Item({v_list[2]})]\nprint(min(items).{field})"
        questions_pool.append(make_q(q, expected_first, v_list[0], v_list[2], "TypeError", "A", "python_advanced"))

    # Template 17: frozen dataclass
    frozen_ops = [
        ("Point", "x: int\n    y: int", "Point(1, 2)", "x", "10"),
        ("Color", "r: int\n    g: int\n    b: int", "Color(255, 0, 0)", "r", "128"),
        ("Coord", "lat: float\n    lng: float", "Coord(1.0, 2.0)", "lat", "3.0"),
    ]
    for cls, fields, init, attr, new_val in frozen_ops:
        q = f"What is the output of this code?\n\nfrom dataclasses import dataclass\n\n@dataclass(frozen=True)\nclass {cls}:\n    {fields}\n\nobj = {init}\ntry:\n    obj.{attr} = {new_val}\n    print('modified')\nexcept Exception as e:\n    print(type(e).__name__)"
        questions_pool.append(make_q(q, "FrozenInstanceError", "modified", "TypeError", "AttributeError", "A", "python_advanced"))

    # Template 18: __init_subclass__
    subclass_hooks = [
        ("register", "Animal", "Dog", "_registry"),
        ("track", "Plugin", "AuthPlugin", "_tracked"),
        ("log", "Handler", "FileHandler", "_logged"),
    ]
    for action, base, child, attr in subclass_hooks:
        q = f"What is the output of this code?\n\nclass {base}:\n    {attr} = []\n    def __init_subclass__(cls, **kwargs):\n        super().__init_subclass__(**kwargs)\n        {base}.{attr}.append(cls.__name__)\n\nclass {child}({base}):\n    pass\n\nclass Another{child}({base}):\n    pass\n\nprint(len({base}.{attr}))"
        questions_pool.append(make_q(q, "2", "0", "1", "3", "A", "python_advanced"))

    # Template 19: operator.attrgetter/itemgetter
    getter_scenarios = [
        ("itemgetter('name')", "[{'name': 'b'}, {'name': 'a'}, {'name': 'c'}]", "a"),
        ("itemgetter('age')", "[{'age': 30}, {'age': 20}, {'age': 25}]", "20"),
        ("itemgetter('score')", "[{'score': 85}, {'score': 92}, {'score': 78}]", "78"),
        ("itemgetter('priority')", "[{'priority': 3}, {'priority': 1}, {'priority': 2}]", "1"),
    ]
    for getter, data, expected in getter_scenarios:
        q = f"What is the output of this code?\n\nimport operator\n\ndata = {data}\nresult = sorted(data, key=operator.{getter})\nprint(result[0]['{getter.split(chr(39))[1]}'])"
        questions_pool.append(make_q(q, expected, "TypeError", "KeyError", "None", "A", "python_advanced"))

    # Template 20: ast module usage
    ast_exprs = [
        ("'1 + 2'", "BinOp"),
        ("'x = 5'", "Assign"),
        ("'if True: pass'", "If"),
        ("'def f(): pass'", "FunctionDef"),
        ("'class C: pass'", "ClassDef"),
        ("'import os'", "Import"),
    ]
    for expr, node_type in ast_exprs:
        q = f"What is the output of this code?\n\nimport ast\n\ntree = ast.parse({expr})\nnode = tree.body[0]\nprint(type(node).__name__)"
        questions_pool.append(make_q(q, node_type, "Module", "Expression", "Name", "A", "python_advanced"))

    random.shuffle(questions_pool)
    return questions_pool[:n]

# ---- TESTING PRODUCTION QUESTION GENERATORS ----

def gen_testing_production(n):
    """Generate n unique testing_production questions."""
    questions_pool = []

    # Template 1: pytest fixture scopes
    scopes = ["function", "class", "module", "session"]
    for scope in scopes:
        q = f"What is the scope behavior of this pytest fixture?\n\nimport pytest\n\n@pytest.fixture(scope='{scope}')\ndef db_connection():\n    conn = create_connection()\n    yield conn\n    conn.close()\n\n# How many times is db_connection created for 5 tests in one module?"
        answers = {"function": "5", "class": "Once per class", "module": "1", "session": "1"}
        if scope == "function":
            questions_pool.append(make_q(q, "5", "1", "Once per class", "0", "A", "testing_production"))
        elif scope == "module":
            questions_pool.append(make_q(q, "1", "5", "Once per class", "0", "A", "testing_production"))
        elif scope == "session":
            questions_pool.append(make_q(q, "1", "5", "Per module", "0", "A", "testing_production"))
        else:
            questions_pool.append(make_q(q, "Once per class", "5", "1", "0", "A", "testing_production"))

    # Template 2: pytest parametrize
    param_scenarios = [
        ("add", "a, b, expected", "[(1,2,3),(2,3,5),(0,0,0)]", "3"),
        ("multiply", "x, y, result", "[(2,3,6),(4,5,20),(0,1,0)]", "3"),
        ("divide", "num, den, ans", "[(10,2,5),(9,3,3),(8,4,2)]", "3"),
        ("power", "base, exp, out", "[(2,3,8),(3,2,9),(5,0,1)]", "3"),
        ("concat", "a, b, out", "[('x','y','xy'),('a','b','ab')]", "2"),
    ]
    for func, params, cases, count in param_scenarios:
        q = f"How many test cases does this parametrized test generate?\n\nimport pytest\n\n@pytest.mark.parametrize('{params}', {cases})\ndef test_{func}({params.replace(', ', ', ')}):\n    assert {func}({params.split(',')[0].strip()}, {params.split(',')[1].strip()}) == {params.split(',')[2].strip()}"
        questions_pool.append(make_q(q, count, "1", str(int(count)*2), "0", "A", "testing_production"))

    # Template 3: mock.patch usage
    mock_targets = [
        ("os.path.exists", "True", "checks if path exists"),
        ("requests.get", "Mock(status_code=200)", "mocks HTTP GET"),
        ("builtins.open", "mock_open(read_data='test')", "mocks file reading"),
        ("time.sleep", "None", "skips sleep in tests"),
        ("json.loads", "{'key': 'val'}", "mocks JSON parsing"),
        ("subprocess.run", "Mock(returncode=0)", "mocks subprocess"),
        ("socket.connect", "None", "mocks socket connection"),
        ("os.environ.get", "'test_value'", "mocks env variable"),
    ]
    for target, return_val, desc in mock_targets:
        q = f"What does this test mock achieve?\n\nfrom unittest.mock import patch, Mock\n\n@patch('{target}', return_value={return_val})\ndef test_function(mock_obj):\n    # This {desc}\n    result = function_under_test()\n    mock_obj.assert_called_once()\n    assert result is not None\n\n# What happens if the mock is not applied?"
        questions_pool.append(make_q(q, f"Real {target.split('.')[0]} is called", "Test passes anyway", "TypeError is raised", "Mock is auto-applied", "A", "testing_production"))

    # Template 4: MagicMock spec
    spec_classes = [
        ("DatabaseConnection", "connect, execute, close"),
        ("HTTPClient", "get, post, put, delete"),
        ("FileHandler", "open, read, write, close"),
        ("CacheService", "get, set, delete, clear"),
        ("MessageQueue", "publish, subscribe, ack"),
        ("Logger", "debug, info, warning, error"),
    ]
    for cls, methods in spec_classes:
        method_list = methods.split(", ")
        q = f"What happens when you access an undefined method on a spec'd mock?\n\nfrom unittest.mock import MagicMock\n\nclass {cls}:\n    def {method_list[0]}(self): pass\n    def {method_list[1]}(self): pass\n\nmock = MagicMock(spec={cls})\ntry:\n    mock.undefined_method()\n    print('allowed')\nexcept AttributeError:\n    print('blocked')"
        questions_pool.append(make_q(q, "blocked", "allowed", "TypeError", "None", "A", "testing_production"))

    # Template 5: side_effect usage
    side_effects = [
        ("[1, 2, 3]", "first call returns 1, second returns 2, third returns 3"),
        ("ValueError('bad input')", "raises ValueError on every call"),
        ("lambda x: x * 2", "returns double the input"),
        ("[None, None, 'result']", "returns None twice then 'result'"),
        ("itertools.cycle([True, False])", "alternates True and False"),
    ]
    for effect, desc in side_effects:
        q = f"What does side_effect={effect} do on a mock?\n\nfrom unittest.mock import Mock\nimport itertools\n\nmock = Mock(side_effect={effect})\n# The mock {desc}"
        questions_pool.append(make_q(q, desc, "Returns None always", "Raises TypeError", "Ignores the effect", "A", "testing_production"))

    # Template 6: pytest fixtures with autouse
    autouse_scenarios = [
        ("reset_db", "Runs before every test automatically", "Only on marked tests", "module"),
        ("setup_logging", "Runs before every test automatically", "Runs once per session", "function"),
        ("clear_cache", "Runs before every test automatically", "Only when imported", "function"),
    ]
    for fixture, correct, wrong, scope in autouse_scenarios:
        q = f"What is the behavior of this autouse fixture?\n\nimport pytest\n\n@pytest.fixture(autouse=True, scope='{scope}')\ndef {fixture}():\n    # setup\n    yield\n    # teardown"
        questions_pool.append(make_q(q, correct, wrong, "Raises error without explicit use", "Does nothing", "A", "testing_production"))

    # Template 7: coverage patterns
    coverage_scenarios = [
        ("branch", "Measures which branches (if/else) are taken", "Only counts line execution"),
        ("line", "Counts which lines are executed", "Measures branch paths"),
        ("path", "Tracks complete execution paths through code", "Only counts functions"),
    ]
    for cov_type, correct, wrong in coverage_scenarios:
        q = f"What does {cov_type} coverage measure in Python testing?\n\n# Running: pytest --cov --cov-branch\n# or: coverage run --branch"
        questions_pool.append(make_q(q, correct, wrong, "Counts import statements", "Measures memory usage", "A", "testing_production"))

    # Template 8: property-based testing with hypothesis
    hypothesis_strategies = [
        ("integers()", "generates random integers", "always returns 0"),
        ("text()", "generates random Unicode strings", "only returns empty string"),
        ("lists(integers())", "generates lists of random integers", "only returns empty list"),
        ("floats(allow_nan=False)", "generates floats excluding NaN", "only returns 0.0"),
        ("booleans()", "generates True or False randomly", "always returns True"),
        ("dictionaries(text(), integers())", "generates dicts with string keys and int values", "returns empty dict"),
    ]
    for strategy, correct, wrong in hypothesis_strategies:
        q = f"What does the hypothesis strategy {strategy} do?\n\nfrom hypothesis import given\nfrom hypothesis.strategies import *\n\n@given({strategy})\ndef test_property(value):\n    # hypothesis {correct}\n    assert some_property(value)"
        questions_pool.append(make_q(q, correct, wrong, "Raises on first failure only", "Runs exactly once", "A", "testing_production"))

    # Template 9: conftest.py behavior
    conftest_scenarios = [
        ("fixtures are available to all tests in the directory and subdirectories", "fixtures are global", "fixtures only work in conftest.py itself"),
        ("plugins registered in conftest.py apply to all tests in scope", "plugins are ignored", "plugins only work with explicit import"),
        ("hooks defined in conftest.py are auto-discovered by pytest", "hooks must be imported", "hooks only work in root conftest"),
    ]
    for correct, wrong1, wrong2 in conftest_scenarios:
        q = f"What is true about conftest.py in pytest?\n\n# conftest.py placed in test directory\nimport pytest\n\n@pytest.fixture\ndef shared_resource():\n    return create_resource()"
        questions_pool.append(make_q(q, correct, wrong1, wrong2, "conftest.py is deprecated", "A", "testing_production"))

    # Template 10: test doubles classification
    doubles = [
        ("Stub", "provides predetermined responses to method calls", "records calls for later verification"),
        ("Mock", "verifies that expected interactions occurred", "provides real implementation"),
        ("Spy", "wraps real object and records interactions", "prevents any real calls"),
        ("Fake", "provides working implementation unsuitable for production", "always raises errors"),
        ("Dummy", "passed around but never used; fills parameter lists", "provides complex behavior"),
    ]
    for double_type, correct, wrong in doubles:
        q = f"What is a {double_type} in testing terminology?\n\n# In the context of test doubles and testing patterns"
        questions_pool.append(make_q(q, f"A {double_type} {correct}", f"A {double_type} {wrong}", f"A {double_type} is the same as a mock", f"A {double_type} is not used in Python", "A", "testing_production"))

    # Template 11: pytest markers
    markers = [
        ("skip", "unconditionally skips the test"),
        ("skipif", "skips test if condition is True"),
        ("xfail", "marks test as expected to fail"),
        ("timeout", "fails test if it exceeds time limit"),
        ("filterwarnings", "controls warning behavior for the test"),
    ]
    for marker, desc in markers:
        q = f"What does @pytest.mark.{marker} do?\n\nimport pytest\n\n@pytest.mark.{marker}\ndef test_example():\n    pass"
        questions_pool.append(make_q(q, desc, "Marks test for parallel execution", "Removes test from collection", "Runs test multiple times", "A", "testing_production"))

    # Template 12: Integration testing patterns
    integration_patterns = [
        ("arrange-act-assert", "Structures test in setup, action, and verification phases"),
        ("given-when-then", "BDD style: given preconditions, when action, then outcome"),
        ("fixture-teardown", "Sets up state before test and cleans up after"),
        ("test-container", "Uses Docker containers for integration dependencies"),
    ]
    for pattern, desc in integration_patterns:
        q = f"What is the '{pattern}' pattern in integration testing?\n\n# Applied to Python integration tests with pytest"
        questions_pool.append(make_q(q, desc, "A way to skip slow tests", "Only for unit tests", "Deprecated testing approach", "A", "testing_production"))

    # Template 13: assert_called patterns
    assert_patterns = [
        ("assert_called_once_with(42)", "Passes only if mock was called exactly once with argument 42"),
        ("assert_called_with('test')", "Passes if the last call used argument 'test'"),
        ("assert_not_called()", "Passes only if mock was never called"),
        ("assert_any_call(1, 2)", "Passes if mock was called with (1, 2) at any point"),
    ]
    for assertion, desc in assert_patterns:
        q = f"What does mock.{assertion} verify?\n\nfrom unittest.mock import Mock\n\nmock = Mock()\n# ... some code that may call mock ...\nmock.{assertion}"
        questions_pool.append(make_q(q, desc, "Always passes", "Checks return value", "Resets the mock", "A", "testing_production"))

    random.shuffle(questions_pool)
    return questions_pool[:n]

# ---- PERFORMANCE OPTIMIZATION QUESTION GENERATORS ----

def gen_performance_optimization(n):
    """Generate n unique performance_optimization questions."""
    questions_pool = []

    # Template 1: Time complexity
    complexities = [
        ("list.append(x)", "O(1) amortized", "O(n)", "O(log n)"),
        ("list.insert(0, x)", "O(n)", "O(1)", "O(log n)"),
        ("dict[key] = value", "O(1) average", "O(n)", "O(log n)"),
        ("set.add(x)", "O(1) average", "O(n)", "O(log n)"),
        ("list.sort()", "O(n log n)", "O(n)", "O(n^2)"),
        ("bisect.insort(lst, x)", "O(n)", "O(log n)", "O(n log n)"),
        ("heapq.heappush(heap, x)", "O(log n)", "O(n)", "O(1)"),
        ("collections.deque.appendleft(x)", "O(1)", "O(n)", "O(log n)"),
        ("x in set_obj", "O(1) average", "O(n)", "O(log n)"),
        ("x in list_obj", "O(n)", "O(1)", "O(log n)"),
        ("dict.get(key)", "O(1) average", "O(n)", "O(log n)"),
        ("sorted(iterable)", "O(n log n)", "O(n)", "O(n^2)"),
    ]
    for op, correct, wrong1, wrong2 in complexities:
        q = f"What is the time complexity of this Python operation?\n\n# Operation: {op}"
        questions_pool.append(make_q(q, correct, wrong1, wrong2, "O(2^n)", "A", "performance_optimization"))

    # Template 2: Memory optimization
    mem_techniques = [
        ("__slots__", "Reduces memory by eliminating per-instance __dict__", "Increases memory for type safety"),
        ("generators vs lists", "Generators use O(1) memory regardless of sequence length", "Generators are always slower"),
        ("array.array vs list", "array.array stores typed values more compactly", "array.array is always faster"),
        ("sys.intern()", "Reuses string objects to save memory for repeated strings", "Makes strings immutable"),
        ("weakref", "Allows garbage collection of referenced objects", "Makes references faster"),
        ("memoryview", "Provides zero-copy access to buffer data", "Copies data for safety"),
        ("tuple vs list", "Tuples use less memory and are cached by Python", "Tuples are always faster"),
    ]
    for technique, correct, wrong in mem_techniques:
        q = f"What memory optimization does {technique} provide?\n\n# In the context of Python memory management"
        questions_pool.append(make_q(q, correct, wrong, "No memory benefit", "Only works in CPython", "A", "performance_optimization"))

    # Template 3: Profiling tools
    profiling_tools = [
        ("cProfile", "Deterministic profiling of function call times and counts"),
        ("line_profiler", "Line-by-line timing of decorated functions"),
        ("memory_profiler", "Line-by-line memory usage tracking"),
        ("tracemalloc", "Traces memory allocations to their source"),
        ("timeit", "Accurate timing of small code snippets"),
        ("py-spy", "Sampling profiler that works without code modification"),
    ]
    for tool, desc in profiling_tools:
        q = f"What does {tool} do in Python performance analysis?\n\n# Usage: python -m {tool.replace('-', '_')} script.py"
        questions_pool.append(make_q(q, desc, "Optimizes code automatically", "Only works in production", "Replaces unittest", "A", "performance_optimization"))

    # Template 4: Generator vs list comprehension
    gen_scenarios = [
        ("sum(x*x for x in range(1000000))", "Uses O(1) memory - no list created", "Creates a list of 1M items"),
        ("any(is_valid(x) for x in items)", "Short-circuits on first True - may not process all items", "Always processes all items"),
        ("' '.join(str(x) for x in range(100))", "Generator is slightly slower than list here due to join internals", "Generator is always faster"),
        ("max(len(line) for line in file)", "Processes one line at a time - O(1) memory", "Loads entire file into memory"),
    ]
    for expr, correct, wrong in gen_scenarios:
        q = f"What is the memory behavior of this expression?\n\nresult = {expr}"
        questions_pool.append(make_q(q, correct, wrong, "Raises MemoryError", "Same as list version", "A", "performance_optimization"))

    # Template 5: Collection choice for performance
    collection_choices = [
        ("frequent membership testing", "set or frozenset - O(1) lookup", "list - simpler API"),
        ("ordered unique elements", "dict (Python 3.7+) - preserves insertion order", "sorted list - always sorted"),
        ("FIFO queue operations", "collections.deque - O(1) append and popleft", "list - built-in type"),
        ("counting occurrences", "collections.Counter - optimized for counting", "manual dict with get()"),
        ("default values for missing keys", "collections.defaultdict - avoids KeyError", "try/except on regular dict"),
        ("priority queue", "heapq - O(log n) push and pop", "sorted list - O(n) insert"),
        ("bidirectional mapping", "Two dicts or bidict library", "Single dict with reverse lookup O(n)"),
        ("LRU cache", "functools.lru_cache - built-in with maxsize", "Manual dict with timestamp"),
    ]
    for use_case, correct, wrong in collection_choices:
        q = f"What is the best Python collection for {use_case}?\n\n# Considering time complexity and standard library options"
        questions_pool.append(make_q(q, correct, wrong, "numpy array", "Regular list", "A", "performance_optimization"))

    # Template 6: String concatenation performance
    string_scenarios = [
        ("''.join(parts)", "O(n) total - single pass concatenation", "O(n^2) - creates intermediate strings"),
        ("f-string formatting", "Fast for simple interpolation - compiled at parse time", "Slower than % formatting"),
        ("io.StringIO for building", "Efficient for many small writes", "Same as += concatenation"),
        ("+= in a loop", "O(n^2) in worst case - may create copies each iteration", "O(n) - optimized by CPython"),
    ]
    for technique, correct, wrong in string_scenarios:
        q = f"What is the performance characteristic of {technique} for string building?\n\n# Building a large string from many parts"
        questions_pool.append(make_q(q, correct, wrong, "Always O(1)", "Depends on string length only", "A", "performance_optimization"))

    # Template 7: Caching strategies
    cache_strategies = [
        ("lru_cache", "Evicts least recently used entries when maxsize reached", "Evicts oldest entries first"),
        ("cache (unbounded)", "Never evicts - grows without limit", "Automatically clears on memory pressure"),
        ("TTL cache", "Entries expire after a time-to-live period", "Entries never expire"),
        ("memoization", "Caches function results based on arguments", "Caches all variable assignments"),
    ]
    for strategy, correct, wrong in cache_strategies:
        q = f"What is the behavior of a {strategy} strategy in Python?\n\n# Considering functools and cachetools patterns"
        questions_pool.append(make_q(q, correct, wrong, "Only works with pure functions", "Requires database backend", "A", "performance_optimization"))

    # Template 8: NumPy vs pure Python
    numpy_scenarios = [
        ("element-wise multiplication of 1M numbers", "NumPy is 10-100x faster due to vectorized C operations", "Pure Python is faster for small arrays"),
        ("summing a large array", "NumPy uses optimized BLAS routines", "sum() builtin is equally fast"),
        ("filtering with boolean mask", "NumPy boolean indexing avoids Python loop overhead", "List comprehension is faster"),
    ]
    for scenario, correct, wrong in numpy_scenarios:
        q = f"Why is NumPy faster for {scenario}?\n\n# Comparing import numpy as np; np.array vs pure Python list"
        questions_pool.append(make_q(q, correct, wrong, "NumPy uses more memory", "No real difference", "A", "performance_optimization"))

    # Template 9: GIL and threading
    gil_scenarios = [
        ("CPU-bound tasks", "Threading provides no speedup due to GIL - use multiprocessing", "Threading gives linear speedup"),
        ("I/O-bound tasks", "Threading helps because GIL is released during I/O waits", "GIL prevents all parallelism"),
        ("C extension calls", "GIL can be released in C extensions for true parallelism", "C extensions always hold the GIL"),
        ("asyncio event loop", "Single-threaded but efficiently handles I/O concurrency", "Uses multiple threads internally"),
    ]
    for scenario, correct, wrong in gil_scenarios:
        q = f"How does Python's GIL affect {scenario}?\n\n# In CPython implementation"
        questions_pool.append(make_q(q, correct, wrong, "GIL does not exist in Python 3", "Only affects Windows", "A", "performance_optimization"))

    random.shuffle(questions_pool)
    return questions_pool[:n]


# ---- ASYNC PATTERNS QUESTION GENERATORS ----

def gen_async_patterns(n):
    """Generate n unique async_patterns questions."""
    questions_pool = []

    # Template 1: asyncio basics
    async_basics = [
        ("asyncio.run(main())", "Creates event loop, runs coroutine, and closes loop", "Only schedules the coroutine"),
        ("await asyncio.sleep(1)", "Suspends coroutine for 1 second, allowing other tasks to run", "Blocks the entire thread"),
        ("asyncio.create_task(coro())", "Schedules coroutine to run concurrently in current loop", "Runs coroutine immediately to completion"),
        ("asyncio.gather(*coros)", "Runs multiple coroutines concurrently and collects results", "Runs coroutines sequentially"),
        ("async for item in aiter", "Iterates asynchronously, awaiting each next value", "Same as regular for loop"),
        ("async with resource as r", "Asynchronous context manager - awaits __aenter__ and __aexit__", "Same as regular with statement"),
    ]
    for expr, correct, wrong in async_basics:
        q = f"What does {expr} do?\n\nimport asyncio\n\nasync def main():\n    {expr.replace('main()', 'helper()')}"
        questions_pool.append(make_q(q, correct, wrong, "Raises RuntimeError", "Deprecated in Python 3.10+", "A", "async_patterns"))

    # Template 2: TaskGroup (Python 3.11+)
    taskgroup_scenarios = [
        ("all tasks complete successfully", "All results are available after the group exits"),
        ("one task raises an exception", "All other tasks are cancelled and ExceptionGroup is raised"),
        ("task is cancelled externally", "The TaskGroup handles cancellation and propagates it"),
    ]
    for scenario, correct in taskgroup_scenarios:
        q = f"What happens in asyncio.TaskGroup when {scenario}?\n\nimport asyncio\n\nasync def main():\n    async with asyncio.TaskGroup() as tg:\n        tg.create_task(task_a())\n        tg.create_task(task_b())"
        questions_pool.append(make_q(q, correct, "Tasks continue running independently", "Only the first task runs", "RuntimeError is raised", "A", "async_patterns"))

    # Template 3: asyncio synchronization
    sync_primitives = [
        ("asyncio.Lock()", "Only one coroutine can hold the lock at a time", "Multiple coroutines can hold it"),
        ("asyncio.Semaphore(3)", "At most 3 coroutines can acquire it simultaneously", "Exactly 3 coroutines must acquire it"),
        ("asyncio.Event()", "Coroutines can wait until the event is set by another coroutine", "Automatically triggers on timer"),
        ("asyncio.Condition()", "Allows coroutines to wait for and notify about state changes", "Same as threading.Condition"),
        ("asyncio.Queue(maxsize=10)", "Bounded async queue - put() blocks when full", "Drops items when full"),
        ("asyncio.BoundedSemaphore(5)", "Like Semaphore but raises ValueError if released too many times", "Same as regular Semaphore"),
    ]
    for primitive, correct, wrong in sync_primitives:
        q = f"What is the behavior of {primitive}?\n\nimport asyncio\n\nasync def worker(prim):\n    async with prim:\n        await do_work()"
        questions_pool.append(make_q(q, correct, wrong, "Blocks the event loop", "Only works with threads", "A", "async_patterns"))

    # Template 4: async context managers
    async_ctx_scenarios = [
        ("aiohttp.ClientSession()", "Manages connection pool - reuses connections for multiple requests"),
        ("aiofiles.open('file.txt')", "Opens file with async I/O - does not block event loop"),
        ("asyncio.timeout(5.0)", "Cancels the enclosed operation after 5 seconds"),
        ("async_generator_context()", "Manages async setup and teardown around yielded value"),
    ]
    for ctx, desc in async_ctx_scenarios:
        q = f"What does this async context manager provide?\n\nasync with {ctx} as resource:\n    await use(resource)"
        questions_pool.append(make_q(q, desc, "Same as synchronous version", "Blocks until resource is ready", "Only works in main coroutine", "A", "async_patterns"))

    # Template 5: async iterators
    async_iter_patterns = [
        ("async def gen():\n    for i in range(5):\n        await asyncio.sleep(0.1)\n        yield i", "Produces values with async delays between them"),
        ("async def stream():\n    async for chunk in reader:\n        yield process(chunk)", "Transforms an async stream element by element"),
        ("async def merge(*iters):\n    for it in iters:\n        async for item in it:\n            yield item", "Concatenates multiple async iterables sequentially"),
    ]
    for code, desc in async_iter_patterns:
        q = f"What does this async generator do?\n\nimport asyncio\n\n{code}\n\nasync def main():\n    async for val in gen():\n        print(val)"
        questions_pool.append(make_q(q, desc, "Produces all values at once", "Blocks the event loop", "Raises StopAsyncIteration immediately", "A", "async_patterns"))

    # Template 6: Error handling in async
    async_error_scenarios = [
        ("unhandled exception in task", "Exception is stored and raised when task result is awaited", "Exception crashes the event loop"),
        ("CancelledError in task", "Task's cancel() was called - coroutine receives CancelledError", "Task silently stops"),
        ("TimeoutError from asyncio.wait_for", "Coroutine exceeded the specified timeout duration", "Network connection timed out"),
        ("RuntimeError: no running event loop", "Async code called outside of asyncio.run() or similar", "Event loop crashed"),
    ]
    for scenario, correct, wrong in async_error_scenarios:
        q = f"What causes {scenario} in asyncio?\n\nimport asyncio"
        questions_pool.append(make_q(q, correct, wrong, "Bug in asyncio library", "Only happens in debug mode", "A", "async_patterns"))

    # Template 7: Graceful shutdown
    shutdown_patterns = [
        ("signal handling", "Register signal handlers to initiate graceful shutdown of running tasks"),
        ("asyncio.shield()", "Protects a coroutine from cancellation during shutdown"),
        ("task.cancel() + await task", "Requests cancellation and waits for cleanup to complete"),
        ("asyncio.all_tasks()", "Gets all running tasks for batch cancellation during shutdown"),
    ]
    for pattern, desc in shutdown_patterns:
        q = f"What role does {pattern} play in async graceful shutdown?\n\nimport asyncio\nimport signal"
        questions_pool.append(make_q(q, desc, "Immediately kills all tasks", "Only works on Linux", "Deprecated in Python 3.11", "A", "async_patterns"))

    # Template 8: asyncio.Queue patterns
    queue_patterns = [
        ("producer-consumer", "Multiple producers put items, multiple consumers process them concurrently"),
        ("rate limiting", "Queue with maxsize limits concurrent work in progress"),
        ("work distribution", "Single producer distributes tasks to a pool of consumer workers"),
        ("pipeline stages", "Chain of queues connecting processing stages"),
    ]
    for pattern, desc in queue_patterns:
        q = f"What is the {pattern} pattern with asyncio.Queue?\n\nimport asyncio\n\nasync def worker(queue):\n    while True:\n        item = await queue.get()\n        await process(item)\n        queue.task_done()"
        questions_pool.append(make_q(q, desc, "Synchronous processing only", "Requires threading", "Single consumer only", "A", "async_patterns"))

    # Template 9: Performance patterns
    perf_patterns = [
        ("connection pooling", "Reuses established connections to avoid handshake overhead per request"),
        ("batching requests", "Groups multiple small requests into fewer larger ones for efficiency"),
        ("semaphore throttling", "Limits concurrent operations to prevent overwhelming a service"),
        ("gather vs create_task", "gather() awaits all results; create_task() allows fire-and-forget"),
    ]
    for pattern, desc in perf_patterns:
        q = f"What optimization does {pattern} provide in async Python?\n\nimport asyncio\nimport aiohttp"
        questions_pool.append(make_q(q, desc, "Reduces memory usage only", "Only benefits single requests", "No real benefit over sync", "A", "async_patterns"))

    random.shuffle(questions_pool)
    return questions_pool[:n]

# ---- ERROR HANDLING QUESTION GENERATORS ----

def gen_error_handling(n):
    """Generate n unique error_handling questions."""
    questions_pool = []

    # Template 1: Exception chaining
    chain_scenarios = [
        ("raise ValueError('bad') from original", "__cause__ is set to original - explicit chaining"),
        ("raise ValueError('bad') inside except block", "__context__ is set automatically - implicit chaining"),
        ("raise ValueError('bad') from None", "Suppresses the exception context chain"),
    ]
    for code, desc in chain_scenarios:
        q = f"What happens with exception chaining when you use:\n\ntry:\n    risky_operation()\nexcept KeyError as original:\n    {code}"
        questions_pool.append(make_q(q, desc, "Original exception is lost", "Both exceptions are raised simultaneously", "SyntaxError", "A", "error_handling"))

    # Template 2: ExceptionGroup (Python 3.11+)
    eg_scenarios = [
        ("except* ValueError as eg", "Catches only ValueError exceptions from the group"),
        ("except* (TypeError, ValueError) as eg", "Catches both TypeError and ValueError from the group"),
        ("multiple except* clauses", "Each clause handles its matching exceptions independently"),
        ("unmatched exceptions", "Propagate in a new ExceptionGroup to outer handlers"),
    ]
    for handler, desc in eg_scenarios:
        q = f"What does {handler} do with ExceptionGroup?\n\ntry:\n    async with asyncio.TaskGroup() as tg:\n        tg.create_task(may_fail_1())\n        tg.create_task(may_fail_2())\n{handler.split(' as')[0] if 'as' in handler else handler}:\n    # handler code"
        questions_pool.append(make_q(q, desc, "Catches all exceptions regardless of type", "Raises RuntimeError", "Only works with asyncio", "A", "error_handling"))

    # Template 3: contextlib.suppress
    suppress_exceptions = [
        ("FileNotFoundError", "silently ignores if file does not exist"),
        ("KeyError", "silently ignores if key is missing from dict"),
        ("AttributeError", "silently ignores if attribute does not exist"),
        ("ValueError", "silently ignores value conversion errors"),
        ("ImportError", "silently ignores if module is not available"),
        ("PermissionError", "silently ignores permission denied errors"),
    ]
    for exc, desc in suppress_exceptions:
        q = f"What does contextlib.suppress({exc}) do?\n\nfrom contextlib import suppress\n\nwith suppress({exc}):\n    operation_that_might_raise()\n\nprint('continues here')"
        questions_pool.append(make_q(q, f"Code {desc} and continues", f"Logs the {exc} then continues", f"Re-raises after logging", "Catches all exceptions", "A", "error_handling"))

    # Template 4: Custom exception hierarchies
    hierarchy_scenarios = [
        ("ApplicationError -> ValidationError, DatabaseError", "Catching ApplicationError catches both subtypes"),
        ("Base -> Retryable -> Timeout, ConnectionLost", "Retryable exceptions can be automatically retried"),
        ("APIError -> ClientError (4xx), ServerError (5xx)", "Different handling based on error category"),
    ]
    for hierarchy, desc in hierarchy_scenarios:
        q = f"What is the benefit of this exception hierarchy?\n\nclass {hierarchy.split(' -> ')[0]}(Exception): pass\n# {hierarchy}\n\n# {desc}"
        questions_pool.append(make_q(q, desc, "No benefit over using Exception directly", "Python does not support exception hierarchies", "Only works with try/except/finally", "A", "error_handling"))

    # Template 5: traceback module
    traceback_funcs = [
        ("traceback.format_exc()", "Returns the current exception traceback as a string"),
        ("traceback.print_exc()", "Prints the current exception traceback to stderr"),
        ("traceback.extract_tb(tb)", "Extracts structured traceback information as a list"),
        ("traceback.format_exception(exc)", "Formats exception with full traceback as list of strings"),
    ]
    for func, desc in traceback_funcs:
        q = f"What does {func} do?\n\nimport traceback\n\ntry:\n    1/0\nexcept:\n    result = {func}"
        questions_pool.append(make_q(q, desc, "Raises the exception again", "Returns None", "Only works in debug mode", "A", "error_handling"))

    # Template 6: sys.exc_info()
    exc_info_parts = [
        ("sys.exc_info()[0]", "The exception type (class)"),
        ("sys.exc_info()[1]", "The exception instance (value)"),
        ("sys.exc_info()[2]", "The traceback object"),
    ]
    for expr, desc in exc_info_parts:
        q = f"What does {expr} return inside an except block?\n\nimport sys\n\ntry:\n    raise ValueError('test')\nexcept:\n    info = {expr}"
        questions_pool.append(make_q(q, desc, "Always returns None", "The exception message string", "A tuple of all exceptions", "A", "error_handling"))

    # Template 7: warnings module
    warning_types = [
        ("DeprecationWarning", "Function or feature will be removed in future version"),
        ("FutureWarning", "Behavior will change in future version - visible to end users"),
        ("UserWarning", "Generic warning for user-facing issues"),
        ("ResourceWarning", "Resource like file or connection was not properly closed"),
        ("RuntimeWarning", "Dubious runtime behavior detected"),
    ]
    for warning, desc in warning_types:
        q = f"When should you use {warning}?\n\nimport warnings\nwarnings.warn('message', {warning})"
        questions_pool.append(make_q(q, desc, "System is about to crash", "Only for testing", "Memory is running low", "A", "error_handling"))

    # Template 8: Retry decorators
    retry_scenarios = [
        ("max_retries=3, backoff=exponential", "Retries up to 3 times with increasing delays between attempts"),
        ("retry_on=(ConnectionError, Timeout)", "Only retries for specific exception types"),
        ("max_retries=5, jitter=True", "Adds random jitter to prevent thundering herd problem"),
    ]
    for config, desc in retry_scenarios:
        q = f"What does a retry decorator with {config} do?\n\n@retry({config})\ndef call_service():\n    return requests.get(url)"
        questions_pool.append(make_q(q, desc, "Retries indefinitely", "Only retries once", "Caches the last result", "A", "error_handling"))

    # Template 9: Circuit breaker pattern
    cb_states = [
        ("CLOSED", "Normal operation - requests pass through, failures are counted"),
        ("OPEN", "All requests fail immediately without calling the service"),
        ("HALF-OPEN", "Limited requests pass through to test if service recovered"),
    ]
    for state, desc in cb_states:
        q = f"What happens in the {state} state of a circuit breaker?\n\n# Circuit breaker pattern for resilient service calls"
        questions_pool.append(make_q(q, desc, "All requests are queued", "Requests are redirected", "Service is restarted", "A", "error_handling"))

    random.shuffle(questions_pool)
    return questions_pool[:n]


# ---- SECURITY AUTH QUESTION GENERATORS ----

def gen_security_auth(n):
    """Generate n unique security_auth questions."""
    questions_pool = []

    security_topics = [
        ("SQL injection prevention", "Use parameterized queries with placeholders, never string concatenation", "Escape special characters manually"),
        ("XSS prevention", "Escape/sanitize user input before rendering in HTML", "Block all JavaScript"),
        ("CSRF protection", "Include unique token in forms and validate on submission", "Use HTTPS only"),
        ("JWT token validation", "Verify signature, check expiration, validate claims", "Only check if token exists"),
        ("Password hashing", "Use bcrypt/argon2 with salt - never store plaintext", "Use SHA-256 without salt"),
        ("Rate limiting", "Limit requests per IP/user to prevent brute force attacks", "Block IPs permanently after 1 failure"),
        ("Input validation", "Validate type, length, format, and range on server side", "Only validate on client side"),
        ("Secrets management", "Use environment variables or vault service, never commit secrets", "Store in config file with restricted permissions"),
        ("Session fixation", "Regenerate session ID after authentication", "Keep same session ID throughout"),
        ("Content Security Policy", "HTTP header that restricts resource loading sources", "Server-side content filter"),
        ("CORS configuration", "Specifies which origins can make cross-origin requests", "Blocks all cross-origin requests"),
        ("OAuth2 PKCE flow", "Prevents authorization code interception in public clients", "Only for mobile apps"),
        ("HTTP-only cookies", "Prevents JavaScript access to session cookies", "Makes cookies encrypted"),
        ("Timing attack prevention", "Use constant-time comparison for secrets", "Add random delays"),
        ("Certificate pinning", "Validates server certificate against known hash", "Uses longer certificate chains"),
        ("API key rotation", "Regularly replace keys to limit exposure window", "Use longer keys instead"),
        ("Privilege escalation", "Process runs with minimum required permissions", "Run everything as admin for simplicity"),
        ("Input sanitization", "Remove or encode dangerous characters before processing", "Reject all input with special characters"),
        ("Secure headers", "X-Frame-Options, X-Content-Type-Options prevent clickjacking and MIME sniffing", "Only needed for banking sites"),
        ("Two-factor authentication", "Combines something you know with something you have", "Uses two different passwords"),
        ("Token refresh pattern", "Short-lived access tokens with long-lived refresh tokens", "Single long-lived access token"),
        ("OWASP top 10", "Most critical web application security risks classification", "Python-specific vulnerability list"),
        ("Broken authentication", "Session management flaws allowing account compromise", "Using weak passwords only"),
        ("Sensitive data exposure", "Encrypting data at rest and in transit with proper key management", "Hiding URLs from users"),
        ("Security misconfiguration", "Default configs, unnecessary features, missing patches", "Only affects production"),
    ]
    for topic, correct, wrong in security_topics:
        q = f"What is the correct approach for {topic}?\n\n# In a Python web application context"
        questions_pool.append(make_q(q, correct, wrong, "Not relevant for Python applications", "Handled automatically by the framework", "A", "security_auth"))

    random.shuffle(questions_pool)
    return questions_pool[:n]


# ---- DEVOPS DEPLOYMENT QUESTION GENERATORS ----

def gen_devops_deployment(n):
    """Generate n unique devops_deployment questions."""
    questions_pool = []

    devops_topics = [
        ("Docker multi-stage build", "Reduces final image size by separating build and runtime stages", "Runs multiple containers simultaneously"),
        ("Docker COPY vs ADD", "COPY is simpler and preferred; ADD handles URLs and tar extraction", "ADD is deprecated"),
        ("Dockerfile layer caching", "Unchanged layers are cached - put rarely changing commands first", "All layers are rebuilt every time"),
        ("docker-compose volumes", "Persist data between container restarts and share between containers", "Increase container memory"),
        ("CI/CD pipeline stages", "Build, test, deploy stages run sequentially with gates between them", "All stages run simultaneously"),
        ("Blue-green deployment", "Two identical environments - switch traffic to new version atomically", "Gradual percentage rollout"),
        ("Canary deployment", "Route small percentage of traffic to new version to detect issues", "Deploy to a test environment first"),
        ("Rolling update", "Gradually replace instances of old version with new version", "Replace all instances at once"),
        ("Health checks", "Automated probes that verify service is functioning correctly", "Manual verification by operators"),
        ("Container orchestration", "Automated deployment, scaling, and management of containers", "Manual container lifecycle management"),
        ("Infrastructure as Code", "Define infrastructure in version-controlled configuration files", "Manual cloud console configuration"),
        ("GitOps workflow", "Git repository as single source of truth for infrastructure state", "Direct API calls to change infrastructure"),
        ("Secrets in CI/CD", "Use encrypted environment variables or vault integration", "Store in repository as encrypted files"),
        ("Docker networking", "Containers communicate via virtual networks with DNS resolution", "All containers share host network"),
        ("Log aggregation", "Centralized collection and analysis of logs from all services", "Check logs on each server individually"),
        ("Monitoring and alerting", "Track metrics and trigger alerts when thresholds are breached", "Check dashboards manually"),
        ("Container resource limits", "Set CPU and memory limits to prevent resource exhaustion", "Unlimited resources for best performance"),
        ("Image vulnerability scanning", "Automated detection of known CVEs in container images", "Manual code review only"),
        ("Deployment rollback", "Revert to previous version when new deployment causes issues", "Fix forward only"),
        ("Feature flags", "Toggle features on/off without redeployment", "Deploy features only when complete"),
        ("Kubernetes liveness probe", "Restarts container if probe fails - detects deadlocks", "Checks if container is ready for traffic"),
        ("Kubernetes readiness probe", "Removes pod from service if not ready - handles startup/overload", "Restarts the container"),
        ("Pod autoscaling", "Automatically adjusts replica count based on CPU/memory metrics", "Manually scale before traffic spikes"),
        ("ConfigMap vs Secret", "ConfigMap for non-sensitive config; Secret for sensitive data with encryption", "Both are identical in behavior"),
        ("Service mesh", "Handles service-to-service communication, observability, and security", "Replaces Kubernetes networking"),
    ]
    for topic, correct, wrong in devops_topics:
        q = f"What is {topic}?\n\n# In the context of Python application deployment"
        questions_pool.append(make_q(q, correct, wrong, "Not applicable to Python", "Only for monolithic applications", "A", "devops_deployment"))

    random.shuffle(questions_pool)
    return questions_pool[:n]


# ---- SYSTEM DESIGN GENERATORS ----

def gen_system_design(n):
    """Generate n unique system_design questions."""
    questions_pool = []

    sd_topics = [
        ("event-driven architecture", "Components communicate through events - loose coupling and high scalability", "All components poll a central database"),
        ("CQRS pattern", "Separates read and write models for independent optimization", "Uses single model for all operations"),
        ("saga pattern", "Manages distributed transactions through compensating actions", "Uses two-phase commit across services"),
        ("database sharding", "Horizontally partitions data across multiple database instances", "Vertically splits tables by columns"),
        ("API gateway pattern", "Single entry point that routes, authenticates, and rate-limits API calls", "Direct client-to-service communication"),
    ]
    for topic, correct, wrong in sd_topics:
        q = f"What is {topic} in distributed systems?\n\n# Applied to Python microservices architecture"
        questions_pool.append(make_q(q, correct, wrong, "Only for monolithic applications", "Deprecated pattern", "A", "system_design"))

    random.shuffle(questions_pool)
    return questions_pool[:n]


# ---- MIXED ADVANCED GENERATORS ----

def gen_mixed_advanced(n):
    """Generate n unique mixed_advanced questions."""
    questions_pool = []
    mixed_topics = [
        ("What is the difference between deepcopy and copy?", "deepcopy recursively copies nested objects; copy only copies the top level", "No difference for mutable objects", "deepcopy is slower but identical result", "copy handles nested objects too"),
        ("What does the walrus operator := do?", "Assigns and returns a value in a single expression", "Compares two values", "Creates a constant", "Defines a lambda function"),
        ("What is structural pattern matching in Python 3.10+?", "match/case statements for pattern-based branching similar to switch", "Regular expression matching built into syntax", "Type checking at runtime", "String formatting shorthand"),
    ]
    for q_text, opt_a, opt_b, opt_c, opt_d in mixed_topics:
        questions_pool.append(make_q(q_text, opt_a, opt_b, opt_c, opt_d, "A", "mixed_advanced"))

    random.shuffle(questions_pool)
    return questions_pool[:n]

# ============================================================
# STEP 6: Assemble replacements with correct answer distribution
# ============================================================

# Generate raw questions for each topic (all with answer "A")
topic_generators = {
    "python_advanced": gen_python_advanced,
    "testing_production": gen_testing_production,
    "performance_optimization": gen_performance_optimization,
    "async_patterns": gen_async_patterns,
    "error_handling": gen_error_handling,
    "security_auth": gen_security_auth,
    "devops_deployment": gen_devops_deployment,
    "system_design": gen_system_design,
    "mixed_advanced": gen_mixed_advanced,
}

all_replacements = []
for topic, count in topic_alloc.items():
    if topic in topic_generators:
        generated = topic_generators[topic](count)
        all_replacements.extend(generated)
    else:
        print(f"WARNING: No generator for topic '{topic}', skipping {count}")

print(f"Generated {len(all_replacements)} raw replacement questions")

# Deduplicate generated questions by question_text
seen_gen = set()
unique_replacements = []
for q in all_replacements:
    if q["question_text"] not in seen_gen:
        seen_gen.add(q["question_text"])
        unique_replacements.append(q)
all_replacements = unique_replacements
print(f"After dedup: {len(all_replacements)} unique generated questions")

# Generate additional filler questions if needed
def gen_filler(needed_count, existing_texts):
    """Generate additional unique filler questions."""
    fillers = []
    topics_cycle = ["python_advanced", "testing_production", "performance_optimization",
                    "async_patterns", "error_handling"]
    
    # Python built-in functions and methods
    builtins_qs = [
        ("enumerate()", "Returns iterator of (index, value) pairs", "Returns only indices"),
        ("zip()", "Combines iterables element-wise into tuples", "Concatenates iterables"),
        ("map()", "Applies function to each item in iterable", "Filters items from iterable"),
        ("filter()", "Returns items where function returns True", "Applies function to items"),
        ("any()", "Returns True if any element is truthy", "Returns True if all are truthy"),
        ("all()", "Returns True if all elements are truthy", "Returns True if any is truthy"),
        ("vars()", "Returns __dict__ of an object", "Returns all variables in scope"),
        ("dir()", "Returns list of names in current scope or object attributes", "Returns directory listing"),
        ("getattr()", "Gets attribute by name with optional default", "Sets attribute value"),
        ("setattr()", "Sets attribute value by name", "Gets attribute value"),
        ("hasattr()", "Returns True if object has named attribute", "Creates attribute if missing"),
        ("isinstance()", "Checks if object is instance of a class or tuple of classes", "Converts object to type"),
        ("issubclass()", "Checks if class is subclass of another", "Creates subclass dynamically"),
        ("super()", "Returns proxy to parent class for method delegation", "Creates superclass"),
        ("property()", "Creates managed attribute with getter/setter/deleter", "Makes attribute read-only"),
        ("classmethod()", "Binds method to class instead of instance", "Makes method static"),
        ("staticmethod()", "Method with no access to class or instance", "Binds method to class"),
        ("repr()", "Returns developer-readable string representation", "Returns user-readable string"),
        ("hash()", "Returns integer hash for use in dicts and sets", "Returns memory address"),
        ("id()", "Returns unique integer identifier (memory address in CPython)", "Returns hash value"),
        ("type()", "Returns type of object or creates new class dynamically", "Converts object type"),
        ("callable()", "Returns True if object can be called as function", "Calls the object"),
        ("sorted()", "Returns new sorted list from iterable", "Sorts iterable in place"),
        ("reversed()", "Returns reverse iterator", "Reverses list in place"),
        ("abs()", "Returns absolute value of a number", "Returns the sign of a number"),
        ("round()", "Rounds number to given precision using banker's rounding", "Always rounds up"),
        ("divmod()", "Returns tuple of (quotient, remainder)", "Returns only quotient"),
        ("pow()", "Returns base raised to power, optionally mod", "Returns power of 2"),
        ("min()", "Returns smallest item or smallest of arguments", "Returns first item"),
        ("max()", "Returns largest item or largest of arguments", "Returns last item"),
        ("sum()", "Returns sum of iterable with optional start value", "Returns count of items"),
        ("len()", "Returns number of items in container", "Returns memory size in bytes"),
        ("range()", "Returns immutable sequence of integers", "Returns list of integers"),
        ("slice()", "Creates slice object for extended indexing", "Cuts string at position"),
        ("format()", "Formats value according to format spec", "Converts value to string"),
        ("chr()", "Returns character for Unicode code point", "Returns ASCII code of character"),
        ("ord()", "Returns Unicode code point for character", "Returns position in alphabet"),
        ("bin()", "Returns binary string representation of integer", "Converts binary to int"),
        ("hex()", "Returns hexadecimal string representation", "Converts hex string to int"),
        ("oct()", "Returns octal string representation", "Converts octal string to int"),
        ("bool()", "Converts value to Boolean using truthiness rules", "Returns True always"),
        ("int()", "Converts to integer, optionally from given base", "Rounds float to integer"),
        ("float()", "Converts string or number to floating point", "Returns infinity"),
        ("complex()", "Creates complex number from real and imaginary parts", "Returns absolute value"),
        ("str()", "Converts object to string using __str__", "Returns raw bytes"),
        ("bytes()", "Creates immutable byte sequence", "Creates mutable string"),
        ("bytearray()", "Creates mutable byte sequence", "Creates immutable bytes"),
        ("list()", "Creates list from iterable", "Creates tuple from iterable"),
        ("tuple()", "Creates immutable tuple from iterable", "Creates mutable list"),
        ("set()", "Creates mutable set of unique elements", "Creates ordered collection"),
        ("frozenset()", "Creates immutable set (hashable)", "Creates faster mutable set"),
        ("dict()", "Creates dictionary from keyword args or iterable of pairs", "Creates ordered list"),
        ("memoryview()", "Creates memory view of bytes-like object without copying", "Copies memory region"),
        ("iter()", "Returns iterator from iterable or callable with sentinel", "Returns list of items"),
        ("next()", "Retrieves next item from iterator with optional default", "Advances by 2 items"),
        ("input()", "Reads line from stdin with optional prompt", "Reads binary from stdin"),
        ("print()", "Outputs to stream with sep, end, file, flush options", "Returns formatted string"),
        ("open()", "Opens file returning file object with specified mode and encoding", "Creates new file always"),
        ("compile()", "Compiles source into code object for exec or eval", "Compresses source code"),
        ("exec()", "Executes dynamically compiled code in given scope", "Evaluates expression"),
        ("eval()", "Evaluates single expression and returns result", "Executes statements"),
        ("globals()", "Returns dictionary of current global symbol table", "Returns all Python globals"),
        ("locals()", "Returns dictionary of current local scope", "Returns module variables only"),
        ("breakpoint()", "Drops into debugger at call site", "Exits the program"),
        ("object()", "Creates featureless base object instance", "Creates dict-like object"),
    ]
    
    # String methods
    string_methods = [
        ("str.split()", "Splits string by separator into list of substrings", "Joins list into string"),
        ("str.join()", "Joins iterable of strings with separator", "Splits string into parts"),
        ("str.strip()", "Removes leading and trailing whitespace", "Removes all spaces"),
        ("str.replace()", "Returns string with all occurrences replaced", "Modifies string in place"),
        ("str.find()", "Returns lowest index of substring or -1 if not found", "Raises ValueError if not found"),
        ("str.index()", "Returns lowest index of substring or raises ValueError", "Returns -1 if not found"),
        ("str.startswith()", "Returns True if string starts with prefix", "Modifies string start"),
        ("str.endswith()", "Returns True if string ends with suffix", "Modifies string end"),
        ("str.upper()", "Returns uppercased copy of string", "Modifies string in place"),
        ("str.lower()", "Returns lowercased copy of string", "Modifies string in place"),
        ("str.title()", "Returns titlecased copy (each word capitalized)", "Capitalizes first char only"),
        ("str.capitalize()", "Returns string with first character capitalized", "Uppercases all chars"),
        ("str.count()", "Returns number of non-overlapping occurrences", "Returns True if found"),
        ("str.format()", "Performs string formatting with positional/keyword args", "Returns format spec"),
        ("str.encode()", "Returns bytes encoded with specified encoding", "Decodes bytes to string"),
        ("str.isdigit()", "Returns True if all characters are digits", "Converts string to int"),
        ("str.isalpha()", "Returns True if all characters are alphabetic", "Removes non-alpha chars"),
        ("str.isalnum()", "Returns True if all characters are alphanumeric", "Removes special chars"),
        ("str.partition()", "Splits at first occurrence into (before, sep, after) tuple", "Splits into list"),
        ("str.zfill()", "Pads string with zeros on the left to specified width", "Fills with spaces"),
    ]
    
    # Dict methods
    dict_methods = [
        ("dict.get(key, default)", "Returns value for key or default if missing (no KeyError)", "Raises KeyError if missing"),
        ("dict.setdefault(key, val)", "Returns value if key exists, else inserts val and returns it", "Always overwrites existing"),
        ("dict.update(other)", "Updates dict with key-value pairs from other mapping", "Returns new merged dict"),
        ("dict.pop(key)", "Removes key and returns value, or raises KeyError", "Returns True if key existed"),
        ("dict.popitem()", "Removes and returns last inserted key-value pair (LIFO)", "Removes random pair"),
        ("dict.keys()", "Returns dynamic view of dictionary keys", "Returns static list of keys"),
        ("dict.values()", "Returns dynamic view of dictionary values", "Returns static list of values"),
        ("dict.items()", "Returns dynamic view of (key, value) pairs", "Returns list of keys"),
        ("dict | other (Python 3.9+)", "Creates new merged dict (other takes precedence)", "Modifies dict in place"),
        ("dict |= other (Python 3.9+)", "Updates dict in place with other (other takes precedence)", "Creates new merged dict"),
    ]
    
    # List methods
    list_methods = [
        ("list.append(x)", "Adds single item to end of list", "Extends list with iterable"),
        ("list.extend(iter)", "Extends list with all items from iterable", "Appends iterable as single item"),
        ("list.insert(i, x)", "Inserts item at given position", "Replaces item at position"),
        ("list.remove(x)", "Removes first occurrence of value or raises ValueError", "Removes by index"),
        ("list.pop(i)", "Removes and returns item at index (default last)", "Returns without removing"),
        ("list.sort()", "Sorts list in place and returns None", "Returns new sorted list"),
        ("list.reverse()", "Reverses list in place and returns None", "Returns new reversed list"),
        ("list.copy()", "Returns shallow copy of the list", "Returns deep copy"),
        ("list.clear()", "Removes all items from list", "Deletes the list variable"),
        ("list.count(x)", "Returns number of occurrences of value", "Returns True if found"),
        ("list.index(x)", "Returns index of first occurrence or raises ValueError", "Returns -1 if not found"),
    ]
    
    idx = 0
    all_method_qs = builtins_qs + string_methods + dict_methods + list_methods
    random.shuffle(all_method_qs)
    
    for func, correct, wrong in all_method_qs:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What does {func} do in Python?\n\n# Standard library / built-in behavior"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not a valid Python function", "Raises NotImplementedError", "A", topic))
            existing_texts.add(q_text)
    
    # Module-level questions
    modules = [
        ("os.path.join()", "Joins path components with OS-appropriate separator", "Concatenates strings with /"),
        ("os.path.exists()", "Returns True if path exists in filesystem", "Creates path if missing"),
        ("os.path.dirname()", "Returns directory component of path", "Returns filename only"),
        ("os.path.basename()", "Returns final component of path", "Returns directory part"),
        ("os.path.splitext()", "Splits path into (root, extension) tuple", "Splits by / separator"),
        ("os.makedirs()", "Creates directory and all intermediate parents", "Creates single directory only"),
        ("os.listdir()", "Returns list of entries in directory", "Returns recursive file tree"),
        ("os.environ", "Mapping of environment variables", "System configuration dict"),
        ("os.getcwd()", "Returns current working directory path", "Returns home directory"),
        ("os.path.abspath()", "Returns absolute version of path", "Returns relative path"),
        ("pathlib.Path.glob()", "Returns iterator of paths matching pattern", "Returns single path"),
        ("pathlib.Path.mkdir()", "Creates directory with optional parents and exist_ok", "Creates file"),
        ("pathlib.Path.read_text()", "Reads entire file content as string", "Reads first line only"),
        ("pathlib.Path.write_text()", "Writes string to file (creates/overwrites)", "Appends to file"),
        ("pathlib.Path.stem", "Returns filename without extension", "Returns full filename"),
        ("pathlib.Path.suffix", "Returns file extension including dot", "Returns filename without dot"),
        ("pathlib.Path.parent", "Returns parent directory as Path", "Returns string of parent"),
        ("pathlib.Path.resolve()", "Returns absolute path resolving symlinks", "Checks if path exists"),
        ("pathlib.Path.iterdir()", "Yields path objects of directory contents", "Yields file contents"),
        ("pathlib.Path.is_file()", "Returns True if path points to regular file", "Returns True for directories too"),
        ("json.dumps()", "Serializes object to JSON string", "Writes JSON to file"),
        ("json.loads()", "Deserializes JSON string to Python object", "Reads JSON from file"),
        ("json.dump()", "Writes JSON to file-like object", "Returns JSON string"),
        ("json.load()", "Reads JSON from file-like object", "Parses JSON string"),
        ("re.match()", "Matches pattern at start of string only", "Searches entire string"),
        ("re.search()", "Searches entire string for first match", "Matches at start only"),
        ("re.findall()", "Returns list of all non-overlapping matches", "Returns first match only"),
        ("re.sub()", "Replaces pattern matches with replacement string", "Returns match object"),
        ("re.compile()", "Pre-compiles pattern for reuse (faster repeated matching)", "Executes pattern immediately"),
        ("re.split()", "Splits string by pattern occurrences", "Joins strings with pattern"),
        ("collections.defaultdict", "Dict subclass that calls factory for missing keys", "Dict that ignores missing keys"),
        ("collections.OrderedDict", "Dict that remembers insertion order (useful pre-3.7)", "Dict sorted by keys"),
        ("collections.namedtuple", "Creates tuple subclass with named fields", "Creates mutable named container"),
        ("collections.deque", "Double-ended queue with O(1) append/pop on both ends", "Fixed-size array"),
        ("collections.Counter", "Dict subclass for counting hashable objects", "Counts function calls"),
        ("collections.ChainMap", "Groups multiple dicts into single view", "Merges dicts permanently"),
        ("itertools.count()", "Creates infinite counter from start with step", "Counts items in iterable"),
        ("itertools.cycle()", "Repeats iterable elements infinitely", "Cycles through once"),
        ("itertools.repeat()", "Repeats single value specified number of times", "Repeats function call"),
        ("itertools.chain()", "Chains multiple iterables into one sequential iterator", "Runs iterables in parallel"),
        ("itertools.product()", "Cartesian product of input iterables", "Element-wise product"),
        ("itertools.tee()", "Creates n independent iterators from one", "Splits iterable in half"),
        ("datetime.now()", "Returns current local date and time", "Returns UTC time"),
        ("datetime.utcnow()", "Returns current UTC date and time (naive)", "Returns local time"),
        ("datetime.strftime()", "Formats datetime as string with format codes", "Parses string to datetime"),
        ("datetime.strptime()", "Parses string to datetime using format codes", "Formats datetime as string"),
        ("datetime.timedelta()", "Represents duration between two datetimes", "Represents a specific point in time"),
        ("logging.getLogger()", "Returns logger instance with hierarchical name", "Creates log file"),
        ("logging.basicConfig()", "Configures root logger with format, level, handlers", "Creates custom logger"),
        ("logging.debug()", "Logs message at DEBUG level (lowest severity)", "Prints to console"),
        ("logging.warning()", "Logs message at WARNING level", "Raises Warning exception"),
        ("logging.exception()", "Logs ERROR with exception traceback info", "Raises the exception"),
        ("threading.Lock()", "Mutual exclusion lock for thread synchronization", "Creates new thread"),
        ("threading.Thread()", "Creates new thread of execution", "Returns current thread"),
        ("threading.Event()", "Thread synchronization primitive for signaling", "Logs thread events"),
        ("subprocess.run()", "Runs command and waits for completion, returns CompletedProcess", "Starts background process"),
        ("subprocess.Popen()", "Creates subprocess with full control over I/O streams", "Same as run() but faster"),
        ("tempfile.NamedTemporaryFile()", "Creates named temp file that auto-deletes on close", "Creates permanent file"),
        ("tempfile.mkdtemp()", "Creates temporary directory and returns its path", "Creates temp file in /tmp"),
        ("shutil.copy()", "Copies file content and permissions", "Moves file to new location"),
        ("shutil.copytree()", "Recursively copies directory tree", "Copies single file"),
        ("shutil.rmtree()", "Recursively deletes directory tree", "Removes single file"),
        ("pickle.dumps()", "Serializes Python object to bytes", "Writes pickle to file"),
        ("pickle.loads()", "Deserializes bytes to Python object", "Reads pickle from file"),
        ("hashlib.sha256()", "Creates SHA-256 hash object for secure hashing", "Encrypts data with SHA-256"),
        ("base64.b64encode()", "Encodes bytes to base64 ASCII bytes", "Encrypts data with base64"),
        ("urllib.parse.urljoin()", "Joins base URL with relative URL", "Concatenates URL strings"),
        ("urllib.parse.urlparse()", "Parses URL into 6 components", "Validates URL format"),
        ("socket.socket()", "Creates network socket for communication", "Opens HTTP connection"),
        ("struct.pack()", "Packs values into bytes according to format string", "Creates C struct"),
        ("struct.unpack()", "Unpacks bytes into tuple according to format string", "Parses text format"),
    ]
    
    random.shuffle(modules)
    for func, correct, wrong in modules:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What does {func} do?\n\n# Python standard library"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not available in Python 3", "Deprecated function", "A", topic))
            existing_texts.add(q_text)
    
    # Dunder method questions
    dunders = [
        ("__repr__", "Returns official string representation for debugging", "Returns user-friendly string"),
        ("__str__", "Returns informal string representation for display", "Returns debug representation"),
        ("__len__", "Returns length when len() is called on object", "Returns size in bytes"),
        ("__getitem__", "Enables indexing with obj[key] syntax", "Gets attribute by name"),
        ("__setitem__", "Enables assignment with obj[key] = value syntax", "Sets attribute by name"),
        ("__delitem__", "Enables deletion with del obj[key] syntax", "Deletes attribute"),
        ("__contains__", "Enables 'in' operator for membership testing", "Returns all contents"),
        ("__iter__", "Returns iterator object for iteration protocol", "Returns list of items"),
        ("__next__", "Returns next item from iterator or raises StopIteration", "Returns remaining items"),
        ("__call__", "Makes instance callable like a function", "Called on object creation"),
        ("__enter__", "Sets up context manager and returns context value", "Enters a loop"),
        ("__exit__", "Tears down context manager, optionally suppresses exceptions", "Exits the program"),
        ("__hash__", "Returns integer hash for use in sets and dict keys", "Returns unique ID"),
        ("__eq__", "Defines equality comparison with == operator", "Defines identity comparison"),
        ("__lt__", "Defines less-than comparison with < operator", "Defines subtraction"),
        ("__add__", "Defines addition with + operator", "Appends to list"),
        ("__mul__", "Defines multiplication with * operator", "Repeats string"),
        ("__bool__", "Defines truthiness when bool() is called or in conditions", "Converts to integer"),
        ("__del__", "Called when object is about to be garbage collected (destructor)", "Deletes object immediately"),
        ("__slots__", "Restricts instance attributes to declared names, saves memory", "Defines class methods"),
        ("__init_subclass__", "Called when class is subclassed, allows customization", "Initializes instance"),
        ("__class_getitem__", "Enables class subscripting like MyClass[int]", "Gets class attribute"),
        ("__missing__", "Called by dict subclass when key is not found", "Raises KeyError"),
        ("__format__", "Defines custom formatting with format() and f-strings", "Returns formatted string"),
        ("__bytes__", "Returns bytes representation when bytes() is called", "Encodes to UTF-8"),
        ("__abs__", "Defines absolute value when abs() is called", "Returns positive version"),
        ("__neg__", "Defines negation with unary - operator", "Subtracts from zero"),
        ("__pos__", "Defines unary + operator behavior", "Makes value positive"),
        ("__invert__", "Defines bitwise NOT with ~ operator", "Reverses object"),
        ("__index__", "Returns integer for use in slicing and bin/hex/oct", "Returns array index"),
        ("__matmul__", "Defines matrix multiplication with @ operator", "Sends email"),
    ]
    
    random.shuffle(dunders)
    for method, correct, wrong in dunders:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What does the {method} dunder method do in Python?\n\nclass MyClass:\n    def {method}(self, *args):\n        ..."
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not a valid dunder method", "Only works in Python 2", "A", topic))
            existing_texts.add(q_text)
    
    # Design patterns
    patterns = [
        ("Observer pattern", "Objects subscribe to events and get notified of state changes", "Objects observe each other's memory"),
        ("Strategy pattern", "Defines family of algorithms and makes them interchangeable at runtime", "Defines winning strategy for games"),
        ("Factory pattern", "Creates objects without specifying exact class to instantiate", "Manufactures hardware components"),
        ("Decorator pattern", "Adds behavior to objects dynamically without modifying their class", "Only refers to Python @ syntax"),
        ("Adapter pattern", "Converts interface of one class to interface expected by client", "Connects to external APIs"),
        ("Facade pattern", "Provides simplified interface to complex subsystem", "Hides implementation bugs"),
        ("Proxy pattern", "Controls access to another object through a surrogate", "Creates duplicate objects"),
        ("Command pattern", "Encapsulates request as object for parameterization and queuing", "Executes shell commands"),
        ("Template Method pattern", "Defines algorithm skeleton in base class, steps in subclasses", "Generates code from templates"),
        ("Iterator pattern", "Provides sequential access to aggregate elements without exposing internals", "Counts loop iterations"),
        ("State pattern", "Object alters behavior when internal state changes", "Manages global state"),
        ("Builder pattern", "Constructs complex objects step by step with fluent interface", "Compiles source code"),
        ("Composite pattern", "Treats individual objects and compositions uniformly as tree structure", "Combines multiple inheritance"),
        ("Chain of Responsibility", "Passes request along chain of handlers until one handles it", "Chains function calls"),
        ("Mediator pattern", "Defines object that encapsulates how objects interact", "Resolves merge conflicts"),
        ("Flyweight pattern", "Shares common state between multiple objects to save memory", "Makes objects lighter"),
        ("Bridge pattern", "Separates abstraction from implementation so both can vary independently", "Connects two networks"),
        ("Visitor pattern", "Separates algorithm from object structure it operates on", "Tracks website visitors"),
        ("Memento pattern", "Captures object state for later restoration without violating encapsulation", "Memorizes function results"),
        ("Prototype pattern", "Creates new objects by cloning existing prototype instances", "Defines class prototypes"),
    ]
    random.shuffle(patterns)
    for name, correct, wrong in patterns:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is the {name} in software design?\n\n# Applied to Python implementation"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not applicable to Python", "Only used in compiled languages", "A", topic))
            existing_texts.add(q_text)
    
    # Python concepts
    concepts = [
        ("GIL (Global Interpreter Lock)", "Mutex that allows only one thread to execute Python bytecode at a time", "Lock that prevents global variable access"),
        ("generator expression vs list comprehension", "Generator is lazy (O(1) memory), list comprehension creates full list in memory", "No practical difference between them"),
        ("duck typing", "If it walks like a duck and quacks like a duck, treat it as a duck - type by behavior", "Using the typing.Duck class"),
        ("EAFP vs LBYL", "Easier to Ask Forgiveness (try/except) vs Look Before You Leap (if checks)", "Error And Failure Prevention vs Load Before You Look"),
        ("name mangling", "Double underscore prefix __attr becomes _ClassName__attr to avoid conflicts", "Makes attributes truly private and inaccessible"),
        ("monkey patching", "Dynamically modifying classes or modules at runtime", "Using patch() in unittest.mock only"),
        ("descriptor protocol", "Objects implementing __get__, __set__, __delete__ to customize attribute access", "XML descriptor files for configuration"),
        ("cooperative multiple inheritance", "Using super() to ensure all classes in MRO get called in order", "Inheriting from exactly two classes"),
        ("context manager protocol", "Implementing __enter__ and __exit__ for resource management with 'with' statement", "Managing program execution context only"),
        ("iterable vs iterator", "Iterable has __iter__ (creates iterator); iterator has __next__ (produces values)", "They are the same thing"),
        ("closure", "Inner function capturing variables from enclosing scope that persist after outer returns", "Any nested function definition"),
        ("decorator with arguments", "Requires extra layer of nesting - decorator factory returns the actual decorator", "Same as decorator without arguments"),
        ("metaclass", "Class of a class - customizes class creation process itself", "Abstract base class"),
        ("mixin class", "Class providing methods to other classes via multiple inheritance without being standalone", "Class that mixes Python versions"),
        ("abstract base class", "Cannot be instantiated; defines interface that subclasses must implement", "First class defined in a module"),
        ("slots vs dict", "__slots__ uses tuple of names for fixed memory layout; __dict__ uses dynamic dict", "Both use the same memory"),
        ("weak reference", "Reference that does not prevent garbage collection of the referent", "Reference that points to None"),
        ("coroutine vs generator", "Coroutine uses async/await for I/O; generator uses yield for lazy iteration", "They are exactly the same"),
        ("data descriptor vs non-data descriptor", "Data descriptor defines __set__ or __delete__; takes priority over instance __dict__", "Non-data descriptors cannot be overridden"),
        ("PEP 8 naming conventions", "snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants", "camelCase for everything"),
        ("comprehension scope", "Comprehension variables are scoped to the comprehension (Python 3)", "Variables leak into enclosing scope"),
        ("walrus operator :=", "Assignment expression that assigns and returns value in single expression", "Comparison operator like =="),
        ("structural pattern matching", "match/case for pattern-based branching with destructuring (Python 3.10+)", "Regular expression matching syntax"),
        ("positional-only parameters", "Parameters before / in signature cannot be passed as keyword arguments", "Parameters that must be integers"),
        ("keyword-only parameters", "Parameters after * in signature must be passed as keyword arguments", "Parameters that must be strings"),
        ("f-string debugging (=)", "f'{expr=}' shows both expression text and value for debugging", "Enables debug mode for f-strings"),
        ("exception groups", "Python 3.11+ ExceptionGroup bundles multiple exceptions from concurrent tasks", "Group of related exception classes"),
        ("type narrowing", "Using isinstance/assert to tell type checker about more specific type", "Converting between types"),
        ("Protocol class", "Structural subtyping - class is compatible if it has required methods (duck typing for types)", "Network protocol implementation"),
        ("ParamSpec", "Captures parameter types of a callable for accurate decorator typing", "Specifies parameter defaults"),
        ("TypeGuard", "Return type annotation that narrows type in conditional branches", "Runtime type validation"),
    ]
    random.shuffle(concepts)
    for concept, correct, wrong in concepts:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is {concept} in Python?\n\n# Advanced Python concept"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not a real Python concept", "Removed in Python 3", "A", topic))
            existing_texts.add(q_text)
    
    # Best practices
    practices = [
        ("Use context managers for resource cleanup", "Guarantees cleanup via __exit__ even if exceptions occur", "Only for file operations"),
        ("Prefer composition over inheritance", "Creates flexible designs by combining behaviors via contained objects", "Never use inheritance"),
        ("Use dataclasses for simple data containers", "Auto-generates __init__, __repr__, __eq__ reducing boilerplate", "Only for database models"),
        ("Type hints for function signatures", "Documents expected types and enables static analysis without runtime cost", "Enforces types at runtime"),
        ("Use logging instead of print", "Configurable levels, handlers, and formatting for production diagnostics", "print() is removed in production"),
        ("Virtual environments for isolation", "Isolates project dependencies preventing version conflicts between projects", "Makes Python run faster"),
        ("Use pathlib over os.path", "Object-oriented path handling with cleaner API and operator overloading", "pathlib is faster than os.path"),
        ("Avoid mutable default arguments", "Mutable defaults are shared across calls - use None and create inside function", "Python prevents mutable defaults"),
        ("Use enumerate instead of range(len())", "Provides both index and value cleanly without manual counter", "enumerate is faster than range"),
        ("Use collections.defaultdict for grouping", "Eliminates key existence checks by auto-creating default values", "defaultdict is always faster than dict"),
        ("Generator functions for large sequences", "Yields items one at a time - constant memory regardless of sequence size", "Generators are always faster"),
        ("Use pytest fixtures over setUp/tearDown", "More flexible scope, parametrization, and dependency injection", "setUp/tearDown is deprecated"),
        ("Apply single responsibility principle", "Each class/function should have one reason to change", "Each file has one class"),
        ("Use ABC for interface definitions", "Enforces method implementation in subclasses at instantiation time", "ABC makes classes abstract only"),
        ("Prefer specific exceptions over bare except", "Catches only expected errors, letting unexpected ones propagate for debugging", "bare except is faster"),
        ("Use __all__ to control public API", "Defines what is exported with 'from module import *' and documents public interface", "Prevents all imports"),
        ("Implement __hash__ with __eq__", "Objects that compare equal must have same hash for correct dict/set behavior", "__hash__ is optional"),
        ("Use functools.wraps in decorators", "Preserves original function metadata (name, docstring, signature)", "Makes decorator faster"),
        ("Avoid circular imports", "Restructure code or use local imports to break dependency cycles", "Circular imports always crash"),
        ("Use typing.Protocol for structural subtyping", "Enables duck-typed interfaces checkable by mypy without inheritance", "Protocol replaces ABC"),
    ]
    random.shuffle(practices)
    for practice, correct, wrong in practices:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"Why should you: {practice}?\n\n# Python best practices"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "This is not a recommended practice", "Only applies to Python 2", "A", topic))
            existing_texts.add(q_text)
    
    # Error types and when they occur
    error_types = [
        ("TypeError", "Operation applied to object of inappropriate type", "Any type-related issue"),
        ("ValueError", "Operation receives argument of right type but inappropriate value", "Value is None"),
        ("AttributeError", "Accessing attribute that does not exist on object", "Setting attribute fails"),
        ("KeyError", "Dictionary key not found", "Key is wrong type"),
        ("IndexError", "Sequence index out of range", "Index is negative"),
        ("NameError", "Local or global name not found", "Name is misspelled"),
        ("ImportError", "Module or name cannot be imported", "Module has syntax errors"),
        ("FileNotFoundError", "File or directory path does not exist", "File is corrupted"),
        ("PermissionError", "Operation lacks required filesystem permissions", "User is not admin"),
        ("OSError", "System-related operation fails (I/O, networking)", "Operating system crash"),
        ("RuntimeError", "Error that does not fit other categories", "Code runs too slowly"),
        ("StopIteration", "Iterator exhausted - no more items available", "Iteration was cancelled"),
        ("RecursionError", "Maximum recursion depth exceeded", "Any recursive function call"),
        ("MemoryError", "Operation ran out of available memory", "Variable is too large"),
        ("NotImplementedError", "Abstract method not overridden in subclass", "Feature not yet coded"),
        ("ZeroDivisionError", "Division or modulo by zero", "Result is zero"),
        ("OverflowError", "Arithmetic result too large for representation", "Integer is too big"),
        ("UnicodeDecodeError", "Cannot decode bytes to string with specified encoding", "String contains emoji"),
        ("ConnectionError", "Network connection related failure", "Internet is unavailable"),
        ("TimeoutError", "Operation exceeded allowed time limit", "Server is overloaded"),
    ]
    random.shuffle(error_types)
    for error, correct, wrong in error_types:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"When does Python raise {error}?\n\n# Exception handling context"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "This exception does not exist", "Only raised by C extensions", "A", topic))
            existing_texts.add(q_text)
    
    # Testing concepts
    testing_concepts = [
        ("test isolation", "Each test is independent and does not affect or depend on other tests", "Tests must run in order"),
        ("test coverage", "Percentage of code lines/branches exercised by the test suite", "Number of tests written"),
        ("regression testing", "Re-running tests to ensure changes did not break existing functionality", "Testing old Python versions"),
        ("mutation testing", "Introduces small code changes to verify tests catch them", "Testing code mutations/genetics"),
        ("fuzz testing", "Feeds random/malformed input to find crashes and edge cases", "Testing with fuzzy matching"),
        ("smoke testing", "Quick subset of tests verifying basic functionality works", "Testing with fire/heat"),
        ("load testing", "Simulates expected concurrent users to verify performance under load", "Testing heavy file operations"),
        ("stress testing", "Pushes system beyond normal capacity to find breaking point", "Testing under deadline pressure"),
        ("contract testing", "Verifies API interactions between services match agreed contract", "Legal contract verification"),
        ("snapshot testing", "Compares output against previously stored expected output", "Taking screenshots of UI"),
        ("parameterized testing", "Runs same test logic with multiple input/output combinations", "Tests with configurable parameters"),
        ("test fixture", "Setup/teardown code that provides known state for tests", "Physical test equipment"),
        ("test double", "Generic term for objects that stand in for real dependencies in tests", "Duplicate test file"),
        ("test pyramid", "Many unit tests, fewer integration tests, fewest E2E tests", "Testing in order of importance"),
        ("TDD (Test-Driven Development)", "Write test first, then implement code to make it pass, then refactor", "Testing during deployment"),
        ("BDD (Behavior-Driven Development)", "Specifications written in natural language (Given-When-Then) drive tests", "Bug-Driven Development"),
        ("mocking vs stubbing", "Mocks verify interactions occurred; stubs provide canned responses", "They are the same thing"),
        ("test flakiness", "Tests that pass and fail intermittently without code changes (timing, state)", "Tests with incorrect assertions"),
        ("assertion introspection", "pytest rewrites assertions to show detailed failure info on failed tests", "Manual assertion message writing"),
        ("test markers", "Metadata labels on tests for selection, skipping, or parameterization", "Physical markers on test files"),
    ]
    random.shuffle(testing_concepts)
    for concept, correct, wrong in testing_concepts:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is {concept} in software testing?\n\n# Testing methodology"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not a real testing concept", "Only for compiled languages", "A", topic))
            existing_texts.add(q_text)
    
    # Async concepts
    async_concepts = [
        ("event loop", "Single-threaded loop that schedules and runs async tasks cooperatively", "Multi-threaded task scheduler"),
        ("coroutine", "Function defined with async def that can be suspended and resumed at await points", "Any function that uses yield"),
        ("awaitable", "Object that can be used with await - coroutines, Tasks, and Futures", "Any Python object"),
        ("Task", "Wraps coroutine in Future-like object that runs in event loop", "Background thread"),
        ("Future", "Placeholder for result that will be available later", "Function return value"),
        ("callback", "Function scheduled to run when event occurs", "Any function parameter"),
        ("backpressure", "Mechanism to slow producer when consumer cannot keep up", "Network congestion"),
        ("cooperative multitasking", "Tasks voluntarily yield control at await points", "OS preempts tasks"),
        ("structured concurrency", "Tasks are organized in hierarchy with clear lifetimes and error propagation", "Unstructured threading"),
        ("cancellation token", "Mechanism to signal async operations to stop gracefully", "Token for API authentication"),
    ]
    random.shuffle(async_concepts)
    for concept, correct, wrong in async_concepts:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is an {concept} in async Python programming?\n\n# asyncio concepts"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not used in Python", "Only in JavaScript", "A", topic))
            existing_texts.add(q_text)
    
    # Performance concepts
    perf_concepts = [
        ("amortized O(1)", "Average time per operation is O(1) even if occasional operations are O(n)", "Always exactly O(1)"),
        ("cache locality", "Accessing memory locations close together is faster due to CPU cache lines", "Caching data in Redis"),
        ("branch prediction", "CPU predicts conditional branch outcome - misprediction causes pipeline stall", "if/else optimization"),
        ("vectorization", "Performing operation on multiple data elements simultaneously using SIMD", "Using Python lists"),
        ("lazy evaluation", "Delaying computation until result is actually needed", "Using less CPU"),
        ("memoization", "Storing function results to avoid redundant computation for same inputs", "Memorizing algorithms"),
        ("tail call optimization", "Reusing stack frame for recursive call in tail position (not in CPython)", "Any recursive optimization"),
        ("short-circuit evaluation", "Stopping evaluation of logical expression as soon as result is determined", "Electrical short circuit"),
        ("string interning", "Reusing immutable string objects to save memory and enable O(1) comparison", "Converting strings to integers"),
        ("copy-on-write", "Sharing memory until modification occurs, then creating a copy", "Always copying data"),
    ]
    random.shuffle(perf_concepts)
    for concept, correct, wrong in perf_concepts:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is {concept} in the context of Python performance?\n\n# Performance optimization"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, correct, wrong, "Not relevant to Python", "Only matters for C/C++", "A", topic))
            existing_texts.add(q_text)
    
    # Additional code output questions using various constructs
    code_output_qs = [
        ("x = [1, 2, 3]\ny = x[:]\ny.append(4)\nprint(len(x))", "3", "4", "TypeError", "None"),
        ("d = {'a': 1, 'b': 2}\nprint(list(d.keys()))", "['a', 'b']", "['b', 'a']", "dict_keys(['a', 'b'])", "TypeError"),
        ("s = {1, 2, 3, 2, 1}\nprint(len(s))", "3", "5", "2", "TypeError"),
        ("t = (1, [2, 3])\nt[1].append(4)\nprint(t)", "(1, [2, 3, 4])", "TypeError", "(1, [2, 3])", "None"),
        ("x = 'hello'\nprint(x[1:4])", "ell", "hel", "ello", "IndexError"),
        ("a = [1, 2, 3]\nb = a\nb.append(4)\nprint(a)", "[1, 2, 3, 4]", "[1, 2, 3]", "TypeError", "None"),
        ("x = {'a': 1}\ny = {'b': 2}\nz = {**x, **y}\nprint(z)", "{'a': 1, 'b': 2}", "{'a': 1}", "{'b': 2}", "TypeError"),
        ("nums = [1, 2, 3, 4, 5]\nresult = nums[::2]\nprint(result)", "[1, 3, 5]", "[2, 4]", "[1, 2, 3]", "TypeError"),
        ("x = [i**2 for i in range(5)]\nprint(x[3])", "9", "16", "4", "IndexError"),
        ("d = dict.fromkeys(['a', 'b', 'c'], 0)\nprint(d)", "{'a': 0, 'b': 0, 'c': 0}", "{'a': None, 'b': None, 'c': None}", "{}", "TypeError"),
        ("x = 'Python'\nprint(x[-2:])", "on", "Py", "hon", "IndexError"),
        ("a, *b, c = [1, 2, 3, 4, 5]\nprint(b)", "[2, 3, 4]", "[1, 2, 3, 4]", "[2, 3, 4, 5]", "SyntaxError"),
        ("x = [None] * 3\nprint(x)", "[None, None, None]", "[]", "[None]", "TypeError"),
        ("s = 'hello world'\nprint(s.title())", "Hello World", "HELLO WORLD", "hello world", "Hello world"),
        ("x = [1, 2, 3]\nx.insert(1, 'a')\nprint(x)", "[1, 'a', 2, 3]", "['a', 1, 2, 3]", "[1, 2, 'a', 3]", "TypeError"),
        ("print(bool(''), bool(' '), bool('0'))", "False True True", "False False False", "False True False", "True True True"),
        ("x = [1, 2, 3]\ny = x.copy()\ny[0] = 99\nprint(x[0])", "1", "99", "None", "TypeError"),
        ("d = {'x': 1}\nresult = d.pop('y', 'default')\nprint(result)", "default", "KeyError", "None", "1"),
        ("x = (1, 2) + (3, 4)\nprint(x)", "(1, 2, 3, 4)", "(4, 6)", "TypeError", "((1,2),(3,4))"),
        ("s = set([1, 2, 3])\ns.discard(5)\nprint(len(s))", "3", "KeyError", "2", "None"),
        ("x = 'abcdef'\nprint(x[::-1])", "fedcba", "abcdef", "f", "TypeError"),
        ("a = [1, 2, 3]\nb = [4, 5, 6]\nprint(list(zip(a, b)))", "[(1, 4), (2, 5), (3, 6)]", "[(1, 2, 3, 4, 5, 6)]", "[1, 4, 2, 5, 3, 6]", "TypeError"),
        ("x = {'a': 1, 'b': 2, 'c': 3}\nprint(list(x.values()))", "[1, 2, 3]", "['a', 'b', 'c']", "[('a',1),('b',2),('c',3)]", "TypeError"),
        ("print(type(lambda: None).__name__)", "function", "lambda", "NoneType", "method"),
        ("x = [1, 2, 3, 4]\nprint(x.pop(1))", "2", "1", "4", "IndexError"),
        ("s = frozenset([1, 2, 3])\ntry:\n    s.add(4)\nexcept AttributeError:\n    print('immutable')", "immutable", "frozenset({1,2,3,4})", "TypeError", "None"),
        ("x = 10\ny = x\nx = 20\nprint(y)", "10", "20", "None", "TypeError"),
        ("d = {}\nd.setdefault('key', []).append(1)\nprint(d)", "{'key': [1]}", "{'key': []}", "{}", "TypeError"),
        ("x = [1, 2, 3]\nprint(x * 2)", "[1, 2, 3, 1, 2, 3]", "[2, 4, 6]", "TypeError", "[1, 2, 3, 2]"),
        ("print(isinstance(True, int))", "True", "False", "TypeError", "None"),
        ("x = {'a': 1}\ny = {'a': 2, 'b': 3}\nx.update(y)\nprint(x['a'])", "2", "1", "KeyError", "TypeError"),
        ("print(0.1 + 0.2 == 0.3)", "False", "True", "TypeError", "0.3"),
        ("x = [1, [2, 3]]\nimport copy\ny = copy.deepcopy(x)\ny[1].append(4)\nprint(x[1])", "[2, 3]", "[2, 3, 4]", "TypeError", "None"),
        ("print(len(set('aabbcc')))", "3", "6", "2", "TypeError"),
        ("x = {i: i**2 for i in range(4)}\nprint(x[3])", "9", "3", "4", "KeyError"),
        ("a = [1, 2, 3, 4, 5]\nprint(a[-3:])", "[3, 4, 5]", "[1, 2, 3]", "[5, 4, 3]", "IndexError"),
        ("x = 'hello'\nprint(x.replace('l', 'L', 1))", "heLlo", "heLLo", "hello", "TypeError"),
        ("print(sum(range(1, 6)))", "15", "21", "10", "TypeError"),
        ("x = [3, 1, 4, 1, 5]\nx.sort(reverse=True)\nprint(x[0])", "5", "1", "3", "TypeError"),
        ("print(all([True, True, False]))", "False", "True", "None", "TypeError"),
        ("print(any([False, False, True]))", "True", "False", "None", "TypeError"),
    ]
    random.shuffle(code_output_qs)
    for code, opt_a, opt_b, opt_c, opt_d in code_output_qs:
        if len(fillers) >= needed_count:
            break
        topic = topics_cycle[idx % len(topics_cycle)]
        idx += 1
        q_text = f"What is the output of this code?\n\n{code}"
        if q_text not in existing_texts:
            fillers.append(make_q(q_text, opt_a, opt_b, opt_c, opt_d, "A", topic))
            existing_texts.add(q_text)
    
    return fillers

# Check if we need more questions
if len(all_replacements) < total_needed:
    shortfall = total_needed - len(all_replacements)
    print(f"Need {shortfall} more unique questions, generating fillers...")
    existing = {q["question_text"] for q in all_replacements}
    # Also exclude existing kept question texts
    existing.update(q["question_text"] for q in kept)
    fillers = gen_filler(shortfall, existing)
    all_replacements.extend(fillers)
    print(f"After fillers: {len(all_replacements)} total")

# Final dedup pass
final_seen = set()
final_unique = []
for q in all_replacements:
    if q["question_text"] not in final_seen:
        final_seen.add(q["question_text"])
        final_unique.append(q)
all_replacements = final_unique[:total_needed]
print(f"Final unique replacements: {len(all_replacements)}")

# Now rotate answers to match the needed distribution
# All generated questions have correct_answer = "A"
# We need: A=164, B=184, C=192, D=175

def rotate_answer(question, new_answer):
    """Rotate the options so the correct answer moves to new_answer position."""
    if new_answer == "A":
        return question  # Already correct
    
    q = question.copy()
    # Current correct is A, move it to new position
    correct_option = q["option_a"]  # This is the correct answer text
    
    if new_answer == "B":
        # Swap A and B
        q["option_a"], q["option_b"] = q["option_b"], q["option_a"]
    elif new_answer == "C":
        # Swap A and C
        q["option_a"], q["option_c"] = q["option_c"], q["option_a"]
    elif new_answer == "D":
        # Swap A and D
        q["option_a"], q["option_d"] = q["option_d"], q["option_a"]
    
    q["correct_answer"] = new_answer
    return q

# Build the answer assignment list
answer_assignments = []
for ans in "ABCD":
    answer_assignments.extend([ans] * needed_per_answer[ans])

# Shuffle to distribute evenly
random.shuffle(answer_assignments)

# Apply answer rotation
final_replacements = []
for i, q in enumerate(all_replacements):
    rotated = rotate_answer(q, answer_assignments[i])
    final_replacements.append(rotated)

print(f"Final replacements: {len(final_replacements)}")
replacement_answers = Counter(q["correct_answer"] for q in final_replacements)
print(f"Replacement answer distribution: {dict(sorted(replacement_answers.items()))}")

# ============================================================
# STEP 7: Combine and write output
# ============================================================
final_questions = kept + final_replacements
random.shuffle(final_questions)  # Shuffle so new questions are distributed throughout

print(f"\nFinal question count: {len(final_questions)}")

# Write to file
with open("app/questions.json", "w") as f:
    json.dump(final_questions, f, indent=2)

print("Written to app/questions.json")

# ============================================================
# STEP 8: Verification
# ============================================================
print("\n=== VERIFICATION ===")

# Reload and verify
with open("app/questions.json", "r") as f:
    verified = json.load(f)

# Check 1: Total count
assert len(verified) == 10000, f"FAIL: Count is {len(verified)}, expected 10000"
print(f"[PASS] Total count: {len(verified)}")

# Check 2: No template markers
marker_pattern = r"\(variation|\(Scenario|\[context"
violations = [q for q in verified if re.search(marker_pattern, q["question_text"])]
assert len(violations) == 0, f"FAIL: {len(violations)} questions still have markers"
print(f"[PASS] No template markers found")

# Check 3: Answer distribution
final_dist = Counter(q["correct_answer"] for q in verified)
print(f"Answer distribution: {dict(sorted(final_dist.items()))}")
for ans in "ABCD":
    diff = abs(final_dist[ans] - 2500)
    assert diff <= 5, f"FAIL: Answer {ans} has {final_dist[ans]}, expected 2500 +/- 5"
print(f"[PASS] Answer distribution balanced (within +/- 5)")

# Check 4: No duplicate question_text
texts = [q["question_text"] for q in verified]
unique_texts = set(texts)
assert len(texts) == len(unique_texts), f"FAIL: {len(texts) - len(unique_texts)} duplicates remain"
print(f"[PASS] No duplicate question_text values")

# Check 5: All required fields present
required_fields = {"question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "difficulty", "topic"}
for i, q in enumerate(verified):
    missing = required_fields - set(q.keys())
    assert not missing, f"FAIL: Question {i} missing fields: {missing}"
print(f"[PASS] All questions have required fields")

# Check 6: Valid answers
valid_answers = {"A", "B", "C", "D"}
invalid = [q for q in verified if q["correct_answer"] not in valid_answers]
assert len(invalid) == 0, f"FAIL: {len(invalid)} questions have invalid answers"
print(f"[PASS] All answers are valid (A/B/C/D)")

print("\n=== ALL VERIFICATIONS PASSED ===")
