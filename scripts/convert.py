"""Convert entity annotation from Doccano format to spaCy v3
.spacy format."""

import srsly
import typer
import warnings
from pathlib import Path

import spacy
from spacy.tokens import Doc, DocBin
if not Doc.has_extension('name'):
    Doc.set_extension('name', default=None)
    
from sklearn.model_selection import train_test_split

def main(lang: str, input_path: Path, train_percent: int):
    raw = list(srsly.read_jsonl(input_path))
    if any([key not in raw[0].keys() for key in ['id', 'data', 'label']]):
        warnings.warn("Raw data is expected to be json lines with id, data, label keys.")
    else:
        train, _remains = train_test_split(raw, train_size=train_percent/100, random_state=0)
        dev, test = train_test_split(_remains, train_size=0.5, random_state=0)
        convert(lang, train, 'corpus/train.spacy')
        convert(lang, dev, 'corpus/dev.spacy')
        convert(lang, test, 'corpus/test.spacy')
    
    
def convert(lang: str, text_lines: list, output_path: str):
    nlp = spacy.blank(lang)
    db = DocBin()
    for line in text_lines:
        text = line['data']
        doc = nlp.make_doc(text)
        doc._.name = line['id']
        ents = []
        for start, end, label in line['label']:
            span = doc.char_span(start, end, label=label, alignment_mode="strict")
            if span is None:
                msg = f"Document: {line['id']}\nEntity [{start}, {end}, {label}] does not align with token boundaries.\nOriginal entity was '{doc.text[start:end]}'"
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
                msg += f"\nAttempting to set entity as '{span}'"
                warnings.warn(msg)
            ents.append(span)
        doc.ents = ents
        db.add(doc)
    db.to_disk(Path(output_path))


if __name__ == "__main__":
    typer.run(main)
