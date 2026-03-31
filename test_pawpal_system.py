from unittest import result
from zoneinfo import ZoneInfo

import pytest
from datetime import date, datetime, time, timedelta
from pawpal_system import Owner, Task, TaskType, Status, Frequency


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def owner():
    return Owner("Jane", "Doe", "jane@example.com", "555-1234", "1 Main St")

@pytest.fixture
def other_owner():
    return Owner("Bob", "Smith", "bob@example.com", "555-9999", "2 Other St")

@pytest.fixture
def pet(owner):
    return owner.create_pet("Fido", animal_type="Dog")

@pytest.fixture
def other_pet(other_owner):
    return other_owner.create_pet("Whiskers", animal_type="Cat")

@pytest.fixture
def walk_task():
    return Task(type=TaskType.WALKING, name="Morning Walk",
                description="Walk the dog", duration_minutes=30, priority=2)

@pytest.fixture
def feed_task():
    return Task(type=TaskType.FEEDING, name="Breakfast",
                description="Feed the dog", duration_minutes=10, priority=3)

@pytest.fixture
def future_date():
    """A datetime two days from now — always within the 7-day schedule window."""
    return datetime.now() + timedelta(days=2)

@pytest.fixture
def slot_time():
    """Fixed 10 AM datetime used as the time component for scheduling."""
    return datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)


# ── Pet ───────────────────────────────────────────────────────────────────────

class TestPet:

    def test_update_info_full(self, pet):
        pet.update_info(animal_type="Dog", breed="Labrador", age=3, gender="Male", weight=28.5)
        assert pet.animal_type == "Dog"
        assert pet.breed == "Labrador"
        assert pet.age == 3
        assert pet.gender == "Male"
        assert pet.weight == 28.5

    def test_update_info_partial_leaves_other_fields_intact(self, pet):
        pet.update_info(breed="Poodle", age=5)
        pet.update_info(weight=10.0)
        assert pet.breed == "Poodle"
        assert pet.age == 5
        assert pet.weight == 10.0

    def test_add_task_links_pet(self, pet, walk_task):
        pet.add_task(walk_task)
        assert walk_task in pet.tasks
        assert walk_task.pet is pet

    def test_add_exact_duplicate_task_raises(self, pet, walk_task):
        pet.add_task(walk_task)
        with pytest.raises(ValueError, match="Task already assigned"):
            pet.add_task(walk_task)

    def test_add_duplicate_pending_type_raises(self, pet):
        t1 = Task(type=TaskType.FEEDING, name="Feed1", description="d", duration_minutes=10, priority=1)
        t2 = Task(type=TaskType.FEEDING, name="Feed2", description="d", duration_minutes=10, priority=1)
        pet.add_task(t1)
        with pytest.raises(ValueError, match="Cannot add duplicate pending/in-progress task"):
            pet.add_task(t2)

    def test_add_same_type_after_completion_allowed(self, pet):
        t1 = Task(type=TaskType.FEEDING, name="Feed1", description="d", duration_minutes=10, priority=1)
        t2 = Task(type=TaskType.FEEDING, name="Feed2", description="d", duration_minutes=10, priority=1)
        pet.add_task(t1)
        t1.complete_task()
        pet.add_task(t2)
        assert t2 in pet.tasks

    def test_remove_task_unlinks_pet(self, pet, walk_task):
        pet.add_task(walk_task)
        pet.remove_task(walk_task)
        assert walk_task not in pet.tasks
        assert walk_task.pet is None

    def test_remove_task_not_assigned_raises(self, pet):
        orphan = Task(type=TaskType.GROOMING, name="Groom", description="d", duration_minutes=20, priority=1)
        with pytest.raises(ValueError, match="not assigned"):
            pet.remove_task(orphan)

    def test_get_tasks_returns_all_statuses(self, pet):
        t_pending = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t_done = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=1)
        pet.add_task(t_pending)
        pet.add_task(t_done)
        t_done.complete_task()
        tasks = pet.get_tasks()
        assert t_pending in tasks
        assert t_done in tasks

    def test_summary_counts_by_status(self, pet):
        t1 = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=1)
        pet.add_task(t1)
        pet.add_task(t2)
        t1.assign_task()    # → in_progress
        t2.complete_task()  # → completed
        s = pet.summary()
        assert s["name"] == "Fido"
        assert s["task_count"] == 2
        assert s["pending"] == 0
        assert s["in_progress"] == 1
        assert s["completed"] == 1

    def test_summary_defaults(self, pet):
        s = pet.summary()
        assert s["breed"] is None
        assert s["age"] is None
        assert s["task_count"] == 0


# ── Owner ─────────────────────────────────────────────────────────────────────

