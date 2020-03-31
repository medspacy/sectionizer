def get_section_titles(doc):
    return [title for (title, _, _) in doc._.sections]

def get_section_headers(doc):
    return [header for (_, header, _) in doc._.sections]

def get_section_spans(doc):
    return [span for (_, _, span) in doc._.sections]