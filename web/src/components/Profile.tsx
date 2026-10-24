import type { ReactNode } from "react";
import Link from "@docusaurus/Link";
import useBaseUrl from "@docusaurus/useBaseUrl";
import { usePluginData } from "@docusaurus/useGlobalData";
import type { LabData } from "@site/plugins/lab-data";

const EMAIL = "saifulislam84210@gmail.com";

/**
 * The cover banner, the portrait over its edge, and the details below — the
 * home page and /about open with the same card, so a visitor meets one person.
 */
export default function Profile({ on = "home" }: { on?: "home" | "about" }): ReactNode {
  const { writing, projects } = usePluginData("ocl-lab-data") as LabData;
  const banner = useBaseUrl("/img/art/home/banner.svg");
  const portrait = useBaseUrl("/img/about/portrait.jpg");
  return (
    <section className={`ocl-profile ocl-profile--${on}`} aria-label="Who runs this lab">
      <div className="ocl-profile__banner">
        <img
          src={banner}
          alt="A terminal showing this site build and pass its own design check, a shield with a tick, a padlock, servers under a cloud, and circuit traces along the bottom."
          decoding="async"
        />
      </div>
      <div className="ocl-profile__body">
        <img className="ocl-profile__avatar" src={portrait} alt="Saif Ul Islam" width={160} height={160} />
        <div className="ocl-profile__who">
          <p className="ocl-profile__name">Saif Ul Islam</p>
          <p className="ocl-profile__headline">
            Knowledge editing and interpretability in language models
          </p>
          <p className="ocl-profile__meta">
            Open Concept Lab <span aria-hidden="true">·</span> {writing.length} pieces of writing{" "}
            <span aria-hidden="true">·</span> {projects.length} projects
          </p>
        </div>
        <div className="ocl-profile__actions">
          {on === "home" ? (
            <Link className="ocl-profile__btn ocl-profile__btn--primary" to="/about">About me</Link>
          ) : (
            <a className="ocl-profile__btn ocl-profile__btn--primary" href={`mailto:${EMAIL}`}>Email me</a>
          )}
          <a className="ocl-profile__btn" href="https://www.linkedin.com/in/suislam" target="_blank" rel="noreferrer">LinkedIn ↗</a>
          <a className="ocl-profile__btn" href="https://github.com/Rubix982" target="_blank" rel="noreferrer">GitHub ↗</a>
        </div>
      </div>
    </section>
  );
}
