# **Deal Flow: Problem Tracks**

These four tracks come straight from problems NYC VCs and LPs told us they would pay to solve. Pick one, talk to the people who have the problem before build day, and build a company, not a project.

## **Track 1: Sourcing. Find the founder before the round**

**Problem statement.** The best deals are won before a company raises. Today most funds find founders through warm intros and the same LinkedIn searches every other fund runs, so they all chase the same names at the same time. Build a system that surfaces exceptional founders early, from public signals, and explains why each one deserves a meeting.  
**Who has this problem:** associates and partners at pre-seed and seed funds, venture scouts, angel syndicates.  
**Directions to explore**

> * A founder-quality score built from public signals: shipped projects, GitHub activity, papers, hackathon wins, job changes  
> * Alerts when a strong operator leaves a top company or a new company files a Form D  
> * A one-page "why this founder" brief for every lead: what they built, the shared connections, which part of the thesis they fit  
> * Thesis matching that ranks inbound and outbound leads against a fund's stated focus

**Why it can be a company:** every fund already pays for sourcing data. The opening is better signal and a clear explanation for each lead, not more names.  
**Data to start with:** [SEC EDGAR](https://www.sec.gov/edgar/search/) (Form D filings), the GitHub API, arXiv, Crunchbase, and the Akta API from Wokelo. LinkedIn's terms prohibit scraping, so use official APIs, data people export with consent, or licensed providers.  
**Ask in your interviews**

> * What share of your last 10 deals came from outbound?  
> * What signal got the last great founder a meeting with you?  
> * What would make you trust a score enough to act on it?

## **Track 2: Diligence. Underwrite a startup in an hour, not two weeks**

**Problem statement.** VCs told us the three things that matter most in diligence: a startup's market signals, its comps, and the issues hiding in its financials and metrics. A first pass still takes an associate days of pulling data, rebuilding numbers from a messy data room and spotting what does not add up. Build a tool that takes a deck or data room and returns the market signals, the right comps and the red flags a partner needs before a second meeting.  
**Who has this problem:** associates and principals at VC funds, angels doing diligence alone, accelerators screening hundreds of applicants.  
**Directions to explore**

> * A red-flag engine for financials and metrics: churn hidden in cohort charts, revenue counted as ARR when it is not recurring, burn that does not match the hiring plan, numbers that disagree between the deck and the model  
> * A comp builder that picks comparable companies and recent rounds, and explains why each one is a fair comp  
> * A market signal tracker for a company and its competitors: hiring, web traffic, reviews, pricing changes, customer wins  
> * A first-draft investment memo where every claim links back to its source

**Why it can be a company:** diligence is expensive time for every fund, angel group and corporate VC. A tool a partner trusts on the first pass saves days on every deal.  
**Data to start with:** public company filings on [SEC EDGAR](https://www.sec.gov/edgar/search/) for comps, the Akta API from Wokelo, Crunchbase, and web search APIs such as You.com and Tavily. Bring a synthetic data room; never upload a real company's confidential data.  
**Ask in your interviews**

> * What do you check first when you open a data room?  
> * Which red flag did you once miss and regret?  
> * How long does your first-pass memo take, and which part is the slowest?

## **Track 3: Portfolio. Know every company before the board meeting**

**Problem statement.** A fund with 40 portfolio companies gets 40 updates in 40 formats, when it gets them at all. Partners often learn a company is in trouble when it asks for a bridge. LPs who invest across many funds see even less: the same sector bet can sit in five of their GPs at once. Build the layer that turns scattered portfolio data into early warnings and patterns a fund can act on.  
**Who has this problem:** platform and portfolio teams at VC funds, partners, fund-of-funds and LPs invested with many GPs.  
**Directions to explore**

> * Agentic check-ins: an agent that asks founders for updates, reads the replies, follows up on gaps and flags who needs help  
> * A firm-wide, open-source model on a fund's own portfolio data, so partners can question their portfolio in plain language while the data stays in-house  
> * A cross-GP view for LPs that combines portfolio data from many funds to show sector concentration, overlap and trends  
> * A runway and risk radar: projected cash-out dates and early warning signs across the whole portfolio

**Why it can be a company:** every fund tracks its portfolio, and most still do it in spreadsheets and inboxes. A self-hosted, open-source option answers the biggest objection funds raise: their data cannot leave the firm.  
**Data to start with:** a synthetic portfolio of 20 to 50 companies with monthly updates (generate it before the event), open-weight models you can run yourself, and the Akta API from Wokelo for outside signals on each company.  
**Ask in your interviews**

> * How do you collect founder updates today, and what share of companies reply?  
> * What do you wish you had known three months earlier about a company that struggled?  
> * Which portfolio data would you never let leave the firm?

## **Track 4: Funds. Make LPs as informed as their GPs**

**Problem statement.** LPs commit capital for ten years and get PDFs in return. Yearly K-1s and quarterly reports arrive in different formats, valuation marks move with little explanation, and judging a GP's real track record means rebuilding it by hand. Secondary buyers face the same fog when they price an LP stake. Build tools that read fund documents, diligence GP teams and price what LPs own.  
**Who has this problem:** family offices, endowments, fund-of-funds, emerging LPs, secondary buyers, fund admins, and emerging managers raising Fund I or II.  
**Directions to explore**

> * A K-1 and quarterly report reader that pulls out NAV, capital calls, distributions and valuation changes, and explains what moved since last quarter  
> * GP diligence: rebuild a manager's track record, sourcing ability and key metrics (TVPI, DPI, IRR) from public and shared data  
> * Secondary pricing: estimate what an LP stake is worth from the underlying NAV, the portfolio's latest marks and current market discounts  
> * One dashboard of exposure, cash flows and performance across every fund an LP holds

**Why it can be a company:** GPs have a full stack of software, while most LPs still run on spreadsheets and email. Every LP gets these documents every quarter, so a tool that reads them is used every quarter.  
**Data to start with:** adviser filings (Form ADV) on the [SEC's adviser search](https://adviserinfo.sec.gov/), the reporting templates published by [ILPA](https://ilpa.org/), and synthetic K-1s and quarterly reports you generate before the event. Never upload real LP documents without the owner's permission.  
**Ask in your interviews**

> * How many hours does one quarter of fund reports take your team?  
> * How do you judge a GP's track record today, and what can't you verify?  
> * How do you decide what an LP stake is worth on the secondary market?