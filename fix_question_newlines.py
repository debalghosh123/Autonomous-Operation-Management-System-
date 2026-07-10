"""
Fix question_text formatting in questions.json.

Some questions store line breaks as literal two-character sequences (backslash + n)
instead of actual newline characters. This script converts those to real newlines
so that the browser can render them properly with CSS white-space: pre-wrap.

Only converts questions where literal \\n is used for formatting (no real newlines present).
Questions that already have real newlines AND literal \\n in code strings are left unchanged.
"""

import json

BACKSLASH_N = chr(92) + "n"  # The two-character sequence: \ followed by n
REAL_NEWLINE = chr(10)  # Actual newline character


def fix_questions():
    with open("app/questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_count = 0

    for question in data:
        text = question["question_text"]
        has_real_newline = REAL_NEWLINE in text
        has_literal_backslash_n = BACKSLASH_N in text

        # Only fix questions that use literal \n for formatting
        # (no real newlines present, meaning all line breaks are escaped)
        if has_literal_backslash_n and not has_real_newline:
            question["question_text"] = text.replace(BACKSLASH_N, REAL_NEWLINE)
            fixed_count += 1

    # Write back with ensure_ascii=False to preserve unicode
    with open("app/questions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"Fixed {fixed_count} questions (converted literal \\\\n to real newlines)")
    print(f"Total questions: {len(data)}")

    # Verify by loading and checking a sample
    with open("app/questions.json", "r", encoding="utf-8") as f:
        verify_data = json.load(f)

    # Find a previously-broken question and confirm it has real newlines
    sample = None
    for q in verify_data:
        if "What does exc_info=True do here?" in q["question_text"]:
            sample = q
            break

    if sample:
        text = sample["question_text"]
        assert REAL_NEWLINE in text, "ERROR: Sample question should have real newlines"
        assert BACKSLASH_N not in text, "ERROR: Sample question should not have literal \\\\n"
        print("Verification passed: sample question has real newlines")
    else:
        # Verify any question with a newline
        for q in verify_data:
            if REAL_NEWLINE in q["question_text"]:
                print(
                    f"Verification passed: found question with real newline in question_text"
                )
                break

    # Count questions that still have literal \n (should be the 16 with both)
    remaining = sum(
        1 for q in verify_data if BACKSLASH_N in q["question_text"]
    )
    print(
        f"Questions still containing literal \\\\n (in code strings): {remaining}"
    )


if __name__ == "__main__":
    fix_questions()
