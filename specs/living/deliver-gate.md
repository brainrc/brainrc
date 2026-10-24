# deliver-gate

What must happen before a run's outward actions are allowed.

### Understand quiz before Deliver
The system SHALL quiz the run's owner with questions, each with 3–4 choices and asked in a pop-up where available, from the read-only examiner role (or the engine in inline/fallback mode), sized by tier plus one risk question per touched trigger, before presenting the Deliver gate, for every size and unattended runs too. (AC1, AC2, AC3, AC8)
_Last changed by 069-deliver-owner-quiz._

### Quiz grading and approval
The system SHALL grade each pick against the diff, explain a wrong pick with a `file:line` pointer and re-ask a rephrased question with fresh choices, and refuse Deliver approval until every question is understood. (AC2, AC4)
_Last changed by 069-deliver-owner-quiz._

### Understanding record
The system SHALL record `metrics.understanding` (`asked`, `first_try`, `after_explanation`, `rounds`), show it in the retro, and list the questions without answers in the PR body. (AC5, AC6, AC7)
_Last changed by 069-deliver-owner-quiz._
