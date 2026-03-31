import streamlit as st
from datetime import datetime
from pawpal_system import Owner, Pet, Task, Scheduler, TaskType, Frequency, Status

# ===================================================================
# PAGE CONFIG — must be the FIRST Streamlit command
# ===================================================================
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ===================================================================
# Step 2: Session State — persistent "memory" across reruns
# ===================================================================
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(
        first_name="John",
        last_name="Doe",
        email="john@email.com",
        phone="555-123-4567",
        address="123 Main St",
    )

owner = st.session_state["owner"]

# ===================================================================
# Title & Intro
# ===================================================================
st.title("🐾 PawPal+")
st.markdown(
    "Welcome to **PawPal+** — your pet care planning assistant. "
    "Add pets, assign tasks, and schedule everything below."
)

st.divider()

# ===================================================================
# Section 1: Add a Pet (wired to owner.create_pet)
# ===================================================================
st.header("➕ Add a Pet")

with st.form("add_pet_form"):
    pet_name = st.text_input("Pet Name")
    animal_type = st.text_input("Animal Type (e.g., Dog, Cat)")
    submitted = st.form_submit_button("Add Pet")

    if submitted:
        if pet_name.strip():
            owner.create_pet(name=pet_name.strip(), animal_type=animal_type.strip() or None)
            st.success(f"✅ Added **{pet_name}** the {animal_type or 'pet'}!")
        else:
            st.error("Please enter a pet name.")

# --- Display Current Pets ---
st.subheader("Your Pets")
if owner.pets:
    for pet in owner.pets:
        summary = pet.summary()
        st.write(
            f"🐾 **{summary['name']}** — {summary['animal_type'] or 'Unknown type'} | "
            f"Tasks: {summary['task_count']} "
            f"(✅ {summary['completed']} | 🔄 {summary['in_progress']} | ⏳ {summary['pending']})"
        )
else:
    st.info("No pets added yet. Use the form above!")

st.divider()

# ===================================================================
# Section 2: Assign a Task to a Pet (wired to owner.assign_task_to_pet)
# ===================================================================
st.header("📋 Assign a Task to a Pet")

if owner.pets:
    with st.form("assign_task_form"):
        # Select pet
        pet_names = [pet.name for pet in owner.pets]
        selected_pet_name = st.selectbox("Select Pet", pet_names)

        # Task details matching your Task dataclass
        task_type = st.selectbox("Task Type", [t.value for t in TaskType])
        task_name = st.text_input("Task Name")
        task_description = st.text_input("Description")
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, step=5, value=30)
        priority = st.number_input("Priority (1–10, higher = more important)", min_value=1, max_value=10, step=1, value=5)
        frequency = st.selectbox("Frequency", [f.value for f in Frequency])

        task_submitted = st.form_submit_button("Assign Task")

        if task_submitted:
            if task_name.strip():
                selected_pet = next(p for p in owner.pets if p.name == selected_pet_name)

                new_task = Task(
                    type=TaskType(task_type),
                    name=task_name.strip(),
                    description=task_description.strip(),
                    duration_minutes=int(duration),
                    priority=int(priority),
                    frequency=Frequency(frequency),
                )

                try:
                    owner.assign_task_to_pet(selected_pet, new_task)
                    st.success(f"✅ Assigned **'{task_name}'** to **{selected_pet_name}**!")
                except ValueError as e:
                    st.error(f"❌ {e}")
            else:
                st.error("Please enter a task name.")

    # --- Display Tasks Per Pet ---
    st.subheader("Tasks by Pet")
    for pet in owner.pets:
        tasks = owner.view_pet_tasks(pet)
        if tasks:
            st.markdown(f"**{pet.name}'s Tasks:**")
            for task in tasks:
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(task.status.value, "❓")
                st.write(
                    f"  {status_icon} **{task.name}** ({task.type.value}) — "
                    f"Priority: {task.priority} | Duration: {task.duration_minutes} min | "
                    f"Status: {task.status.value}"
                )
        else:
            st.caption(f"{pet.name} has no tasks yet.")
else:
    st.info("Add a pet first before assigning tasks.")

st.divider()

# ===================================================================
# Section 3: Schedule a Task (wired to owner.scheduler.assign_task_to_schedule)
# ===================================================================
st.header("📅 Schedule a Task")

# Collect all unscheduled tasks across all pets
unscheduled = []
for pet in owner.pets:
    for task in pet.tasks:
        if task.scheduled_date is None and task.status != Status.COMPLETED:
            unscheduled.append((pet, task))

