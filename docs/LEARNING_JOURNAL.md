# 📓 Development Journal: Ossi Voice AI

> **Purpose:** Document the learning journey, challenges, and insights from building a production-grade healthcare voice AI system.

**Author:** Quellin Govender  
**Role:** Senior Chief Product Officer @ M42 Health  
**Started:** January 27, 2026  
**Status:** Phase 2 Complete - Core Intelligence Layer

---

## 🎯 Project Goals

### **Primary Goals**
1. **Demonstrate technical capability** - Show I can build production-grade AI systems, not just manage them
2. **Portfolio piece** - Create something impressive for VP/Director Product roles
3. **Learning mastery** - Deepen understanding of voice AI, LLMs, healthcare compliance
4. **Real-world application** - Solve actual M42 problem (call center efficiency)

### **Success Metrics**
- ✅ Working code that demonstrates production patterns
- ✅ Professional documentation for multiple audiences
- ✅ Technical depth that impresses engineering leaders
- ✅ Business case that resonates with product leaders

---

## 📅 Timeline & Progress

### **Week 1: Foundation (Jan 27-28, 2026)**

#### **Day 1: Setup & Architecture (8 hours)**
- ✅ Project structure design
- ✅ Technology stack decisions (Claude vs GPT-4)
- ✅ Virtual environment setup
- ✅ Git repository initialization

**Key Decision:** Chose Claude over OpenAI
- **Rationale:** Better safety guardrails for healthcare, superior reasoning
- **Trade-off:** Slightly higher latency vs GPT-4, but worth it for clinical safety

**Challenges:**
- SSL certificate issues with pip (Python 3.14 on macOS)
- **Solution:** Created pip.conf with trusted hosts
- **Learning:** macOS Python installations often need certificate installer

#### **Day 2: Configuration & Logging (5 hours)**
- ✅ Type-safe config with Pydantic
- ✅ Structured logging system
- ✅ Environment variable management

**Key Learning:** Pydantic V2 Migration
```python
# OLD (Pydantic V1)
class Config:
    env_file = ".env"

# NEW (Pydantic V2)
model_config = SettingsConfigDict(
    env_file=".env",
    case_sensitive=True
)
```

**Why This Matters:** 
- Pydantic V2 is 5-50x faster
- Better error messages
- Cleaner syntax
- Industry is moving to V2

**Challenges:**
- Module import errors (`ModuleNotFoundError: No module named 'src'`)
- **Solution:** Added path manipulation in files:
```python
  project_root = Path(__file__).parent.parent.parent
  sys.path.insert(0, str(project_root))
```
- **Better Solution:** Use `python -m src.utils.module` for running

---

## 🧠 Technical Deep Dives

### **1. Why Type-Safe Configuration Matters**

**Before:**
```python
import os
api_key = os.getenv("ANTHROPIC_API_KEY")  # Could be None!
threshold = float(os.getenv("THRESHOLD", "0.7"))  # Could crash!
```

**Problems:**
- No validation until runtime
- Silent failures (None values)
- Type errors discovered late
- Hard to debug

**After (Pydantic):**
```python
class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str  # Required - fails fast if missing
    CONFIDENCE_THRESHOLD: float = 0.7  # Type-safe with default
```

**Benefits:**
- Fails at startup (before serving traffic)
- Self-documenting configuration
- IDE autocomplete
- Type safety throughout app

**Real-world impact at M42:**
- Caught 3 production misconfigurations during development
- Would have caused downtime without this pattern
- Now standard across our team

---

### **2. Structured Logging Architecture**

**Why it's critical for healthcare:**

In healthcare AI, you need to answer:
- "What did the AI recommend for patient X?"
- "Why did it escalate this case?"
- "How confident was the model?"
- "What was the conversation history?"

**Traditional logging (insufficient):**
```python
print(f"User {user_id} called at {time}")
```

**Can't answer:**
- Show me all calls from user_456
- What was average confidence today?
- Which calls escalated to humans?

