"""Rich per-(team, year) feature matrix from the DuckDB code index.

This is the single source of truth for the *expanded* code-sophistication signals — far
more than the 6 aggregate queries the original mechanical scorer used. Both the
EPA-prediction notebook (`scripts/build_prediction_notebook.py`) and the production scorer
draw from here, so a signal is defined once.

Design notes / what the exploration taught us (all verified against the corpus):
  * The honest modeling panel is ~232 team-years across 55 teams (EPA status='ok' joined to
    cloned code). Repeated measures are severe, so downstream analysis must group by `team`.
  * "Score what's USED, not present": where possible a signal is a *call* or a *deploy file*
    actually referenced in code (e.g. `fromChoreoTrajectory`), not just a vendordep import.
  * Brittle names retired: `*IOReal` (only ~5 teams) is kept but de-emphasised in favour of
    device-named impls (`*IOTalonFX/*IOSparkMax/*IOKraken`, 18 teams, 309 classes).
  * Build-file linting (spotless/checkstyle) is NOT detectable: `.gradle` files are listed in
    `files` but their DSL is not parsed, so D8 process leans on CI-workflow + repo/commit
    metadata instead.

Usage:
    import duckdb
    from scout import features
    con = duckdb.connect("data/code-index.duckdb", read_only=True)
    df = features.build(con)                 # one row per (team, year), raw + derived columns
    panel = features.panel(con)              # df ⋈ EPA(status='ok') + name + is_sandiego
    X = features.model_matrix(df)            # log1p the count columns -> model-ready
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Vendor packages whose appearance ABOVE the IO line is the architecture smell.
_VENDOR = "(target LIKE 'com.ctre%' OR target LIKE 'com.revrobotics%' OR target LIKE 'org.photonvision%')"

# "Above the IO line" consumer files — a vendor import here is the leak we care about. Defined
# POSITIVELY (subsystem/command/coordinator/robot-level names) rather than "not an IO file": the
# latter false-positives on teams that wrap hardware under non-IO names (e.g. Patribots' Kraken.java,
# SafeSpark.java). This is a coarse filename proxy; the agent tier confirms real confinement by reading.
_ABOVE_LINE = ("(source_file LIKE '%Subsystem.java' OR source_file LIKE '%Superstructure%' "
               "OR source_file LIKE '%RobotState%' OR source_file LIKE '%RobotContainer%' "
               "OR source_file = 'Robot.java' OR source_file LIKE '%Command.java')")

# Device-named IO implementations — the real-world naming (not the rare `*IOReal`).
_IO_DEVICE = ("(name LIKE '%IOTalonFX' OR name LIKE '%IOKraken' OR name LIKE '%IOSparkMax' "
              "OR name LIKE '%IOSpark' OR name LIKE '%IOFalcon' OR name LIKE '%IONeo' "
              "OR name LIKE '%IOPigeon2' OR name LIKE '%IOCANcoder' OR name LIKE '%IONavX')")

# WPILib mechanism-physics constructors (callee = bare class name in the `calls` table).
_SIM_CTORS = "('ElevatorSim','SingleJointedArmSim','FlywheelSim','DCMotorSim','SwerveDriveSim')"

# JUnit + gtest assertion family (density signal for D4).
_ASSERTS = ("('assertEquals','assertTrue','assertFalse','assertThat','assertNotNull',"
            "'assertSame','EXPECT_EQ','EXPECT_TRUE','EXPECT_FALSE','EXPECT_NEAR','ASSERT_EQ','ASSERT_TRUE')")


def _q(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


# --- per-(team, year) raw feature blocks -----------------------------------------------------

def _symbols(con) -> pd.DataFrame:
    return _q(con, f"""
      SELECT team, year,
        -- D1 architecture
        count(*) FILTER (WHERE kind='interface' AND name LIKE '%IO')             AS d1_io_iface,
        count(*) FILTER (WHERE kind='class' AND name LIKE '%IOSim')              AS d1_io_sim,
        count(*) FILTER (WHERE kind='class' AND {_IO_DEVICE})                    AS d1_io_device,
        count(*) FILTER (WHERE kind='class' AND name LIKE '%IOReal')             AS d1_io_real,
        count(*) FILTER (WHERE kind='interface' AND name LIKE '%MotorIO')        AS d1_generic_motorio,
        count(*) FILTER (WHERE name LIKE '%ServoMotorSubsystem')                 AS d1_servomotor,
        count(*) FILTER (WHERE name LIKE '%TunerConstants')                      AS d1_tuner,
        -- D2 coordination
        count(*) FILTER (WHERE name LIKE '%Superstructure' OR name LIKE '%RobotManager') AS d2_coordinator,
        count(*) FILTER (WHERE kind='enum' AND (name LIKE '%WantedState' OR name LIKE '%SystemState')) AS d2_fsm_enum,
        count(*) FILTER (WHERE kind='enum' AND name LIKE '%Goal')                AS d2_goal_enum,
        count(*) FILTER (WHERE kind='method' AND name LIKE 'handleState%')       AS d2_handle_transitions,
        count(*) FILTER (WHERE kind='method' AND name IN ('requestGoal','request')) AS d2_request_api,
        count(*) FILTER (WHERE name LIKE '%AStarSolver' OR name LIKE '%BehaviorTree%') AS d2_graph,
        -- D3 simulation
        count(*) FILTER (WHERE name='simulationPeriodic')                        AS d3_sim_periodic,
        count(*) FILTER (WHERE name LIKE '%IOReplay')                            AS d3_replay,
        count(*) FILTER (WHERE name LIKE '%IONull' OR name LIKE '%IOReplay' OR name LIKE '%IdealSim') AS d3_io_adv,
        -- D5 logging
        count(*) FILTER (WHERE name LIKE '%FaultReporter')                       AS d5_faultreporter,
        -- D6 auto
        count(*) FILTER (WHERE name LIKE '%Repulsor')                            AS d6_repulsor,
        -- D7 vision
        count(*) FILTER (WHERE name LIKE '%RobotState')                          AS d7_robotstate,
        count(*) FILTER (WHERE kind='interface' AND (name LIKE 'Vision%IO' OR name LIKE '%VisionIO')) AS d7_vision_io,
        -- size / complexity
        count(*) FILTER (WHERE kind='method')                                    AS size_methods,
        count(*) FILTER (WHERE kind='class')                                     AS size_classes,
        count(*) FILTER (WHERE kind='interface')                                 AS size_interfaces,
        count(*) FILTER (WHERE kind='enum')                                      AS size_enums
      FROM symbols GROUP BY team, year""")


def _imports(con) -> pd.DataFrame:
    return _q(con, f"""
      SELECT team, year,
        count(*) FILTER (WHERE target LIKE 'swervelib%')                         AS d1_yagsl,
        count(*) FILTER (WHERE {_VENDOR})                                        AS d1_vendor_total,
        count(*) FILTER (WHERE {_VENDOR} AND {_ABOVE_LINE})                      AS d1_vendor_above,
        count(*) FILTER (WHERE target LIKE 'org.jgrapht%')                       AS d2_jgrapht,
        count(*) FILTER (WHERE target LIKE 'org.ironmaple%')                     AS d3_maple,
        count(*) FILTER (WHERE target LIKE '%wpilibj.simulation%')               AS d3_wpilib_sim,
        count(*) FILTER (WHERE target LIKE 'org.junit%')                         AS d4_junit,
        count(*) FILTER (WHERE target LIKE 'edu.wpi.first.hal%')                 AS d4_hal,
        count(*) FILTER (WHERE target LIKE 'org.littletonrobotics.junction%')    AS d5_advantagekit,
        count(*) FILTER (WHERE target LIKE 'dev.doglog%')                        AS d5_doglog,
        count(*) FILTER (WHERE target LIKE '%epilogue%')                         AS d5_epilogue,
        count(*) FILTER (WHERE target LIKE 'com.pathplanner%')                   AS d6_pathplanner,
        count(*) FILTER (WHERE target LIKE 'choreo%')                            AS d6_choreo_imp,
        count(*) FILTER (WHERE target LIKE 'org.photonvision%')                  AS d7_photon,
        count(*) FILTER (WHERE target LIKE '%PoseEstimator%')                    AS d7_poseest,
        count(*) FILTER (WHERE target LIKE '%LimelightHelpers%')                 AS d7_limelight,
        count(*) FILTER (WHERE target LIKE '%TimeInterpolatableBuffer%')         AS d7_tib,
        count(DISTINCT target)                                                   AS size_distinct_imports
      FROM imports GROUP BY team, year""")


def _calls(con) -> pd.DataFrame:
    return _q(con, f"""
      SELECT team, year,
        coalesce(sum(n) FILTER (WHERE callee IN {_SIM_CTORS}), 0)                AS d3_sim_ctor,
        coalesce(sum(n) FILTER (WHERE callee='stepTiming'), 0)                   AS d3_steptiming,
        coalesce(sum(n) FILTER (WHERE callee IN {_ASSERTS}), 0)                  AS d4_asserts,
        coalesce(sum(n) FILTER (WHERE callee='runToCompletion'), 0)             AS d4_runtocompletion,
        coalesce(sum(n) FILTER (WHERE callee='recordOutput'), 0)                AS d5_recordoutput,
        coalesce(sum(n) FILTER (WHERE callee='processInputs'), 0)               AS d5_processinputs,
        coalesce(sum(n) FILTER (WHERE callee LIKE 'put%'), 0)                    AS d5_dashboard,
        coalesce(sum(n) FILTER (WHERE callee IN ('fromChoreoTrajectory','Choreo')), 0) AS d6_choreo_used,
        coalesce(sum(n) FILTER (WHERE callee LIKE 'pathfind%'), 0)               AS d6_pathfind,
        coalesce(sum(n) FILTER (WHERE callee='addVisionMeasurement'), 0)         AS d7_addvision,
        coalesce(sum(n) FILTER (WHERE callee='setVisionMeasurementStdDevs'), 0)  AS d7_stddev
      FROM calls GROUP BY team, year""")


def _annotations(con) -> pd.DataFrame:
    return _q(con, """
      SELECT team, year,
        coalesce(sum(n) FILTER (WHERE name='AutoLog'), 0)                        AS d5_autolog,
        coalesce(sum(n) FILTER (WHERE name IN ('Logged','Epilogue')), 0)         AS d5_logged_ann,
        coalesce(sum(n) FILTER (WHERE name='Test'), 0)                           AS d4_test_ann
      FROM annotations GROUP BY team, year""")


def _deploy(con) -> pd.DataFrame:
    return _q(con, """
      SELECT team, year,
        count(*) FILTER (WHERE kind LIKE 'pathplanner%')                         AS d6_pp_files,
        count(*) FILTER (WHERE kind='choreo')                                    AS d6_choreo_files,
        count(*) FILTER (WHERE kind='ci_workflow')                               AS d4_ci_files,
        count(*) FILTER (WHERE kind='swerve_config')                             AS d1_swerve_cfg
      FROM deploy_files GROUP BY team, year""")


def _files(con) -> pd.DataFrame:
    return _q(con, """
      SELECT team, year,
        count(*)                                                                 AS size_files,
        coalesce(sum(line_count), 0)                                             AS size_loc,
        count(*) FILTER (WHERE file_path LIKE '%/test/%')                        AS d4_test_files,
        count(DISTINCT lang)                                                     AS size_langs,
        avg(CASE WHEN lang='java' THEN 1.0 ELSE 0.0 END)                         AS size_frac_java
      FROM files GROUP BY team, year""")


def _repo_year(con) -> pd.DataFrame:
    """Per-(team, year) commit dynamics from the season repos (program-age confounded)."""
    return _q(con, """
      SELECT team, year,
        coalesce(sum(commits), 0)                                                AS d8_commits,
        coalesce(sum(insertions), 0)                                             AS d8_insertions,
        coalesce(sum(deletions), 0)                                              AS d8_deletions,
        coalesce(sum(files_touched), 0)                                          AS d8_files_touched,
        coalesce(max(contributors), 0)                                           AS d8_contrib_year,
        coalesce(date_diff('day', min(first_commit), max(last_commit)), 0)       AS d8_season_days
      FROM repos WHERE cloned AND bucket='season' AND year > 0
      GROUP BY team, year""")


def _team_level(con) -> pd.DataFrame:
    """Team attributes (constant within a team — vanish under within-team demeaning, by design)."""
    d8 = _q(con, """
      SELECT team,
        count(DISTINCT year) FILTER (WHERE bucket='season')                      AS d8_n_seasons,
        coalesce(max(contributors), 0)                                           AS d8_contrib_max,
        CAST(bool_or(bucket='library') AS INTEGER)                               AS d8_has_library
      FROM repos WHERE cloned GROUP BY team""")
    ci = _q(con, "SELECT team, count(*) AS d8_ci_any FROM deploy_files WHERE kind='ci_workflow' GROUP BY team")
    return d8.merge(ci, on="team", how="left")


# --- assembly ---------------------------------------------------------------------------------

def build(con) -> pd.DataFrame:
    """Per-(team, year) feature matrix (seasonal repos only), raw counts + a few derived ratios."""
    feat = _files(con)
    for block in (_symbols, _imports, _calls, _annotations, _deploy, _repo_year):
        feat = feat.merge(block(con), on=["team", "year"], how="left")
    feat = feat[feat.year.fillna(0) > 0].copy()
    feat = feat.merge(_team_level(con), on="team", how="left")
    feat = feat.fillna(0)
    feat["team"] = feat.team.astype(int)
    feat["year"] = feat.year.astype(int)

    # Derived ratio features (size-normalised so we don't just re-measure repo bulk).
    kloc = feat.size_loc / 1000.0
    feat["d4_asserts_per_kloc"] = feat.d4_asserts / (kloc + 1)
    feat["d5_record_per_file"] = feat.d5_recordoutput / (feat.size_files + 1)
    feat["d5_processinputs_per_file"] = feat.d5_processinputs / (feat.size_files + 1)
    # Vendor-confinement proxy: fraction of vendor imports sitting in above-the-IO-line files
    # (subsystem/command/coordinator). Lower = better confined. Coarse; agent tier confirms.
    feat["d1_vendor_above_ratio"] = np.where(
        feat.d1_vendor_total > 0, feat.d1_vendor_above / feat.d1_vendor_total, 0.0)
    return feat


# Columns to log1p before modelling (right-skewed counts). Ratios/levels/fractions excluded.
COUNT_COLS = [
    "size_files", "size_loc", "size_methods", "size_classes", "size_interfaces", "size_enums",
    "size_distinct_imports", "d1_io_iface", "d1_io_sim", "d1_io_device", "d1_io_real",
    "d1_generic_motorio", "d1_servomotor", "d1_tuner", "d1_yagsl", "d1_vendor_total",
    "d1_vendor_above", "d1_swerve_cfg", "d2_coordinator", "d2_fsm_enum", "d2_goal_enum",
    "d2_handle_transitions", "d2_request_api", "d2_graph", "d2_jgrapht", "d3_sim_periodic",
    "d3_replay", "d3_io_adv", "d3_maple", "d3_wpilib_sim", "d3_sim_ctor", "d3_steptiming",
    "d4_test_files", "d4_asserts", "d4_test_ann", "d4_junit", "d4_hal", "d4_runtocompletion",
    "d4_ci_files", "d5_faultreporter", "d5_advantagekit", "d5_doglog", "d5_epilogue",
    "d5_autolog", "d5_logged_ann", "d5_recordoutput", "d5_processinputs", "d5_dashboard",
    "d6_repulsor", "d6_pathplanner", "d6_choreo_imp", "d6_pp_files", "d6_choreo_files",
    "d6_choreo_used", "d6_pathfind", "d7_robotstate", "d7_vision_io", "d7_photon",
    "d7_poseest", "d7_limelight", "d7_tib", "d7_addvision", "d7_stddev", "d8_commits",
    "d8_insertions", "d8_deletions", "d8_files_touched", "d8_contrib_year", "d8_season_days",
    "d8_n_seasons", "d8_contrib_max", "d8_ci_any",
]

KEY_COLS = ["team", "year"]


def feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in KEY_COLS]


DIMS = [f"D{i}" for i in range(1, 9)]


def _lvl(*pairs):
    for cond, level in pairs:
        if cond:
            return level
    return 0


def candidate_levels(r) -> dict:
    """The mechanical candidate D1–D8, computed from a `build()` feature row.

    This is the **as-studied baseline** (the original presence-based thresholds) that
    `notebooks/epa-prediction.ipynb` reproduces and that the study compares against the agent tier
    (mechanical CV ρ≈0.29 vs agent-confirmed ρ≈0.53) — kept frozen so that finding stays
    reproducible. The post-study signal improvements (Choreo-used-not-present for D6, RobotState+
    TimeInterpolatableBuffer for D7) live in `scripts/build_notebook.py:score()`; the validated
    accuracy path is the agent confirmation tier (`scripts/agent_score.py`). A candidate is a *lead*,
    confirmed by reading — see knowledge/rubric/rubric.md."""
    return {
        "D1": _lvl((r.d1_servomotor > 0 or r.d3_io_adv > 0, 4), (r.d1_io_iface >= 2, 3),
                   (r.d1_io_iface == 1 or r.d1_yagsl > 0 or r.d1_tuner > 0, 2), (r.size_files > 0, 1)),
        "D2": _lvl((r.d2_graph > 0 or r.d2_jgrapht > 0, 4), (r.d2_coordinator > 0, 3),
                   (r.d2_fsm_enum > 0, 2), (r.size_files > 0, 1)),
        "D3": _lvl((r.d3_io_adv > 0, 4), (r.d3_maple > 0, 3), (r.d3_wpilib_sim > 0, 2),
                   (r.d3_sim_periodic > 0, 1)),
        "D4": _lvl((r.d4_runtocompletion > 0 or (r.d4_test_files >= 10 and r.d4_asserts > 0), 4),
                   (r.d4_ci_files > 0 and r.d4_test_files > 0, 3),
                   (r.d4_test_files > 0 and (r.d4_asserts > 0 or r.d4_test_ann > 0), 2),
                   (r.d4_test_files > 0 or r.d4_test_ann > 0, 1)),
        "D5": _lvl((r.d5_faultreporter > 0 or r.d3_io_adv > 0, 4),
                   (r.d5_advantagekit > 0 and r.d5_autolog > 0, 3),
                   (r.d5_doglog > 0 or r.d5_logged_ann > 0 or r.d5_epilogue > 0, 2),
                   (r.d5_dashboard > 0, 1)),
        "D6": _lvl((r.d6_repulsor > 0, 4), (r.d6_choreo_imp > 0 or r.d6_choreo_files > 0, 3),
                   (r.d6_pathplanner > 0 or r.d6_pp_files > 0, 2), (r.size_files > 0, 1)),
        "D7": _lvl((r.d7_robotstate > 0, 4), (r.d7_photon > 0 and r.d7_addvision > 0, 3),
                   (r.d7_poseest > 0 or r.d7_addvision > 0, 2), (r.d7_limelight > 0, 1)),
        "D8": _lvl((r.d8_n_seasons >= 4 and r.d8_has_library > 0 and r.d8_ci_any > 0, 4),
                   (r.d8_ci_any > 0 and r.d8_has_library > 0, 3),
                   (r.d8_contrib_max >= 5 or r.d8_has_library > 0, 2), (r.d8_contrib_max >= 2, 1)),
    }


def model_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with COUNT_COLS log1p-transformed; ratios/fractions left as-is."""
    out = df.copy()
    for c in COUNT_COLS:
        if c in out.columns:
            out[c] = np.log1p(out[c].clip(lower=0))
    return out


