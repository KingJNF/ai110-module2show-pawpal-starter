# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

SMARTER SCHEDULING:
    I added several new features or modifications to existing sections of the app to make it easier for pet owners. They can now see whether a block of time has been taken up the same pet or another pet they own. They are able to filter and sort the assigned tasks for their pet or pets. It can also detect conflicts in scheduling with the same pet or other pets belonging to the same owner. It also can now handle reoccuring daily and weekly tasks.

    TESTING PAWPAL+:
     Using the following command line in the terminal: python -m pytest test_pawpal_system.py -v
     I was able to run the gamut of tests created by the AI to test for common and edge test cases of the app. My confidence level is at 5. That is a result of after I ran the test after fixing the errors found in about a dozen of the testing scripts a total of at least three times and got all 107 tests passed each time.