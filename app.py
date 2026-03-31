import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time as dt_time
from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    TaskType, Frequency, Status, DEFAULT_DURATIONS,
)

# ===================================================================
# PAGE CONFIG — must be the FIRST Streamlit command
# ===================================================================
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ===================================================================
# Helper: Generate time options between 8AM and 8PM
# ===================================================================
def get_time_options(interval_minutes=15):
    """Generate a list of time strings from 8:00 AM to 8:00 PM."""
    times = []
    current = dt_time(8, 0)
    end = dt_time(20, 0)
    while current <= end:
        times.append(current)
        # Advance by interval
        total_minutes = current.hour * 60 + current.minute + interval_minutes
        if total_minutes > 20 * 60:
            break
        current = dt_time(total_minutes // 60, total_minutes % 60)
    return times

TIME_OPTIONS = get_time_options(interval_minutes=15)
TIME_LABELS = [t.strftime("%I:%M %p") for t in TIME_OPTIONS]

# ===================================================================
# Session State — persistent "memory" across reruns
# ===================================================================
if "owner" not in st.session_state:
    st.session_state["owner"] = None  # No default — user enters info

if "selected_task_type" not in st.session_state:
    st.session_state["selected_task_type"] = TaskType.FEEDING.value

owner = st.session_state["owner"]

# ===================================================================
# Owner Registration (shown if no owner exists yet)
# ===================================================================
if owner is None:
    st.title("🐾 Welcome to PawPal+")
    st.markdown("**Let's get started!** Enter your information below to set up your account.")

    with st.form("owner_setup_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            email = st.text_input("Email")
        with col2:
            phone = st.text_input("Phone Number")
            address = st.text_input("Address")

        owner_submitted = st.form_submit_button("Create My Account")

        if owner_submitted:
            if first_name.strip() and last_name.strip() and email.strip():
                st.session_state["owner"] = Owner(
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    address=address.strip(),
                )
                st.success(f"✅ Welcome, {first_name}! Your account has been created.")
                st.rerun()
            else:
                st.error("Please fill in at least your first name, last name, and email.")

    st.stop()  # Don't render the rest of the app until owner is created

# ===================================================================
# From here on, owner is guaranteed to exist
# ===================================================================
scheduler = owner.scheduler

# ===================================================================
# Sidebar — Owner Info, Filters, and Controls
# ===================================================================
st.sidebar.title("👤 Owner Profile")
with st.sidebar.expander("View / Edit Profile", expanded=False):
    st.write(f"**Name:** {owner.first_name} {owner.last_name}")
    st.write(f"**Email:** {owner.email}")
    st.write(f"**Phone:** {owner.phone}")
    st.write(f"**Address:** {owner.address}")

    with st.form("edit_owner_form"):
        new_first = st.text_input("First Name", value=owner.first_name)
        new_last = st.text_input("Last Name", value=owner.last_name)
        new_email = st.text_input("Email", value=owner.email)
        new_phone = st.text_input("Phone", value=owner.phone)
        new_address = st.text_input("Address", value=owner.address)
        edit_submitted = st.form_submit_button("Update Profile")

        if edit_submitted:
            owner.modify_info(
                first_name=new_first.strip() or None,
                last_name=new_last.strip() or None,
                email=new_email.strip() or None,
                phone=new_phone.strip() or None,
                address=new_address.strip() or None,
            )
            st.session_state["profile_updated"] = True
            st.rerun()


# Show profile update notification in sidebar
if st.session_state.get("profile_updated", False):
    st.sidebar.success(
        f"✅ Profile updated successfully! "
    )
    st.session_state["profile_updated"] = False

st.sidebar.divider()
st.sidebar.title("🔍 Filters")


# Pet filter
pet_filter_options = ["All Pets"] + [p.name for p in owner.pets]
selected_pet_filter = st.sidebar.selectbox("Filter by Pet", pet_filter_options)

# Status filter
status_filter_options = ["All Statuses"] + [s.value for s in Status]
selected_status_filter = st.sidebar.selectbox("Filter by Status", status_filter_options)

# Sort control
sort_options = ["By Time (Earliest First)", "By Priority (Highest First)"]
selected_sort = st.sidebar.radio("Sort Tasks", sort_options)

st.sidebar.divider()
st.sidebar.caption(f"📊 Total Pets: {len(owner.pets)}")
total_tasks = sum(len(p.tasks) for p in owner.pets)
st.sidebar.caption(f"📋 Total Tasks: {total_tasks}")

# ===================================================================
# Title & Intro
# ===================================================================
st.title("🐾 PawPal+")
st.markdown(
    f"Welcome back, **{owner.first_name}**! "
    "Add pets, assign tasks, and schedule everything below."
)

# ===================================================================
# Conflict & Notification Banner (always visible at the top)
# ===================================================================
if owner.pets:
    # Conflict warnings
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(f"🚨 **{len(conflicts)} Scheduling Conflict(s) Detected!**")
        for warning in conflicts:
            st.warning(warning)
        st.caption(
            "💡 **Tip:** Use the 'Move a Task' section below to resolve "
            "conflicts by rescheduling one of the overlapping tasks."
        )

    # Overdue tasks
    overdue = scheduler.get_overdue_tasks()
    if overdue:
        st.warning(f"⏰ **{len(overdue)} Overdue Task(s)!**")
        for task_info in overdue:
            st.write(
                f"  ⚠️ **{task_info['task_name']}** for {task_info['pet_name']} "
                f"— was due {task_info['was_scheduled']} "
                f"(Priority: {task_info['priority']})"
            )

    # Upcoming tasks (next 24 hours)
    upcoming = scheduler.get_upcoming_tasks(hours=24)
    if upcoming:
        with st.expander(
            f"🔔 {len(upcoming)} Task(s) Coming Up in the Next 24 Hours",
            expanded=False,
        ):
            for task_info in upcoming:
                hours_until = task_info["minutes_until"] // 60
                mins_until = task_info["minutes_until"] % 60
                st.info(
                    f"🐾 **{task_info['task_name']}** for {task_info['pet_name']} "
                    f"— in {hours_until}h {mins_until}m "
                    f"({task_info['scheduled']}) | Priority: {task_info['priority']}"
                )

st.divider()

# ===================================================================
# Section 1: Add a Pet
# ===================================================================
st.header("➕ Add a Pet")

with st.form("add_pet_form"):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet Name")
    with col2:
        animal_type = st.text_input("Animal Type (e.g., Dog, Cat)")
    submitted = st.form_submit_button("Add Pet")

    if submitted:
        if pet_name.strip():
            owner.create_pet(
                name=pet_name.strip(),
                animal_type=animal_type.strip() or None,
            )
            st.success(f"✅ Added **{pet_name}** the {animal_type or 'pet'}!")
            st.rerun()
        else:
            st.error("Please enter a pet name.")

# Display Current Pets
st.subheader("Your Pets")
if owner.pets:
    pet_data = []
    for pet in owner.pets:
        s = pet.summary()
        pet_data.append({
            "🐾 Name": s["name"],
            "Type": s["animal_type"] or "Unknown",
            "Total Tasks": s["task_count"],
            "⏳ Pending": s["pending"],
            "🔄 In Progress": s["in_progress"],
            "✅ Completed": s["completed"],
        })
    st.table(pd.DataFrame(pet_data))
else:
    st.info("No pets added yet. Use the form above!")

st.divider()

# ===================================================================
# Section 2: Assign a Task to a Pet
# ===================================================================
st.header("📋 Assign a Task to a Pet")

if owner.pets:
    # Task type selector OUTSIDE the form so it triggers a rerun
    # and updates the default duration dynamically
    task_type_value = st.selectbox(
        "Task Type (select first — duration will auto-adjust)",
        [t.value for t in TaskType],
        key="task_type_selector",
    )
    suggested_duration = DEFAULT_DURATIONS.get(TaskType(task_type_value), 30)
    st.caption(f"💡 Suggested duration for **{task_type_value}**: **{suggested_duration} minutes**")

    with st.form("assign_task_form"):
        col1, col2 = st.columns(2)

        with col1:
            pet_names = [pet.name for pet in owner.pets]
            selected_pet_name = st.selectbox("Select Pet", pet_names)
            task_name = st.text_input("Task Name")
            task_description = st.text_input("Description")

        with col2:
            duration = st.number_input(
                "Duration (minutes)",
                min_value=1, max_value=240, step=5,
                value=suggested_duration,
            )
            priority = st.number_input(
                "Priority (1–10, higher = more important)",
                min_value=1, max_value=10, step=1, value=5,
            )
            frequency = st.selectbox("Frequency", [f.value for f in Frequency])

            # Show custom fields only when Custom frequency is selected
            repeat_count = None
            repeat_interval = None
            if frequency == Frequency.CUSTOM.value:
                repeat_count = st.number_input(
                    "Total Occurrences", min_value=2, max_value=365, value=7,
                    help="How many times total should this task repeat?",
                )
                repeat_interval = st.number_input(
                    "Days Between Occurrences", min_value=1, max_value=30, value=1,
                    help="E.g., 1 = every day, 2 = every other day",
                )

        task_submitted = st.form_submit_button("Assign Task")

        if task_submitted:
            if task_name.strip():
                selected_pet = next(
                    p for p in owner.pets if p.name == selected_pet_name
                )

                new_task = Task(
                    type=TaskType(task_type_value),
                    name=task_name.strip(),
                    description=task_description.strip(),
                    duration_minutes=int(duration),
                    priority=int(priority),
                    frequency=Frequency(frequency),
                    repeat_count=int(repeat_count) if repeat_count else None,
                    repeat_interval_days=int(repeat_interval) if repeat_interval else None,
                )

                try:
                    owner.assign_task_to_pet(selected_pet, new_task)
                    st.success(f"✅ Assigned **'{task_name}'** to **{selected_pet_name}**!")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {e}")
            else:
                st.error("Please enter a task name.")
else:
    st.info("Add a pet first before assigning tasks.")

st.divider()

# ===================================================================
# Section 3: Schedule a Task
# ===================================================================
st.header("📅 Schedule a Task")

unscheduled = []
for pet in owner.pets:
    for task in pet.tasks:
        if task.scheduled_date is None and task.status != Status.COMPLETED:
            unscheduled.append((pet, task))

if unscheduled:
    with st.form("schedule_task_form"):
        task_labels = [
            f"{pet.name} → {task.name} ({task.type.value}, {task.duration_minutes} min)"
            for pet, task in unscheduled
        ]
        selected_label = st.selectbox("Select an unscheduled task", task_labels)
        selected_index = task_labels.index(selected_label)
        selected_pet, selected_task = unscheduled[selected_index]

        col1, col2 = st.columns(2)
        with col1:
            sched_date = st.date_input("Date")
        with col2:
            # Restricted time picker: only 8AM–8PM in 15-min increments
            selected_time_label = st.selectbox("Time (8AM – 8PM)", TIME_LABELS)
            selected_time_index = TIME_LABELS.index(selected_time_label)
            selected_time = TIME_OPTIONS[selected_time_index]

        st.caption(
            f"⏰ Selected: **{selected_time_label}** — "
            f"Task runs {selected_task.duration_minutes} min, "
            f"ending at "
            f"**{(datetime.combine(sched_date, selected_time) + timedelta(minutes=selected_task.duration_minutes)).strftime('%I:%M %p')}**"
        )

        schedule_submitted = st.form_submit_button("Schedule Task")

        if schedule_submitted:
            date_as_dt = datetime(sched_date.year, sched_date.month, sched_date.day)
            time_as_dt = datetime(1900, 1, 1, selected_time.hour, selected_time.minute)

            try:
                owner.scheduler.assign_task_to_schedule(
                    pet=selected_pet,
                    task=selected_task,
                    date=date_as_dt,
                    time=time_as_dt,
                )
                st.success(
                    f"✅ Scheduled **'{selected_task.name}'** for "
                    f"**{selected_pet.name}** on "
                    f"{sched_date.strftime('%Y-%m-%d')} at {selected_time_label}!"
                )

                new_conflicts = scheduler.detect_conflicts()
                if new_conflicts:
                    st.warning(
                        f"⚠️ Heads up — this created {len(new_conflicts)} "
                        f"conflict(s). Check the top of the page."
                    )
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")

    # Auto-schedule button
    if st.button("🤖 Auto-Schedule All Unscheduled Tasks"):
        scheduler.auto_schedule()
        st.success(
            "✅ All unscheduled tasks have been placed using "
            "priority-based scheduling!"
        )
        st.rerun()

elif owner.pets:
    st.info(
        "All tasks are already scheduled or completed. "
        "Assign a new task above!"
    )
else:
    st.info("Add a pet and assign tasks first.")

st.divider()

# ===================================================================
# Section 4: Sorted & Filtered Task Dashboard
# ===================================================================
st.header("📊 Task Dashboard")

if owner.pets and total_tasks > 0:
    # Apply filters from sidebar
    filter_pet = None
    filter_status = None

    if selected_pet_filter != "All Pets":
        filter_pet = next(
            (p for p in owner.pets if p.name == selected_pet_filter), None
        )

    if selected_status_filter != "All Statuses":
        filter_status = Status(selected_status_filter)

    # Get filtered data
    filtered_tasks = scheduler.filter_tasks(
        pet=filter_pet, status=filter_status
    )

    # Apply sort
    if selected_sort == "By Priority (Highest First)":
        filtered_tasks = sorted(
            filtered_tasks, key=lambda t: t["priority"], reverse=True
        )

    if filtered_tasks:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Shown", len(filtered_tasks))
        with col2:
            pending_count = len(
                [t for t in filtered_tasks if t["status"] == "pending"]
            )
            st.metric("⏳ Pending", pending_count)
        with col3:
            in_progress_count = len(
                [t for t in filtered_tasks if t["status"] == "in_progress"]
            )
            st.metric("🔄 In Progress", in_progress_count)
        with col4:
            completed_count = len(
                [t for t in filtered_tasks if t["status"] == "completed"]
            )
            st.metric("✅ Completed", completed_count)

        # Build table data
        table_data = []
        for t in filtered_tasks:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
            }.get(t["status"], "❓")

            table_data.append({
                "Pet": t["pet_name"],
                "Task": t["task_name"],
                "Type": t["task_type"],
                "Priority": f"{'⭐' * min(t['priority'], 5)} ({t['priority']})",
                "Duration": f"{t['duration_minutes']} min",
                "Time": f"{t['scheduled_date']} {t['scheduled_time']}–{t['end_time']}",
                "Status": f"{status_icon} {t['status']}",
                "Frequency": t["frequency"],
            })

        st.dataframe(
            pd.DataFrame(table_data),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No tasks match the current filters. Try adjusting the sidebar.")
else:
    st.info("Add pets and tasks to see your dashboard.")

st.divider()

# ===================================================================
# Section 5: Complete a Task (with recurring auto-renewal)
# ===================================================================
st.header("✅ Complete a Task")

active_tasks = []
for pet in owner.pets:
    for task in pet.tasks:
        if task.status in {Status.PENDING, Status.IN_PROGRESS} and task.scheduled_date:
            active_tasks.append((pet, task))

if active_tasks:
    with st.form("complete_task_form"):
        complete_labels = [
            f"{pet.name} → {task.name} ({task.type.value}) "
            f"at {task.scheduled_time.strftime('%I:%M %p')} "
            f"on {task.scheduled_date.strftime('%Y-%m-%d')}"
            for pet, task in active_tasks
        ]
        selected_complete = st.selectbox(
            "Select a task to complete", complete_labels
        )
        complete_index = complete_labels.index(selected_complete)
        complete_pet, complete_task = active_tasks[complete_index]

        # Show recurring info
        if complete_task.is_recurring():
            st.info(
                f"🔄 This is a **{complete_task.frequency.value}** recurring task. "
                f"Completing it will automatically create the next occurrence."
            )
            if (
                complete_task.frequency == Frequency.CUSTOM
                and complete_task.repeat_count
            ):
                remaining = (
                    complete_task.repeat_count
                    - complete_task.occurrences_completed
                )
                st.caption(f"📋 Remaining occurrences: {remaining}")

        complete_submitted = st.form_submit_button("Mark as Complete")

        if complete_submitted:
            new_task = scheduler.complete_and_renew(complete_pet, complete_task)

            st.success(f"✅ **'{complete_task.name}'** marked as complete!")

            if new_task:
                new_date = (
                    new_task.scheduled_date.strftime("%Y-%m-%d")
                    if new_task.scheduled_date
                    else "TBD"
                )
                new_time = (
                    new_task.scheduled_time.strftime("%I:%M %p")
                    if new_task.scheduled_time
                    else "TBD"
                )
                st.info(
                    f"🔄 **Next occurrence auto-created:** '{new_task.name}' "
                    f"scheduled for {new_date} at {new_time}"
                )
            st.rerun()
else:
    st.info("No active scheduled tasks to complete.")

st.divider()

# ===================================================================
# Section 6: Move a Scheduled Task
# ===================================================================
st.header("🔀 Move a Scheduled Task")

scheduled_tasks = []
for pet in owner.pets:
    for task in pet.tasks:
        if task.scheduled_date is not None and task.status != Status.COMPLETED:
            scheduled_tasks.append((pet, task))

if scheduled_tasks:
    with st.form("move_task_form"):
        move_labels = [
            f"{pet.name} → {task.name} "
            f"(currently {task.scheduled_date.strftime('%Y-%m-%d')} "
            f"at {task.scheduled_time.strftime('%I:%M %p')})"
            for pet, task in scheduled_tasks
        ]
        selected_move_label = st.selectbox(
            "Select a task to move", move_labels
        )
        move_index = move_labels.index(selected_move_label)
        move_pet, move_task = scheduled_tasks[move_index]

        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("New Date")
        with col2:
            # Restricted time picker: only 8AM–8PM
            new_time_label = st.selectbox("New Time (8AM – 8PM)", TIME_LABELS)
            new_time_index = TIME_LABELS.index(new_time_label)
            new_time_obj = TIME_OPTIONS[new_time_index]

        st.caption(
            f"⏰ Task is {move_task.duration_minutes} min — "
            f"would end at "
            f"**{(datetime.combine(new_date, new_time_obj) + timedelta(minutes=move_task.duration_minutes)).strftime('%I:%M %p')}**"
        )

        move_submitted = st.form_submit_button("Move Task")

        if move_submitted:
            new_date_dt = datetime(new_date.year, new_date.month, new_date.day)
            new_time_dt = datetime(1900, 1, 1, new_time_obj.hour, new_time_obj.minute)

            try:
                result = owner.scheduler.move_task(
                    pet=move_pet,
                    task=move_task,
                    date=new_date_dt,
                    time=new_time_dt,
                )
                st.success(f"✅ {result['message']}")

                post_move_conflicts = scheduler.detect_conflicts()
                if post_move_conflicts:
                    st.warning(
                        f"⚠️ Moving this task created "
                        f"{len(post_move_conflicts)} conflict(s). "
                        f"Check the top of the page."
                    )
                st.rerun()
            except ValueError as e:
                st.error(f"❌ {e}")
else:
    st.info("No scheduled tasks to move. Schedule a task first!")

st.divider()

# ===================================================================
# Section 7: Schedule Explanation
# ===================================================================
st.header("📖 Schedule Explanation")

if owner.pets and total_tasks > 0:
    with st.expander(
        "Why was each task scheduled at its time?", expanded=False
    ):
        explanations = scheduler.explain_schedule()
        for explanation in explanations:
            st.write(explanation)
else:
    st.info("Schedule tasks to see explanations for each placement.")

st.divider()

# ===================================================================
# Section 8: Full 7-Day Schedule View
# ===================================================================
st.header("🗓️ 7-Day Schedule View")

if owner.pets:
    if st.button("Generate 7-Day Schedule"):
        schedule = owner.scheduler.view_schedule(list(owner.pets))

        if schedule:
            booked_slots = [s for s in schedule if not s["available"]]
            free_count = len([s for s in schedule if s["available"]])

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📅 Booked Slots", len(booked_slots))
            with col2:
                st.metric("✅ Available Slots", free_count)

            if booked_slots:
                from collections import defaultdict

                by_date = defaultdict(list)
                for slot in booked_slots:
                    by_date[slot["date"]].append(slot)

                for date_str in sorted(by_date.keys()):
                    st.subheader(f"📆 {date_str}")
                    day_data = []
                    for slot in by_date[date_str]:
                        for booking in slot["bookings"]:
                            day_data.append({
                                "Time": slot["time"],
                                "Pet": booking["pet_name"],
                                "Task": booking["task_name"],
                                "Type": booking["task_type"],
                                "Priority": booking["priority"],
                                "Duration": f"{booking['duration_minutes']} min",
                                "Status": booking["task_status"],
                            })
                    if day_data:
                        st.dataframe(
                            pd.DataFrame(day_data),
                            use_container_width=True,
                            hide_index=True,
                        )
            else:
                st.info("No tasks scheduled yet.")
        else:
            st.warning("Could not generate schedule.")
else:
    st.info("Add pets and schedule tasks to view your calendar.")

st.divider()

# ===================================================================
# Footer
# ===================================================================
st.caption("Built with ❤️ using PawPal+ and Streamlit")