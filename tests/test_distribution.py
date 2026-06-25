from meta_video_filter.distribution import distribute_videos


def make_rows(count):
    return [{"file": f"video_{i}.mp4", "final_score": i} for i in range(count)]


def test_distribution_empty():
    groups, later = distribute_videos(make_rows(0))
    assert groups == [[], []]
    assert later == []


def test_distribution_fewer_than_capacity():
    groups, later = distribute_videos(make_rows(7))
    group_a, group_b = groups
    assert len(group_a) == 3
    assert len(group_b) == 4
    assert later == []
    assert group_a[0]["file"] == "video_6.mp4"
    assert group_b[0]["file"] == "video_5.mp4"


def test_distribution_default_two_groups_ten_each():
    groups, later = distribute_videos(make_rows(23))
    group_a, group_b = groups
    assert len(group_a) == 10
    assert len(group_b) == 10
    assert len(later) == 3
    assert {row["group"] for row in group_a} == {"Group_A"}
    assert {row["group"] for row in group_b} == {"Group_B"}
    assert {row["group"] for row in later} == {"To_Be_Used_Later"}
    assert group_a[0]["export_index"] == 1
    assert group_a[0]["export_file"] == "1.mp4"


def test_distribution_allows_single_group():
    groups, later = distribute_videos(make_rows(5), group_count=1, videos_per_group=3)
    assert len(groups) == 1
    assert [row["file"] for row in groups[0]] == ["video_4.mp4", "video_3.mp4", "video_2.mp4"]
    assert {row["group"] for row in groups[0]} == {"Group_A"}
    assert [row["file"] for row in later] == ["video_1.mp4", "video_0.mp4"]


def test_distribution_custom_three_group_snake_split():
    groups, later = distribute_videos(make_rows(17), group_count=3, videos_per_group=5)
    assert [[row["file"] for row in group] for group in groups] == [
        ["video_16.mp4", "video_11.mp4", "video_10.mp4", "video_5.mp4", "video_4.mp4"],
        ["video_15.mp4", "video_12.mp4", "video_9.mp4", "video_6.mp4", "video_3.mp4"],
        ["video_14.mp4", "video_13.mp4", "video_8.mp4", "video_7.mp4", "video_2.mp4"],
    ]
    assert [row["file"] for row in later] == ["video_1.mp4", "video_0.mp4"]
    assert {row["group"] for row in groups[2]} == {"Group_C"}
