import { e, m } from "../../provides-yGf6-zdY.js";
import { match } from "@unified-latex/unified-latex-util-match";
import { decorateArrayForPegjs, SystemePegParser } from "@unified-latex/unified-latex-util-pegjs";
import { printRaw as printRaw$1 } from "@unified-latex/unified-latex-util-print-raw";
import { arrayJoin } from "@unified-latex/unified-latex-util-split";
import { s as structuredClone } from "../../index-NHd3tQDq.js";
import { deleteComments } from "@unified-latex/unified-latex-util-comments";
import { visit } from "@unified-latex/unified-latex-util-visit";
import { updateRenderInfo } from "@unified-latex/unified-latex-util-render-info";
import { getArgsContent } from "@unified-latex/unified-latex-util-arguments";
function createMatchers({
  at = "@",
  equals = "=",
  equationSeparator = ",",
  mathOperations = ["+", "-"],
  whitelistedVariables
} = {}) {
  let isVar = (node) => match.anyString(node) && !!node.content.match(/[a-zA-Z]/);
  if (whitelistedVariables) {
    whitelistedVariables = whitelistedVariables.map(
      (v) => match.anyString(v) ? v.content : v
    );
    const macros = whitelistedVariables.filter(
      (v) => match.anyMacro(v)
    );
    const strings = whitelistedVariables.filter(
      (v) => typeof v === "string"
    );
    const macroHash = Object.fromEntries(macros.map((v) => [v.content, v]));
    const stringHash = Object.fromEntries(strings.map((s) => [s, s]));
    const macroMatcher = match.createMacroMatcher(macroHash);
    isVar = (node) => macroMatcher(node) || match.anyString(node) && !!stringHash[node.content];
  }
  return {
    isSep: (node) => match.string(node, equationSeparator),
    isVar,
    isOperation: (node) => mathOperations.some((op) => match.string(node, op)),
    isEquals: (node) => match.string(node, equals),
    isAt: (node) => match.string(node, at),
    isSubscript: (node) => match.macro(node, "_") && node.escapeToken === "",
    isWhitespace: match.whitespace,
    isSameLineComment: (node) => match.comment(node) && node.sameline,
    isOwnLineComment: (node) => match.comment(node) && !node.sameline
  };
}
function parse(ast, options) {
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = decorateArrayForPegjs([...ast]);
  return SystemePegParser.parse(
    ast,
    createMatchers(options || {})
  );
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
    case "annotation":
      return `${printRaw$1(node.marker)}${printRaw$1(
        node.content
      )}`;
    case "item":
      return `${node.op ? printRaw$1(node.op) : ""}${printRaw$1(
        node.content
      )}`;
    case "equation":
      const left = node.left.map((n) => printRaw(n)).join("");
      const right = printRaw$1(node.right);
      const equals = node.equals ? printRaw$1(node.equals) : "";
      return `${left}${equals}${right}`;
    case "line":
      const equation = node.equation ? printRaw(node.equation) : "";
      const annotation = node.annotation ? printRaw(node.annotation) : "";
      const sep = node.sep ? printRaw$1(node.sep) : "";
      const body = `${equation}${annotation}${sep}`;
      if (node.trailingComment) {
        return printRaw$1([body, node.trailingComment]);
      }
      return body;
    default:
      console.warn(
        `Unknown node type "${node.type}" for node`,
        node
      );
      return "";
  }
}
const AMP = { type: "string", content: "&" };
const SEP = { type: "macro", content: "\\" };
const QUAD = { type: "macro", content: "quad" };
const PLUS = { type: "string", content: "+" };
const COLUMN_KERN_ADJUSTMENT = [
  { type: "string", content: "@" },
  {
    type: "group",
    content: [
      { type: "macro", content: "mkern" },
      { type: "string", content: "5mu" }
    ]
  }
];
function sortVariables(vars, whitelistedVariables) {
  const varMap = new Map(vars.map((v) => [v, printRaw$1(v)]));
  const varNames = Array.from(new Set(varMap.values()));
  varNames.sort();
  const nameToPos = whitelistedVariables ? new Map(whitelistedVariables.map((v, i) => [printRaw$1(v), i])) : new Map(varNames.map((name, i) => [name, i]));
  return new Map(
    Array.from(varMap.entries()).map(([variable, name]) => {
      return [variable, nameToPos.get(name) ?? -1];
    })
  );
}
function processLine(line, numVars, varOrder, hasEquals, hasAnnotation) {
  const ret = [];
  if (line.equation) {
    const nonVarItems = line.equation.left.filter(
      (item) => item.variable == null
    );
    const varItems = line.equation.left.filter(
      (item) => item.variable != null
    );
    let nonVarTerm = null;
    if (nonVarItems.length === 1) {
      nonVarTerm = nonVarItems[0];
    } else if (nonVarItems.length > 1) {
      nonVarTerm = {
        ...nonVarItems[0],
        content: nonVarItems[0].content.concat(
          nonVarItems.slice(1).flatMap((item) => {
            if (item.op) {
              return [item.op, ...item.content];
            }
            return [PLUS, ...item.content];
          })
        )
      };
    }
    const allItems = nonVarTerm ? varItems.concat(nonVarTerm) : varItems;
    const indexToItem = new Map(
      allItems.map((item) => {
        if (item.variable == null) {
          return [numVars - 1, item];
        }
        return [varOrder.get(item.variable), item];
      })
    );
    let isFirstItem = true;
    for (let i = 0; i < numVars; i++) {
      const item = indexToItem.get(i);
      if (item) {
        if (isFirstItem && (match.string(item.op, "+") || item.op == null)) {
          ret.push([]);
          ret.push(item.content);
        } else {
          ret.push([item.op || PLUS]);
          ret.push(item.content);
        }
        isFirstItem = false;
      } else {
        ret.push([]);
        ret.push([]);
      }
    }
    if (hasEquals) {
      const equalsPart = (line.equation.equals ? [line.equation.equals] : []).concat(line.equation.right);
      ret.push(equalsPart);
    }
  }
  if (hasAnnotation) {
    ret.push(line.annotation ? line.annotation.content : []);
  }
  return ret;
}
function arraySpecToSpacedArraySpec(spec, hasAnnotation) {
  const annotationSpec = hasAnnotation ? spec.charAt(spec.length - 1) : "";
  const bodySpec = hasAnnotation ? spec.slice(0, spec.length - 1) : spec;
  const bodyStrings = Array.from(bodySpec).map((x) => [
    { type: "string", content: x }
  ]);
  const body = arrayJoin(bodyStrings, COLUMN_KERN_ADJUSTMENT);
  return annotationSpec ? body.concat({ type: "string", content: annotationSpec }) : body;
}
function extractVariables(nodes) {
  return nodes.flatMap((node) => {
    if (node.type === "line" && node.equation) {
      return extractVariables(node.equation.left);
    }
    if (node.type === "equation") {
      return node.left.flatMap(
        (item) => item.variable ? [item.variable] : []
      );
    }
    if (node.type === "item") {
      return node.variable ? [node.variable] : [];
    }
    return [];
  });
}
function normalizeVariableWhitelist(vars) {
  if (!vars) {
    return null;
  }
  const normalized = vars.map(
    (v) => typeof v === "string" ? { type: "string", content: v } : v
  );
  const ret = normalized.filter(
    (v) => (match.anyMacro(v) || match.anyString(v)) && !match.string(v, " ") && !match.whitespace(v)
  );
  return ret;
}
function systemeContentsToArray(nodes, options) {
  nodes = structuredClone(nodes);
  deleteComments(nodes);
  const { properSpacing = true, whitelistedVariables } = options || {};
  const coercedWhitelistedVariables = normalizeVariableWhitelist(whitelistedVariables);
  const systemeAst = parse(nodes, { whitelistedVariables });
  const vars = extractVariables(systemeAst);
  const varOrder = sortVariables(vars, coercedWhitelistedVariables);
  let numVars = coercedWhitelistedVariables ? coercedWhitelistedVariables.length : Math.max(...Array.from(varOrder.values())) + 1;
  if (systemeAst.some((line) => {
    if (line.equation) {
      return line.equation.left.some((item) => item.variable == null);
    }
  })) {
    numVars += 1;
  }
  const hasEquals = systemeAst.some(
    (line) => line.equation && line.equation.equals
  );
  const hasAnnotation = systemeAst.some((line) => line.annotation);
  let rows = systemeAst.map(
    (line) => processLine(line, numVars, varOrder, hasEquals, hasAnnotation)
  );
  const noLeadingOperation = rows.every((row) => row[0].length === 0);
  let arraySignature = Array.from({ length: numVars }, () => "cr").join("");
  if (noLeadingOperation) {
    arraySignature = arraySignature.slice(1);
    rows = rows.map((row) => row.slice(1));
  }
  if (hasEquals) {
    arraySignature += "l";
  }
  if (hasAnnotation) {
    arraySignature += "l";
    rows = rows.map((row) => {
      if (row[row.length - 1].length === 0) {
        return row;
      }
      return [
        ...row.slice(0, row.length - 1),
        [QUAD, { type: "whitespace" }, ...row[row.length - 1]]
      ];
    });
  }
  const arraySignatureWithSpacing = properSpacing ? arraySpecToSpacedArraySpec(arraySignature, hasAnnotation) : [{ type: "string", content: arraySignature }];
  const bodyRows = rows.map((row) => arrayJoin(row, AMP));
  const body = arrayJoin(bodyRows, SEP);
  const ret = {
    type: "environment",
    env: "array",
    args: [
      {
        type: "argument",
        openMark: "{",
        closeMark: "}",
        content: arraySignatureWithSpacing
      }
    ],
    content: body
  };
  return ret;
}
function attachSystemeSettingsAsRenderInfo(ast) {
  const systemeMatcher = match.createMacroMatcher(["systeme", "sysdelim"]);
  visit(
    ast,
    (nodes, info) => {
      if (!info.context.inMathMode || !nodes.some(systemeMatcher)) {
        return;
      }
      const systemeLocations = nodes.flatMap(
        (node, i) => match.macro(node, "systeme") ? i : []
      );
      const sysdelimLocations = nodes.flatMap(
        (node, i) => match.macro(node, "sysdelim") ? i : []
      );
      if (systemeLocations.length === 0 || sysdelimLocations.length === 0) {
        return;
      }
      for (const i of systemeLocations) {
        const lastSysdelim = Math.max(
          ...sysdelimLocations.filter((loc) => loc < i)
        );
        if (lastSysdelim >= 0) {
          const node = nodes[i];
          const sysdelimMacro = nodes[lastSysdelim];
          if (!match.anyMacro(sysdelimMacro)) {
            throw new Error(
              `Expecting sysdelim macro but found "${printRaw$1(
                sysdelimMacro
              )}"`
            );
          }
          const args = getArgsContent(sysdelimMacro);
          updateRenderInfo(node, { sysdelims: args });
        }
      }
    },
    {
      test: Array.isArray,
      includeArrays: true
    }
  );
}
export {
  attachSystemeSettingsAsRenderInfo,
  e as environments,
  extractVariables,
  m as macros,
  parse,
  printRaw,
  systemeContentsToArray
};
//# sourceMappingURL=index.js.map
