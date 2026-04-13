from __future__ import annotations

import json
import os
from datetime import date, datetime

from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

from db import db, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SCRIMTRACKER_SECRET", "dev-change-me")


AGENT_ROLES: dict[str, str] = {
    # Controllers
    "Astra": "controller",
    "Brimstone": "controller",
    "Clove": "controller",
    "Harbor": "controller",
    "Omen": "controller",
    "Viper": "controller",
    # Duelists
    "Iso": "duelist",
    "Jett": "duelist",
    "Neon": "duelist",
    "Phoenix": "duelist",
    "Raze": "duelist",
    "Reyna": "duelist",
    "Waylay": "duelist",
    "Yoru": "duelist",
    # Initiators
    "Breach": "initiator",
    "Fade": "initiator",
    "Gekko": "initiator",
    "KAY/O": "initiator",
    "Skye": "initiator",
    "Sova": "initiator",
    "Tejo": "initiator",
    # Sentinels
    "Chamber": "sentinel",
    "Cypher": "sentinel",
    "Deadlock": "sentinel",
    "Killjoy": "sentinel",
    "Sage": "sentinel",
    "Veto": "sentinel",
    "Vyse": "sentinel",
}

ROLE_ORDER = {"duelist": 0, "initiator": 1, "controller": 2, "sentinel": 3}

# Agent display icons from valorant-api.com
AGENT_ICONS: dict[str, str] = {
    "Astra": "https://media.valorant-api.com/agents/41fb69c1-4189-7b37-f117-bcaf1e96f1bf/displayicon.png",
    "Breach": "https://media.valorant-api.com/agents/5f8d3a7f-467b-97f3-062c-13acf203c006/displayicon.png",
    "Brimstone": "https://media.valorant-api.com/agents/9f0d8ba9-4140-b941-57d3-a7ad57c6b417/displayicon.png",
    "Chamber": "https://media.valorant-api.com/agents/22697a3d-45bf-8dd7-4fec-84a9e28c69d7/displayicon.png",
    "Clove": "https://media.valorant-api.com/agents/1dbf2edd-4729-0984-3115-daa5eed44993/displayicon.png",
    "Cypher": "https://media.valorant-api.com/agents/117ed9e3-49f3-6512-3ccf-0cada7e3823b/displayicon.png",
    "Deadlock": "https://media.valorant-api.com/agents/cc8b64c8-4b25-4ff9-6e7f-37b4da43d235/displayicon.png",
    "Fade": "https://media.valorant-api.com/agents/dade69b4-4f5a-8528-247b-219e5a1facd6/displayicon.png",
    "Gekko": "https://media.valorant-api.com/agents/e370fa57-4757-3604-3648-499e1f642d3f/displayicon.png",
    "Harbor": "https://media.valorant-api.com/agents/95b78ed7-4637-86d9-7e41-71ba8c293152/displayicon.png",
    "Iso": "https://media.valorant-api.com/agents/0e38b510-41a8-5780-5e8f-568b2a4f2d6c/displayicon.png",
    "Jett": "https://media.valorant-api.com/agents/add6443a-41bd-e414-f6ad-e58d267f4e95/displayicon.png",
    "KAY/O": "https://media.valorant-api.com/agents/601dbbe7-43ce-be57-2a40-4abd24953621/displayicon.png",
    "Killjoy": "https://media.valorant-api.com/agents/1e58de9c-4950-5125-93e9-a0aee9f98746/displayicon.png",
    "Neon": "https://media.valorant-api.com/agents/bb2a4828-46eb-8cd1-e765-15848195d751/displayicon.png",
    "Omen": "https://media.valorant-api.com/agents/8e253930-4c05-31dd-1b6c-968525494517/displayicon.png",
    "Phoenix": "https://media.valorant-api.com/agents/eb93336a-449b-9c1b-0a54-a891f7921d69/displayicon.png",
    "Raze": "https://media.valorant-api.com/agents/f94c3b30-42be-e959-889c-5aa313dba261/displayicon.png",
    "Reyna": "https://media.valorant-api.com/agents/a3bfb853-43b2-7238-a4f1-ad90e9e46bcc/displayicon.png",
    "Sage": "https://media.valorant-api.com/agents/569fdd95-4d10-43ab-ca70-79becc718b46/displayicon.png",
    "Skye": "https://media.valorant-api.com/agents/6f2a04ca-43e0-be17-7f36-b3908627744d/displayicon.png",
    "Sova": "https://media.valorant-api.com/agents/320b2a48-4d9b-a075-30f1-1f93a9b638fa/displayicon.png",
    "Tejo": "https://media.valorant-api.com/agents/b444168c-4e35-8076-db47-ef9bf368f384/displayicon.png",
    "Veto": "https://media.valorant-api.com/agents/92eeef5d-43b5-1d4a-8d03-b3927a09034b/displayicon.png",
    "Viper": "https://media.valorant-api.com/agents/707eab51-4836-f488-046a-cda6bf494859/displayicon.png",
    "Vyse": "https://media.valorant-api.com/agents/efba5359-4016-a1e5-7626-b1ae76895940/displayicon.png",
    "Waylay": "https://media.valorant-api.com/agents/df1cb487-4902-002e-5c17-d28e83e78588/displayicon.png",
    "Yoru": "https://media.valorant-api.com/agents/7f94d92c-4234-0a36-9646-3a87eb8b5c89/displayicon.png",
}

# Map icons from valorant-api.com (splash = loading screen art, not map minimap)
MAP_ICONS: dict[str, str] = {
    "Abyss": "https://media.valorant-api.com/maps/224b0a95-48b9-f703-1bd8-67aca101a61f/splash.png",
    "Ascent": "https://media.valorant-api.com/maps/7eaecc1b-4337-bbf6-6ab9-04b8f06b3319/splash.png",
    "Bind": "https://media.valorant-api.com/maps/2c9d57ec-4431-9c5e-2939-8f9ef6dd5cba/splash.png",
    "Breeze": "https://media.valorant-api.com/maps/2fb9a4fd-47b8-4e7d-a969-74b4046ebd53/splash.png",
    "Corrode": "https://media.valorant-api.com/maps/1c18ab1f-420d-0d8b-71d0-77ad3c439115/splash.png",
    "District": "https://media.valorant-api.com/maps/690b3ed2-4dff-945b-8223-6da834e30d24/splash.png",
    "Drift": "https://media.valorant-api.com/maps/2c09d728-42d5-30d8-43dc-96a05cc7ee9d/splash.png",
    "Fracture": "https://media.valorant-api.com/maps/b529448b-4d60-346e-e89e-00a4c527a405/splash.png",
    "Glitch": "https://media.valorant-api.com/maps/d6336a5a-428f-c591-98db-c8a291159134/splash.png",
    "Haven": "https://media.valorant-api.com/maps/2bee0dc9-4ffe-519b-1cbd-7fbe763a6047/splash.png",
    "Icebox": "https://media.valorant-api.com/maps/e2ad5c54-4114-a870-9641-8ea21279579a/splash.png",
    "Kasbah": "https://media.valorant-api.com/maps/12452a9d-48c3-0b02-e7eb-0381c3520404/splash.png",
    "Lotus": "https://media.valorant-api.com/maps/2fe4ed3a-450a-948b-6d6b-e89a78e680a9/splash.png",
    "Pearl": "https://media.valorant-api.com/maps/fd267378-4d1d-484f-ff52-77821ed10dc2/splash.png",
    "Piazza": "https://media.valorant-api.com/maps/de28aa9b-4cbe-1003-320e-6cb3ec309557/splash.png",
    "Split": "https://media.valorant-api.com/maps/d960549e-485c-e861-8d71-aa9d1aed12a2/splash.png",
    "Sunset": "https://media.valorant-api.com/maps/92584fbe-486a-b1b2-9faa-39b0f486b498/splash.png",
}

