import * as Ast from '@unified-latex/unified-latex-types';
import { PluginOptions } from '@unified-latex/unified-latex-util-to-string';
import { PluginOptions as PluginOptions_2 } from '@unified-latex/unified-latex-util-parse';
import { Processor } from 'unified';

/**
 * Use `unified()` to a string to an `Ast.Ast` and then return it. This function
 * will not print/pretty-print the `Ast.Ast` back to a string.
 */
export declare const processLatexToAstViaUnified: () => Processor<Ast.Root, Ast.Root, Ast.Root, void>;

/**
 * Use `unified()` to a string to an `Ast.Ast` and then pretty-print it.
 */
export declare const processLatexViaUnified: (options?: PluginOptions & PluginOptions_2) => Processor<Ast.Root, Ast.Root, Ast.Root, string>;

export { }
