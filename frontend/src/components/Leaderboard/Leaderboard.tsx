import { useEffect, useState } from "react";
import "./Leaderboard.css";

interface LeaderboardEntry {
  username: string;
  cubes_created: number;
  cubes_frozen: number;
  trays_frozen: number;
}

export function Leaderboard() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/leaderboard");
        if (res.ok) {
          const data = await res.json();
          if (!cancelled) setEntries(data);
        }
      } catch {
        // ignore
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (isLoading) {
    return <div className="leaderboard" />;
  }

  return (
    <div className="leaderboard">
      <LeaderboardTable
        title="Ice Cubes Filled"
        statKey="cubes_created"
        entries={entries}
      />

      <LeaderboardTable
        title="Trays Frozen"
        statKey="trays_frozen"
        entries={entries}
      />

      <LeaderboardTable
        title="Cubes Frozen"
        statKey="cubes_frozen"
        entries={entries}
      />
    </div>
  );
}

function LeaderboardTable({
  title,
  statKey,
  entries,
}: {
  title: string;
  statKey: keyof Pick<LeaderboardEntry, "cubes_created" | "cubes_frozen" | "trays_frozen">;
  entries: LeaderboardEntry[];
}) {
  const sorted = [...entries].sort((a, b) => b[statKey] - a[statKey]);

  return (
    <section className="leaderboard__section">
      <h2 className="leaderboard__sectionTitle">{title}</h2>
      {sorted.length === 0 ? (
        <p className="leaderboard__empty">No data yet.</p>
      ) : (
        <table className="leaderboard__table">
          <colgroup>
            <col className="leaderboard__colRank" />
            <col className="leaderboard__colName" />
            <col className="leaderboard__colStat" />
          </colgroup>
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>{title}</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((entry, i) => (
              <tr key={entry.username}>
                <td className="leaderboard__rank">{i + 1}</td>
                <td>{entry.username}</td>
                <td>{entry[statKey]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