# Competitive maps only (excludes HURM: District, Drift, Glitch, Kasbah, Piazza)
COMPETITIVE_MAPS = [
    "Abyss", "Ascent", "Bind", "Breeze", "Corrode", "Fracture",
    "Haven", "Icebox", "Lotus", "Pearl", "Split", "Sunset",
]


def agent_icon_url(agent: str | None) -> str | None:
    """Return the display icon URL for an agent, or None if unknown."""
    if not agent or not (name := agent.strip()):
        return None
    return AGENT_ICONS.get(name)


# Map name aliases (typos / alternate spellings) -> canonical name
MAP_NAME_ALIASES: dict[str, str] = {
    "abys": "Abyss",
    "abbys": "Abyss",
    "abyss": "Abyss",
}


def map_icon_url(map_name: str | None) -> str | None:
    """Return the display icon URL for a map, or None if unknown."""
    if not map_name or not (name := map_name.strip()):
        return None
    # Try exact match first
    url = MAP_ICONS.get(name)
    if url:
        return url
    # Try case-insensitive alias
    canonical = MAP_NAME_ALIASES.get(name.casefold())
    if canonical:
        return MAP_ICONS.get(canonical)
    # Try case-insensitive direct lookup
    for key, val in MAP_ICONS.items():
        if key.casefold() == name.casefold():
            return val
    return None


def agent_role(agent: str | None) -> str | None:
    if not agent:
        return None
    return AGENT_ROLES.get(agent.strip())


def agent_role_class(agent: str | None) -> str:
    role = agent_role(agent)
    if not role:
        return "agent-unknown"
    return f"agent-{role}"


def _agent_sort_key(agent: str | None, *, picks: int | None = None):
    role = agent_role(agent)
    role_rank = ROLE_ORDER.get(role or "", 99)
    name = (agent or "").strip()
    # Within role: higher picks first (when available), then alphabetical.
    return (role_rank, -(picks or 0), name.casefold())


def _get_list_setting(conn, key: str) -> list[str]:
    row = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
    if not row or not row["value"]:
        return []
    try:
        val = json.loads(row["value"])
        return list(val) if isinstance(val, list) else []
    except json.JSONDecodeError:
        return []


def _set_list_setting(conn, key: str, value: list) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
        (key, json.dumps(value)),
    )


@app.before_request
def _require_auth():
    if request.endpoint in ("login", "login_post", "static") or request.path.startswith("/static/"):
        return None
    if request.endpoint is None:
        return None
    if session.get("auth"):
        return None
    return redirect(url_for("login", next=request.full_path.rstrip("?")))


@app.get("/login")
def login():
    return render_template("login.html")


def _safe_redirect_url(url: str | None) -> str | None:
    """Return url only if it's a safe relative path (no open redirect)."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if url.startswith("//") or ":" in url.split("/")[0]:
        return None  # reject protocol-relative or absolute URLs
    if url.startswith("/") and not url.startswith("//"):
        return url
    return None


@app.post("/login")
def login_post():
    if request.form.get("password") == "hasloczycos123":
        session["auth"] = True
        next_url = _safe_redirect_url(request.args.get("next"))
        return redirect(next_url or url_for("scrims_list"))
    return render_template("login.html", error="Wrong password"), 401


@app.get("/logout")
def logout():
    session.pop("auth", None)
    return redirect(url_for("login"))


@app.template_filter("skill_filter_url")
def _skill_filter_url(target: str, skill_val: str) -> str:
    """Build analytics URL with kind, skill, and optionally map from current request."""
    kind = request.args.get("kind", "scrim")
    kwargs: dict = {"kind": kind, "skill": skill_val}
    if target == "analytics_players" and request.args.get("map"):
        kwargs["map"] = request.args.get("map")
    return url_for(target, **kwargs)


@app.context_processor
def _inject_agent_roles():
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    with db() as conn:
        roster = _roster_players(conn)
    return {
        "agent_role_class": agent_role_class,
        "agent_role": agent_role,
        "agent_icon_url": agent_icon_url,
        "map_icon_url": map_icon_url,
        "format_date": _format_date,
        "match_detail_url": _match_detail_url,
        "map_new_url": _map_new_url,
        "map_edit_url": _map_edit_url,
        "player_stat_new_url": _player_stat_new_url,
        "player_stat_edit_url": _player_stat_edit_url,
        "nav_roster": roster,
        "nav_kind": kind,
    }


def _format_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        dt = datetime.strptime(value, "%Y-%m-%d")
        return dt.strftime("%b %d, %Y")
    except ValueError:
        return value or ""


def _int_or_none(v: str | None) -> int | None:
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    return int(v)


def _float_or_none(v: str | None) -> float | None:
    if v is None:
        return None
    v = v.strip()
    if v == "":
        return None
    return float(v)


@app.get("/")
def home():
    return redirect(url_for("scrims_list"))


def _matches_list(match_kind: str):
    q = (request.args.get("q") or "").strip()
    with db() as conn:
        if q:
            scrims = conn.execute(
                """
                SELECT * FROM scrims
                WHERE match_kind = ?
                  AND (
                    opponent LIKE ?
                    OR notes LIKE ?
                    OR patch LIKE ?
                    OR event_name LIKE ?
                  )
                ORDER BY played_on DESC, id DESC
                """,
                (match_kind, f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            scrims = conn.execute(
                "SELECT * FROM scrims WHERE match_kind = ? ORDER BY played_on DESC, id DESC",
                (match_kind,),
            ).fetchall()

        scrim_ids = [s["id"] for s in scrims]
        maps_by_scrim: dict[int, list[dict]] = {sid: [] for sid in scrim_ids}
        agents_by_map: dict[int, list[list[dict]]] = {sid: [] for sid in scrim_ids}
        if scrim_ids:
            placeholders = ",".join(["?"] * len(scrim_ids))
            rows = conn.execute(
                f"""
                SELECT
                  sm.id AS map_id,
                  scrim_id, map_name,
                  our_score, opp_score,
                  our_attack_rounds, our_def_rounds,
                  opp_attack_rounds, opp_def_rounds,
                  our_pistol_atk_won, our_pistol_def_won
                FROM scrim_maps sm
                WHERE scrim_id IN ({placeholders})
                ORDER BY scrim_id DESC, sm.id ASC
                """,
                tuple(scrim_ids),
            ).fetchall()
            for r in rows:
                maps_by_scrim[r["scrim_id"]].append(
                    {
                        "map_id": r["map_id"],
                        "map_name": r["map_name"],
                        "our_score": r["our_score"],
                        "opp_score": r["opp_score"],
                        "our_attack_rounds": r["our_attack_rounds"],
                        "our_def_rounds": r["our_def_rounds"],
                        "opp_attack_rounds": r["opp_attack_rounds"],
                        "opp_def_rounds": r["opp_def_rounds"],
                        "our_pistol_atk_won": r["our_pistol_atk_won"],
                        "our_pistol_def_won": r["our_pistol_def_won"],
                    }
                )

            # Agents per map (repeat agents per map if same agent played multiple maps)
            agent_rows = conn.execute(
                f"""
                SELECT
                  sm.id AS scrim_map_id,
                  sm.scrim_id AS scrim_id,
                  p.agent AS agent,
                  COUNT(*) AS picks
                FROM player_map_stats p
                JOIN scrim_maps sm ON sm.id = p.scrim_map_id
                WHERE sm.scrim_id IN ({placeholders})
                  AND p.agent IS NOT NULL
                  AND TRIM(p.agent) <> ''
                GROUP BY sm.id, p.agent
                ORDER BY sm.scrim_id DESC, sm.id ASC, picks DESC, p.agent COLLATE NOCASE ASC
                """,
                tuple(scrim_ids),
            ).fetchall()
            # agents_by_map[scrim_id] = [agents_for_map0, agents_for_map1, ...]
            for sid in scrim_ids:
                maps_list = maps_by_scrim[sid]
                for _ in maps_list:
                    agents_by_map[sid].append([])
            for r in agent_rows:
                sid = r["scrim_id"]
                map_id = r["scrim_map_id"]
                maps_list = maps_by_scrim[sid]
                map_idx = next(i for i, m in enumerate(maps_list) if m["map_id"] == map_id)
                agents_by_map[sid][map_idx].append({"agent": r["agent"], "picks": r["picks"]})
            for sid, map_agents in agents_by_map.items():
                for agents in map_agents:
                    agents.sort(
                        key=lambda a: _agent_sort_key(a.get("agent"), picks=a.get("picks"))
                    )

    return render_template(
        "scrims_list.html",
        scrims=scrims,
        q=q,
        maps_by_scrim=maps_by_scrim,
        agents_by_map=agents_by_map,
        match_kind=match_kind,
    )


@app.get("/scrims")
def scrims_list():
    return _matches_list("scrim")


@app.get("/officials")
def officials_list():
    return _matches_list("official")


@app.get("/matches/new")
def match_new():
    return render_template("match_new.html", default_date=date.today().isoformat())


@app.post("/matches/new")
def match_new_post():
    played_on = (request.form.get("played_on") or "").strip()
    match_kind = (request.form.get("match_kind") or "scrim").strip().lower()
    official_type = (request.form.get("official_type") or "").strip().lower() or None
    event_name = (request.form.get("event_name") or "").strip() or None
    opponent = (request.form.get("opponent") or "").strip()
    skill_level = (request.form.get("skill_level") or "").strip() or None
    patch = (request.form.get("patch") or "").strip() or None
    vod_url = (request.form.get("vod_url") or "").strip() or None
    notes = (request.form.get("notes") or "").strip() or None

    if match_kind not in {"scrim", "official"}:
        abort(400, "match_kind must be scrim or official")
    if official_type and official_type not in {"tournament", "premier"}:
        abort(400, "official_type must be tournament or premier")
    if match_kind != "official":
        official_type = None
        event_name = None

    if not played_on or not opponent:
        abort(400, "played_on and opponent are required")

    with db() as conn:
        cur = conn.execute(
            """
            INSERT INTO scrims (played_on, match_kind, official_type, event_name, opponent, skill_level, patch, vod_url, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (played_on, match_kind, official_type, event_name, opponent, skill_level, patch, vod_url, notes),
        )
        scrim_id = cur.lastrowid
    match_kind = "official" if match_kind == "official" else "scrim"
    if match_kind == "official":
        return redirect(url_for("official_detail", scrim_id=scrim_id))
    return redirect(url_for("scrim_detail", scrim_id=scrim_id))


