# ifbot

ifbot is two things in one small repository:

1. A tiny rules-only chatbot (the seed). No models, no network, standard library only.
2. A harness for growing that bot by hill-climbing a benchmark. A proposer (a person, or any agent you can start from a shell command) edits a copy of the bot. The harness runs the tests, scores the change on a held-out split, and keeps it only if the score is strictly better.

The idea is inspired by [huggingface/pybot](https://github.com/huggingface/pybot), a rules-only chatbot grown by an agent swarm against a benchmark. This is an independent implementation with its own code and data.

Requirements: Python 3.9 or newer. No dependencies.

## Quick start

```
python3 -m ifbot                      # interactive chat (/reset, /exit)
python3 -m ifbot -p "hi, i'm Sam"     # one reply, then exit
echo "what is 12 * 7" | python3 -m ifbot   # one reply per input line
python3 -m ifbot -v -p "hello"        # also show the winning module and time (stderr)
python3 -m ifbot -s 3                 # pick the random seed used for reply variety

python3 -m ifbot eval --split dev
python3 -m ifbot eval --split heldout --json
python3 -m unittest discover -s tests
```

Run these from the repository root. The data files live in `data/`, so the harness expects a checkout rather than an installed package.

The seed bot, scored with the offline overlap judge (token F1 against the reference answer, win at 0.35 or above), as printed by `python3 -m ifbot eval`:

| split   | wins | total | win rate |
| ------- | ---- | ----- | -------- |
| dev     | 7    | 40    | 0.175    |
| heldout | 1    | 30    | 0.033    |

These are the only numbers this project claims. The seed is meant to be bad: most of its dev wins come from greetings, smalltalk and three facts.

## Layout

```
ifbot/bot/            the chatbot: engine, arbiter, understand, memory, modules/
ifbot/evals/          dataset loader, judges, scorer, isolated worker
ifbot/evolve/         workspace, gate, ledger, loop
data/dev.jsonl        40 questions the proposer can see
data/heldout.jsonl    30 different questions in the same 8 categories, used only by the gate
tests/                test_bot_*.py are the bot's own tests; the rest test the harness
runs/ledger.jsonl     created on first submit (git-ignored)
```

Each bot module under `ifbot/bot/modules/` defines `propose(ctx)` and returns a `Proposal(text, confidence)` or `None`. A module may also define `learn(ctx)` to write to the conversation memory. The arbiter picks the highest confidence and breaks ties by module name, so the bot is deterministic for a given seed.

## How the loop works

```
  evolve new ──> workspace (temp dir)
                   bot/        copy of the current bot
                   tests/      the bot's tests
                   data/       dev.jsonl only
                   BRIEF.md    rules + current dev failures
                      │
          proposer command edits bot/ (cwd = workspace, IFBOT_WORKSPACE set)
                      │
  evolve submit ──> validate ──> bot tests ──> score dev + held-out ──> better than best?
                    (ast and     (subprocess,   (subprocess,            │
                     file checks) timeout)       timeout)       yes: copy bot/ into ifbot/bot
                                                                no:  discard
                      every submission is appended to runs/ledger.jsonl
```

Rules enforced by the gate, each a rejection with a reason in the ledger:

- The candidate adds or edits files outside `bot/` (the gate also ignores any edited tests: it runs its own copies).
- The bot imports anything outside the standard library, imports a forbidden module (subprocess, socket, urllib, http, ctypes, threading and a few more), or uses `eval`, `exec`, `compile`, `__import__`, `os.system` and related calls. Checked with `ast`. Imports of the bot's own code must be relative.
- The bot's source contains a held-out instruction or a held-out reference answer verbatim (compared after lowercasing and stripping punctuation, including across concatenated string literals). Instructions shorter than five words are only checked for non-smalltalk rows, because phrases like "good morning" legitimately exist in any chatbot.
- The bot tests fail, hang, or the bot crashes or times out while answering.
- The held-out win rate is not strictly greater than the best accepted so far.

The first `evolve submit` on an empty ledger records the current bot as the baseline.

Commands:

```
python3 -m ifbot evolve new
python3 -m ifbot evolve submit <workspace-dir>
python3 -m ifbot evolve run --rounds 5 --proposer-cmd "<command>"
python3 -m ifbot evolve log
```

## Writing a proposer command

A proposer is any shell command. It is started with the workspace as its working directory and `IFBOT_WORKSPACE` set to the same path. It should read `BRIEF.md`, edit files under `bot/`, run the tests, and exit. A non-zero exit or a timeout skips the gate for that round and is recorded in the ledger.

Generic shape, with `my-agent` standing in for whatever agent CLI you use:

```
python3 -m ifbot evolve run --rounds 10 \
  --proposer-cmd 'my-agent --prompt "Read BRIEF.md and improve the bot in bot/. Edit only bot/. Run python -m unittest discover -s tests before you finish."'
```

Or a plain script, if you want to write the rules yourself:

```
python3 -m ifbot evolve run --rounds 1 --proposer-cmd "python3 /path/to/my_proposer.py"
```

The proposer inherits your environment, so any credentials your agent CLI needs reach it. The bot it edits must not need them.

## Plugging in an LLM judge

The overlap judge is offline and free. To use a stronger judge, pass a shell command. For every row it receives JSON on stdin:

```
{"instruction": "...", "reference": "...", "reply": "..."}
```

and must print a line starting with `WIN` or `LOSS`. Anything else, a non-zero exit, or a timeout counts as a loss and is logged.

```
python3 -m ifbot eval --split dev --judge command --judge-cmd "python3 my_judge.py"
python3 -m ifbot evolve run --rounds 5 --proposer-cmd "..." --judge command --judge-cmd "python3 my_judge.py"
```

If your judge calls a model, that is where the model call and its key live. Nothing inside ifbot makes one. Use the same judge for the whole climb: the ledger compares win rates across rows, and numbers from different judges are not comparable.

## Demo run

One short run, recorded in `docs/demo-run-1.jsonl`. The grown bot is on the `demo/run-1` branch; `main` keeps the seed.

| | dev | held-out |
| --- | --- | --- |
| seed | 7/40 (0.175) | 1/30 (0.033) |
| after 2 rounds | 30/40 (0.750) | 16/30 (0.533) |

Setup: two rounds of five agent proposers (Claude Sonnet, about 1.6 million tokens in total), offline overlap judge. Each proposer added one new knowledge module. Ten candidates were submitted: seven were kept and three rejected. One rejection was the leak check firing on a generic smalltalk reply that happened to equal a held-out reference; the other two did not raise the held-out score. The bot grew to 2906 lines.

Read these numbers with care:

- The held-out figure is optimistic. The person running the loop had read the held-out questions, saw per-category held-out scores between rounds, and wrote round-two briefs that named likely question shapes. That leaks held-out signal into the proposers. A clean run needs an operator who never sees the held-out set.
- The run was orchestrated by hand, not with `evolve run`. The gate replaces the whole bot on accept, so parallel candidates built on the same base would overwrite each other. Each candidate's new module was copied onto a fresh workspace of the current best before `evolve submit`. A rebase step in the loop is not implemented yet.
- Accepted changes can cost elsewhere: one accepted candidate dropped dev from 0.725 to 0.625, and science on held-out went from 4/4 to 3/4 by the end, because newer modules outbid older ones.
- The judge is word overlap. 0.533 means the reply shares enough words with the reference on 16 of 30 questions, not that 16 answers are correct.

## Limits

- The overlap judge is crude. It rewards word overlap with the reference, not correctness, and it will give credit to a wrong answer that reuses the question's words. Treat its win rate as a training signal, not a quality measure.
- Held-out secrecy is a convention, not a sandbox. The workspace never contains the held-out file, the gate runs candidate code in a separate interpreter with an empty working directory and a minimal environment, and the `ast` checks catch obvious tricks. But on one machine, a proposer runs as your user and can read `data/heldout.jsonl` if it goes looking, and static checks can be evaded. Run proposers you do not trust in a container or a separate account.
- Repeated hill-climbing on a 30-row held-out set will overfit it. Each accepted change is selected on those rows, so the held-out win rate drifts upward optimistically. Refresh the held-out data now and then.
- The seed bot is tiny: a few facts, greetings, a name memory, arithmetic and a fallback. Dev and held-out sets are small and were written by hand for everyday topics; they are not a benchmark of general ability.
- The reference answers are short everyday statements written for this project. Do not rely on them as advice.

## Licence

Apache-2.0. See `LICENSE`. Copyright 2026 ifbot contributors.
