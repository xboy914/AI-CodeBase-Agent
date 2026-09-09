from codebase_agent.store import build_index_plan


def test_first_index_marks_every_file_changed():
    plan = build_index_plan(
        {"src/app.ts": "hash-a", "src/auth.ts": "hash-b"},
        {},
    )

    assert plan.changed == {"src/app.ts", "src/auth.ts"}
    assert plan.unchanged == set()
    assert plan.deleted == set()


def test_reindex_skips_unchanged_files():
    plan = build_index_plan(
        {"src/app.ts": "same", "src/auth.ts": "new"},
        {"src/app.ts": "same", "src/auth.ts": "old"},
    )

    assert plan.changed == {"src/auth.ts"}
    assert plan.unchanged == {"src/app.ts"}
    assert plan.deleted == set()


def test_deleted_files_are_scheduled_for_cleanup():
    plan = build_index_plan(
        {"src/app.ts": "same"},
        {"src/app.ts": "same", "src/removed.ts": "old"},
    )

    assert plan.changed == set()
    assert plan.unchanged == {"src/app.ts"}
    assert plan.deleted == {"src/removed.ts"}


def test_changed_and_deleted_sets_do_not_overlap():
    plan = build_index_plan(
        {"src/changed.ts": "new", "src/new.ts": "new"},
        {"src/changed.ts": "old", "src/deleted.ts": "old"},
    )

    assert plan.changed == {"src/changed.ts", "src/new.ts"}
    assert plan.deleted == {"src/deleted.ts"}
    assert plan.changed.isdisjoint(plan.deleted)
