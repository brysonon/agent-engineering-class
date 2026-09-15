ELEMENTS = ['Air', 'Water', 'Earth', 'Fire']

BENDER_SCHEMA = {
    'type': 'object',
    'properties': {
        'evidence': {
            'type': 'array',
            'description': (
                'Every phrase in the input that signals a bending personality '
                'trait. Quote the input verbatim. Empty array if the input '
                'contains no personality signal at all.'
            ),
            'items': {
                'type': 'object',
                'properties': {
                    'quote': {
                        'type': 'string',
                        'description': 'The phrase, copied verbatim from the input.',
                    },
                    'trait': {
                        'type': 'string',
                        'description': 'The personality trait the phrase demonstrates.',
                    },
                    'element': {
                        'type': 'string',
                        'description': 'The element whose trait list this phrase matches.',
                        'enum': ELEMENTS,
                    },
                },
                'required': ['quote', 'trait', 'element'],
                'additionalProperties': False,
            },
        },
        'element': {
            'type': 'string',
            'description': (
                'The classification. Avatar if the evidence spans more than one '
                'element. Unknown if there is no evidence to classify on.'
            ),
            'enum': [
                'Airbender',
                'Waterbender',
                'Earthbender',
                'Firebender',
                'Avatar',
                'Unknown',
            ],
        },
        'confidence': {
            'type': 'string',
            'description': 'How strongly the evidence supports the classification.',
            'enum': ['low', 'medium', 'high'],
        },
    },
    'required': ['evidence', 'element', 'confidence'],
    'additionalProperties': False,
}

CODE_SCHEMA = {
    'type': 'object',
    'properties': {
        'status': {
            'type': 'string',
            'description': (
                'ok if the request can be met under the prompt rules, '
                'cannot_comply if it cannot.'
            ),
            'enum': ['ok', 'cannot_comply'],
        },
        'reason': {
            'type': ['string', 'null'],
            'description': 'Why the request cannot be met. Null when status is ok.',
        },
        'imports_used': {
            'type': 'array',
            'description': (
                'Top-level module names imported by the code. Empty array if it '
                'imports nothing. Empty array when status is cannot_comply.'
            ),
            'items': {'type': 'string'},
        },
        'code': {
            'type': ['string', 'null'],
            'description': (
                'The complete Python source, with no Markdown fences. '
                'Null when status is cannot_comply.'
            ),
        },
        'assumptions': {
            'type': 'array',
            'description': 'Anything the request left unspecified that was decided here.',
            'items': {'type': 'string'},
        },
    },
    'required': ['status', 'reason', 'imports_used', 'code', 'assumptions'],
    'additionalProperties': False,
}

SCHEMAS = {
    'bender': BENDER_SCHEMA,
    'code': CODE_SCHEMA,
}
