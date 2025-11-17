import * as Ast from '@unified-latex/unified-latex-types';

export declare function createMatchers(): {
    isChar: (node: Ast.Node, char: string) => node is Ast.String;
    isComma: (node: Ast.Node) => node is Ast.String;
    isEquals: (node: Ast.Node) => node is Ast.String;
    isWhitespace: (node: Ast.Node) => node is Ast.Whitespace;
    isParbreak: (node: Ast.Node) => node is Ast.Parbreak;
    isSameLineComment: (node: Ast.Node) => boolean | undefined;
    isOwnLineComment: (node: Ast.Node) => boolean;
};

export declare type Item = {
    itemParts?: Ast.Node[][];
    trailingComment: Ast.Comment | null;
    trailingComma?: boolean;
    leadingParbreak?: boolean;
};

/**
 * Parse the arguments of a Pgfkeys macro. The `ast`
 * is expected to be a comma separated list of `Item`s.
 * Each item can have 0 or more item parts, which are separated
 * by "=". If `itemPart` is undefined,
 *
 * If `options.allowParenGroups === true`, then commas that occur inside groups of parenthesis
 * will not be parsed as separators. This is useful for parsing tikz `\foreach` loops.
 */
export declare function parsePgfkeys(ast: Ast.Node[], options?: {
    allowParenGroups: boolean;
}): Item[];

/**
 * Parse `arg` as pgfkeys and return a JavaScript object with the results.
 * The keys will be normalized to strings and the values will be arrays of nodes.
 */
export declare function pgfkeysArgToObject(arg: Ast.Argument | Ast.Node[]): Record<string, Ast.Node[]>;

export { }
