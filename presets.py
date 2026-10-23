"""Caption Studio style presets.

Each preset changes three things at once, so videos genuinely differ:
  - rotation:    which caption modes cycle through the video
  - theme:       the text colors (base Roman, Nastaliq overlays, gold gradient)
  - background:  the canvas color
Plus giant_max (phrases up to this many words become one giant word)
and plain_over (phrases longer than this fall back to a plain subtitle block).
"""

DEFAULT_THEME = {
    'base': '#651311',           # Roman stack color (dark maroon red)
    'on_base_overlay': '#F0C070',  # Nastaliq over the base stack (gold)
    'on_gold_overlay': '#C4100C',  # Nastaliq over the gold stack (bright red)
    'gold_hi': '#F0C070', 'gold_lo': '#926A3A',   # gold gradient ends
    'line_ur': '#F0C070',        # line_pair Urdu color
    'line_ro': '#651311',        # line_pair Roman color (non-inverted)
    'only': '#F0C070',           # urdu_only line color
}


def theme(**over):
    t = dict(DEFAULT_THEME)
    t.update(over)
    return t


PRESETS = {
    'Classic Herr': {
        'desc': 'The original edit style: red + gold stacks and full-line pairs on maroon.',
        'background': '#290f05', 'theme': theme(),
        'rotation': ['stack_gold', 'line_pair', 'stack_red', 'urdu_only',
                     'stack_gold', 'line_pair', 'stack_red', 'stack_gold'],
        'giant_max': 1, 'plain_over': 8},
    'Mystic Gold': {
        'desc': 'Gold-dominant and calmer: gold stacks with Urdu-only breathing lines.',
        'background': '#1c0303',
        'theme': theme(gold_hi='#FFD98A', gold_lo='#A87C3F', line_ur='#FFD98A', only='#FFD98A'),
        'rotation': ['stack_gold', 'stack_gold', 'urdu_only', 'line_pair',
                     'stack_gold', 'urdu_only', 'stack_red', 'line_pair'],
        'giant_max': 1, 'plain_over': 9},
    'Crimson Stage': {
        'desc': 'Loud and dramatic: bright red stacks and giant two-word hits.',
        'background': '#20040a',
        'theme': theme(base='#C4100C', on_gold_overlay='#8F0D0A'),
        'rotation': ['stack_red', 'stack_gold', 'line_pair', 'stack_red',
                     'urdu_only', 'stack_gold', 'stack_red', 'line_pair'],
        'giant_max': 2, 'plain_over': 8},
    "Poet's Lines": {
        'desc': 'Elegant and literary: every phrase shown as a full poetic line pair.',
        'background': '#290f05', 'theme': theme(),
        'rotation': ['line_pair'] * 8,
        'giant_max': 0, 'plain_over': 12},
    'Giant Words': {
        'desc': 'Poster energy: short phrases explode into giant single words.',
        'background': '#170403', 'theme': theme(),
        'rotation': ['stack_gold', 'stack_red', 'stack_gold', 'line_pair',
                     'stack_red', 'stack_gold', 'urdu_only', 'stack_red'],
        'giant_max': 2, 'plain_over': 8},
    'Interlude Calm': {
        'desc': 'Slow and spacious: frequent gold Urdu-only lines on espresso brown.',
        'background': '#201004',
        'theme': theme(gold_hi='#F5CD85', gold_lo='#9C7434', only='#F5CD85', line_ur='#F5CD85'),
        'rotation': ['urdu_only', 'line_pair', 'stack_gold', 'urdu_only',
                     'line_pair', 'stack_red', 'urdu_only', 'line_pair'],
        'giant_max': 1, 'plain_over': 9},
    'Ivory & Gold': {
        'desc': 'Clean contrast: ivory-white Roman type with gold calligraphy on charcoal.',
        'background': '#101014',
        'theme': theme(base='#F4F0EF', on_base_overlay='#F0C070',
                       on_gold_overlay='#F4F0EF', line_ro='#F4F0EF'),
        'rotation': ['stack_red', 'line_pair', 'stack_gold', 'urdu_only',
                     'stack_red', 'line_pair', 'stack_gold', 'stack_red'],
        'giant_max': 1, 'plain_over': 8},
    'Marquee Mix': {
        'desc': 'Variety pack: artsy stacks mixed with clean readable subtitle blocks.',
        'background': '#290f05', 'theme': theme(),
        'rotation': ['stack_gold', 'plain', 'stack_red', 'line_pair',
                     'plain', 'stack_gold', 'urdu_only', 'stack_red'],
        'giant_max': 1, 'plain_over': 6},
    'Midnight Mono': {
        'desc': 'Moody monochrome: silver-gold and white on near-black, no red base.',
        'background': '#0b0b0d',
        'theme': theme(base='#3A3A40', on_gold_overlay='#F4F0EF',
                       gold_hi='#E8E4DA', gold_lo='#8A8578',
                       line_ur='#E8E4DA', only='#E8E4DA', line_ro='#3A3A40'),
        'rotation': ['stack_gold', 'line_pair', 'stack_red', 'stack_gold',
                     'line_pair', 'urdu_only', 'stack_gold', 'stack_red'],
        'giant_max': 1, 'plain_over': 8},
    'Royal Maroon': {
        'desc': 'Rich plum-maroon canvas, line pairs leading, deeper red and brighter gold.',
        'background': '#2b0714',
        'theme': theme(base='#8E1F2F', gold_hi='#FFCE7A', gold_lo='#9C6B30',
                       line_ur='#FFCE7A', only='#FFCE7A'),
        'rotation': ['line_pair', 'stack_gold', 'line_pair', 'stack_red',
                     'urdu_only', 'line_pair', 'stack_gold', 'stack_red'],
        'giant_max': 1, 'plain_over': 9},
}

DEFAULT_PRESET = 'Classic Herr'


def get_preset(name):
    return PRESETS.get(name, PRESETS[DEFAULT_PRESET])
