# New Feature Plan: Make the Handbook Assistant Easier to Start, Trust and Reuse

**Status:** proposal for team discussion (11 Nov 2026). Nothing is built yet.
**Deadline:** submit ZIP by **16 Nov 2026, 23:59**.

**How to read this document.** **Part A** summarises the five core features; each member's tasks are in `docs/tasks/`. **Part B** lists optional features; we build them only if time remains, and we do not start them until our core pull request is merged.

## 1. Why these features

Teacher feedback: the project is a single feature (ask a question, get a cited answer). It would be stronger with a few more features, and **every feature should follow from the motivation**.

**Motivation:** students who use the assistant run into four problems.

1. They don't know what to ask, or what the assistant can do.
2. They can't tell when an answer is wrong, and we have no way to find out.
3. Answers and conversations they need later are lost when the page is closed.
4. They can only use the handbook through this separate chatbot, but they would like to use it inside the AI agents they already use every day.

| Core feature | Problem it solves |
|---|---|
| A1 Saved chat history | Conversations are lost on refresh |
| A2 My collection | Important answers can't be kept and found again |
| A3 Suggested questions | New users don't know what to ask |
| A4 Feedback and report | Wrong answers go unnoticed; no way to improve |
| A5 MCP server | Students must switch to a separate chatbot; this lets them use the handbook inside the AI agents they already use (Claude, Claude Code, Codex) |

The features support each other: suggested questions get a new user started; feedback shows which answers need fixing; saved chats and the collection make good answers easy to find again; the MCP server brings the same handbook search into the AI agents students already use, so they don't have to switch to a separate chatbot.

**Optional (Part B):** AR forms page, student profile, study change advisor, connecting to calendar and email, and extra tools.

---

# Part A: Core features

The detailed tasks for each person are in four files with the same format (goal, branches and files, tasks, interfaces, done when):

| Member | Features | Task file |
|---|---|---|
| A | A1 Saved chat history, app skeleton, storage, UI layout | [member-a-skeleton-and-history.md](tasks/member-a-skeleton-and-history.md) |
| B | A2 My collection | [member-b-collection.md](tasks/member-b-collection.md) |
| C | A4 Feedback and report, final docs | [member-c-feedback-and-docs.md](tasks/member-c-feedback-and-docs.md) |
| D | A3 Suggested questions, A5 MCP server | [member-d-suggestions-and-mcp.md](tasks/member-d-suggestions-and-mcp.md) |

**Merge order:** A's skeleton branch first; then B, C and D; C updates the docs last.

## Shared decisions

- **Storage:** one local, single-user file `data/user_data.sqlite` (git-ignored by `data/*`), Python `sqlite3`. Chats are saved automatically unless the student starts a **Temporary chat**; saved answers, ratings and reports are stored only on click; **Delete all my data** removes everything.
- **UI:** `app.py` stays a single script; the sidebar follows ChatGPT's layout (New chat, Search chats, Collection, Chats list, Settings at the bottom). No `st.navigation`, because `tests/test_app.py` uses `AppTest.from_file("app.py")`.
- **MCP hosting:** local over stdio (team lead, 11 Nov). A temporary public link (Streamable HTTP + tunnel, about 1 hour) or a hosted server (about 1 day) stay as future options; both need a public HTTPS URL, copyright permission for handbook passages, enough memory for `BAAI/bge-small-en-v1.5`, and rate limiting.

## Final verification

- `python -m pytest -q -rs` passes (temporary database, injected answer service).
- `streamlit run app.py` on the real index: click a suggested question; rate, save and report an answer; restart; confirm chats, collection and ratings persist; reopen a chat and ask a follow-up; run the export script.
- A Temporary chat writes nothing; Settings > Delete all my data removes everything.
- MCP Inspector shows both tools; Claude Desktop and Claude Code answer a handbook question.
- Check a large zoom level and a narrow window for the chips and the action row.
- `git status` does not show `data/user_data.sqlite`.

## Questions for the team

1. Is automatic chat saving on by default acceptable, or should saving be opt-in?
2. Is `get_section` the right second MCP tool?
3. Who reviews each pull request (rotation)?
4. Who re-tests the 18 suggested questions? It needs the model API key.
5. Feedback stays on each person's machine. Is exporting and merging by hand enough?
6. Are the six suggestion domains and the wording right for students?

---

# Part B: Optional features

Each block below is **optional: build it only if time remains** and only after the core pull requests are merged.

## B1. AR forms page

