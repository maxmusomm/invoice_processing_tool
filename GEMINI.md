# Agent Instructions

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

**Layer 1: Directive (What to do)**
- Basically just SOPs written in Markdown, live in `directives/`
- Define the goals, inputs, tools/scripts to use, outputs, and edge cases
- Natural language instructions, like you'd give a mid-level employee

**Layer 2: Orchestration (Decision making)**
- This is you. Your job: intelligent routing.
- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings
- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read `directives/scrape_website.md` and come up with inputs/outputs and then run `execution/scrape_single_site.py`
- **All orchestration logic is implemented in Python using LangChain.** Use LangChain's agent abstractions, chains, and tool interfaces to wire directives to execution scripts. Prefer `AgentExecutor`, `LangGraph` graphs, or LCEL chains as appropriate for the complexity of the task.

**Layer 3: Execution (Doing the work)**
- Deterministic Python scripts in `execution/`
- All scripts are pure Python 3.10+. Use LangChain's tool interface (`@tool` decorator or `Tool`/`StructuredTool` wrappers) to expose execution scripts as callable tools for the orchestration layer.
- Environment variables, API tokens, etc. are stored in `.env` and loaded via `python-dotenv`
- Handle API calls, data processing, file operations, database interactions
- Reliable, testable, fast. Use scripts instead of manual work. Commented well.

**Why this works:** if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

## Operating Principles

**1. Check for tools first**
Before writing a script, check `execution/` per your directive. Only create new scripts if none exist. All new scripts must be Python 3.10+ and, where they are exposed to the orchestration layer, wrapped as LangChain tools.

**2. Self-anneal when things break**
- Read error message and stack trace
- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)
- Update the directive with what you learned (API limits, timing, edge cases)
- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

**3. Update directives as you learn**
Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

## Self-annealing loop

Errors are learning opportunities. When something breaks:
1. Fix it
2. Update the tool
3. Test tool, make sure it works
4. Update directive to include new flow
5. System is now stronger

## File Organization

**Deliverables vs Intermediates:**
- **Deliverables**: Google Sheets, Google Slides, or other cloud-based outputs that the user can access
- **Intermediates**: Temporary files needed during processing

**Directory structure:**
- `.tmp/` - All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.
- `execution/` - Python scripts (the deterministic tools), each exposed as a LangChain tool where applicable
- `directives/` - SOPs in Markdown (the instruction set)
- `.env` - Environment variables and API keys (loaded via `python-dotenv`)
- `credentials.json`, `token.json` - Google OAuth credentials (required files, in `.gitignore`)
- `requirements.txt` - Must stay current. Core dependencies include `langchain`, `langchain-community`, `langgraph`, `python-dotenv`, and any tool-specific packages.

**Key principle:** Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in `.tmp/` can be deleted and regenerated.

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system. All orchestration is Python + LangChain, fast api and steamlit; all execution scripts are Python 3.10+.

Be pragmatic. Be reliable. Self-anneal.

