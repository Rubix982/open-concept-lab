from typing import TypedDict, Set


class Faculty:
    def __init__(
        self,
        name: str,
        dept: str,
        affiliation: str,
        homepage: str,
        matched_areas: list[str],
    ):
        self.name = name
        self.dept = dept
        self.affiliation = affiliation
        self.homepage = homepage
        self.matched_areas = matched_areas


class FacultyData(TypedDict):
    name: str
    affiliation: str
    dept: str
    homepage: str
    matched_areas: Set[str]