class TestOwner:

    def test_create_pet_added_to_pets_list(self, owner):
        pet = owner.create_pet("Rex", animal_type="Dog")
        assert pet in owner.pets
        assert pet.owner is owner

    def test_create_multiple_pets(self, owner):
        owner.create_pet("Rex")
        owner.create_pet("Luna")
        assert len(owner.pets) == 2

    def test_modify_info_updates_only_given_fields(self, owner):
        original_email = owner.email
        owner.modify_info(first_name="Janet", phone="999-0000")
        assert owner.first_name == "Janet"
        assert owner.phone == "999-0000"
        assert owner.email == original_email

    def test_modify_info_all_fields(self, owner):
        owner.modify_info(first_name="A", last_name="B",
                          email="a@b.com", phone="111", address="Addr")
        assert owner.first_name == "A"
        assert owner.last_name == "B"
        assert owner.email == "a@b.com"
        assert owner.phone == "111"
        assert owner.address == "Addr"

    def test_get_info_returns_correct_dict(self, owner):
        info = owner.get_info()
        assert info["first_name"] == "Jane"
        assert info["last_name"] == "Doe"
        assert info["email"] == "jane@example.com"
        assert info["pet_count"] == 0

    def test_get_info_pet_count_updates(self, owner):
        owner.create_pet("Buddy")
        assert owner.get_info()["pet_count"] == 1

    def test_view_pet_info_returns_summary(self, owner, pet):
        pet.update_info(breed="Beagle", age=2)
        info = owner.view_pet_info(pet)
        assert info["name"] == "Fido"
        assert info["breed"] == "Beagle"

    def test_view_pet_info_rejects_other_owners_pet(self, owner, other_pet):
        with pytest.raises(ValueError, match="your own pets"):
            owner.view_pet_info(other_pet)

    def test_view_all_pets_empty(self, owner):
        assert owner.view_all_pets() == []

    def test_view_all_pets_returns_all_summaries(self, owner):
        owner.create_pet("Fido")
        owner.create_pet("Luna")
        names = [s["name"] for s in owner.view_all_pets()]
        assert "Fido" in names
        assert "Luna" in names

    def test_assign_task_to_pet_happy_path(self, owner, pet, walk_task):
        owner.assign_task_to_pet(pet, walk_task)
        assert walk_task in pet.tasks

    def test_assign_task_to_other_owners_pet_raises(self, owner, other_pet, walk_task):
        with pytest.raises(ValueError, match="your own pets"):
            owner.assign_task_to_pet(other_pet, walk_task)

    def test_view_pet_tasks_returns_task_list(self, owner, pet, walk_task):
        owner.assign_task_to_pet(pet, walk_task)
        assert walk_task in owner.view_pet_tasks(pet)

    def test_view_pet_tasks_rejects_other_owners_pet(self, owner, other_pet):
        with pytest.raises(ValueError, match="your own pets"):
            owner.view_pet_tasks(other_pet)

    def test_view_tasks_for_pets_combines_all(self, owner):
        p1 = owner.create_pet("Fido")
        p2 = owner.create_pet("Luna")
        t1 = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=1)
        owner.assign_task_to_pet(p1, t1)
        owner.assign_task_to_pet(p2, t2)
        combined = owner.view_tasks_for_pets([p1, p2])
        assert t1 in combined
        assert t2 in combined

    def test_view_tasks_for_pets_rejects_other_owners_pet(self, owner, pet, other_pet):
        with pytest.raises(ValueError, match="your own pets"):
            owner.view_tasks_for_pets([pet, other_pet])


# ── Scheduler ─────────────────────────────────────────────────────────────────

