#!/usr/bin/env python3
"""Validate the architecture + rubric docs against the code index.

Runs a battery of queries and prints labeled results. Season-repo symbols are
identified by year IS NOT NULL (library/training repos were indexed with NULL year).
"""
import duckdb
from pathlib import Path

def root():
    for b in [Path.cwd(), *Path.cwd().parents]:
        if (b/"data"/"code-index.duckdb").exists(): return b
    raise SystemExit("db not found")
con = duckdb.connect(str(root()/"data"/"code-index.duckdb"), read_only=True)
def show(title, sql):
    print(f"\n### {title}")
    try:
        df = con.execute(sql).df()
        print(df.to_string(index=False))
    except Exception as e:
        print("ERR:", str(e).splitlines()[-1][:90])

N_SEASON_TEAMS = con.execute("SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL").fetchone()[0]
print(f"teams with a season repo indexed: {N_SEASON_TEAMS}")

# ── A. THE THREE SEAMS — prevalence ────────────────────────────────────────
show("A1 · Seam prevalence (distinct teams, any season repo)", """
WITH io  AS (SELECT DISTINCT team FROM symbols WHERE year IS NOT NULL AND kind='interface' AND name LIKE '%IO'),
     rs  AS (SELECT DISTINCT team FROM symbols WHERE year IS NOT NULL AND name LIKE '%RobotState'),
     sup AS (SELECT DISTINCT team FROM symbols WHERE year IS NOT NULL AND (name LIKE '%Superstructure' OR name LIKE '%RobotManager'))
SELECT
  (SELECT count(*) FROM io) AS io_seam_teams,
  (SELECT count(*) FROM rs) AS robotstate_teams,
  (SELECT count(*) FROM sup) AS coordinator_teams,
  (SELECT count(*) FROM io WHERE team IN (SELECT team FROM rs) AND team IN (SELECT team FROM sup)) AS all_three
""")

# ── B. SUBSYSTEM STRUCTURE — what are the real subsystems? ──────────────────
show("B1 · Most common subsystems/<dir> across the corpus (distinct teams using each)", """
SELECT lower(regexp_extract(file_path, '/subsystems?/([^/]+)/', 1)) AS subsystem,
       count(DISTINCT team) AS teams, count(*) AS files
FROM files
WHERE year IS NOT NULL AND regexp_extract(file_path, '/subsystems?/([^/]+)/', 1) <> ''
GROUP BY 1 HAVING teams >= 3 ORDER BY teams DESC, files DESC LIMIT 25
""")
show("B2 · How many teams even use a subsystems/ directory", """
SELECT count(DISTINCT team) AS teams_with_subsystems_dir,
       (SELECT count(DISTINCT team) FROM files WHERE year IS NOT NULL) AS total
FROM files WHERE year IS NOT NULL AND file_path LIKE '%/subsystems/%'
""")

