"use strict";
const unifiedLatexBuilder = require("@unified-latex/unified-latex-builder");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilRenderInfo = require("@unified-latex/unified-latex-util-render-info");
const unifiedLatexUtilReplace = require("@unified-latex/unified-latex-util-replace");
const unifiedLatexUtilSplit = require("@unified-latex/unified-latex-util-split");
const unifiedLatexUtilTrim = require("@unified-latex/unified-latex-util-trim");
function cleanEnumerateBody(ast, itemName = "item") {
  let { segments, macros } = unifiedLatexUtilSplit.splitOnMacro(ast, itemName);
  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i];
    if (i === 0) {
      unifiedLatexUtilTrim.trimEnd(segment);
    } else {
      unifiedLatexUtilTrim.trim(segment);
    }
    if (segment.length > 0 && i > 0) {
      segment.unshift({ type: "whitespace" });
    }
  }
  let insertParbreakBefore = /* @__PURE__ */ new WeakSet();
  let body = macros.flatMap((node, i) => {
    var _a;
    const segment = segments[i + 1];
    const trailingComments = popTrailingComments(segment);
    node.args = node.args || [];
    node.args.push(unifiedLatexBuilder.arg(segment, { openMark: "", closeMark: "" }));
    unifiedLatexUtilRenderInfo.updateRenderInfo(node, { inParMode: true });
    if (i > 0 || ((_a = segments[0]) == null ? void 0 : _a.length) > 0) {
      insertParbreakBefore.add(node);
    }
    return [node, ...trailingComments];
  });
  body = body.flatMap(
    (node) => insertParbreakBefore.has(node) ? [{ type: "parbreak" }, node] : node
  );
  body.unshift(...segments[0]);
  for (let i = 0; i < body.length - 1; i++) {
    const node = body[i];
    const nextNode = body[i + 1];
    if (!unifiedLatexUtilMatch.match.parbreak(nextNode)) {
      continue;
    }
    if (unifiedLatexUtilMatch.match.comment(node)) {
      node.suffixParbreak = true;
    }
    if (unifiedLatexUtilMatch.match.macro(node) && node.args && node.args[node.args.length - 1].closeMark === "") {
      const args = node.args[node.args.length - 1].content;
      const lastArg = args[args.length - 1];
      if (unifiedLatexUtilMatch.match.comment(lastArg)) {
        lastArg.suffixParbreak = true;
      }
    }
  }
  return body;
}
function popTrailingComments(nodes) {
  let lastNodeIndex = unifiedLatexUtilReplace.lastSignificantNodeIndex(nodes, true);
  if (lastNodeIndex === nodes.length - 1 || lastNodeIndex == null && nodes.length === 0) {
    return [];
  }
  if (lastNodeIndex == null) {
    lastNodeIndex = -1;
  }
  return nodes.splice(lastNodeIndex + 1);
}
exports.cleanEnumerateBody = cleanEnumerateBody;
//# sourceMappingURL=enumerate-DSh8p1uS.cjs.map
