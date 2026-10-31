import os
import uuid

# must be set before the app is imported: a throw-away SQLite file, pre-filled by the startup seed
os.environ["DATABASE_URL"] = f"sqlite:///./test_{uuid.uuid4().hex}.db"
os.environ["AUTO_SEED"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app import models  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed_if_empty  # noqa: E402
from app.seed_data import CRIMINALS, HUNTS  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
    engine.dispose()
    os.remove(os.environ["DATABASE_URL"].replace("sqlite:///./", ""))


def criminal_id(client, nickname):
    items = client.get("/api/criminals/").json()
    return next(c["id"] for c in items if c["nickname"] == nickname)


def new_hunt(client, **overrides):
    body = {"criminal_id": criminal_id(client, "Lazy Jack"), "success": False, "notes": "test entry"}
    body.update(overrides)
    r = client.post("/api/hunts/", json=body)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------- database / seed
def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "database": "up"}


def test_database_is_prefilled(client):
    assert len(client.get("/api/criminals/").json()) == len(CRIMINALS) >= 5
    assert len(client.get("/api/hunts/").json()) == len(HUNTS) >= 10


def test_seed_is_idempotent(client):
    with SessionLocal() as db:
        assert seed_if_empty(db) is False
    assert len(client.get("/api/criminals/").json()) == len(CRIMINALS)


def test_one_to_many_relationship(client):
    with SessionLocal() as db:
        comet = db.scalars(select(models.WantedCriminal).where(models.WantedCriminal.nickname == "Crimson Comet")).one()
        assert len(comet.hunts) == 3
        assert all(h.criminal is comet for h in comet.hunts)


# ---------------------------------------------------------------- criminals: list / filter / sort
def test_list_default_order_is_by_id(client):
    ids = [c["id"] for c in client.get("/api/criminals/").json()]
    assert ids == sorted(ids)


def test_list_without_trailing_slash_redirects(client):
    assert client.get("/api/criminals").status_code == 200


def test_criminal_fields(client):
    c = client.get("/api/criminals/").json()[0]
    assert set(c) == {
        "id", "name", "nickname", "reward", "latitude", "longitude",
        "location_note", "difficulty", "armed", "has_crew", "escape_master",
    }


def test_unknown_name_and_note_only_location_are_null(client):
    items = {c["nickname"]: c for c in client.get("/api/criminals/").json()}
    assert items["Lazy Jack"]["name"] is None
    assert items["Dr. Nebula"]["latitude"] is None and items["Dr. Nebula"]["location_note"]


def test_reward_filters(client):
    assert all(c["reward"] >= 5000 for c in client.get("/api/criminals/?min_reward=5000").json())
    assert all(c["reward"] <= 20000 for c in client.get("/api/criminals/?max_reward=20000").json())
    both = client.get("/api/criminals/?min_reward=10000&max_reward=50000").json()
    assert both and all(10000 <= c["reward"] <= 50000 for c in both)
    # bounds are inclusive
    assert [c["reward"] for c in client.get("/api/criminals/?min_reward=3500&max_reward=3500").json()] == [3500]


def test_boolean_filters(client):
    total = len(client.get("/api/criminals/").json())
    for flag in ("armed", "has_crew", "escape_master"):
        yes = client.get(f"/api/criminals/?{flag}=true").json()
        no = client.get(f"/api/criminals/?{flag}=false").json()
        assert yes and no
        assert all(c[flag] is True for c in yes)
        assert all(c[flag] is False for c in no)  # false must really filter, not be ignored
        assert len(yes) + len(no) == total


def test_sorting(client):
    asc = [c["reward"] for c in client.get("/api/criminals/?sort=reward").json()]
    desc = [c["reward"] for c in client.get("/api/criminals/?sort=-reward").json()]
    assert asc == sorted(asc) and desc == sorted(desc, reverse=True)
    assert asc == desc[::-1]


def test_filters_work_together(client):
    r = client.get("/api/criminals/?min_reward=5000&armed=true&sort=-reward")
    assert r.status_code == 200
    assert [c["nickname"] for c in r.json()] == ["Crimson Comet", "Madame Static", "Iron Mama", "Silent Rook"]

    r = client.get("/api/criminals/?has_crew=true&escape_master=true&min_reward=10000&max_reward=100000&sort=reward")
    assert [c["nickname"] for c in r.json()] == ["Madame Static", "Dr. Nebula"]

    assert client.get("/api/criminals/?min_reward=1000000").json() == []


@pytest.mark.parametrize(
    "query",
    [
        "sort=cheapest", "min_reward=abc", "max_reward=1.5", "min_reward=-1",
        "min_reward=99999999999999999999", "armed=maybe", "has_crew=2", "min_reward=9000&max_reward=100",
    ],
)
def test_invalid_query_parameters_give_422(client, query):
    assert client.get(f"/api/criminals/?{query}").status_code == 422


# ---------------------------------------------------------------- criminals: details
def test_criminal_details(client):
    cid = criminal_id(client, "Crimson Comet")
    r = client.get(f"/api/criminals/{cid}/")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == cid and body["reward"] == 120000 and body["difficulty"] == 9
    assert body["armed"] is True and body["has_crew"] is True and body["escape_master"] is True


@pytest.mark.parametrize("bad_id, expected", [(9999, 404), (0, 404), (-5, 404), (99999999999999999999, 404), ("abc", 422)])
def test_criminal_details_invalid_id(client, bad_id, expected):
    assert client.get(f"/api/criminals/{bad_id}/").status_code == expected


