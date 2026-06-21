from meta_video_filter.distribution import distribute_videos


def make_rows(count):
    return [{"file": f"video_{i}.mp4", "final_score": i} for i in range(count)]


def test_distribution_empty():
    group_a, group_b, later = distribute_videos(make_rows(0))
    assert group_a == []
    assert group_b == []
    assert later == []


def test_distribution_fewer_than_ten():
    group_a, group_b, later = distribute_videos(make_rows(7))
    assert len(group_a) == 5
    assert len(group_b) == 2
    assert later == []
    assert group_a[0]["file"] == "video_6.mp4"


def test_distribution_more_than_twenty():
    group_a, group_b, later = distribute_videos(make_rows(23))
    assert len(group_a) == 10
    assert len(group_b) == 10
    assert len(later) == 3
    assert {row["group"] for row in group_a} == {"Group_A"}
    assert {row["group"] for row in group_b} == {"Group_B"}
    assert {row["group"] for row in later} == {"To_Be_Used_Later"}
