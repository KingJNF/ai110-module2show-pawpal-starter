# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
I chose four classes: Pet, Owner, Task and Schedule. The pet class will show the pet's name and species. The task will provide the owner with the specific task the pet will be doing the priority or how important it is for their pet and how long do they want the task or the pet to do that task for. Meanwhile the schedule will show when the pet will do the task or tasks that they have been assigned. 

- What classes did you include, and what responsibilities did you assign to each?
The three core actions should be:(In no particular order)
1) Add a pet.
2) Add/Edit the pet's tasks.
3) See the pets schedule.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
   Yes there were design changes made. There were several logical steps that between my brainstorming and my initial design implementation via AI that I had not considered. For example, I had set it up so you can choose the duration but not specifically the date & time when the task should be actually scheduled. Also the scheduler was not setup to be able to be used by an Owner to choose a pet and task and assign it to a specific date and time. Also changed it so owner can choose the duration date and time of the task.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
Time available, Priority, Owner Preferences.

- How did you decide which constraints mattered most?
   I decided by putting myself in the mindset of a user of this app, in this case a pet owner. What would be the most useful info I would want to see or be able to choose while using an app like this? 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?
   The initial algorithm is from 807 to 852 in the pawpal system file. It is specifically for the lightweight conflict detection system. That is 45 lines of code. It's alternate idea for it is 25 lines. The updated code only provides minor improvement in performance but makes it more readable. I kept the updated algorithm since it is not only almost half the amount of lines, it also includes multiple lines of comments which makes it easier to come back to in the future. The less amount of lines the less likely an error to occur and even if one does appear in the future its easier to determine if that segment of code is the culprit or not.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used it during the design, coding, brainstorming, debugging, and refactoring phases.


- What kinds of prompts or questions were most helpful?



**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?


**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
If  you want something done properly by the AI, you have to be as specific as possible and even allow it to ask you questions. This way it can give you the best possible answer.