**Structured logging (proper):**
```python
logger.info("Call received", extra={
    "call_id": "call_123",
    "user_id": "user_456",
    "timestamp": time.time(),
    "intent": "appointment"
})
```

**Now you can query:**
```bash
# Show all calls for user_456
grep "user_456" logs.json

# Find low-confidence calls
jq 'select(.confidence < 0.7)' logs.json

# Calculate average latency
jq '.latency_ms' logs.json | awk '{sum+=$1} END {print sum/NR}'
```

**Production value:**
- Debugging: Find issues in 5 minutes instead of 5 hours
- Compliance: Audit trail for every decision
- Analytics: Measure performance metrics
- Monitoring: Alert on anomalies

---

### **3. Claude vs GPT-4: The Decision Process**

**Evaluation Matrix:**

| Criteria | Weight | Claude Sonnet 4 | GPT-4o | Winner |
|----------|--------|----------------|--------|---------|
| Safety guardrails | 30% | 9/10 | 7/10 | Claude |
| Multi-turn reasoning | 25% | 9/10 | 8/10 | Claude |
| Latency (p95) | 15% | 7/10 | 9/10 | GPT-4 |
| Cost per 1M tokens | 20% | 8/10 | 9/10 | GPT-4 |
| Healthcare compliance | 10% | 9/10 | 7/10 | Claude |
| **Weighted Score** | | **8.35** | **7.95** | **Claude** |

**Why safety weighted 30%:**
- Healthcare AI cannot hallucinate medication dosages
- One wrong triage decision could cost a life
- HIPAA penalties are severe ($50K per violation)
- Better to be slightly slower and safe

**Cost analysis:**
- Claude: $3 input / $15 output per 1M tokens
- GPT-4: $2.50 input / $10 output per 1M tokens

**But:** Healthcare conversations average 5K tokens (longer context)
- Claude's better reasoning → fewer retries
- Fewer errors → lower total cost
- **Real cost with retries: Claude ~20% cheaper**

**Final decision:** Claude Sonnet 4

---

## 💡 Key Insights & Learnings

### **Product Management Insights**

**1. Build vs. Buy Decision Framework**

For voice AI, I evaluated:
- **OpenAI Realtime API** (new, voice-native)
- **Twilio + separate STT/TTS** (mature, proven)
- **Custom WebRTC solution** (flexible, complex)

**Decision:** Twilio + OpenAI TTS
- **Why:** Twilio has HIPAA BAA, enterprise support
- **Why not:** OpenAI Realtime doesn't have HIPAA BAA yet
- **Trade-off:** Slightly higher latency, but worth it for compliance

**Learning:** In healthcare, compliance trumps cool technology

---

**2. MVP Scope Definition**

**What I cut:**
- ❌ Multi-language support (focus English first)
- ❌ Voice biometrics (nice-to-have)
- ❌ Outbound calling (future phase)
- ❌ EMR integration (can stub for demo)

**What I kept:**
- ✅ Type-safe configuration (non-negotiable for production)
- ✅ Structured logging (critical for debugging)
- ✅ Red flag detection (safety-critical)
- ✅ Intent classification (core value prop)

**Principle:** "Production foundation first, features second"

This is opposite of typical startup MVP, but correct for healthcare where safety is paramount.

---

**3. Technical Debt as Strategic Decision**

**Intentional shortcuts taken:**
- Using synchronous LLM calls (not async)
- No caching layer yet
- Single-language only
- Mock data instead of real FHIR integration

**Why this is OK:**
- Faster to validate product-market fit
- Can refactor once validated
- Document as known limitations

**When this becomes a problem:**
- >100 concurrent calls (async required)
- >1000 calls/day (caching ROI positive)
- International expansion (multi-language)
- Production deployment (real integrations)

**Learning:** Technical debt is fine if:
1. You document it
2. You have a payoff plan
3. It doesn't compromise safety

---

### **Technical Learnings**

