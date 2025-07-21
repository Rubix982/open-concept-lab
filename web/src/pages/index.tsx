import type { ReactNode } from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import Heading from "@theme/Heading";

import styles from "./index.module.css";

function HomepageHeader() {
  return (
    <header className={clsx("hero hero--primary", styles.heroBanner)}>
      <div className="container">
        <Heading as="h1" className="hero__title">
          open-concept-lab
        </Heading>
        <p className="hero__subtitle">
          An exploratory, long-term research lab documenting real-world
          DevSecOps incidents, high-signal writeups, and systems-level research
          across AI, Security, and Infrastructure.
        </p>
        <div className={styles.buttons}>
          <Link
            className="button button--secondary button--lg"
            to="/docs/category/devsecops"
          >
            🔐 Browse DevSecOps Scenarios
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/category/research"
          >
            📚 Explore Research & Tooling
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title={`Open Concept Lab — Research & DevSecOps`}
      description="A statically rendered lab of scenario-driven documentation, low-level experiments, and research tool tracking"
    >
      <HomepageHeader />
      <main>
        <section className="container margin-vert--lg">
          <div className="row">
            <div className="col col--6">
              <h2>🧪 What This Lab Is</h2>
              <p>
                This site is a living notebook of engineering practice, systems
                thinking, and research experiments. It's not a blog. It's not a
                course. It's the record of an engineer trying to build
                understanding from scratch.
              </p>
              <ul>
                <li>
                  🔍 Real-world incident scenarios and DevSecOps walkthroughs
                </li>
                <li>
                  ✍️ Thoughtful engineering reflection with logs, graphs, and
                  configs
                </li>
                <li>
                  📊 Tools to track and analyze NSF-funded research + faculty
                  networks
                </li>
                <li>
                  🧠 Project notes and replications of systems, AI, and HPC
                  concepts
                </li>
              </ul>
            </div>
            <div className="col col--6">
              <h2>🌱 Built With a Long-Term Mindset</h2>
              <p>
                Inspired by the best minds in DeepMind, OpenAI, Stanford, and
                ETH Zurich — this lab helps keep pace with cutting-edge research
                while documenting the rough edges of real infrastructure.
              </p>
              <ul>
                <li>
                  📁 Modular writeups with `README`, `reflection`, and
                  `extension`
                </li>
                <li>
                  📚 Research exploration pipelines like{" "}
                  <strong>rank-nsf-linker</strong>
                </li>
                <li>🔗 Code-backed learning, no fluff or filler</li>
              </ul>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
