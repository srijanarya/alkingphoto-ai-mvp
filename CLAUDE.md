# TalkingPhoto AI - AI Assistant Development Guide

## Project Overview
TalkingPhoto AI is a Streamlit-based web application that transforms static photos into talking videos using AI technology. The UI/UX is inspired by premium SaaS products like sunmetalon.com and heimdallpower.com.

## Critical UI/UX Requirements

### ⚠️ MUST FOLLOW - UI Consistency Rules

1. **COLOR CONSISTENCY IS MANDATORY**
   - Navigation text MUST be white (#ece7e2), NEVER blue
   - Orange (#d96833) is ONLY for hover states and CTAs
   - Check UI_CONSISTENCY_GUIDE.md before ANY changes

2. **HOVER EFFECTS ARE REQUIRED**
   - Every interactive element MUST have a hover state
   - Cards must lift and text must turn orange on hover
   - Input fields must show orange border on hover

3. **NO STREAMLIT DEFAULTS**
   - Override ALL default Streamlit blue colors
   - Custom style ALL components to match our theme

## Before Making ANY UI Changes

1. **Read UI_CONSISTENCY_GUIDE.md** - This is your bible for UI consistency
2. **Check existing components** for patterns to follow
3. **Test all hover states** before committing
4. **Verify no blue text** appears anywhere

## File Structure

```
/Users/srijan/alkingphoto-ai-mvp/
├── app.py                    # Main application
├── ui_theme.py              # ALL styling lives here
├── UI_CONSISTENCY_GUIDE.md  # UI/UX rules and checklist
├── CLAUDE.md               # This file - AI assistant guide
└── requirements.txt         # Dependencies
```

## Common Tasks & How to Handle Them

### Adding a New Component
1. First check `ui_theme.py` for similar component styles
2. Copy the pattern, don't create new inconsistent styles
3. Ensure hover effects match existing components
4. Test thoroughly before committing

### Fixing UI Inconsistencies
1. User reports often focus on:
   - Wrong colors (especially blue text)
   - Missing hover effects
   - Inconsistent borders or shadows
2. Always fix in `ui_theme.py`, not with inline styles
3. Use `!important` if needed to override Streamlit defaults

### Navigation & Scrolling Issues
- All navigation must use smooth scrolling
- Check ID anchors match between navigation and sections
- Use `scroll-margin-top` for proper positioning

## Testing Checklist for EVERY Change

```bash
# After any UI modification:
1. Check all text is white (not blue)
2. Test all hover states work
3. Verify orange appears only on hover/active
4. Test navigation scrolling
5. Check mobile responsiveness
```

## Git Commit Standards

Always use descriptive commits:
```bash
git commit -m "fix: [specific issue]
- [what was changed]
- [why it was changed]
- [impact on UX]"
```

## Known Issues & Solutions

| Issue | Solution |
|-------|----------|
| Blue text appearing | Add `!important` to color CSS |
| Hover not working | Check z-index and pointer-events |
| Navigation not scrolling | Verify ID anchors and JavaScript |
| Inconsistent styling | Check UI_CONSISTENCY_GUIDE.md |

## Priority Order for Development

1. **UI Consistency** - Fix any reported inconsistencies immediately
2. **User Experience** - Smooth interactions and feedback
3. **Functionality** - Features work as expected
4. **Performance** - Optimize after everything works

## References & Inspiration

- **Primary Reference**: sunmetalon.com (fonts, navigation style)
- **Secondary Reference**: heimdallpower.com (clean design)
- **Color Scheme**: Dark theme with orange accents
- **Typography**: Space Grotesk + Syne fonts

## Contact & Repository

- **Repository**: https://github.com/srijanarya/alkingphoto-ai-mvp
- **Live Demo**: [Streamlit deployment URL]

## Remember

> "Consistency creates trust. Every pixel matters. If the user notices an inconsistency, we've failed."

Always prioritize UI consistency over new features. A polished, consistent UI with fewer features is better than a feature-rich app with inconsistent design.

---

**Last Updated**: 2024-01-15
**Version**: 1.0.0