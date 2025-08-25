# Configuration settings for the content classification system

# Text normalization settings
NORMALIZATION_SETTINGS = {
    'preserve_case': True,
    'preserve_punctuation': True,
    'preserve_special_chars': ['€', '%'],
    'normalize_newlines': True,
    'collapse_whitespace': True
}

# Sentence splitting settings
SENTENCE_SPLIT_SETTINGS = {
    'sentence_endings': ['.', '!', '?'],
    'common_abbreviations': [
        # English abbreviations
        'dr', 'mr', 'mrs', 'ms', 'prof', 'inc', 'ltd', 'corp', 'co', 'etc', 'vs', 'e.g', 'i.e',
        'jr', 'sr', 'st', 'ave', 'blvd', 'dept', 'govt', 'min', 'max', 'approx', 'est',
        # Generic business/legal terms
        'gmbh', 'llc', 'plc', 'sa', 'bv', 'nv', 'ag', 'kg', 'oy', 'ab', 'as',
        # Common short forms
        'tel', 'fax', 'www', 'http', 'https', 'ftp', 'no', 'ref', 'fig', 'vol', 'ed',
        # Time/date abbreviations
        'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
        'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'am', 'pm'
    ],
    'avoid_split_patterns': [
        r'\d+\.\d+',  # Decimals
        r'\d+\s*%',   # Percentages
        r'\d+\.\s*talletus',  # Finnish: "1. talletus" 
        r'100\s*%'    # Specific pattern from docs
    ]
}

# LLM settings
LLM_SETTINGS = {
    'max_retries': 3,
    'retry_delay': 1,  # seconds
    'target_tokens_per_batch': 4000,
    'temperature': 0.0,
    'top_p': 1.0
}

# Heuristics patterns for Stage 2 candidate selection
HEURISTICS_PATTERNS = {
    'action_words': [
        # English action words
        'sign', 'signup', 'register', 'join', 'get', 'claim', 'grab', 'take', 'receive',
        'download', 'play', 'start', 'begin', 'try', 'test', 'experience', 'discover',
        'unlock', 'access', 'enter', 'visit', 'browse', 'explore', 'check', 'view',
        'trade', 'invest', 'deposit', 'withdraw', 'bet', 'wager', 'gamble',
        # Common CTA verbs
        'buy', 'purchase', 'order', 'subscribe', 'upgrade', 'contact', 'call', 'email',
        'book', 'reserve', 'schedule', 'apply', 'submit', 'send', 'share', 'follow',
        # Generic action indicators
        'click', 'tap', 'press', 'select', 'choose', 'pick', 'open', 'close', 'save'
    ],
    
    'disclaimer_indicators': [
        'terms', 'conditions', 'apply', 'subject to', 'restrictions', 'limitations',
        'minimum', 'maximum', 'required', 'eligible', 'qualification', 'criteria',
        'wagering', 'rollover', 'playthrough', 'valid', 'expires', 'expiry',
        'age', 'jurisdiction', 'country', 'region', 'location', 'residence',
        'void', 'prohibited', 'excluded', 'available', 'offer', 'promotion'
    ],
    
    'info_indicators': [
        'features', 'benefits', 'how', 'what', 'when', 'where', 'why', 'information',
        'details', 'specifications', 'description', 'overview', 'summary', 'guide',
        'tutorial', 'instructions', 'steps', 'process', 'method', 'system',
        'platform', 'technology', 'service', 'product', 'solution', 'tool',
        'analysis', 'research', 'study', 'report', 'data', 'statistics',
        'includes', 'contains', 'provides', 'offers', 'supports', 'enables'
    ],
    
    'promo_indicators': [
        'bonus', 'free', 'offer', 'deal', 'discount', 'save', 'special', 'exclusive',
        'limited', 'time', 'hurry', 'now', 'today', 'immediate', 'instant', 'fast',
        'best', 'top', 'premium', 'ultimate', 'amazing', 'incredible', 'fantastic',
        'welcome', 'new', 'first', 'deposit', 'match', 'double', 'triple',
        'win', 'prize', 'reward', 'gift', 'surprise', 'extra', 'additional',
        'promotion', 'campaign', 'event', 'contest', 'competition', 'tournament'
    ],
    
    'risk_indicators': [
        'risk', 'warning', 'caution', 'danger', 'loss', 'lose', 'liability',
        'responsible', 'addiction', 'problem', 'gambling', 'help', 'support',
        'age', 'limit', 'restrict', 'control', 'self-exclusion', 'cool-off',
        'deposit limit', 'loss limit', 'time limit', 'session limit',
        'regulated', 'license', 'authority', 'commission', 'compliance',
        'legal', 'lawful', 'jurisdiction', 'prohibited', 'forbidden',
        'terms', 'conditions', 'rules', 'policy', 'agreement', 'disclaimer'
    ]
}

# HTML rendering settings
HTML_SETTINGS = {
    'max_paragraph_sentences': 10,
    'preserve_headers': True,
    'preserve_lists': True,
    'preserve_tables': False,  # Tables are complex, disabled for now
    'css_inline': True,
    'include_legend': True
}

# Cache settings
CACHE_SETTINGS = {
    'max_stage1_entries': 10000,
    'max_stage2_entries': 5000,
    'session_only': True,  # Don't persist between sessions
    'version': 1
}