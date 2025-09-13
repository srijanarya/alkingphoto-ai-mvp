# TalkingPhoto MVP - Team Collaboration Protocols

## 🤝 Team Communication Framework

### Core Communication Principles

1. **Transparency First**: All decisions, blockers, and progress visible to team
2. **Context Over Clarity**: Provide background information for better understanding
3. **Async by Default**: Respect focus time, use synchronous only when necessary
4. **Documentation Rich**: Record decisions and learnings for future reference
5. **Feedback Culture**: Constructive feedback welcomed and acted upon promptly

---

## 📱 Communication Tools & Channels

### Slack Channel Structure

```
🏠 #talkingphoto-general
   └── Daily updates, team announcements, general discussion
   └── @channel sparingly, @here for urgent items only

🚨 #talkingphoto-blockers
   └── Real-time impediment reporting and resolution
   └── Automated GitHub issue alerts for blockers
   └── Resolution updates and learnings shared

🔧 #talkingphoto-decisions
   └── Architecture decisions and technical choices
   └── Business logic decisions requiring team input
   └── Template: Problem → Options → Decision → Rationale

🤖 #talkingphoto-alerts
   └── Automated notifications from GitHub, CI/CD
   └── Performance monitoring alerts
   └── Deployment status updates

💻 #talkingphoto-dev
   └── Technical deep dives and debugging
   └── Code review discussions
   └── API integration troubleshooting
```

### Communication Urgency Levels

| Level           | Response Time    | Use Cases                              | Notification Method       |
| --------------- | ---------------- | -------------------------------------- | ------------------------- |
| **🔴 Critical** | < 30 minutes     | Production issues, team blocked        | @channel + direct message |
| **🟡 High**     | < 4 hours        | Individual blockers, urgent decisions  | @here + thread mention    |
| **🟢 Medium**   | < 24 hours       | Standard questions, non-blocking items | Channel message           |
| **⚪ Low**      | Next working day | FYI updates, process improvements      | Threaded responses        |

### Daily Communication Rhythm

```
9:30 AM  - Pre-standup async check-in (optional)
10:00 AM - Daily standup (15 minutes max)
10:15 AM - Post-standup coordination (as needed)
12:00 PM - Lunch break communication pause
6:00 PM  - End-of-day progress update
6:30 PM  - Next-day planning (async)
```

---

## 🎯 Meeting Protocols & Guidelines

### Daily Standup Excellence

#### Pre-Standup Preparation (5 minutes)

- [ ] Review yesterday's commits and completed work
- [ ] Check current story status and blockers
- [ ] Prepare specific, actionable updates
- [ ] Identify any help needed from team members

#### Standup Facilitation Rotation

| Week       | Facilitator  | Backup         | Focus Theme            |
| ---------- | ------------ | -------------- | ---------------------- |
| **Week 1** | Scrum Master | Tech Lead      | Process establishment  |
| **Week 2** | Tech Lead    | Full-Stack Dev | Technical coordination |

#### Standup Anti-Patterns Prevention

❌ **Avoid These Behaviors:**

- Detailed technical problem-solving discussions
- Status reporting directed to Scrum Master only
- Vague updates like "working on the same thing"
- Not listening to others' updates and dependencies
- Going over 15-minute timebox

✅ **Embrace These Practices:**

- Specific story IDs and concrete progress updates
- Proactive offering of help to blocked team members
- Clear communication of dependencies on others
- Active listening and building on others' updates
- Quick identification of items for offline discussion

### Code Review Ceremonies

#### Pull Request Standards

```
PR Title Format: [Story-ID] Brief description of changes
Example: [TP-002] Implement Google Nano Banana API integration

PR Description Template:
## What Changed
- Specific functionality added/modified
- Files affected and why

## Testing Done
- Unit tests added/updated
- Manual testing scenarios executed
- Performance impact assessed

## Dependencies
- Other PRs this depends on
- External dependencies introduced

## Screenshots/Demo
- UI changes screenshots
- Terminal output for API changes

## Checklist
- [ ] Code follows team standards
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No secrets in code
- [ ] Performance impact considered
```

#### Code Review Process

1. **Author Responsibility**: Ensure PR is complete and self-reviewing first
2. **Review Assignment**: Automatic assignment to 2 team members minimum
3. **Review Timeline**: 24-hour target for initial review, 48-hour max
4. **Review Quality**: Focus on logic, performance, maintainability, security
5. **Approval Process**: Two approvals required for merge to main branch

