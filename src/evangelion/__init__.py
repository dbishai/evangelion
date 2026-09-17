"""evangelion -- a Coptic Orthodox Gospel lectionary PDF generator.

`evangelion.generate` builds the booklet from the lectionary database
seeded by `evangelion.seed_offline_db` (`uv run evangelion-seed-offline`,
run once first).
"""

from evangelion.generate import main

__all__ = ["main"]
