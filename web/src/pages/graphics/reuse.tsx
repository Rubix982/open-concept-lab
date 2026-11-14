import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import Figure from "@site/src/components/Figure";
import { AS_OF, REUSE, WRITEUP } from "@site/src/data/graphics";

// Everything on this page is taken from the graphics-reuse repository: the axes from
// README.md, the checks from CARD.md and agents/researcher/findings/, the entries from
// entries/. The test bed is private and stays unnamed, as it is in the repository.

const AXES: [string, string][] = [
  ["across time", "the previous frame or step: warm-starting a solver, refitting a bounding-volume tree, reusing the last frame's pixels"],
  ["across space", "a neighbour's work: irradiance caching, ReSTIR's shared light samples"],
  ["across runs", "an earlier run with slightly different inputs: the repeated simulations of a fitting loop"],
  ["across resolutions", "a coarse solution: multigrid, coarse-to-fine cloth"],
  ["across shapes", "a result on another shape or body: deformation transfer, garment transfer"],
  ["across many instances", "work paid once and reused for every case: precomputed radiance transfer, learned models"],
];

const CHECKS: { q: string; a: string }[] = [
  {
    q: "Do the six categories sort real techniques?",
    a:
      "Twelve of twelve sorted cleanly. That is weaker than it sounds: all twelve came from " +
      "the conversation that produced the categories, so the test could hardly fail. A test " +
      "on papers drawn by a fixed procedure is written and waiting.",
  },
  {
    q: "Does an entry tell an AI agent anything it doesn't already know?",
    a:
      "A fresh agent, given only the problem, named 11 of the 18 conditions in the first three " +
      "entries. Those entries had been written from abstracts by the same model, so this mostly " +
      "measured the model against itself. What only the entries carried was a measurement: the " +
      "agent guessed a transferred garment would stretch 9 %, and the test bed measured 6–7 % at " +
      "the median and 22–30 % at the 95th percentile.",
  },
  {
    q: "What does reading the paper in full add?",
    a:
      "One paper, Brouet et al. 2012 on garment transfer, was read in full. Of 16 points taken " +
      "from it, 11 were named by none of three agent runs. The six general ones were all about " +
      "grading, making a version of the garment that fits the new body, which no agent thought " +
      "to ask about. The reading added a different question more than new answers to the " +
      "agents' own.",
  },
];

const ENTRIES: { title: string; file: string; axis: string; changes: string; status: string }[] = [
  { title: "Garment transfer by surface binding", file: "garment-transfer-surface-binding", axis: "across shapes", changes: "the answer", status: "measured in part" },
  { title: "Design-preserving garment transfer", file: "design-preserving-garment-transfer", axis: "across shapes", changes: "the answer", status: "read in full, untested" },
  { title: "Warm-starting repeated drapes", file: "warm-start-repeated-drapes", axis: "across runs", changes: "depends", status: "untested" },
  { title: "Coarse-to-fine cloth", file: "coarse-to-fine-cloth", axis: "across resolutions", changes: "depends on the mechanism", status: "untested" },
];