def _get_scrim_or_404(conn, scrim_id: int):
    scrim = conn.execute("SELECT * FROM scrims WHERE id = ?", (scrim_id,)).fetchone()
    if not scrim:
        abort(404)
    return scrim


def _get_map_or_404(conn, scrim_map_id: int):
    m = conn.execute("SELECT * FROM scrim_maps WHERE id = ?", (scrim_map_id,)).fetchone()
    if not m:
        abort(404)
    return m


def _get_stat_or_404(conn, stat_id: int):
    st = conn.execute(
        "SELECT * FROM player_map_stats WHERE id = ?", (stat_id,)
    ).fetchone()
    if not st:
        abort(404)
    return st


def _render_match_detail(scrim, scrim_id: int, conn):
    maps_ = conn.execute(
        "SELECT * FROM scrim_maps WHERE scrim_id = ? ORDER BY id ASC",
        (scrim_id,),
    ).fetchall()
    stats_by_map = {}
    for m in maps_:
        stats_by_map[m["id"]] = conn.execute(
            """
            SELECT * FROM player_map_stats
            WHERE scrim_map_id = ?
            ORDER BY player_name COLLATE NOCASE ASC, id ASC
            """,
            (m["id"],),
        ).fetchall()
    return render_template(
        "scrim_detail.html", scrim=scrim, maps=maps_, stats_by_map=stats_by_map
    )


@app.get("/scrims/<int:scrim_id>")
def scrim_detail(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] == "official":
            return redirect(url_for("official_detail", scrim_id=scrim_id))
        return _render_match_detail(scrim, scrim_id, conn)


