"""Which token the coefficient is read at. Everything downstream depends on it."""

from __future__ import annotations

import pytest

from editreach.rome import SubjectNotInPrompt, subject_last_index

S = "Maurice de Vlaminck"


class _Tok:
    """One token per character, so an index is readable by eye."""

    def __call__(self, text):
        class _R:
            input_ids = list(range(len(text)))
        return _R()


@pytest.fixture
def tok() -> _Tok:
    return _Tok()


def test_the_default_is_the_first_mention_which_is_what_edit_slice_recorded(tok) -> None:
    """Behaviour is preserved deliberately: changing it would move recorded numbers."""
    p = f"{S} painted in Chatou. {S} was born in the country of"
    assert subject_last_index(tok, p, S) == len(S) - 1


def test_the_last_mention_can_be_asked_for(tok) -> None:
    p = f"{S} painted in Chatou. {S} was born in the country of"
    second = p.index(S, 1)
    assert subject_last_index(tok, p, S, occurrence=-1) == second + len(S) - 1


def test_the_two_differ_which_is_the_whole_point(tok) -> None:
    p = f"{S} painted in Chatou. {S} was born in the country of"
    assert subject_last_index(tok, p, S) != subject_last_index(tok, p, S, occurrence=-1)


def test_a_single_mention_is_unaffected_by_the_parameter(tok) -> None:
    p = f"{S} was born in the country of"
    assert subject_last_index(tok, p, S) == subject_last_index(tok, p, S, occurrence=-1)


def test_an_absent_subject_raises_instead_of_being_assigned_a_position(tok) -> None:
    """A far-field probe reaches its entity by description. It has no subject index."""
    p = "The head of government of the place where the painter of that river scene was born is"
    with pytest.raises(SubjectNotInPrompt, match="far-field"):
        subject_last_index(tok, p, S)


def test_an_occurrence_the_prompt_does_not_have_raises(tok) -> None:
    with pytest.raises(IndexError, match="occurrence 3 of 1"):
        subject_last_index(tok, f"{S} was born in", S, occurrence=3)
