import { match } from "@unified-latex/unified-latex-util-match";
import { replaceNode } from "@unified-latex/unified-latex-util-replace";
function deleteComments(ast) {
  return replaceNode(ast, (node) => {
    if (!match.comment(node)) {
      return;
    }
    if (node.leadingWhitespace) {
      return { type: "whitespace" };
    }
    return null;
  });
}
export {
  deleteComments
};
//# sourceMappingURL=index.js.map
