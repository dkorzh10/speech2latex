import { visit } from "@unified-latex/unified-latex-util-visit";
function updateRenderInfo(node, renderInfo) {
  if (renderInfo != null) {
    node._renderInfo = { ...node._renderInfo || {}, ...renderInfo };
  }
  return node;
}
function trimRenderInfo(ast) {
  visit(ast, (node) => {
    delete node._renderInfo;
    delete node.position;
  });
  return ast;
}
export {
  trimRenderInfo,
  updateRenderInfo
};
//# sourceMappingURL=index.js.map
