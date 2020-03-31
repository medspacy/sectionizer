

class TextSectionizer:
    def __init__(self):
        raise NotImplementedError()
        self.sections = set()
        self.patterns = {}

    def add(self, patterns):
        for sect_patterns in patterns:
            name = sect_patterns["section"]
            self.sections.add(name)
            self.patterns.setdefault(name, list())
            self.patterns[name] += sect_patterns["patterns"]

    def extract_sections(self, text):
        matches = []
        for name, sect_patterns in self.patterns.items():
            for pattern in sect_patterns:
                sect_matches = list(pattern.finditer(text))
                for match in sect_matches:
                    matches.append((name, match))
        if len(matches) == 0:
            return [(None, text)]

        matches = sorted(matches, key=lambda x: (x[1].start(), 0 - x[1].end()))
        matches = self._dedup_matches(matches)

        sections = []
        if matches[0][1].start() != 0:
            sections.append(("UNK", text[:matches[0][1].start()]))
        for i, (name, match) in enumerate(matches):
            if i == len(matches) - 1:
                sections.append((name, text[match.start():]))
            else:
                next_match = matches[i + 1][1]
                sections.append((name, text[match.start():next_match.start()]))

        return sections

    def _dedup_matches(self, matches):
        deduped = []
        # TODO: Make this smarter
        deduped.append(matches[0])
        for i, match in enumerate(matches[1:], start=1):
            if not self._overlaps(deduped[-1], match):
                deduped.append(match)
        return deduped

    def _overlaps(self, a, b):
        (_, a) = a
        (_, b) = b
        if a.start() <= b.start() < a.end():
            return True
        if b.start() <= a.start() < b.end():
            return True