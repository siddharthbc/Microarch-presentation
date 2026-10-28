"""Produce the concise v2 talk while retaining the paper figures and code.

Build integration runs after paper_visuals.apply on the original 60-slide source.
The CLI can instead trim a saved deck, preserving edits on retained slides.
"""
from pathlib import Path
import argparse
import json
import re

from pptx import Presentation
from pptx.enum.text import PP_ALIGN
import kit
from kit import tx, bullets, key, rgb, M, CW, SW, TOP

REMOVED = {
    3: 'Headline numbers repeated in the application results',
    4: 'Standalone roadmap',
    5: 'Section divider',
    11: 'Reverse-engineering preview repeated by the experiments',
    13: 'Section divider',
    18: 'Recency detail merged into the DevTLB structure notes',
    22: 'Activity-versus-data explanation merged into Prime–Idle–Probe notes',
    27: 'Channel comparison repeated by the mechanisms; active footprint retained in notes',
    28: 'Section divider',
    40: 'Section divider',
    46: 'Verdict section divider',
    47: 'Separate strengths slide condensed into the closing slide',
    48: 'Separate critique slide condensed into the closing slide',
    49: 'Separate proposed future-work slide removed',
    52: 'Descriptor diagram already shown in the main talk',
    56: 'Generic metric definitions removed from the appendix',
    57: 'Cross-paper comparison already shown in the main talk',
}
KEEP = [n for n in range(1, 61) if n not in REMOVED]
MAPPING = {old: new for new, old in enumerate(KEEP, 1)}
CLOSING_TITLE = 'Findings and limits'
CLOSING_SOURCE = 'Paper §§ IV–VII · evidence and evaluation scope'
PRESENTERS = 'Siddharth Banakar and Dinesh Samala'
PRESENTATION_DATE = '29 October 2026'


def set_text_preserving_style(shape, value):
    paragraph = shape.text_frame.paragraphs[0]
    if paragraph.runs:
        paragraph.runs[0].text = value
        for run in list(paragraph.runs)[1:]:
            run._r.getparent().remove(run._r)
    else:
        paragraph.text = value


def closing(slide):
    for shape in list(slide.shapes):
        shape._element.getparent().remove(shape._element)
    kit._DARK[id(slide)] = False
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb('white')
    tx(slide, 'Conclusion', M, .55, CW, .3, 12, 'accent', semi=True)
    tx(slide, CLOSING_TITLE, M, .9, CW, 1, 30, 'black', semi=True)
    bullets(slide, [
        ('Channels', 'DevTLB replacement timing + SWQ admission feedback'),
        ('Evidence', 'Controlled page / field / engine tests and four workload demonstrations'),
        ('Scope', 'Provisioned co-location; controlled datasets; residual mitigation leakage unmeasured'),
    ], y=TOP+.1, gap=1.2, size=24, body_size=19)
    key(slide, 'Shared accelerator state belongs in the isolation model.', y=6.2, size=22)
    tx(slide, CLOSING_SOURCE, M, 7.02, CW-1, .25, 10, 'gray3')
    tx(slide, '50', SW-M-.6, 7.02, .6, .25, 10, 'gray3', align=PP_ALIGN.RIGHT)
    slide.notes_slide.notes_text_frame.text = (
        'MAIN TALK | ~70 s\n\n'
        'The paper identifies two observable interfaces: completion timing exposes shared-engine '
        'DevTLB replacement, while submission feedback exposes shared-work-queue admission state. '
        'Controlled page, field, and engine experiments support the causal mechanism, followed by '
        'covert communication, website classification, keystroke event timing, and LLM configuration '
        'classification. Those results require provisioned DSA access and the relevant co-location. '
        'The classification datasets are controlled, and the mitigation experiment measures overhead '
        'without quantifying residual leakage. The keystroke event counts also have a reporting '
        'inconsistency, documented with the results and in the appendix. These scope limits qualify '
        'the reported accuracy; they do not negate the observed shared-state channels. '
        'The conclusion is that accelerator isolation must account for observable shared state as '
        'well as address permissions.\n\nSOURCE: '+CLOSING_SOURCE
    )


def apply_presentation_style(presentation):
    """Keep only page numbers in the footer and set the named presenters."""
    removed_headers = 0
    removed_footers = 0
    presenter_lines = 0
    for slide in presentation.slides:
        for shape in list(slide.shapes):
            if not shape.has_text_frame:
                continue
            text = shape.text.strip()
            y, x = shape.top/914400, shape.left/914400
            if text == 'The detective story' and y < 1:
                shape._element.getparent().remove(shape._element)
                removed_headers += 1
            elif y >= 7 and not (x > 11 and text.isdigit()):
                if text and text not in slide.notes_slide.notes_text_frame.text:
                    slide.notes_slide.notes_text_frame.text += '\n\nSOURCE REFERENCE: '+text
                shape._element.getparent().remove(shape._element)
                removed_footers += 1
            elif text.startswith('Presented by '):
                set_text_preserving_style(shape, 'Presented by '+PRESENTERS+' · '+PRESENTATION_DATE)
                presenter_lines += 1
    if presenter_lines != 1:
        raise ValueError(f'Expected one title-slide presenter line, found {presenter_lines}')
    presentation.core_properties.author = 'Siddharth Banakar; Dinesh Samala'
    return {'removed_headers':removed_headers, 'removed_footers':removed_footers,
            'presenters':PRESENTERS, 'presentation_date':PRESENTATION_DATE,
            'slide_count':len(presentation.slides)}


