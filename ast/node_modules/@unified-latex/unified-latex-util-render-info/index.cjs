"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
function updateRenderInfo(node, renderInfo) {
  if (renderInfo != null) {
    node._renderInfo = { ...node._renderInfo || {}, ...renderInfo };
  }
  return node;
}
function trimRenderInfo(ast) {
  unifiedLatexUtilVisit.visit(ast, (node) => {
    delete node._renderInfo;
    delete node.position;
  });
  return ast;
}
exports.trimRenderInfo = trimRenderInfo;
exports.updateRenderInfo = updateRenderInfo;
//# sourceMappingURL=index.cjs.map
