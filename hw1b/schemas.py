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

SPEECH_SCHEMA = {
    'type': 'object',
    'properties': {
        'title': {
            'type': ['string', 'null'],
            'description': 'The title of the speech if it is stated in the text, otherwise null.',
        },
        'speaker': {
            'type': ['string', 'null'],
            'description': 'The name of the speaker if it is stated in the text, otherwise null.',
        },
        'key_takeaways': {
            'type': 'array',
            'description': (
                'The main points a listener should leave with, in the order the '
                'speech develops them. Between three and six of them.'
            ),
            'items': {
                'type': 'object',
                'properties': {
                    'quote': {
                        'type': 'string',
                        'description': (
                            'The sentence or two from the speech that best carries '
                            'this point, copied verbatim.'
                        ),
                    },
                    'takeaway': {
                        'type': 'string',
                        'description': 'The point itself, stated in one sentence.',
                    },
                },
                'required': ['quote', 'takeaway'],
                'additionalProperties': False,
            },
        },
        'speaker_emphasis': {
            'type': 'array',
            'description': (
                'Messages the speaker themselves treated as most important. Include '
                'a message only when the text shows a concrete signal of emphasis, '
                'not because it seems important in general.'
            ),
            'items': {
                'type': 'object',
                'properties': {
                    'quote': {
                        'type': 'string',
                        'description': 'The passage showing the emphasis, copied verbatim.',
                    },
                    'message': {
                        'type': 'string',
                        'description': 'What the speaker was emphasizing, in one sentence.',
                    },
                    'signal': {
                        'type': 'string',
                        'description': 'The observable reason this counts as emphasis.',
                        'enum': [
                            'repeated_throughout',
                            'stated_as_purpose',
                            'personal_experience',
                            'direct_invitation',
                            'closing_testimony',
                        ],
                    },
                },
                'required': ['quote', 'message', 'signal'],
                'additionalProperties': False,
            },
        },
        'divine_promises': {
            'type': 'array',
            'description': (
                'Every place the speaker describes a promise from the Lord. Include '
                'promises quoted from scripture, quoted from a prophet, or borne as '
                'a personal witness. Do not include general encouragement, advice, '
                'or opinions about what might happen.'
            ),
            'items': {
                'type': 'object',
                'properties': {
                    'quote': {
                        'type': 'string',
                        'description': 'The passage stating the promise, copied verbatim.',
                    },
                    'promise': {
                        'type': 'string',
                        'description': 'What the Lord is said to give, do, or guarantee.',
                    },
                    'condition': {
                        'type': ['string', 'null'],
                        'description': (
                            'What the promise is conditioned on. Null if it is stated '
                            'unconditionally.'
                        ),
                    },
                    'attribution': {
                        'type': 'string',
                        'description': 'How the speaker grounds the promise.',
                        'enum': [
                            'scripture',
                            'living_prophet',
                            'speaker_testimony',
                            'unattributed',
                        ],
                    },
                },
                'required': ['quote', 'promise', 'condition', 'attribution'],
                'additionalProperties': False,
            },
        },
        'one_sentence_summary': {
            'type': 'string',
            'description': 'The whole speech reduced to a single sentence.',
        },
    },
    'required': [
        'title',
        'speaker',
        'key_takeaways',
        'speaker_emphasis',
        'divine_promises',
        'one_sentence_summary',
    ],
    'additionalProperties': False,
}

SCHEMAS = {
    'bender': BENDER_SCHEMA,
    'code': CODE_SCHEMA,
    'speech': SPEECH_SCHEMA,
}