# ── C. IO SEAM details ─────────────────────────────────────────────────────
show("C1 · IO interfaces per team (latest season), and Inputs/impl companions", """
WITH latest AS (SELECT team, max(year) y FROM symbols WHERE year IS NOT NULL GROUP BY team)
SELECT
  count(*) FILTER (WHERE io>=1) AS teams_with_any_IO,
  count(*) FILTER (WHERE io>=3) AS teams_with_3plus_IO,
  round(avg(io) FILTER (WHERE io>0),1) AS avg_IO_when_present,
  count(*) FILTER (WHERE inputs>0) AS teams_with_Inputs_struct,
  count(*) FILTER (WHERE io>0 AND inputs=0) AS IO_but_no_Inputs_struct
FROM (
  SELECT l.team,
    count(*) FILTER (WHERE s.kind='interface' AND s.name LIKE '%IO') AS io,
    count(*) FILTER (WHERE s.name LIKE '%Inputs') AS inputs
  FROM latest l JOIN symbols s ON s.team=l.team AND s.year=l.y
  GROUP BY l.team)
""")
show("C2 · @AutoLog vs IO interfaces (the 'inputs struct' logging contract)", """
WITH io AS (SELECT DISTINCT team FROM symbols WHERE year IS NOT NULL AND kind='interface' AND name LIKE '%IO'),
     al AS (SELECT DISTINCT team FROM annotations WHERE year IS NOT NULL AND name='AutoLog')
SELECT (SELECT count(*) FROM io) AS io_teams, (SELECT count(*) FROM al) AS autolog_teams,
       (SELECT count(*) FROM io WHERE team IN (SELECT team FROM al)) AS both
""")
show("C3 · Hardware-impl naming variety (suffix after '...IO' in class names)", """
SELECT regexp_extract(name, 'IO([A-Za-z0-9]+)$', 1) AS io_suffix, count(DISTINCT team) AS teams, count(*) AS classes
FROM symbols WHERE year IS NOT NULL AND kind='class' AND name LIKE '%IO_' ESCAPE '_' AND name ~ 'IO[A-Za-z0-9]+$'
GROUP BY 1 HAVING io_suffix <> '' ORDER BY teams DESC LIMIT 20
""")
show("C4 · Loop above vs below the line — methods declared inside *IO interfaces", """
SELECT name AS io_method, count(DISTINCT team) AS teams, count(*) AS decls
FROM symbols
WHERE year IS NOT NULL AND parent_kind='interface' AND parent_name LIKE '%IO'
  AND kind IN ('method','function')
GROUP BY 1 ORDER BY teams DESC LIMIT 20
""")

# ── D. PACKAGE LAYOUT ──────────────────────────────────────────────────────
show("D1 · Top-level package directories (distinct teams with each, season repos)", """
SELECT dir, count(DISTINCT team) AS teams FROM (
  SELECT team, x.dir FROM files, regexp_extract_all(file_path, '/(subsystems?|commands?|superstructure|util|lib|io|generated|constants|autos?|vision|states?|controllers?)/') AS arr,
       unnest(arr) AS t(dir)
  WHERE year IS NOT NULL
) GROUP BY dir ORDER BY teams DESC
""")
show("D2 · lib/ vs robot split (254-style) — teams with a /lib/ package", """
SELECT count(DISTINCT team) AS teams_with_lib_dir FROM files
WHERE year IS NOT NULL AND (file_path LIKE '%/lib/%' OR file_path LIKE '%/frc/lib/%')
""")

# ── E. SPECIFIC NAMED-TEAM CLAIMS ──────────────────────────────────────────
show("E1 · 4738 Patribots — per-mechanism IO interfaces (latest)", """
SELECT DISTINCT name, year FROM symbols WHERE team=4738 AND kind='interface' AND name LIKE '%IO' ORDER BY year DESC, name LIMIT 20
""")
show("E2 · 5137 Iron Kodiaks — generalized MotorIO?", """
SELECT name, kind, count(*) FROM symbols WHERE team=5137 AND (name LIKE '%MotorIO%' OR name LIKE '%IO') GROUP BY 1,2 ORDER BY 1 LIMIT 20
""")
show("E3 · 3647 Millennium Falcons — maple-sim import + 254-style base?", """
SELECT
 (SELECT count(*) FROM imports WHERE team=3647 AND target LIKE 'org.ironmaple%') AS maple_imports,
 (SELECT count(*) FROM symbols WHERE team=3647 AND (name LIKE '%ServoMotorSubsystem%' OR name LIKE '%MotorSubsystem%')) AS servo_base
""")
show("E4 · 3128 Aluminum Narwhals — RobotManager superstructure?", """
SELECT name, kind, year FROM symbols WHERE team=3128 AND (name LIKE '%RobotManager%' OR name LIKE '%Superstructure%' OR name LIKE '%IO') ORDER BY year DESC LIMIT 15
""")

