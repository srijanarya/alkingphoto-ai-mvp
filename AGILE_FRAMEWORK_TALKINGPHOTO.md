# TalkingPhoto MVP - Agile Framework & Scrum Master Guide

## 🎯 Sprint Overview & Context

**Product**: TalkingPhoto MVP - AI-powered talking video generation platform  
**Timeline**: 14-day sprint implementation (2 x 7-day sprints)  
**Business Goal**: Launch MVP with ₹7.5L MRR target within 8 weeks  
**Technical Stack**: Streamlit, HeyGen API, Google Nano Banana, Stripe integration

---

## 🤝 Team Working Agreement

### Core Team Structure

| Role                     | Name            | Capacity | Primary Responsibilities                        |
| ------------------------ | --------------- | -------- | ----------------------------------------------- |
| **Scrum Master**         | Claude AI       | 100%     | Process facilitation, impediment removal        |
| **Product Owner**        | Product Manager | 60%      | Backlog prioritization, stakeholder management  |
| **Tech Lead**            | Lead Developer  | 80%      | Architecture, code reviews, technical decisions |
| **Full-Stack Developer** | Developer 1     | 80%      | Feature implementation, API integration         |
| **Frontend Developer**   | Developer 2     | 80%      | UI/UX implementation, Streamlit optimization    |
| **QA Engineer**          | QA Specialist   | 60%      | Testing, quality assurance, user acceptance     |

### Working Hours & Availability

- **Core Hours**: 10:00 AM - 4:00 PM IST (overlap for collaboration)
- **Daily Standup**: 10:00 AM IST (15 minutes)
- **Focused Development**: 11:00 AM - 1:00 PM and 2:30 PM - 5:30 PM
- **Code Review Time**: 5:30 PM - 6:00 PM
- **Emergency Availability**: Team lead available until 8:00 PM

### Communication Protocols

1. **Urgent Issues**: Slack direct message + immediate escalation
2. **Blockers**: Report in standup + Slack #talkingphoto-blockers channel
3. **Code Reviews**: GitHub PRs with 24-hour review SLA
4. **Stakeholder Updates**: Daily progress reports via email
5. **Technical Decisions**: Documented in #talkingphoto-decisions channel

---

## ✅ Definition of Done (DoD) Criteria

### Story-Level DoD

Every user story must meet ALL criteria before marking as complete:

#### 🔧 Development Complete

- [ ] All acceptance criteria implemented and functioning
- [ ] Code follows established coding standards and patterns
- [ ] Unit tests written with 90%+ coverage for business logic
- [ ] Integration tests cover component interactions
- [ ] Error handling implemented for all edge cases
- [ ] Performance requirements met (< 2s photo processing, < 30s video)

#### 🧪 Quality Assurance

- [ ] Manual testing completed for happy path and edge cases
- [ ] Cross-browser testing (Chrome, Firefox, Safari, Edge)
- [ ] Mobile responsiveness verified on 3+ devices
- [ ] Accessibility compliance (WCAG AA) validated
- [ ] Security review completed (input validation, XSS prevention)
- [ ] Performance benchmarks met and documented

#### 📚 Documentation & Review

- [ ] Code peer reviewed and approved by 2+ team members
- [ ] API documentation updated (if applicable)
- [ ] User-facing changes documented in release notes
- [ ] Technical debt items logged if introduced
- [ ] Monitoring/logging implemented for production tracking

#### 🚀 Deployment Ready

- [ ] Feature tested in staging environment
- [ ] Environment configurations validated
- [ ] Rollback plan documented and tested
- [ ] Production deployment checklist completed
- [ ] Post-deployment verification plan ready

### Sprint-Level DoD

Complete sprint success requires:

#### 📊 Sprint Completion

- [ ] Sprint goal achieved (90%+ of committed story points)
- [ ] All stories meet individual DoD criteria
- [ ] Sprint demo successfully presented to stakeholders
- [ ] User acceptance testing passed with 85%+ satisfaction
- [ ] No critical bugs remaining in sprint scope

#### 🎯 Business Value Delivered

- [ ] Feature functionality aligns with business objectives
- [ ] User feedback collected and analyzed
- [ ] Key performance indicators show positive trend
- [ ] Revenue impact pathway clearly demonstrated
- [ ] Next sprint priorities validated by Product Owner

---

## 📈 Sprint Velocity Tracking

### Velocity Calculation Method

**Velocity = Total Story Points Completed ÷ Sprint Duration**

#### Historical Baseline (Estimated)

