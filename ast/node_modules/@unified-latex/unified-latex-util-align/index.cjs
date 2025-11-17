"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilPegjs = require("@unified-latex/unified-latex-util-pegjs");
function createMatchers(rowSepMacros, colSep) {
  const isRowSep = unifiedLatexUtilMatch.match.createMacroMatcher(rowSepMacros);
  return {
    isRowSep,
    isColSep: (node) => colSep.some((sep) => unifiedLatexUtilMatch.match.string(node, sep)),
    isWhitespace: (node) => unifiedLatexUtilMatch.match.whitespace(node),
    isSameLineComment: (node) => unifiedLatexUtilMatch.match.comment(node) && node.sameline,
    isOwnLineComment: (node) => unifiedLatexUtilMatch.match.comment(node) && !node.sameline
  };
}
function parseAlignEnvironment(ast, colSep = ["&"], rowSepMacros = ["\\", "hline", "cr"]) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = unifiedLatexUtilPegjs.decorateArrayForPegjs([...ast]);
  return unifiedLatexUtilPegjs.AlignEnvironmentPegParser.parse(
    ast,
    createMatchers(rowSepMacros, colSep)
  );
}
exports.createMatchers = createMatchers;
exports.parseAlignEnvironment = parseAlignEnvironment;
//# sourceMappingURL=index.cjs.map
