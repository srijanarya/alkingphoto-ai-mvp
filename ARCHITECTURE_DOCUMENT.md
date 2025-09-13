# TalkingPhoto AI MVP - Architecture Document

**Version:** 2.0
**Last Updated:** 2024-12-12
**Status:** Approved for Implementation

---

## Architecture Change Log

| Version | Date       | Changes                        | Reviewed By      |
| ------- | ---------- | ------------------------------ | ---------------- |
| 1.0     | 2024-12-11 | Initial monolithic structure   | -                |
| 2.0     | 2024-12-12 | Modular component architecture | Senior Architect |

---

## System Architecture Overview

### Current Architecture (v1.0)

```
talkingphoto-mvp/
├── app.py (50 lines - monolithic)
└── requirements.txt (streamlit only)
```

### Target Architecture (v2.0)

```
talkingphoto-mvp/
├── app.py                 # Thin controller (50 lines max)
├── requirements.txt       # ONLY: streamlit
├── ui/                    # UI Components
│   ├── __init__.py
│   ├── theme.py          # CSS styling and colors
│   ├── header.py         # Top navigation component
│   ├── footer.py         # Bottom section component
│   ├── create_video.py   # Main feature component
│   └── validators.py     # Input validation logic
├── core/                  # Business Logic
│   ├── __init__.py
│   ├── session.py        # Session state management
│   ├── credits.py        # Credit system logic
│   └── config.py         # Configuration management
└── tests/                 # Test Suite
    ├── test_validators.py
    └── test_components.py
```

---

## Design Principles

### 1. Separation of Concerns

- **UI Layer:** Presentation logic only
- **Core Layer:** Business logic and state
- **No cross-layer dependencies**

### 2. Pure Python Constraint

- **NO C++ dependencies**
- **NO compiled libraries**
- **Streamlit-native solutions only**

### 3. Progressive Enhancement

- **Start with basic functionality**
- **Add features incrementally**
- **Maintain fallbacks**

### 4. Mobile-First Design

- **Responsive by default**
- **Touch-friendly interfaces**
- **Optimized for small screens**

---

## Component Architecture

### UI Components

#### theme.py

```python
def apply_theme():
    """Apply CSS theme to Streamlit app"""
    css = """
    <style>
    :root {
        --primary-color: #ff882e;
        --secondary-color: #1a365d;
        --text-color: #2d3748;
        --bg-color: #f7fafc;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
```

#### validators.py

```python
class FileValidator:
    MAX_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg']

    @staticmethod
    def validate(file) -> tuple[bool, str]:
        """Validate uploaded file"""
        # Pure Python validation logic
        pass
```

### Core Components

#### session.py

```python
class SessionManager:
    """Manage Streamlit session state"""

    @staticmethod
    def init_session():
        if 'credits' not in st.session_state:
            st.session_state.credits = 1

    @staticmethod
    def use_credit() -> bool:
        """Attempt to use a credit"""
        if st.session_state.credits > 0:
            st.session_state.credits -= 1
            return True
        return False
```

---

## Integration Architecture

### Current State: Mock Services

```python
class VideoService:
    def generate(self, photo, text):
        # Mock implementation
        return mock_video_url
```

### Future State: Service Abstraction

```python
class VideoService:
    def __init__(self, provider='mock'):
        self.provider = self._get_provider(provider)

    def generate(self, photo, text):
        return self.provider.generate(photo, text)
```

---

## Security Architecture

### Input Validation

- **File size limits:** 50MB max
- **File type validation:** JPEG, PNG only
- **Content sanitization:** XSS prevention
- **Rate limiting:** Session-based

### Data Privacy

- **No data persistence:** Session-only storage
- **No external calls:** Mock mode only
- **HTTPS only:** Enforced by Streamlit Cloud
- **No user tracking:** Privacy-first

---

## Performance Architecture

### Optimization Strategies

1. **Lazy Loading:** Components load on demand
2. **Caching:** `@st.cache_data` for expensive operations
3. **Minimal Dependencies:** Single package only
4. **CDN Usage:** Static assets via CDN

### Performance Targets

- **Initial Load:** < 3 seconds
- **Interaction Response:** < 100ms
- **Processing Feedback:** < 50ms
- **Memory Usage:** < 100MB

---

## Deployment Architecture

### Streamlit Cloud Configuration

```yaml
# .streamlit/config.toml
[server]
maxUploadSize = 50
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#ff882e"
backgroundColor = "#f7fafc"
secondaryBackgroundColor = "#e2e8f0"
textColor = "#2d3748"
```

### Environment Variables

```
# Secrets management via Streamlit Cloud
# No local .env files in repository
GEMINI_API_KEY=<stored-in-streamlit-secrets>
CLOUDINARY_URL=<stored-in-streamlit-secrets>
DATABASE_URL=<stored-in-streamlit-secrets>
```

---

## Quality Assurance Architecture

### Testing Strategy

```
Unit Tests (70%)
├── Component validation
├── Business logic
└── Utility functions

Integration Tests (20%)
├── Component interaction
└── Session management

E2E Tests (10%)
└── User workflows
```

### Code Quality Gates

- **Linting:** Python style guide compliance
- **Type Hints:** Optional but recommended
- **Documentation:** Docstrings required
- **Test Coverage:** Minimum 80%

---

## Scalability Considerations

### Horizontal Scaling

- **Stateless design:** Ready for multi-instance
- **Session affinity:** Not required
- **CDN compatibility:** Static assets ready

### Vertical Scaling

- **Memory efficient:** Minimal footprint
- **CPU optimized:** No heavy processing
- **Bandwidth conscious:** Compressed assets

---

## Risk Mitigation

### Technical Risks

| Risk                     | Mitigation                          |
| ------------------------ | ----------------------------------- |
| Dependency conflicts     | Single dependency policy            |
| Deployment failures      | Staging environment testing         |
| Performance issues       | Continuous monitoring               |
| Security vulnerabilities | Input validation, no external calls |

### Architectural Decisions Record (ADR)

#### ADR-001: Pure Python Only

**Decision:** No C++ or compiled dependencies
**Rationale:** Deployment stability on Streamlit Cloud
**Consequences:** Limited image processing capabilities

#### ADR-002: Modular Structure

**Decision:** Separate UI and core logic
**Rationale:** Maintainability and testability
**Consequences:** Slightly more complex file structure

#### ADR-003: Mock-First Development

**Decision:** All features work with mock data initially
**Rationale:** Ensure UI/UX perfection before integration
**Consequences:** Delayed real functionality

---

## Future Architecture Evolution

### Phase 2: Service Integration

- Add service abstraction layer
- Integrate Gemini API
- Connect Cloudinary storage
- Implement Supabase tracking

### Phase 3: Microservices

- Separate video processing service
- Independent payment service
- Analytics microservice
- API gateway pattern

---

## Compliance & Standards

### Standards Compliance

- **WCAG 2.1 AA:** Accessibility
- **GDPR:** Privacy compliance
- **ISO 27001:** Security practices
- **PCI DSS:** Payment handling (future)

### Code Standards

- **PEP 8:** Python style guide
- **Type Hints:** Where beneficial
- **Docstrings:** Google style
- **Comments:** Explain why, not what

---

**Document Owner:** Senior Architect
**Review Cycle:** Per significant change
**Distribution:** Development Team
