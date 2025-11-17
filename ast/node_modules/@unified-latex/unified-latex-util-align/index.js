import { match } from "@unified-latex/unified-latex-util-match";
import { decorateArrayForPegjs, AlignEnvironmentPegParser } from "@unified-latex/unified-latex-util-pegjs";
function createMatchers(rowSepMacros, colSep) {
  const isRowSep = match.createMacroMatcher(rowSepMacros);
  return {
    isRowSep,
    isColSep: (node) => colSep.some((sep) => match.string(node, sep)),
    isWhitespace: (node) => match.whitespace(node),
    isSameLineComment: (node) => match.comment(node) && node.sameline,
    isOwnLineComment: (node) => match.comment(node) && !node.sameline
  };
}
function parseAlignEnvironment(ast, colSep = ["&"], rowSepMacros = ["\\", "hline", "cr"]) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = decorateArrayForPegjs([...ast]);
  return AlignEnvironmentPegParser.parse(
    ast,
    createMatchers(rowSepMacros, colSep)
  );
}
export {
  createMatchers,
  parseAlignEnvironment
};
//# sourceMappingURL=index.js.map
