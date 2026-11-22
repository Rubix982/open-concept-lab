import ComponentTypes from "@theme-original/NavbarItem/ComponentTypes";
import MakingMenu from "@site/src/components/MakingMenu";

// The theme's navbar item types, plus the Making menu (type "custom-making" in docusaurus.config.ts).
export default {
  ...ComponentTypes,
  "custom-making": MakingMenu,
};
