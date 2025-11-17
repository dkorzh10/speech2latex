import { unified } from "unified";
import { macroInfo, environmentInfo } from "@unified-latex/unified-latex-ctan";
import { unifiedLatexTrimEnvironmentContents, unifiedLatexTrimRoot } from "@unified-latex/unified-latex-util-trim";
import { LatexPegParser } from "@unified-latex/unified-latex-util-pegjs";
import { visit } from "@unified-latex/unified-latex-util-visit";
import { match } from "@unified-latex/unified-latex-util-match";
import { printRaw } from "@unified-latex/unified-latex-util-print-raw";
import { attachMacroArgsInArray } from "@unified-latex/unified-latex-util-arguments";
import { processEnvironment } from "@unified-latex/unified-latex-util-environments";
import { reparseExpl3AndAtLetterRegions, hasReparsableMacroNames, reparseMacroNames } from "@unified-latex/unified-latex-util-catcode";
const unifiedLatexAstComplier = function unifiedLatexAstComplier2() {
  Object.assign(this, { Compiler: (x) => x });
};
function parseMinimal(str) {
  return LatexPegParser.parse(str);
}
function parseMathMinimal(str) {
  return LatexPegParser.parse(str, { startRule: "math" });
}
const unifiedLatexFromStringMinimal = function unifiedLatexFromStringMinimal2(options) {
  const parser2 = (str) => {
    if ((options == null ? void 0 : options.mode) === "math") {
      return {
        type: "root",
        content: parseMathMinimal(str),
        _renderInfo: { inMathMode: true }
      };
    }
    return parseMinimal(str);
  };
  Object.assign(this, { Parser: parser2 });
};
const unifiedLatexReparseMath = function unifiedLatexReparseMath2(options) {
  const { mathEnvs = [], mathMacros = [] } = options || {};
  return unifiedLatexReparseMathConstructPlugin({ mathMacros, mathEnvs });
};
function unifiedLatexReparseMathConstructPlugin({
  mathEnvs,
  mathMacros
}) {
  const isMathEnvironment = match.createEnvironmentMatcher(mathEnvs);
  const isMathMacro = match.createMacroMatcher(mathMacros);
  return (tree) => {
    visit(
      tree,
      (node) => {
        if (match.anyMacro(node)) {
          for (const arg of node.args || []) {
            if (arg.content.length > 0 && !wasParsedInMathMode(arg.content)) {
              arg.content = parseMathMinimal(
                printRaw(arg.content)
              );
            }
          }
        }
        if (match.anyEnvironment(node)) {
          if (!wasParsedInMathMode(node.content)) {
            node.content = parseMathMinimal(printRaw(node.content));
          }
        }
      },
      {
        test: (node) => isMathEnvironment(node) || isMathMacro(node)
      }
    );
  };
}
function wasParsedInMathMode(nodes) {
  return !nodes.some(
    (node) => (
      // If there are multi-char strings or ^ and _ have been parsed as strings, we know
      // that we were not parsed in math mode.
      match.anyString(node) && node.content.length > 1 || match.string(node, "^") || match.string(node, "_")
    )
  );
}
const unifiedLatexProcessMacrosAndEnvironmentsWithMathReparse = function unifiedLatexProcessMacrosAndEnvironmentsWithMathReparse2(options) {
  const { environments = {}, macros = {} } = options || {};
  const mathMacros = Object.fromEntries(
    Object.entries(macros).filter(
      ([_, info]) => {
        var _a;
        return ((_a = info.renderInfo) == null ? void 0 : _a.inMathMode) === true;
      }
    )
  );
  const mathEnvs = Object.fromEntries(
    Object.entries(environments).filter(
      ([_, info]) => {
        var _a;
        return ((_a = info.renderInfo) == null ? void 0 : _a.inMathMode) === true;
      }
    )
  );
  const mathReparser = unifiedLatexReparseMathConstructPlugin({
    mathEnvs: Object.keys(mathEnvs),
    mathMacros: Object.keys(mathMacros)
  });
  const isRelevantEnvironment = match.createEnvironmentMatcher(environments);
  const isRelevantMathEnvironment = match.createEnvironmentMatcher(mathEnvs);
  return (tree) => {
    visit(
      tree,
      {
        enter: (nodes) => {
          if (!Array.isArray(nodes)) {
            return;
          }
          attachMacroArgsInArray(nodes, mathMacros);
        },
        leave: (node) => {
          if (!isRelevantMathEnvironment(node)) {
            return;
          }
          const envName = printRaw(node.env);
          const envInfo = environments[envName];
          if (!envInfo) {
            throw new Error(
              `Could not find environment info for environment "${envName}"`
            );
          }
          processEnvironment(node, envInfo);
        }
      },
      { includeArrays: true }
    );
    mathReparser(tree);
    visit(
      tree,
      {
        enter: (nodes) => {
          if (!Array.isArray(nodes)) {
            return;
          }
          attachMacroArgsInArray(nodes, macros);
        },
        leave: (node) => {
          if (!isRelevantEnvironment(node)) {
            return;
          }
          const envName = printRaw(node.env);
          const envInfo = environments[envName];
          if (!envInfo) {
            throw new Error(
              `Could not find environment info for environment "${envName}"`
            );
          }
          processEnvironment(node, envInfo);
        }
      },
      { includeArrays: true }
    );
  };
};
const unifiedLatexProcessAtLetterAndExplMacros = function unifiedLatexProcessAtLetterAndExplMacros2(options) {
  let {
    atLetter = false,
    expl3 = false,
    autodetectExpl3AndAtLetter = false
  } = options || {};
  return (tree) => {
    reparseExpl3AndAtLetterRegions(tree);
    if (atLetter || expl3) {
      autodetectExpl3AndAtLetter = false;
    }
    if (autodetectExpl3AndAtLetter) {
      atLetter = hasReparsableMacroNames(tree, "@");
      expl3 = hasReparsableMacroNames(tree, "_");
    }
    const charSet = /* @__PURE__ */ new Set();
    if (atLetter) {
      charSet.add("@");
    }
    if (expl3) {
      charSet.add(":");
      charSet.add("_");
    }
    if (charSet.size > 0) {
      reparseMacroNames(tree, charSet);
    }
  };
};
const unifiedLatexFromString = function unifiedLatexFromString2(options) {
  const {
    mode = "regular",
    macros = {},
    environments = {},
    flags: {
      atLetter = false,
      expl3 = false,
      autodetectExpl3AndAtLetter = false
    } = {}
  } = options || {};
  const allMacroInfo = Object.assign(
    {},
    ...Object.values(macroInfo),
    macros
  );
  const allEnvInfo = Object.assign(
    {},
    ...Object.values(environmentInfo),
    environments
  );
  const fullParser = unified().use(unifiedLatexFromStringMinimal, { mode }).use(unifiedLatexProcessAtLetterAndExplMacros, {
    atLetter,
    expl3,
    autodetectExpl3AndAtLetter
  }).use(unifiedLatexProcessMacrosAndEnvironmentsWithMathReparse, {
    macros: allMacroInfo,
    environments: allEnvInfo
  }).use(unifiedLatexTrimEnvironmentContents).use(unifiedLatexTrimRoot).use(unifiedLatexAstComplier);
  const parser2 = (str) => {
    const file = fullParser.processSync({ value: str });
    return file.result;
  };
  Object.assign(this, { Parser: parser2 });
};
let parser = unified().use(unifiedLatexFromString).freeze();
function parse(str) {
  return parser.parse(str);
}
function getParser(options) {
  return options ? unified().use(unifiedLatexFromString, options).freeze() : parser;
}
function parseMath(str) {
  if (typeof str !== "string") {
    str = printRaw(str);
  }
  const parser2 = unified().use(unifiedLatexFromString, { mode: "math" });
  return parser2.parse({ value: str }).content;
}
export {
  getParser,
  parse,
  parseMath,
  parseMathMinimal,
  parseMinimal,
  unifiedLatexAstComplier,
  unifiedLatexFromString,
  unifiedLatexFromStringMinimal,
  unifiedLatexProcessAtLetterAndExplMacros,
  unifiedLatexProcessMacrosAndEnvironmentsWithMathReparse,
  unifiedLatexReparseMath,
  unifiedLatexReparseMathConstructPlugin
};
//# sourceMappingURL=index.js.map
