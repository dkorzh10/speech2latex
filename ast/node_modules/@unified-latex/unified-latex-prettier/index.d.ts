import * as Ast from '@unified-latex/unified-latex-types';
import { AstPath as AstPath_2 } from 'prettier';
import { Doc } from 'prettier';
import { Options } from 'prettier';
import { ParserOptions } from 'prettier';
import { Plugin as Plugin_2 } from 'prettier';

declare type AstPath = AstPath_2<Ast.Node | Ast.Argument>;

export declare const prettierPluginLatex: Plugin_2<Ast.Node>;

declare namespace PrettierTypes {
    export {
        Doc,
        Options,
        AstPath,
        PrintFunc,
        RecursivePrintFunc
    }
}

declare interface PrintFunc {
    (path: AstPath, options: ParserOptions, print: (path: AstPath) => Doc): Doc;
}

declare function printLatexAst(path: PrettierTypes.AstPath, options: PrettierTypes.Options & {
    referenceMap?: ReferenceMap;
}, print: PrettierTypes.RecursivePrintFunc): Doc;
export { printLatexAst }
export { printLatexAst as printer }

declare interface RecursivePrintFunc<U = any> {
    (path: U, index?: number, value?: any): Doc;
}

/**
 * Generate a data structure that can be queried
 * for the next/previous node. This allows for "peeking"
 * during the rendering process.
 *
 * @class ReferenceMap
 */
declare class ReferenceMap {
    ast: Ast.Ast;
    map: Map<Ast.Ast, {
        previous?: Ast.Ast;
        next?: Ast.Ast;
        renderCache?: any;
    }>;
    constructor(ast: Ast.Ast);
    /**
     * Associate render-specific data with this node. This data
     * will be overwritten if `setRenderCache` is called twice.
     *
     * @param {Ast.Ast} node
     * @param {*} data
     * @memberof ReferenceMap
     */
    setRenderCache(node: any, data: any): void;
    /**
     * Retrieve data associated with `node` via `setRenderCache`
     *
     * @param {Ast.Ast} node
     * @returns {(object | undefined)}
     * @memberof ReferenceMap
     */
    getRenderCache(node: any): object | any[] | undefined;
    getPreviousNode(node: Ast.Ast): Ast.Node | undefined;
    getNextNode(node: Ast.Ast): Ast.Node | undefined;
}

export { }