# ── F. VENDOR-LEAK DISCIPLINE ──────────────────────────────────────────────
show("F1 · Vendor imports above the IO line (in files whose name is NOT *IO*), among IO-layer teams", """
WITH io_teams AS (SELECT DISTINCT team FROM symbols WHERE year IS NOT NULL AND kind='interface' AND name LIKE '%IO')
SELECT
  count(DISTINCT team) FILTER (WHERE leaks>0) AS teams_leaking_vendor_above_IO,
  (SELECT count(*) FROM io_teams) AS io_layer_teams
FROM (
  SELECT i.team,
    count(*) FILTER (WHERE (i.target LIKE 'com.ctre%' OR i.target LIKE 'com.revrobotics%')
                     AND i.source_file NOT LIKE '%IO%'
                     AND (i.file_path LIKE '%/subsystems/%' OR i.file_path LIKE '%/commands/%' OR i.file_path LIKE '%superstructure%')) AS leaks
  FROM imports i WHERE i.year IS NOT NULL AND i.team IN (SELECT team FROM io_teams)
  GROUP BY i.team)
""")

# ── G. RUBRIC TOKEN REALITY CHECK ──────────────────────────────────────────
show("G1 · D2 coordination tokens — which actually appear (distinct teams)", """
SELECT
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND name LIKE '%Superstructure') AS superstructure,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND name LIKE '%RobotManager') AS robotmanager,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND kind='enum' AND name LIKE '%WantedState') AS wantedstate_enum,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND (name LIKE '%StateMachine%')) AS statemachine,
 (SELECT count(DISTINCT team) FROM imports WHERE year IS NOT NULL AND target LIKE 'org.jgrapht%') AS jgrapht,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND (name LIKE '%BehaviorTree%')) AS behaviortree
""")
show("G2 · Coordinator-ish class names NOT named Superstructure/RobotManager (what else do teams call it?)", """
SELECT name, count(DISTINCT team) AS teams FROM symbols
WHERE year IS NOT NULL AND kind='class'
  AND (name LIKE '%Coordinator' OR name LIKE '%Manager' OR name LIKE '%StateMachine' OR name LIKE '%Superstructure')
GROUP BY 1 HAVING teams>=2 ORDER BY teams DESC LIMIT 25
""")
show("G3 · D7 vision tokens reality (distinct teams)", """
SELECT
 (SELECT count(DISTINCT team) FROM imports WHERE year IS NOT NULL AND target LIKE 'org.photonvision%') AS photon,
 (SELECT count(DISTINCT team) FROM calls   WHERE year IS NOT NULL AND callee='addVisionMeasurement') AS addvision,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND name LIKE '%RobotState') AS robotstate,
 (SELECT count(DISTINCT team) FROM imports WHERE year IS NOT NULL AND target LIKE '%LimelightHelpers%') AS limelight,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND name LIKE '%PoseEstimator%') AS poseestimator_symbol
""")

# ── H. EMERGENT STRUCTURE (what the docs under-describe) ────────────────────
show("H1 · Common structural class-name suffixes (the real vocabulary)", """
SELECT suffix, count(DISTINCT team) AS teams, count(*) AS classes FROM (
  SELECT team, regexp_extract(name, '([A-Z][a-z]+)$', 1) AS suffix
  FROM symbols WHERE year IS NOT NULL AND kind='class') t
WHERE suffix <> '' GROUP BY suffix ORDER BY teams DESC LIMIT 25
""")
show("H2 · Command structure: commands/ dir + *Command classes + command factories", """
SELECT
 (SELECT count(DISTINCT team) FROM files WHERE year IS NOT NULL AND file_path LIKE '%/commands/%') AS commands_dir_teams,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND kind='class' AND name LIKE '%Command') AS command_class_teams,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND kind='class' AND name LIKE '%Factory') AS factory_teams,
 (SELECT count(DISTINCT team) FROM symbols WHERE year IS NOT NULL AND kind='class' AND name LIKE '%Constants') AS constants_teams
""")
con.close()
