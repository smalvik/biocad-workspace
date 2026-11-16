import pytest

from race_probe.guard import isolated_parent, owned_child

SAFE = {
    "APP_ENV": "local",
    "ALLOW_DATABASE_TESTS": "1",
    "DATABASE_URL": "postgresql+asyncpg://biocad:biocad-test-only@postgres:5432/biocad",
}


@pytest.mark.parametrize(
    "change",
    [
        {"APP_ENV": "production"},
        {"ALLOW_DATABASE_TESTS": "0"},
        {"DATABASE_URL": "postgresql+asyncpg://biocad:other@postgres/biocad"},
        {"DATABASE_URL": "postgresql+asyncpg://biocad:biocad-test-only@remote/biocad"},
        {"DATABASE_URL": "postgresql+asyncpg://biocad:biocad-test-only@postgres/production"},
        {"DATABASE_URL": "malformed"},
    ],
)
def test_mutation_probe_refuses_non_disposable_environment(change):
    with pytest.raises(RuntimeError):
        isolated_parent(SAFE | change)


def test_disposable_creation_identity_is_required_before_mutation_or_drop():
    assert isolated_parent(SAFE).database == "biocad"
    name, marker = "wb08_" + "a" * 32, "wb08-owned:" + "a" * 32
    owned_child(name, marker, 12345, 12345)
    for args in (
        ("biocad", marker, 12345, 12345),
        (name, "foreign", 12345, 12345),
        (name, marker, 99999, 12345),
    ):
        with pytest.raises(RuntimeError):
            owned_child(*args)
