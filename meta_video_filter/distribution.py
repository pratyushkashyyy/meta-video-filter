from __future__ import annotations

VideoRow = dict[str, object]


def _with_group(rows: list[VideoRow], group: str) -> list[VideoRow]:
    return [{**row, "group": group} for row in rows]


def distribute_videos(rows: list[VideoRow]) -> tuple[list[VideoRow], list[VideoRow], list[VideoRow]]:
    """Return Group A, Group B, and later videos sorted by descending score."""
    if not rows:
        return [], [], []

    ranked = sorted(rows, key=lambda row: float(row.get("final_score", 0)), reverse=True)
    top_a = ranked[0:5]
    top_b = ranked[5:10]
    remaining = ranked[10:]

    group_a = top_a + remaining[0:5]
    group_b = top_b + remaining[5:10]
    later = remaining[10:]

    return (
        _with_group(group_a, "Group_A"),
        _with_group(group_b, "Group_B"),
        _with_group(later, "To_Be_Used_Later"),
    )
