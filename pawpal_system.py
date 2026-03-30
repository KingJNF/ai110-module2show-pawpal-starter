from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TaskType(Enum):
    FEEDING = "Feeding"
    WALKING = "Walking"
    BATHING = "Bathing"
    GROOMING = "Grooming"
    MEDICATION = "Medication"
    ENRICHMENT = "Enrichment"

class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    INTERVAL = "interval"  # interval in minutes

class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class Task:
    type: TaskType
    name: str
    description: str
    duration_minutes: int
    priority: int
    frequency: Frequency = Frequency.ONCE
    interval_minutes: Optional[int] = None
    status: Status = Status.PENDING
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    pet: Optional['Pet'] = None

    def assign_task(self):
        """Mark the task as in-progress."""
        self.status = Status.IN_PROGRESS

    def complete_task(self):
        """Mark the task as completed."""
        self.status = Status.COMPLETED

    def reset_task(self):
        """Reset the task status back to pending."""
        self.status = Status.PENDING

    def is_due(self) -> bool:
        """Return True if the task's scheduled datetime has passed."""
        if self.scheduled_date is None or self.scheduled_time is None:
            return False
        now = datetime.now()
        scheduled = datetime(
            self.scheduled_date.year,
            self.scheduled_date.month,
            self.scheduled_date.day,
            self.scheduled_time.hour,
            self.scheduled_time.minute,
            self.scheduled_time.second,
        )
        return now >= scheduled

@dataclass
class Pet:
    name: str
    animal_type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[float] = None
    owner: Optional['Owner'] = None
    tasks: List[Task] = field(default_factory=list)

    def update_info(
        self,
        *,
        animal_type: Optional[str] = None,
        breed: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        weight: Optional[float] = None,
    ):
        """Update any provided pet profile fields, leaving omitted fields unchanged."""
        if animal_type is not None:
            self.animal_type = animal_type
        if breed is not None:
            self.breed = breed
        if age is not None:
            self.age = age
        if gender is not None:
            self.gender = gender
        if weight is not None:
            self.weight = weight

    def add_task(self, task: Task):
        """Add a task to the pet, enforcing no duplicate pending/in-progress types."""
        if task in self.tasks:
            raise ValueError("Task already assigned to this pet.")

        for existing in self.tasks:
            if existing.type == task.type and existing.status in {Status.PENDING, Status.IN_PROGRESS}:
                raise ValueError(
                    f"Cannot add duplicate pending/in-progress task of type {task.type.value} for the same pet."
                )

        self.tasks.append(task)
        task.pet = self

    def remove_task(self, task: Task):
        """Remove a task from the pet and clear its pet reference."""
        if task not in self.tasks:
            raise ValueError("Task is not assigned to this pet.")
        self.tasks.remove(task)
        task.pet = None

    def get_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet regardless of status."""
        return self.tasks

    def summary(self) -> dict:
        """Return a dict of the pet's profile and task status counts."""
        return {
            "name": self.name,
            "animal_type": self.animal_type,
            "breed": self.breed,
            "age": self.age,
            "gender": self.gender,
            "weight": self.weight,
            "task_count": len(self.tasks),
            "pending": len([t for t in self.tasks if t.status == Status.PENDING]),
            "in_progress": len([t for t in self.tasks if t.status == Status.IN_PROGRESS]),
            "completed": len([t for t in self.tasks if t.status == Status.COMPLETED]),
        }

class Owner:
    def __init__(self, first_name: str, last_name: str, email: str, phone: str, address: str):
        """Initialize a new Owner with contact details and an empty pet list."""
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.pets: List[Pet] = []
        self.scheduler = Scheduler(self)

    def create_pet(self, name: str, animal_type: Optional[str] = None) -> Pet:
        """Create a new Pet owned by this owner and add it to the pets list."""
        pet = Pet(name=name, animal_type=animal_type, owner=self)
        self.pets.append(pet)
        return pet

    def view_pet_tasks(self, pet: Pet) -> List[Task]:
        """Return all tasks for one of the owner's pets."""
        if pet.owner != self:
            raise ValueError("You can only view tasks for your own pets.")
        return pet.get_tasks()

    def view_tasks_for_pets(self, pets: List[Pet]) -> List[Task]:
        """Return a combined list of tasks across multiple owned pets."""
        combined: List[Task] = []
        for pet in pets:
            if pet.owner != self:
                raise ValueError("You can only view tasks for your own pets.")
            combined.extend(pet.get_tasks())
        return combined

    def assign_task_to_pet(self, pet: Pet, task: Task):
        """Add a task to one of the owner's pets, enforcing ownership."""
        if pet.owner != self:
            raise ValueError("You can only assign tasks to your own pets.")
        pet.add_task(task)

    def modify_info(
        self,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ):
        """Update any subset of the owner's profile fields."""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address

    def get_info(self) -> dict:
        """Return the owner's current profile as a dictionary."""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "pet_count": len(self.pets),
        }

    def view_pet_info(self, pet: Pet) -> dict:
        """Return the summary dict for one of the owner's pets."""
        if pet.owner != self:
            raise ValueError("You can only view info for your own pets.")
        return pet.summary()

    def view_all_pets(self) -> List[dict]:
        """Return a summary dict for every pet registered to this owner."""
        return [pet.summary() for pet in self.pets]