**1. Python Import Hell (And How to Escape It)**

**The Problem:**
```python
from src.utils.config import get_settings
# ModuleNotFoundError: No module named 'src'
```

**Root Cause:** Python doesn't know where project root is

**Solutions (tried all):**

| Solution | Pros | Cons | Use When |
|----------|------|------|----------|
| `sys.path.insert()` | Works everywhere | Hacky | Quick fix |
| `python -m` flag | Pythonic | Longer command | Running modules |
| `PYTHONPATH` env var | Clean | Shell-specific | Development |
| `setup.py` package | Professional | Overkill for portfolio | Production |

**Best practice for portfolio:** Use `python -m src.module.name`

---

**2. Pydantic V2 vs V1 Migration**

**What broke:**
```python
# This worked in V1, fails in V2
class Settings(BaseSettings):
    class Config:
        env_file = ".env"  # Deprecated!
```

**Why it matters:**
- Pydantic V2 is industry standard now
- 5-50x performance improvement
- Better with FastAPI

**Fix:**
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )
```

**Learning:** Stay current with major version updates

---

**3. SSL Certificate Issues on macOS**

**Problem:** `pip install` failing with SSL certificate errors

**Root cause:** macOS Python doesn't trust PyPI certificates by default

**Solutions tried:**
1. ❌ Reinstall Python (too nuclear)
2. ✅ Run `/Applications/Python 3.14/Install Certificates.command`
3. ✅ Create `~/.pip/pip.conf` with trusted hosts

**Best solution:** #2 (proper fix), #3 as fallback

**Learning:** macOS Python quirks are common, document workarounds

---

## 🚧 Challenges & How I Overcame Them

### **Challenge 1: Decision Paralysis (Which LLM?)**

**Problem:** Spent 4 hours researching Claude vs GPT-4 vs Llama

**What helped:**
1. Created weighted decision matrix
2. Set time limit (1 day max)
3. Remembered: "Can change later"

**Outcome:** Claude Sonnet 4

**Learning:** For reversible decisions, bias toward action

---

### **Challenge 2: Scope Creep Temptation**

**Problem:** Wanted to add voice cloning, multi-language, RAG, fine-tuning...

**What helped:**
1. Defined MVP (minimum viable portfolio piece)
2. Created "Phase 2+" backlog
3. Reminded self: "Ship first, enhance later"

**Outcome:** Stayed focused on foundation

**Learning:** Portfolio projects need to demonstrate depth, not breadth

---

### **Challenge 3: Impostor Syndrome**

**Problem:** "Why am I building this? Real engineers already did this better."

**What helped:**
1. Reframed as learning exercise
2. Focused on unique angle (healthcare + product thinking)
3. Remembered: Portfolio shows trajectory, not mastery

**Outcome:** Kept building

**Learning:** Senior PMs aren't expected to be senior engineers—showing capability is enough

---

## 📊 Metrics & Results (So Far)

### **Development Velocity**

| Phase | Estimated | Actual | Variance |
|-------|-----------|--------|----------|
| Setup & Architecture | 4 hrs | 8 hrs | +100% |
| Config & Logging | 3 hrs | 5 hrs | +67% |
| LLM Orchestrator | 6 hrs | TBD | TBD |

**Learnings:**
- Underestimated learning curve (first voice AI project)
- Overestimated familiarity with Python ecosystem
- Debugging took 40% of time

---

### **Code Quality Metrics**
```bash
# Lines of code (excluding comments)
src/: 450 lines
tests/: 0 lines (Phase 3 goal: >80% coverage)
docs/: 2000 lines

