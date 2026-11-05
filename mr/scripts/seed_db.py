from datetime import datetime, timezone

from app.db import site_db
from app.models import Post, Project

REAL_PROJECTS = (
    Project(
        slug="classifying-classical-composers",
        title="Classifying Classical Composers with a CNN-LSTM Model",
        description=(
            "A hybrid CNN-LSTM model that names the composer behind a piece of "
            "classical music from raw MIDI data — 97%+ accuracy across four composers."
        ),
        body=(
            "Team project for AAI-511 (Neural Networks and Deep Learning) at the "
            "University of San Diego, built with Anitra Hernandez and Lakshmi Deepti "
            "Pamula. The question: given a piece of music, can a model learn to tell "
            "Bach from Beethoven from Chopin from Mozart — not from a recording, but "
            "from the raw MIDI data underneath it.\n\n"
            "The dataset (Kaggle's midi_classic_music) was badly imbalanced — about "
            "1,020 Bach files against roughly 250 Mozart, 215 Beethoven, and 140 "
            "Chopin. We tokenized each composer's files with a REMI tokenizer, used "
            "pitch/velocity/duration augmentation to even out the underrepresented "
            "composers, then downsampled everyone to 100 files to keep the classes "
            "balanced. From there, each MIDI file was rendered to audio with "
            "FluidSynth, converted to a mel-spectrogram with librosa, and sliced into "
            "time-step images — turning the music into something a CNN could actually "
            "look at.\n\n"
            "The model itself combines both architectures: four convolutional layers "
            "pull feature maps out of each spectrogram image, which then feed into an "
            "LSTM instead of a standard fully-connected head, so the model learns how "
            "those features change across time rather than treating each slice in "
            "isolation. A linear layer and softmax over the four composers close it out.\n\n"
            "Trained on 240 images and tested on 80 held-out ones, the combined model "
            "hit accuracy, precision, recall, and F1 all above 97%, missing only two "
            "files. To check that the hybrid design was actually earning its keep, we "
            "also built standalone CNN and LSTM baselines: the CNN alone reached ~90%, "
            "and the LSTM alone started at a rough 38% until real optimization work — "
            "packed sequences instead of manual padding, a second bidirectional layer, "
            "gradient clipping — brought it up to 90% too. The combined CNN-LSTM still "
            "beat both outright, heavier preprocessing and all."
        ),
        url="https://github.com/mr-kelsey/su25-aai511-group6",
        report_pdf="/static/projects/classifying-classical-composers-report.pdf",
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
)

REAL_POSTS = (
    Post(
        slug="stop-asking-your-ai-agent-nicely",
        title="Stop Asking Your AI Agent Nicely",
        body=(
            "Every Claude Code project I run has a CLAUDE.md file — a list of rules "
            "I want followed: use the virtual environment, not the system "
            "interpreter; no wildcard imports; write tests first. It reads like "
            "policy. It isn't. It's a prompt. The model reads it, weighs it against "
            "everything else competing for its attention that turn, and does "
            "something that's probably compliant. Probably is the word that should "
            "worry a security person.\n\n"
            "I proved it to myself building this site. One of my rules is simple: "
            "\"Use .venv, not global python environment.\" Straightforward, "
            "unambiguous, sitting right there in the system prompt. And deep into a "
            "task — the model mid-flow, attention on the actual problem — it "
            "reached for a bare python3 -c \"...\" anyway. Not malicious, not even "
            "careless by LLM standards. Just a model doing what models do: "
            "generating the statistically reasonable next action, and \"run "
            "python3\" is reasonable in a vacuum. The instruction didn't fail "
            "because it was badly written. It failed because instructions in a "
            "prompt are advisory, no matter how emphatically you phrase them.\n\n"
            "Hooks are the fix, because they move enforcement outside the model "
            "entirely. A hook is a shell command the Claude Code harness runs at a "
            "defined point in the tool-call lifecycle — before a tool executes, "
            "after it finishes, on a prompt submission — and the harness, not the "
            "model, decides what happens with the hook's output. The model can't "
            "argue with a hook. It can't talk its way around one. It doesn't even "
            "see the hook coming; it proposes an action, the harness checks that "
            "action against the script, and the script returns a decision the "
            "model has to live with.\n\n"
            "In this repo that looks like .claude/hooks/block-system-python.sh, "
            "wired up in .claude/settings.json to fire on every Bash tool call "
            "before it runs. It parses the proposed command, unwraps the stuff "
            "that doesn't change what's actually executing — env var assignments, "
            "timeout, nice, xargs, and so on — and checks whether what's left "
            "starts with python or python3 instead of a venv path. If it does, it "
            "returns a JSON deny decision with a reason, and the command never "
            "runs. No model judgment involved. The rule either held or it didn't, "
            "and the hook is the only thing that gets a vote.\n\n"
            "The broader principle generalizes past this one script: write your "
            "rules file for the things that genuinely need judgment — "
            "collaboration style, architectural taste, how blunt to be in a commit "
            "message. Write a hook for the subset of rules that are mechanically "
            "checkable: a regex over a shell command, a file-existence check, a "
            "grep for a banned import pattern. If you can express the rule as "
            "\"check X, then allow or deny,\" it belongs in a hook, not a "
            "paragraph of prose the model has to remember to re-read every turn.\n\n"
            "It's the same instinct that got me into security in the first place: "
            "don't build your safety story on a layer that's allowed to be wrong "
            "some percentage of the time when a deterministic layer underneath it "
            "is available for free. A rules file is a policy. A hook is a control. "
            "I'd rather enforce the one I can actually verify."
        ),
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
)


def seed() -> None:
    for project in REAL_PROJECTS:
        site_db.projects.insert(project)
    for post in REAL_POSTS:
        site_db.posts.insert(post)


if __name__ == "__main__":
    seed()
