# Clinical Sectionizer
This package offers a component for tagging clinical section titles in docs. 

# This package is deprecated!
Development for `clinical_sectionizer` has been moved to [medSpaCy](https://github.com/medspacy/medspacy) and should now be installed as:

```bash
pip install medspacy
```

```python
# Option 1: Load with a medspacy pipeline
import medspacy
nlp = medspacy.load(enable=["sectionizer"])
print(nlp.pipe_names)

# Option 2: Manually add to a spaCy model
import spacy
from medspacy.section_detection import Sectionizer
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe(Sectionizer(nlp))
```
[<img src="https://github.com/medspacy/medspacy/raw/master/images/medspacy_logo.png" align="center">](https://github.com/medspacy/medspacy)

Please see the [medSpaCy](https://github.com/medspacy/medspacy) GitHub page for additional information and documentation.
