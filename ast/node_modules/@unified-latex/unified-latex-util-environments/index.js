import { updateRenderInfo } from "@unified-latex/unified-latex-util-render-info";
import { gobbleArguments } from "@unified-latex/unified-latex-util-arguments";
import { match } from "@unified-latex/unified-latex-util-match";
import { visit } from "@unified-latex/unified-latex-util-visit";
import { printRaw } from "@unified-latex/unified-latex-util-print-raw";
function processEnvironment(envNode, envInfo) {
  if (envInfo.signature && envNode.args == null) {
    const { args } = gobbleArguments(envNode.content, envInfo.signature);
    envNode.args = args;
  }
  updateRenderInfo(envNode, envInfo.renderInfo);
  if (typeof envInfo.processContent === "function") {
    envNode.content = envInfo.processContent(envNode.content);
  }
}
function processEnvironments(tree, environments) {
  const isRelevantEnvironment = match.createEnvironmentMatcher(environments);
  visit(
    tree,
    {
      leave: (node) => {
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
    { test: isRelevantEnvironment }
  );
}
const unifiedLatexProcessEnvironments = function unifiedLatexAttachMacroArguments(options) {
  const { environments = {} } = options || {};
  const isRelevantEnvironment = match.createEnvironmentMatcher(environments);
  return (tree) => {
    if (Object.keys(environments).length === 0) {
      console.warn(
        "Attempting to attach macro arguments but no macros are specified."
      );
    }
    visit(
      tree,
      {
        leave: (node) => {
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
      { test: isRelevantEnvironment }
    );
  };
};
export {
  processEnvironment,
  processEnvironments,
  unifiedLatexProcessEnvironments
};
//# sourceMappingURL=index.js.map
