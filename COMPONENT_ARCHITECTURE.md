# TalkingPhoto MVP - Component Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     TALKINGPHOTO AI MVP                         │
│                    (Pure Streamlit Stack)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         app.py                                  │
│                    (Main Entry Point)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • Page Configuration                                    │  │
│  │  • Session Initialization                                │  │
│  │  • Theme Application                                     │  │
│  │  • Component Orchestration                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
        │               │                │               │
        ▼               ▼                ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   UI Layer   │ │  Core Layer  │ │  Validators  │ │   Assets     │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘

```

## Detailed Component Breakdown

### 1. UI Components Layer

```
ui/
├── __init__.py
├── theme.py ──────────────┐
│   └── apply_theme()      │ Applies CSS styling
│                          │
├── header.py ─────────────┤
│   └── render_header()    │ Top navigation & branding
│                          │
├── footer.py ─────────────┤
│   └── render_footer()    │ Links & copyright
│                          │
├── create_video.py ───────┤
│   ├── render_upload()    │ Main functionality
│   ├── render_text()      │
│   └── render_generate()  │
│                          │
├── pricing.py ────────────┤
│   └── render_pricing()   │ Pricing display
│                          │
└── validators.py ─────────┘
    ├── validate_photo()
    ├── validate_text()
    └── validate_email()
```

### 2. Core Business Logic Layer

```
core/
├── __init__.py
├── session.py ────────────┐
│   ├── initialize()       │ State management
│   ├── get()              │
│   ├── set()              │
│   └── use_credit()       │
│                          │
├── credits.py ────────────┤
│   ├── check_credits()    │ Credit system
│   ├── deduct_credit()    │
│   └── add_credits()      │
│                          │
└── config.py ─────────────┘
    ├── APP_CONFIG         Configuration
    ├── LIMITS
    └── FEATURES
```

### 3. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Input Validation                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Photo: Size, Type, Dimensions                     │    │
│  │  Text: Length, Content, Language                   │    │
│  │  Email: Format, Domain                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Session State                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Credits: Available, Used, History                 │    │
│  │  User: Auth, Preferences, Settings                 │    │
│  │  Video: Current, Queue, Generated                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Processing Pipeline                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  1. Validate Inputs                                │    │
│  │  2. Check Credits                                  │    │
│  │  3. Process Request                                │    │
│  │  4. Generate Output                                │    │
│  │  5. Update State                                   │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 4. Component Interaction Flow

```
User Action
    │
    ▼
app.py (Controller)
    │
    ├──► theme.py (Apply Styling)
    │
    ├──► header.py (Render Header)
    │
    ├──► Tab Selection
    │    │
    │    ├──► create_video.py
    │    │    │
    │    │    ├──► validators.py (Input Check)
    │    │    │
    │    │    ├──► session.py (State Check)
    │    │    │
    │    │    ├──► credits.py (Credit Check)
    │    │    │
    │    │    └──► Generate Video
    │    │
    │    ├──► pricing.py
    │    │
    │    └──► Other Tabs
    │
    └──► footer.py (Render Footer)
```

### 5. State Management Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   st.session_state                          │
├─────────────────────────────────────────────────────────────┤
│  User State        │  App State         │  UI State        │
├────────────────────┼────────────────────┼──────────────────┤
│  • credits: int    │  • theme: str      │  • tab: str      │
│  • user_id: str    │  • version: str    │  • modal: bool   │
│  • auth: bool      │  • features: dict  │  • loading: bool │
│  • tier: str       │  • limits: dict    │  • error: str    │
└────────────────────┴────────────────────┴──────────────────┘
```

### 6. Service Integration Points (Future)