class Scheduler:
    def __init__(self, owner: 'Owner'):
        """Initialize the Scheduler with an owner and an empty schedule."""
        self.owner = owner
        # schedule maps datetime slots -> list of booking dicts built by build_schedule
        self.schedule: dict = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_slot(date: datetime, time: datetime) -> datetime:
        """Combine separate date and time objects into a single datetime slot."""
        return datetime(date.year, date.month, date.day,
                        time.hour, time.minute, time.second)

    def _booking_entry(self, pet: 'Pet', task: Task) -> dict:
        """Produce a display-ready dict for one pet/task booking."""
        return {
            "pet_name": pet.name,
            "task_name": task.name,
            "task_type": task.type.value,
            "priority": task.priority,
            "duration_minutes": task.duration_minutes,
            "task_status": task.status.value,
        }

    def _all_owner_tasks(self) -> List[tuple]:
        """Yield (pet, task) pairs for every task across all owner pets."""
        pairs = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    # ------------------------------------------------------------------
    # Build / refresh the internal schedule
    # ------------------------------------------------------------------

    def build_schedule(self, pets: List['Pet']) -> dict:
        """Seed a 7-day hourly schedule and populate it with each pet's already-scheduled tasks."""
        from datetime import timedelta

        for pet in pets:
            if pet.owner != self.owner:
                raise ValueError("You can only build schedules for your own pets.")

        base_date = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
        schedule: dict = {}

        # seed all hourly slots for 7 days as empty
        for day in range(7):
            for hour in range(12):  # 8 AM – 7 PM
                slot = base_date + timedelta(days=day, hours=hour)
                schedule[slot] = []

        # fill in tasks that already have a scheduled date/time
        for pet in pets:
            for task in pet.tasks:
                if task.scheduled_date and task.scheduled_time:
                    slot = self._to_slot(task.scheduled_date, task.scheduled_time)
                    if slot not in schedule:
                        schedule[slot] = []
                    schedule[slot].append(self._booking_entry(pet, task))

        self.schedule = schedule
        return schedule

    # ------------------------------------------------------------------
    # Viewing the schedule
    # ------------------------------------------------------------------

    def view_schedule(self, pets: Optional[List['Pet']] = None) -> List[dict]:
        """Return the full 7-day schedule as a sorted list of slot entries with availability and booking details."""
        target_pets = pets if pets is not None else list(self.owner.pets)
        self.build_schedule(target_pets)

        result = []
        for slot in sorted(self.schedule):
            bookings = self.schedule[slot]
            result.append({
                "slot": slot,
                "date": slot.strftime("%Y-%m-%d"),
                "time": slot.strftime("%H:%M"),
                "available": len(bookings) == 0,
                "bookings": sorted(bookings, key=lambda b: b["priority"], reverse=True),
            })
        return result

    def get_available_slots(
        self,
        pets: Optional[List['Pet']] = None,
        date: Optional[datetime] = None,
    ) -> List[dict]:
        """Return only unbooked slots, optionally filtered to a single calendar day."""
        all_slots = self.view_schedule(pets)
        free = [s for s in all_slots if s["available"]]
        if date is not None:
            free = [s for s in free if s["date"] == date.strftime("%Y-%m-%d")]
        return free

    def get_slot_info(self, date: datetime, time: datetime) -> dict:
        """Return availability and booking details for a specific date/time slot."""
        # Always work with up-to-date data
        self.build_schedule(list(self.owner.pets))

        slot = self._to_slot(date, time)
        bookings = self.schedule.get(slot, [])

        # If the slot wasn't seeded (outside the 7-day window) still collect
        # any tasks explicitly scheduled there
        if slot not in self.schedule:
            for pet, task in self._all_owner_tasks():
                if task.scheduled_date and task.scheduled_time:
                    if self._to_slot(task.scheduled_date, task.scheduled_time) == slot:
                        bookings.append(self._booking_entry(pet, task))

        return {
            "slot": slot,
            "date": slot.strftime("%Y-%m-%d"),
            "time": slot.strftime("%H:%M"),
            "available": len(bookings) == 0,
            "bookings": sorted(bookings, key=lambda b: b["priority"], reverse=True),
        }

    def is_slot_available(self, date: datetime, time: datetime) -> bool:
        """Return True if no tasks are booked at the given date/time."""
        return self.get_slot_info(date, time)["available"]

    def view_tasks_by_priority(self, pets: Optional[List['Pet']] = None) -> List[dict]:
        """Return all scheduled tasks across the owner's pets sorted by priority descending."""
        target_pets = pets if pets is not None else list(self.owner.pets)
        for pet in target_pets:
            if pet.owner != self.owner:
                raise ValueError("You can only view tasks for your own pets.")

        entries = []
        for pet in target_pets:
            for task in pet.tasks:
                if task.scheduled_date and task.scheduled_time:
                    entries.append({
                        "priority": task.priority,
                        "pet_name": pet.name,
                        "task_name": task.name,
                        "task_type": task.type.value,
                        "duration_minutes": task.duration_minutes,
                        "task_status": task.status.value,
                        "scheduled_date": task.scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": task.scheduled_time.strftime("%H:%M"),
                    })

        return sorted(entries, key=lambda e: e["priority"], reverse=True)

    # ------------------------------------------------------------------
    # Mutating the schedule (unchanged logic, same behaviour as before)
    # ------------------------------------------------------------------

    def assign_task_to_schedule(self, pet: 'Pet', task: Task, date: datetime, time: datetime):
        """Place a task on the schedule at the given date/time."""
        from datetime import timedelta

        if pet.owner != self.owner:
            raise ValueError("You can only assign tasks for your own pets.")
        if task.pet != pet:
            raise ValueError("Task must be assigned to the pet first.")
        if task.status == Status.COMPLETED:
            raise ValueError("Cannot schedule a task that is already completed.")

        candidate_slot = self._to_slot(date, time)

        for existing in pet.tasks:
            if existing is task or existing.scheduled_date is None or existing.scheduled_time is None:
                continue
            existing_slot = self._to_slot(existing.scheduled_date, existing.scheduled_time)
            if existing_slot == candidate_slot:
                raise ValueError(f"Conflict: {existing.name} already scheduled at {candidate_slot}.")

            if existing.type == task.type:
                existing_end = existing_slot + timedelta(minutes=existing.duration_minutes)
                if abs((existing_end - candidate_slot).total_seconds()) <= 60:
                    raise ValueError(
                        f"Cannot schedule {task.type.value} back-to-back; "
                        f"existing '{existing.name}' ends at {existing_end}."
                    )

        task.scheduled_date = date
        task.scheduled_time = time
        task.status = Status.IN_PROGRESS if self._to_slot(date, time) <= datetime.now() else Status.PENDING

    def move_task(self, pet: 'Pet', task: Task, date: datetime, time: datetime) -> dict:
        """Move an already-scheduled task to a new date/time."""
        if pet.owner != self.owner:
            raise ValueError("You can only move tasks for your own pets.")
        if task.pet != pet:
            raise ValueError("Task must be assigned to the pet first.")
        if task.status == Status.COMPLETED:
            raise ValueError("Cannot move a task that is already completed.")

        old_slot = (
            self._to_slot(task.scheduled_date, task.scheduled_time)
            if task.scheduled_date and task.scheduled_time
            else None
        )
        new_slot = self._to_slot(date, time)

        for existing in pet.tasks:
            if existing is task or existing.scheduled_date is None or existing.scheduled_time is None:
                continue
            existing_slot = self._to_slot(existing.scheduled_date, existing.scheduled_time)
            if existing_slot == new_slot:
                raise ValueError(f"Conflict: {existing.name} is already scheduled at {new_slot}.")

        task.scheduled_date = date
        task.scheduled_time = time
        task.status = Status.IN_PROGRESS if new_slot <= datetime.now() else Status.PENDING

        return {
            "previous_slot": old_slot,
            "new_slot": new_slot,
            "status": task.status,
            "message": f"Task '{task.name}' moved from {old_slot} to {new_slot}.",
        }

