import MDXComponents from "@docusaurus/theme-classic/lib/theme/MDXComponents";
import Figure from "@site/src/components/Figure";
import Cite from "@site/src/components/Cite";
import Evidence from "@site/src/components/Evidence";
import Anchor from "@site/src/components/Anchor";
import ThreadsPanel from "@site/src/components/LabLog";
import Margin from "@site/src/components/Margin";
import Claim from "@site/src/components/Claim";
import Embed from "@site/src/components/Embed";
import Aside from "@site/src/components/Aside";
import Projects from "@site/src/components/Projects";
import References from "@site/src/components/References";
import Status, { Notice } from "@site/src/components/Status";
import Claude from "@site/src/components/Claude";
import Gloss from "@site/src/components/Gloss";
import PageArt from "@site/src/components/PageArt";
import Profile from "@site/src/components/Profile";
import {
  Paper, PaperHead, Abstract, Contributions, Eq, Lead, Prov,
  Ledger, Finding, Runs, Run,
  Revisions, Rev, Readiness, Check, Data,
  Glance, Stat, Cards, Card, Threads, Thread,
} from "@site/src/components/Paper";
import { AboutRooms, AboutQuestions, AboutElsewhere, AboutCorrections } from "@site/src/components/About";

/**
 * Available in every .md/.mdx file without an import.
 */
export default {
  ...MDXComponents,
  Figure,
  Cite,
  Evidence,
  Anchor,
  ThreadsPanel,
  Margin,
  Claim,
  Embed,
  Aside,
  Projects,
  References,
  Status,
  Notice,
  Claude,
  Gloss,
  PageArt,
  Profile,
  AboutRooms,
  AboutQuestions,
  AboutElsewhere,
  AboutCorrections,
  Paper,
  PaperHead,
  Abstract,
  Contributions,
  Eq,
  Lead,
  Prov,
  Ledger,
  Finding,
  Runs,
  Run,
  Revisions,
  Rev,
  Readiness,
  Check,
  Data,
  Glance,
  Stat,
  Cards,
  Card,
  Threads,
  Thread,
};
