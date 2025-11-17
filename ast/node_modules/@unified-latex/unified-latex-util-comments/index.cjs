"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilReplace = require("@unified-latex/unified-latex-util-replace");
function deleteComments(ast) {
  return unifiedLatexUtilReplace.replaceNode(ast, (node) => {
    if (!unifiedLatexUtilMatch.match.comment(node)) {
      return;
    }
    if (node.leadingWhitespace) {
      return { type: "whitespace" };
    }
    return null;
  });
}
exports.deleteComments = deleteComments;
//# sourceMappingURL=index.cjs.map
