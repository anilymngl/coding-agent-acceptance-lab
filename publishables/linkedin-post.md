I have built and experimented with quite a few things over the years.

I shared almost none of them.

There was always a reasonable excuse: it was not ready, someone had probably done it better, or perhaps the whole thing was obvious and I was just Captain Obvious with a GitHub account.

At some point, waiting until the work cannot look ordinary becomes another way of never publishing it.

So this is my first real public post—and my first academic-ish technical paper.

Evaluation and governance around data, semantic layers and agents are not new to me.

Coding-agent evals were.

The project began when a colleague asked me to evaluate a small coding model.

I knew enough to distrust a few vibe prompts, a toy application and a green test suite followed by the conclusion that the model was “surprisingly capable.”

But I did not yet know what the real evaluation target should be when the system produces a code patch.

So I started designing a few tests.

Those tests became a harness. The harness became repeated attempts, hidden acceptance tests, failure classification, released datasets, a technical paper and, somehow, a six-page research site.

What started as a look at one model grew into a two-stage, multi-model study.

Stage A compared four model families: Cohere North Mini Code, Google Gemma 4 12B, DeepSeek V4 Pro and Poolside Laguna XS.2.

Stage B was a 391-attempt depth study comparing two roughly 30B-class coding-agent systems—North Mini and Laguna XS.2—across 33 scenarios, two prompt lanes and three independent attempts.

The central question stayed simple:

**When a coding agent makes CI green, did it actually fix the problem?**

The agent sees a broken repository and its public tests. It makes a patch.

Only after the agent exits does the harness inject hidden acceptance tests it never saw.

When the public tests pass but hidden acceptance fails, I refer to it as a false-green.

The patch looks finished, but the actual acceptance contract is still broken.

The loop can look good while the reasoning stops at the assertion: read, edit, test, exit.

In the depth study, 385 attempts passed public CI.

101 still failed hidden acceptance.

Under sparse prompts, where the agent mostly saw the symptom, 84 of 194 public-green attempts were false-greens: **43.3%**.

The sparse lane was diagnostic. It was not an expectation that agents should infer requirements that existed only in my head.

When the actual acceptance contract was visible in the prompt, the rate fell to 17 of 191: **8.9%**.

But 17 is not zero.

Product workflows remained the hardest pack. Contract exposure recovered broad scenario coverage, but per-attempt reliability—especially for North Mini—remained weaker than on bounded repair and maintenance tasks.

The evidence does not establish that one model is universally better, that agents are unsafe, or that longer prompts solve software engineering.

The narrower finding is more useful:

**A coding agent can produce a clean, plausible patch that passes visible CI while still missing the acceptance rule that matters. Explicit contracts reduce that risk substantially, but they do not remove the need for verification.**

The project also changed while I was building it.

I began by asking whether the models were reliable.

I ended up asking whether my own evidence was reliable.

A single run could be luck. A timeout could be mistaken for a wrong answer. An evaluator could produce a confident diagnosis without enough evidence. A published chart could drift away from the underlying data.

Each problem forced another layer of the system to become explicit and checkable.

That is why I do not think of this as a leaderboard.

It is a behavior microscope for one specific failure mode: the apparently reasonable, public-green, contract-incomplete patch.

I started with a practical question about one small coding model.

I ended up with a broader one:

**What acceptance boundary makes this kind of work safe to delegate?**

I have open-sourced the harness, scenarios, released data, evidence site and paper.

I do not plan to publish constant AI commentary or predictions about how everything changes next Tuesday.

I want to share the work itself, slowly: evaluation systems, semantic layers, data agents, failure mechanisms, and the uncomfortable gap between an output that looks right and one that can actually be trusted.

Some of it may turn out to be obvious.

That is fine. I would rather make the work concrete and inspectable than leave it sitting in a folder.

Site:
https://anilymngl.github.io/coding-agent-acceptance-lab/

Repository:
https://github.com/anilymngl/coding-agent-acceptance-lab
