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
        (section_title, header, parent, section) = doc._.sections[0]
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
        (section_title, header, parent, section) = doc._.sections[0]
        assert section_title == "past_medical_history"
        assert header.text == "Past Medical History:"
        assert section.text == "Past Medical History: PE"

    def test_document_starts_no_header(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        doc = nlp("This is separate. Past Medical History: PE")
        sectionizer(doc)
        assert len(doc._.sections) == 2
        (section_title, header, parent, section_span) = doc._.sections[0]
        assert section_title is None
        assert header is None
        assert section_span.text == "This is separate."

        (section_title, header, parent, section_span) = doc._.sections[1]
        assert section_title == "past_medical_history"
        assert header.text == "Past Medical History:"
        assert section_span.text == "Past Medical History: PE"

    def test_max_scope_none(self):
        sectionizer = Sectionizer(nlp, patterns=None, max_scope=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        title, header, parent, section = doc._.sections[0]
        assert section[len(header)-1+2]._.section_title == "past_medical_history"
        assert section[len(header)-1+3]._.section_title == "past_medical_history"

    def test_max_scope(self):
        sectionizer = Sectionizer(nlp, patterns=None, max_scope=2)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        doc = nlp("Past Medical History: This is the sentence.")
        sectionizer(doc)
        title, header, parent, section = doc._.sections[0]
        assert section[len(header)-1+2]._.section_title == "past_medical_history"
        assert section[len(header)-1+3]._.section_title is None

    def test_start_line(self):
        sectionizer = Sectionizer(nlp, patterns=None, require_start_line=True)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        text = "\n\n Past Medical History: The patient has a Past Medical History:"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_end_line(self):
        sectionizer = Sectionizer(nlp, patterns=None, require_end_line=True)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"}])
        text = "\n\n Past Medical History:\n The patient has a Past Medical History: this"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2

    def test_parent_section(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"},
                        {"section_title": "explanation", "pattern": "Explanation:", "parents":["past_medical_history"]}])
        text = "Past Medical History: some other text Explanation: The patient has one"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2
        _,_,pmh_parent,_ = doc._.sections[0]
        _,_,explanation_parent,_  = doc._.sections[1]
        assert pmh_parent is None
        assert explanation_parent == "past_medical_history"

    def test_parent_section_multiple_candidates(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"},
                        {"section_title": "explanation", "pattern": "Explanation:", "parents":["past_medical_history", "allergies"]}])
        text = "Past Medical History: some other text. Explanation: The patient has one"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 2
        _,_,pmh_parent,_ = doc._.sections[0]
        _,_,explanation_parent,_  = doc._.sections[1]
        assert pmh_parent is None
        assert explanation_parent == "past_medical_history"

    def test_parent_section_candidate_after_section(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"},
                        {"section_title": "allergies", "pattern": "Allergies:"},
                        {"section_title": "explanation", "pattern": "Explanation:", "parents":["past_medical_history", "allergies"]}])
        text = "Past Medical History: some other text. Explanation: The patient has one. Allergies: peanuts"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 3
        _,_,pmh_parent,_ = doc._.sections[0]
        _,_,explanation_parent,_  = doc._.sections[1]
        _,_,allergies_parent,_ = doc._.sections[2]
        assert pmh_parent is None
        assert explanation_parent == "past_medical_history"
        assert allergies_parent is None

    def test_parent_section_duplicate_sections_different_parents(self):
        sectionizer = Sectionizer(nlp, patterns=None)
        sectionizer.add([{"section_title": "past_medical_history", "pattern": "Past Medical History:"},
                        {"section_title": "allergies", "pattern": "Allergies:"},
                        {"section_title": "explanation", "pattern": "Explanation:", "parents":["past_medical_history", "allergies"]}])
        text = "Past Medical History: some other text. Explanation: The patient has one. Allergies: peanuts Explanation: pt cannot eat peanuts"
        doc = nlp(text)
        sectionizer(doc)
        assert len(doc._.sections) == 4
        _,_,pmh_parent,_ = doc._.sections[0]
        _,_,explanation_parent,_  = doc._.sections[1]
        _,_,allergies_parent,_ = doc._.sections[2]
        _,_,explanation_parent2,_ = doc._.sections[3]
        assert pmh_parent is None
        assert explanation_parent == "past_medical_history"
        assert allergies_parent is None
        assert explanation_parent2 == "allergies"