**Optional: only if time.** The forms catalogue and page below are kept in full so no research is lost. Note: `data/*` is git-ignored, so `forms.json` must live under `assets/` or get a `!data/forms.json` exception in `.gitignore`, otherwise teammates will not receive it.

A second Streamlit page with one card per AR form: **40 entries** (AR1 to AR178), e.g. AR6 withdrawal, AR7 deferment, AR8 leave of absence, AR3 transcript, AR41c credit transfer. Forms are sorted by **what the student needs**, in six categories (catalogue below), not by where the information came from.

**Each card shows:**
- form code and name
- purpose (when you would use it)
- who it applies to
- what to prepare (supporting documents, approvals)
- deadline
- where to get it and where to return it (eStudent / AR website / department)
- handbook section and page as the source, when the form is covered in the handbook; otherwise the label "Not covered in the handbook. Check with your department or the Academic Registry."

**Page features:** search box, category filter (the six categories below), and links from chat answers and advisor recommendations to the matching card.

**Data:** build `data/forms.json`. Most fields can be extracted automatically because every form uses the same "Get the form from / Return it to / Deadline" layout, but **every card that uses handbook text must be checked by hand against the handbook**.

**Scope: all AR forms (team decision, 11 Nov).** The catalogue is not limited to forms the handbook mentions. It covers every AR form PolyU lists for taught-programme students: 31 entries named in the handbook (30 codes; AR121a and AR121b counted separately) plus 9 more from the Academic Registry page and eStudent, **40 in total** (AR1 is one entry with two ways to apply). Cards are sorted and filtered by category only. The source is a small label on each card:
- **Covered in the handbook:** purpose, who it applies to, what to prepare and deadline come from the handbook, with the section and page.
- **Not covered in the handbook** (9 forms, marked "Not in handbook" in the tables): only the official title, who it is for as PolyU states it, how to apply and links. No purpose, deadline or "what to prepare" text is invented for these.

The chat answers and the study change advisor stay grounded in the handbook. Only the Forms page and the MCP `get_form` tool use the wider catalogue. Research postgraduate forms (GSB/19, GSB/30) are not AR forms and are left out.

### Form catalogue: sorted by what the student needs (checked 11 Nov 2026)