- **Estimated Team Velocity**: 35-42 story points per week
- **Sprint 1 Target**: 38 story points (foundation & integration)
- **Sprint 2 Target**: 42 story points (polish & production readiness)
- **Velocity Buffer**: 15% capacity reserved for unknown unknowns

#### Velocity Tracking Metrics

```
Sprint Burndown Formula:
- Day 0: Total committed points
- Daily: Remaining points = Total - Completed points
- Ideal burndown line: Linear decrease to zero
- Actual vs. ideal variance tracking
```

#### Velocity Factors & Adjustments

| Factor                         | Impact    | Mitigation                           |
| ------------------------------ | --------- | ------------------------------------ |
| **Streamlit Learning Curve**   | -5 points | Pair programming, documentation      |
| **API Integration Complexity** | -3 points | Early prototyping, fallback plans    |
| **Team Coordination**          | +2 points | Strong communication protocols       |
| **Clear Requirements**         | +3 points | Detailed PRD and acceptance criteria |

---

## 🚫 Impediment Log & Resolution Process

### Impediment Classification

#### 🔴 Critical (< 4 hours resolution)

- Production system down
- Complete team blocked
- API service completely unavailable
- Security vulnerability discovered

#### 🟡 High (< 24 hours resolution)

- Individual developer blocked
- Test environment issues
- Third-party service degradation
- Requirements clarification needed

#### 🟢 Medium (< 72 hours resolution)

- Process improvements needed
- Tool/environment optimization
- Non-critical bug fixes
- Documentation gaps

### Impediment Resolution Framework

#### Step 1: Identification & Logging

```
Impediment ID: IMP-YYYY-MM-DD-XXX
Reporter: [Team Member]
Date/Time: [Timestamp]
Severity: [Critical/High/Medium/Low]
Description: [What is blocked and impact]
Current Workaround: [If any]
Owner: [Who will resolve]
Target Resolution: [Date/time]
```

#### Step 2: Escalation Path

1. **Team Level** (0-2 hours): Team self-resolution attempt
2. **Scrum Master** (2-8 hours): Process facilitation and resource coordination
3. **Technical Lead** (8-24 hours): Technical decision making and architecture guidance
4. **Product Owner** (24+ hours): Business priority and scope decisions
5. **Stakeholder** (48+ hours): External dependency resolution

#### Step 3: Resolution Tracking

- **Daily Review**: All open impediments reviewed in standup
- **Progress Updates**: Real-time updates in #talkingphoto-blockers channel
- **Resolution Documentation**: Root cause and prevention measures logged
- **Process Improvement**: Retrospective analysis for prevention

---

## 🛠️ Team Collaboration Tools Setup

### Primary Tool Stack

#### Development & Code Management

- **GitHub**: Source control, code reviews, issue tracking
- **VS Code**: Primary IDE with shared extensions/settings
- **Docker**: Consistent development environments
- **Streamlit Cloud**: Staging environment for testing

#### Communication & Collaboration

- **Slack**:
  - #talkingphoto-general (daily communication)
  - #talkingphoto-blockers (impediment tracking)
  - #talkingphoto-decisions (technical decisions)
  - #talkingphoto-alerts (automated notifications)
- **Zoom**: Daily standups, sprint ceremonies, pair programming
- **Miro**: Sprint planning, retrospectives, architecture diagrams
- **Google Workspace**: Shared documentation, calendar coordination

#### Project Management & Tracking

- **GitHub Projects**: Sprint board, backlog management
- **GitHub Issues**: User story tracking with labels
- **Google Sheets**: Velocity tracking, metrics dashboard
- **Confluence**: Knowledge base, technical documentation

### Tool Configuration Checklist

- [ ] GitHub repository access for all team members
- [ ] Slack channels created with proper permissions
- [ ] Zoom recurring meetings scheduled
- [ ] Miro workspace set up with templates
- [ ] GitHub Projects board configured with sprint columns
- [ ] Issue templates created for bugs, features, spikes
- [ ] Automated notifications configured (GitHub → Slack)
- [ ] Shared calendar with all ceremony times

---

## 🗣️ Daily Standup Format & Questions

### Standup Structure (15 minutes max)

#### Format: Round-Robin + Focus Areas

**Time**: 10:00 AM IST Daily  
**Duration**: 15 minutes maximum  
**Participants**: Core development team only  
**Location**: Zoom (backup: async in Slack)

#### Standard Three Questions

1. **What did you accomplish yesterday?**
   - Specific completed work with story IDs
   - Key milestones or breakthroughs achieved
   - Any deliverables ready for review

2. **What will you work on today?**
   - Specific tasks planned with time estimates
   - Dependencies on other team members
   - Expected deliverables by end of day

