# TalkingPhoto MVP - Daily Standup Guide & Templates

## 🎯 Daily Standup Excellence Framework

### Standup Purpose & Objectives

**Primary Purpose**: Synchronize team progress and identify collaboration opportunities  
**Secondary Purpose**: Surface impediments early and coordinate daily work  
**Success Criteria**: Team leaves with clear understanding of day's priorities and blockers

### Core Standup Principles

1. **Focus on Collaboration**: What can we help each other with?
2. **Be Specific**: Use story IDs, concrete progress, clear next steps
3. **Identify Dependencies**: Who needs what from whom by when?
4. **Surface Impediments Early**: Don't struggle in silence
5. **Keep It Timeboxed**: Respect everyone's focus time

---

## ⏰ Daily Standup Structure (15 Minutes Max)

### Pre-Standup Preparation (5 minutes individual)

#### Personal Preparation Checklist

```
Before joining standup, each team member reviews:
□ Yesterday's completed work and commits
□ Current story status and progress percentage
□ Today's planned work and dependencies
□ Any blockers or help needed from team
□ Items ready for review or testing
```

#### Standup Preparation Template

```markdown
## My Standup Prep - [Date]

### Yesterday's Achievements ✅

- [TP-XXX] Specific work completed with % done
- Code commits: [Link to commits or brief description]
- Reviews completed: [PR numbers reviewed]
- Tests written/run: [Test coverage or results]

### Today's Plan 🎯

- [TP-XXX] Specific tasks with time estimates
- Dependencies: Need [what] from [who] by [when]
- Will help: [Team member] with [specific task]
- Expected deliverables by end of day

### Blockers & Help Needed 🚨

- Blocked on: [Specific impediment with context]
- Help needed: [Specific request for team member]
- Will escalate: [If not resolved by when]

### Confidence Level: [High/Medium/Low]

- Concerns: [Specific risks or challenges]
```

### Standup Flow & Timing

#### Round-Robin Format (12 minutes)

**2 minutes per person maximum**

```
👨‍💻 Team Member Updates (2 min each × 6 people = 12 min)
├── Yesterday's completed work (30 seconds)
├── Today's planned work (30 seconds)
├── Dependencies and collaboration needs (30 seconds)
├── Blockers and help requests (30 seconds)

🤝 Team Coordination (3 minutes)
├── Cross-story dependencies clarification
├── Pair programming opportunities identification
├── Quick decision on urgent items
├── Parking lot items for later discussion
```

#### Alternative: Walking the Board (When needed)

**Story-focused instead of person-focused**

```
📋 Story Status Review (10 minutes)
├── Stories in "In Progress" column
├── Stories ready for review/testing
├── Stories blocked or at risk
├── Stories ready to move to "Done"

🎯 Today's Focus (5 minutes)
├── Highest priority stories for today
├── Cross-team collaboration needed
├── Testing and review priorities
├── Risk mitigation actions
```

---

## 🗣️ Standup Communication Templates

### Daily Update Template - Standard Format

```
🎯 [Your Name] - [Date] Daily Update

YESTERDAY ✅:
- [TP-001] Photo upload interface: Completed drag-drop functionality (80% done)
- Reviewed PRs: #45 (TP-003) and #47 (TP-005)
- Fixed bug in file validation that was blocking QA testing

TODAY 🔄:
- [TP-001] Photo upload: Complete error handling and add tests (target: 100% done)
- [TP-002] API integration: Start HeyGen API connection (target: 30% done)
- Help [Team Member] with authentication flow debugging (30 min planned)

DEPENDENCIES 🔗:
- Need: Design mockups from [Designer] for upload error states by 2 PM
- Provide: Upload component API for [Backend Dev] by 4 PM

BLOCKERS 🚨:
- None currently / [Specific blocker with context]

CONFIDENCE: High - on track for sprint goals
```

### Standup Update Template - Concise Format

```
🎯 [Your Name] - Quick Update

✅ DONE: [TP-001] Upload UI complete, PRs reviewed
🔄 TODAY: [TP-002] API integration, help with auth debugging
🔗 NEED: Design mockups by 2 PM from [Designer]
🚨 BLOCKERS: None / [Specific issue]
📈 CONFIDENCE: High/Medium/Low
```

### Standup Update Template - First Day of Sprint

```
🎯 [Your Name] - Sprint Start

🚀 SPRINT GOAL: [Remind team of sprint objective]
🎯 MY FOCUS: [TP-001, TP-002] - Photo upload and API integration
📋 TODAY: Story kickoff, environment setup, initial research
🤝 PAIRING: Available for [TP-003] auth flow collaboration
📈 CONFIDENCE: High - excited to start building!
```

### Standup Update Template - Sprint End

