"""Kùzu-backed store for the claim knowledge graph.

Schema:
  Paper(id, title, year, venue, url)
  Claim(id, text, paper_id, section, char_start, char_end, emb DOUBLE[dim])
  (Claim)-[:FROM_PAPER]->(Paper)
  (Claim)-[:RELATES {rel_type, score, similarity}]->(Claim)
    rel_type in {SUPPORTS, CONTRADICTS, RELATED}; score = NLI prob; similarity = cosine.

All writes are parameterized. `fresh=True` wipes the DB dir for an idempotent rebuild.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import kuzu


class GraphStore:
    def __init__(self, path: str | Path, embed_dim: int = 384, fresh: bool = False):
        self.path = Path(path)
        self.embed_dim = embed_dim
        if fresh:
            # Kùzu may store the DB as a single file or a directory, plus a sibling
            # .wal — remove whichever exists for an idempotent rebuild.
            for p in (self.path, self.path.with_name(self.path.name + ".wal")):
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.exists():
                    p.unlink()
        self.db = kuzu.Database(str(self.path))
        self.con = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self) -> None:
        self.con.execute(
            "CREATE NODE TABLE IF NOT EXISTS Paper("
            "id STRING, title STRING, year INT64, venue STRING, url STRING,"
            " PRIMARY KEY(id))"
        )
        self.con.execute(
            "CREATE NODE TABLE IF NOT EXISTS Claim("
            "id STRING, text STRING, paper_id STRING, section STRING,"
            f" char_start INT64, char_end INT64, emb DOUBLE[{self.embed_dim}],"
            " PRIMARY KEY(id))"
        )
        self.con.execute(
            "CREATE REL TABLE IF NOT EXISTS FROM_PAPER(FROM Claim TO Paper)"
        )
        self.con.execute(
            "CREATE REL TABLE IF NOT EXISTS RELATES("
            "FROM Claim TO Claim, rel_type STRING, score DOUBLE, similarity DOUBLE,"
            " direction STRING, rationale STRING)"
        )

    # ---- writes ----
    def add_paper(self, meta: dict[str, Any]) -> None:
        self.con.execute(
            "MERGE (p:Paper {id:$id}) SET p.title=$title, p.year=$year,"
            " p.venue=$venue, p.url=$url",
            parameters={
                "id": meta["paper_id"],
                "title": meta.get("title") or "",
                "year": int(meta["year"]) if meta.get("year") else 0,
                "venue": meta.get("venue") or "",
                "url": meta.get("url") or "",
            },
        )

    def add_claim(
        self,
        claim_id: str,
        text: str,
        paper_id: str,
        section: str,
        char_start: int,
        char_end: int,
        embedding: list[float],
    ) -> None:
        self.con.execute(
            "CREATE (:Claim {id:$id, text:$text, paper_id:$pid, section:$sec,"
            " char_start:$cs, char_end:$ce, emb:$emb})",
            parameters={
                "id": claim_id,
                "text": text,
                "pid": paper_id,
                "sec": section,
                "cs": char_start,
                "ce": char_end,
                "emb": embedding,
            },
        )
        self.con.execute(
            "MATCH (c:Claim {id:$cid}), (p:Paper {id:$pid})"
            " CREATE (c)-[:FROM_PAPER]->(p)",
            parameters={"cid": claim_id, "pid": paper_id},
        )

    def add_relation(
        self,
        src_id: str,
        dst_id: str,
        rel_type: str,
        score: float,
        similarity: float,
        direction: str = "SYMMETRIC",
        rationale: str = "",
    ) -> None:
        self.con.execute(
            "MATCH (a:Claim {id:$a}), (b:Claim {id:$b})"
            " CREATE (a)-[:RELATES {rel_type:$rt, score:$sc, similarity:$sim,"
            " direction:$dir, rationale:$rat}]->(b)",
            parameters={
                "a": src_id,
                "b": dst_id,
                "rt": rel_type,
                "sc": float(score),
                "sim": float(similarity),
                "dir": direction,
                "rat": rationale,
            },
        )

    # ---- reads ----
    def all_claims(self) -> list[dict[str, Any]]:
        res = self.con.execute(
            "MATCH (c:Claim) RETURN c.id, c.text, c.emb, c.paper_id"
        )
        out: list[dict[str, Any]] = []
        while res.has_next():
            cid, text, emb, pid = res.get_next()
            out.append({"id": cid, "text": text, "emb": emb, "paper_id": pid})
        return out

    def claim_with_paper(self, claim_id: str) -> dict[str, Any] | None:
        res = self.con.execute(
            "MATCH (c:Claim {id:$id})-[:FROM_PAPER]->(p:Paper)"
            " RETURN c.text, p.title, p.year, p.url",
            parameters={"id": claim_id},
        )
        if res.has_next():
            text, title, year, url = res.get_next()
            return {"text": text, "title": title, "year": year, "url": url}
        return None

    def related(self, claim_id: str) -> list[dict[str, Any]]:
        """Return claims related to `claim_id` (both directions) with edge info."""
        res = self.con.execute(
            "MATCH (c:Claim {id:$id})-[r:RELATES]-(o:Claim)-[:FROM_PAPER]->(p:Paper)"
            " RETURN o.id, o.text, r.rel_type, r.score, p.title, p.year",
            parameters={"id": claim_id},
        )
        out: list[dict[str, Any]] = []
        while res.has_next():
            oid, otext, rt, score, title, year = res.get_next()
            out.append(
                {
                    "id": oid,
                    "text": otext,
                    "rel_type": rt,
                    "score": score,
                    "title": title,
                    "year": year,
                }
            )
        return out

    def counts(self) -> dict[str, int]:
        def _count(q: str) -> int:
            res = self.con.execute(q)
            return res.get_next()[0] if res.has_next() else 0

        return {
            "papers": _count("MATCH (p:Paper) RETURN count(p)"),
            "claims": _count("MATCH (c:Claim) RETURN count(c)"),
            "edges": _count("MATCH ()-[r:RELATES]->() RETURN count(r)"),
        }