@app.get("/officials/<int:scrim_id>")
def official_detail(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_detail", scrim_id=scrim_id))
        return _render_match_detail(scrim, scrim_id, conn)


def _match_detail_url(scrim: dict) -> str:
    """Return the correct detail URL for a match (scrims or officials)."""
    if scrim["match_kind"] == "official":
        return url_for("official_detail", scrim_id=scrim["id"])
    return url_for("scrim_detail", scrim_id=scrim["id"])


def _map_new_url(scrim: dict) -> str:
    if scrim["match_kind"] == "official":
        return url_for("official_map_new", scrim_id=scrim["id"])
    return url_for("scrim_map_new", scrim_id=scrim["id"])


def _map_edit_url(scrim: dict, scrim_map_id: int) -> str:
    if scrim["match_kind"] == "official":
        return url_for("official_map_edit", scrim_map_id=scrim_map_id)
    return url_for("scrim_map_edit", scrim_map_id=scrim_map_id)


def _player_stat_new_url(scrim: dict, scrim_map_id: int) -> str:
    if scrim["match_kind"] == "official":
        return url_for("official_player_stat_new", scrim_map_id=scrim_map_id)
    return url_for("scrim_player_stat_new", scrim_map_id=scrim_map_id)


def _player_stat_edit_url(scrim: dict, stat_id: int) -> str:
    if scrim["match_kind"] == "official":
        return url_for("official_player_stat_edit", stat_id=stat_id)
    return url_for("scrim_player_stat_edit", stat_id=stat_id)


@app.post("/scrims/<int:scrim_id>/delete")
def scrim_delete(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        match_kind = scrim["match_kind"]
        conn.execute("DELETE FROM scrims WHERE id = ?", (scrim_id,))

    return redirect(url_for("officials_list" if match_kind == "official" else "scrims_list"))


@app.get("/scrims/<int:scrim_id>/edit-notes")
def scrim_edit_notes(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
    return render_template("scrim_edit_notes.html", scrim=scrim)


@app.post("/scrims/<int:scrim_id>/edit-notes")
def scrim_edit_notes_post(scrim_id: int):
    played_on = (request.form.get("played_on") or "").strip()
    opponent = (request.form.get("opponent") or "").strip()
    notes = (request.form.get("notes") or "").strip() or None
    skill_level = (request.form.get("skill_level") or "").strip() or None
    event_name = (request.form.get("event_name") or "").strip() or None
    official_type = (request.form.get("official_type") or "").strip().lower() or None
    if official_type and official_type not in {"tournament", "premier"}:
        official_type = None

    if not played_on or not opponent:
        abort(400, "Date and opponent are required")

    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] != "official":
            event_name = None
            official_type = None
        conn.execute(
            """
            UPDATE scrims SET played_on = ?, opponent = ?, notes = ?, skill_level = ?,
              event_name = ?, official_type = ?
            WHERE id = ?
            """,
            (played_on, opponent, notes, skill_level, event_name, official_type, scrim_id),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/scrims/<int:scrim_id>/maps/new")
def scrim_map_new(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] == "official":
            return redirect(url_for("official_map_new", scrim_id=scrim_id))
        maps = _available_maps(conn)
    return render_template("map_new.html", scrim=scrim, maps=maps)


@app.post("/scrims/<int:scrim_id>/maps/new")
def scrim_map_new_post(scrim_id: int):
    map_name = (request.form.get("map_name") or "").strip()
    our_score = _int_or_none(request.form.get("our_score"))
    opp_score = _int_or_none(request.form.get("opp_score"))
    our_attack_rounds = _int_or_none(request.form.get("our_attack_rounds"))
    our_def_rounds = _int_or_none(request.form.get("our_def_rounds"))
    opp_attack_rounds = _int_or_none(request.form.get("opp_attack_rounds"))
    opp_def_rounds = _int_or_none(request.form.get("opp_def_rounds"))
    pistol_atk_won = _int_or_none(request.form.get("pistol_atk_won"))
    pistol_def_won = _int_or_none(request.form.get("pistol_def_won"))
    notes = (request.form.get("notes") or "").strip() or None

    if not map_name or our_score is None or opp_score is None:
        abort(400, "map_name, our_score, opp_score are required")

    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        conn.execute(
            """
            INSERT INTO scrim_maps (
              scrim_id, map_name, our_score, opp_score,
              our_attack_rounds, our_def_rounds, opp_attack_rounds, opp_def_rounds,
              our_pistol_atk_won, our_pistol_def_won,
              notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scrim_id,
                map_name,
                our_score,
                opp_score,
                our_attack_rounds,
                our_def_rounds,
                opp_attack_rounds,
                opp_def_rounds,
                pistol_atk_won,
                pistol_def_won,
                notes,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/officials/<int:scrim_id>/maps/new")
def official_map_new(scrim_id: int):
    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_map_new", scrim_id=scrim_id))
        maps = _available_maps(conn)
    return render_template("map_new.html", scrim=scrim, maps=maps)


@app.post("/officials/<int:scrim_id>/maps/new")
def official_map_new_post(scrim_id: int):
    map_name = (request.form.get("map_name") or "").strip()
    our_score = _int_or_none(request.form.get("our_score"))
    opp_score = _int_or_none(request.form.get("opp_score"))
    our_attack_rounds = _int_or_none(request.form.get("our_attack_rounds"))
    our_def_rounds = _int_or_none(request.form.get("our_def_rounds"))
    opp_attack_rounds = _int_or_none(request.form.get("opp_attack_rounds"))
    opp_def_rounds = _int_or_none(request.form.get("opp_def_rounds"))
    pistol_atk_won = _int_or_none(request.form.get("pistol_atk_won"))
    pistol_def_won = _int_or_none(request.form.get("pistol_def_won"))
    notes = (request.form.get("notes") or "").strip() or None

    if not map_name or our_score is None or opp_score is None:
        abort(400, "map_name, our_score, opp_score are required")

    with db() as conn:
        scrim = _get_scrim_or_404(conn, scrim_id)
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_map_new", scrim_id=scrim_id))
        conn.execute(
            """
            INSERT INTO scrim_maps (
              scrim_id, map_name, our_score, opp_score,
              our_attack_rounds, our_def_rounds, opp_attack_rounds, opp_def_rounds,
              our_pistol_atk_won, our_pistol_def_won,
              notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scrim_id,
                map_name,
                our_score,
                opp_score,
                our_attack_rounds,
                our_def_rounds,
                opp_attack_rounds,
                opp_def_rounds,
                pistol_atk_won,
                pistol_def_won,
                notes,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/scrims/maps/<int:scrim_map_id>/edit")
def scrim_map_edit(scrim_map_id: int):
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] == "official":
            return redirect(url_for("official_map_edit", scrim_map_id=scrim_map_id))
        maps = _available_maps(conn)
    return render_template("map_edit.html", scrim=scrim, m=m, maps=maps)


@app.post("/scrims/maps/<int:scrim_map_id>/edit")
def scrim_map_edit_post(scrim_map_id: int):
    map_name = (request.form.get("map_name") or "").strip()
    our_score = _int_or_none(request.form.get("our_score"))
    opp_score = _int_or_none(request.form.get("opp_score"))
    our_attack_rounds = _int_or_none(request.form.get("our_attack_rounds"))
    our_def_rounds = _int_or_none(request.form.get("our_def_rounds"))
    opp_attack_rounds = _int_or_none(request.form.get("opp_attack_rounds"))
    opp_def_rounds = _int_or_none(request.form.get("opp_def_rounds"))
    pistol_atk_won = _int_or_none(request.form.get("pistol_atk_won"))
    pistol_def_won = _int_or_none(request.form.get("pistol_def_won"))
    notes = (request.form.get("notes") or "").strip() or None

    if not map_name or our_score is None or opp_score is None:
        abort(400, "map_name, our_score, opp_score are required")

    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            UPDATE scrim_maps
            SET map_name = ?,
                our_score = ?,
                opp_score = ?,
                our_attack_rounds = ?,
                our_def_rounds = ?,
                opp_attack_rounds = ?,
                opp_def_rounds = ?,
                our_pistol_atk_won = ?,
                our_pistol_def_won = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                map_name,
                our_score,
                opp_score,
                our_attack_rounds,
                our_def_rounds,
                opp_attack_rounds,
                opp_def_rounds,
                pistol_atk_won,
                pistol_def_won,
                notes,
                scrim_map_id,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/officials/maps/<int:scrim_map_id>/edit")
def official_map_edit(scrim_map_id: int):
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_map_edit", scrim_map_id=scrim_map_id))
        maps = _available_maps(conn)
    return render_template("map_edit.html", scrim=scrim, m=m, maps=maps)


@app.post("/officials/maps/<int:scrim_map_id>/edit")
def official_map_edit_post(scrim_map_id: int):
    map_name = (request.form.get("map_name") or "").strip()
    our_score = _int_or_none(request.form.get("our_score"))
    opp_score = _int_or_none(request.form.get("opp_score"))
    our_attack_rounds = _int_or_none(request.form.get("our_attack_rounds"))
    our_def_rounds = _int_or_none(request.form.get("our_def_rounds"))
    opp_attack_rounds = _int_or_none(request.form.get("opp_attack_rounds"))
    opp_def_rounds = _int_or_none(request.form.get("opp_def_rounds"))
    pistol_atk_won = _int_or_none(request.form.get("pistol_atk_won"))
    pistol_def_won = _int_or_none(request.form.get("pistol_def_won"))
    notes = (request.form.get("notes") or "").strip() or None

    if not map_name or our_score is None or opp_score is None:
        abort(400, "map_name, our_score, opp_score are required")

    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            UPDATE scrim_maps
            SET map_name = ?,
                our_score = ?,
                opp_score = ?,
                our_attack_rounds = ?,
                our_def_rounds = ?,
                opp_attack_rounds = ?,
                opp_def_rounds = ?,
                our_pistol_atk_won = ?,
                our_pistol_def_won = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                map_name,
                our_score,
                opp_score,
                our_attack_rounds,
                our_def_rounds,
                opp_attack_rounds,
                opp_def_rounds,
                pistol_atk_won,
                pistol_def_won,
                notes,
                scrim_map_id,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/scrims/maps/<int:scrim_map_id>/stats/new")
def scrim_player_stat_new(scrim_map_id: int):
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] == "official":
            return redirect(url_for("official_player_stat_new", scrim_map_id=scrim_map_id))
        roster = _roster_players(conn)
        available_agents = _available_agents(conn)
    return render_template("player_stat_new.html", scrim=scrim, m=m, roster=roster, available_agents=available_agents)


@app.post("/scrims/maps/<int:scrim_map_id>/stats/new")
def scrim_player_stat_new_post(scrim_map_id: int):
    player_name = (request.form.get("player_name") or "").strip()
    agent = (request.form.get("agent") or "").strip() or None
    kills = _int_or_none(request.form.get("kills"))
    deaths = _int_or_none(request.form.get("deaths"))
    assists = _int_or_none(request.form.get("assists"))
    acs = _int_or_none(request.form.get("acs"))
    kast_pct = _float_or_none(request.form.get("kast_pct"))
    first_kills = _int_or_none(request.form.get("first_kills"))
    first_deaths = _int_or_none(request.form.get("first_deaths"))
    notes = (request.form.get("notes") or "").strip() or None

    if not player_name:
        abort(400, "player_name is required")

    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            INSERT INTO player_map_stats (
              scrim_map_id, player_name, agent,
              kills, deaths, assists, acs, kast_pct, first_kills, first_deaths,
              notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scrim_map_id,
                player_name,
                agent,
                kills,
                deaths,
                assists,
                acs,
                kast_pct,
                first_kills,
                first_deaths,
                notes,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/officials/maps/<int:scrim_map_id>/stats/new")
def official_player_stat_new(scrim_map_id: int):
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_player_stat_new", scrim_map_id=scrim_map_id))
        roster = _roster_players(conn)
        available_agents = _available_agents(conn)
    return render_template("player_stat_new.html", scrim=scrim, m=m, roster=roster, available_agents=available_agents)


@app.post("/officials/maps/<int:scrim_map_id>/stats/new")
def official_player_stat_new_post(scrim_map_id: int):
    player_name = (request.form.get("player_name") or "").strip()
    agent = (request.form.get("agent") or "").strip() or None
    kills = _int_or_none(request.form.get("kills"))
    deaths = _int_or_none(request.form.get("deaths"))
    assists = _int_or_none(request.form.get("assists"))
    acs = _int_or_none(request.form.get("acs"))
    kast_pct = _float_or_none(request.form.get("kast_pct"))
    first_kills = _int_or_none(request.form.get("first_kills"))
    first_deaths = _int_or_none(request.form.get("first_deaths"))
    notes = (request.form.get("notes") or "").strip() or None

    if not player_name:
        abort(400, "player_name is required")

    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            INSERT INTO player_map_stats (
              scrim_map_id, player_name, agent,
              kills, deaths, assists, acs, kast_pct, first_kills, first_deaths,
              notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scrim_map_id,
                player_name,
                agent,
                kills,
                deaths,
                assists,
                acs,
                kast_pct,
                first_kills,
                first_deaths,
                notes,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/scrims/stats/<int:stat_id>/edit")
def scrim_player_stat_edit(stat_id: int):
    with db() as conn:
        st = _get_stat_or_404(conn, stat_id)
        m = _get_map_or_404(conn, st["scrim_map_id"])
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] == "official":
            return redirect(url_for("official_player_stat_edit", stat_id=stat_id))
        roster = _roster_players(conn)
        available_agents = _available_agents(conn)
    return render_template("player_stat_edit.html", scrim=scrim, m=m, st=st, roster=roster, available_agents=available_agents)


@app.post("/scrims/stats/<int:stat_id>/edit")
def scrim_player_stat_edit_post(stat_id: int):
    player_name = (request.form.get("player_name") or "").strip()
    agent = (request.form.get("agent") or "").strip() or None
    kills = _int_or_none(request.form.get("kills"))
    deaths = _int_or_none(request.form.get("deaths"))
    assists = _int_or_none(request.form.get("assists"))
    acs = _int_or_none(request.form.get("acs"))
    kast_pct = _float_or_none(request.form.get("kast_pct"))
    first_kills = _int_or_none(request.form.get("first_kills"))
    first_deaths = _int_or_none(request.form.get("first_deaths"))
    notes = (request.form.get("notes") or "").strip() or None

    if not player_name:
        abort(400, "player_name is required")

    with db() as conn:
        st = _get_stat_or_404(conn, stat_id)
        m = _get_map_or_404(conn, st["scrim_map_id"])
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            UPDATE player_map_stats
            SET player_name = ?,
                agent = ?,
                kills = ?,
                deaths = ?,
                assists = ?,
                acs = ?,
                kast_pct = ?,
                first_kills = ?,
                first_deaths = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                player_name,
                agent,
                kills,
                deaths,
                assists,
                acs,
                kast_pct,
                first_kills,
                first_deaths,
                notes,
                stat_id,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/officials/stats/<int:stat_id>/edit")
def official_player_stat_edit(stat_id: int):
    with db() as conn:
        st = _get_stat_or_404(conn, stat_id)
        m = _get_map_or_404(conn, st["scrim_map_id"])
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        if scrim["match_kind"] != "official":
            return redirect(url_for("scrim_player_stat_edit", stat_id=stat_id))
        roster = _roster_players(conn)
        available_agents = _available_agents(conn)
    return render_template("player_stat_edit.html", scrim=scrim, m=m, st=st, roster=roster, available_agents=available_agents)


@app.post("/officials/stats/<int:stat_id>/edit")
def official_player_stat_edit_post(stat_id: int):
    player_name = (request.form.get("player_name") or "").strip()
    agent = (request.form.get("agent") or "").strip() or None
    kills = _int_or_none(request.form.get("kills"))
    deaths = _int_or_none(request.form.get("deaths"))
    assists = _int_or_none(request.form.get("assists"))
    acs = _int_or_none(request.form.get("acs"))
    kast_pct = _float_or_none(request.form.get("kast_pct"))
    first_kills = _int_or_none(request.form.get("first_kills"))
    first_deaths = _int_or_none(request.form.get("first_deaths"))
    notes = (request.form.get("notes") or "").strip() or None

    if not player_name:
        abort(400, "player_name is required")

    with db() as conn:
        st = _get_stat_or_404(conn, stat_id)
        m = _get_map_or_404(conn, st["scrim_map_id"])
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
        conn.execute(
            """
            UPDATE player_map_stats
            SET player_name = ?,
                agent = ?,
                kills = ?,
                deaths = ?,
                assists = ?,
                acs = ?,
                kast_pct = ?,
                first_kills = ?,
                first_deaths = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                player_name,
                agent,
                kills,
                deaths,
                assists,
                acs,
                kast_pct,
                first_kills,
                first_deaths,
                notes,
                stat_id,
            ),
        )
    return redirect(_match_detail_url(scrim))


@app.get("/maps/<int:scrim_map_id>/stats/new")
@app.post("/maps/<int:scrim_map_id>/stats/new")
def _redirect_player_stat_new(scrim_map_id: int):
    """Redirect old /maps/<id>/stats/new to scrims or officials path."""
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
    if scrim["match_kind"] == "official":
        return redirect(url_for("official_player_stat_new", scrim_map_id=scrim_map_id), code=307)
    return redirect(url_for("scrim_player_stat_new", scrim_map_id=scrim_map_id), code=307)


@app.get("/maps/<int:scrim_map_id>/edit")
@app.post("/maps/<int:scrim_map_id>/edit")
def _redirect_map_edit(scrim_map_id: int):
    """Redirect old /maps/<id>/edit to scrims or officials path."""
    with db() as conn:
        m = _get_map_or_404(conn, scrim_map_id)
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
    if scrim["match_kind"] == "official":
        return redirect(url_for("official_map_edit", scrim_map_id=scrim_map_id), code=307)
    return redirect(url_for("scrim_map_edit", scrim_map_id=scrim_map_id), code=307)


@app.get("/stats/<int:stat_id>/edit")
@app.post("/stats/<int:stat_id>/edit")
def _redirect_player_stat_edit(stat_id: int):
    """Redirect old /stats/<id>/edit to scrims or officials path."""
    with db() as conn:
        st = _get_stat_or_404(conn, stat_id)
        m = _get_map_or_404(conn, st["scrim_map_id"])
        scrim = _get_scrim_or_404(conn, m["scrim_id"])
    if scrim["match_kind"] == "official":
        return redirect(url_for("official_player_stat_edit", stat_id=stat_id), code=307)
    return redirect(url_for("scrim_player_stat_edit", stat_id=stat_id), code=307)


# Skill level filter groups for analytics
SKILL_LEVEL_FILTERS = {
    "high": ["tier 1", "tier 2"],
    "mid": ["invite"],
    "low": ["contender"],
    "gc": ["gc"],
}


def _skill_level_clause(skill: str) -> tuple[str, tuple]:
    """Return (sql_condition, params) for skill level filter. Empty for 'all'."""
    skill = (skill or "").strip().lower()
    if not skill or skill == "all":
        return ("", ())
    if skill not in SKILL_LEVEL_FILTERS:
        return ("", ())
    levels = SKILL_LEVEL_FILTERS[skill]
    placeholders = ", ".join("?" for _ in levels)
    return (
        f" AND (LOWER(TRIM(s.skill_level)) IN ({placeholders}))",
        tuple(levels),
    )


@app.get("/analytics")
def analytics():
    return redirect(url_for("analytics_players"))


@app.get("/analytics/players")
def analytics_players():
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    skill = (request.args.get("skill") or "all").strip().lower()
    skill_clause, skill_params = _skill_level_clause(skill)

    with db() as conn:
        maps = conn.execute(
            """
            SELECT DISTINCT map_name
            FROM scrim_maps
            JOIN scrims s ON s.id = scrim_maps.scrim_id
            WHERE s.match_kind = ?
            """ + skill_clause + """
            ORDER BY map_name COLLATE NOCASE ASC
            """,
            (kind,) + skill_params,
        ).fetchall()

        selected_map = (request.args.get("map") or "").strip() or None
        if not selected_map and maps:
            selected_map = maps[0]["map_name"]

        if selected_map:
            per_map = conn.execute(
                """
                SELECT
                  sm.map_name AS map_name,
                  p.player_name AS player_name,
                  COUNT(*) AS rows_count,
                  AVG(p.kills) AS avg_kills,
                  AVG(p.deaths) AS avg_deaths,
                  AVG(p.assists) AS avg_assists,
                  AVG(p.acs) AS avg_acs,
                  AVG(p.kast_pct) AS avg_kast_pct,
                  AVG(p.first_kills) AS avg_fk,
                  AVG(p.first_deaths) AS avg_fd
                FROM player_map_stats p
                JOIN scrim_maps sm ON sm.id = p.scrim_map_id
                JOIN scrims s ON s.id = sm.scrim_id
                WHERE sm.map_name = ?
                  AND s.match_kind = ?
                """ + skill_clause + """
                GROUP BY sm.map_name, p.player_name
                ORDER BY p.player_name COLLATE NOCASE ASC
                """,
                (selected_map, kind) + skill_params,
            ).fetchall()
        else:
            per_map = []

        overall = conn.execute(
            """
            SELECT
              p.player_name AS player_name,
              COUNT(*) AS rows_count,
              AVG(p.kills) AS avg_kills,
              AVG(p.deaths) AS avg_deaths,
              AVG(p.assists) AS avg_assists,
              AVG(p.acs) AS avg_acs,
              AVG(p.kast_pct) AS avg_kast_pct,
              AVG(p.first_kills) AS avg_fk,
              AVG(p.first_deaths) AS avg_fd
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE s.match_kind = ?
            """ + skill_clause + """
            GROUP BY p.player_name
            ORDER BY p.player_name COLLATE NOCASE ASC
            """,
            (kind,) + skill_params,
        ).fetchall()

    return render_template(
        "analytics_players.html",
        per_map=per_map,
        overall=overall,
        maps=maps,
        selected_map=selected_map,
        kind=kind,
        skill=skill if skill in SKILL_LEVEL_FILTERS else "all",
    )


@app.get("/analytics/players/map-stats")
def analytics_players_map_stats():
    """Return per-map player stats as JSON for dynamic map switching."""
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    skill = (request.args.get("skill") or "all").strip().lower()
    skill_clause, skill_params = _skill_level_clause(skill)
    map_name = (request.args.get("map") or "").strip() or None
    if not map_name:
        return jsonify({"rows": []})
    with db() as conn:
        rows = conn.execute(
            """
            SELECT
              sm.map_name AS map_name,
              p.player_name AS player_name,
              COUNT(*) AS rows_count,
              AVG(p.kills) AS avg_kills,
              AVG(p.deaths) AS avg_deaths,
              AVG(p.assists) AS avg_assists,
              AVG(p.acs) AS avg_acs,
              AVG(p.kast_pct) AS avg_kast_pct,
              AVG(p.first_kills) AS avg_fk,
              AVG(p.first_deaths) AS avg_fd
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE sm.map_name = ?
              AND s.match_kind = ?
            """ + skill_clause + """
            GROUP BY sm.map_name, p.player_name
            ORDER BY p.player_name COLLATE NOCASE ASC
            """,
            (map_name, kind) + skill_params,
        ).fetchall()
    return jsonify({
        "rows": [
            {
                "player_name": r["player_name"],
                "rows_count": r["rows_count"],
                "avg_kills": float(r["avg_kills"]) if r["avg_kills"] is not None else None,
                "avg_deaths": float(r["avg_deaths"]) if r["avg_deaths"] is not None else None,
                "avg_assists": float(r["avg_assists"]) if r["avg_assists"] is not None else None,
                "avg_acs": float(r["avg_acs"]) if r["avg_acs"] is not None else None,
                "avg_kast_pct": float(r["avg_kast_pct"]) if r["avg_kast_pct"] is not None else None,
                "avg_fk": float(r["avg_fk"]) if r["avg_fk"] is not None else None,
                "avg_fd": float(r["avg_fd"]) if r["avg_fd"] is not None else None,
            }
            for r in rows
        ],
    })


@app.get("/analytics/players/<path:player_name>")
def analytics_player_recent(player_name: str):
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    player_name = player_name.strip()
    if not player_name:
        abort(404)

    # Kept for backwards-compat; player profiles live at /players/<name>.
    return redirect(url_for("player_profile", player_name=player_name, kind=kind))


@app.get("/players/<path:player_name>")
def player_profile(player_name: str):
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    player_name = player_name.strip()
    if not player_name:
        abort(404)

    with db() as conn:
        overall = conn.execute(
            """
            SELECT
              COUNT(*) AS games,
              AVG(p.kills) AS avg_kills,
              AVG(p.deaths) AS avg_deaths,
              AVG(p.assists) AS avg_assists,
              AVG(p.acs) AS avg_acs,
              AVG(p.kast_pct) AS avg_kast_pct,
              AVG(p.first_kills) AS avg_fk,
              AVG(p.first_deaths) AS avg_fd
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE p.player_name = ?
              AND s.match_kind = ?
            """,
            (player_name, kind),
        ).fetchone()

        agent_stats = conn.execute(
            """
            SELECT
              p.agent AS agent,
              COUNT(*) AS games,
              AVG(p.kills) AS avg_kills,
              AVG(p.deaths) AS avg_deaths,
              AVG(p.assists) AS avg_assists,
              AVG(p.acs) AS avg_acs,
              AVG(p.kast_pct) AS avg_kast_pct,
              AVG(p.first_kills) AS avg_fk,
              AVG(p.first_deaths) AS avg_fd
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE p.player_name = ?
              AND s.match_kind = ?
              AND p.agent IS NOT NULL AND TRIM(p.agent) <> ''
            GROUP BY p.agent
            ORDER BY games DESC, p.agent COLLATE NOCASE ASC
            """,
            (player_name, kind),
        ).fetchall()

        map_stats = conn.execute(
            """
            SELECT
              sm.map_name AS map_name,
              COUNT(*) AS games,
              AVG(p.kills) AS avg_kills,
              AVG(p.deaths) AS avg_deaths,
              AVG(p.assists) AS avg_assists,
              AVG(p.acs) AS avg_acs,
              AVG(p.kast_pct) AS avg_kast_pct,
              AVG(p.first_kills) AS avg_fk,
              AVG(p.first_deaths) AS avg_fd
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE p.player_name = ?
              AND s.match_kind = ?
            GROUP BY sm.map_name
            ORDER BY games DESC, sm.map_name COLLATE NOCASE ASC
            """,
            (player_name, kind),
        ).fetchall()

        recent = conn.execute(
            """
            SELECT
              s.played_on AS played_on,
              s.opponent AS opponent,
              sm.map_name AS map_name,
              p.agent AS agent,
              p.kills AS kills,
              p.deaths AS deaths,
              p.assists AS assists,
              p.acs AS acs,
              p.kast_pct AS kast_pct,
              p.first_kills AS first_kills,
              p.first_deaths AS first_deaths
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE p.player_name = ?
              AND s.match_kind = ?
            ORDER BY s.played_on DESC, sm.id DESC, p.id DESC
            LIMIT 10
            """,
            (player_name, kind),
        ).fetchall()

    def _best(rows, name_key: str, value_key: str):
        best = None
        for r in rows:
            v = r[value_key]
            if v is None:
                continue
            if best is None or v > best[value_key]:
                best = r
        return best

    def _worst(rows, name_key: str, value_key: str):
        worst = None
        for r in rows:
            v = r[value_key]
            if v is None:
                continue
            if worst is None or v < worst[value_key]:
                worst = r
        return worst

    best_agent_kills = _best(agent_stats, "agent", "avg_kills")
    best_agent_acs = _best(agent_stats, "agent", "avg_acs")
    best_map_kills = _best(map_stats, "map_name", "avg_kills")
    best_map_acs = _best(map_stats, "map_name", "avg_acs")
    worst_agent_kills = _worst(agent_stats, "agent", "avg_kills")
    worst_agent_acs = _worst(agent_stats, "agent", "avg_acs")
    worst_map_kills = _worst(map_stats, "map_name", "avg_kills")
    worst_map_acs = _worst(map_stats, "map_name", "avg_acs")

    return render_template(
        "player_profile.html",
        player_name=player_name,
        kind=kind,
        overall=overall,
        agent_stats=agent_stats,
        map_stats=map_stats,
        best_agent_kills=best_agent_kills,
        best_agent_acs=best_agent_acs,
        best_map_kills=best_map_kills,
        best_map_acs=best_map_acs,
        worst_agent_kills=worst_agent_kills,
        worst_agent_acs=worst_agent_acs,
        worst_map_kills=worst_map_kills,
        worst_map_acs=worst_map_acs,
        recent=recent,
    )


@app.get("/analytics/maps")
def analytics_maps():
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    skill = (request.args.get("skill") or "all").strip().lower()
    skill_clause, skill_params = _skill_level_clause(skill)

    with db() as conn:
        map_overall = conn.execute(
            """
            WITH rounds AS (
              SELECT
                m.map_name AS map_name,
                COUNT(*) AS map_count,
                SUM(CASE WHEN m.our_score > m.opp_score THEN 1 ELSE 0 END) AS maps_won,
                SUM(CASE WHEN m.our_score < m.opp_score THEN 1 ELSE 0 END) AS maps_lost,
                SUM(CASE WHEN m.our_score = m.opp_score THEN 1 ELSE 0 END) AS maps_drawn,
                SUM(m.our_score) AS rounds_won,
                SUM(m.opp_score) AS rounds_lost,
                SUM(COALESCE(m.our_attack_rounds, 0)) AS atk_rounds_won,
                SUM(COALESCE(m.our_def_rounds, 0)) AS def_rounds_won,
                SUM(COALESCE(m.opp_attack_rounds, 0)) AS opp_atk_won,
                SUM(COALESCE(m.opp_def_rounds, 0)) AS opp_def_won,
                SUM(CASE WHEN m.our_pistol_atk_won IS NOT NULL THEN 1 ELSE 0 END) AS pistol_atk_count,
                SUM(CASE WHEN m.our_pistol_def_won IS NOT NULL THEN 1 ELSE 0 END) AS pistol_def_count,
                SUM(COALESCE(m.our_pistol_atk_won, 0)) AS pistol_atk_wins,
                SUM(COALESCE(m.our_pistol_def_won, 0)) AS pistol_def_wins
              FROM scrim_maps m
              JOIN scrims s ON s.id = m.scrim_id
              WHERE s.match_kind = ?
              """ + skill_clause + """
              GROUP BY map_name
            ),
            stats AS (
              SELECT
                sm.map_name AS map_name,
                SUM(COALESCE(p.first_kills, 0)) AS sum_fk
              FROM player_map_stats p
              JOIN scrim_maps sm ON sm.id = p.scrim_map_id
              JOIN scrims s ON s.id = sm.scrim_id
              WHERE s.match_kind = ?
              """ + skill_clause + """
              GROUP BY sm.map_name
            )
            SELECT
              COALESCE(r.map_name, s.map_name) AS map_name,
              COALESCE(r.map_count, 0) AS map_count,
              COALESCE(r.maps_won, 0) AS maps_won,
              COALESCE(r.maps_lost, 0) AS maps_lost,
              COALESCE(r.maps_drawn, 0) AS maps_drawn,
              COALESCE(r.rounds_won, 0) AS rounds_won,
              COALESCE(r.rounds_lost, 0) AS rounds_lost,
              CASE
                WHEN COALESCE(r.map_count, 0) = 0 THEN NULL
                ELSE (1.0 * COALESCE(r.maps_won, 0)) / r.map_count
              END AS map_winrate,
              CASE
                WHEN COALESCE(r.rounds_won, 0) + COALESCE(r.rounds_lost, 0) = 0 THEN NULL
                ELSE (1.0 * r.rounds_won) / (r.rounds_won + r.rounds_lost)
              END AS round_winrate,
              CASE
                WHEN COALESCE(r.map_count, 0) = 0 OR s.sum_fk IS NULL THEN NULL
                ELSE (1.0 * s.sum_fk) / r.map_count
              END AS avg_fk_per_map,
              CASE
                WHEN COALESCE(r.atk_rounds_won, 0) + COALESCE(r.opp_def_won, 0) = 0 THEN NULL
                ELSE (1.0 * r.atk_rounds_won) / (r.atk_rounds_won + r.opp_def_won)
              END AS atk_winrate,
              CASE
                WHEN COALESCE(r.def_rounds_won, 0) + COALESCE(r.opp_atk_won, 0) = 0 THEN NULL
                ELSE (1.0 * r.def_rounds_won) / (r.def_rounds_won + r.opp_atk_won)
              END AS def_winrate,
              CASE
                WHEN COALESCE(r.pistol_atk_count, 0) = 0 THEN NULL
                ELSE (1.0 * r.pistol_atk_wins) / r.pistol_atk_count
              END AS pistol_atk_winrate,
              CASE
                WHEN COALESCE(r.pistol_def_count, 0) = 0 THEN NULL
                ELSE (1.0 * r.pistol_def_wins) / r.pistol_def_count
              END AS pistol_def_winrate
            FROM rounds r
            LEFT JOIN stats s ON s.map_name = r.map_name
            UNION ALL
            SELECT
              s.map_name AS map_name,
              0 AS map_count,
              0 AS maps_won,
              0 AS maps_lost,
              0 AS maps_drawn,
              0 AS rounds_won,
              0 AS rounds_lost,
              NULL AS map_winrate,
              NULL AS round_winrate,
              NULL AS avg_fk_per_map,
              NULL AS atk_winrate,
              NULL AS def_winrate,
              NULL AS pistol_atk_winrate,
              NULL AS pistol_def_winrate
            FROM stats s
            WHERE s.map_name NOT IN (SELECT map_name FROM rounds)
            ORDER BY map_name COLLATE NOCASE ASC
            """
            ,
            (kind,) + skill_params + (kind,) + skill_params,
        ).fetchall()

    chart_data = [
        {
            "map_name": r["map_name"],
            "map_icon_url": map_icon_url(r["map_name"]),
            "map_count": r["map_count"],
            "maps_won": r["maps_won"],
            "maps_lost": r["maps_lost"],
            "maps_drawn": r["maps_drawn"],
            "rounds_won": r["rounds_won"],
            "rounds_lost": r["rounds_lost"],
            "map_winrate": r["map_winrate"],
            "round_winrate": r["round_winrate"],
            "atk_winrate": r["atk_winrate"],
            "def_winrate": r["def_winrate"],
            "pistol_atk_winrate": r["pistol_atk_winrate"],
            "pistol_def_winrate": r["pistol_def_winrate"],
        }
        for r in map_overall
    ]
    return render_template(
        "analytics_maps.html",
        map_overall=map_overall,
        chart_data=chart_data,
        kind=kind,
        skill=skill if skill in SKILL_LEVEL_FILTERS else "all",
    )


@app.get("/agent-pool")
def agent_pool():
    kind = (request.args.get("kind") or "scrim").strip().lower()
    if kind not in {"scrim", "official"}:
        kind = "scrim"
    min_games = request.args.get("min_games", "1").strip()
    try:
        min_games = max(1, int(min_games))
    except ValueError:
        min_games = 1
    with db() as conn:
        rows = conn.execute(
            """
            SELECT
              player_name,
              agent,
              COUNT(*) AS picks
            FROM player_map_stats
            JOIN scrim_maps sm ON sm.id = player_map_stats.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE agent IS NOT NULL AND TRIM(agent) <> ''
              AND s.match_kind = ?
            GROUP BY player_name, agent
            ORDER BY player_name COLLATE NOCASE ASC, picks DESC, agent COLLATE NOCASE ASC
            """
            ,
            (kind,),
        ).fetchall()

        agent_avgs = conn.execute(
            """
            SELECT
              p.player_name AS player_name,
              p.agent AS agent,
              COUNT(*) AS games,
              AVG(p.kills) AS avg_kills,
              AVG(p.acs) AS avg_acs
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE p.agent IS NOT NULL AND TRIM(p.agent) <> ''
              AND s.match_kind = ?
            GROUP BY p.player_name, p.agent
            """,
            (kind,),
        ).fetchall()

        map_avgs = conn.execute(
            """
            SELECT
              p.player_name AS player_name,
              sm.map_name AS map_name,
              COUNT(*) AS games,
              AVG(p.kills) AS avg_kills,
              AVG(p.acs) AS avg_acs
            FROM player_map_stats p
            JOIN scrim_maps sm ON sm.id = p.scrim_map_id
            JOIN scrims s ON s.id = sm.scrim_id
            WHERE s.match_kind = ?
            GROUP BY p.player_name, sm.map_name
            """,
            (kind,),
        ).fetchall()

    by_player: dict[str, list[dict]] = {}
    for r in rows:
        by_player.setdefault(r["player_name"], []).append(
            {"agent": r["agent"], "picks": r["picks"]}
        )
    for _player, agents in by_player.items():
        agents.sort(key=lambda a: _agent_sort_key(a.get("agent"), picks=a.get("picks")))

    # Build per-player summary.
    most_played: dict[str, dict] = {}
    for player, agents in by_player.items():
        if not agents:
            continue
        top = max(agents, key=lambda a: (a.get("picks") or 0, (a.get("agent") or "").casefold()))
        most_played[player] = {"agent": top.get("agent"), "picks": top.get("picks") or 0}

    best_agent_by_kills: dict[str, dict] = {}
    best_agent_by_acs: dict[str, dict] = {}
    for r in agent_avgs:
        p = r["player_name"]
        agent = r["agent"]
        games = r["games"] or 0
        if games < min_games:
            continue
        ak = r["avg_kills"]
        aa = r["avg_acs"]
        if ak is not None:
            cur = best_agent_by_kills.get(p)
            cand = (ak, games, (agent or "").casefold())
            if cur is None or cand > (cur["avg_kills"], cur["games"], cur["agent"].casefold()):
                best_agent_by_kills[p] = {
                    "agent": agent,
                    "avg_kills": float(ak),
                    "games": int(games),
                }
        if aa is not None:
            cur = best_agent_by_acs.get(p)
            cand = (aa, games, (agent or "").casefold())
            if cur is None or cand > (cur["avg_acs"], cur["games"], cur["agent"].casefold()):
                best_agent_by_acs[p] = {
                    "agent": agent,
                    "avg_acs": float(aa),
                    "games": int(games),
                }

    best_map_by_kills: dict[str, dict] = {}
    best_map_by_acs: dict[str, dict] = {}
    for r in map_avgs:
        p = r["player_name"]
        map_name = r["map_name"]
        games = r["games"] or 0
        if games < min_games:
            continue
        ak = r["avg_kills"]
        aa = r["avg_acs"]
        if ak is not None:
            cur = best_map_by_kills.get(p)
            cand = (ak, games, (map_name or "").casefold())
            if cur is None or cand > (cur["avg_kills"], cur["games"], cur["map_name"].casefold()):
                best_map_by_kills[p] = {
                    "map_name": map_name,
                    "avg_kills": float(ak),
                    "games": int(games),
                }
        if aa is not None:
            cur = best_map_by_acs.get(p)
            cand = (aa, games, (map_name or "").casefold())
            if cur is None or cand > (cur["avg_acs"], cur["games"], cur["map_name"].casefold()):
                best_map_by_acs[p] = {
                    "map_name": map_name,
                    "avg_acs": float(aa),
                    "games": int(games),
                }

    summary_by_player: dict[str, dict] = {}
    for player in by_player.keys():
        summary_by_player[player] = {
            "most_played": most_played.get(player),
            "best_agent_kills": best_agent_by_kills.get(player),
            "best_agent_acs": best_agent_by_acs.get(player),
            "best_map_kills": best_map_by_kills.get(player),
            "best_map_acs": best_map_by_acs.get(player),
        }

    # Keep Meixior at end (marked as sub in UI).
    def _player_sort_key(name: str):
        if name.strip().casefold() == "meixior":
            return (1, name.casefold())
        return (0, name.casefold())

    by_player_sorted = dict(sorted(by_player.items(), key=lambda kv: _player_sort_key(kv[0])))

    return render_template(
        "agent_pool.html",
        by_player=by_player_sorted,
        summary_by_player=summary_by_player,
        kind=kind,
        min_games=min_games,
    )


DEFAULT_ROSTER = ["Sefa", "Zaspalem", "Bye", "Milan", "Repu", "Meixior"]


def _roster_players(conn) -> list[str]:
    roster = _get_list_setting(conn, "roster_players")
    if not roster:
        roster = DEFAULT_ROSTER.copy()
        _set_list_setting(conn, "roster_players", roster)
    return sorted(set(roster), key=lambda x: x.casefold())


def _available_maps(conn) -> list[str]:
    custom = _get_list_setting(conn, "custom_maps")
    return sorted(set(COMPETITIVE_MAPS) | set(custom), key=lambda x: x.casefold())


def _available_agents(conn) -> list[str]:
    builtin = list(AGENT_ROLES.keys())
    custom = _get_list_setting(conn, "custom_agents")
    seen = {a.casefold() for a in builtin}
    extra = [a for a in custom if a.strip() and a.strip().casefold() not in seen]
    return sorted(builtin + extra, key=lambda x: x.casefold())


@app.get("/settings")
def settings():
    with db() as conn:
        roster = _get_list_setting(conn, "roster_players")
        if not roster:
            roster = DEFAULT_ROSTER.copy()
            _set_list_setting(conn, "roster_players", roster)
        custom_maps = _get_list_setting(conn, "custom_maps")
        custom_agents = _get_list_setting(conn, "custom_agents")
    return render_template(
        "settings.html",
        roster=roster,
        custom_maps=custom_maps,
        custom_agents=custom_agents,
    )


@app.post("/settings")
def settings_post():
    def parse_list(text: str) -> list[str]:
        return [x.strip() for x in (text or "").strip().splitlines() if x.strip()]

    roster = parse_list(request.form.get("roster_players", ""))
    custom_maps = parse_list(request.form.get("custom_maps", ""))
    custom_agents = parse_list(request.form.get("custom_agents", ""))

    with db() as conn:
        _set_list_setting(conn, "roster_players", roster)
        _set_list_setting(conn, "custom_maps", custom_maps)
        _set_list_setting(conn, "custom_agents", custom_agents)

    return redirect(url_for("settings"))


if __name__ == "__main__":
    init_db()
    # debug=False in production: debug=True exposes full tracebacks (source code) on errors
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("FLASK_DEBUG", "").lower() == "true")

