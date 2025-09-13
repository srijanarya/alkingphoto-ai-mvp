# TalkingPhoto AI MVP - Project Requirements Document (PRD)

**Version:** 2.0
**Last Updated:** 2024-12-12
**Status:** In Development

---

## Document Change Log

| Version | Date       | Changes                      | Approved By                 |
| ------- | ---------- | ---------------------------- | --------------------------- |
| 1.0     | 2024-12-11 | Initial MVP deployment       | PM                          |
| 2.0     | 2024-12-12 | UI/UX Enhancement Epic added | PM, Architect, Scrum Master |

---

## Executive Summary

TalkingPhoto AI is an AI-powered web application that transforms static photos into talking videos. The MVP focuses on demonstrating core functionality with a professional, user-friendly interface optimized for mobile users in the Indian market.

---

## Current State (v1.0 - Deployed)

### Technical Stack

- **Framework:** Streamlit
- **Dependencies:** streamlit (only)
- **Deployment:** Streamlit Cloud
- **Code Size:** 50 lines
- **Status:** ✅ Live and working

### Core Features

1. Photo upload interface
2. Text input for script
3. Mock video generation
4. Credit system (1 free)
5. Basic pricing display

---

## Approved Changes (v2.0 - In Development)

### Epic: UI/UX Enhancement

#### Approved Features

1. **Visual Identity Enhancement**
   - Orange (#ff882e) and Deep Blue (#1a365d) color scheme
   - Professional typography (Libre Franklin, Manrope)
   - Consistent spacing and layout

2. **User Experience Optimization**
   - Native progress indicators
   - Input validation with friendly errors
   - Processing feedback system
   - Professional header/footer

#### Architecture Requirements

- **Modular component structure**
- **Pure Python/Streamlit only**
- **No C++ dependencies**
- **Progressive enhancement approach**

#### Technical Constraints

- Maximum file size: 200MB (Streamlit limit)
- Session timeout: 30 minutes
- Concurrent users: 100 (free tier)
- Memory limit: 1GB

---

## Deferred Features (Future Phases)

### Phase 2 (Month 2)

- Gemini API integration
- Cloudinary storage
- Supabase user tracking
- Basic lip-sync APIs
- WhatsApp sharing

### Phase 3 (Month 3)

- Payment integration (Razorpay/Stripe)
- Multi-language support (Hindi, Tamil)
- Advanced video generation
- User accounts
- API access

---

## Success Metrics

### Technical KPIs

- Deployment success rate: 100%
- Page load time: < 3 seconds
- Error rate: < 1%
- Mobile usability: > 80%

### Business KPIs

- User session duration: > 2 minutes
- Completion rate: > 90%
- NPS score: > 8
- Return rate: > 15%

---

## Risk Register

| Risk                    | Probability | Impact | Mitigation                         |
| ----------------------- | ----------- | ------ | ---------------------------------- |
| Deployment failure      | Low         | High   | Test in staging, maintain rollback |
| CSS conflicts           | Medium      | Medium | Use Streamlit patterns             |
| Mobile issues           | Low         | Medium | Progressive enhancement            |
| Performance degradation | Low         | Low    | Monitor metrics                    |

---

## Approval Chain

### Required Approvals for Changes

1. **Project Manager** - Business alignment
2. **Architect** - Technical feasibility
3. **Scrum Master** - Sprint planning
4. **Developer Lead** - Implementation approach
5. **QA Lead** - Testing strategy

### Current Approvals

- ✅ UI/UX Enhancement Epic - Approved by PM, Architect, Scrum Master
- ⏳ Implementation - Pending developer review

---

## Dependencies

### Allowed Dependencies

```txt
streamlit
python-dotenv (if needed)
```

### Forbidden Dependencies

```txt
opencv-python
pillow-heif
numpy
tensorflow
Any C++ based libraries
```

---

## Communication Plan

### Stakeholders

- Product Owner: Strategic decisions
- Development Team: Implementation
- QA Team: Testing
- Users: Feedback collection

### Update Frequency

- Daily: Standup updates
- Weekly: Progress reports
- Sprint: Review and retrospective

---

## Appendices

### A. UI/UX Research Report

- Competitor analysis completed
- Best practices identified
- Mobile-first patterns documented

### B. Architecture Documents

- Component structure defined
- Integration patterns established
- Security guidelines documented

### C. Testing Strategy

- Unit test coverage: 70%
- Integration tests: 20%
- E2E tests: 10%

---

**Document Owner:** Project Manager
**Review Cycle:** Sprint-based
**Distribution:** Development Team, Stakeholders
