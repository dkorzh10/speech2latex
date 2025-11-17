import { unified } from "unified";
import { unifiedLatexFromString, unifiedLatexAstComplier } from "@unified-latex/unified-latex-util-parse";
import { unifiedLatexStringCompiler } from "@unified-latex/unified-latex-util-to-string";
const processLatexViaUnified = (options) => {
  return unified().use(unifiedLatexFromString, options).use(
    unifiedLatexStringCompiler,
    Object.assign({ pretty: true }, options)
  );
};
const processLatexToAstViaUnified = () => {
  return unified().use(unifiedLatexFromString).use(unifiedLatexAstComplier);
};
export {
  processLatexToAstViaUnified,
  processLatexViaUnified
};
//# sourceMappingURL=index.js.map