def apply(presentation, manifest):
    if len(presentation.slides) != 60 or len(manifest) != 60:
        raise ValueError('Expected the untrimmed 60-slide v2 deck and its matching manifest.')
    for old, fragment in {7:'descriptor-driven pipeline', 15:'The reveal',
                          21:'Weapon #1', 25:'The trap', 50:'Shared accelerator state'}.items():
        text='\n'.join(s.text for s in presentation.slides[old-1].shapes if s.has_text_frame)
        if fragment not in text:
            raise ValueError(f'Unexpected source slide {old}; refusing to trim another deck.')

    originals = [dict(row) for row in manifest]
    additions = {
        15: ('Cross-page detail (§IV-B): a multi-page transaction leaves only its final page '
             'translation in the relevant slot. The batch fetcher’s own descriptor reads and '
             'completion-record writes use a path that bypasses these slots; distinguish that '
             'batch-fetcher traffic from engine completion writes used by the NOOP probe.'),
        21: ('The probe measures coarse activity on the shared resource using the attacker’s own '
             'completion page. It does not read the victim’s address, packet, or typed character. '
             'Application labels come from repeated timing patterns and workload-specific inference.'),
        26: ('SWQ probing actively congests the shared queue used by the victim. Its signal avoids '
             'duration measurement, but the congestion window and queue drain still require control. '
             'Victim performance impact and detectability are not fully evaluated in the paper.'),
    }
    for old, note in additions.items():
        tf = presentation.slides[old-1].notes_slide.notes_text_frame
        tf.text += '\n\nRETAINED DETAIL:\n'+note

    closing(presentation.slides[49])
    manifest[49].update(title=CLOSING_TITLE, act='Conclusion', source=CLOSING_SOURCE, seconds=70)

    for old in KEEP:
        tf = presentation.slides[old-1].notes_slide.notes_text_frame
        text = tf.text
        text = text.replace('An assumption; I revisit it in the critique.',
                            'This is an assumption to carry through the results.')
        text = text.replace('I hold them to that in the critique.',
                            'Keep that scope when interpreting the reported accuracy.')
        text = text.replace('The gap, and the perfect transition to critique:',
                            'The remaining limitation:')
        def renumber(match):
            old_number = int(match.group(2))
            if old_number not in MAPPING:
                raise ValueError(f'Retained note refers to removed slide {old_number}')
            return match.group(1)+str(MAPPING[old_number])
        text = re.sub(r'(\b[Ss]lide\s+)(\d+)', renumber, text)
        tf.text = text

    for old in sorted(REMOVED, reverse=True):
        slide_id = presentation.slides._sldIdLst[old-1]
        presentation.part.drop_rel(slide_id.rId)
        presentation.slides._sldIdLst.remove(slide_id)

    kept_manifest=[]
    for new, old in enumerate(KEEP, 1):
        slide = presentation.slides[new-1]
        found=False
        for shape in slide.shapes:
            if shape.has_text_frame and shape.top/914400 >= 7 and shape.left/914400 > 11:
                set_text_preserving_style(shape, str(new))
                found=True
        if not found:
            raise ValueError(f'Cannot find slide-number footer on slide {new}')
        row=dict(manifest[old-1]); row['n']=new
        kept_manifest.append(row)
    manifest[:] = kept_manifest
    apply_presentation_style(presentation)

    return {
        'source_slides':60, 'slides':43, 'main':36, 'backup':7,
        'main_duration_seconds':sum(row['seconds'] for row in manifest if not row['backup']),
        'closing_slide':36,
        'mapping':[{'original':old,'current':new} for old,new in MAPPING.items()],
        'removed':[{'original':old,'title':originals[old-1]['title'],'reason':reason}
                   for old,reason in REMOVED.items()],
    }


def remap_visuals(changes):
    return [dict(change, slide=MAPPING[change['slide']]) for change in changes]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--style-only',action='store_true',
                        help='Update presenters, headers and footers in an already shortened deck.')
    args=parser.parse_args()
    manifest=json.loads((args.input.parent/'slide_manifest.json').read_text(encoding='utf-8'))
    visuals=json.loads((args.input.parent/'paper_visuals_manifest.json').read_text(encoding='utf-8'))
    p=Presentation(args.input)
    if args.style_only:
        if len(p.slides) != 43:
            raise ValueError('Expected the current 43-slide deck for the style-only update.')
        report=apply_presentation_style(p)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        p.save(args.output)
        for name,data in [('slide_manifest.json',manifest),('paper_visuals_manifest.json',visuals),
                          ('style_manifest.json',report)]:
            (args.output.parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report))
        return
    report=apply(p,manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    p.save(args.output)
    for name,data in [('slide_manifest.json',manifest),('trim_manifest.json',report),
                      ('paper_visuals_manifest.json',remap_visuals(visuals))]:
        (args.output.parent/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('slides','main','backup','main_duration_seconds')}))


if __name__ == '__main__':
    main()
