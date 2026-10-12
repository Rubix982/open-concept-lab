import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";

const SITE = "https://advisoratlas.fyi/";
// Figures as of the golden dataset (9 October 2026), the same as the app's own overview page.
const TALLY: [string, string][] = [
  ["198,570", "researchers"],
  ["700", "universities"],
  ["61", "countries"],
  ["1.26M", "recent papers"],
  ["1.1M", "research grants"],
  ["42", "funders"],
  ["183,002", "grants running now"],
  ["95", "scholarship programmes"],
];

function Shot({ name, alt }: { name: string; alt: string }): ReactNode {
  const src = useBaseUrl(`/img/shipped/advisor-atlas/${name}.jpg`);
  return (
    <a href={src} target="_blank" rel="noreferrer" className="ocl-ship__shot">
      <img src={src} alt={alt} loading="lazy" decoding="async" />
    </a>
  );
}

function Step({ n, title, shot, alt, children }: {
  n: number; title: string; shot: string; alt: string; children: ReactNode;
}): ReactNode {
  return (
    <li className="ocl-ship__step">
      <div className="ocl-ship__stepText">
        <h3><span className="ocl-ship__stepN">{n}</span>{title}</h3>
        {children}
      </div>
      <Shot name={shot} alt={alt} />
    </li>
  );
}

