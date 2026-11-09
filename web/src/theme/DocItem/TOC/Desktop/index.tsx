import Desktop from "@theme-original/DocItem/TOC/Desktop";
import type DesktopType from "@theme/DocItem/TOC/Desktop";
import type { WrapperProps } from "@docusaurus/types";
import RecordPanel from "@site/src/components/RecordPanel";
import type { ReactNode } from "react";

type Props = WrapperProps<typeof DesktopType>;

/**
 * The contents rail on a doc page, with the state of the record above it.
 *
 * Wrapping `@theme/TOC` instead looked equivalent and was not: the blog renders
 * a TOC too, and `RecordPanel` reads `useDoc()`, so three writing pages failed
 * static generation with a context error. This component only ever mounts
 * inside a doc.
 */
export default function DesktopWrapper(props: Props): ReactNode {
  return (
    <>
      <RecordPanel />
      <Desktop {...props} />
    </>
  );
}
