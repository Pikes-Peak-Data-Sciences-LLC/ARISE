"""Visualize how agent roles evolve from action_log.jsonl."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer

VIS_DIR = Path(__file__).resolve().parent
LOG_PATH = VIS_DIR.parents[2] / "action_log.jsonl"
IMAGES_DIR = VIS_DIR / "images"


def role_title(content: str) -> str:
    return content.split(":", 1)[0].strip() or content.strip()


def load_role_events(log_path: Path) -> list[dict]:
    events = []
    with log_path.open(encoding="utf-8") as f:
        for step, line in enumerate(f):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("action") != "assign_role":
                continue
            content = (record.get("content") or "").strip()
            if not content:
                continue
            events.append(
                {
                    "step": step,
                    "agent_id": int(record["agent_id"]),
                    "role": role_title(content),
                }
            )
    return events


def main() -> None:
    events = load_role_events(LOG_PATH)

    titles = [e["role"] for e in events]
    embeddings = TfidfVectorizer(ngram_range=(1, 2)).fit_transform(titles).toarray()

    n = len(embeddings)
    if n == 1:
        coords = np.zeros((1, 2))
    else:
        coords = PCA(n_components=min(2, n)).fit_transform(embeddings)
        if coords.shape[1] == 1:
            coords = np.column_stack([coords[:, 0], np.zeros(n)])

    cmap = plt.get_cmap("tab10")
    by_agent: dict[int, list[int]] = defaultdict(list)
    for i, event in enumerate(events):
        by_agent[event["agent_id"]].append(i)

    fig, ax = plt.subplots(figsize=(10, 7))
    for agent_id, indices in sorted(by_agent.items()):
        color = cmap(agent_id % 10)
        xs, ys = coords[indices, 0], coords[indices, 1]
        ax.plot(xs, ys, color=color, alpha=0.4, linewidth=1.5)
        for i in range(len(indices) - 1):
            ax.annotate(
                "",
                xy=(xs[i + 1], ys[i + 1]),
                xytext=(xs[i], ys[i]),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2),
            )
        ax.scatter(xs, ys, c=[color], s=80, edgecolors="white", label=f"Agent {agent_id}")
        for j, idx in enumerate(indices):
            ax.annotate(
                f"{j + 1}. {events[idx]['role']}",
                (coords[idx, 0], coords[idx, 1]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
                color=color,
            )

    ax.set_title("Agent Role Evolution")
    ax.set_xlabel("PCA 1")
    ax.set_ylabel("PCA 2")
    ax.legend()
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = IMAGES_DIR / "role_embeddings.png"
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
