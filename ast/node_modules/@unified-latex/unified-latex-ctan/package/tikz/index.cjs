"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const parser = require("../../parser-9Q3EtimU.cjs");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
const unifiedLatexUtilTrim = require("@unified-latex/unified-latex-util-trim");
function printRaw(node, root = false) {
  if (typeof node === "string") {
    return node;
  }
  if (Array.isArray(node)) {
    const sepToken = root ? " " : "";
    const printed = [];
    for (let i = 0; i < node.length; i++) {
      const tok = node[i];
      const prevTok = node[i - 1];
      if (!prevTok) {
        printed.push(printRaw(tok));
        continue;
      }
      if (prevTok.type === "comment") {
        printed.push(printRaw(tok));
        continue;
      }
      if (tok.type !== "comment") {
        printed.push(sepToken);
      }
      printed.push(printRaw(tok));
    }
    return printed.join("");
  }
  const type = node.type;
  switch (type) {
    case "path_spec":
      return printRaw(node.content, root = true);
    case "coordinate":
      return `${unifiedLatexUtilPrintRaw.printRaw(node.prefix)}(${unifiedLatexUtilPrintRaw.printRaw(
        node.content
      )})`;
    case "operation":
      return unifiedLatexUtilPrintRaw.printRaw(node.content);
    case "comment":
      return unifiedLatexUtilPrintRaw.printRaw(node);
    case "line_to":
      return node.command;
    case "curve_to": {
      const comments = node.comments.map((c) => unifiedLatexUtilPrintRaw.printRaw({ ...c, leadingWhitespace: false })).join("");
      if (node.controls.length === 1) {
        return `${comments}.. controls ${printRaw(
          node.controls[0]
        )} ..`;
      } else {
        return `${comments}.. controls ${printRaw(
          node.controls[0]
        )} and ${printRaw(node.controls[1])} ..`;
      }
    }
    case "unknown":
      return unifiedLatexUtilPrintRaw.printRaw(node.content);
    case "square_brace_group":
      return `[${unifiedLatexUtilPrintRaw.printRaw(node.content)}]`;
    case "foreach": {
      const comments = node.comments.map((c) => unifiedLatexUtilPrintRaw.printRaw({ ...c, leadingWhitespace: false })).join("");
      let options = "";
      if (node.options) {
        options = ` [${unifiedLatexUtilPrintRaw.printRaw(node.options)}]`;
      }
      const start = unifiedLatexUtilPrintRaw.printRaw(node.start);
      const variables = [...node.variables];
      unifiedLatexUtilTrim.trim(variables);
      let printedVariables = unifiedLatexUtilPrintRaw.printRaw(variables);
      if (printedVariables.length > 0) {
        printedVariables = " " + printedVariables;
      }
      const command = node.command.type === "foreach" ? printRaw(node.command) : unifiedLatexUtilPrintRaw.printRaw(node.command);
      return `${comments}${start}${printedVariables}${options} in ${unifiedLatexUtilPrintRaw.printRaw(
        node.list
      )} ${command}`;
    }
    case "svg_operation": {
      const comments = node.comments.map((c) => unifiedLatexUtilPrintRaw.printRaw({ ...c, leadingWhitespace: false })).join("");
      let options = "";
      if (node.options) {
        options = `[${unifiedLatexUtilPrintRaw.printRaw(node.options)}]`;
      }
      return `${comments}svg${options} ${unifiedLatexUtilPrintRaw.printRaw(node.content)}`;
    }
    case "animation": {
      const comments = node.comments.map((c) => unifiedLatexUtilPrintRaw.printRaw({ ...c, leadingWhitespace: false })).join("");
      return `${comments}:${node.attribute} = {${unifiedLatexUtilPrintRaw.printRaw(
        node.content
      )}}`;
    }
    default:
      const unprintedType = type;
      console.warn(`Unknown node type "${unprintedType}" for node`, node);
      return "";
  }
}
exports.conditionalMacros = parser.conditionalMacros;
exports.environments = parser.environments;
exports.macros = parser.macros;
exports.parse = parser.parse;
exports.printRaw = printRaw;
//# sourceMappingURL=index.cjs.map
