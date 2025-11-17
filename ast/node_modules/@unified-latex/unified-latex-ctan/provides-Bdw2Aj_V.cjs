"use strict";
const unifiedLatexBuilder = require("@unified-latex/unified-latex-builder");
const unifiedLatexUtilArgspec = require("@unified-latex/unified-latex-util-argspec");
const unifiedLatexUtilArguments = require("@unified-latex/unified-latex-util-arguments");
const unifiedLatexUtilMatch = require("@unified-latex/unified-latex-util-match");
const argSpecM = unifiedLatexUtilArgspec.parse("m")[0];
const argSpecO = unifiedLatexUtilArgspec.parse("o")[0];
const argSpecRDelim = {};
const argumentParser = (nodes, startPos) => {
  const { argument: optionalArg, nodesRemoved: optionalArgNodesRemoved } = unifiedLatexUtilArguments.gobbleSingleArgument(nodes, argSpecO, startPos);
  const { argument: languageArg, nodesRemoved: languageArgNodesRemoved } = unifiedLatexUtilArguments.gobbleSingleArgument(nodes, argSpecM, startPos);
  let codeArg = null;
  let codeArgNodesRemoved = 0;
  const nextNode = nodes[startPos];
  if (unifiedLatexUtilMatch.match.group(nextNode)) {
    const mandatoryArg = unifiedLatexUtilArguments.gobbleSingleArgument(nodes, argSpecM, startPos);
    codeArg = mandatoryArg.argument;
    codeArgNodesRemoved = mandatoryArg.nodesRemoved;
  } else if (unifiedLatexUtilMatch.match.string(nextNode) && nextNode.content.length === 1) {
    const delim = nextNode.content;
    argSpecRDelim[delim] = argSpecRDelim[delim] || unifiedLatexUtilArgspec.parse(`r${delim}${delim}`)[0];
    const delimArg = unifiedLatexUtilArguments.gobbleSingleArgument(
      nodes,
      argSpecRDelim[delim],
      startPos
    );
    codeArg = delimArg.argument;
    codeArgNodesRemoved = delimArg.nodesRemoved;
  }
  return {
    args: [
      optionalArg || unifiedLatexBuilder.arg(null),
      languageArg || unifiedLatexBuilder.arg(null),
      codeArg || unifiedLatexBuilder.arg(null)
    ],
    nodesRemoved: optionalArgNodesRemoved + languageArgNodesRemoved + codeArgNodesRemoved
  };
};
const macros = {
  mint: { argumentParser },
  mintinline: { argumentParser },
  inputminted: { argumentParser },
  usemintedstyle: { signature: "m" },
  setminted: { signature: "o m" },
  setmintedinline: { signature: "o m" },
  newmint: { signature: "o m m" },
  newminted: { signature: "o m m" },
  newmintinline: { signature: "o m m" },
  newmintedfile: { signature: "o m m" }
};
const environments = {
  minted: { signature: "o m" }
};
exports.environments = environments;
exports.macros = macros;
//# sourceMappingURL=provides-Bdw2Aj_V.cjs.map