export default function Reuse(): ReactNode {
  return (
    <Layout
      title="graphics-reuse"
      description="A reference of the ways graphics software avoids redoing work, and of when the reused answer is still good enough."
    >
      <div className="ocl-page">
        <header className="ocl-page__head">
          <p className="ocl-page__kicker"><Link to="/graphics">Graphics</Link></p>
          <h1 className="ocl-page__title">graphics-reuse</h1>
          <p className="ocl-page__lede">
            A reference of the ways graphics software avoids redoing work it has already
            done, and of when the reused answer is still good enough. It starts from papers;
            one entry has been measured.
          </p>
          <p className="ocl-page__note">
            The story of how it got here, with the figures:{" "}
            <Link to={WRITEUP.href}>{WRITEUP.title}</Link>
          </p>
        </header>

        <section className="ocl-ag__sec">
          <h2>Where it started</h2>
          <p>
            In a private cloth-simulation test bed, one drape of a garment piece of about
            5,000 vertices took 4–7 minutes, and nearly all of a run's time went to the
            solver. The largest saving on record there came from not redoing work: carrying
            an already-settled garment onto a new body took 1.2 seconds, against about 6
            minutes for a fresh drape. Graphics is full of moves like that, and the hard
            part is usually knowing when the reused answer is still right.
          </p>
          <Figure
            src="/img/writing/garment-transfer.svg"
            alt="A kameez, trousers and dupatta draped on a figure 1.609 m tall are carried in 1.2 seconds to a figure 1.753 m tall. The kameez and trousers come out graded to the new body, with edges 6 to 7 percent longer at the median and 22 to 30 percent longer at the 95th percentile. The dupatta's free end tears. Below, on one time axis, draping again takes about 6 minutes and carrying over takes 1.2 seconds."
            caption="The one measured entry. The body-hugging pieces survived the trip and the free-hanging one did not."
            plain
          />
        </section>

        <section className="ocl-ag__sec">
          <h2>How entries are filed</h2>
          <p>By what gets reused, since the same moves turn up in rendering, simulation and geometry:</p>
          <Figure
            src="/img/writing/six-ways-to-reuse.svg"
            alt="Six small drawings in two rows, one for each thing graphics software reuses: the previous frame, a neighbour's work, an earlier and slightly different run, a coarse solution, a result on another shape, and work paid once and used for every case."
            caption="The six categories, by what gets reused."
            plain
          />
          <dl className="ocl-ag__dl">
            {AXES.map(([name, body]) => (
              <div key={name} className="ocl-ag__dlRow">
                <dt>{name}</dt>
                <dd>{body}</dd>
              </div>
            ))}
          </dl>
          <p>
            And by whether the reuse changes the answer. Refitting a tree changes only the
            cost: queries stay correct and get slower as the tree loosens. Reusing the last
            frame's pixels changes the answer, which shows as ghosting when the history is
            stale. Conditions for when reuse is safe matter mostly for the second kind.
          </p>
          <Figure
            src="/img/writing/cost-or-answer.svg"
            alt="Left: bounding boxes refitted around points that have drifted apart grow large and overlapping, but every point is still inside its box, so queries stay right and get slower. Right: a moving ball with fading copies trailing behind it, where reused pixels from older frames leave a ghost."
            caption="Reuse that changes only the cost fails by slowing down; reuse that changes the answer fails by being wrong."
            plain
          />
          <p>
            Each entry says what work is wasted, which technique avoids it and where it comes
            from, when the reuse stays valid, how it fails, how to check it, and where it was
            measured. Every condition is marked as coming from a paper, from a measurement, or
            from reasoning nobody has tested yet.
          </p>
        </section>

        <section className="ocl-ag__sec">
          <h2>What the checks found</h2>
          <dl className="ocl-ag__dl">
            {CHECKS.map(({ q, a }) => (
              <div key={q} className="ocl-ag__dlRow">
                <dt>{q}</dt>
                <dd>{a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <Figure
          src="/img/writing/redrape-or-grade.svg"
          alt="Three figures with a dashed line at knee height. The first body wears a flared dress with its hem at the knee. A taller body wears the same pattern draped again: the hem rides well above the knee and the cloth pulls. The taller body wears the dress graded to it: the hem is back at the knee and the flare keeps its slope."
          caption="What the full reading added: a garment moved to a new body can be draped again or graded, and no agent asked which was wanted."
          plain
        />

        <section className="ocl-ag__sec">
          <h2>Entries so far</h2>
          <div className="ocl-table__scroll">
            <table>
              <thead>
                <tr><th>entry</th><th>reuses</th><th>changes</th><th>status</th></tr>
              </thead>
              <tbody>
                {ENTRIES.map((e) => (
                  <tr key={e.file}>
                    <td><a href={`${REUSE.repo}/blob/main/entries/${e.file}.md`} target="_blank" rel="noreferrer">{e.title}</a></td>
                    <td>{e.axis}</td>
                    <td>{e.changes}</td>
                    <td>{e.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="ocl-ag__sec ocl-ag__limit">
          <h2>What it can't show yet</h2>
          <p>
            Every check so far was scored by a model of the same family the agents run on,
            from lists it wrote. Where it could, the list was fixed before the answers were
            read, but not every time. One paper has been read in full and one entry measured,
            in one test bed.
          </p>
          <p>
            No entry has been tried yet as context for an agent doing real work, which is
            what the library is meant for. Until then it is a map for whoever reads it.
          </p>
        </section>

        <p className="ocl-page__foot">
          Source: <a href={REUSE.repo} target="_blank" rel="noreferrer">github.com/Rubix982/graphics-reuse</a>.
          The method is adapted from{" "}
          <a href="https://github.com/Rubix982/patternbook" target="_blank" rel="noreferrer">patternbook</a>.
          Figures as of {AS_OF}.
        </p>
      </div>
    </Layout>
  );
}
