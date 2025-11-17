import { c, e, m, p } from "../../parser-BBXMi7mQ.js";
import { printRaw as printRaw$1 } from "@unified-latex/unified-latex-util-print-raw";
import { trim } from "@unified-latex/unified-latex-util-trim";
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
      return `${printRaw$1(node.prefix)}(${printRaw$1(
        node.content
      )})`;
    case "operation":
      return printRaw$1(node.content);
    case "comment":
      return printRaw$1(node);
    case "line_to":
      return node.command;
    case "curve_to": {
      const comments = node.comments.map((c2) => printRaw$1({ ...c2, leadingWhitespace: false })).join("");
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
      return printRaw$1(node.content);
    case "square_brace_group":
      return `[${printRaw$1(node.content)}]`;
    case "foreach": {
      const comments = node.comments.map((c2) => printRaw$1({ ...c2, leadingWhitespace: false })).join("");
      let options = "";
      if (node.options) {
        options = ` [${printRaw$1(node.options)}]`;
      }
      const start = printRaw$1(node.start);
      const variables = [...node.variables];
      trim(variables);
      let printedVariables = printRaw$1(variables);
      if (printedVariables.length > 0) {
        printedVariables = " " + printedVariables;
      }
      const command = node.command.type === "foreach" ? printRaw(node.command) : printRaw$1(node.command);
      return `${comments}${start}${printedVariables}${options} in ${printRaw$1(
        node.list
      )} ${command}`;
    }
    case "svg_operation": {
      const comments = node.comments.map((c2) => printRaw$1({ ...c2, leadingWhitespace: false })).join("");
      let options = "";
      if (node.options) {
        options = `[${printRaw$1(node.options)}]`;
      }
      return `${comments}svg${options} ${printRaw$1(node.content)}`;
    }
    case "animation": {
      const comments = node.comments.map((c2) => printRaw$1({ ...c2, leadingWhitespace: false })).join("");
      return `${comments}:${node.attribute} = {${printRaw$1(
        node.content
      )}}`;
    }
    default:
      const unprintedType = type;
      console.warn(`Unknown node type "${unprintedType}" for node`, node);
      return "";
  }
}
export {
  c as conditionalMacros,
  e as environments,
  m as macros,
  p as parse,
  printRaw
};
//# sourceMappingURL=index.js.map
