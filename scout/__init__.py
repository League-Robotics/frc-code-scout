"""FRC Code Scout corpus builder.

Assembles a multi-year FRC team code corpus + a master EPA/repo dataset:
discover each team's season repos, clone with full history, extract the commit
activity log (history.json), strip .git, suppress large working-tree files to
*.sup stubs, and look up Statbotics EPA per team per year.

Pure standard library — no third-party dependencies.
"""

__all__ = ["config"]
