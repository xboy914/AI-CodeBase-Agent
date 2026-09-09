from codebase_agent.store import build_index_plan


def test_index_plan_classifies_changed_unchanged_and_deleted_files():
    plan = build_index_plan(
        current={"same.ts": "a", "changed.ts": "new", "added.ts": "first"},
        stored={"same.ts": "a", "changed.ts": "old", "deleted.ts": "gone"},
    )

    assert plan.unchanged == {"same.ts"}
    assert plan.changed == {"changed.ts", "added.ts"}
    assert plan.deleted == {"deleted.ts"}


def test_first_index_marks_every_file_as_changed():
    plan = build_index_plan(current={"a.ts": "1", "b.tsx": "2"}, stored={})

    assert plan.changed == {"a.ts", "b.tsx"}
    assert plan.unchanged == set()
    assert plan.deleted == set()


def test_noop_index_has_no_changed_or_deleted_files():
    hashes = {"a.ts": "1"}

    plan = build_index_plan(current=hashes, stored=hashes)

    assert plan.changed == set()
    assert plan.unchanged == {"a.ts"}
    assert plan.deleted == set()
