import { gobbleSingleArgument, attachMacroArgsInArray } from "@unified-latex/unified-latex-util-arguments";
import { arg } from "@unified-latex/unified-latex-builder";
import { parse as parse$1 } from "@unified-latex/unified-latex-util-argspec";
import { match } from "@unified-latex/unified-latex-util-match";
import { scan } from "@unified-latex/unified-latex-util-scan";
import { trim } from "@unified-latex/unified-latex-util-trim";
import { decorateArrayForPegjs, TikzPegParser } from "@unified-latex/unified-latex-util-pegjs";
const OPTIONAL_ARGUMENT_ARG_SPEC = parse$1("o")[0];
function blankArg() {
  return arg([], { openMark: "", closeMark: "" });
}
const tikzCommandArgumentParser = (nodes, startPos) => {
  const origStartPos = startPos;
  let pos = startPos;
  let nodesRemoved = 0;
  const cursorPosAfterAnimations = eatAllAnimationSpecs(nodes, pos);
  let animationArg = blankArg();
  if (cursorPosAfterAnimations !== pos) {
    const argContent = nodes.splice(pos, cursorPosAfterAnimations - pos);
    trim(argContent);
    animationArg = arg(argContent, {
      openMark: " ",
      closeMark: " "
    });
  }
  nodesRemoved += cursorPosAfterAnimations - pos;
  const {
    argument: _optionalArgument,
    nodesRemoved: optionalArgumentNodesRemoved
  } = gobbleSingleArgument(nodes, OPTIONAL_ARGUMENT_ARG_SPEC, pos);
  nodesRemoved += optionalArgumentNodesRemoved;
  const optionalArg = _optionalArgument || blankArg();
  while (match.whitespace(nodes[pos])) {
    pos++;
  }
  const firstNode = nodes[pos];
  if (!firstNode) {
    return {
      args: [animationArg, optionalArg, blankArg()],
      nodesRemoved: 0
    };
  }
  if (match.group(firstNode)) {
    const args = [animationArg, optionalArg, arg(firstNode.content)];
    nodes.splice(origStartPos, pos - origStartPos + 1);
    return { args, nodesRemoved: pos - origStartPos + 1 + nodesRemoved };
  }
  const semicolonPosition = scan(nodes, ";", { startIndex: pos });
  if (semicolonPosition != null) {
    const argNodes = nodes.splice(
      origStartPos,
      semicolonPosition - origStartPos + 1
    );
    trim(argNodes);
    const args = [animationArg, optionalArg, arg(argNodes)];
    return {
      args,
      nodesRemoved: origStartPos - semicolonPosition + 1 + nodesRemoved
    };
  }
  return {
    args: [animationArg, optionalArg, blankArg()],
    nodesRemoved: 0
  };
};
function eatAllAnimationSpecs(nodes, startPos) {
  const colonPos = scan(nodes, ":", {
    startIndex: startPos,
    allowSubstringMatches: true,
    onlySkipWhitespaceAndComments: true
  });
  if (!colonPos) {
    return startPos;
  }
  let lastMatchPos = startPos;
  let i = colonPos + 1;
  for (; i < nodes.length; i++) {
    const node = nodes[i];
    if (match.string(node, "[")) {
      break;
    }
    if (match.string(node, "=")) {
      i++;
      while (match.whitespace(nodes[i]) || match.comment(nodes[i])) {
        i++;
      }
      if (!match.group(nodes[i])) {
        break;
      }
      lastMatchPos = i + 1;
      const colonPos2 = scan(nodes, ":", {
        startIndex: lastMatchPos,
        allowSubstringMatches: true,
        onlySkipWhitespaceAndComments: true
      });
      if (colonPos2 == null) {
        break;
      }
      i = colonPos2 + 1;
    }
  }
  return lastMatchPos;
}
const macros = {
  pgfkeys: {
    signature: "m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  tikzoption: {
    signature: "m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  tikzstyle: {
    signature: "m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  usetikzlibrary: {
    signature: "m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  usepgfmodule: { signature: "m", renderInfo: { pgfkeysArgs: true } },
  usepgflibrary: { signature: "m", renderInfo: { pgfkeysArgs: true } },
  pgfplotsset: {
    signature: "m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  pgfplotstabletypeset: {
    signature: "o m",
    renderInfo: { breakAround: true, pgfkeysArgs: true }
  },
  tikz: {
    signature: "o o m",
    argumentParser: tikzCommandArgumentParser,
    renderInfo: { namedArguments: ["animation", "options", "command"] }
  }
};
const environments = {
  tikzpicture: {
    signature: "o",
    renderInfo: { pgfkeysArgs: true, tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  axis: {
    signature: "o",
    renderInfo: { pgfkeysArgs: true, tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  scope: {
    signature: "o",
    renderInfo: { pgfkeysArgs: true, tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  pgfonlayer: {
    signature: "m",
    renderInfo: { tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  pgflowlevelscope: {
    signature: "m",
    renderInfo: { tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  pgfviewboxscope: {
    signature: "m m m m m",
    renderInfo: { tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  pgftransparencygroup: {
    signature: "o",
    renderInfo: { pgfkeysArgs: true, tikzEnvironment: true },
    processContent: processTikzEnvironmentContent
  },
  behindforegroundpath: {
    signature: "m",
    processContent: processTikzEnvironmentContent
  },
  pgfmetadecoration: {
    signature: "m",
    processContent: processTikzEnvironmentContent
  },
  colormixin: { signature: "m", renderInfo: { pgfkeysArgs: true } }
};
function processTikzEnvironmentContent(nodes) {
  attachMacroArgsInArray(nodes, conditionalMacros);
  return nodes;
}
const conditionalMacros = {
  pgfextra: { signature: "m" },
  beginpgfgraphicnamed: { signature: "m" },
  pgfrealjobname: { signature: "m" },
  pgfplotstreampoint: { signature: "m" },
  pgfplotstreampointoutlier: { signature: "m" },
  pgfplotstreamspecial: { signature: "m" },
  pgfplotxyfile: { signature: "m" },
  pgfplotxyzfile: { signature: "m" },
  pgfplotfunction: { signature: "mmm" },
  pgfplotgnuplot: { signature: "o m" },
  pgfplothandlerrecord: { signature: "m" },
  pgfdeclareplothandler: { signature: "m m m" },
  pgfdeclarelayer: { signature: "m" },
  pgfsetlayers: { signature: "m", renderInfo: { pgfkeysArgs: true } },
  pgfonlayer: { signature: "m" },
  startpgfonlayer: { signature: "m" },
  pgfdeclarehorizontalshading: { signature: "o m m m " },
  pgfdeclareradialshading: { signature: "o m m m" },
  pgfdeclarefunctionalshading: { signature: "o m m m m m" },
  pgfshadecolortorgb: { signature: "m m" },
  pgfshadecolortocmyk: { signature: "m m" },
  pgfshadecolortogray: { signature: "m m" },
  pgfuseshading: { signature: "m" },
  pgfshadepath: { signature: "m m" },
  pgfsetadditionalshadetransform: { signature: "m" },
  pgfsetstrokeopacity: { signature: "m" },
  pgfsetfillopacity: { signature: "m" },
  pgfsetblendmode: { signature: "m" },
  pgfdeclarefading: { signature: "m m" },
  pgfsetfading: { signature: "m m" },
  pgfsetfadingforcurrentpath: { signature: "m m" },
  pgfsetfadingforcurrentpathstroked: { signature: "m m" },
  pgfanimateattribute: { signature: "m m" },
  pgfsnapshot: { signature: "m" },
  pgfqpoint: { signature: "m m" },
  pgfqpointxy: { signature: "m m" },
  pgfqpointxyz: { signature: "m m m" },
  pgfqpointscale: { signature: "m m" },
  pgfpathqmoveto: { signature: "m m" },
  pgfpathqlineto: { signature: "m m" },
  pgfpathqcurveto: { signature: "m m m m m m" },
  pgfpathqcircle: { signature: "m" },
  pgfqbox: { signature: "m" },
  pgfqboxsynced: { signature: "m" },
  pgfaliasimage: { signature: "m m" },
  pgfuseimage: { signature: "m" },
  pgfimage: { signature: "o m", renderInfo: { pgfkeysArgs: true } },
  pgfdeclaremask: { signature: "o m m", renderInfo: { pgfkeysArgs: true } },
  pgfdeclarepatternformonly: { signature: "o m m m m m" },
  pgfdeclarepatterninherentlycolored: { signature: "o m m m m m" },
  pgfsetfillpattern: { signature: "m m" },
  // Coordinate canvas and nonlinear transformations
  pgftransformshift: { signature: "m" },
  pgftransformxshift: { signature: "m" },
  pgftransformyshift: { signature: "m" },
  pgftransformscale: { signature: "m" },
  pgftransformxscale: { signature: "m" },
  pgftransformyscale: { signature: "m" },
  pgftransformxslant: { signature: "m" },
  pgftransformyslant: { signature: "m" },
  pgftransformrotate: { signature: "m" },
  pgftransformtriangle: { signature: "m m m" },
  pgftransformcm: { signature: "m m m m m" },
  pgftransformarrow: { signature: "m m" },
  pgftransformlineattime: { signature: "m m m" },
  pgftransformcurveattime: { signature: "m m m m m" },
  pgftransformarcaxesattime: { signature: "m m m m m m" },
  pgfgettransform: { signature: "m" },
  pgfsettransform: { signature: "m" },
  pgfgettransformentries: { signature: "m m m m m m" },
  pgfsettransformentries: { signature: "m m m m m m" },
  pgfpointtransformed: { signature: "m" },
  pgflowlevel: { signature: "m" },
  pgflowlevelobj: { signature: "m m" },
  pgflowlevelscope: { signature: "m" },
  startpgflowlevelscope: { signature: "m" },
  pgfviewboxscope: { signature: "m m m m m" },
  startpgfviewboxscope: { signature: "m m m m m" },
  pgftransformnonlinear: { signature: "m" },
  pgfpointtransformednonlinear: { signature: "m" },
  pgfsetcurvilinearbeziercurve: { signature: "m m m m" },
  pgfcurvilineardistancetotime: { signature: "m" },
  pgfpointcurvilinearbezierorthogonal: { signature: "m m" },
  pgfpointcurvilinearbezierpolar: { signature: "m m" },
  // Matrices
  pgfmatrix: { signature: "m m m m m m m" },
  pgfsetmatrixcolumnsep: { signature: "m" },
  pgfmatrixnextcell: { signature: "o" },
  pgfsetmatrixrowsep: { signature: "m" },
  pgfmatrixendrow: { signature: "o" },
  // Nodes and shapes
  pgfnode: { signature: "m m m m m" },
  pgfmultipartnode: { signature: "m m m m" },
  pgfcoordinate: { signature: "m m" },
  pgfnodealias: { signature: "m m" },
  pgfnoderename: { signature: "m m" },
  pgfpositionnodelater: { signature: "m" },
  pgfpositionnodenow: { signature: "m" },
  pgfnodepostsetupcode: { signature: "m m" },
  pgfpointanchor: { signature: "m m" },
  pgfpointshapeborder: { signature: "m m" },
  pgfdeclareshape: { signature: "m m" },
  saveddimen: { signature: "m m" },
  savedmacro: { signature: " m" },
  anchor: { signature: "m m" },
  deferredanchor: { signature: "m m" },
  anchorborder: { signature: "m" },
  backgroundpath: { signature: "m" },
  foregroundpath: { signature: "m" },
  behindbackgroundpath: { signature: "m" },
  beforebackgroundpath: { signature: "m" },
  beforeforegroundpath: { signature: "m" },
  behindforegroundpath: { signature: "m" },
  // Arrows
  pgfdeclarearrow: { signature: "m" },
  pgfarrowssettipend: { signature: "m" },
  pgfarrowssetbackend: { signature: "m" },
  pgfarrowssetlineend: { signature: "m" },
  pgfarrowssetvisualbackend: { signature: "m" },
  pgfarrowssetvisualtipend: { signature: "m" },
  pgfarrowshullpoint: { signature: "m m" },
  pgfarrowsupperhullpoint: { signature: "m m" },
  pgfarrowssave: { signature: "m" },
  pgfarrowssavethe: { signature: "m" },
  pgfarrowsaddtooptions: { signature: "m" },
  pgfarrowsaddtolateoptions: { signature: "m" },
  pgfarrowsaddtolengthscalelist: { signature: "m" },
  pgfarrowsaddtowidthscalelist: { signature: "m" },
  pgfarrowsthreeparameters: { signature: "m" },
  pgfarrowslinewidthdependent: { signature: "m m m" },
  pgfarrowslengthdependent: { signature: "m" },
  // Path
  pgfusepath: { signature: "m" },
  pgfsetlinewidth: { signature: "m" },
  pgfsetmiterlimit: { signature: "m" },
  pgfsetdash: { signature: "m m" },
  pgfsetstrokecolor: { signature: "m" },
  pgfsetcolor: { signature: "m" },
  pgfsetinnerlinewidth: { signature: "m" },
  pgfsetinnerstrokecolor: { signature: "m" },
  pgfsetarrowsstart: { signature: "m" },
  pgfsetarrowsend: { signature: "m" },
  pgfsetarrows: { signature: "m" },
  pgfsetshortenstart: { signature: "m" },
  pgfsetshortenend: { signature: "m" },
  pgfsetfillcolor: { signature: "m" },
  // Decorations
  pgfdeclaredecoration: { signature: "m m m" },
  state: { signature: "m o m" },
  pgfdecoratepath: { signature: "m m" },
  startpgfdecoration: { signature: "m" },
  pgfdecoration: { signature: "m" },
  pgfdecoratecurrentpath: { signature: "m" },
  pgfsetdecorationsegmenttransformation: { signature: "m" },
  pgfdeclaremetadecorate: { signature: "m m m" },
  pgfmetadecoration: { signature: "m" },
  startpgfmetadecoration: { signature: "m" },
  // Constructing paths
  pgfpathmoveto: { signature: "m" },
  pgfpathlineto: { signature: "m" },
  pgfpathcurveto: { signature: "m m m" },
  pgfpathquadraticcurveto: { signature: "m m" },
  pgfpathcurvebetweentime: { signature: "m m m m m m" },
  pgfpathcurvebetweentimecontinue: { signature: "m m m m m m" },
  pgfpatharc: { signature: "m m m" },
  pgfpatharcaxes: { signature: "m m m m" },
  pgfpatharcto: { signature: "m m m m m m" },
  pgfpatharctoprecomputed: { signature: "m m m m m m m m" },
  pgfpathellipse: { signature: "m m m" },
  pgfpathcircle: { signature: "m m" },
  pgfpathrectangle: { signature: "m m" },
  pgfpathrectanglecorners: { signature: "m m" },
  pgfpathgrid: { signature: " o m m" },
  pgfpathparabola: { signature: "m m" },
  pgfpathsine: { signature: "m" },
  pgfpathcosine: { signature: "m" },
  pgfsetcornersarced: { signature: "m" },
  "pgf@protocolsizes": { signature: "m m" },
  // Specifying coordinates
  pgfpoint: { signature: "m m" },
  pgfpointpolar: { signature: "m m m" },
  pgfpointxy: { signature: "m m" },
  pgfsetxvec: { signature: "m" },
  pgfsetyvec: { signature: "m" },
  pgfpointpolarxy: { signature: "m m" },
  pgfpointxyz: { signature: "m m m" },
  pgfsetzvec: { signature: "m" },
  pgfpointcylindrical: { signature: "m m m" },
  pgfpointspherical: { signature: "m m m" },
  pgfpointadd: { signature: "m m" },
  pgfpointscale: { signature: "m m" },
  pgfpointdiff: { signature: "m m" },
  pgfpointnormalised: { signature: "m" },
  pgfpointlineattime: { signature: "m m m" },
  pgfpointlineatdistance: { signature: "m m m" },
  pgfpointarcaxesattime: { signature: "m m m m m m" },
  pgfpointcurveattime: { signature: "m m m m m" },
  pgfpointborderrectangle: { signature: "m m" },
  pgfpointborderellipse: { signature: "m m" },
  pgfpointintersectionoflines: { signature: "m m m m" },
  pgfpointintersectionofcircles: { signature: "m m m m m" },
  pgfintersectionofpaths: { signature: "m m" },
  pgfpointintersectionsolution: { signature: "m" },
  pgfextractx: { signature: "m m" },
  pgfextracty: { signature: "m m" },
  pgfgetlastxy: { signature: "m m" },
  "pgf@process": { signature: "m" },
  // Heirarchical structres ...
  pgfsetbaseline: { signature: "m" },
  pgfsetbaselinepointnow: { signature: "m" },
  pgfsetbaselinepointlater: { signature: "m" },
  pgftext: { signature: "o m", renderInfo: { pgfkeysArgs: true } },
  pgfuseid: { signature: "m" },
  pgfusetype: { signature: "m" },
  pgfidrefnextuse: { signature: "m m" },
  pgfidrefprevuse: { signature: "m m" },
  pgfaliasid: { signature: "m m" },
  pgfgaliasid: { signature: "m m" },
  pgfifidreferenced: { signature: "m m m" },
  pgfrdfabout: { signature: "m" },
  pgfrdfcontent: { signature: "m" },
  pgfrdfdatatype: { signature: "m" },
  pgfrdfhref: { signature: "m" },
  pgfrdfprefix: { signature: "m" },
  pgfrdfproperty: { signature: "m" },
  pgfrdfrel: { signature: "m" },
  pgfrdfresource: { signature: "m" },
  pgfrdfrev: { signature: "m" },
  pgfrdfsrc: { signature: "m" },
  pgfrdftypeof: { signature: "m" },
  pgfrdfvocab: { signature: "m" },
  pgferror: { signature: "m" },
  pgfwarning: { signature: "m" },
  path: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  draw: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  fill: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  filldraw: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  pattern: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  shade: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  clip: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  useasboundingbox: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  node: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  coordinate: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  graph: {
    signature: "u;",
    renderInfo: { breakAround: true, tikzPathCommand: true }
  },
  scoped: {
    signature: "o o m",
    argumentParser: tikzCommandArgumentParser,
    renderInfo: {
      namedArguments: ["animation", "options", "command"],
      breakAround: true
    }
  }
};
function createMatchers() {
  return {
    isChar: match.string,
    isTerminal: (node) => match.string(node, ";"),
    isOperation: (node) => match.anyString(node) && node.content.match(/[a-zA-Z]/),
    isWhitespace: (node) => match.whitespace(node) || match.parbreak(node),
    isComment: match.comment,
    isGroup: match.group,
    isMacro: match.macro,
    isAnyMacro: match.anyMacro
  };
}
const matchers = createMatchers();
function parse(ast, options) {
  const { startRule = "path_spec" } = options || {};
  if (!Array.isArray(ast)) {
    throw new Error("You must pass an array of nodes");
  }
  ast = decorateArrayForPegjs([...ast]);
  return TikzPegParser.parse(ast, {
    ...matchers,
    startRule
  });
}
export {
  conditionalMacros as c,
  environments as e,
  macros as m,
  parse as p
};
//# sourceMappingURL=parser-BBXMi7mQ.js.map
