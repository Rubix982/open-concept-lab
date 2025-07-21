from typing import Dict, List
import questionary

from logger import logger


# Project Imports
from groups import AREA_GROUPS, CONFERENCE_MAP
from logger import logger


def research_area_selection() -> List[str]:
    selected_subareas: List[str] = []

    logger.info("🧭 Entering tree-style selection mode for research areas...")

    while True:
        top_level_choice = questionary.select(
            "🎓 Select a research group to explore (or finish selection):",
            choices=list(AREA_GROUPS.keys()) + ["✓ Finish selection"],
        ).ask()

        if top_level_choice == "✓ Finish selection":
            break

        subarea_group = AREA_GROUPS[top_level_choice]
        choices: List[questionary.Choice] = []

        # Keep track of a mapping from a 'select all' value to its children
        select_all_mapping: Dict[str, List[str]] = {}

        for label, meta in subarea_group.items():
            subarea_ids = meta["subareas"]
            select_all_token = f"<<ALL:{label}>>"
            select_all_mapping[select_all_token] = subarea_ids

            # Add "Select all in ..." option
            choices.append(
                questionary.Choice(
                    title=f"📂 All of [{label}] → {meta['name']}",
                    value=select_all_token,
                )
            )

            for subarea_acronym in subarea_ids:
                full_name = CONFERENCE_MAP.get(subarea_acronym, "Unknown Conference")
                title = f"[{label}] {subarea_acronym.upper()} → {full_name}"
                choices.append(questionary.Choice(title=title, value=subarea_acronym))

        selected = questionary.checkbox(
            f"📌 Select specific subareas in {top_level_choice}:\n",
            choices=choices,
        ).ask()

        if selected:
            logger.info(
                f"✅ You selected {len(selected)} subareas in {top_level_choice}. Selected: {selected}"
            )
            for val in selected:
                if val.startswith("<<ALL:"):
                    selected_subareas.extend(select_all_mapping[val])
                else:
                    selected_subareas.append(val)

    if not selected_subareas:
        logger.warning("⚠️  No subareas selected. You can restart the selection.")
    else:
        logger.info(f"✅ You selected {len(selected_subareas)} subareas.")

    return selected_subareas
