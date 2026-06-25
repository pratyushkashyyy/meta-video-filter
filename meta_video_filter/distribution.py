from __future__ import annotations

VideoRow = dict[str, object]

MIN_GROUP_COUNT = 1
MAX_GROUP_COUNT = 10
MIN_VIDEOS_PER_GROUP = 1
MAX_VIDEOS_PER_GROUP = 100


def validate_group_settings(group_count: int, videos_per_group: int) -> None:
    if not MIN_GROUP_COUNT <= group_count <= MAX_GROUP_COUNT:
        raise ValueError(f"Groups must be between {MIN_GROUP_COUNT} and {MAX_GROUP_COUNT}.")
    if not MIN_VIDEOS_PER_GROUP <= videos_per_group <= MAX_VIDEOS_PER_GROUP:
        raise ValueError(
            f"Videos per group must be between {MIN_VIDEOS_PER_GROUP} and {MAX_VIDEOS_PER_GROUP}."
        )


def group_name(index: int) -> str:
    return f"Group_{chr(ord('A') + index)}"


def _snake_group_indexes(group_count: int) -> list[int]:
    forward = list(range(group_count))
    if group_count == 1:
        return forward
    return forward + forward[-1::-1]


def distribute_videos(
    rows: list[VideoRow],
    group_count: int = 2,
    videos_per_group: int = 10,
) -> tuple[list[list[VideoRow]], list[VideoRow]]:
    """Return selected groups and later videos sorted by descending score."""
    validate_group_settings(group_count, videos_per_group)
    if not rows:
        return [[] for _ in range(group_count)], []

    ranked = sorted(rows, key=lambda row: float(row.get("final_score", 0)), reverse=True)
    groups: list[list[VideoRow]] = [[] for _ in range(group_count)]
    later: list[VideoRow] = []
    snake_indexes = _snake_group_indexes(group_count)
    snake_position = 0

    for row in ranked:
        target_index = None
        for offset in range(len(snake_indexes)):
            group_index = snake_indexes[(snake_position + offset) % len(snake_indexes)]
            if len(groups[group_index]) < videos_per_group:
                target_index = group_index
                snake_position = (snake_position + offset + 1) % len(snake_indexes)
                break

        if target_index is None:
            later.append({**row, "group": "To_Be_Used_Later", "export_index": "", "export_file": ""})
            continue

        export_index = len(groups[target_index]) + 1
        groups[target_index].append(
            {
                **row,
                "group": group_name(target_index),
                "export_index": export_index,
                "export_file": f"{export_index}.mp4",
            }
        )

    return groups, later
