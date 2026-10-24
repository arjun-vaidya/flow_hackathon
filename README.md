# Pull

**Find early technical founders through evidence of customer demand.**

Pull is a sourcing assistant for pre-seed investors in AI infrastructure and developer tools. It connects public user problems to projects, their builders, and commercial context, then produces a short, evidence-backed explanation of why an investor should meet a builder now.

Built for **Track 1: Sourcing** at [Deal Flow: NYC's First VC Hackathon](https://nyc-vc-hack.devpost.com/).

> **Status: frontend demo.** The React app in `frontend/` implements discovery, shortlisting, saved builders, evidence review, and builder briefs with clearly labeled fictional data. Backend services, sponsor integrations, and real evaluations are still planned. Example outputs are illustrative, not verified investment leads.

## The product

An investor enters a thesis:

> Find early builders developing tools for testing and monitoring AI agents.

Pull discovers relevant public projects, examines user demand, researches competitors, and returns three founder opportunities. Each brief includes:

- The builder and what they have shipped.
- Specific demand evidence with source links and dates.
- Recent developments and fit with the fund's thesis.
- Commercial alternatives and reasons to be skeptical.
- Unknowns and questions for a first meeting.

The core question is **“Which builder should this investor meet this week, and what evidence makes that meeting worthwhile?”**

## Required sponsor integrations

| Tool | Planned responsibility |
| --- | --- |
| [NicrronNinoo](https://nicrron.ai/) | Model calls for thesis interpretation, evidence extraction, research, verification, and brief generation. |
| [akta.pro by Wokelo AI](https://docs.akta.pro/home) | Company, competitor, and news context. An early project can be absent from its database while its competitors are covered. |
| Roundtable | Shared evidence files, version history, and task messages between our scouting, research, and verification agents. Use the sponsor's workspace described in the [event resources](https://nyc-vc-hack.devpost.com/resources), not unrelated products with the same name. |
| [PRISM by Block Convey](https://blockconvey.com/docs) | Traces, evaluations, failure investigation, and comparison of corrected behavior on fixed inputs. |

Every sponsor must be used in the working project. These are planned responsibilities, not completed integrations.

## Read the plan

- [Product design and build checklist](docs/PROJECT_PLAN.md)
- [Architecture: stack, data flow, APIs, database, and deployment](docs/ARCHITECTURE.md)
- [Organizer's problem tracks](docs/Deal%20Flow_%20Problem%20Tracks.md)
- [Local requirements excerpt](docs/hackathon_requirements.txt)
- [Official requirements](https://nyc-vc-hack.devpost.com/), [rules](https://nyc-vc-hack.devpost.com/rules), and [sponsor resources](https://nyc-vc-hack.devpost.com/resources)

## Working together

```sh
git clone https://github.com/arjun-vaidya/flow_hackathon.git
cd flow_hackathon
git switch -c feature/your-task
```

Keep changes focused and open pull requests into `main`.

Run the frontend with Node 22.12+:

```sh
cd frontend
npm ci
npm run dev
```

See [frontend setup and demo limitations](frontend/README.md). Run `npm run build` for the production build and `npm test` for interaction checks.

Never commit API keys, `.env` files, confidential fund documents, or raw private customer data. Use public or clearly labeled synthetic data. Access to each sponsor account must be established before building against it.

## Event constraints

- All four sponsor tools are required for prize eligibility.
- All project code must be written during the event; libraries, public APIs, and starter templates are allowed.
- Research, interviews, designs, and datasets can be prepared beforehand.
- Teams have 2–4 people, with at least one person who can write code. The event is in person at Betaworks.
- Use public or permitted synthetic data. The sourcing brief prohibits LinkedIn scraping.
- Submit a repository, live demo, video of at most three minutes, and the founder brief described in the plan. Demo live to the judges.
- **Target October 24, 2026, 4:00 p.m. ET for submission.** The event header and dates section say 4:00; one rules bullet says 4:30. Use the earlier time unless organizers clarify.

Requirements were checked on October 24, 2026. The linked official pages are authoritative; the local excerpt is not the complete rules.
