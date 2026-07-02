# How to Use This Skill

This guide explains how to run the ratchet-loop skill in plain terms. You do not need to read the
other files to use it; Claude reads those itself.

## What it does

The skill improves something you can measure, one step at a time, without ever making it worse. Each
round, it tries several different changes at once, scores all of them, and keeps only the single
change that scores better than what you started with. Then it repeats. Because it only keeps changes
that measurably win, the work can only move forward.

It suits any goal where a program can put a number on "better": making something faster, smaller, or
more accurate; improving a transcription; tuning a method. If you cannot measure the goal, this skill
is not the right tool.

## What you need before starting

1. A working copy of your project that Claude Code can open.
2. A clear goal stated as a number to raise or lower (for example, "lower the transcription error
   rate," "raise the accuracy score").
3. A way to measure that number automatically — a command, script, or benchmark that runs and reports
   the result. This measurement is the foundation of everything; if it is unreliable, the results will
   be too.
4. A set of examples to measure against.

## How to start it

Open your project in Claude Code and ask it to run the ratchet loop on your goal — for example,
"Use the ratchet-loop skill to lower the error rate on these manuscript pages." Claude will recognize
the task and begin the setup conversation below.

## The setup conversation (done once)

Before any work starts, Claude will ask you to settle a few things and write them into a file called
`ratchet-forum/config.yaml` in your project. You decide the values; Claude proposes sensible defaults. You
will be asked about:

- **The goal and how it is scored.** Which number(s) to optimize, and the exact command that measures
  them.
- **Hard limits that must never be broken.** Things a change is not allowed to damage no matter how
  good its score looks (for example, "the existing tests must still pass," "do not lose this feature").
- **Which files may be changed.** The parts of the project the loop is allowed to edit. Everything
  else — especially the scoring code and the example data — is locked so it cannot be altered.
- **Examples to optimize against, and examples held back for checking.** Some examples are used to
  improve against; others are kept aside to confirm a change is real and not just luck.
- **When to stop.** A target to reach, a budget of time or money, or a number of rounds. You can also
  let it run open-ended with a spending cap.

- **How involved you want to be.** You can let the loop run on its own, or stay in the loop as a
  reviewer. If you know the subject well, staying in the loop is valuable: each round produces not just
  scores but the *reasons* each change was supposed to work, and an expert can often tell a sound reason
  from a lucky number in a way the score alone cannot. You choose how often you're asked — every change,
  only when the loop and its built-in reviewer disagree, only on surprising results, or never.

Take your time here. Good limits and honest scoring are what keep the loop from "winning" in useless
ways.

## If you stay in the loop

When you've chosen to review, the loop hands you a short, focused decision each time — not a wall of
text. You'll see the change it wants to keep, the reason it was supposed to help, the score it got, and
the objections raised by the loop's own independent reviewer (a separate check that argues the other
side, so the loop doesn't just agree with itself). You can:

- accept it,
- reject it even though the number looks good, if the reasoning doesn't hold,
- rescue a change the loop discarded, if you think it was onto something,
- or add a note that steers what it tries next.

Your judgment is treated as the strongest version of that independent review. You're never required to
respond instantly, and the loop batches decisions so reviewing is quick.

## What happens each round

1. Claude tries several different approaches at once, each worked on in isolation so they do not
   interfere.
2. Each approach makes one focused change and is scored by your measurement.
3. Any change that breaks a hard limit, or that quietly edited the scoring or the data, is thrown out.
4. The best remaining change is checked by an independent reviewer (and by you, if you're in the loop)
   that argues the other side — could this be luck, could a rejected change have been better?
5. The change is kept **only if** it clearly beats the current best by more than normal measurement
   wobble, survives that challenge, and passes a double-check.
6. If a change is kept, it becomes the new starting point. If nothing is good enough this round, the
   starting point stays the same, which is normal.
7. Everything that happened — including the reasons and the objections — is written to a log, and the
   loop checks whether it is time to stop.

## Watching and controlling it

You can let it run on its own or stay involved. By default Claude will check in periodically — at
least whenever it accepts a change — and you can ask it to check in more or less often. You can ask to
see what it plans to try before a round, and you can ask for a single trial round with no changes
kept, just to see what it produces, before committing real time to it.

You can stop the loop at any point. Because every accepted change is a real saved checkpoint, nothing
in progress is lost when you stop.

## Where to find the results

- The current best version is the latest accepted checkpoint in your project's history.
- A running record of every round — what was tried, what it scored, and what was kept and why — is in
  `ratchet-forum/ledger.jsonl`. This is your full history and is also how the loop picks up again if it is
  interrupted.

## Picking it up again

If the loop stops or is interrupted, just ask Claude to resume it. It reads the log and the
configuration, finds the current best version, and continues from there. Nothing needs to be set up
twice.

## A note on honesty

Two things make or break this skill: the measurement must be trustworthy, and the hard limits must be
generous. If the score can be fooled, the loop will eventually fool it. Spend your setup effort there,
and the rest takes care of itself.
