"""Statbotics v3 EPA lookups (no auth).

Endpoint shape confirmed against the live API:
  GET https://api.statbotics.io/v3/team_year/{team}/{year}
  { "epa": {"total_points": 51.71, "unitless": 1949.0, "norm": 1876.0,
            "ranks": {"state": {"percentile": 0.9894}, ...}, ... },
    "record": {"wins":45,"losses":5,"ties":1,"count":51,"winrate":0.8922} }

We store the whole epa/record objects verbatim (insulates against key drift) and
also extract named convenience fields matching knowledge/survey/sd-frc-master.csv.
"""

from __future__ import annotations

from pathlib import Path

from . import config
from .httpc import HttpError, get_json


def _dig(obj, *keys):
    for k in keys:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(k)
    return obj


def fetch_team_year(
    team: int, year: int, *, cache_dir: Path | None
) -> dict:
    """Return an EPA record for (team, year).

    status == "ok"        -> named fields + epa_raw/record_raw present
    status == "no_data"   -> team didn't compete that year (404)
    status == "error"     -> network/HTTP error (recorded, not fatal)
    """
    url = f"{config.STATBOTICS_BASE}/team_year/{team}/{year}"
    cache_path = cache_dir / f"statbotics-{team}-{year}.json" if cache_dir else None
    try:
        data = get_json(url, cache_path=cache_path, pause=0.1)
    except HttpError as e:
        if e.status == 404:
            return {"year": year, "status": "no_data"}
        return {"year": year, "status": "error", "http": e.status}
    except Exception as e:  # network exhaustion etc. — record, don't crash the run
        return {"year": year, "status": "error", "detail": str(e)[:120]}

    epa = data.get("epa") or {}
    record = data.get("record") or {}
    return {
        "year": year,
        "status": "ok",
        "norm_EPA": epa.get("norm"),
        "epa_points": epa.get("total_points"),
        "unitless_epa": epa.get("unitless"),
        "state_pctile": _dig(epa, "ranks", "state", "percentile"),
        "country_pctile": _dig(epa, "ranks", "country", "percentile"),
        "winrate": record.get("winrate"),
        "wins": record.get("wins"),
        "losses": record.get("losses"),
        "ties": record.get("ties"),
        "epa_raw": epa,
        "record_raw": record,
    }