# ---------------------------------------------------------------- hunt logs: CRUD
def test_hunt_crud_flow(client):
    cid = criminal_id(client, "Silent Rook")

    # create
    r = client.post("/api/hunts/", json={"criminal_id": cid, "success": False, "notes": "Target escaped through an asteroid field."})
    assert r.status_code == 201, r.text
    hunt = r.json()
    assert hunt["criminal_id"] == cid and hunt["success"] is False and hunt["notes"].startswith("Target escaped")
    assert hunt["id"] and hunt["created_at"]
    hid = hunt["id"]

    # read
    assert client.get(f"/api/hunts/{hid}/").json()["id"] == hid
    assert hid in [h["id"] for h in client.get("/api/hunts/").json()]

    # update: only the sent fields change
    r = client.patch(f"/api/hunts/{hid}/", json={"success": True})
    assert r.status_code == 200 and r.json()["success"] is True and r.json()["notes"].startswith("Target escaped")
    r = client.patch(f"/api/hunts/{hid}/", json={"notes": "Captured after all."})
    assert r.status_code == 200 and r.json()["notes"] == "Captured after all." and r.json()["success"] is True
    r = client.patch(f"/api/hunts/{hid}/", json={"success": False, "notes": ""})
    assert r.status_code == 200 and r.json()["success"] is False and r.json()["notes"] == ""

    # delete
    assert client.delete(f"/api/hunts/{hid}/").status_code == 204
    assert client.get(f"/api/hunts/{hid}/").status_code == 404
    assert client.delete(f"/api/hunts/{hid}/").status_code == 404


def test_created_at_is_generated_by_the_server(client):
    hunt = new_hunt(client, created_at="2000-01-01T00:00:00Z")  # the client value must be ignored
    assert not hunt["created_at"].startswith("2000")
    fetched = client.get(f"/api/hunts/{hunt['id']}/").json()
    assert not fetched["created_at"].startswith("2000")
    # the client cannot change it later either
    r = client.patch(f"/api/hunts/{hunt['id']}/", json={"notes": "x", "created_at": "1999-01-01T00:00:00Z"})
    assert r.status_code == 200 and not r.json()["created_at"].startswith("1999")
    client.delete(f"/api/hunts/{hunt['id']}/")


def test_notes_are_optional_on_create(client):
    hunt = new_hunt(client, notes="")
    assert hunt["notes"] == ""
    r = client.post("/api/hunts/", json={"criminal_id": hunt["criminal_id"], "success": True})
    assert r.status_code == 201 and r.json()["notes"] == ""
    client.delete(f"/api/hunts/{hunt['id']}/")
    client.delete(f"/api/hunts/{r.json()['id']}/")


# ---------------------------------------------------------------- hunt logs: filter
def test_filter_hunts_by_criminal(client):
    cid = criminal_id(client, "Crimson Comet")
    items = client.get(f"/api/hunts/?criminal_id={cid}").json()
    assert len(items) == 3 and all(h["criminal_id"] == cid for h in items)


def test_filter_hunts_unknown_criminal_gives_empty_list(client):
    assert client.get("/api/hunts/?criminal_id=9999").json() == []
    assert client.get("/api/hunts/?criminal_id=99999999999999999999").json() == []


def test_filter_hunts_invalid_criminal_id(client):
    assert client.get("/api/hunts/?criminal_id=abc").status_code == 422


# ---------------------------------------------------------------- hunt logs: validation
@pytest.mark.parametrize(
    "body",
    [
        {"criminal_id": 9999, "success": False, "notes": "no such criminal"},
        {"criminal_id": 0, "success": False},
        {"criminal_id": -1, "success": False},
        {"criminal_id": 99999999999999999999, "success": False},
        {"success": False, "notes": "criminal_id is missing"},
        {"criminal_id": 1, "notes": "success is missing"},
        {"criminal_id": 1, "success": "yes"},
        {"criminal_id": 1, "success": 1},
        {"criminal_id": "abc", "success": True},
        {"criminal_id": 1.5, "success": True},
        {"criminal_id": None, "success": True},
        {"criminal_id": 1, "success": True, "notes": 123},
        {"criminal_id": 1, "success": True, "notes": "x" * 5001},
        {},
        [],
    ],
)
def test_create_hunt_invalid_body_gives_422(client, body):
    before = len(client.get("/api/hunts/").json())
    assert client.post("/api/hunts/", json=body).status_code == 422
    assert len(client.get("/api/hunts/").json()) == before  # nothing was saved


def test_create_hunt_malformed_json_gives_422(client):
    r = client.post("/api/hunts/", content="{not json", headers={"Content-Type": "application/json"})
    assert r.status_code == 422


@pytest.mark.parametrize("body", [{}, {"success": None}, {"notes": None}, {"success": "yes"}, {"notes": 5}, {"unknown": 1}])
def test_update_hunt_invalid_body_gives_422(client, body):
    hunt = new_hunt(client)
    assert client.patch(f"/api/hunts/{hunt['id']}/", json=body).status_code == 422
    client.delete(f"/api/hunts/{hunt['id']}/")


@pytest.mark.parametrize("bad_id, expected", [(9999, 404), (0, 404), (99999999999999999999, 404), ("abc", 422)])
def test_hunt_invalid_id(client, bad_id, expected):
    assert client.get(f"/api/hunts/{bad_id}/").status_code == expected
    assert client.patch(f"/api/hunts/{bad_id}/", json={"success": True}).status_code == expected
    assert client.delete(f"/api/hunts/{bad_id}/").status_code == expected
