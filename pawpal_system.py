from dataclasses import dataclass
from typing import List

@dataclass
class Pet:
    name: str
    species: str
    tasks: List['Task'] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = []

    def assign_task(self):
        pass

@dataclass
class Task:
    type: str
    duration: int
    name: str
    priority: int

class Owner:
    def __init__(self, first_name: str, last_name: str, email: str, phone: str, address: str):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.pets: List[Pet] = []

    def create_pet(self):
        pass

    def assign_pet(self):
        pass

    def modify_info(self):
        pass

class Scheduler:
    def build_schedule(self):
        pass