if unscheduled:
    with st.form("schedule_task_form"):
        # Build display labels for the dropdown
        task_labels = [f"{pet.name} → {task.name} ({task.type.value})" for pet, task in unscheduled]
        selected_label = st.selectbox("Select an unscheduled task", task_labels)
        selected_index = task_labels.index(selected_label)
        selected_pet, selected_task = unscheduled[selected_index]

        # Date and time pickers
        sched_date = st.date_input("Date")
        sched_time = st.time_input("Time")

        schedule_submitted = st.form_submit_button("Schedule Task")

        if schedule_submitted:
            # Convert date and time to datetime objects for the Scheduler
            date_as_dt = datetime(sched_date.year, sched_date.month, sched_date.day)
            time_as_dt = datetime(1900, 1, 1, sched_time.hour, sched_time.minute)

            try:
                owner.scheduler.assign_task_to_schedule(
                    pet=selected_pet,
                    task=selected_task,
                    date=date_as_dt,
                    time=time_as_dt,
                )
                st.success(
                    f"✅ Scheduled **'{selected_task.name}'** for **{selected_pet.name}** "
                    f"on {sched_date.strftime('%Y-%m-%d')} at {sched_time.strftime('%H:%M')}!"
                )
            except ValueError as e:
                st.error(f"❌ {e}")
elif owner.pets:
    st.info("All tasks are either already scheduled or completed. Assign a new task above!")
else:
    st.info("Add a pet and assign tasks first.")

st.divider()

# ===================================================================
# Section 4: View Full Schedule (wired to owner.scheduler.view_schedule)
# ===================================================================
st.header("🗓️ View Schedule")

if owner.pets:
    if st.button("Generate 7-Day Schedule"):
        schedule = owner.scheduler.view_schedule(list(owner.pets))

        if schedule:
            booked_slots = [s for s in schedule if not s["available"]]
            free_count = len([s for s in schedule if s["available"]])

            if booked_slots:
                st.subheader("Booked Slots")
                for slot in booked_slots:
                    st.markdown(f"**{slot['date']}** at **{slot['time']}**")
                    for booking in slot["bookings"]:
                        st.write(
                            f"  🐾 {booking['pet_name']} — {booking['task_name']} "
                            f"({booking['task_type']}) | Priority: {booking['priority']} | "
                            f"Duration: {booking['duration_minutes']} min | Status: {booking['task_status']}"
                        )
            else:
                st.info("No tasks scheduled yet.")

            st.caption(f"📊 {len(booked_slots)} booked slot(s) | {free_count} available slot(s)")
        else:
            st.warning("Could not generate schedule.")

    # --- View by Priority ---
    if st.button("View Tasks by Priority"):
        priority_list = owner.scheduler.view_tasks_by_priority(list(owner.pets))
        if priority_list:
            st.subheader("Scheduled Tasks (Highest Priority First)")
            for entry in priority_list:
                st.write(
                    f"⭐ **Priority {entry['priority']}** — {entry['pet_name']}: "
                    f"{entry['task_name']} ({entry['task_type']}) | "
                    f"{entry['scheduled_date']} at {entry['scheduled_time']} | "
                    f"Duration: {entry['duration_minutes']} min | Status: {entry['task_status']}"
                )
        else:
            st.info("No scheduled tasks to display.")
else:
    st.info("Add pets and schedule tasks to view your calendar.")

st.divider()

# ===================================================================
# Section 5: Move a Task (wired to owner.scheduler.move_task)
# ===================================================================
st.header("🔀 Move a Scheduled Task")

# Collect all scheduled, non-completed tasks
scheduled_tasks = []
for pet in owner.pets:
    for task in pet.tasks:
        if task.scheduled_date is not None and task.status != Status.COMPLETED:
            scheduled_tasks.append((pet, task))

if scheduled_tasks:
    with st.form("move_task_form"):
        move_labels = [
            f"{pet.name} → {task.name} (currently {task.scheduled_date.strftime('%Y-%m-%d')} "
            f"at {task.scheduled_time.strftime('%H:%M')})"
            for pet, task in scheduled_tasks
        ]
        selected_move_label = st.selectbox("Select a task to move", move_labels)
        move_index = move_labels.index(selected_move_label)
        move_pet, move_task = scheduled_tasks[move_index]

        new_date = st.date_input("New Date")
        new_time = st.time_input("New Time")

        move_submitted = st.form_submit_button("Move Task")

        if move_submitted:
            new_date_dt = datetime(new_date.year, new_date.month, new_date.day)
            new_time_dt = datetime(1900, 1, 1, new_time.hour, new_time.minute)

            try:
                result = owner.scheduler.move_task(
                    pet=move_pet,
                    task=move_task,
                    date=new_date_dt,
                    time=new_time_dt,
                )
                st.success(f"✅ {result['message']}")
            except ValueError as e:
                st.error(f"❌ {e}")
else:
    st.info("No scheduled tasks to move. Schedule a task first!")

st.divider()
st.caption("Built with ❤️ using PawPal+ and Streamlit")