### Sprint Ceremony Protocols

#### Sprint Planning Deep Dive

**Duration**: 2 hours maximum  
**Participants**: Full development team + Product Owner

**Agenda Structure:**

```
Hour 1: Sprint Goal & Story Refinement
├── Sprint goal alignment (15 minutes)
├── Story walkthrough and Q&A (30 minutes)
├── Technical approach discussion (15 minutes)

Hour 2: Estimation & Commitment
├── Story point estimation (poker planning) (45 minutes)
├── Capacity planning and assignment (10 minutes)
├── Sprint commitment and risk assessment (5 minutes)
```

**Planning Poker Guidelines:**

- Fibonacci sequence: 1, 2, 3, 5, 8, 13, 20
- Everyone estimates simultaneously (no anchoring)
- Discuss outliers and re-estimate
- Focus on complexity, not just time
- Consider unknowns and dependencies

#### Sprint Review Excellence

**Duration**: 45 minutes  
**Participants**: Team + Stakeholders + Users (if available)

**Demo Structure:**

```
Demo Flow (30 minutes):
├── Sprint goal recap (2 minutes)
├── Feature demonstrations (20 minutes)
├── Metrics and achievements (5 minutes)
├── Next sprint preview (3 minutes)

Feedback Collection (15 minutes):
├── Stakeholder feedback and questions
├── User acceptance validation
├── Business value assessment
├── Next sprint priorities discussion
```

---

## 🔄 Decision Making Framework

### Decision Categories & Processes

#### Technical Architecture Decisions

**Process**: Architecture Decision Records (ADRs)

```markdown
# ADR-001: API Integration Strategy

## Status

PROPOSED | ACCEPTED | DEPRECATED | SUPERSEDED

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing or have agreed to implement?

## Consequences

What becomes easier or more difficult to do and any risks introduced?
```

**Decision Authority:**

- **Individual Contributor**: Implementation details, code patterns
- **Tech Lead**: Architecture choices, major technical decisions
- **Product Owner**: Feature priorities, business logic decisions
- **Team Consensus**: Process changes, tool selections
- **Escalation**: Scrum Master → Management for conflicts

#### Business Logic Decisions

**Process**: Collaborative discussion in #talkingphoto-decisions

**Template:**

```
🎯 DECISION NEEDED: [Brief description]

Background:
- Current situation and constraints
- Options considered with pros/cons
- Impact on sprint goals and timeline

Recommendation:
- Preferred option with rationale
- Resource requirements and timeline
- Risk assessment and mitigation

Stakeholders:
- @product-owner for business impact
- @tech-lead for technical feasibility
- @team-members for implementation effort

Deadline: [When decision is needed]
```

### Conflict Resolution Process

1. **Direct Communication**: Team members attempt resolution directly
2. **Facilitated Discussion**: Scrum Master facilitates team discussion
3. **Technical Advisory**: Tech Lead provides technical guidance
4. **Business Priority**: Product Owner clarifies business priorities
5. **Escalation**: Management involvement for persistent conflicts

---

## 🧠 Knowledge Sharing Protocols

### Documentation Standards

#### Code Documentation

```python
def enhance_photo_with_nano_banana(image_data: bytes, enhancement_options: dict) -> dict:
    """
    Enhance uploaded photo using Google Nano Banana API.

    Args:
        image_data (bytes): Raw image data from user upload
        enhancement_options (dict): Enhancement parameters
            - brightness: float (0.0-2.0, default 1.0)
            - contrast: float (0.0-2.0, default 1.0)
            - saturation: float (0.0-2.0, default 1.0)

    Returns:
        dict: {
            'enhanced_image_url': str,
            'processing_time': float,
            'enhancement_score': float,
            'error': str | None
        }

    Raises:
        APIConnectionError: When Nano Banana API is unreachable
        InvalidImageError: When image format is unsupported

    Example:
        >>> options = {'brightness': 1.2, 'contrast': 1.1}
        >>> result = enhance_photo_with_nano_banana(img_bytes, options)
        >>> print(result['enhanced_image_url'])
    """
```

#### API Integration Documentation

````markdown
# HeyGen API Integration Guide

## Overview

HeyGen API provides video generation from photos and text scripts.

## Authentication

```python
headers = {
    'Authorization': f'Bearer {HEYGEN_API_KEY}',
    'Content-Type': 'application/json'
}
```
````