```
🎯 [Your Name] - Sprint Wrap

✅ COMPLETED: [TP-001] 100% done, [TP-002] 95% done (testing pending)
🎯 TODAY: Final testing, demo prep, retrospective preparation
📊 SPRINT STATUS: 95% of committed work complete
🎉 HIGHLIGHTS: [Specific achievement or learning to celebrate]
📈 CONFIDENCE: High - sprint goal achieved!
```

---

## 🎭 Standup Roles & Responsibilities

### Scrum Master Facilitation Guide

#### Before Standup (9:55 AM)

```
Scrum Master Pre-Standup Checklist:
□ Review sprint board for story status updates
□ Check overnight notifications for blockers or issues
□ Prepare timebox reminders and parking lot items
□ Have impediment log ready for updates
□ Review previous day's action items
```

#### During Standup Facilitation

```
Facilitation Script:

"Good morning team! Let's sync up for 15 minutes max.
Quick reminder of our sprint goal: [State goal]

Format today: Each person shares Yesterday/Today/Dependencies/Blockers
Time limit: 2 minutes per person
Questions for offline discussion go to parking lot

[Team Member 1], please start us off..."

[After each person]:
"Thank you. Any quick clarifications? No? [Next person] you're up."

[After all updates]:
"Great updates everyone. Three items for parking lot:
1. [Item requiring offline discussion]
2. [Technical decision needed]
3. [Process improvement suggestion]

Any other immediate coordination needed? No?
See you all at 6 PM for daily wrap-up. Have a productive day!"
```

#### After Standup (10:15 AM)

```
Scrum Master Post-Standup Actions:
□ Update sprint board with any status changes
□ Create/update impediment log entries
□ Schedule parking lot discussions with relevant people
□ Send daily summary to stakeholders (if required)
□ Follow up on action items from previous day
```

### Team Member Best Practices

#### Effective Standup Participation

**DO:**

- ✅ Arrive on time and prepared with specific updates
- ✅ Use story IDs and concrete progress percentages
- ✅ Proactively offer help to teammates facing challenges
- ✅ Be honest about struggles and blockers
- ✅ Listen actively to others and identify collaboration opportunities

**DON'T:**

- ❌ Give vague updates like "working on the same thing"
- ❌ Go into detailed technical explanations
- ❌ Have side conversations during others' updates
- ❌ Wait until standup to surface critical blockers
- ❌ Report status to Scrum Master instead of sharing with team

#### Managing Difficult Standup Situations

**Situation: Team Member Goes Over Time**

```
Intervention Script:
"Thanks [Name], that's great progress. Can we take the
technical details offline and get [specific next person] input on
[relevant dependency]? [Next person], you're up."
```

**Situation: Vague or Unhelpful Update**

```
Follow-up Questions:
"[Name], which specific story are you working on today?"
"What percentage complete would you estimate [Story ID] to be?"
"What specific help do you need from the team?"
"When do you expect to have [deliverable] ready for review?"
```

**Situation: Technical Discussion Derailing Standup**

```
Parking Lot Redirect:
"This sounds like an important architectural decision.
Let's add it to parking lot for [Name] and [Name] to
discuss after standup. [Next person], your update please."
```

---

## 📊 Standup Effectiveness Tracking

### Daily Standup Metrics

#### Quantitative Metrics

| Metric            | Target                 | Measurement        | Action if Off-Target       |
| ----------------- | ---------------------- | ------------------ | -------------------------- |
| **Duration**      | 15 minutes             | Stopwatch timing   | Facilitate more strictly   |
| **Attendance**    | 95%+                   | Meeting attendance | Address with individuals   |
| **Participation** | 100% speak             | Observation        | Encourage quiet members    |
| **Action Items**  | 80% completed next day | Follow-up tracking | Improve commitment process |

#### Qualitative Assessment (Weekly)

```
Standup Quality Checklist (Rate 1-5 daily):
□ Updates were specific and actionable
□ Dependencies were clearly communicated
□ Blockers were surfaced appropriately
□ Team coordination opportunities identified
□ Meeting stayed focused and on-time

Weekly Average Target: 4+ out of 5
```

### Standup Improvement Framework

#### Weekly Standup Retrospective (5 minutes Friday)

```
Quick Standup Review Questions:
1. What worked well in our standups this week?
2. What was frustrating or ineffective?
3. One specific improvement for next week?
4. Are we getting value from our standup format?

Action: Implement one improvement experiment for following week
```

#### Monthly Standup Health Check

```
Team Survey (Anonymous, 2 minutes):
1. Standups help me coordinate my work effectively (1-10)
2. I feel comfortable sharing blockers and asking for help (1-10)
3. Our standup format works well for our team (1-10)
4. I learn useful information from teammates' updates (1-10)
5. Standups are a good use of our team time (1-10)

Open feedback: What would make standups more valuable?
```

