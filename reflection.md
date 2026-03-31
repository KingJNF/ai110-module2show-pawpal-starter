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
   I placed time boundaries. Making sure that tasks can only be assigned between 8 AM and 8 PM. ALso that no two tasks for the same pet can occur at the same time on the same day. Set it up so for example if a 30 minute walk is scheduled for 2 PM the system recoginizes that from 2 to 2:30 nothing else can be set. For example a 10 minute medication task can't be set for 2:15 because the pet is being walked at that time. Also with the priority system, set from 1 to 10, 10 being the highest priority, if its a priority 10 medication task it will be scheduled before the level 3 grooming task. Another constraint is preventing two tasks of the same tpe to be scheduled back to back. No pet would ever be walked or fed twice in a row. Also I implemented a system that helps the individual owners where if they have multiple pets it will take into account if another pet already has a task for that day and time. Example being it would be impossible for an owner to walk their dog and feed their cat at 1 PM on the same day.


- How did you decide which constraints mattered most?
   I decided by putting myself in the mindset of a user of this app, in this case a pet owner. What would be the most useful info I would want to see or be able to choose while using an app like this? What came first was the time boundaries. Anything that a pet owner would have to do before 8 AM or after 8 PM with their pet would most likely constitute some type of emergency or one off unique occurrence. Setting a mundane normal pet related task between 8 AM and 8 PM sounds reasonable as a pet owner. Then making sure that the system recoginized and properly took into consideration overlapping times came second. If a 45 minute bath starts at 2 PM its not just 2 PM that's taken. It actually means that from 2 PM - 2:45 PM, that pet is being bathed. Can't schedule a walk at 2:30 PM. Priority comes next, because after time slots that matters most. A can't miss medical dose thats set to priority 10 is infinitely more important than a level 4 grooming session. Then back to back same task prevention came next on the list. That was due to it being more logic but still something needed. Last thing an owner needs is realizing they are about to feed their dog twice when it reality it should be a feeding then a walk for example. No one gives their pet two meals in a row. While the last one is cross pet scheduling conflicts. I put this last since not everyone that owns a pet has more than one. So while an owner with multiple pets can use this app/website, it does not mean that every single user of this app will be in that situation.



**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
   The auto scheduler uses a greedy algorithm. It sorts tasks by priority, placing each one into the earliest available slot. The tradoess is this approach priortizes speed and simplicity over finding the most optimal schedule. This means high priority tasks will get the best slot while lesser tasks will get less than ideal times.

- Why is that tradeoff reasonable for this scenario?
   Its reasonable because this is a simple app for individual owners with only a handful of pets across a single week. The average user/owner might be possibly scheduling 10 to 20 tasks throughout the week for their pet or pets, not thousands. Pet care is by nature flexible, if the owner doesn't like where a task landed they can move it easily. The greedy approach gives them a quick easy starting point while the maunal move casuses them litte to no 

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used it during the design, coding, brainstorming, debugging, and refactoring phases.


- What kinds of prompts or questions were most helpful?
   The most useful ones were it provided the majority of the testing scripts especially for edge cases. Questions that were helpful in answering was trying to find a specific snippet of code and determine what was wrong with just that part of the code.


**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
   One time I didn't accept thier answer was when I wanted to enter a pop up notification for when the owner updated their profile.


- How did you evaluate or verify what the AI suggested?
   It suggested to place it in a certain point of the code in a specific file, but I couldn't find it. Instead of placing it where I thought it should go, I asked it and let it know that I was unaware and if it could be more detailed. It then gave me a specific line of where that segment of code should have started at and then gave me the two specific lines where that snippet ends and told me to palce the additional code it gave me right before those two lines. And that worked, the first time, without getting an error. 

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
 In the end we created a grand total of 107 tests. Some were basic logic tests while other were testing possible usual and edge case secenarios.

- Why were these tests important?
   These are important because they might not be picked up directly by a user, but they can affect performmance. Also some of these tests check for edge cases. Also, it would take alot more time to individually, manually test for each of those sections of the website/app.

**b. Confidence**

- How confident are you that your scheduler works correctly?
   I give it a 9 out of 10. Nothing is perfect, and I dont know enough of AI coding or coding in genertal to make this app as streamlined and smoooth as an experience possible.
- What edge cases would you test next if you had more time?
   
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
   The main coding segments were extremely smooth. I basically told the AI what I wanted and it wrote the code to do just that. And when testing it myself if I saw the logic was wrong or some type of notification was missing it was as easy as telling some expert programmer, "hey, the pop up notification when they do this is missing. Put it in", and the AI would just go and write it and even outside VS Code, it would tell me where to place the new code exactly down to an estimate of the specific line and which is the old code it should be replacing.


**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
   If I had more time I would choose a different color scheme for the website. I would implement an active calendar.
   IT would show in real time what pets and tasks are available and you can click and drag the tasks to specific dates and times instead of entering all the info and then hoping there isn't something scheduled already for that date and time.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
If  you want something done properly by the AI, you have to be as specific as possible and even allow it to ask you questions. This way it can give you the best possible answer. Also, working with a built in AI agent on a coding project helps out much more than using an AI outside of the coding.