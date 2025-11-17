import { splitStringsIntoSingleChars, decorateArrayForPegjs, TabularPegParser } from "@unified-latex/unified-latex-util-pegjs";
import { match } from "@unified-latex/unified-latex-util-match";
import { printRaw as printRaw$1 } from "@unified-latex/unified-latex-util-print-raw";
const macros = {};
const environments = {
  tabularx: { signature: "m o m", renderInfo: { alignContent: true } }
};
function createMatchers() {
  return {
    matchChar: (node, char) => match.string(node, char),
    isWhitespace: match.whitespace,
    isGroup: match.group
  };
}
function parseTabularSpec(ast) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = splitStringsIntoSingleChars(ast);
  ast = decorateArrayForPegjs([...ast]);
  return TabularPegParser.parse(ast, createMatchers());
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
      return `@{${printRaw$1(node.content)}}`;
    case "bang_divider":
      return `!{${printRaw$1(node.content)}}`;
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
          return `p{${printRaw$1(node.size)}}`;
        }
        if (node.baseline === "default") {
          return `m{${printRaw$1(node.size)}}`;
        }
        if (node.baseline === "bottom") {
          return `b{${printRaw$1(node.size)}}`;
        }
        return `w{${printRaw$1(node.baseline)}}{${printRaw$1(
          node.size
        )}}`;
      }
      break;
    case "decl_code":
      return printRaw$1(node.code);
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
export {
  environments,
  macros,
  parseTabularSpec,
  printRaw
};
//# sourceMappingURL=index.js.map
