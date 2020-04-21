from spacy.tokens import Doc, Token, Span
from spacy.matcher import Matcher, PhraseMatcher

# Filepath to default rules which are included in package
from os import path
from pathlib import Path

from ._utils import *

Doc.set_extension("sections", default=list(), force=True)
Doc.set_extension("section_titles", getter=get_section_titles, force=True)
Doc.set_extension("section_headers", getter=get_section_headers, force=True)
Doc.set_extension("section_spans", getter=get_section_spans, force=True)

Token.set_extension("section_span", default=None, force=True)
Token.set_extension("section_title", default=None, force=True)
Token.set_extension("section_header", default=None, force=True)

# Set span attributes to the attribute of the first token
# in case there is some overlap between a span and a new section header
Span.set_extension("section_span", getter=lambda x: x[0]._.section_span, force=True)
Span.set_extension("section_title", getter=lambda x: x[0]._.section_title, force=True)
Span.set_extension("section_header", getter=lambda x: x[0]._.section_header, force=True)

DEFAULT_RULES_FILEPATH = path.join(
    Path(__file__).resolve().parents[1], "resources", "spacy_section_patterns.jsonl"
)

DEFAULT_ATTRS = {
    "past_medical_history": {"is_historical": True},
    "sexual_and_social_history": {"is_historical": True},
    "family_history": {"is_family": True},
    "patient_instructions": {"is_hypothetical": True},
    "education": {"is_hypothetical": True},
    "allergy": {"is_hypothetical": True}
}

class Sectionizer:
    name = "sectionizer"

    def __init__(self, nlp, patterns="default", add_attrs=False, max_scope=None):
        self.nlp = nlp
        self.add_attrs = add_attrs
        self.matcher = Matcher(nlp.vocab)
        self.max_scope = max_scope
        self.phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        self.assertion_attributes_mapping = None
        self._patterns = []
        self._section_titles = set()

        if patterns is not None:
            if patterns == "default":
                import os
                if not os.path.exists(DEFAULT_RULES_FILEPATH):
                    raise FileNotFoundError("The expected location of the default patterns file cannot be found. Please either "
                                            "add patterns manually or add a jsonl file to the following location: ",
                                            DEFAULT_RULES_FILEPATH)
                self.add(self.load_patterns_from_jsonl(DEFAULT_RULES_FILEPATH))
            # If a list, add each of the patterns in the list
            elif isinstance(patterns, list):
                self.add(patterns)
            elif isinstance(patterns, str):
                import os
                assert os.path.exists(patterns)
                self.add(self.load_patterns_from_jsonl(patterns))

        if add_attrs is False:
            self.add_attrs = False
        elif add_attrs is True:
            self.assertion_attributes_mapping = DEFAULT_ATTRS
            self.register_default_attributes()
        elif isinstance(add_attrs, dict):
            # Check that each of the attributes being added has been set
            for modifier in add_attrs.keys():
                attr_dict = add_attrs[modifier]
                for attr_name, attr_value in attr_dict.items():
                    if not Span.has_extension(attr_name):
                        raise ValueError(
                            "Custom extension {0} has not been set. Call Span.set_extension."
                        )

            self.add_attrs = True
            self.assertion_attributes_mapping = add_attrs

        else:
            raise ValueError(
                "add_attrs must be either True (default), False, or a dictionary, not {0}".format(
                    add_attrs
                )
            )

    @property
    def patterns(self):
        return self._patterns

    @property
    def section_titles(self):
        return self._section_titles

    @classmethod
    def load_patterns_from_jsonl(self, filepath):

        import json
        patterns = []
        with open(filepath) as f:
            for line in f:
                if line.startswith("//"):
                    continue
                patterns.append(json.loads(line))

        return patterns

    def register_default_attributes(self):
        """Register the default values for the Span attributes defined in DEFAULT_ATTRS."""
        for attr_name in [
            "is_negated",
            "is_uncertain",
            "is_historical",
            "is_hypothetical",
            "is_family",
        ]:
            try:
                Span.set_extension(attr_name, default=False)
            except ValueError:  # Extension already set
                pass

    def add(self, patterns):
        """Add a list of patterns to the clinical_sectionizer. Each pattern should be a dictionary with
       two keys:
           'section': The normalized section name of the section, such as 'pmh'.
           'pattern': The spaCy pattern matching a span of text.
               Either a string for exact matching (case insensitive)
               or a list of dicts.

       Example:
       >>> patterns = [ \
           {"section_title": "past_medical_history", "pattern": "pmh"}\
           {"section_title": "past_medical_history", "pattern": [{"LOWER": "past", "OP": "?"}, \
               {"LOWER": "medical"}, \
               {"LOWER": "history"}]\
               },\
           {"section_title": "assessment_and_plan", "pattern": "a/p:"}\
           ]
       >>> clinical_sectionizer.add(patterns)
       """
        for pattern_dict in patterns:
            name = pattern_dict["section_title"]
            pattern = pattern_dict["pattern"]
            if isinstance(pattern, str):
                self.phrase_matcher.add(name, None, self.nlp.make_doc(pattern))
            else:
                self.matcher.add(name, [pattern])
            self._patterns.append(pattern_dict)
            self._section_titles.add(name)

    def set_assertion_attributes(self, ents):
        """Add Span-level attributes to entities based on which section they occur in.

        Args:
            edges: the edges to modify

        """
        for ent in ents:
            if ent._.section_title in self.assertion_attributes_mapping:
                attr_dict = self.assertion_attributes_mapping[ent._.section_title]
                for (attr_name, attr_value) in attr_dict.items():
                    setattr(ent._, attr_name, attr_value)


    def __call__(self, doc):
        matches = self.matcher(doc)
        matches += self.phrase_matcher(doc)
        matches = prune_overlapping_matches(matches)
        if len(matches) == 0:
            doc._.sections.append((None, None, doc[0:]))
            return doc

        first_match = matches[0]
        section_spans = []
        if first_match[1] != 0:
            section_spans.append((None, None, doc[0:first_match[1]]))
        for i, match in enumerate(matches):
            (match_id, start, end) = match
            section_header = doc[start:end]
            name = self.nlp.vocab.strings[match_id]
            # If this is the last match, it should include the rest of the doc
            if i == len(matches) - 1:
                if self.max_scope is None:
                    section_spans.append((name, section_header, doc[start:]))
                else:

                    section_spans.append((name, section_header, doc[start:end+self.max_scope]))
            # Otherwise, go until the next section header
            else:
                next_match = matches[i + 1]
                _, next_start, _ = next_match
                if self.max_scope is None:
                    section_spans.append((name, section_header, doc[start:next_start]))
                else:
                    section_spans.append((name, section_header, doc[start:end+self.max_scope]))

        for name, header, section in section_spans:
            doc._.sections.append((name, header, section))
            for token in section:
                token._.section_span = section
                token._.section_title = name
                token._.section_header = header

        # If it is specified to add assertion attributes,
        # iterate through the entities in doc and add them
        if self.add_attrs is True:
            self.set_assertion_attributes(doc.ents)
        return doc

