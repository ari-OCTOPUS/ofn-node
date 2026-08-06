import hmac, hashlib, json, time
from urllib.parse import parse_qsl, unquote

class InitDataError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

def _pairs(init_data):
    if not init_data:
        raise InitDataError('missing_init_data', 'Mini App باید از داخل تلگرام و از دکمه همین ربات باز شود.')
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    if not pairs:
        raise InitDataError('empty_init_data', 'initData خالی است.')
    got = pairs.get('hash', '')
    if not got:
        raise InitDataError('missing_hash', 'hash تلگرام در initData نیست.')
    return pairs, got

def _data_check_string(pairs, exclude_signature=False):
    items = []
    for k, v in pairs.items():
        if k == 'hash':
            continue
        if exclude_signature and k == 'signature':
            continue
        items.append(f'{k}={v}')
    return '\n'.join(sorted(items))

def validate(init_data, bot_token, max_age=86400):
    pairs, got = _pairs(init_data)
    if not bot_token:
        raise InitDataError('missing_bot_token', 'توکن ربات روی سرور تنظیم نشده است.')

    # Telegram official bot-token validation. Some recent launch modes also
    # include a third-party `signature`; for bot-token hash validation it must
    # not break older clients, so we try both canonical strings safely.
    key = hmac.new(b'WebAppData', bot_token.encode(), hashlib.sha256).digest()
    variants = [('std', _data_check_string(pairs, False))]
    if 'signature' in pairs:
        variants.append(('no_signature', _data_check_string(pairs, True)))

    ok = False
    used = None
    for name, s in variants:
        calc = hmac.new(key, s.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(calc, got):
            ok = True
            used = name
            break
    if not ok:
        raise InitDataError('bad_init_data', 'امضای تلگرام با این ربات نمی‌خواند. Mini App را از دکمه تازه همین ربات باز کن.')

    try:
        auth_date = int(pairs.get('auth_date', '0') or 0)
    except ValueError:
        raise InitDataError('bad_auth_date', 'auth_date تلگرام نامعتبر است.')
    if auth_date and time.time() - auth_date > max_age:
        raise InitDataError('expired_init_data', 'initData تلگرام منقضی شده؛ مینی‌اپ را ببند و دوباره از ربات باز کن.')

    user_raw = pairs.get('user', '{}')
    try:
        user = json.loads(user_raw)
    except Exception:
        user = json.loads(unquote(user_raw or '{}'))
    if not user.get('id'):
        raise InitDataError('missing_user', 'شناسه کاربر تلگرام در initData نیست.')
    user['_auth_variant'] = used
    user['_auth_age'] = int(time.time() - auth_date) if auth_date else None
    return user

def debug(init_data):
    try:
        pairs, got = _pairs(init_data)
        user = {}
        if pairs.get('user'):
            try:
                user = json.loads(pairs['user'])
            except Exception:
                user = {}
        return {
            'has_initData': True,
            'has_hash': bool(got),
            'keys': sorted([k for k in pairs.keys() if k != 'hash']),
            'user_id': str(user.get('id', '')),
            'auth_date': pairs.get('auth_date'),
            'has_signature': 'signature' in pairs,
            'len': len(init_data),
        }
    except InitDataError as e:
        return {'has_initData': bool(init_data), 'error_code': e.code, 'error': e.message, 'len': len(init_data or '')}
