# Sectionizer
This package offers a spaCy component for tagging clinical section titles in docs. The `sectionizer` takes a list of 
patterns for section titles and searches for matches in a `doc`. When a section is found, it generates three outputs:
1. `section_name`: The normalized name of a section, a `string`
2. `section_header`: The span of the doc containing the header, a `Span`
3. `section`: The entire span of the doc containing the section, a `Span`

Calling `sectionizer(doc)` adds the 
following extensions to spaCy objects:

- `Doc.sections`: A list of 3-tuples of (`name`, `header`, `section`)
- `Token.section`: The `span` of the entire section which the token occurs in
- `Token.section_header`: The `span` of the section header of the section a token occurs in
- `Token.section_name`: The name of the section header defined by a pattern
- `Span` attributes corresponding `section`, `section_header`, and `section_name` to the first token in a span

# Example
```python
>>> text = """Family History:
    Diabetes
    
    Past Medical History:
    Pneumonia
    
    Assessment and Plan:
    Atrial fibrillation. There is no evidence of pneumonia.
    """
>>> import spacy
>>> nlp = spacy.load(...) # Load a model which will match clinical concepts

>>> from sectionizer import Sectionizer
>>> sectionizer = nlp.add_pipe(Sectionizer(nlp))


>>> section_patterns = [
        {"section_name": "family_history", "pattern": "Family History:"},
        {"section_name": "past_medical_history", 
            "pattern": [
                {"LOWER": "past", "OP": "?"}, 
                {"LOWER": "medical"},
                {"LOWER": "history"}, 
                {"LOWER": ":"},
            ]
            
        },
        {"section_name": "assessment_and_plan", "pattern": "Assessment and Plan:"},
    ]
>>> sectionizer.add(section_patterns)

>>> nlp.add_pipe(sectionizer)
>>> doc = nlp(text)
>>> print(nlp.ents)
(Diabetes, Pneumonia, Atrial fibrillation, pneumonia)


>>> for (section_name, section_header, section) in doc._.sections:
        print(section_name, section_header, section, sep="\n")

family_history
Family History:
Family History:
Diabetes

past_medical_history
Past Medical History:
Past Medical History:
Pneumonia

assessment_and_plan
Assessment and Plan:
Assessment and Plan:
Atrial fibrillation. There is no evidence of pneumonia.

>>> for ent in doc.ents:
        print(ent, ent._.section_name)
    
Diabetes family_history
Pneumonia past_medical_history
Atrial fibrillation assessment_and_plan
pneumonia assessment_and_plan
```

Using cycontext, you can also use a visualizer which shows section headers, along with any extracted entities and 
optionally cycontext modifiers, in an NER-style visualization.
```python
from cycontext.viz import visualize_ent
visualize_ent(doc, sections=True, context=False)
``` 
<p align="center"><img width="50%" height="50%" src="img/viz_ent.png" /></p>
