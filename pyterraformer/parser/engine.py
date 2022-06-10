from lark import Lark, Transformer, v_args, Tree

from pyterraformer.parser.generics import (
    Comment,
    Variable,
    Interpolation,
    String,
    StringLit,
    DictLookup,
    PropertyLookup,
    TerraformConfig,
    Backend,
    Provider,
    BinaryTerm,
    Data,
    Expression,
    Conditional,
    BinaryOp,
    BinaryOperator,
    Output,
    Local,
    Parenthetical,
    LegacySplat,
    Block,
    File,
    Boolean,
    Merge,
    Concat,
    Types,
    Replace,
    ArrayLookup,
    GenericFunction,
    Symlink,
    ToSet,
)

# TODO: rewrite to comply with https://github.com/hashicorp/hcl2/blob/master/hcl/hclsyntax/spec.md

grammar = r"""
    start: (comment| item | symlink)*
    ?item: resource
    | object
    | module
    | provider
    | terraform
    | variable
    | locals
    | data
    | output
    | multiline_comment

    //TODO: in parsing - follow symlinks?
    symlink: "."+ "/" /[a-zA-Z_\-]+/ ".tf"

    resource: "resource" string_lit string_lit  "{" (sub_object | lifecycle | provider | split_subarray| comment) + "}"

    output: "output" string_lit "{"[( comment| sub_object)+] "}"

    module: "module" string_lit  "{"  (comment | sub_object | split_subarray)+ "}"

    lifecycle: "lifecycle"  "{" [sub_object ( sub_object)*] "}"

    // this exists without the = option as a perf optimization
    split_subarray: IDENTIFIER "{" [(comment|sub_object|split_subarray)+] "}"

    provider: "provider" (string_lit | IDENTIFIER)  "{" [(sub_object | split_subarray) ( sub_object| split_subarray)*]  "}"

    data: "data" string_lit string_lit "{" [(sub_object | split_subarray | comment) ( sub_object| split_subarray | comment)*] "}"

    metadata: "metadata" "{" [sub_object ( sub_object)*] "}"

    object: "object" string_lit "{" [sub_object ( sub_object)*] "}"

    locals: "locals" dict

    variable: "variable" (string_lit | IDENTIFIER) "{" (comment | variable_type_declaration| variable_default_declaration | variable_description)* "}"

    variable_type_declaration: ("type" | "\"type\"") "=" (types | ( "\""  TYPE"\"" ))
    variable_description: ("description" | "\"description\"") "=" (string_lit | heredoc_eof)
    variable_default_declaration: ("default"| "\"default\"") "=" (tuple | string_lit | boolean | dict | int_lit | heredoc_eof) 

    // terraform specific settings
    terraform: "terraform" "{" (backend | sub_object | split_subarray )* "}"

    backend: "backend" string_lit  "{" [sub_object ( sub_object)*] "}"

    // handling inside items
    // figure out how to handle comments better
    tuple: "["  [ comment* (string_lit| int_lit| dict| tuple | lookup | EMPTY_STRING )  ( "," comment*  (string_lit| int_lit| dict| tuple | lookup) )*] ","? comment?  "]" -> tuple

    // replace with expr_contents
    // figure out why dot identifiers are ever valid
    sub_object: (IDENTIFIER |string_lit | IDENTIFIER_WITH_DOT) "=" ( setsubtract | lookup | tuple | string_lit | file | toset | concat | merge | boolean | dict | int_lit | object_access |  conditional | heredoc_eof | IDENTIFIER | generic_function | list_comp) ","? comment?   -> sub_object

    // annoyingly repetitive
    dict_sub_object: (IDENTIFIER |string_lit | IDENTIFIER_WITH_DOT) ("=" | ":") ( setsubtract | lookup | tuple | string_lit | file | toset | concat | merge | boolean | dict | int_lit | object_access |  conditional | heredoc_eof | IDENTIFIER | generic_function | list_comp) ","? comment?   -> sub_object

    dict: "{" (comment | dict_sub_object )* "}"

    object_access: IDENTIFIER "." IDENTIFIER

    null: "null"

    IDENTIFIER_WITH_DOT : /[a-zA-Z_][a-zA-Z0-9_\\-\\.]*/
    STRING_TERM : STRING_CHARS _WHITESPACE
    IDENTIFIER : /[a-zA-Z_][a-zA-Z0-9_-]*/
    //string section
    string_lit: "\"" ( STRING_CHARS | interpolation)* "\""
    STRING_CHARS: /(?:(?!\${)([^"\\]|\\.))+/+ // any character except '"" unless inside a interpolation string

    EMPTY_STRING: "\"" "\""
    interpolation: "${" (expr_contents)+ "}"
    // simple_interpolation:  lookup (expr_contents)+
    lookup  : IDENTIFIER "." (IDENTIFIER | lookup | dict_lookup | array_lookup | legacy_splat)+
    // interpolation to prioritize match
    // TODO: determine better way
    dict_lookup: IDENTIFIER "[" ( string_lit | lookup | interpolation | conditional | dict_lookup | concat | toset | setsubtract| merge | replace | )  "]"
    array_lookup: IDENTIFIER "[" DECIMAL "]"
    file: "file" "(" string_lit ","? ")"
    replace: "replace" "(" (expr_contents)+ "," string_lit "," string_lit ")"
    concat: "concat" "("  (expr_contents | tuple )+  (","  (expr_contents | tuple))* ","? ")"
    merge: "merge" "("  (expr_contents | tuple )+  ","  (expr_contents | tuple)+  ")"
    coalesce: "coalesce" "(" (expr_contents | tuple )  (  "," expr_contents | tuple)+   ")"
    contains: "contains" "(" (expr_contents | tuple )  (  "," expr_contents | tuple)+   ")"
    flatten: "flatten" "(" tuple ")"
    toset: "toset" "(" expr_contents ")"
    setsubtract: "setsubtract" "(" (expr_contents | tuple) "," (expr_contents | tuple) ")"
    list_lit: "list" "("  ( (EMPTY_STRING)| expr_contents )+ ")"
    element: "element" "(" (expr_contents)+ "," int_lit ")"
    generic_function: IDENTIFIER "(" (expr_contents)+ ")"

    ?expr_contents : conditional
                | interpolation
                | lookup
                | array_lookup
                | dict_lookup
                | IDENTIFIER
                | boolean
                | int_lit
                | string_lit
                | file
                | replace
                | flatten
                | toset
                | coalesce
                | contains
                | setsubtract
                | concat
                | merge
                | element
                | generic_function
                | binary_operator
                | parenthetical
                | legacy_splat
                | list_lit
                | heredoc_eof
                | heredoc_template
                | heredoc_template_trim
                | list_comp
                | comment
                | tuple
                | null

    heredoc_eof: /<<-?(?P<delimiter>[^\s]+).*?(?P=delimiter)/s
    //heredoc_eof : ("<<EOF" | "<<-EOF" | "<<-EOT" | "<<EOT" | "<<-EOS" ) /((.|\n)(?!(EOF)|(EOT)|(EOS)))+/  /(.|\n){1}/ ("EOF" | "EOT" | "EOS" )
    // : ("<<" "-"? "EO" ("T" | "S" | "F"  ) ) /((.|\n)(?!(EOF)|(EOT)))+/  /(.|\n){1}/ ("EOF" | "EOT" | "EOS")
    heredoc_template : /<<(?P<heredoc>[a-zA-Z][a-zA-Z0-9._-]+)\n(?:.|\n)+?\n+\s*(?P=heredoc)/
    heredoc_template_trim : /<<-(?P<heredoc_trim>[a-zA-Z][a-zA-Z0-9._-]+)\n(?:.|\n)+?\n+\s*(?P=heredoc_trim)/     

    expression : (expr_contents)+ | operation | conditional

    // be smarter about handling this
    legacy_splat : IDENTIFIER "." "*" "."

    conditional : expression "?" expression ":" expression
    list_comp: "[" "for" expression  ("," expression)* "in" expression ":" expression "]"
    ?operation : unary_op | binary_op
    !unary_op : ("-" | "!") expr_contents
    binary_op : expression binary_term
    !binary_operator : "==" | "!=" | "<" | ">" | "<=" | ">=" | "-" | "*" | "/" | "%" | "&&" | "||" | "+" -> bool_token
    binary_term : binary_operator expression

    parenthetical : "(" (expr_contents)+ ")"

    !boolean : "true" | "false"
    DECIMAL: "0".."9"
    int_lit: "-"? DECIMAL+ 

    comment :   /#.*(\n|$)/ |  /\/\/.*\n/   

    multiline_comment: "/*" /((.|\n)(?!\*\/))+/  /(.|\n)/ "*/"

    //variables
    // map is valid and refers to map(any) https://www.terraform.io/docs/configuration/types.html#map-
    TYPE : "string" | "number" | "bool" | "map" | "list" | "any"
    // TODO: finish object and tuple
    types:(("tuple" | "set" | "map" | "object" | "list" ) "(" types ")") | TYPE

    %import common.WS_INLINE -> _WHITESPACE
    %import common.WS
    %ignore WS
"""