3. **Are there any impediments or blockers?**
   - Current blockers preventing progress
   - Potential future blockers anticipated
   - Help needed from other team members

#### Enhanced Focus Areas (Rotating Daily)

**Monday**: Sprint goal alignment and weekly planning  
**Tuesday**: Technical architecture and integration points  
**Wednesday**: Quality assurance and testing progress  
**Thursday**: Stakeholder feedback and business value  
**Friday**: Sprint progress and weekend handoff

#### Standup Anti-Patterns to Avoid

❌ **Status reporting to Scrum Master**  
✅ **Team coordination and collaboration**

❌ **Detailed technical discussions**  
✅ **Identifying issues for offline discussion**

❌ **Problem solving in standup**  
✅ **Committing to offline problem resolution**

❌ **Going over 15 minutes**  
✅ **Parking lot for extended discussions**

### Standup Effectiveness Metrics

- **Attendance Rate**: Target 95%+ team participation
- **Duration**: Target 12-15 minutes average
- **Blocker Resolution**: Target 80% resolved within 24 hours
- **Team Satisfaction**: Monthly survey targeting 8/10 satisfaction

---

## 🔄 Sprint Retrospective Framework

### Retrospective Structure (60 minutes)

#### Sprint 1 Retrospective (End of Week 1)

**Focus**: Foundation establishment and team dynamics

**Agenda**:

1. **Check-in** (5 minutes): Team mood and energy
2. **Data Gathering** (15 minutes): What happened?
3. **Generate Insights** (20 minutes): Why did it happen?
4. **Decide Actions** (15 minutes): What will we do differently?
5. **Close** (5 minutes): Action item commitment

#### Sprint 2 Retrospective (End of Week 2)

**Focus**: MVP completion and production readiness

**Agenda**:

1. **Check-in** (5 minutes): Achievement celebration
2. **MVP Review** (10 minutes): Feature completeness assessment
3. **Process Evaluation** (20 minutes): What worked/didn't work
4. **Lessons Learned** (15 minutes): Knowledge capture for future sprints
5. **Next Steps** (10 minutes): Post-MVP planning and handoff

### Retrospective Techniques by Sprint

#### Week 1: "Start, Stop, Continue"

- **Start**: What should we begin doing?
- **Stop**: What should we stop doing?
- **Continue**: What's working well that we should keep doing?

#### Week 2: "Mad, Sad, Glad"

- **Mad**: What frustrated us or blocked progress?
- **Sad**: What disappointed us or didn't meet expectations?
- **Glad**: What made us happy or exceeded expectations?

### Action Item Framework

```
Action Item Template:
- What: Specific action to implement
- Why: Root cause or opportunity
- Who: Owner (not group ownership)
- When: Target completion date
- How: Concrete steps to implement
- Measure: Success criteria
```

#### Action Item Categories

1. **Process Improvements**: Team workflow enhancements
2. **Technical Debt**: Code quality and architecture improvements
3. **Tool Optimization**: Development environment improvements
4. **Communication Enhancement**: Information flow improvements
5. **Skill Development**: Team capability building

---

## 📊 Agile Metrics & KPIs

### Sprint-Level Metrics

#### Velocity & Capacity

- **Planned vs. Actual Velocity**: Story points committed vs completed
- **Capacity Utilization**: Hours planned vs hours logged
- **Velocity Trend**: Week-over-week velocity tracking
- **Commitment Reliability**: Percentage of committed work completed

#### Quality Metrics

- **Defect Rate**: Bugs per story point delivered
- **Rework Rate**: Percentage of work requiring rework
- **Code Review Efficiency**: Time from PR creation to merge
- **Test Coverage**: Percentage of code covered by automated tests

#### Flow Metrics

- **Lead Time**: Idea to production deployment time
- **Cycle Time**: Development start to completion time
- **Throughput**: Stories completed per sprint
- **Work in Progress**: Number of active stories per developer

### Business Impact Metrics

#### User Value Delivery

- **Feature Adoption**: Percentage of users engaging with new features
- **User Satisfaction**: Post-feature surveys and NPS scores
- **Business Value**: Revenue impact or cost savings delivered
- **Time to Market**: Feature conception to user availability

#### Technical Health

- **System Performance**: API response times and uptime
- **Technical Debt**: Code complexity and maintainability scores
- **Security Posture**: Vulnerability count and resolution time
- **Scalability Readiness**: Performance under increased load

### Metrics Dashboard Structure

