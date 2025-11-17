import { x as xcolorColorToHex } from "../../xcolor-CIejE3rZ.js";
import { D, P, S, a, X, c, e, m, p } from "../../xcolor-CIejE3rZ.js";
import { getArgsContent } from "@unified-latex/unified-latex-util-arguments";
import { printRaw as printRaw$1 } from "@unified-latex/unified-latex-util-print-raw";
import { s as structuredClone } from "../../index-NHd3tQDq.js";
import { deleteComments } from "@unified-latex/unified-latex-util-comments";
import { arg } from "@unified-latex/unified-latex-builder";
function printRaw(node, root = false) {
  if (typeof node === "string") {
    return node;
  }
  if (Array.isArray(node)) {
    const sepToken = root ? " " : "";
    return node.map((tok) => printRaw(tok)).join(sepToken);
  }
  if (node.type === "invalid_spec") {
    return node.content;
  }
  switch (node.type) {
    case "postfix":
      if (node.plusses != null) {
        return `!!${node.plusses}`;
      } else {
        return `!![${node.num}]`;
      }
    case "complete_mix":
      return `!${node.mix_percent}!${node.name}`;
    case "partial_mix":
      return `!${node.mix_percent}`;
    case "expr":
      return `${node.prefix || ""}${node.name}${node.mix_expr.map((mix) => printRaw(mix)).join("")}${node.postfix ? printRaw(node.postfix) : ""}`;
    case "weighted_expr":
      return `${printRaw(node.color)},${node.weight}`;
    case "extended_expr":
      let prefix = node.core_model;
      if (node.div) {
        prefix += `,${node.div}`;
      }
      return `${prefix}:${node.expressions.map((expr) => printRaw(expr)).join(";")}`;
    case "function":
      return `>${node.name},${node.args.map((a2) => "" + a2).join(",")}`;
    case "color":
      return printRaw(node.color) + node.functions.map((f) => printRaw(f)).join("");
    default:
      console.warn(
        `Unknown node type "${node.type}" for node`,
        node
      );
      return "";
  }
}
function xcolorMacroToHex(node) {
  node = structuredClone(node);
  deleteComments(node);
  const args = getArgsContent(node);
  const model = args[0] && printRaw$1(args[0]);
  const colorStr = printRaw$1(args[1] || []);
  let hex = null;
  try {
    hex = xcolorColorToHex(colorStr, model);
  } catch (e2) {
  }
  const cssVarName = "--" + colorStr.replace(/[^a-zA-Z0-9-_]/g, "-");
  return { hex, cssVarName };
}
function colorToTextcolorMacro(content, origMacro) {
  if (!Array.isArray(content)) {
    content = [content];
  }
  const args = (origMacro.args ? origMacro.args : [arg([], { closeMark: "", openMark: "" }), arg([])]).concat(arg(content));
  return {
    type: "macro",
    content: "textcolor",
    args,
    _renderInfo: { inParMode: true }
  };
}
export {
  D as DVI_PS_NAMES,
  P as PREDEFINED_XCOLOR_COLORS,
  S as SVG_NAMES,
  a as X11_NAMES,
  X as XColorCoreModelToColor,
  colorToTextcolorMacro,
  c as computeColor,
  e as environments,
  m as macros,
  p as parse,
  printRaw,
  xcolorColorToHex,
  xcolorMacroToHex
};
//# sourceMappingURL=index.js.map