Sources: the Academic Registry page [Application Forms](https://www.polyu.edu.hk/ar/students-in-taught-programmes/application-forms/) for taught-programme students, the handbook text, and screenshots of the eStudent "Application Forms" screens taken from a team member's login (11 Nov). **How to apply:** *Download* is a public Word file; *Online* means submit through eStudent (PolyU login needed, no public form file). 20 forms are downloads and 20 are online.

**1. Study status and load (8)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR7 | Deferment of study | Online | 4.H | Genuine need, e.g. prolonged illness |
| AR8 | Leave of absence | Download | 4.F | Temporary absence from class |
| AR9 | Extension of study duration | Online | 4.D | Taught programmes, 2020/21 intake onwards |
| AR112 | Retention of study place (zero subject enrolment) | Online | 4.I | HK$2,350 per semester |
| AR114 | Change to self-paced status | Download | 4.K | Not following the specified progression pattern |
| AR121a | Fewer than 9 credits in a semester | Download | 4.K | Full-time students, 2017 intake or before |
| AR121b | Fewer than 9 credits in a semester | Download | 4.K | Full-time students, 2018 intake onwards |
| AR150 | Study load on academic probation | Download | 6.C | Students on academic probation |

**2. Leaving, transfer and appeals (5)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR6 | Withdrawal of study | Online | 4.L | Leaving the programme |
| AR10 | Refund of caution money | Download | 4.L | After official withdrawal or de-registration |
| AR25 | Transfer of study | Download | 4.J | Exceptional circumstances |
| AR118 | Reinstatement of registration | Download | 5.H | After registration was nullified |
| AR149 | Appeal against de-registration | Download | 6.I | De-registered students |

**3. Subjects and credits (6)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR41a | Prior agreement for subject selection at exchange-out institution | Download | 5.B | Exchange-out students only |
| AR41c | Credit transfer | Online | 5.B | |
| AR41e | Subject exemption | Online | 5.B | |
| AR41f | Waiver of CAR subjects requirement, Healthy Lifestyle exemption, GE e-module waiver | Download | 5.B | |
| AR160 | Second retake of failed subject | Download | 5.C | |
| AR163 | Waiver of "Understanding China and Hong Kong SAR" education | Download | 5.B | Taught postgraduate programmes, 2022/23 intake onwards only |

**4. Programme options: concurrent study, minor, major, fast-track (12)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR38 | Concurrent enrolment | Download | 4.G | |
| AR147 | Minor | Online | 4.M | GPA rule in 4.M |
| AR147a | Counting subjects under major towards minor | Download | Not in handbook | On the public page only |
| AR164 | Major / secondary major / double major | Online | 4.M | GPA rules in 4.M |
| AR167 | Fast-track programme | Online | 4.M | |
| AR168 | Withdrawal from fast-track programmes | Online | Not in handbook | |
| AR169 | Switching to a different departmental scheme or stand-alone programme | Online | Not in handbook | |
| AR170 | Ranking choices for the iteration process | Online | Not in handbook | |
| AR173 | Reassessment of iteration result | Online | Not in handbook | |
| AR176 | Withdrawal from minor | Online | Not in handbook | |
| AR177 | Withdrawal from secondary major | Online | Not in handbook | |
| AR178 | Withdrawal from double major | Online | Not in handbook | |

**5. Graduation, transcripts and certificates (6)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR84c | Graduate in exit award / specialism | Download | 6.K | |
| AR3 | Transcript of studies | Online | 7.A | HK$100 per copy |
| AR4 | Testimonial | Online | 7.B | HK$100 per copy |
| AR5 | Certification of true copy | Download (page unchecked) | 7.E | Graduates |
| AR106 | Certification of award | Download (page unchecked) | 7.D | Graduates |
| AR171 | Replacement award parchment | Download (page unchecked) | 7.D | Graduates |

**6. Personal details, student card and visa (3)**

| Code | Form | How to apply | Handbook | Who it is for / note |
|---|---|---|---|---|
| AR1 | Amendment of personal data (download) and of contact information (online, also a download) | Both | 4.C | One card, two ways to apply |
| AR2 | Replacement of student identity card | Online | 4.B | The public page also links the card site `https://cardreplace.polyu.edu.hk/` |
| AR165 | Supporting letter for student visa extension | Online | Not in handbook | Full-time student visa holders only |

**Download file names** (all under `https://www.polyu.edu.hk/ar/docdrive/polyu-students/eng-forms/`; each link responded, HTTP 200, on 11 Nov; file contents not opened): AR1 `ar1.doc` · AR5 `ar5.docx` · AR8 `ar8.doc` · AR10 `ar10.doc` · AR25 `ar25.doc` · AR38 `ar38.docx` · AR41a `ar41a.doc` · AR41f `ar41f.doc` · AR84c `ar84c.doc` · AR106 `ar106.docx` · AR114 `ar114.doc` · AR118 `ar118.docx` · AR121a `ar121_2017_intake_or_before.doc` · AR121b `ar121_2018_intake_onwards.doc` · AR147a `ar147a.doc` · AR149 `AR149.docx` · AR150 `ar150.docx` · AR160 `ar160.doc` · AR163 `ar163.doc` · AR171 `ar171.docx`

**Online forms:** eStudent link `https://www.polyu.edu.hk/student`. The card says "Apply through eStudent (PolyU login required)".

**Resolved by the eStudent screenshots:** AR7, AR6 and AR112 are online (Apply); AR2 is listed too, with Apply; AR121a/b intake rules confirmed. Download forms that appear in the public page's file list also show a "Form" link in eStudent, except AR149, AR147a, AR5, AR106 and AR171, which are not in the eStudent list.

**Still needs your check (I cannot confirm these myself):**

| # | What to check | Why |
|---|---|---|
| 1 | **AR5, AR106, AR171:** open the Academic Registry "Graduates" forms page and confirm the three forms and their links are listed. | They are not in eStudent and I did not read that page. |
| 2 | **Open 3 or 4 download files** (e.g. AR8, AR25, AR114, AR149) in Word. | I only checked that the links respond, not that the right, current form is inside. |
| 3 | **AR2:** click Apply in eStudent and see whether it opens the card-replacement site. | The handbook and eStudent say eStudent; the public page links the separate site. Probably the same flow, but unconfirmed. |
| 4 | **Do not link** `ar2.docx`, `ar112.doc`, `ar147.doc`. | They exist at the web address, but both the public page and eStudent show these forms as online, so these files may be old versions. |
| 5 | **Recheck every link just before submitting (15 and 16 Nov).** | PolyU can rename or replace files. A small script that requests each address can do this. |
| 6 | **AR147a:** open the file and confirm what it is for. | Only on the public page, not in eStudent. |
| 7 | **The 9 "Not in handbook" forms:** copy PolyU's own wording for who each is for (eStudent shows some, e.g. AR165 for visa holders only). If PolyU gives no wording, leave it blank. | We must not invent purposes for forms the handbook does not cover. |

Other notes: AR1 appears twice on the page (a download and an online "Update contact information"), so its card shows both. The public page and eStudent also list GSB/19 and GSB/30 for research postgraduates; these are not AR forms and are left out.

Add four fields to each card in `forms.json`: `source` (`handbook` or `polyu_forms_page`, which decides whether the card shows handbook details and the "Not covered in the handbook" label), `access` (`download` or `online`), `official_page_url` (the public Application Forms page, always shown) and `download_url` (only for download forms). For online forms show "Apply through eStudent (PolyU login required)" with the eStudent link, never a direct form link. Link to the official page and files instead of copying them into our repository. Re-check every link before submission, since PolyU can rename files; a small script that requests each URL can do this.

**Limit to state honestly:** the handbook does not list the actual boxes on each form. "Key info" means what the handbook says to prepare, not invented form fields.

**Ready-made tools:** Streamlit `st.navigation` / `st.Page` for the second page; `st.text_input` + `st.pills` for search and category filters; Pydantic to validate every entry in `forms.json`. Optional: `ics` + a Google Calendar link to add a form's deadline to a calendar.

### Forms page layout

- Search box and category chips (all, study status and load, leaving / transfer / appeals, subjects and credits, programme options, graduation and certificates, personal details and visa).
- A grid of form cards. Each card: code and name, purpose, who it applies to, what to prepare, deadline, where to get and return it, handbook section and page.
- **Open form card** from the chat opens this page with that form highlighted, using a query parameter such as `?form=AR7`.

### get_form MCP tool (optional)

If the forms catalogue is built, add `get_form(code)` to the MCP server (A5, see Member D's task file). It reads `forms.json` and returns one form card (for example `AR7`): purpose, who it applies to, what to prepare, deadline, where to get and return it, and the handbook source. It works for all 40 AR forms; each result has a `source` field (`handbook` or `polyu_forms_page`), and forms not covered by the handbook return only title, audience, access type and links. For an unknown code it returns a clear message with the valid codes. It needs no model API key.

## B2. Student profile

**Optional: only if time.** A few facts the student chooses to save in the sidebar, kept separate from chat history (A1):
- undergraduate or postgraduate, full-time or part-time
- year of study (first-year full-time students can defer only in exceptional cases, 4.H)
- admission year (fee rules differ for admission in or after 2018/19; normal-duration rules for 2020/21 onwards; 4.E applies only to admission in or before 2019/20)
- local or non-local (fee deferment is for local UGC-funded students, 8.E; non-local students must also check visa rules, Section 9 of the handbook)

The profile is opt-in, stored in the same local database, and cleared by "Delete all my data". The study change advisor (B3) needs it.

## B3. Study change advisor (recommender)

**Optional: only if time.** Depends on the student profile (B2) and on the forms catalogue (B1). Note: `study_options.json` has the same `data/*` git-ignore issue as `forms.json`.

### B3.1 Domain: changing or pausing your study

We restrict recommendations to one narrow domain. After reviewing all handbook sections, this one fits the ask-then-recommend design best:

- students arrive with a *situation* ("I'm sick", "I can't afford this semester"), not a rule name
- there are about 12 similar-sounding options, and students often pick the wrong one or miss a cheaper one
- a few follow-up answers really change which option is right (timing, scope, profile)
- the handbook states conditions, deadlines and trade-offs for each option, so every recommendation can be cited
- 9 of the options have forms, so each recommendation links to the forms page

**Domains considered and not chosen:**
- *Study path options* (Minor, Secondary Major, fast-track): mostly a GPA filter; choosing between them depends on interests, which the handbook can't judge.
- *Support services* (counselling, health, financial aid): one question is usually enough, so there is little to follow up. Used only as a short "you may also want" line.
- Fees, exam conduct, bad weather, lab safety, discipline, certificates: fixed facts or too few options to rank.

### B3.2 Option catalogue (`data/study_options.json`)

| Option | Section | Form | Key conditions from the handbook |
|---|---|---|---|
| Leave of absence | 4.F | AR8 | Temporary absence from class; apply as early as possible before the leave; approval not automatic; supporting documents |
| Late assessment | 6.H | Written application | Missed exam/assessment through illness, injury or unforeseeable reasons; within **five working days** of the assessment; original supporting documents |
| Add/drop subjects | 5.E | eStudent | Only during the two-week add/drop period (one week for Summer Term) |
| Withdrawal of subjects | 5.G | Apply to department | After add/drop; strong justification; fees not refunded; not accepted after the examination period starts |
| Fewer than 9 credits | 4.K | AR121a/b | Full-time students; before the end of the add/drop period |
| Self-paced status | 4.K | AR114 | Before subject registration, no later than the start of the semester |
| Zero subject enrolment | 4.I | AR112 | Before the semester starts, no later than end of add/drop; HK$2,350 per semester; normally counts toward study period; campus facilities still available |
| Deferment of study | 4.H | AR7 | Genuine need (e.g. prolonged illness, posted to work outside HK); first-year full-time only in exceptional cases; documentary proof; not counted toward study period; normally no campus facilities; result within about 3 weeks |
| Withdrawal of study | 4.L | AR6 | Before the examination period for the current semester; fees normally not refunded; clear outstanding fees, loans and lockers first |
| Transfer of study | 4.J | AR25 | Exceptional circumstances; new students from their second semester; deadlines 31 Jan (for next Semester One) / 30 Sep (for Semester Two) |
| Extension of study duration | 4.D | AR9 | Students admitted in or after 2020/21; before the examination period of the semester |
| Deferred payment of tuition fees | 8.E | Via Student Affairs Office | Local students of UGC-funded full-time programmes; at least two working days before the payment deadline |

Support line (not ranked): Student Counselling Service (12.C), University Health Service (12.D).

All entries must be re-checked against the handbook text before use.

### B3.3 Conversation flow

1. The student describes their situation in one message.
2. The model extracts what it can and asks **only the missing questions** (at most 3–4), shown with quick-reply buttons:
   - **Where are you in the semester?** not started / first 2 weeks (add/drop) / after add/drop, before exams / exam period or after
   - **What would help most?** miss classes for a while / drop a subject / take fewer credits / stop for the rest of the semester / pause longer / switch programme / leave the programme / can't pay fees
   - **Do you plan to come back, and when?**
   - **Do you have supporting documents** (e.g. a medical certificate)?
   - Profile facts are taken from memory and asked only if missing and relevant.
3. The assistant shows up to 3 ranked options, each with a reason it fits, the trade-offs (fees, campus access, counts toward study period, deadline), the form, and the handbook source.
4. It also lists options that **no longer fit and why** (e.g. "Zero subject enrolment: the deadline was the end of add/drop").
5. Each option links to its forms page card.

The advisor suggests options; it never decides eligibility. Every result ends by pointing to the department or Academic Registry.

### B3.4 How it works

| Step | Done by | Why |
|---|---|---|
| Understand the situation, fill in answers | Model (JSON output) | Students describe situations in free text |
| Choose and rank options | **Plain Python rules** over `study_options.json` | Same answers always give the same options, so it can be tested; hard constraints like deadlines are never guessed |
| Explain each option | Model, from the cited handbook passages only | Keeps the existing grounding and citation checks |

**When the advisor runs:** only for questions about study status or attendance. Every other question gets the normal cited answer, with no follow-up questions or recommendations.

**Feedback (optional):** 👍/👎 on each option, saved in memory, used to slightly re-rank.

**Cold start:** we have no usage data from many students, so collaborative filtering ("students like you also chose…") is not possible. The advisor uses rules plus the student's own profile instead. Worth saying in Q&A.

### B3.5 Evaluation

- Write about **20 student cases** (situation + profile) with the correct options agreed by the team from the handbook.
- Measure: correct option ranked first (top-1 accuracy), correct options in the top 3 (Precision@3 / nDCG@3), and correct "no longer fits" explanations.
- Check that the advisor asks no more than 4 questions and does not trigger on ordinary factual questions (reuse the existing 30-question set).

### B3.6 Ready-made tools

| Part | Tool |
|---|---|
| Quick-reply buttons | Streamlit `st.pills` / `st.segmented_control` |
| Extract answers from free text | DeepSeek function calling (`strict`, beta) or JSON Output + **Pydantic**; optionally **Instructor** |
| Option conditions | **rule-engine** or **json-logic** expressions in `study_options.json` |
| Evaluation | **ranx** (Precision@3, nDCG@3, MRR) |
| Skipped | LangGraph, Rasa CALM, LightFM / RecBole (see B4) |

## B4. Other ready-made tools (don't build from scratch)

**Optional: only if time.** Tools researched on 11 Nov 2026 for the optional features, plus the ones we decided to skip.

Researched 11 Nov 2026. The app already runs Streamlit 1.67 and an OpenAI-compatible model API (DeepSeek by default), so the first choice is tools that plug into that stack.

### Use (low effort, clear value)

| Need | Tool | How we use it |
|---|---|---|
| Forms page, multi-page app | Streamlit `st.navigation` / `st.Page` (built in) | Adds the forms page without a new framework |
| Quick-reply buttons for advisor questions | Streamlit `st.pills` / `st.segmented_control` (built in) | Student taps an answer instead of typing |
| 👍/👎 on answers and recommendations | Streamlit `st.feedback` (built in) | Feedback saved to the memory database |
| Saved chats and profile | Python `sqlite3` or Streamlit `st.connection("sql")` | One local file, no server |
| Reliable slot extraction from free text | DeepSeek function calling with `strict` schemas (beta) or JSON Output, validated with **Pydantic**; optionally the **Instructor** library, which has a DeepSeek guide | The model returns `{timing, goal, returning, documents}` as checked fields, not free text |
| Readable eligibility rules | **rule-engine** (BSD-3, active in 2026) or **json-logic** | Conditions in `study_options.json` written as expressions, e.g. `period == "add_drop"` |
| Ranking evaluation | **ranx** (MIT; Precision, nDCG, MRR, tested against TREC Eval) | Scores the advisor on the 20 student cases |
| MCP server (A5) | **MCP Python SDK** / **`fastmcp`**, **MCP Inspector**, **Google Workspace MCP servers** | Details and version note in A5.4 |

### Maybe (if time allows)

| Need | Tool | Note |
|---|---|---|
| Answer quality evaluation | **Ragas** (faithfulness, context recall) | Strengthens the evaluation results; costs extra model calls |
| "Add deadline to calendar" | **ics** (`.ics` file) + Google Calendar `render?action=TEMPLATE` link; **workalendar** / **calendra** for Hong Kong working days | Makes "within five working days" a real date |
| Use the assistant from Telegram | **python-telegram-bot** (v22) | Another thin wrapper around `answer_question` |
| Tracing and feedback dashboard | **Langfuse** (MIT, self-host with Docker) | Nice for debugging; not needed |

### Considered and skipped

| Tool | Why not now |
|---|---|
| LangGraph (`interrupt` + `SqliteSaver`) | Built for pause-and-ask flows, but adds a framework; our 3–4 question flow is a small state machine |
| mem0 / Memori (long-term memory layers) | Need a vector store and model-based extraction; a few explicit profile fields are simpler and more transparent |
| Chainlit | Has built-in chat history, feedback and action buttons, but means rewriting the UI; history also needs login |
| Rasa CALM | Designed for slot-filling flows, but heavy and its LLM features are in the commercial Pro edition |
| LightFM / RecBole (recommender libraries) | Need many users' interaction data (cold start); original LightFM is only maintained as a fork |

## B5. Future work (not planned)

- Exporting deadlines to Google / Outlook / Apple Calendar (`.ics`)
- GPA and eligibility calculator using tool calling
- Uploading a student's own Programme Requirement Document
- Telegram bot so students can use the assistant on their phones
- Showing the AR forms inside chat answers
- Study path and support-services recommenders


## B6. Connect page

**Optional: only if time.** In-app setup page for the MCP server.

- Heading: "Use this handbook in your own AI app".
- One tab per app (Claude Desktop, Claude Code, Codex), each with a copy-paste setup example.
- The tools, `search_handbook(query)` and `get_section(section)` (and `get_form(code)` if B1 is built), with a note that they are read-only and need no API key.

## B7. Connect to calendar and email

**Optional: only if time.** Existing, mature MCP servers can give the AI agent a calendar and an email tool, so the agent can combine them with our handbook server.

| Need | Tool | Note |
|---|---|---|
| Calendar and email | Existing **Google Workspace MCP servers** (e.g. `google_workspace_mcp`, MIT; `mcp-google`) or Claude Desktop's own Google connectors | **No extra code from us.** With both servers connected, the agent can look up a rule with `search_handbook` (or `get_form` if B1 is built), then create a calendar reminder for the deadline or draft an email to the department. Needs a Google OAuth setup; use a test Google account, and check each project's recent activity first |

Our server provides the handbook knowledge, the existing servers provide calendar and email, and the AI agent combines them. Working days in Hong Kong can be calculated with `workalendar` or `calendra` (see B4).
