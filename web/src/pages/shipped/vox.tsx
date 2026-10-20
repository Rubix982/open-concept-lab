import type { ReactNode } from "react";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";

const REPO = "https://github.com/Rubix982/vox";
// Read from the vox README and index.html as of 20 October 2026. Nothing here
// checks them against that repo, so they are a snapshot.
const TALLY: [string, string][] = [
  ["1", "HTML file, no build step"],
  ["2", "ways in: voice and image"],
  ["5", "built-in templates"],
  ["5", "shaping models, 0.5B to 3B"],
  ["2", "OCR engines"],
  ["60", "sessions kept"],
  ["0", "recordings, transcripts or images sent off the machine"],
];

function Shot({ name, alt }: { name: string; alt: string }): ReactNode {
  const src = useBaseUrl(`/img/shipped/vox/${name}.jpg`);
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

export default function Vox(): ReactNode {
  return (
    <Layout
      title="Vox"
      description="Speak a long instruction and get back a clean prompt for a language model, or pull the text out of an image. Everything runs locally in the browser."
    >
      <div className="ocl-page ocl-ship">
        <p className="ocl-ship__back"><Link to="/shipped">Shipped</Link></p>
        <header className="ocl-ship__head">
          <h1 className="ocl-page__title">Vox</h1>
          <p className="ocl-ship__lede">
            Speak the instruction, paste the prompt. Vox turns a spoken ramble
            into a clean, structured prompt for a language model, and pulls the
            text out of a screenshot or a photo. All of it runs on your own
            machine.
          </p>
          <p className="ocl-ship__actions">
            <a href={REPO} target="_blank" rel="noreferrer" className="ocl-ship__primary">Get Vox on GitHub ↗</a>
            <a href={`${REPO}/blob/main/samples.md`} target="_blank" rel="noreferrer">Test scripts ↗</a>
          </p>
          <dl className="ocl-ship__facts">
            <div><dt>In use since</dt><dd>2 August 2026</dd></div>
            <div><dt>Image tab since</dt><dd>31 August 2026</dd></div>
            <div><dt>Runs</dt><dd>In the browser, from <code>localhost</code></dd></div>
          </dl>
        </header>

        <Shot name="shape" alt="Vox: a spoken request about rate limiting on the left, full of 'um' and 'uh', and on the right the same request as a prompt with Goal, Context and Constraints headings." />

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Why it exists</h2>
          <p>
            The prompts that get good work out of a model are long. They name
            the files, the constraint that broke things last time, and what not
            to touch. Typing all that is slow, so people cut it short, and the
            model guesses at the rest.
          </p>
          <p>
            Saying it out loud is fast but messy. A raw transcript is full of
            filler and false starts, and it puts things in the order you thought
            of them, not the order a reader needs.
          </p>
          <p>
            Vox sits in between. You talk, Whisper writes it down, and a small
            local model sorts it into a prompt you can paste. What you dictate is
            often work in progress, so none of it is sent to a server to do
            this.
          </p>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What you do with it</h2>
          <ol className="ocl-ship__steps">
            <Step n={1} title="Talk" shot="capture"
              alt="The capture panel showing the waveform of a 50-second recording, above a transcript of 142 words.">
              <p>
                Press <code>Space</code> and speak. The waveform shows it is
                hearing you, and you can pause and resume within one take. When
                you stop, Whisper transcribes it on your machine. The transcript
                is editable, because Whisper gets library names wrong and you
                should fix them before anything else reads it.
              </p>
            </Step>
            <Step n={2} title="Pick a shape" shot="templates"
              alt="The template editor, with the Review brief template open showing its role, rules and reply format fields.">
              <p>
                A template says what the prompt should look like: plain cleanup,
                a coding task, a bug report, a review brief, a design question,
                or one you write. Each has a role, rules and a reply format, and
                you can edit all of them.
              </p>
            </Step>
            <Step n={3} title="Read it, then paste it" shot="formatted"
              alt="A shaped review brief shown as Markdown source above and rendered with Subject, Goals, Look at and Leave alone headings below.">
              <p>
                The prompt streams in as it is written. You can view it rendered
                or as Markdown source, and <i>Copy prompt</i> always copies the
                source. Vox also checks the output for its two known failure
                modes: placeholders it made up, and your template's rules
                repeated back as the answer. If it finds either, it tells you
                instead of passing the result off as good.
              </p>
            </Step>
          </ol>
          <div className="ocl-ship__gallery">
            <figure>
              <Shot name="models" alt="The shaping model menu: Llama 3.2 3B, Qwen2.5 1.5B, Llama 3.2 1B, Gemma 2 2B, and Qwen2.5 0.5B on CPU." />
              <figcaption>
                <b>A model that fits your machine.</b> With WebGPU you get
                Whisper large-v3-turbo and a 1.5B–3B shaper. Without it, both
                fall back to smaller models on the CPU. Slower, but nothing is
                switched off.
              </figcaption>
            </figure>
            <figure>
              <Shot name="ocr-darkmode" alt="A dark-mode code screenshot with a light panel beside it, one of the reference samples for the Image tab." />
              <figcaption>
                <b>The screenshot that used to come back empty.</b> A dark
                editor next to a light panel. With Tesseract's default threshold
                it yielded 0 characters; with a local threshold, 561 at 83%
                confidence.
              </figcaption>
            </figure>
          </div>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Pulling text out of an image</h2>
          <p>
            The second tab takes an image instead of your voice. It is for the
            times when copying by hand is the only other option: a screenshot of
            code, a forwarded chat image, a photo of a printed page. You can
            paste it, drop it in, choose a file, or grab a region of your screen.
          </p>
          <p>
            <b>Fast</b> uses Tesseract and is the right choice for anything
            shown on a screen. All of it ships with Vox, so it works with no
            network at all. When its confidence is under 60%, it says the text is
            probably unreliable. <b>Photo</b> uses Florence-2 on WebGPU and is
            for angled, real-world shots. It is a 357MB download the first time,
            so Vox never picks it for you. The text goes into its own editable
            box. From there you can copy it, or send it to the transcript and
            shape it like a spoken take.
          </p>
        </section>

        <section className="ocl-ship__section">
          <h2 className="ocl-page__sectionTitle">What it holds</h2>
          <dl className="ocl-tally ocl-ship__tally">
            {TALLY.map(([n, label]) => (
              <div key={label}><dt>{label}</dt><dd>{n}</dd></div>
            ))}
          </dl>
          <p className="ocl-page__note">
            Models download once from Hugging Face into browser storage. After
            that you can disconnect and everything still works. Sessions keep
            the transcript, the prompt, the template used, and for images the
            extracted text and a small thumbnail. The original image is not kept.
          </p>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Choices that shaped it</h2>
          <dl className="ocl-ship__choices">
            <dt>Instructions in the system message, the transcript alone</dt>
            <dd>
              Chat models treat the user message as the thing to work on. Put
              the rules there and a small model will politely "clean up" your
              rules and hand them back as the answer, and <code>---</code>{" "}
              separators don't stop it. So everything the template says goes in
              the system message and the user message is only the transcript.
              The rules are written about "the speaker", not "me", because rules
              in the first person read as content and get echoed back.
            </dd>

            <dt>No live preview, because it broke the one promise</dt>
            <dd>
              An early version showed words appearing as you spoke, using the
              browser's speech API. In Chrome that API streams your microphone to
              Google. It was removed. The waveform replaced it as the sign that
              Vox is listening.
            </dd>

            <dt>Small models need plain descriptions</dt>
            <dd>
              The built-in formats describe each field in words, not with{" "}
              <code>&lt;angle brackets&gt;</code> or <code>[square brackets]</code>,
              because small models copy those out as if they were the answer.
              Repetition penalties are off, since they push the model away from
              reusing your own words, which is exactly what a faithful rewrite
              should do.
            </dd>

            <dt>One setting that recovers dark screenshots</dt>
            <dd>
              Tesseract's default picks one brightness threshold for the whole
              image. A screenshot with a light panel and a dark one suits
              neither, and the engine returns nothing at all, silently. Switching
              to a local threshold took the dark-mode sample from 0 characters
              to 561 at 83% confidence.
            </dd>

            <dt>Losing a session is the worst outcome</dt>
            <dd>
              When browser storage fills, Vox drops thumbnails first, then the
              oldest sessions, until the newest one fits, and says what it did.
              If a private window blocks storage altogether, it tells you when it
              loads rather than on your first save.
            </dd>
          </dl>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">What it is still missing</h2>
          <ul>
            <li>
              <b>A hosted copy.</b> You run it yourself with one command. It
              must be opened from <code>localhost</code>, <code>https://</code>{" "}
              or a local file. From a bare IP address the browser hides the
              microphone and WebGPU without warning. Vox detects this and says
              so, but it can't fix it.
            </li>
            <li>
              Handwriting. Neither OCR engine reads it reliably. It is listed in
              the test samples as a known failure rather than hidden.
            </li>
            <li>
              Photo mode is not reliable for copying code character for
              character. Use Fast for that.
            </li>
            <li>
              It is pinned to transformers.js 3.0.2. Version 4 has an open bug
              that breaks Whisper on WebGPU in exactly the setup Vox uses, so the
              upgrade waits on that fix.
            </li>
          </ul>
        </section>

        <section className="ocl-ship__section ocl-ship__prose">
          <h2 className="ocl-page__sectionTitle">Try it</h2>
          <p>
            Clone the repository, run <code>python3 -m http.server 43869</code>{" "}
            in it, and open <code>http://localhost:43869</code> in Chrome or
            Edge. The repository includes test scripts: six dictations, each
            aimed at one way shaping can fail, and four images for the Image
            tab, with what a pass and a fail look like. The unit tests run in
            the page itself at <code>?test=1</code>.
          </p>
          <p className="ocl-ship__actions">
            <a href={REPO} target="_blank" rel="noreferrer" className="ocl-ship__primary">Get Vox on GitHub ↗</a>
          </p>
        </section>

        <p className="ocl-page__foot ocl-ship__sources">
          A single HTML file with no build step. Speech recognition is Whisper,
          run through <code>@huggingface/transformers</code> 3.0.2. Shaping runs
          through WebLLM on WebGPU, or transformers.js on the CPU. OCR is
          Tesseract, bundled in the repository, and Florence-2. Models are
          downloaded from Hugging Face's CDN; typefaces come from Google Fonts
          and fall back to system fonts offline.
        </p>
      </div>
    </Layout>
  );
}