# Complexity
- Modules: 4
- Classes: 6
- Functions: 15
- Average cyclomatic complexity: 3.2 (good - under 10)
```

---

### **Documentation Completeness**

- ✅ README.md (professional overview)
- ✅ START_HERE.md (5-min onboarding)
- ✅ ARCHITECTURE.md (technical deep dive)
- ✅ LEARNING_JOURNAL.md (this document)
- 🚧 API_REFERENCE.md (Phase 3)
- 🚧 TESTING.md (Phase 4)

**Goal:** Every hiring manager question has a documented answer

---

## 🎓 Lessons Learned

### **For Product Management**

**1. Document decisions, not just outcomes**
- Hiring managers want to see *how* you think
- Decision logs show strategic thinking
- Trade-offs demonstrate maturity

**2. Build for multiple audiences**
- Execs: Business case (README)
- Engineers: Architecture (ARCHITECTURE.md)
- PMs: Product thinking (PORTFOLIO_NOTES.md)
- Yourself: Learning (LEARNING_JOURNAL.md)

**3. Production patterns from day 1**
- Config, logging, error handling aren't "nice to have"
- They signal "I ship to production"
- Skip them = "I built a toy"

---

### **For Technical Growth**

**1. Best way to learn: Build something real**
- Tutorials teach syntax, projects teach systems
- You don't understand constraints until you hit them
- Debugging is where real learning happens

**2. Choose proven over bleeding-edge**
- Claude > OpenAI GPT-4 (for healthcare)
- FastAPI > Flask (for modern Python)
- PostgreSQL > MongoDB (for healthcare compliance)

**3. Type safety is underrated**
- Pydantic catches bugs at startup
- IDE autocomplete saves hours
- Refactoring becomes safe

---

### **For Career Development**

**1. This project demonstrates:**
- ✅ I can bridge product ↔ engineering
- ✅ I understand production systems
- ✅ I apply domain expertise (healthcare)
- ✅ I document and communicate well

**2. What it doesn't demonstrate (yet):**
- Scalability (1000+ concurrent users)
- Testing (unit + integration + E2E)
- Monitoring & alerting (production ops)
- Team collaboration (solo project)

**Plan:** Add these in Phase 3-5

---

## 🔮 Next Steps

### **Immediate (This Week)**
- [ ] Complete Step 3: LLM Orchestrator
- [ ] Add intent classification
- [ ] Test with real Claude API calls
- [ ] Document prompt engineering decisions

### **Phase 3 (Next 2 Weeks)**
- [ ] Voice integration (Twilio)
- [ ] OpenAI Realtime API for speech
- [ ] Multi-turn conversation handling
- [ ] Demo video recording

### **Phase 4 (Future)**
- [ ] Receptionist module (appointment booking)
- [ ] Triage module (symptom assessment)
- [ ] Testing framework (>80% coverage)
- [ ] CI/CD pipeline

---

## 📚 Resources That Helped

**Technical Resources:**
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/2.0/migration/)
- [Twilio Voice API](https://www.twilio.com/docs/voice)

**Product Resources:**
- M42 internal healthcare AI guidelines
- HIPAA Technical Safeguards documentation
- Healthcare AI safety best practices

**Inspiration:**
- Other voice AI projects on GitHub
- M42's existing AI agent implementations
- Healthcare call center workflow observations

---

## 💭 Reflections

**What surprised me:**
- How much time documentation takes (40% of project)
- How important type safety is (caught 10+ bugs)
- How fun it is to build something tangible

**What I'd do differently:**
- Start with simpler problem (voice AI is complex)
- Timebox research decisions (4 hours max)
- Write tests from day 1 (will add in Phase 3)

**What I'm proud of:**
- Didn't give up when SSL certs failed
- Chose production patterns over quick hacks
- Created portfolio-quality documentation

---

## 🎯 Key Takeaway

**Building this project taught me:** The distance between "understanding a technology" and "shipping production code with that technology" is vast. Reading about LLMs ≠ integrating LLMs ≠ building production LLM systems.

**For my career:** This bridges the credibility gap. I can now say "I don't just manage AI products, I build them" with evidence.

---

*Last Updated: January 28, 2026*  
*Current Status: Phase 2 In Progress - LLM Orchestrator*  
*Total Time Invested: ~15 hours*
