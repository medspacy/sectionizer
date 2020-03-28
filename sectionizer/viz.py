from spacy import displacy

def visualize_ent(doc, context=True, sections=True, jupyter=True, colors=None):
    # TODO: This should replace the cycontext visualizer
    """Create a NER-style visualization
    for section titles.
    """
    # Make sure that doc has the custom medSpaCy attributes registered
    if not hasattr(doc._, "context_graph"):
        context = False
    if not hasattr(doc._, "sections"):
        sections = False

    ents_data = []


    for target in doc.ents:
        ent_data = {"start": target.start_char, "end":  target.end_char, "label": target.label_.upper()}
        ents_data.append((ent_data, "ent"))

    if context:
        for modifier in doc._.context_graph.modifiers:
            ent_data = {"start": modifier.span.start_char, "end": modifier.span.end_char, "label": modifier.category}
            ents_data.append((ent_data, "modifier"))
    if sections:
        for (title, header, _) in doc._.sections:
            if title is None:
                continue
            ent_data = {"start": header.start_char, "end": header.end_char, "label": f"<< {title.upper()} >>"}
            ents_data.append((ent_data, "section"))

    ents_data = sorted(ents_data, key=lambda x: x[0]["start"])

    # If colors aren't defined, generate color mappings for each entity and modifier label
    # And set all section titles to a light gray
    if colors is None:
        labels = set()
        section_titles = set()
        for (ent_data, ent_type) in ents_data:
            if ent_type in ("ent", "modifier"):
                labels.add(ent_data["label"])
            elif ent_type == "section":
                section_titles.add(ent_data["label"])
        colors = _create_color_mapping(labels)
        for title in section_titles:
            colors[title] = "#dee0e3"
    ents_display_data, _ = zip(*ents_data)
    viz_data = [{"text": doc.text,
                "ents": ents_display_data,
                }]

    options = {"colors": colors,
              }
    return displacy.render(viz_data, style="ent", manual=True, options=options, jupyter=jupyter)

def _create_color_mapping(labels):
    mapping = {}
    color_cycle = _create_color_generator()
    for label in labels:
        if label not in mapping:
            mapping[label] = next(color_cycle)
    return mapping

def _create_color_generator():
    """Create a generator which will cycle through a list of default matplotlib colors"""
    from itertools import cycle
    colors = [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728',
              u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f', u'#bcbd22', u'#17becf']
    return cycle(colors)