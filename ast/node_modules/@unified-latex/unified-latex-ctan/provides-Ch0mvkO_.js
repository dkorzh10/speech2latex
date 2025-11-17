import { arg } from "@unified-latex/unified-latex-builder";
import { parse } from "@unified-latex/unified-latex-util-argspec";
import { gobbleSingleArgument } from "@unified-latex/unified-latex-util-arguments";
import { match } from "@unified-latex/unified-latex-util-match";
const argSpecM = parse("m")[0];
const argSpecO = parse("o")[0];
const argSpecRDelim = {};
const argumentParser = (nodes, startPos) => {
  const { argument: optionalArg, nodesRemoved: optionalArgNodesRemoved } = gobbleSingleArgument(nodes, argSpecO, startPos);
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
    args: [optionalArg || arg(null), codeArg || arg(null)],
    nodesRemoved: optionalArgNodesRemoved + codeArgNodesRemoved
  };
};
const macros = {
  lstset: { signature: "m" },
  lstinline: { argumentParser },
  lstinputlisting: { signature: "o m" },
  lstdefinestyle: { signature: "m m" },
  lstnewenvironment: { signature: "m o o m m" },
  lstMakeShortInline: { signature: "o m" },
  lstDeleteShortInline: { signature: "m" },
  lstdefineformat: { signature: "m m" },
  lstdefinelanguage: { signature: "o m o m o" },
  lstalias: { signature: "o m o m" },
  lstloadlanguages: { signature: "m" }
};
const environments = {};
export {
  environments as e,
  macros as m
};
//# sourceMappingURL=provides-Ch0mvkO_.js.map
