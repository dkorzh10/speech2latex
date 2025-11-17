"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilPegjs = require("@unified-latex/unified-latex-util-pegjs");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
const macros = {};
const environments = {
  tabularx: { signature: "m o m", renderInfo: { alignContent: true } }
};
function createMatchers() {
  return {
    matchChar: (node, char) => unifiedLatexUtilMatch.match.string(node, char),
    isWhitespace: unifiedLatexUtilMatch.match.whitespace,
    isGroup: unifiedLatexUtilMatch.match.group
  };
}
function parseTabularSpec(ast) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = unifiedLatexUtilPegjs.splitStringsIntoSingleChars(ast);
  ast = unifiedLatexUtilPegjs.decorateArrayForPegjs([...ast]);
  return unifiedLatexUtilPegjs.TabularPegParser.parse(ast, createMatchers());
}
function printRaw(node, root = false) {
  if (typeof node === "string") {
    return node;
  }
  if (Array.isArray(node)) {
    const sepToken = root ? " " : "";
    return node.map((tok) => printRaw(tok)).join(sepToken);
  }
  switch (node.type) {
    case "vert_divider":
      return "|";
    case "at_divider":
      return `@{${unifiedLatexUtilPrintRaw.printRaw(node.content)}}`;
    case "bang_divider":
      return `!{${unifiedLatexUtilPrintRaw.printRaw(node.content)}}`;
    case "alignment":
      if (node.alignment === "left") {
        return "l";
      }
      if (node.alignment === "right") {
        return "r";
      }
      if (node.alignment === "center") {
        return "c";
      }
      if (node.alignment === "X") {
        return "X";
      }
      if (node.alignment === "parbox") {
        if (node.baseline === "top") {
          return `p{${unifiedLatexUtilPrintRaw.printRaw(node.size)}}`;
        }
        if (node.baseline === "default") {
          return `m{${unifiedLatexUtilPrintRaw.printRaw(node.size)}}`;
        }
        if (node.baseline === "bottom") {
          return `b{${unifiedLatexUtilPrintRaw.printRaw(node.size)}}`;
        }
        return `w{${unifiedLatexUtilPrintRaw.printRaw(node.baseline)}}{${unifiedLatexUtilPrintRaw.printRaw(
          node.size
        )}}`;
      }
      break;
    case "decl_code":
      return unifiedLatexUtilPrintRaw.printRaw(node.code);
    case "column":
      const end_code = node.before_end_code ? `<{${printRaw(node.before_end_code)}}` : "";
      const start_code = node.before_start_code ? `>{${printRaw(node.before_start_code)}}` : "";
      return [
        printRaw(node.pre_dividers),
        start_code,
        printRaw(node.alignment),
        end_code,
        printRaw(node.post_dividers)
      ].join("");
    default:
      console.warn(
        `Unknown node type "${node.type}" for node`,
        node
      );
      return "";
  }
  return "";
}
exports.environments = environments;
exports.macros = macros;
exports.parseTabularSpec = parseTabularSpec;
exports.printRaw = printRaw;
//# sourceMappingURL=index.cjs.map
