import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pawpal_system import Owner, Task, TaskType, Status


def test_complete_task_changes_status():
    """Calling complete_task() on a Task should change its status to COMPLETED."""
    task = Task(
        type=TaskType.FEEDING,
        name="Breakfast",
        description="Morning meal",
        duration_minutes=10,
        priority=1,
    )
    assert task.status == Status.PENDING

    task.complete_task()

    assert task.status == Status.COMPLETED


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet should increase that pet's task count by one."""
    owner = Owner("Jane", "Doe", "jane@example.com", "555-0000", "1 Main St")
    pet = owner.create_pet("Fido", animal_type="Dog")
    assert len(pet.tasks) == 0

    task = Task(
        type=TaskType.WALKING,
        name="Morning Walk",
        description="Walk around the block",
        duration_minutes=30,
        priority=2,
    )
    owner.assign_task_to_pet(pet, task)

    assert len(pet.tasks) == 1
