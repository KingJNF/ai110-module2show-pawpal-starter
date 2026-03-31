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


![PawPal+ App Screenshot](<PawPal App Final Screenshot.PNG>)


     🐾 PawPal+ Feature List:
     
Core Data Model:

1) Owner Profile Management — Owners register with name, email, phone, and address, and can update their info at any time.
2) Pet Profile Management — Owners create pets with detailed profiles including name, type, breed, age, gender, and weight.
3) Task Data Model — Tasks carry a type, name, description, duration, priority, frequency, and status.
4) Enum-Based Categorization — Tasks, frequencies, and statuses use Python enums to prevent invalid values and enforce consistency.
5) Default Duration Suggestions — Each task type auto-fills a realistic default duration based on a predefined lookup table.


Scheduling Engine:

6) 7-Day Schedule Builder — Generates 168 half-hour time slots across a full week from 8 AM to 8 PM.
7) Task Scheduling with Validation — Verifies time boundary and overlap rules before placing any task on the schedule.
8) Task Moving with Rollback — Moves a task to a new date and time, automatically rolling back if the new slot fails validation.
9) Auto-Schedule (Greedy Algorithm) — Automatically places all unscheduled tasks into the earliest available slots sorted by priority.
10) Next Available Slot Finder — Scans forward in 5-minute increments across up to 7 days to find the first open slot that fits a task's duration.


Sorting & Filtering:

11) Sort Tasks by Time — Displays all scheduled tasks in chronological order regardless of the order they were added.
12) Filter by Pet — Narrows the task list to show only a specific pet's tasks.
13) Filter by Status — Narrows the task list to show only tasks matching a chosen status such as Pending or Completed.
14) Combined Filter — Applies both pet and status filters simultaneously while maintaining chronological sort order.
15) Priority View — Displays all scheduled tasks ordered from highest to lowest priority.


Conflict Detection:

16) Lightweight Conflict Detection — Compares every unique pair of scheduled tasks for time overlaps and returns warning messages instead of crashing.
17) Same-Pet Conflict Detection — Identifies when a single pet has two tasks whose time ranges overlap.
18) Cross-Pet Conflict Detection — Identifies when tasks for different pets overlap since the owner can only attend to one pet at a time.
19) Post-Action Conflict Check — Runs conflict detection immediately after scheduling or moving a task and warns the user of any new overlaps.
20) Conflict Resolution Guidance — Displays an actionable tip directing the user to the Move a Task section to fix overlaps.


Recurring Task Management:

21) Recurring Task Detection — Determines whether a task repeats based on its frequency setting.
22) Auto-Renewal on Completion — Completing a recurring task automatically creates and schedules the next occurrence.
23) Accurate Date Calculation — Computes the next occurrence date using Python's timedelta for daily, weekly, monthly, and custom intervals.
24) Occurrence Tracking — Counts how many times a recurring task has been completed and stops renewing custom tasks after reaching their repeat count.
25) Renewal Conflict Fallback — Searches for an alternative time slot if the preferred renewal slot is already occupied.


Timezone Support:

26) Timezone-Aware Datetimes — All scheduling operations create and compare datetimes with timezone info attached via Python's zoneinfo module.
27) Configurable Owner Timezone — Each owner can be assigned a timezone that propagates to their scheduler and all datetime calculations.
28) Timezone-Safe Comparisons — Ensures all datetime comparisons involve timezone-aware objects to prevent silent errors across daylight saving transitions.


Notifications & Insights:

29) Upcoming Task Alerts — Surfaces all tasks scheduled within the next 24 hours sorted by how soon they occur.
30) Overdue Task Alerts — Flags any task whose scheduled time has passed but has not been marked as completed.
31) Schedule Explanation — Generates a human-readable sentence for each task explaining why it was placed at its current time and priority.


User Interface:

32) Owner Registration Flow — Presents a setup form on first visit and blocks the rest of the app until the owner's information is submitted.
33) Sidebar Filters & Sort Controls — Provides dropdown menus and a radio toggle in the sidebar for filtering by pet, status, and sort order.
34) Conflict Warning Banner — Displays a red alert at the top of the page listing every detected scheduling conflict.
35) Task Dashboard with Metrics — Shows an interactive table of all tasks alongside summary counters for pending, in-progress, and completed totals.
36) Restricted Time Picker — Limits the scheduling dropdown to 8 AM through 8 PM in 15-minute increments to prevent invalid selections.
37) Dynamic Duration Defaults — Updates the duration field automatically when the user selects a different task type.
38) Recurring Task Completion UI — Displays the task's frequency and remaining occurrences before the user confirms completion.
39) Profile Edit with Persistent Notification — Uses session state to carry a success message across the page rerun so the user sees confirmation after updating their profile.


Testing:

40) 107 Automated Tests — Comprehensive pytest suite covering every public method across all four main classes
41) Happy Path Coverage — 23 tests verifying that sorting, filtering, recurring renewal, and conflict detection work correctly under normal usage.
42) Edge Case Coverage — 18 tests validating graceful handling of empty lists, duplicate times, exhausted repeat counts, missing fields, and partial overlaps.