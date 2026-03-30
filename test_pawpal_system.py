import pytest
from datetime import datetime, timedelta
from pawpal_system import Owner, Task, TaskType, Status


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
        assert len(schedule) == 7 * 12  # 7 days × 12 hourly slots (8 AM–7 PM)

    def test_build_schedule_all_empty_with_no_tasks(self, owner, pet):
        schedule = owner.scheduler.build_schedule([pet])
        assert all(v == [] for v in schedule.values())

    def test_build_schedule_places_task_in_correct_slot(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        schedule = owner.scheduler.build_schedule([pet])
        slot = datetime(future_date.year, future_date.month, future_date.day,
                        slot_time.hour, slot_time.minute, slot_time.second)
        assert any(b["task_name"] == "Morning Walk" for b in schedule[slot])

    def test_build_schedule_rejects_other_owners_pet(self, owner, other_pet):
        with pytest.raises(ValueError, match="your own pets"):
            owner.scheduler.build_schedule([other_pet])

    def test_build_schedule_stores_result_in_self(self, owner, pet):
        owner.scheduler.build_schedule([pet])
        assert len(owner.scheduler.schedule) == 84

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
        assert len(entries) == 84

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
        assert len(slots) == 12
        assert all(s["date"] == future_date.strftime("%Y-%m-%d") for s in slots)

    def test_get_available_slots_filtered_date_excludes_booked(self, owner, pet, walk_task, future_date, slot_time):
        owner.assign_task_to_pet(pet, walk_task)
        owner.scheduler.assign_task_to_schedule(pet, walk_task, future_date, slot_time)
        slots = owner.scheduler.get_available_slots([pet], date=future_date)
        assert len(slots) == 11  # one of the 12 slots is booked

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
        assert walk_task.scheduled_date == future_date
        assert walk_task.scheduled_time == slot_time
        assert walk_task.status == Status.PENDING

    def test_assign_task_conflict_same_slot_raises(self, owner, pet, future_date, slot_time):
        t1 = Task(type=TaskType.WALKING,    name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.ENRICHMENT, name="Play", description="d", duration_minutes=20, priority=1)
        owner.assign_task_to_pet(pet, t1)
        owner.assign_task_to_pet(pet, t2)
        owner.scheduler.assign_task_to_schedule(pet, t1, future_date, slot_time)
        with pytest.raises(ValueError, match="Conflict"):
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
        assert walk_task.scheduled_date == new_date
        assert result["previous_slot"] is not None
        assert result["new_slot"] == datetime(new_date.year, new_date.month, new_date.day,
                                              slot_time.hour, slot_time.minute, slot_time.second)

    def test_move_task_conflict_raises(self, owner, pet, future_date):
        t1 = Task(type=TaskType.WALKING, name="Walk", description="d", duration_minutes=30, priority=1)
        t2 = Task(type=TaskType.BATHING, name="Bath", description="d", duration_minutes=20, priority=2)
        owner.assign_task_to_pet(pet, t1)
        owner.assign_task_to_pet(pet, t2)
        s1 = datetime.now().replace(hour=9,  minute=0, second=0, microsecond=0)
        s2 = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        owner.scheduler.assign_task_to_schedule(pet, t1, future_date, s1)
        owner.scheduler.assign_task_to_schedule(pet, t2, future_date, s2)
        with pytest.raises(ValueError, match="Conflict"):
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


def test_schedule_conflict_is_raised():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    task1 = Task(type=TaskType.WALKING,    name="Walk", description="Walk", duration_minutes=30, priority=1)
    task2 = Task(type=TaskType.ENRICHMENT, name="Play", description="Play", duration_minutes=30, priority=1)
    owner.assign_task_to_pet(pet, task1)
    owner.assign_task_to_pet(pet, task2)
    date = datetime.now() + timedelta(days=3)
    time = datetime.now().replace(hour=18, minute=0, second=0, microsecond=0)
    owner.scheduler.assign_task_to_schedule(pet, task1, date, time)
    with pytest.raises(ValueError, match="Conflict"):
        owner.scheduler.assign_task_to_schedule(pet, task2, date, time)


def test_task_moves_and_reporting():
    owner = Owner("Jane", "Doe", "jane@example.com", "123", "addr")
    pet = owner.create_pet("Fido", animal_type="Dog")
    task = Task(type=TaskType.FEEDING, name="Feed", description="Feed the dog",
                duration_minutes=10, priority=1)
    owner.assign_task_to_pet(pet, task)
    date = datetime.now() + timedelta(days=1)
    time = datetime.now().replace(hour=20, minute=0, second=0, microsecond=0)
    owner.scheduler.assign_task_to_schedule(pet, task, date, time)
    assert task.status == Status.PENDING
    later_date = date + timedelta(days=1)
    move_info = owner.scheduler.move_task(pet, task, later_date, time)
    assert move_info["previous_slot"] is not None
    assert move_info["new_slot"] == datetime(later_date.year, later_date.month, later_date.day,
                                             time.hour, time.minute, time.second)
    assert task.scheduled_date == later_date


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
    slot1 = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
    slot2 = datetime(date.year, date.month, date.day, time.hour + 1, time.minute, time.second)
    # build_schedule now returns booking dicts, not Task objects
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
