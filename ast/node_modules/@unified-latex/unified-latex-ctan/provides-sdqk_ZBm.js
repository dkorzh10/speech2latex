import { arg } from "@unified-latex/unified-latex-builder";
import { parse } from "@unified-latex/unified-latex-util-argspec";
import { gobbleSingleArgument } from "@unified-latex/unified-latex-util-arguments";
import { match } from "@unified-latex/unified-latex-util-match";
const argSpecM = parse("m")[0];
const argSpecO = parse("o")[0];
const argSpecRDelim = {};
const argumentParser = (nodes, startPos) => {
  const { argument: optionalArg, nodesRemoved: optionalArgNodesRemoved } = gobbleSingleArgument(nodes, argSpecO, startPos);
  const { argument: languageArg, nodesRemoved: languageArgNodesRemoved } = gobbleSingleArgument(nodes, argSpecM, startPos);
  let codeArg = null;
  let codeArgNodesRemoved = 0;
  const nextNode = nodes[startPos];
  if (match.group(nextNode)) {
    const mandatoryArg = gobbleSingleArgument(nodes, argSpecM, startPos);
    codeArg = mandatoryArg.argument;
    codeArgNodesRemoved = mandatoryArg.nodesRemoved;
  } else if (match.string(nextNode) && nextNode.content.length === 1) {
    const delim = nextNode.content;
    argSpecRDelim[delim] = argSpecRDelim[delim] || parse(`r${delim}${delim}`)[0];
    const delimArg = gobbleSingleArgument(
      nodes,
      argSpecRDelim[delim],
      startPos
    );
    codeArg = delimArg.argument;
    codeArgNodesRemoved = delimArg.nodesRemoved;
  }
  return {
    args: [
      optionalArg || arg(null),
      languageArg || arg(null),
      codeArg || arg(null)
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
export {
  environments as e,
  macros as m
};
//# sourceMappingURL=provides-sdqk_ZBm.js.map