## Rate Limits

- 100 requests per hour per API key
- 10 concurrent video generations max
- Queue system implemented for overflow

## Error Handling

- Retry logic: 3 attempts with exponential backoff
- Fallback: Queue for manual processing
- User notification: Progress updates via WebSocket

```

### Learning Session Framework
#### Technical Deep Dives (Weekly)
**Format**: 30-minute focused sessions
**Timing**: Friday 4:00 PM (end of week knowledge sharing)

**Session Structure:**
```

Week 1: "HeyGen API Best Practices"
├── API integration patterns (10 minutes)
├── Error handling strategies (10 minutes)  
├── Performance optimization tips (10 minutes)

Week 2: "Streamlit Advanced Patterns"  
├── Custom component creation (10 minutes)
├── State management patterns (10 minutes)
├── Performance optimization (10 minutes)

```

#### Pair Programming Guidelines
**Recommended Pairings:**
- Junior + Senior for knowledge transfer
- Frontend + Backend for integration work
- Different domain expertise for learning

**Pair Programming Etiquette:**
- Switch driver/navigator every 25 minutes
- Both pairs actively engaged and contributing
- Document learnings and decisions made
- Share session notes with rest of team

---

## 🚀 Productivity & Focus Protocols

### Deep Work Time Protection
#### Individual Focus Blocks
```

🔴 Deep Work Hours (No meetings/interruptions):
├── 11:00 AM - 1:00 PM: Morning focus block
├── 2:30 PM - 4:30 PM: Afternoon focus block  
├── Optional: 7:00 PM - 9:00 PM: Evening focus (remote)

📞 Collaboration Hours (Meetings/discussions welcome):
├── 10:00 AM - 11:00 AM: Standup + coordination
├── 1:00 PM - 2:30 PM: Lunch + informal collaboration  
├── 4:30 PM - 6:00 PM: Reviews, planning, demos

```

#### Focus Time Indicators
- **Slack Status**: "🔴 Deep Work" during focus blocks
- **Calendar Blocking**: Focus blocks marked as busy
- **Physical Indicators**: Headphones for in-office team members
- **Interruption Protocol**: Slack DM for non-urgent items

### Meeting Hygiene
#### Meeting Quality Standards
- **Purpose Clarity**: Clear objective stated in invite
- **Agenda Required**: Shared 24 hours in advance
- **Timeboxing**: Start/end times strictly observed
- **Action Items**: Captured and assigned during meeting
- **Follow-up**: Summary sent within 2 hours

#### Meeting Types & Standards
| Meeting Type | Max Duration | Required Prep | Participants |
|--------------|--------------|---------------|--------------|
| **Daily Standup** | 15 minutes | Review yesterday's work | Core team only |
| **Planning** | 2 hours | Story refinement complete | Team + PO |
| **Review** | 45 minutes | Demo prep completed | Team + stakeholders |
| **Retrospective** | 60 minutes | Metrics review | Core team only |
| **Technical Spike** | 30 minutes | Research completed | Relevant specialists |

---

## 🎯 Performance & Accountability Framework

### Individual Accountability
#### Daily Commitment Tracking
```

Daily Commitment Template (shared in standup):
Today's Goals:
├── [Story-ID] Specific task with completion criteria  
├── [Story-ID] Collaboration needed with [team member]
├── [Story-ID] Expected completion percentage

Dependencies:
├── Waiting on: [What/Who] by [When]
├── Blocking: [Who] on [What] - resolution by [When]
├── Help needed: [Specific request] from [Team member]

Confidence Level: [High/Medium/Low] with specific concerns

````

#### Weekly Goal Setting
**Friday Planning Session (Individual)**:
- Review current sprint progress and blockers
- Set specific goals for following week
- Identify learning opportunities and skill development
- Plan collaboration needs with team members

### Team Accountability
#### Sprint Commitment Honor System
**Commitment Principles:**
- Conservative estimation with confidence intervals
- Proactive communication when commitment at risk
- Early escalation for scope or timeline issues
- Collective ownership of sprint success

**Commitment Tracking:**
- Daily progress against committed points
- Velocity trending and predictability analysis
- Team discussion of capacity planning accuracy
- Retrospective analysis of commitment reliability

