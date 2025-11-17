"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilPegjs = require("@unified-latex/unified-latex-util-pegjs");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
function createMatchers() {
  return {
    isChar: (node, char) => unifiedLatexUtilMatch.match.string(node, char),
    isComma: (node) => unifiedLatexUtilMatch.match.string(node, ","),
    isEquals: (node) => unifiedLatexUtilMatch.match.string(node, "="),
    isWhitespace: (node) => unifiedLatexUtilMatch.match.whitespace(node),
    isParbreak: (node) => unifiedLatexUtilMatch.match.parbreak(node),
    isSameLineComment: (node) => unifiedLatexUtilMatch.match.comment(node) && node.sameline,
    isOwnLineComment: (node) => unifiedLatexUtilMatch.match.comment(node) && !node.sameline
  };
}
function parsePgfkeys(ast, options) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  const { allowParenGroups = false } = options || {};
  ast = unifiedLatexUtilPegjs.decorateArrayForPegjs([...ast]);
  return unifiedLatexUtilPegjs.PgfkeysPegParser.parse(ast, {
    ...createMatchers(),
    allowParenGroups
  });
}
function pgfkeysArgToObject(arg) {
  function parseFront(nodes) {
    return unifiedLatexUtilPrintRaw.printRaw(nodes);
  }
  function parseBack(nodes) {
    if (!nodes) {
      return [];
    }
    if (nodes.length === 1 && unifiedLatexUtilMatch.match.group(nodes[0])) {
      return nodes[0].content;
    }
    return nodes;
  }
  let nodeList;
  if (unifiedLatexUtilMatch.match.argument(arg)) {
    nodeList = arg.content;
  } else {
    nodeList = arg;
  }
  const parsedArgs = parsePgfkeys(nodeList);
  return Object.fromEntries(
    parsedArgs.filter((part) => part.itemParts).map((part) => [
      parseFront(part.itemParts[0]),
      parseBack(part.itemParts[1])
    ])
  );
}
exports.createMatchers = createMatchers;
exports.parsePgfkeys = parsePgfkeys;
exports.pgfkeysArgToObject = pgfkeysArgToObject;
//# sourceMappingURL=index.cjs.map
