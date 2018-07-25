import timeit

"""Based on
https://github.com/vlasovskikh/funcparserlib/blob/master/funcparserlib/tests/json.py.

"""

import re

from funcparserlib.lexer import make_tokenizer
from funcparserlib.lexer import Token
from funcparserlib.parser import some
from funcparserlib.parser import a
from funcparserlib.parser import maybe
from funcparserlib.parser import many
from funcparserlib.parser import skip
from funcparserlib.parser import forward_decl
from funcparserlib.parser import finished


REGEXPS = {
    'escaped': r'''
    \\                                  # Escape
    ((?P<standard>["\\/bfnrt])        # Standard escapes
    | (u(?P<unicode>[0-9A-Fa-f]{4})))   # uXXXX
    ''',
    'unescaped': r'''
    [^"\\]                              # Unescaped: avoid ["\\]
    '''
}


def tokenize(string):
    """str -> Sequence(Token)

    """

    specs = [
        ('Space', (r'[ \t\r\n]+',)),
        ('String', (r'"(%(unescaped)s | %(escaped)s)*"' % REGEXPS, re.VERBOSE)),
        ('Number', (r'''
            -?                  # Minus
            (0|([1-9][0-9]*))   # Int
            (\.[0-9]+)?         # Frac
            ([Ee][+-][0-9]+)?   # Exp
            ''', re.VERBOSE)),
        ('Op', (r'[{}\[\]\-,:]',)),
        ('Name', (r'[A-Za-z_][A-Za-z_0-9]*',)),
    ]

    useless = ['Space']

    t = make_tokenizer(specs)

    return [x for x in t(string) if x.type not in useless]


def parse_json(seq):
    """Sequence(Token) -> object

    """

    tokval = lambda x: x.value
    toktype = lambda t: some(lambda x: x.type == t) >> tokval
    op = lambda s: a(Token('Op', s)) >> tokval
    op_ = lambda s: skip(op(s))
    n = lambda s: a(Token('Name', s)) >> tokval

    def make_string(n):
        return n[1:-1]

    null = n('null')
    true = n('true')
    false = n('false')
    number = toktype('Number')
    string = toktype('String') >> make_string
    value = forward_decl()
    member = string + op_(':') + value
    object_ = (op_('{') +
               maybe(member + many(op_(',') + member)) +
               op_('}'))
    array = (op_('[') +
             maybe(value + many(op_(',') + value)) +
             op_(']'))
    value.define(null
                 | true
                 | false
                 | object_
                 | array
                 | number
                 | string)
    json_text = object_ | array
    json_file = json_text + skip(finished)

    return json_file.parse(seq)


def parse(json_string, iterations):
    def _parse():
        parse_json(tokenize(json_string))

    return timeit.timeit(_parse, number=iterations)