### Performance Support Framework
#### Struggling Team Member Support
**Indicators:**
- Consistent missing of daily commitments
- Silent in standups or avoiding communication
- Code quality issues or excessive rework needed
- Difficulty with technical implementation

**Support Process:**
1. **Peer Support**: Pair programming and knowledge sharing
2. **Scrum Master Check-in**: Private discussion of challenges
3. **Technical Mentoring**: Tech Lead provides additional guidance
4. **Resource Allocation**: Temporary adjustment of story assignments
5. **Skill Development**: Focused learning time and resources

#### High Performer Recognition
**Recognition Opportunities:**
- **Technical Innovation**: Creative solutions and improvements
- **Team Leadership**: Mentoring and supporting others
- **Quality Excellence**: Consistently high code and delivery quality
- **Problem Solving**: Effective impediment resolution
- **Customer Focus**: User-centered thinking and solutions

---

## 🔧 Tools & Automation Setup

### Development Environment Standardization
#### Required Tool Setup
```bash
# Core development tools
git --version                    # Version control
docker --version                 # Containerization
python --version                 # Python 3.9+
node --version                   # Node.js for tooling

# Development environment
code --version                   # VS Code with extensions
streamlit --version              # UI framework
pytest --version                 # Testing framework

# Collaboration tools
slack --version                  # Team communication
zoom --version                   # Video meetings
````

#### VS Code Shared Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-toolsai.jupyter",
    "redhat.vscode-yaml",
    "streetsidesoftware.code-spell-checker",
    "GitHub.copilot",
    "ms-vscode.vscode-json"
  ]
}
```

#### Git Workflow Standards

```bash
# Branch naming convention
feature/TP-001-photo-upload-interface
bugfix/TP-002-api-error-handling
hotfix/production-critical-issue

# Commit message format
[TP-001] Add photo upload interface component

- Implement drag-and-drop functionality
- Add file type validation
- Include progress indicator
- Update tests and documentation

Co-authored-by: [Team Member] <email@domain.com>
```

### Automation & Integration Setup

#### GitHub Actions Workflow

```yaml
name: TalkingPhoto CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: "3.9"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: |
          pytest tests/ --cov=app --cov-report=xml

      - name: Code quality check
        run: |
          flake8 app/ tests/
          black --check app/ tests/
```

#### Slack Integration Automation

- **GitHub Notifications**: PR updates, deployments, issues
- **CI/CD Alerts**: Build status, test failures, deployment success
- **Performance Monitoring**: API response times, error rates
- **Sprint Tracking**: Daily burndown updates, velocity alerts

---

## 📊 Collaboration Effectiveness Metrics

### Communication Quality Indicators

| Metric                        | Target           | Measurement Method              | Frequency |
| ----------------------------- | ---------------- | ------------------------------- | --------- |
| **Response Time to Blockers** | < 4 hours        | Slack message timestamps        | Daily     |
| **Standup Attendance**        | 95%+             | Meeting attendance tracking     | Weekly    |
| **Decision Documentation**    | 100%             | ADR and decision channel review | Sprint    |
| **Knowledge Sharing**         | 2+ sessions/week | Learning session tracking       | Weekly    |

### Collaboration Health Metrics

- **Cross-functional Pairing**: Hours spent in collaborative work
- **Code Review Participation**: Percentage of PRs reviewed by each member
- **Help Request/Offer Ratio**: Balance of asking for and offering help
- **Conflict Resolution Time**: Average time to resolve disagreements

### Team Satisfaction Tracking

```
Weekly Team Pulse Survey (5 questions, 2 minutes):
1. How supported do you feel by your teammates? (1-10)
2. How clear are project communications? (1-10)
3. How effective are our meetings and ceremonies? (1-10)
4. How comfortable are you asking for help? (1-10)
5. How confident are you in our sprint success? (1-10)

Additional feedback: [Optional text field]
```

### Continuous Improvement Process

#### Weekly Collaboration Review

**Friday 5:30 PM (15 minutes)**:

- Review collaboration metrics and trends
- Identify communication pain points
- Celebrate collaboration successes
- Plan improvements for following week

#### Monthly Team Health Assessment

- Comprehensive survey with detailed feedback
- One-on-one discussions with Scrum Master
- Team dynamics assessment and adjustment
- Process optimization based on feedback

---

_Team Collaboration Protocols established: September 13, 2025_  
_Version: 1.0_  
_Review cycle: Weekly updates, monthly comprehensive review_  
_Next review: September 20, 2025_