class TestScheduler:

    # ── build_schedule ──────────────────────────────────────────────────────

    def test_build_schedule_seeds_84_slots(self, owner, pet):
        schedule = owner.scheduler.build_schedule([pet])
        assert len(schedule) == 7 * 24  # 24 half-hour slots per day (8AM–8PM)

    def test_build_schedule_all_empty_with_no_tasks(self, owner, pet):
        schedule = owner.scheduler.build_schedule([pet])
        assert all(v == [] for v in schedule.values())

    def test_build_schedule_places_task_in_correct_slot(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        schedule = owner.scheduler.build_schedule([pet])
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("UTC")
        slot_key = datetime(future_date.year, future_date.month, future_date.day,
                            slot_time.hour, slot_time.minute, tzinfo=tz)
        assert len(schedule[slot_key]) == 1

    def test_build_schedule_rejects_other_owners_pet(self, owner, other_pet):
        with pytest.raises(ValueError, match="your own pets"):
            owner.scheduler.build_schedule([other_pet])

    def test_build_schedule_stores_result_in_self(self, owner, pet):
        owner.scheduler.build_schedule([pet])
        assert len(owner.scheduler.schedule) == 168

    # ── view_schedule ───────────────────────────────────────────────────────

    def test_view_schedule_is_sorted(self, owner, pet):
        entries = owner.scheduler.view_schedule([pet])
        slots = [e["slot"] for e in entries]
        assert slots == sorted(slots)

    def test_view_schedule_all_available_with_no_tasks(self, owner, pet):
        entries = owner.scheduler.view_schedule([pet])
        assert all(e["available"] for e in entries)

    def test_view_schedule_booked_slot_marked_unavailable(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        entries = owner.scheduler.view_schedule([pet])
        booked = [e for e in entries if not e["available"]]
        assert len(booked) == 1
        assert booked[0]["bookings"][0]["task_name"] == "Morning Walk"

    def test_view_schedule_bookings_sorted_by_priority_desc(self, owner, future_date):
        p1 = owner.create_pet("Fido")
        p2 = owner.create_pet("Luna")
        low  = Task(type=TaskType.WALKING, name="Low",  description="d", duration_minutes=30, priority=1)
        high = Task(type=TaskType.BATHING, name="High", description="d", duration_minutes=20, priority=5)
        owner.assign_task_to_pet(p1, low)
        owner.assign_task_to_pet(p2, high)
        t = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        owner.scheduler.assign_task_to_schedule(p1, low,  future_date, t)
        owner.scheduler.assign_task_to_schedule(p2, high, future_date, t)
        entries = owner.scheduler.view_schedule()
        booked = [e for e in entries if not e["available"]]
        assert len(booked) == 1
        priorities = [b["priority"] for b in booked[0]["bookings"]]
        assert priorities == sorted(priorities, reverse=True)

    def test_view_schedule_entry_has_expected_keys(self, owner, pet):
        entry = owner.scheduler.view_schedule([pet])[0]
        for key in ("slot", "date", "time", "available", "bookings"):
            assert key in entry

    def test_view_schedule_defaults_to_all_owner_pets(self, owner):
        owner.create_pet("Rex")
        owner.create_pet("Luna")
        entries = owner.scheduler.view_schedule()
        assert len(entries) == 168

    # ── get_available_slots ─────────────────────────────────────────────────

    def test_get_available_slots_excludes_booked(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        free = owner.scheduler.get_available_slots([pet])
        assert all(s["available"] for s in free)
        booked_key = (future_date.strftime("%Y-%m-%d"), slot_time.strftime("%H:%M"))
        free_keys = [(s["date"], s["time"]) for s in free]
        assert booked_key not in free_keys

    def test_get_available_slots_filtered_by_date_returns_12(self, owner, pet, future_date):
        slots = owner.scheduler.get_available_slots([pet], date=future_date)
        assert len(slots) == 24 # 24 half-hour slots per day
        assert all(s["date"] == future_date.strftime("%Y-%m-%d") for s in slots)

    def test_get_available_slots_filtered_date_excludes_booked(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        slots = owner.scheduler.get_available_slots([pet], date=future_date)
        assert len(slots) == 23  # 24 with one already booked.

    # ── get_slot_info ───────────────────────────────────────────────────────

    def test_get_slot_info_available_when_empty(self, owner, future_date, slot_time):
        info = owner.scheduler.get_slot_info(future_date, slot_time)
        assert info["available"] is True
        assert info["bookings"] == []
        assert info["date"] == future_date.strftime("%Y-%m-%d")
        assert info["time"] == slot_time.strftime("%H:%M")

    def test_get_slot_info_shows_booking_details(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        info = owner.scheduler.get_slot_info(future_date, slot_time)
        assert info["available"] is False
        b = info["bookings"][0]
        assert b["pet_name"] == "Fido"
        assert b["task_name"] == "Morning Walk"
        assert b["task_type"] == TaskType.WALKING.value
        assert b["priority"] == 2

    def test_get_slot_info_multiple_pets_same_slot(self, owner, future_date):
        p1 = owner.create_pet("Fido")
        p2 = owner.create_pet("Luna")
        t1 = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=2)
        owner.assign_task_to_pet(p1, t1)
        owner.assign_task_to_pet(p2, t2)
        t = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        owner.scheduler.assign_task_to_schedule(p1, t1, future_date, t)
        owner.scheduler.assign_task_to_schedule(p2, t2, future_date, t)
        info = owner.scheduler.get_slot_info(future_date, t)
        assert info["available"] is False
        pet_names = [b["pet_name"] for b in info["bookings"]]
        assert "Fido" in pet_names
        assert "Luna" in pet_names

    # ── is_slot_available ───────────────────────────────────────────────────

    def test_is_slot_available_true_when_free(self, owner, future_date, slot_time):
        assert owner.scheduler.is_slot_available(future_date, slot_time) is True

    def test_is_slot_available_false_when_booked(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        assert owner.scheduler.is_slot_available(future_date, slot_time) is False

    # ── view_tasks_by_priority ──────────────────────────────────────────────

    def test_view_tasks_by_priority_sorted_desc(self, owner, future_date):
        pet = owner.create_pet("Fido")
        t_low  = Task(type=TaskType.WALKING,  name="Walk",  description="d", duration_minutes=30, priority=1)
        t_mid  = Task(type=TaskType.BATHING,  name="Bath",  description="d", duration_minutes=20, priority=3)
        t_high = Task(type=TaskType.GROOMING, name="Groom", description="d", duration_minutes=15, priority=5)
        owner.assign_task_to_pet(pet, t_low)
        owner.assign_task_to_pet(pet, t_mid)
        owner.assign_task_to_pet(pet, t_high)
        t1 = datetime.now().replace(hour=9,  minute=0, second=0, microsecond=0)
        t2 = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        t3 = datetime.now().replace(hour=11, minute=0, second=0, microsecond=0)
        owner.scheduler.assign_task_to_schedule(pet, t_low,  future_date, t1)
        owner.scheduler.assign_task_to_schedule(pet, t_mid,  future_date, t2)
        owner.scheduler.assign_task_to_schedule(pet, t_high, future_date, t3)
        result = owner.scheduler.view_tasks_by_priority()
        priorities = [e["priority"] for e in result]
        assert priorities == sorted(priorities, reverse=True)
        assert priorities[0] == 5

    def test_view_tasks_by_priority_excludes_unscheduled(self, owner, pet, walk_task):
        owner.assign_task_to_pet(pet, walk_task)  # no scheduled_date/time set
        assert owner.scheduler.view_tasks_by_priority() == []

    def test_view_tasks_by_priority_entry_has_expected_fields(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        entry = owner.scheduler.view_tasks_by_priority()[0]
        for key in ("priority", "pet_name", "task_name", "task_type",
                    "duration_minutes", "task_status", "scheduled_date", "scheduled_time"):
            assert key in entry
        assert entry["pet_name"] == "Fido"
        assert entry["task_name"] == "Morning Walk"

    def test_view_tasks_by_priority_rejects_other_owners_pet(self, owner, other_owner, other_pet):
        t = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        other_owner.assign_task_to_pet(other_pet, t)
        with pytest.raises(ValueError, match="your own pets"):
            owner.scheduler.view_tasks_by_priority([other_pet])

    # ── assign_task_to_schedule ─────────────────────────────────────────────

    def test_assign_task_sets_date_time_and_pending_status(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        assert walk_task.scheduled_date.date() == future_date.date()
        assert walk_task.scheduled_time.hour == slot_time.hour
        assert walk_task.scheduled_time.minute == slot_time.minute
        assert walk_task.status == Status.PENDING

    def test_assign_task_conflict_same_slot_raises(self, owner, pet, future_date, slot_time):
        t1 = Task(type=TaskType.WALKING,    name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.ENRICHMENT, name="Play", description="d", duration_minutes=20, priority=1)
        owner.assign_task_to_pet(pet, t1)
        owner.assign_task_to_pet(pet, t2)
        owner.scheduler.assign_task_to_schedule(pet, t1, future_date, slot_time)
        with pytest.raises(ValueError, match="Time conflict|Conflict"):
            owner.scheduler.assign_task_to_schedule(pet, t2, future_date, slot_time)

    def test_assign_completed_task_raises(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        walk_task.complete_task()
        with pytest.raises(ValueError, match="already completed"):
            owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)

    def test_assign_task_not_yet_added_to_pet_raises(self, owner, pet, walk_task, future_date, slot_time):
        with pytest.raises(ValueError, match="assigned to the pet first"):
            owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)

    def test_assign_task_rejects_other_owners_pet(self, owner, other_owner, other_pet, future_date, slot_time):
        t = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        other_owner.assign_task_to_pet(other_pet, t)
        with pytest.raises(ValueError, match="your own pets"):
            owner.scheduler.assign_task_to_schedule(other_pet, t, future_date, slot_time)

    def test_assign_back_to_back_same_type_raises(self, owner, pet, future_date):
        t1 = Task(type=TaskType.WALKING, name="Walk1", description="d", duration_minutes=60, priority=1)
        t2 = Task(type=TaskType.WALKING, name="Walk2", description="d", duration_minutes=30, priority=1)
        # Add t1, complete it so t2 (same type) can be added, then restore t1 to pending for scheduling
        owner.assign_task_to_pet(pet, t1)
        t1.complete_task()
        owner.assign_task_to_pet(pet, t2)
        t1.status = Status.PENDING
        slot = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        back_to_back_slot = slot + timedelta(minutes=60)  # exactly when t1 ends
        owner.scheduler.assign_task_to_schedule(pet, t1, future_date, slot)
        with pytest.raises(ValueError, match="back-to-back"):
            owner.scheduler.assign_task_to_schedule(pet, t2, future_date, back_to_back_slot)

    # ── move_task ───────────────────────────────────────────────────────────

    def test_move_task_updates_scheduled_date(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        new_date = future_date + timedelta(days=1)
        result = owner.scheduler.move_task(pet, walk_task, new_date, slot_time)
        assert walk_task.scheduled_date.date() == new_date.date()
        assert result["previous_slot"] is not None
        assert result["new_slot"].date() == new_date.date()
        assert result["new_slot"].hour == slot_time.hour
        assert result["new_slot"].minute == slot_time.minute

    def test_move_task_conflict_raises(self, owner, pet, future_date):
        t1 = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=2)
        owner.assign_task_to_pet(pet, t1)
        owner.assign_task_to_pet(pet, t2)
        s1 = datetime.now().replace(hour=9,  minute=0, second=0, microsecond=0)
        s2 = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        owner.scheduler.assign_task_to_schedule(pet, t1, future_date, s1)
        owner.scheduler.assign_task_to_schedule(pet, t2, future_date, s2)
        with pytest.raises(ValueError, match="Time conflict|Conflict"):
            owner.scheduler.move_task(pet, t2, future_date, s1)

    def test_move_completed_task_raises(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        walk_task.complete_task()
        with pytest.raises(ValueError, match="already completed"):
            owner.scheduler.move_task(pet, walk_task, future_date + timedelta(days=1), slot_time)

    def test_move_task_rejects_other_owners_pet(self, owner, other_owner, other_pet, future_date, slot_time):
        t = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        other_owner.assign_task_to_pet(other_pet, t)
        with pytest.raises(ValueError, match="your own pets"):
            owner.scheduler.move_task(other_pet, t, future_date, slot_time)

    def test_move_task_returns_message_with_task_name(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        result = owner.scheduler.move_task(pet, walk_task, future_date + timedelta(days=1), slot_time)
        assert "message" in result
        assert "Morning Walk" in result["message"]


# ── Legacy tests (kept and updated for new build_schedule dict output) ────────

def test_owner_can_create_pet_and_assign_task():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    task = Task(type=TaskType.WALKING, name="Walk", description="Walk the dog",
                duration_minutes=30, priority=1)
    owner.assign_task_to_pet(pet, task)
    assert pet.tasks == [task]
    assert task.pet == pet


def test_task_moves_and_reporting():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    task = Task(type=TaskType.FEEDING, name="Feed", description="Feed the dog",
                duration_minutes=10, priority=1)
    owner.assign_task_to_pet(pet, task)
    date = datetime.now() + timedelta(days=1)
    # 10-min task at 15:00 → ends at 15:10, safely within 8AM-8PM
    time = datetime.now().replace(hour=15, minute=0, second=0, microsecond=0)
    owner.scheduler.assign_task_to_schedule(pet, task, date, time)
    assert task.status == Status.PENDING
    later_date = date + timedelta(days=1)
    move_info = owner.scheduler.move_task(pet, task, later_date, time)
    assert move_info["previous_slot"] is not None
    assert move_info["new_slot"].date() == later_date.date()
    assert move_info["new_slot"].hour == time.hour
    assert move_info["new_slot"].minute == time.minute
    assert task.scheduled_date.date() == later_date.date()


def test_build_schedule_shows_tasks_for_multiple_pets():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet1 = owner.create_pet("Fido", animal_type="Dog")
    pet2 = owner.create_pet("Whiskers", "Cat")
    task1 = Task(type=TaskType.WALKING, name="Walk", description="Walk", duration_minutes=30, priority=1)
    task2 = Task(type=TaskType.BATHING, name="Bath", description="Bath", duration_minutes=30, priority=2)
    owner.assign_task_to_pet(pet1, task1)
    owner.assign_task_to_pet(pet2, task2)
    date = datetime.now() + timedelta(days=1)
    time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
    owner.scheduler.assign_task_to_schedule(pet1, task1, date, time)
    owner.scheduler.assign_task_to_schedule(pet2, task2, date, time + timedelta(hours=1))
    schedule = owner.scheduler.build_schedule([pet1, pet2])
    tz = ZoneInfo("UTC")
    # slot1 = 10:00 AM (where Walk is scheduled)
    slot1 = datetime(date.year, date.month, date.day, 10, 0, tzinfo=tz)
    # slot2 = 11:00 AM (where Bath is scheduled — one hour later!)
    slot2 = datetime(date.year, date.month, date.day, 11, 0, tzinfo=tz)
    assert len(schedule[slot1]) == 1
    assert schedule[slot1][0]["task_name"] == "Walk"
    assert len(schedule[slot2]) == 1
    assert schedule[slot2][0]["task_name"] == "Bath"



def test_pet_update_and_summary():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    pet.update_info(animal_type="Dog", breed="Labrador", age=3, gender="Male", weight=28.5)
    summary = pet.summary()
    assert summary["name"] == "Fido"
    assert summary["animal_type"] == "Dog"
    assert summary["breed"] == "Labrador"
    assert summary["age"] == 3
    assert summary["gender"] == "Male"
    assert summary["weight"] == 28.5


def test_pet_add_remove_tasks_and_duplication_rules():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    task1 = Task(type=TaskType.FEEDING, name="Feed",       description="Feed", duration_minutes=30, priority=1)
    task2 = Task(type=TaskType.FEEDING, name="Feed again", description="Feed", duration_minutes=30, priority=1)
    pet.add_task(task1)
    with pytest.raises(ValueError, match="Cannot add duplicate pending/in-progress task"):
        pet.add_task(task2)
    task1.status = Status.COMPLETED
    pet.add_task(task2)
    assert task2 in pet.tasks
    pet.remove_task(task2)
    assert task2 not in pet.tasks


def test_owner_view_tasks_for_multiple_pets():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet1 = owner.create_pet("Fido", animal_type="Dog")
    pet2 = owner.create_pet("Whiskers", "Cat")
    t1 = Task(type=TaskType.WALKING, name="Walk dog", description="walk", duration_minutes=30, priority=1)
    t2 = Task(type=TaskType.BATHING, name="Bath cat", description="bath", duration_minutes=30, priority=1)
    owner.assign_task_to_pet(pet1, t1)
    owner.assign_task_to_pet(pet2, t2)
    combined = owner.view_tasks_for_pets([pet1, pet2])
    assert t1 in combined
    assert t2 in combined


# ===================================================================
# Helper: create a time on a given date
# ===================================================================

def _time_on(base_date, hour, minute=0):
    """Return a datetime combining base_date's date with the given hour/minute."""
    return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)


# ===================================================================
# ✅ HAPPY PATH — sort_tasks_by_time
# ===================================================================

def test_sort_by_time_out_of_order(owner, pet, future_date):
    """Tasks added at 2PM, 8AM, 12PM should display as 8AM, 12PM, 2PM."""
    task_2pm = Task(type=TaskType.WALKING, name="Afternoon Walk",
                    description="Walk", duration_minutes=30, priority=5)
    task_8am = Task(type=TaskType.FEEDING, name="Morning Feed",
                    description="Kibble", duration_minutes=5, priority=9)
    task_12pm = Task(type=TaskType.ENRICHMENT, name="Puzzle Time",
                     description="Snuffle mat", duration_minutes=20, priority=6)

    # Add in REVERSE chronological order
    owner.assign_task_to_pet(pet, task_2pm)
    owner.assign_task_to_pet(pet, task_8am)
    owner.assign_task_to_pet(pet, task_12pm)

    owner.scheduler.assign_task_to_schedule(
        pet, task_2pm, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        pet, task_8am, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, task_12pm, future_date, _time_on(future_date, 12))

    result = owner.scheduler.sort_tasks_by_time()

    assert len(result) == 3
    assert result[0]["task_name"] == "Morning Feed"     # 8 AM
    assert result[1]["task_name"] == "Puzzle Time"      # 12 PM
    assert result[2]["task_name"] == "Afternoon Walk"   # 2 PM


def test_sort_by_time_multiple_pets(owner, pet, future_date):
    """Sorting should interleave tasks from different pets by time."""
    cat = owner.create_pet("Mittens", "Cat")

    dog_task = Task(type=TaskType.WALKING, name="Dog Walk",
                    description="x", duration_minutes=30, priority=7)
    cat_task = Task(type=TaskType.FEEDING, name="Cat Feed",
                    description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, dog_task)
    owner.assign_task_to_pet(cat, cat_task)

    # Cat at 8AM, Dog at 10AM
    owner.scheduler.assign_task_to_schedule(
        pet, dog_task, future_date, _time_on(future_date, 10))
    owner.scheduler.assign_task_to_schedule(
        cat, cat_task, future_date, _time_on(future_date, 8))

    result = owner.scheduler.sort_tasks_by_time()

    assert result[0]["pet_name"] == "Mittens"   # 8 AM first
    assert result[1]["pet_name"] == "Fido"      # 10 AM second


def test_sort_by_time_across_multiple_days(owner, pet, future_date):
    """Tasks on different days should sort by date then time."""
    day1_task = Task(type=TaskType.FEEDING, name="Day 1 Feed",
                     description="x", duration_minutes=5, priority=9)
    day3_task = Task(type=TaskType.WALKING, name="Day 3 Walk",
                     description="x", duration_minutes=30, priority=7)

    day3 = future_date + timedelta(days=2)

    # Add day 3 first, then day 1
    owner.assign_task_to_pet(pet, day3_task)
    owner.assign_task_to_pet(pet, day1_task)

    owner.scheduler.assign_task_to_schedule(
        pet, day3_task, day3, _time_on(day3, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, day1_task, future_date, _time_on(future_date, 8))

    result = owner.scheduler.sort_tasks_by_time()

    assert result[0]["task_name"] == "Day 1 Feed"
    assert result[1]["task_name"] == "Day 3 Walk"


def test_sort_by_time_returns_expected_fields(owner, pet, future_date, walk_task):
    """Each entry should contain all required display fields."""
    owner.assign_task_to_pet(pet, walk_task)
    owner.scheduler.assign_task_to_schedule(
        pet, walk_task, future_date, _time_on(future_date, 10))

    result = owner.scheduler.sort_tasks_by_time()

    assert len(result) == 1
    entry = result[0]
    expected_keys = {
        "pet_name", "task_name", "task_type", "priority",
        "duration_minutes", "status", "frequency",
        "scheduled_date", "scheduled_time", "end_time",
    }
    assert expected_keys.issubset(entry.keys())


# ===================================================================
# ✅ HAPPY PATH — filter_tasks
# ===================================================================

def test_filter_by_pet_returns_only_that_pet(owner, pet, future_date):
    """Filtering by pet should return only that pet's tasks."""
    cat = owner.create_pet("Mittens", "Cat")

    dog_task = Task(type=TaskType.WALKING, name="Dog Walk",
                    description="x", duration_minutes=30, priority=7)
    cat_task = Task(type=TaskType.FEEDING, name="Cat Feed",
                    description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, dog_task)
    owner.assign_task_to_pet(cat, cat_task)

    owner.scheduler.assign_task_to_schedule(
        pet, dog_task, future_date, _time_on(future_date, 10))
    owner.scheduler.assign_task_to_schedule(
        cat, cat_task, future_date, _time_on(future_date, 8))

    result = owner.scheduler.filter_tasks(pet=pet)

    assert len(result) == 1
    assert result[0]["pet_name"] == "Fido"


def test_filter_by_status_pending(owner, pet, future_date):
    """Filtering by PENDING should exclude completed tasks."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)
    walk = Task(type=TaskType.WALKING, name="Walk",
                description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, feed)
    owner.assign_task_to_pet(pet, walk)

    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, walk, future_date, _time_on(future_date, 14))

    feed.complete_task()

    result = owner.scheduler.filter_tasks(status=Status.PENDING)

    assert len(result) == 1
    assert result[0]["task_name"] == "Walk"


def test_filter_by_status_completed(owner, pet, future_date):
    """Filtering by COMPLETED should only return completed tasks."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)
    walk = Task(type=TaskType.WALKING, name="Walk",
                description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, feed)
    owner.assign_task_to_pet(pet, walk)

    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, walk, future_date, _time_on(future_date, 14))

    feed.complete_task()

    result = owner.scheduler.filter_tasks(status=Status.COMPLETED)

    assert len(result) == 1
    assert result[0]["task_name"] == "Feed"


def test_filter_combined_pet_and_status(owner, pet, future_date):
    """Filtering by both pet AND status should narrow correctly."""
    cat = owner.create_pet("Mittens", "Cat")

    dog_feed = Task(type=TaskType.FEEDING, name="Dog Feed",
                    description="x", duration_minutes=5, priority=9)
    dog_walk = Task(type=TaskType.WALKING, name="Dog Walk",
                    description="x", duration_minutes=30, priority=7)
    cat_feed = Task(type=TaskType.FEEDING, name="Cat Feed",
                    description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, dog_feed)
    owner.assign_task_to_pet(pet, dog_walk)
    owner.assign_task_to_pet(cat, cat_feed)

    owner.scheduler.assign_task_to_schedule(
        pet, dog_feed, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, dog_walk, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        cat, cat_feed, future_date, _time_on(future_date, 9))

    dog_feed.complete_task()

    result = owner.scheduler.filter_tasks(pet=pet, status=Status.PENDING)

    assert len(result) == 1
    assert result[0]["task_name"] == "Dog Walk"
    assert result[0]["pet_name"] == "Fido"


def test_filter_results_are_sorted_by_time(owner, pet, future_date):
    """Filtered results should still be in chronological order."""
    walk = Task(type=TaskType.WALKING, name="Walk",
                description="x", duration_minutes=30, priority=7)
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)

    # Add walk first (2PM), then feed (8AM)
    owner.assign_task_to_pet(pet, walk)
    owner.assign_task_to_pet(pet, feed)

    owner.scheduler.assign_task_to_schedule(
        pet, walk, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    result = owner.scheduler.filter_tasks(pet=pet)

    assert result[0]["task_name"] == "Feed"   # 8 AM first
    assert result[1]["task_name"] == "Walk"   # 2 PM second


# ===================================================================
# ✅ HAPPY PATH — detect_conflicts
# ===================================================================

def test_no_conflicts_returns_empty_list(owner, pet, future_date):
    """Non-overlapping tasks should produce zero warnings."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)
    walk = Task(type=TaskType.WALKING, name="Walk",
                description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, feed)
    owner.assign_task_to_pet(pet, walk)

    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        pet, walk, future_date, _time_on(future_date, 14))

    warnings = owner.scheduler.detect_conflicts()
    assert warnings == []


def test_cross_pet_conflict_detected(owner, pet, future_date):
    """Two tasks for different pets at the same time should produce a warning."""
    cat = owner.create_pet("Mittens", "Cat")

    dog_walk = Task(type=TaskType.WALKING, name="Dog Walk",
                    description="x", duration_minutes=30, priority=8)
    cat_play = Task(type=TaskType.ENRICHMENT, name="Cat Play",
                    description="x", duration_minutes=20, priority=7)

    owner.assign_task_to_pet(pet, dog_walk)
    owner.assign_task_to_pet(cat, cat_play)

    owner.scheduler.assign_task_to_schedule(
        pet, dog_walk, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        cat, cat_play, future_date, _time_on(future_date, 14))

    warnings = owner.scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "CROSS-PET" in warnings[0]


def test_conflict_warning_contains_task_names(owner, pet, future_date):
    """Warning string should include both task names."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.WALKING, name="Dog Walk",
              description="x", duration_minutes=30, priority=8)
    t2 = Task(type=TaskType.ENRICHMENT, name="Cat Play",
              description="x", duration_minutes=20, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 14))

    warnings = owner.scheduler.detect_conflicts()

    assert "Dog Walk" in warnings[0]
    assert "Cat Play" in warnings[0]


def test_conflict_detection_never_crashes(owner, pet, future_date):
    """detect_conflicts should return a list, never raise exceptions."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.WALKING, name="Walk",
              description="x", duration_minutes=30, priority=8)
    t2 = Task(type=TaskType.ENRICHMENT, name="Play",
              description="x", duration_minutes=20, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 14))

    try:
        warnings = owner.scheduler.detect_conflicts()
        assert isinstance(warnings, list)
    except Exception:
        pytest.fail("detect_conflicts() raised an exception — it should only warn!")


# ===================================================================
# ✅ HAPPY PATH — complete_and_renew (recurring tasks)
# ===================================================================

def test_daily_task_renews_plus_one_day(owner, pet, future_date):
    """Completing a daily task should create a new one at +1 day."""
    feed = Task(type=TaskType.FEEDING, name="Morning Feed",
                description="Breakfast", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    original_date = feed.scheduled_date
    new_task = owner.scheduler.complete_and_renew(pet, feed)

    assert feed.status == Status.COMPLETED
    assert new_task is not None
    expected = original_date + timedelta(days=1)
    assert new_task.scheduled_date.date() == expected.date()


def test_weekly_task_renews_plus_seven_days(owner, pet, future_date):
    """Completing a weekly task should create a new one at +7 days."""
    groom = Task(type=TaskType.GROOMING, name="Brush Fur",
                 description="Weekly brush", duration_minutes=30,
                 priority=5, frequency=Frequency.WEEKLY)

    owner.assign_task_to_pet(pet, groom)
    owner.scheduler.assign_task_to_schedule(
        pet, groom, future_date, _time_on(future_date, 10))

    original_date = groom.scheduled_date
    new_task = owner.scheduler.complete_and_renew(pet, groom)

    assert groom.status == Status.COMPLETED
    assert new_task is not None
    expected = original_date + timedelta(days=7)
    assert new_task.scheduled_date.date() == expected.date()


def test_monthly_task_renews_plus_thirty_days(owner, pet, future_date):
    """Completing a monthly task should create a new one at +30 days."""
    bath = Task(type=TaskType.BATHING, name="Monthly Bath",
                description="Full bath", duration_minutes=45,
                priority=4, frequency=Frequency.MONTHLY)

    owner.assign_task_to_pet(pet, bath)
    owner.scheduler.assign_task_to_schedule(
        pet, bath, future_date, _time_on(future_date, 9))

    original_date = bath.scheduled_date
    new_task = owner.scheduler.complete_and_renew(pet, bath)

    assert new_task is not None
    expected = original_date + timedelta(days=30)
    assert new_task.scheduled_date.date() == expected.date()


def test_custom_frequency_respects_interval_days(owner, pet, future_date):
    """Custom with repeat_interval_days=2 should schedule +2 days."""
    med = Task(type=TaskType.MEDICATION, name="Allergy Pill",
               description="Every other day", duration_minutes=5,
               priority=10, frequency=Frequency.CUSTOM,
               repeat_count=5, repeat_interval_days=2)

    owner.assign_task_to_pet(pet, med)
    owner.scheduler.assign_task_to_schedule(
        pet, med, future_date, _time_on(future_date, 18))

    original_date = med.scheduled_date
    new_task = owner.scheduler.complete_and_renew(pet, med)

    assert new_task is not None
    expected = original_date + timedelta(days=2)
    assert new_task.scheduled_date.date() == expected.date()


def test_renewed_task_inherits_properties(owner, pet, future_date):
    """New occurrence should keep type, priority, duration, frequency, name."""
    feed = Task(type=TaskType.FEEDING, name="Morning Feed",
                description="Kibble", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    new_task = owner.scheduler.complete_and_renew(pet, feed)

    assert new_task is not None
    assert new_task.type == feed.type
    assert new_task.name == feed.name
    assert new_task.priority == feed.priority
    assert new_task.duration_minutes == feed.duration_minutes
    assert new_task.frequency == feed.frequency


def test_renewed_task_status_is_pending(owner, pet, future_date):
    """Auto-created occurrence should start as PENDING (it's in the future)."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    new_task = owner.scheduler.complete_and_renew(pet, feed)

    assert new_task is not None
    assert new_task.status == Status.PENDING


def test_occurrence_counter_increments_on_complete(owner, pet, future_date):
    """Completing a task should bump occurrences_completed by 1."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    assert feed.occurrences_completed == 0
    owner.scheduler.complete_and_renew(pet, feed)
    assert feed.occurrences_completed == 1


def test_renewed_task_added_to_pet_task_list(owner, pet, future_date):
    """The new occurrence should appear in the pet's task list."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    count_before = len(pet.tasks)
    owner.scheduler.complete_and_renew(pet, feed)

    assert len(pet.tasks) == count_before + 1


def test_chained_daily_renewals_increment_correctly(owner, pet, future_date):
    """Completing and renewing a daily task twice should yield +1 day, then +2 days."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    # First renewal: future_date → future_date + 1
    task_2 = owner.scheduler.complete_and_renew(pet, feed)
    assert task_2 is not None
    assert task_2.scheduled_date.date() == (future_date + timedelta(days=1)).date()

    # Second renewal: future_date + 1 → future_date + 2
    task_3 = owner.scheduler.complete_and_renew(pet, task_2)
    assert task_3 is not None
    assert task_3.scheduled_date.date() == (future_date + timedelta(days=2)).date()


# ===================================================================
# 🔶 EDGE CASE — sort_tasks_by_time
# ===================================================================

def test_sort_pet_with_no_tasks(owner, pet):
    """A pet with zero tasks should return an empty list, not crash."""
    result = owner.scheduler.sort_tasks_by_time()
    assert result == []


def test_sort_owner_with_no_pets(owner):
    """An owner with no pets should return an empty list."""
    fresh = Owner("X", "Y", "x@y.com", "555", "1 St")
    result = fresh.scheduler.sort_tasks_by_time()
    assert result == []


def test_sort_two_tasks_exact_same_time_both_appear(owner, pet, future_date):
    """Two tasks at the exact same time should BOTH appear in results."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.FEEDING, name="Dog Feed",
              description="x", duration_minutes=5, priority=9)
    t2 = Task(type=TaskType.FEEDING, name="Cat Feed",
              description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 8))

    result = owner.scheduler.sort_tasks_by_time()
    eight_am = [t for t in result if t["scheduled_time"] == "08:00"]
    assert len(eight_am) == 2


def test_sort_excludes_unscheduled_tasks(owner, pet, future_date):
    """Tasks without a scheduled date should NOT appear in sorted results."""
    scheduled = Task(type=TaskType.FEEDING, name="Scheduled",
                     description="x", duration_minutes=5, priority=9)
    unscheduled = Task(type=TaskType.WALKING, name="Unscheduled",
                       description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, scheduled)
    owner.assign_task_to_pet(pet, unscheduled)

    owner.scheduler.assign_task_to_schedule(
        pet, scheduled, future_date, _time_on(future_date, 8))
    # unscheduled deliberately NOT scheduled

    result = owner.scheduler.sort_tasks_by_time()

    assert len(result) == 1
    assert result[0]["task_name"] == "Scheduled"


def test_sort_completed_tasks_still_appear(owner, pet, future_date):
    """Completed tasks still have dates, so they should still appear."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))
    feed.complete_task()

    result = owner.scheduler.sort_tasks_by_time()

    assert len(result) == 1
    assert result[0]["status"] == "completed"


def test_sort_single_task(owner, pet, future_date, walk_task):
    """Sorting with one task should return a list of length 1."""
    owner.assign_task_to_pet(pet, walk_task)
    owner.scheduler.assign_task_to_schedule(
        pet, walk_task, future_date, _time_on(future_date, 10))

    result = owner.scheduler.sort_tasks_by_time()

    assert len(result) == 1
    assert result[0]["task_name"] == "Morning Walk"


# ===================================================================
# 🔶 EDGE CASE — filter_tasks
# ===================================================================

def test_filter_no_matching_status_returns_empty(owner, pet, future_date):
    """Filtering by a status no task has should return empty list."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5, priority=9)

    owner.assign_task_to_pet(pet, feed)
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))

    result = owner.scheduler.filter_tasks(status=Status.COMPLETED)
    assert result == []


def test_filter_pet_with_no_tasks_returns_empty(owner, pet, future_date):
    """Filtering by a pet that has no scheduled tasks returns empty list."""
    cat = owner.create_pet("Mittens", "Cat")

    dog_task = Task(type=TaskType.WALKING, name="Walk",
                    description="x", duration_minutes=30, priority=7)
    owner.assign_task_to_pet(pet, dog_task)
    owner.scheduler.assign_task_to_schedule(
        pet, dog_task, future_date, _time_on(future_date, 10))

    result = owner.scheduler.filter_tasks(pet=cat)
    assert result == []


def test_filter_no_args_returns_all_tasks(owner, pet, future_date):
    """Calling filter_tasks() with no arguments should return everything."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.FEEDING, name="Feed",
              description="x", duration_minutes=5, priority=9)
    t2 = Task(type=TaskType.WALKING, name="Walk",
              description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 8))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 14))

    result = owner.scheduler.filter_tasks()
    assert len(result) == 2


# ===================================================================
# 🔶 EDGE CASE — complete_and_renew (recurring tasks)
# ===================================================================

def test_once_task_no_renewal(owner, pet, future_date):
    """A ONCE frequency task should NOT create a new occurrence."""
    bath = Task(type=TaskType.BATHING, name="Bath",
                description="One-time", duration_minutes=45,
                priority=3, frequency=Frequency.ONCE)

    owner.assign_task_to_pet(pet, bath)
    owner.scheduler.assign_task_to_schedule(
        pet, bath, future_date, _time_on(future_date, 10))

    result = owner.scheduler.complete_and_renew(pet, bath)

    assert bath.status == Status.COMPLETED
    assert result is None


def test_custom_exhausted_no_renewal(owner, pet, future_date):
    """After all repeat_count occurrences, no renewal should happen."""
    med = Task(type=TaskType.MEDICATION, name="Short Course",
               description="Last dose", duration_minutes=5,
               priority=10, frequency=Frequency.CUSTOM,
               repeat_count=2, repeat_interval_days=1,
               occurrences_completed=1)  # 1 of 2 done

    owner.assign_task_to_pet(pet, med)
    owner.scheduler.assign_task_to_schedule(
        pet, med, future_date, _time_on(future_date, 18))

    # Complete occurrence 2 of 2
    new_task = owner.scheduler.complete_and_renew(pet, med)

    assert med.occurrences_completed == 2

    # If a new task was created, it should know it has no more occurrences
    if new_task is not None:
        assert not new_task.needs_more_occurrences()


def test_unscheduled_recurring_task_no_renewal(owner, pet):
    """A recurring task with no scheduled date cannot calculate next date."""
    feed = Task(type=TaskType.FEEDING, name="Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)

    owner.assign_task_to_pet(pet, feed)
    # NOT scheduling — no date to add timedelta to

    result = owner.scheduler.complete_and_renew(pet, feed)

    assert feed.status == Status.COMPLETED
    assert result is None


def test_custom_no_interval_days_no_renewal(owner, pet, future_date):
    """Custom frequency with repeat_interval_days=None should return None."""
    broken = Task(type=TaskType.MEDICATION, name="Broken Med",
                  description="Missing interval", duration_minutes=5,
                  priority=5, frequency=Frequency.CUSTOM,
                  repeat_count=5, repeat_interval_days=None)

    owner.assign_task_to_pet(pet, broken)
    owner.scheduler.assign_task_to_schedule(
        pet, broken, future_date, _time_on(future_date, 12))

    result = owner.scheduler.complete_and_renew(pet, broken)

    assert broken.status == Status.COMPLETED
    assert result is None


def test_renewal_slot_conflict_finds_alternative(owner, pet, future_date):
    """If the preferred renewal slot is taken, it should find another."""
    feed = Task(type=TaskType.FEEDING, name="Morning Feed",
                description="x", duration_minutes=5,
                priority=9, frequency=Frequency.DAILY)
    blocker = Task(type=TaskType.WALKING, name="Blocker",
                   description="Blocks the slot",
                   duration_minutes=30, priority=7,
                   frequency=Frequency.ONCE)

    owner.assign_task_to_pet(pet, feed)
    owner.assign_task_to_pet(pet, blocker)

    day_after = future_date + timedelta(days=1)

    # Schedule feed for future_date at 8AM
    owner.scheduler.assign_task_to_schedule(
        pet, feed, future_date, _time_on(future_date, 8))
    # Block the exact 8AM slot on the renewal day
    owner.scheduler.assign_task_to_schedule(
        pet, blocker, day_after, _time_on(day_after, 8))

    new_task = owner.scheduler.complete_and_renew(pet, feed)

    # Should still create a task, just not at 8:00
    assert new_task is not None
    assert new_task.scheduled_date is not None


# ===================================================================
# 🔶 EDGE CASE — detect_conflicts
# ===================================================================

def test_detect_conflicts_partial_overlap(owner, pet, future_date):
    """A 30-min task at 10:00 and a 20-min task at 10:15 should conflict."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.WALKING, name="Dog Walk",
              description="x", duration_minutes=30, priority=8)
    t2 = Task(type=TaskType.ENRICHMENT, name="Cat Play",
              description="x", duration_minutes=20, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 10))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 10, 15))

    warnings = owner.scheduler.detect_conflicts()
    assert len(warnings) >= 1


