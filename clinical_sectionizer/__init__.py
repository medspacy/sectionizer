import warnings
warnings.simplefilter('once', DeprecationWarning)
warnings.warn("clinical_sectionizer is now *deprecated*. Please use medspacy.section_detection instead: `pip install medspacy`", RuntimeWarning)

from .sectionizer import Sectionizer
from .text_sectionizer import TextSectionizer

from ._version import __version__

__all__ = ["Sectionizer", "TextSectionizer"]
