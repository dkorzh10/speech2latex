import * as Ast from '@unified-latex/unified-latex-types';

export declare function createMatchers(rowSepMacros: string[], colSep: string[]): {
    isRowSep: Ast.TypeGuard<Ast.Macro & {
        content: string;
    }>;
    isColSep: (node: Ast.Node) => boolean;
    isWhitespace: (node: Ast.Node) => node is Ast.Whitespace;
    isSameLineComment: (node: Ast.Node) => boolean | undefined;
    isOwnLineComment: (node: Ast.Node) => boolean;
};

/**
 * Parse the content of an align environment into an array of row objects.
 * Each row object looks like
 * ```
 *  {
 *    cells: [...],
 *    colSeps: [...],
 *    rowSep: ...,
 *    trailingComment: ...
 *  }
 * ```
 * `...` may be an ast node or `null`.
 *
 * @export
 * @param {[object]} ast
 * @param {string} [colSep=["&"]]
 * @param {string} [rowSepMacros=["\\", "hline", "cr"]]
 * @returns
 */
export declare function parseAlignEnvironment(ast: Ast.Node[], colSep?: string[], rowSepMacros?: string[]): Row[];

declare interface Row extends RowItems {
    rowSep: Ast.Macro | null;
    trailingComment: Ast.Comment | null;
}

declare interface RowItems {
    cells: Ast.Node[][];
    colSeps: Ast.String[];
}

export { }
