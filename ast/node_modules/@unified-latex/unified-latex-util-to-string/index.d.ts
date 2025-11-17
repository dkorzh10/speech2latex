import * as Ast from '@unified-latex/unified-latex-types';
import { Plugin as Plugin_2 } from 'unified';

export declare type PluginOptions = {
    pretty?: boolean;
    printWidth?: number;
    useTabs?: boolean;
    /**
     * If true, formatted code always ends with a newline character.
     */
    forceNewlineEnding?: boolean;
} | undefined;

/**
 * Convert an AST into a string, pretty-printing the result. If you want more control
 * over the formatting (e.g. spaces/tabs, etc.) use `unified().use(unifiedLatexStringCompiler, options)`
 * directly.
 */
declare function toString_2(ast: Ast.Ast): string;
export { toString_2 as toString }

/**
 * Unified complier plugin that prints a LaTeX AST as a string.
 */
export declare const unifiedLatexStringCompiler: Plugin_2<PluginOptions[], Ast.Root, string>;

export { }
