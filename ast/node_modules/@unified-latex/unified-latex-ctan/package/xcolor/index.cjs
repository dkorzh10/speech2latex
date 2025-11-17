"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const xcolor = require("../../xcolor-BEfsW_1K.cjs");
const unifiedLatexUtilArguments = require("@unified-latex/unified-latex-util-arguments");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
const index = require("../../index-BuqJUpao.cjs");
const unifiedLatexUtilComments = require("@unified-latex/unified-latex-util-comments");
const unifiedLatexBuilder = require("@unified-latex/unified-latex-builder");
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
      return `>${node.name},${node.args.map((a) => "" + a).join(",")}`;
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
  node = index.structuredClone(node);
  unifiedLatexUtilComments.deleteComments(node);
  const args = unifiedLatexUtilArguments.getArgsContent(node);
  const model = args[0] && unifiedLatexUtilPrintRaw.printRaw(args[0]);
  const colorStr = unifiedLatexUtilPrintRaw.printRaw(args[1] || []);
  let hex = null;
  try {
    hex = xcolor.xcolorColorToHex(colorStr, model);
  } catch (e) {
  }
  const cssVarName = "--" + colorStr.replace(/[^a-zA-Z0-9-_]/g, "-");
  return { hex, cssVarName };
}
function colorToTextcolorMacro(content, origMacro) {
  if (!Array.isArray(content)) {
    content = [content];
  }
  const args = (origMacro.args ? origMacro.args : [unifiedLatexBuilder.arg([], { closeMark: "", openMark: "" }), unifiedLatexBuilder.arg([])]).concat(unifiedLatexBuilder.arg(content));
  return {
    type: "macro",
    content: "textcolor",
    args,
    _renderInfo: { inParMode: true }
  };
}
exports.DVI_PS_NAMES = xcolor.DVI_PS_NAMES;
exports.PREDEFINED_XCOLOR_COLORS = xcolor.PREDEFINED_XCOLOR_COLORS;
exports.SVG_NAMES = xcolor.SVG_NAMES;
exports.X11_NAMES = xcolor.X11_NAMES;
exports.XColorCoreModelToColor = xcolor.XColorCoreModelToColor;
exports.computeColor = xcolor.computeColor;
exports.environments = xcolor.environments;
exports.macros = xcolor.macros;
exports.parse = xcolor.parse;
exports.xcolorColorToHex = xcolor.xcolorColorToHex;
exports.colorToTextcolorMacro = colorToTextcolorMacro;
exports.printRaw = printRaw;
exports.xcolorMacroToHex = xcolorMacroToHex;
//# sourceMappingURL=index.cjs.map
