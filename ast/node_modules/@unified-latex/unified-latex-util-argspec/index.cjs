"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilPegjs = require("@unified-latex/unified-latex-util-pegjs");
function getDecorators(node) {
  let ret = "";
  if (node.noLeadingWhitespace) {
    ret += "!";
  }
  return ret;
}
function printRaw(node, root = false) {
  if (typeof node === "string") {
    return node;
  }
  if (Array.isArray(node)) {
    const sepToken = root ? " " : "";
    return node.map((tok) => printRaw(tok)).join(sepToken);
  }
  const decorators = getDecorators(node);
  const defaultArg = printDefaultArg(
    "defaultArg" in node ? node.defaultArg : void 0,
    // `embellishment`s are the only spec that can have multiple default args
    node.type === "embellishment"
  );
  let spec = decorators;
  const type = node.type;
  switch (type) {
    case "body":
      return decorators + "b";
    case "optionalStar":
      return decorators + "s";
    case "optionalToken":
      return spec + "t" + node.token;
    case "optional":
      if (node.openBrace === "[" && node.closeBrace === "]") {
        spec += node.defaultArg ? "O" : "o";
      } else {
        spec += node.defaultArg ? "D" : "d";
        spec += node.openBrace + node.closeBrace;
      }
      return spec + defaultArg;
    case "mandatory":
      if (node.openBrace === "{" && node.closeBrace === "}") {
        spec += "m";
      } else {
        spec += node.defaultArg ? "R" : "r";
        spec += node.openBrace + node.closeBrace;
      }
      return spec + defaultArg;
    case "embellishment":
      spec += node.defaultArg ? "E" : "e";
      return spec + "{" + printRaw(node.embellishmentTokens) + "}" + defaultArg;
    case "verbatim":
      return spec + "v" + node.openBrace;
    case "group":
      return spec + "{" + printRaw(node.content) + "}";
    case "until": {
      const stopTokens = printRaw(node.stopTokens);
      return stopTokens.length > 1 || stopTokens[0] === " " ? `u{${stopTokens}}` : `u${stopTokens}`;
    }
    default:
      const neverType = type;
      console.warn(`Unknown node type "${neverType}" for node`, node);
      return "";
  }
}
const parseCache = {};
function parse(str = "") {
  parseCache[str] = parseCache[str] || unifiedLatexUtilPegjs.ArgSpecPegParser.parse(str);
  return parseCache[str];
}
function printDefaultArg(args, multipleArgs) {
  if (!args) {
    return "";
  }
  if (typeof args === "string") {
    args = [args];
  }
  if (!multipleArgs) {
    return `{${args.join("")}}`;
  }
  return `{${args.map((a) => `{${a}}`).join("")}}`;
}
const argspecTypes = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null
}, Symbol.toStringTag, { value: "Module" }));
exports.ArgSpecAst = argspecTypes;
exports.parse = parse;
exports.printRaw = printRaw;
//# sourceMappingURL=index.cjs.map
