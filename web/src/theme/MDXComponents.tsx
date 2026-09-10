import MDXComponents from "@docusaurus/theme-classic/lib/theme/MDXComponents";
import Figure from "@site/src/components/Figure";
import Cite from "@site/src/components/Cite";
import Claim from "@site/src/components/Claim";
import Embed from "@site/src/components/Embed";
import Aside from "@site/src/components/Aside";
import Projects from "@site/src/components/Projects";
import References from "@site/src/components/References";
import Status, { Notice } from "@site/src/components/Status";

/**
 * Available in every .md/.mdx file without an import.
 */
export default {
  ...MDXComponents,
  Figure,
  Cite,
  Claim,
  Embed,
  Aside,
  Projects,
  References,
  Status,
  Notice,
};
