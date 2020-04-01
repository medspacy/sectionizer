import pytest
import spacy

from clinical_sectionizer import Sectionizer

nlp = spacy.load("en_core_web_sm")

class TestSectionizer:
    def test_initiate(self):
        assert Sectionizer(nlp)

    def test_load_default_rules(self):
        sectionizer = Sectionizer(nlp, patterns="default")
        assert sectionizer.patterns

    def test_load_no_rules(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        assert sectionizer.patterns == []

    def test_add(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "section", "pattern": "my pattern"}])
        assert sectionizer.patterns

    def test_string_match(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        (section_title, header, section) = doc._.sections[0]
        assert section_title == "past_medical_history"
        assert header.text == "Past Medical History:"
        assert section.text == "Past Medical History: PE"

    def test_list_pattern_match(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": [{"LOWER": "past"},
                                                                              {"LOWER": "medical"},
                                                                              {"LOWER": "history"},
                                                                              {"LOWER": ":"},
                                                                              ]}])
        doc = nlp("Past Medical History: PE")
        sectionizer(doc)
        (section_title, header, section) = doc._.sections[0]
        assert section_title == "past_medical_history"
        assert header.text == "Past Medical History:"
        assert section.text == "Past Medical History: PE"

    def test_document_starts_no_header(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        doc = nlp("This is separate. Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 2
        (section_title, header, section_span) = doc._.sections[0]
        assert section_title is None
        assert header is None
        assert section_span.text == "This is separate."

        (section_title, header, section_span) = doc._.sections[1]
        assert section_title == "past_medical_history"
        assert header.text == "Past Medical History:"
        assert section_span.text == "Past Medical History: PE"