import { decorateArrayForPegjs, PgfkeysPegParser } from "@unified-latex/unified-latex-util-pegjs";
import { match } from "@unified-latex/unified-latex-util-match";
import { printRaw } from "@unified-latex/unified-latex-util-print-raw";
function createMatchers() {
  return {
    isChar: (node, char) => match.string(node, char),
    isComma: (node) => match.string(node, ","),
    isEquals: (node) => match.string(node, "="),
    isWhitespace: (node) => match.whitespace(node),
    isParbreak: (node) => match.parbreak(node),
    isSameLineComment: (node) => match.comment(node) && node.sameline,
    isOwnLineComment: (node) => match.comment(node) && !node.sameline
  };
}
function parsePgfkeys(ast, options) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  const { allowParenGroups = false } = options || {};
  ast = decorateArrayForPegjs([...ast]);
  return PgfkeysPegParser.parse(ast, {
    ...createMatchers(),
    allowParenGroups
  });
}
function pgfkeysArgToObject(arg) {
  function parseFront(nodes) {
    return printRaw(nodes);
  }
  function parseBack(nodes) {
    if (!nodes) {
      return [];
    }
    if (nodes.length === 1 && match.group(nodes[0])) {
      return nodes[0].content;
    }
    return nodes;
  }
  let nodeList;
  if (match.argument(arg)) {
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
export {
  createMatchers,
  parsePgfkeys,
  pgfkeysArgToObject
};
//# sourceMappingURL=index.js.map