def prune_overlapping_matches(matches, strategy="longest"):
    if strategy != "longest":
        raise NotImplementedError()

    # Make a copy and sort
    unpruned = sorted(matches, key=lambda x: (x[1], x[2]))
    pruned = []
    num_matches = len(matches)
    if num_matches == 0:
        return matches
    curr_match = unpruned.pop(0)

    while True:
        if len(unpruned) == 0:
            pruned.append(curr_match)
            break
        next_match = unpruned.pop(0)

        # Check if they overlap
        if overlaps(curr_match, next_match):
            # Choose the larger span
            longer_span = max(curr_match, next_match, key=lambda x: (x[2] - x[1]))
            pruned.append(longer_span)
            if len(unpruned) == 0:
                break
            curr_match = unpruned.pop(0)
        else:
            pruned.append(curr_match)
            curr_match = next_match
    # Recursive base point
    if len(pruned) == num_matches:
        return pruned
    # Recursive function call
    else:
        return prune_overlapping_matches(pruned)

def overlaps(a, b):
    if _span_overlaps(a, b) or _span_overlaps(b, a):
        return True
    return False

def _span_overlaps(a, b):
    _, a_start, a_end = a
    _, b_start, b_end = b
    if a_start >= b_start and a_start < b_end:
        return True
    if a_end > b_start and a_end <= b_end:
        return True
    return False

def matches_to_spans(doc, matches, set_label=True):
    spans = []
    for (rule_id, start, end) in matches:
        if set_label:
            label = doc.vocab.strings[rule_id]
        else:
            label = None
        spans.append(Span(doc, start=start, end=end, label=label))
    return spans