---

## 🔄 Alternative Standup Formats

### Format 1: Focus-Driven Standup

**Use When**: Multiple complex stories in progress

```
🎯 Focus Areas Today (5 minutes):
├── Sprint Goal Progress: Are we on track?
├── Critical Path Items: What must finish today?
├── Cross-Team Dependencies: Who needs what from whom?
├── Risk Mitigation: What needs attention?

👥 Individual Quick Updates (8 minutes):
├── Name + Today's top priority
├── Help needed or offered
├── Blockers requiring team input

🤝 Coordination (2 minutes):
├── Pair programming opportunities
├── Review/testing coordination
├── Parking lot items
```

### Format 2: Story-Walking Standup

**Use When**: Many stories in flight, complex dependencies

```
📋 Board Review (10 minutes):
├── "In Progress" stories: Status and today's work
├── "Ready for Review" stories: Who will review?
├── "Blocked" stories: Impediment status and actions
├── "Ready to Start" stories: Who picks up next?

🎯 Today's Commitments (5 minutes):
├── What will move to "Done" today?
├── What help is needed to unblock stories?
├── What new stories will be started?
├── Any risks to sprint goal achievement?
```

### Format 3: Risk-Focused Standup

**Use When**: Sprint at risk or multiple blockers

```
🚨 Sprint Risk Assessment (5 minutes):
├── Sprint goal achievement probability
├── Current blockers and resolution progress
├── Stories at risk of missing commitment
├── External dependencies status

⚡ Mitigation Actions (8 minutes):
├── What can we do today to reduce risks?
├── Who needs help to get back on track?
├── What stories should we prioritize?
├── Should we consider scope adjustment?

🎯 Daily Focus (2 minutes):
├── Today's highest priority items
├── Team coordination needed
├── End-of-day checkpoint plan
```

---

## 📱 Remote & Hybrid Standup Guidelines

### Virtual Standup Best Practices

#### Technology Setup

```
Required Setup:
□ Stable internet connection (backup hotspot available)
□ Working camera and microphone
□ Zoom/Teams app updated and tested
□ Screen sharing capability for board review
□ Slack open for chat backup communication
```

#### Virtual Engagement Techniques

- **Video On**: Everyone keeps camera on for better engagement
- **Mute Management**: Mute when not speaking, unmute for updates
- **Screen Sharing**: Rotate board sharing between team members
- **Chat Backup**: Use chat for links, story IDs, follow-up items
- **Breakout Option**: Quick breakouts for urgent coordination

#### Async Standup Alternative (When Needed)

```
Async Standup Template (Use sparingly):

Thread in #talkingphoto-general:
🎯 Daily Async Standup - [Date]

Each team member responds with:
✅ Yesterday: [Specific completed work]
🔄 Today: [Specific planned work with time estimates]
🔗 Dependencies: [What needed from whom by when]
🚨 Blockers: [Current impediments or help needed]

⏰ Deadline: All updates by 10:30 AM
📞 Follow-up: Sync call at 11 AM if needed for coordination
```

### Timezone Coordination (When Applicable)

- **Core Hours**: Define overlap times for standup scheduling
- **Rotating Times**: Adjust standup time weekly to share inconvenience
- **Async Components**: Use async updates for non-overlapping hours
- **Recorded Updates**: Video updates for major impediments or decisions

---

## 🎉 Standup Success Stories & Celebrations

### Celebrating Good Standups

```
Weekly Recognition Categories:
🎯 "Most Helpful Update": Clear dependencies and specific help offered
💡 "Best Problem Solver": Creative solution shared with team
🤝 "Team Player": Proactive collaboration and support
📊 "Progress Champion": Consistent, specific progress updates
⚡ "Blocker Buster": Effective impediment identification and resolution
```

### Standup Success Indicators

- **Team Energy**: High energy and engagement in updates
- **Collaboration**: Multiple team members offering help to each other
- **Transparency**: Honest sharing of struggles and blockers
- **Focus**: Clear understanding of daily priorities leaving standup
- **Efficiency**: Consistently finishing within 15-minute timebox

### Continuous Standup Evolution

```
Monthly Standup Innovation:
- Try new format for one week
- Gather team feedback on effectiveness
- Measure impact on coordination and communication
- Adopt improvements that increase value
- Share learnings with other teams
```

---

_Daily Standup Guide created: September 13, 2025_  
_Facilitator: Scrum Master (rotating weekly)_  
_Review schedule: Weekly format assessment, monthly comprehensive review_  
_Next evolution: Week 2 format experiment based on team feedback_