# --- targets + metadata -----------------------------------------------------------------------

def load_targets(con) -> pd.DataFrame:
    return _q(con, """
      SELECT team, year, norm_epa, state_pctile, winrate, epa_points, unitless_epa
      FROM epa WHERE status='ok'""")


def load_meta(con) -> pd.DataFrame:
    m = _q(con, "SELECT team, name, sources FROM teams")
    m["is_sandiego"] = m.sources.apply(lambda s: s is not None and "sandiego" in list(s))
    return m[["team", "name", "is_sandiego"]]


def panel(con) -> pd.DataFrame:
    """Feature matrix inner-joined to season-matched EPA, with name + is_sandiego attached.

    This is the honest modelling panel: ~232 team-years across 55 teams.
    """
    df = build(con)
    tgt = load_targets(con)
    meta = load_meta(con)
    return (df.merge(tgt, on=["team", "year"], how="inner")
              .merge(meta, on="team", how="left"))


if __name__ == "__main__":  # quick smoke test: `uv run python -m scout.features`
    import duckdb
    from pathlib import Path

    root = next((b for b in [Path.cwd(), *Path.cwd().parents]
                 if (b / "data" / "code-index.duckdb").exists()), None)
    if root is None:
        raise SystemExit("run `python3 main.py index-db` first")
    con = duckdb.connect(str(root / "data" / "code-index.duckdb"), read_only=True)
    df = build(con)
    pan = panel(con)
    print(f"feature matrix: {df.shape[0]} team-years x {len(feature_cols(df))} features")
    print(f"modelling panel (⋈ EPA ok): {pan.shape[0]} rows x {pan.team.nunique()} teams "
          f"({pan.is_sandiego.sum()} San Diego)")
    print("feature columns:", ", ".join(feature_cols(df)))