```
Current (Phase 1) - Mock Implementation
┌─────────────────────────────────────────────────────────────┐
│                    Mock Services                            │
├─────────────────────────────────────────────────────────────┤
│  generate_video()  → Returns sample video                   │
│  process_image()   → Returns processed image                │
│  create_audio()    → Returns sample audio                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
Future (Phase 2) - Service Integration
┌─────────────────────────────────────────────────────────────┐
│                 Service Abstraction Layer                   │
├─────────────────────────────────────────────────────────────┤
│  VideoService      → Gemini API                             │
│  StorageService    → Cloudinary                             │
│  AuthService       → Supabase                               │
│  PaymentService    → Stripe/Razorpay                        │
└─────────────────────────────────────────────────────────────┘
```

### 7. Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Error Detection                          │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        Validation Error  Process Error  System Error
                │             │             │
                ▼             ▼             ▼
        st.error()      st.warning()   st.exception()
                │             │             │
                ▼             ▼             ▼
        User Feedback   Retry Option   Fallback Mode
```

### 8. Progressive Enhancement Strategy

```
Phase 1: Core MVP (Current)
├── Basic UI with Theme
├── Input Validation
├── Mock Video Generation
└── Session Management

Phase 2: Enhanced Features
├── Real Video Generation
├── User Authentication
├── Payment Integration
└── Cloud Storage

Phase 3: Advanced Features
├── AI Voice Selection
├── Multi-language Support
├── Video Templates
└── Analytics Dashboard
```

### 9. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Streamlit Cloud                           │
├─────────────────────────────────────────────────────────────┤
│  Repository: GitHub                                         │
│  Branch: main                                               │
│  Entry: app.py                                              │
│  Dependencies: requirements.txt (streamlit only)            │
│  Config: .streamlit/config.toml                             │
│  Secrets: .streamlit/secrets.toml (future)                  │
└─────────────────────────────────────────────────────────────┘
```

### 10. Testing Architecture

```
tests/
├── test_validators.py
│   ├── test_photo_validation()
│   ├── test_text_validation()
│   └── test_email_validation()
│
├── test_session.py
│   ├── test_initialization()
│   ├── test_credit_system()
│   └── test_state_management()
│
├── test_ui_components.py
│   ├── test_header_render()
│   ├── test_footer_render()
│   └── test_video_creation()
│
└── test_integration.py
    ├── test_full_flow()
    ├── test_error_handling()
    └── test_mobile_responsive()
```

### 11. Monitoring & Observability (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Metrics           │  Logs              │  Traces          │
├────────────────────┼────────────────────┼──────────────────┤
│  • Page Views      │  • Error Logs      │  • User Journey  │
│  • Generation Time │  • Access Logs     │  • API Calls     │
│  • Success Rate    │  • Debug Logs      │  • Performance   │
└────────────────────┴────────────────────┴──────────────────┘
```

## Component Responsibilities

### Critical Path Components

1. **app.py** - Orchestrator, must remain lightweight
2. **validators.py** - Gate keeper, prevents bad data
3. **session.py** - State manager, maintains consistency
4. **theme.py** - Visual consistency across app

### Supporting Components

1. **header.py** - Branding and navigation
2. **footer.py** - Legal and links
3. **create_video.py** - Core feature implementation
4. **pricing.py** - Monetization display

### Future Integration Points

1. **services/** - External API integrations
2. **models/** - Data models for backend
3. **utils/** - Shared utilities
4. **api/** - Backend API client

## Architectural Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Dependency Injection**: Components receive dependencies, don't create them
3. **Fail Safe**: All operations have fallbacks
4. **Progressive Enhancement**: Features added without breaking existing
5. **Pure Functions**: Where possible, no side effects
6. **Explicit State**: All state changes are explicit and trackable

## Anti-Patterns to Avoid

❌ **Don't**: Mix UI and business logic in same function
✅ **Do**: Separate presentation from logic

❌ **Don't**: Use global variables for state
✅ **Do**: Use st.session_state exclusively

❌ **Don't**: Import heavy libraries unnecessarily
✅ **Do**: Keep dependencies minimal

❌ **Don't**: Create deep component nesting
✅ **Do**: Keep hierarchy flat and simple

---

_Architecture Version: 1.0_
_Pattern: MVC-lite for Streamlit_
_Complexity: Low_
_Maintainability: High_
