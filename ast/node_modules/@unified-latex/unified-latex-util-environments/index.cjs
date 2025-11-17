"use strict";
Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });
const unifiedLatexUtilRenderInfo = require("@unified-latex/unified-latex-util-render-info");
const unifiedLatexUtilArguments = require("@unified-latex/unified-latex-util-arguments");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const unifiedLatexUtilVisit = require("@unified-latex/unified-latex-util-visit");
const unifiedLatexUtilPrintRaw = require("@unified-latex/unified-latex-util-print-raw");
function processEnvironment(envNode, envInfo) {
  if (envInfo.signature && envNode.args == null) {
    const { args } = unifiedLatexUtilArguments.gobbleArguments(envNode.content, envInfo.signature);
    envNode.args = args;
  }
  unifiedLatexUtilRenderInfo.updateRenderInfo(envNode, envInfo.renderInfo);
  if (typeof envInfo.processContent === "function") {
    envNode.content = envInfo.processContent(envNode.content);
  }
}
function processEnvironments(tree, environments) {
  const isRelevantEnvironment = unifiedLatexUtilMatch.match.createEnvironmentMatcher(environments);
  unifiedLatexUtilVisit.visit(
    tree,
    {
      leave: (node) => {
        const envName = unifiedLatexUtilPrintRaw.printRaw(node.env);
        const envInfo = environments[envName];
        if (!envInfo) {
          throw new Error(
            `Could not find environment info for environment "${envName}"`
          );
        }
        processEnvironment(node, envInfo);
      }
    },
    { test: isRelevantEnvironment }
  );
}
const unifiedLatexProcessEnvironments = function unifiedLatexAttachMacroArguments(options) {
  const { environments = {} } = options || {};
  const isRelevantEnvironment = unifiedLatexUtilMatch.match.createEnvironmentMatcher(environments);
  return (tree) => {
    if (Object.keys(environments).length === 0) {
      console.warn(
        "Attempting to attach macro arguments but no macros are specified."
      );
    }
    unifiedLatexUtilVisit.visit(
      tree,
      {
        leave: (node) => {
          const envName = unifiedLatexUtilPrintRaw.printRaw(node.env);
          const envInfo = environments[envName];
          if (!envInfo) {
            throw new Error(
              `Could not find environment info for environment "${envName}"`
            );
          }
          processEnvironment(node, envInfo);
        }
      },
      { test: isRelevantEnvironment }
    );
  };
};
exports.processEnvironment = processEnvironment;
exports.processEnvironments = processEnvironments;
exports.unifiedLatexProcessEnvironments = unifiedLatexProcessEnvironments;
//# sourceMappingURL=index.cjs.map