export default function AdvisorAtlas(): ReactNode {
  return (
    <Layout
      title="Advisor Atlas"
      description="A map for finding a PhD advisor and a way to pay for the degree, made first for students in Pakistan applying abroad."
    >
      <div className="ocl-page ocl-ship">
        <p className="ocl-ship__back"><Link to="/shipped">Shipped</Link></p>
        <header className="ocl-ship__head">
          <h1 className="ocl-page__title">Advisor Atlas</h1>
          <p className="ocl-ship__lede">
            A map for finding a PhD advisor, and a way to pay for the degree. Made
            first for students in Pakistan applying abroad, who usually do this
            with spreadsheets and guesswork.
          </p>
          <p className="ocl-ship__actions">
            <a href={SITE} target="_blank" rel="noreferrer" className="ocl-ship__primary">Open advisoratlas.fyi ↗</a>
            <a href={`${SITE}?tour=1`} target="_blank" rel="noreferrer">Take the tour ↗</a>
          </p>
          <dl className="ocl-ship__facts">
            <div><dt>Live since</dt><dd>11 October 2026</dd></div>
            <div><dt>Data as of</dt><dd>9 October 2026</dd></div>
            <div><dt>Now</dt><dd>Open to students for feedback</dd></div>
          </dl>
        </header>

        <Shot name="map" alt="Advisor Atlas: a map of universities sized by faculty, beside a search box and a list of universities." />

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Why it exists</h2>
          <p>
            More than half of Pakistan is under thirty. Many of them want to do
            research, and few can see what research is being done: which
            questions are open, who is asking them, with what money, and how a
            student gets in. Industry teaches you to make things; research is
            where you learn to think of new things to make.
          </p>
          <p>
            Advisor Atlas is a window onto those open questions, with the way in
            drawn on it. The PhD advisor is the most concrete door, so it starts
            there. The usual way through it is a spreadsheet of famous names,
            emailed one after another, with no way to tell who has the money to
            take a student this year, or whose lab is new and looking for its
            first ones.
          </p>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What a student does with it</h2>
          <ol className="ocl-ship__steps">
            <Step n={1} title="Say what you want to research" shot="search"
              alt="A search for low-resource languages: researchers on a world map, and a ranked list beside it.">
              <p>
                In your own words, not a field's vocabulary. The search reads
                meaning, so <i>low-resource languages</i> finds 2,356 people at
                491 universities, ranked by how close their recent work is, each
                with the paper that matched.
              </p>
            </Step>
            <Step n={2} title="Read a profile before writing" shot="profile"
              alt="A researcher's profile with a 'Before you write' checklist.">
              <p>
                Recent papers, the grants they hold, who they work with, and a
                short checklist for the first email: the paper closest to your
                search, whether a grant is running, whether the lab is new, and
                what their homepage says about prospective students.
              </p>
            </Step>
            <Step n={3} title="Find the money" shot="funding"
              alt="Funding for malaria vaccine: who pays, with counts and amounts per funder.">
              <p>
                Who pays for your topic, across every grant loaded, not only
                those of people on the map. For <i>malaria vaccine</i>: 1,870
                grants, 590 of them running, and which funders they come from.
              </p>
            </Step>
            <Step n={4} title="Look closely at a university" shot="university"
              alt="LUMS: research strengths by area, and how PhDs there are paid for.">
              <p>
                Its research strengths, who funds its faculty, PhD programmes
                that pay students directly, the grants held there, and the
                scholarships open to you from your country.
              </p>
            </Step>
          </ol>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What it holds</h2>
          <dl className="ocl-tally ocl-ship__tally">
            {TALLY.map(([n, label]) => (
              <div key={label}><dt>{label}</dt><dd>{n}</dd></div>
            ))}
          </dl>
          <p className="ocl-page__note">
            4,708 of the researchers are at 25 universities in Pakistan. Computer
            science faculty come from CSRankings (18,015); researchers in 25 other
            fields, from cardiology to economics, from OpenAlex (180,555). Grants
            come from funders in 29 countries and territories and the European
            Research Council, from NSF and NIH to HEC Pakistan, NSTC Taiwan and
            FAPESP Brazil.
          </p>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Choices that shaped it</h2>
          <dl className="ocl-ship__choices">
            <dt>Search by meaning</dt>
            <dd>
              A student rarely knows a field's words yet. Describing the work in
              plain language should be enough to find the people doing it.
            </dd>
            <dt>Grants as the hiring signal</dt>
            <dd>
              PhD students are usually paid as research or teaching assistants,
              and the professors with running grants are the ones hiring. Grants
              meant for new labs (NSF CAREER, ERC Starting, ARC DECRA, NIH R00)
              mark people recruiting their first students.
            </dd>
            <dt>Every grant readable inside the app</dt>
            <dd>
              Some funders' sites cannot be reached from Pakistan; nsf.gov is
              one. So each grant has its own page in Advisor Atlas, with its
              abstract, amount, dates and team.
            </dd>
            <dt>Calm by default</dt>
            <dd>
              A sentence first and numbers second, short lists with the rest one
              click away, and a signal as a single tag a student can act on
              (<i>New lab, funded</i>) rather than a table.
            </dd>
            <dt>Say what is missing</dt>
            <dd>
              “No grant on record” is shown as exactly that, and the gaps are
              stated where they matter, so an absence is not mistaken for a
              fact.
            </dd>
          </dl>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">What it is still missing</h2>
          <ul>
            <li>
              Researchers outside computer science come from OpenAlex and are
              chosen by citations. They are not a checked list of faculty.
            </li>
            <li>
              Germany has no national grant data yet; India's covers medical
              research only, and Korea's mostly the humanities and social
              sciences.
            </li>
            <li>
              A grant is linked to a person only when the name and the university
              both match, so some grants show no one even when the researcher is
              listed.
            </li>
            <li>
              Industry and university funding is not included, so “no grant” does
              not mean “no funding”.
            </li>
          </ul>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">What happens next</h2>
          <p>
            For its first month it is open to students, with two questions: did
            it help you find someone to write to, and was the funding information
            useful? What they say decides what is built next.
          </p>
          <p className="ocl-ship__actions">
            <a href={SITE} target="_blank" rel="noreferrer" className="ocl-ship__primary">Open advisoratlas.fyi ↗</a>
          </p>
        </section>

        <p className="ocl-page__foot ocl-ship__sources">
          Sources: CSRankings; DBLP (CC0); OpenAlex (CC0), including its awards for
          national funders (each funder's own terms apply); IPEDS, US Department of
          Education; NSF Award Search; NIH RePORTER; UKRI Gateway to Research, Open
          Government Licence v2.0; Australian Research Council; Royal Society Te
          Apārangi (Marsden Fund); Agence nationale de la recherche, ODbL; Swiss
          National Science Foundation; CORDIS, European Commission, and the ERC's
          lists of principal investigators; Japanese grants: created by Advisor
          Atlas, based on KAKEN (NII); NSERC Awards Data, contains information
          licensed under the Open Government Licence – Canada; NWOpen API (CC0); FWF
          Open API (CC0); Research Grants Council of Hong Kong project records
          (facts only); National Health and Medical Research Council (CC BY 4.0);
          FRIS, Flemish Government; Narodowe Centrum Nauki; AMED (Japan); Indian
          Council of Medical Research; Biblioteca Virtual da FAPESP; SweCRIS;
          Research Portal Denmark; National Research Foundation of Korea via
          data.go.kr; ISCIII and NSF Sri Lanka (facts and links only); campus
          locations © OpenStreetMap contributors (ODbL); scholarships from a
          curated list and the DAAD database. Map © Mapbox.
        </p>
      </div>
    </Layout>
  );
}