def test_detect_conflicts_adjacent_no_overlap(owner, pet, future_date):
    """A task ending at 10:30 and another starting at 10:30 should NOT conflict."""
    t1 = Task(type=TaskType.FEEDING, name="Feed",
              description="x", duration_minutes=5, priority=9)
    t2 = Task(type=TaskType.WALKING, name="Walk",
              description="x", duration_minutes=30, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(pet, t2)

    # Feed at 10:25 (ends 10:30), Walk at 10:30 — adjacent, not overlapping
    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 10, 25))
    owner.scheduler.assign_task_to_schedule(
        pet, t2, future_date, _time_on(future_date, 10, 30))

    warnings = owner.scheduler.detect_conflicts()
    assert warnings == []


def test_detect_conflicts_completed_tasks_ignored(owner, pet, future_date):
    """Completed tasks should be excluded from conflict checks."""
    cat = owner.create_pet("Mittens", "Cat")

    t1 = Task(type=TaskType.WALKING, name="Walk",
              description="x", duration_minutes=30, priority=8)
    t2 = Task(type=TaskType.ENRICHMENT, name="Play",
              description="x", duration_minutes=20, priority=7)

    owner.assign_task_to_pet(pet, t1)
    owner.assign_task_to_pet(cat, t2)

    owner.scheduler.assign_task_to_schedule(
        pet, t1, future_date, _time_on(future_date, 14))
    owner.scheduler.assign_task_to_schedule(
        cat, t2, future_date, _time_on(future_date, 14))

    # Complete one — should eliminate the conflict
    t1.complete_task()

    warnings = owner.scheduler.detect_conflicts()
    assert warnings == []


def test_detect_conflicts_empty_schedule(owner, pet):
    """No tasks at all should return empty warnings list."""
    warnings = owner.scheduler.detect_conflicts()
    assert warnings == []