class ParseToObjects(Transformer):
    def __init__(self, visit_tokens, text):
        Transformer.__init__(self, visit_tokens)
        self.text = text

    def meta_to_text(self, meta):
        return self.text[meta.start_pos: meta.end_pos]

    def IDENTIFIER(self, args):
        return String(args.value)

    def STRING_CHARS(self, args):
        return String(args.value)

    def string_lit(self, args):
        return StringLit(args)

    def DECIMAL(self, args):
        return int(args.value)

    @v_args(meta=True)
    def resource(self, args, meta):
        type, name = args[0:2]
        out = RESOURCES_MAP[str(type).replace('"', "")](
            name, str(type), self.meta_to_text(meta), args[2:]
        )
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def module(self, args, meta):
        name = args[0]
        out = Module(self.meta_to_text(meta), name, args[1:])
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def variable(self, args, meta):
        name = args[0]
        args = args[1:]
        out = Variable(self.meta_to_text(meta), name, args)
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def provider(self, args, meta):
        name = args[0]
        out = Provider(name, self.meta_to_text(meta), args)
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def metadata(self, args, meta):
        out = TerraformConfig(self.meta_to_text(meta), args)
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def terraform(self, args, meta):
        out = TerraformConfig(self.meta_to_text(meta), args)
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def data(self, args, meta):
        type, name = args[0:2]
        out = Data(name, type, self.meta_to_text(meta), args[2:])
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def locals(self, args, meta):
        out = Local(self.meta_to_text(meta), args[0])
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def comment(self, args, meta):
        out = Comment(args[0].value)
        out.row_num = meta.start_pos
        return out

    @v_args(meta=True)
    def multiline_comment(self, args, meta):
        base = args[0].value
        if len(args) > 1:
            base += args[1].value
        out = Comment(base, True)
        out.row_num = meta.start_pos
        return out

    def backend(self, args):
        return Backend(args[0], args[1:])

    def output(self, args):
        return Output(args[0], args[1:])

    def tuple(self, args):
        return [*args]

    def sub_object(self, args):
        return args

    def variable_type_declaration(self, args):
        return ["_type", args[0]]

    def variable_default_declaration(self, args):
        return ["default", args[0]]

    def dict(self, args):
        return {key[0]: key[1] for key in args if not isinstance(key, Comment)}

    def interpolation(self, args):
        return Interpolation(args)

    def parenthetical(self, args):
        return Parenthetical(args)

    def legacy_splat(self, args):
        return LegacySplat(args)

    def lookup(self, args):
        base = args[0]
        return PropertyLookup(base, args[1:])

    def dict_lookup(self, args):
        return DictLookup(args[0], args[1:])

    def array_lookup(self, args):
        return ArrayLookup(args[0], args[1:])

    def expression(self, args):
        return Expression(args)

    def conditional(self, args):
        return Conditional(args)

    def binary_op(self, args):
        return BinaryOp(args)

    def binary_operator(self, args):
        return BinaryOperator(args)

    def file(self, args):
        return File(args)

    def types(self, args):
        return Types(args)

    def concat(self, args):
        return Concat(args)

    def merge(self, args):
        return Merge(args)

    def toset(self, args):
        return ToSet(args)

    def generic_function(self, args):
        return GenericFunction(args)

    def replace(self, args):
        return Replace(args)

    def int_lit(self, args):
        return int("".join([str(item) for item in args]))

    def binary_term(self, args):
        return BinaryTerm(args)

    def bool_token(self, args):
        return str(args[0].value)

    def split_subarray(self, args):
        name = args[0]
        return Block(name, args[1:])

    def boolean(self, args):
        type = args[0]
        return Boolean(type == "true")

    def symlink(self, args):
        return Symlink(args)


TERRAFORM_PARSER = Lark(grammar, start="start", propagate_positions=True)


def parse_text(text, print_flag: bool = False):
    if print_flag:
        parsed = TERRAFORM_PARSER.parse(text)
        for row in parsed.children:
            if isinstance(row, Tree):
                for item in row.children:
                    print(item)
            else:
                print(row)
    return ParseToObjects(visit_tokens=True, text=text).transform(TERRAFORM_PARSER.parse(text))
