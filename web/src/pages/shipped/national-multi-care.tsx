import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";

const SITE = "https://nmhnepalgunj.com/";
// Figures as of 14 October 2026, read from the hospital site's own catalogue.
// Nothing in THIS repo checks them — the gate that keeps prose and data in step
// lives in that project, not here — so they are a snapshot and will drift as
// the hospital adds clinicians and announcements.
const TALLY: [string, string][] = [
  ["35", "services"],
  ["12", "departments"],
  ["8", "clinicians"],
  ["3", "languages"],
  ["198", "pages"],
  ["20", "photographs"],
  ["9", "short films"],
  ["365", "interface strings, each translated twice"],
];

function Shot({ name, alt }: { name: string; alt: string }): ReactNode {
  const src = useBaseUrl(`/img/shipped/national-multi-care/${name}.jpg`);
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

export default function NationalMultiCare(): ReactNode {
  return (
    <Layout
      title="National Multi Care Hospital"
      description="The website for a multi-specialty hospital in Nepalgunj, Nepal, in English, Nepali and Hindi, built for people arriving on a phone and often in a hurry."
    >
      <div className="ocl-page ocl-ship">
        <p className="ocl-ship__back"><Link to="/shipped">Shipped</Link></p>
        <header className="ocl-ship__head">
          <h1 className="ocl-page__title">National Multi Care Hospital</h1>
          <p className="ocl-ship__lede">
            The website for a multi-specialty hospital in Nepalgunj, Nepal, in
            English, Nepali and Hindi. Almost everyone who opens it arrives on a
            phone, from a search result, and a fair number of them need
            something quickly.
          </p>
          <p className="ocl-ship__actions">
            <a href={SITE} target="_blank" rel="noreferrer" className="ocl-ship__primary">Open nmhnepalgunj.com ↗</a>
            <a href={`${SITE}ne/`} target="_blank" rel="noreferrer">In Nepali ↗</a>
            <a href={`${SITE}hi/`} target="_blank" rel="noreferrer">In Hindi ↗</a>
          </p>
          <dl className="ocl-ship__facts">
            <div><dt>Live since</dt><dd>16 September 2026</dd></div>
            <div><dt>Built in</dt><dd>Next.js, exported static</dd></div>
            <div><dt>Now</dt><dd>In use; the hospital is filling in what only it knows</dd></div>
          </dl>
        </header>

        <Shot name="home" alt="The homepage: the hospital's own frontage behind a headline, with the phone number and ambulance number pinned to the top of the screen." />

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Why it exists</h2>
          <p>
            A hospital website is read under conditions that most websites never
            see. Someone is in a corridor, or in a vehicle, or holding a referral
            slip they cannot fully read. They want three things: the number to
            call, whether the place is open, and whether anyone there treats what
            is wrong.
          </p>
          <p>
            Nepalgunj sits in the Terai, close to the Indian border, and the
            hospital draws from a district much larger than the city. The
            hospital asked for Nepali and Hindi alongside English, which tells
            you something about who walks in. They arrive on a phone, on mobile
            data they pay for by the megabyte.
          </p>
          <p>
            So the site is built around those conditions rather than around a
            brochure. Every page keeps the phone, WhatsApp and the ambulance
            within thumb reach. Every page exists in all three languages. The
            homepage, photographs and all, is 200KB.
          </p>
          <p>
            The harder part was not the building. It was deciding what the site
            is allowed to say.
          </p>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What a patient does with it</h2>
          <ol className="ocl-ship__steps">
            <Step n={1} title="Call, without reading anything" shot="mobile-bar"
              alt="A phone screen: a language strip under the hospital's name, and a bar of five buttons along the bottom — Call, WhatsApp, Ambulance, Find us, Help.">
              <p>
                The bar along the bottom is on every page, in every language.
                Call and Ambulance are <code>tel:</code> links that open the
                dialler; WhatsApp opens a chat with the message already written.
                None of it needs the page to be read, which matters when the
                person holding the phone cannot read the language it is in.
              </p>
            </Step>
            <Step n={2} title="Find the department, not the brochure" shot="services"
              alt="The services page: one collapsed row per department, each showing its name and how many services it holds.">
              <p>
                Thirty-five services across twelve departments, as one collapsed
                row each. It used to list them all open at once — ten screens of
                scrolling on a phone — with a separate jump list above that
                indexed the same twelve things. Now the index and the content are
                the same object, and eight departments fit in one screen.
              </p>
            </Step>
            <Step n={3} title="Find out when, and get told the truth" shot="service"
              alt="A service page for 24-hour emergency, with a panel stating it is open 24 hours every day.">
              <p>
                Each service says either <i>24 hours, every day</i> or{" "}
                <i>call to fix a time</i>. Nothing in between, because nothing in
                between is known. The hospital cannot guarantee fixed hours for
                visiting consultants, so the site does not print any.
              </p>
            </Step>
            <Step n={4} title="Ask a question without asking a model" shot="help"
              alt="A help panel listing eight common questions, such as 'I need help right now' and 'What should I bring with me?'">
              <p>
                Eight questions a patient actually asks, each resolving to one
                answer written in advance and translated twice. No model, no
                third-party script, no network call. The panel says so at the
                bottom: these are stored answers, not a medical consultation.
              </p>
            </Step>
          </ol>
          <div className="ocl-ship__gallery">
            <figure>
              <Shot name="mobile-nepali" alt="The services page in Nepali on a phone." />
              <figcaption>
                <b>Three languages, not one with a widget.</b> Every page is
                prerendered in English, Nepali and Hindi, each with its own URL
                and its own canonical.
              </figcaption>
            </figure>
            <figure>
              <Shot name="mobile-when" alt="An orthopaedic service page on a phone showing an 'arranged with reception' panel." />
              <figcaption>
                <b>By arrangement.</b> Where hours are not known, the page says
                to call and gives the number, rather than inventing a timetable.
              </figcaption>
            </figure>
            <figure>
              <Shot name="mobile-doctors" alt="The clinician directory on a phone, with photographs, titles and council registration numbers." />
              <figcaption>
                <b>Named, with registration numbers.</b> Eight clinicians, each
                with their Nepal Medical Council number. No credential appears
                that the hospital did not supply.
              </figcaption>
            </figure>
          </div>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What it holds</h2>
          <dl className="ocl-tally ocl-ship__tally">
            {TALLY.map(([n, label]) => (
              <div key={label}><dt>{label}</dt><dd>{n}</dd></div>
            ))}
          </dl>
          <p className="ocl-page__note">
            The twenty photographs are the hospital's own rooms and staff. Faces
            of patients and relatives are covered, not cropped around — the
            distinction matters, and is the subject of one of the choices below.
            On a phone the homepage is 14 requests and 200KB; no page contacts a
            third party on load.
          </p>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Choices that shaped it</h2>
          <dl className="ocl-ship__choices">
            <dt>Never print an hour nobody confirmed</dt>
            <dd>
              An earlier version generated a weekly timetable for each service.
              It looked authoritative and it was invented, and one generated row
              read <i>Saturday: Emergency only — Closed</i>. A patient reading
              that would not have travelled on a Saturday. The tables were
              deleted at source, with a comment in the data file explaining why
              they must not come back.
            </dd>

            <dt>Faces covered, not cropped around</dt>
            <dd>
              Several photographs contain patients and relatives. The temptation
              is to crop until no face is in frame, and one photograph shipped
              that way: the physiotherapy room reduced to carpet, a gait ladder
              and a traffic cone, with the room itself thrown away. Masking the
              faces keeps the room and makes the consent question moot rather
              than answered.
            </dd>

            <dt>Say nothing the hospital cannot back</dt>
            <dd>
              No accreditations, because none were supplied. No charges, because
              that decision is not ours. No <code>aggregateRating</code> in the
              structured data even though the Google listing carries 4.8 from 33
              reviews — those are Google's reviews, not the hospital's to
              re-declare. An absent section is a better state to sit in than a
              plausible-looking one.
            </dd>

            <dt>Someone else's data allowance is not free</dt>
            <dd>
              The framework prefetches every linked page that scrolls into view.
              On the homepage that was 826KB of speculative download, including
              the Nepali and Hindi copies of the page the visitor was already
              reading. The Google Maps embed on the contact page was another
              447KB across seventeen third-party requests, on every single visit,
              and marking it <code>loading="lazy"</code> did nothing because on a
              phone it sat inside the browser's preload margin. Prefetch is off
              and the map is behind one tap.
            </dd>

            <dt>Gates for the failures that look like success</dt>
            <dd>
              Nine checks run on every push, and most exist because something had
              already shipped while looking perfect. The worst: a canonical tag
              set once in the root layout propagated to every descendant, so 202
              pages told Google that the canonical version of themselves was the
              homepage — while the sitemap offered them as 204 separate URLs.
              Nothing about the site looked wrong. Others catch a page rendering
              in the wrong language, a missing or duplicated meta description,
              and prose counts drifting from the catalogue.
            </dd>
          </dl>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">What it is still missing</h2>
          <ul>
            <li>
              <b>Pre-visit instructions.</b> Nothing tells a patient to fast, or
              to bring a referral. It is the gap most likely to cost someone a
              wasted journey, and it cannot be guessed — an earlier attempt to
              derive it told ENT endoscopy patients to do bowel prep.
            </li>
            <li>
              Two departments are listed with services but no named consultant.
              They read as available by arrangement, which is accurate, but a
              department page with nobody on it is a thin page.
            </li>
            <li>
              The Health Library is empty. The publishing path works; there is
              nothing to publish yet.
            </li>
            <li>
              The hospital's name is still fragmented across the web — the older
              films and a Facebook URL carry a previous name, and an abandoned
              domain still resolves. Google's own summary hedged and called the
              hospital by both names at once. That, rather than anything on the
              site, is the real ceiling on being found.
            </li>
          </ul>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">What happens next</h2>
          <p>
            The engineering queue is empty. What is left is the part only the
            hospital can supply: the pre-visit instructions, whether charges may
            be published, and the first announcement. Everything is built to
            render only when that content exists, so the site is complete at
            every stage of being filled in rather than showing an empty shelf.
          </p>
          <p className="ocl-ship__actions">
            <a href={SITE} target="_blank" rel="noreferrer" className="ocl-ship__primary">Open nmhnepalgunj.com ↗</a>
          </p>
        </section>

        <p className="ocl-page__foot ocl-ship__sources">
          Built with Next.js as a static export, hosted on Netlify, with the
          catalogue of departments, services, clinicians and photographs held in
          typed data files rather than a CMS. Photographs and film are the
          hospital's own, published with its permission. Clinician names,
          qualifications and Nepal Medical Council registration numbers are as
          the hospital supplied them. Accessibility verified with axe-core across
          twelve routes at a phone viewport, WCAG 2.1 A and AA.
        </p>
      </div>
    </Layout>
  );
}