```
Daily Metrics:
- Sprint burndown progress
- Impediment count and age
- Code review queue length
- Test pass/fail rates

Weekly Metrics:
- Velocity achievement
- Quality gate compliance
- Team happiness scores
- Stakeholder satisfaction

Sprint Metrics:
- Goal achievement percentage
- Business value delivered
- Technical debt incurred
- Process improvement actions
```

---

## 🎉 Success Celebration & Recognition

### Milestone Celebrations

#### Sprint 1 Success Criteria

**Technical Achievements**:

- [ ] Photo enhancement pipeline working end-to-end
- [ ] Video generation integrated with HeyGen API
- [ ] User authentication and billing system functional
- [ ] Export workflow system providing value to users

**Team Achievements**:

- [ ] Team velocity within 10% of target (38 points)
- [ ] All stories meet Definition of Done
- [ ] Zero critical bugs in production
- [ ] Stakeholder satisfaction score ≥ 8/10

**Celebration**: Team dinner and individual recognition for standout contributions

#### Sprint 2 Success Criteria

**Product Achievements**:

- [ ] MVP fully functional and production-ready
- [ ] User acceptance testing passed with ≥ 85% satisfaction
- [ ] Performance benchmarks met (< 2s photo, < 30s video)
- [ ] Business metrics on track (initial user signups and conversions)

**Team Achievements**:

- [ ] Sprint velocity achieved or exceeded (42 points)
- [ ] Complete MVP delivered on time
- [ ] High team satisfaction scores (≥ 8/10)
- [ ] Successful knowledge transfer to operations team

**Celebration**: Company-wide demo, team achievement awards, individual bonuses

### Recognition Framework

#### Individual Recognition Categories

1. **Technical Excellence**: Outstanding code quality and innovation
2. **Team Collaboration**: Exceptional support and knowledge sharing
3. **Problem Solving**: Creative solutions to complex challenges
4. **User Focus**: Exceptional attention to user experience
5. **Process Innovation**: Improvements to team efficiency

#### Team Recognition Metrics

- **Velocity Achievement**: Consistent delivery of committed work
- **Quality Excellence**: Low defect rates and high test coverage
- **Collaboration Effectiveness**: Strong cross-functional working
- **Innovation Impact**: Technical or process improvements implemented
- **Stakeholder Satisfaction**: High ratings from Product Owner and users

### Post-MVP Success Tracking

#### 30-Day Success Metrics

- **User Adoption**: Active user count and engagement levels
- **Revenue Generation**: Initial revenue and conversion rates
- **System Stability**: Uptime and performance in production
- **User Feedback**: Customer satisfaction and feature requests

#### Knowledge Sharing Plan

- **Technical Documentation**: Architecture and implementation guides
- **Process Documentation**: Agile practices and lessons learned
- **Training Materials**: Onboarding guides for future team members
- **Best Practices**: Reusable patterns and templates

---

## 🔧 Continuous Improvement Framework

### Process Optimization Cycle

#### Weekly Improvement Reviews

- **Metrics Analysis**: Review velocity, quality, and satisfaction trends
- **Process Gaps**: Identify workflow inefficiencies
- **Tool Optimization**: Evaluate and improve development tools
- **Team Feedback**: Collect ongoing improvement suggestions

#### Sprint-Level Improvements

- **Retrospective Actions**: Implement agreed improvements
- **Process Experiments**: Try new approaches with defined success criteria
- **Tool Upgrades**: Adopt new tools or upgrade existing ones
- **Training Initiatives**: Address skill gaps identified

### Learning & Development

#### Technical Skills Development

- **AI Integration**: Advanced API usage and optimization
- **Streamlit Mastery**: Advanced UI/UX patterns and performance
- **Cloud Deployment**: Production deployment and monitoring
- **Quality Assurance**: Advanced testing and quality practices

#### Agile Skills Development

- **Facilitation**: Improved ceremony facilitation skills
- **Estimation**: More accurate story point estimation
- **Communication**: Enhanced stakeholder and team communication
- **Problem Solving**: Systematic impediment resolution

### Success Metrics for Continuous Improvement

- **Process Efficiency**: Reduction in waste and rework
- **Team Satisfaction**: Consistent high satisfaction scores
- **Delivery Predictability**: Improved estimation accuracy
- **Quality Improvement**: Sustained reduction in defect rates

---

_Agile Framework established: September 13, 2025_  
_Scrum Master: Claude AI Assistant_  
_Team: TalkingPhoto MVP Development Team_  
_Sprint Goal: Launch production-ready MVP in 14 days_

**Next Actions:**

1. Team working agreement sign-off
2. Tool setup and configuration
3. Sprint 1 planning ceremony
4. Daily standup schedule establishment
5. Impediment tracking system activation
