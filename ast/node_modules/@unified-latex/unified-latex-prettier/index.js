var __typeError = (msg) => {
  throw TypeError(msg);
};
var __accessCheck = (obj, member, msg) => member.has(obj) || __typeError("Cannot " + msg);
var __privateGet = (obj, member, getter) => (__accessCheck(obj, member, "read from private field"), getter ? getter.call(obj) : member.get(obj));
var __privateAdd = (obj, member, value) => member.has(obj) ? __typeError("Cannot add the same private member more than once") : member instanceof WeakSet ? member.add(obj) : member.set(obj, value);
var __privateSet = (obj, member, value, setter) => (__accessCheck(obj, member, "write to private field"), setter ? setter.call(obj, value) : member.set(obj, value), value);
var _path, _print;
import { builders } from "prettier/doc";
import { printRaw, linebreak } from "@unified-latex/unified-latex-util-print-raw";
import { match } from "@unified-latex/unified-latex-util-match";
import { trim } from "@unified-latex/unified-latex-util-trim";
import { parse } from "@unified-latex/unified-latex-ctan/package/tikz";
import { parsePgfkeys } from "@unified-latex/unified-latex-util-pgfkeys";
import { parseAlignEnvironment } from "@unified-latex/unified-latex-util-align";
import { visit } from "@unified-latex/unified-latex-util-visit";
import { parse as parse$1 } from "@unified-latex/unified-latex-util-parse";
function formatEnvSurround(node) {
  const env = printRaw(node.env);
  return {
    envName: env,
    start: ESCAPE + "begin{" + env + "}",
    end: ESCAPE + "end{" + env + "}"
  };
}
function isLineType(elm) {
  if (elm == null || typeof elm === "string") {
    return false;
  }
  if (Array.isArray(elm)) {
    return isLineType(elm[0]);
  }
  if (elm.type === "concat") {
    return isLineType(elm.parts);
  }
  return elm.type === "line";
}
function joinWithSoftline(arr) {
  if (arr.length === 0 || arr.length === 1) {
    return arr;
  }
  const ret = [arr[0]];
  for (let i = 1; i < arr.length; i++) {
    const prevNode = arr[i - 1];
    const nextNode = arr[i];
    if (!isLineType(prevNode) && !isLineType(nextNode)) {
      ret.push(softline);
    }
    ret.push(nextNode);
  }
  return ret;
}
function getNodeInfo(node, options) {
  if (!node) {
    return { renderInfo: {} };
  }
  const renderInfo = node._renderInfo || {};
  const previousNode = options.referenceMap && options.referenceMap.getPreviousNode(node);
  const nextNode = options.referenceMap && options.referenceMap.getNextNode(node);
  const renderCache = options.referenceMap && options.referenceMap.getRenderCache(node);
  return {
    renderInfo,
    renderCache,
    previousNode,
    nextNode,
    referenceMap: options.referenceMap
  };
}
const ESCAPE = "\\";
const {
  group,
  fill,
  ifBreak,
  line,
  softline,
  hardline,
  lineSuffix,
  lineSuffixBoundary,
  breakParent,
  indent,
  markAsRoot,
  join
} = builders;
function formatDocArray(nodes, docArray, options) {
  const ret = [];
  for (let i = 0; i < nodes.length; i++) {
    const rawNode = nodes[i];
    const printedNode = docArray[i];
    const { renderInfo, referenceMap, previousNode, nextNode } = getNodeInfo(rawNode, options);
    const renderCache = referenceMap && referenceMap.getRenderCache(rawNode);
    switch (rawNode.type) {
      case "comment":
        if (!rawNode.sameline && previousNode && !match.comment(previousNode) && !match.parbreak(previousNode)) {
          ret.push(hardline);
        }
        ret.push(printedNode);
        if (nextNode && !rawNode.suffixParbreak) {
          ret.push(hardline);
        }
        break;
      case "environment":
      case "displaymath":
      case "mathenv":
        if (previousNode && (previousNode == null ? void 0 : previousNode.type) !== "parbreak") {
          if (ret[ret.length - 1] === line) {
            ret.pop();
          }
          if (ret[ret.length - 1] !== hardline) {
            ret.push(hardline);
          }
        }
        ret.push(printedNode);
        if ((nextNode == null ? void 0 : nextNode.type) === "whitespace") {
          ret.push(hardline);
          i++;
        }
        break;
      case "macro":
        if (renderInfo.breakBefore || renderInfo.breakAround) {
          if (previousNode) {
            if (ret[ret.length - 1] === line || ret[ret.length - 1] === hardline) {
              ret.pop();
              ret.push(hardline);
            } else if (!match.comment(previousNode) && !match.parbreak(previousNode)) {
              ret.push(hardline);
            }
          }
        }
        if (renderInfo.inParMode && !renderInfo.hangingIndent && renderCache) {
          ret.push(
            renderCache.content,
            ...renderCache.rawArgs || []
          );
        } else {
          ret.push(printedNode);
        }
        if (renderInfo.breakAfter || renderInfo.breakAround) {
          if (nextNode) {
            if (match.whitespace(nextNode)) {
              ret.push(hardline);
              i++;
            } else if (match.parbreak(nextNode)) ;
            else if (!match.comment(nextNode)) {
              ret.push(hardline);
            }
          }
        }
        break;
      case "parbreak":
        ret.push(hardline, hardline);
        break;
      default:
        ret.push(printedNode);
        break;
    }
  }
  return ret;
}
function zip(array1, array2) {
  const ret = [];
  const len = Math.min(array1.length, array2.length);
  for (let i = 0; i < len; i++) {
    ret.push([array1[i], array2[i]]);
  }
  return ret;
}
function printMacro(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  const content = (node.escapeToken != null ? node.escapeToken : ESCAPE) + node.content;
  const args = node.args ? path.map(print, "args") : [];
  const rawArgs = [];
  for (const [arg, printedArg] of zip(node.args || [], args)) {
    const renderCache = referenceMap && referenceMap.getRenderCache(arg);
    if (renderInfo.inParMode && renderCache) {
      rawArgs.push(...renderCache);
    } else {
      rawArgs.push(printedArg);
    }
  }
  if (referenceMap) {
    referenceMap.setRenderCache(node, { rawArgs, content });
  }
  if (renderInfo.hangingIndent) {
    return indent(fill([content, ...rawArgs]));
  }
  return group([content, ...rawArgs]);
}
function printArgumentPgfkeys(nodes, options) {
  const { allowParenGroups = false } = options;
  const parsed = parsePgfkeys(nodes, { allowParenGroups });
  const content = [];
  for (const part of parsed) {
    const isLastItem = part === parsed[parsed.length - 1];
    if (part.itemParts) {
      const parts = part.itemParts.map(
        (node) => printRaw(node, { asArray: true }).map(
          (token) => token === linebreak ? hardline : token
        )
      );
      const row = join("=", parts);
      content.push(row);
      if (part.trailingComma) {
        content.push(",");
      }
    }
    if (part.trailingComment) {
      const leadingContent = part.itemParts ? [" "] : [];
      if (part.leadingParbreak) {
        leadingContent.push(hardline);
      }
      content.push(
        ...leadingContent,
        // We're carefully and manually controlling the newlines,
        // so print the comment directly without any newlines
        "%",
        part.trailingComment.content,
        breakParent
      );
    }
    if (!isLastItem) {
      content.push(line);
    }
  }
  let leadingComment = [""];
  if (options.leadingComment) {
    if (options.leadingComment.leadingWhitespace) {
      leadingComment.push(" ");
    }
    leadingComment.push("%" + options.leadingComment.content, breakParent);
  }
  return group([
    options.openMark,
    ...leadingComment,
    // If there is no content, we don't want to push an extra `softline`.
    // This matters because the braces group could still be broken by `leadingComment`
    content.length > 0 ? indent([softline, ...content]) : "",
    softline,
    options.closeMark
  ]);
}
function printTikzArgument(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  const content = [];
  const nodes = [...node.content];
  trim(nodes);
  try {
    const tikzAst = parse(nodes);
    if (tikzAst.content.length === 0) {
      content.push(";");
      return content;
    }
    const printer = new TikzArgumentPrinter(tikzAst, path, print);
    return printer.toDoc();
  } catch (e) {
    console.warn("Encountered error when trying to parse tikz argument", e);
  }
  content.push(";");
  return content;
}
function printFragment(fragment, path, print) {
  const tmpKey = Symbol();
  const currNode = path.getNode();
  if (!currNode) {
    throw new Error(
      "tried to print a fragment, but the current node is `null`"
    );
  }
  currNode[tmpKey] = fragment;
  const ret = print(tmpKey);
  delete currNode[tmpKey];
  return ret;
}
function printTikzPathSpecNode(node, path, print) {
  switch (node.type) {
    case "comment":
      return printFragment(node, path, print);
    case "unknown":
      return printFragment(node.content, path, print);
    case "coordinate":
      return [printRaw(node.prefix), "(", printRaw(node.content), ")"];
    case "line_to":
      return node.command;
    case "square_brace_group":
      return printOptionalArgs(node.content);
    case "operation":
      return node.content.content;
    case "svg_operation": {
      const comments = node.comments.map(
        (n) => printTikzPathSpecNode(n, path, print)
      );
      const options = node.options ? printOptionalArgs(node.options) : [];
      const rest = node.options ? [group(indent([line, printRaw(node.content)]))] : [" ", printRaw(node.content)];
      return [...comments, "svg", options, ...rest];
    }
    case "curve_to": {
      const comments = node.comments.map(
        (n) => printTikzPathSpecNode(n, path, print)
      );
      const printedControls = node.controls.length > 1 ? [
        printTikzPathSpecNode(node.controls[0], path, print),
        " ",
        "and",
        line,
        printTikzPathSpecNode(node.controls[1], path, print)
      ] : [printTikzPathSpecNode(node.controls[0], path, print)];
      return [
        ...comments,
        "..",
        " ",
        group(
          indent(["controls", line, ...printedControls, " ", ".."])
        )
      ];
    }
    case "animation": {
      const comments = node.comments.map(
        (n) => printTikzPathSpecNode(n, path, print)
      );
      return [
        ...comments,
        ":",
        node.attribute,
        " ",
        "=",
        " ",
        group(
          indent([
            printArgumentPgfkeys(node.content, {
              openMark: "{",
              closeMark: "}"
            })
          ])
        )
      ];
    }
    case "foreach": {
      const comments = node.comments.map(
        (n) => printTikzPathSpecNode(n, path, print)
      );
      const variables = [...node.variables];
      trim(variables);
      const list = node.list.type === "macro" ? printFragment(node.list, path, print) : printArgumentPgfkeys(node.list.content, {
        openMark: "{",
        closeMark: "}",
        allowParenGroups: true
      });
      const doc = [
        ...comments,
        printRaw(node.start),
        " ",
        printRaw(variables)
      ];
      if (node.options) {
        doc.push(" ", indent(printOptionalArgs(node.options)));
      }
      doc.push(" ", "in", " ", group(indent(list)));
      const commandType = node.command.type;
      switch (commandType) {
        case "foreach":
          doc.push(
            indent([
              line,
              printTikzPathSpecNode(node.command, path, print)
            ])
          );
          break;
        case "macro":
          doc.push(
            indent([line, printFragment(node.command, path, print)])
          );
          break;
        case "group": {
          const groupContent = [...node.command.content];
          trim(groupContent);
          doc.push(
            " ",
            indent(
              group([
                "{",
                indent([
                  softline,
                  ...groupContent.map(
                    (n) => printFragment(n, path, print)
                  )
                ]),
                softline,
                "}"
              ])
            )
          );
          break;
        }
        default:
          const invalidType = commandType;
          console.warn(
            `Unhandled command type when printing "foreach": ${invalidType}`
          );
      }
      return indent(doc);
    }
  }
  console.warn(
    `Encountered unknown type when trying to print tikz PathSpec: "${node.type}"`
  );
  return [];
}
function printOptionalArgs(nodes) {
  return printArgumentPgfkeys(nodes, {
    openMark: "[",
    closeMark: "]"
  });
}
class TikzArgumentPrinter {
  constructor(spec, path, print) {
    __privateAdd(this, _path);
    __privateAdd(this, _print);
    __privateSet(this, _path, path);
    __privateSet(this, _print, print);
    this.nodes = [...spec.content];
  }
  nodeToDoc(node) {
    return printTikzPathSpecNode(node, __privateGet(this, _path), __privateGet(this, _print));
  }
  toDoc() {
    const doc = [];
    const startArg = this.eatOptionalArg();
    if (startArg.optionalArg) {
      doc.push(
        ...startArg.comments.map(
          (c) => printFragment(c, __privateGet(this, _path), __privateGet(this, _print))
        )
      );
      doc.push(printOptionalArgs(startArg.optionalArg.content));
    }
    const innerDoc = [];
    doc.push(group([indent(innerDoc), ";"]));
    let cycle = -1;
    while (this.nodes.length > 0) {
      cycle++;
      const firstSep = cycle === 0 && !startArg.optionalArg ? " " : line;
      const comingUp = this.peek();
      switch (comingUp) {
        case "short_path": {
          const [n0, n1, n2] = this.nodes.splice(0, 3);
          innerDoc.push(
            firstSep,
            this.nodeToDoc(n0),
            " ",
            this.nodeToDoc(n1),
            " ",
            this.nodeToDoc(n2)
          );
          continue;
        }
        case "long_path": {
          const [n0, n1] = this.nodes.splice(0, 2);
          if (n1.type === "operation") {
            this.nodes.unshift(n1);
            innerDoc.push(
              firstSep,
              this.nodeToDoc(n0),
              " ",
              this.eatOperation()
            );
          } else {
            innerDoc.push(
              firstSep,
              this.nodeToDoc(n0),
              " ",
              this.nodeToDoc(n1)
            );
          }
          continue;
        }
        case "node":
          {
            const eatenNode = this.eatNode();
            if (eatenNode) {
              innerDoc.push(line, ...eatenNode);
              continue;
            }
            console.warn(
              "Expected to print a tikz `node` PathSpec but couldn't find the text `node`"
            );
          }
          continue;
        case "operation":
          innerDoc.push(firstSep, this.eatOperation());
          continue;
        case "unknown": {
          const node = this.nodes.shift();
          innerDoc.push(firstSep, this.nodeToDoc(node));
          continue;
        }
      }
      this.nodes.shift();
    }
    return doc;
  }
  /**
   * Look at the current node and the nodes that follow. Return what
   * "type" is recognized.
   */
  peek() {
    const [n0, n1, n2, n3] = [
      this.nodes[0],
      this.nodes[1],
      this.nodes[2],
      this.nodes[3]
    ];
    if ((n0 == null ? void 0 : n0.type) === "coordinate" && isPathJoinOperation(n1)) {
      if ((n2 == null ? void 0 : n2.type) === "coordinate" && !((n3 == null ? void 0 : n3.type) === "coordinate" || isPathJoinOperation(n3))) {
        return "short_path";
      }
      return "long_path";
    }
    if ((n0 == null ? void 0 : n0.type) === "operation") {
      if (n0.content.content === "node") {
        return "node";
      }
      return "operation";
    }
    return "unknown";
  }
  /**
   * Eat comments and an optional arg if present. If no optional
   * arg is present, do nothing.
   */
  eatOptionalArg() {
    let i = 0;
    const comments = [];
    let optionalArg = null;
    for (; i < this.nodes.length; i++) {
      const node = this.nodes[i];
      if (node.type === "square_brace_group") {
        optionalArg = node;
        i++;
        break;
      }
      if (node.type === "comment") {
        comments.push(node);
        continue;
      }
      break;
    }
    if (optionalArg) {
      this.nodes.splice(0, i);
    }
    return { optionalArg, comments };
  }
  /**
   * Eat a `type === "operation"` node whose contents is `"node"`. I.e.,
   * the type of thing that shows up in `\path node at (1,1) {foo};`
   */
  eatNode() {
    const firstNode = this.nodes[0];
    if ((firstNode == null ? void 0 : firstNode.type) === "operation" && firstNode.content.content === "node") {
      this.nodes.shift();
    } else {
      return null;
    }
    const innerDoc = [];
    const commentBlock = [];
    const doc = [commentBlock, "node", group(indent(innerDoc))];
    let hasNodeArgument = false;
    let shouldBail = false;
    let i = 0;
    const comments = [];
    const options = [];
    const name = [];
    const atLocations = [];
    const animations = [];
    let content = [];
    for (; i < this.nodes.length && !shouldBail; i++) {
      const node = this.nodes[i];
      switch (node.type) {
        case "animation":
          animations.push(this.nodeToDoc(node));
          continue;
        case "comment": {
          const comment = {
            ...node,
            leadingWhitespace: false
          };
          comments.push(this.nodeToDoc(comment));
          continue;
        }
        case "square_brace_group":
          options.push(printOptionalArgs(node.content));
          continue;
        case "coordinate":
          name.push(this.nodeToDoc(node));
          continue;
        case "operation": {
          if (node.content.content === "at") {
            const nextNode = this.nodes[i + 1];
            if (!nextNode || !(nextNode.type === "coordinate" || nextNode.type === "unknown" && match.anyMacro(nextNode.content))) {
              shouldBail = true;
              continue;
            }
            atLocations.push(["at", " ", this.nodeToDoc(nextNode)]);
            i++;
            continue;
          }
          shouldBail = true;
          continue;
        }
        case "unknown": {
          if (match.group(node.content)) {
            hasNodeArgument = true;
            content = this.nodeToDoc(node);
          }
        }
      }
      break;
    }
    if (!hasNodeArgument) {
      return innerDoc;
    }
    this.nodes.splice(0, i + 1);
    let isFirstElement = true;
    let isNamed = !(Array.isArray(name) && name.length === 0);
    for (const comment of comments) {
      commentBlock.push(comment, hardline);
    }
    if (options.length > 0) {
      innerDoc.push(join(" ", options));
      isFirstElement = false;
    }
    if (animations.length > 0) {
      innerDoc.push(isFirstElement ? " " : line);
      innerDoc.push(join(line, animations));
      isFirstElement = false;
    }
    if (isNamed) {
      innerDoc.push(isFirstElement ? " " : line);
      innerDoc.push(name);
      isFirstElement = false;
    }
    if (atLocations.length > 0) {
      innerDoc.push(isFirstElement || isNamed ? " " : line);
      innerDoc.push(join(line, atLocations));
      isFirstElement = false;
    }
    innerDoc.push(line, content);
    return doc;
  }
  /**
   * Eat a `type === "operation"` node, including its optional arguments.
   */
  eatOperation() {
    const node = this.nodes[0];
    if ((node == null ? void 0 : node.type) === "operation") {
      this.nodes.shift();
    } else {
      return [];
    }
    const doc = [];
    if ((node == null ? void 0 : node.type) !== "operation") {
      throw new Error("Expecting `operation` node.");
    }
    const options = this.eatOptionalArg();
    doc.push(
      ...options.comments.map(
        (c) => printFragment(c, __privateGet(this, _path), __privateGet(this, _print))
      ),
      node.content.content
    );
    if (options.optionalArg) {
      doc.push(indent(printOptionalArgs(options.optionalArg.content)));
    }
    return doc;
  }
}
_path = new WeakMap();
_print = new WeakMap();
const PATH_JOIN_OPERATIONS = /* @__PURE__ */ new Set(["rectangle", "grid", "sin", "cos", "to"]);
function isPathJoinOperation(node) {
  if (!node) {
    return false;
  }
  switch (node.type) {
    case "line_to":
    case "curve_to":
      return true;
    case "operation":
      return PATH_JOIN_OPERATIONS.has(node.content.content);
  }
  return false;
}
function printArgument(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  if (node.openMark === "" && node.closeMark === "" && node.content.length === 0) {
    return [];
  }
  const parentNode = path.getParentNode();
  const { renderInfo: parentRenderInfo } = getNodeInfo(parentNode, options);
  if (parentRenderInfo.pgfkeysArgs) {
    const leadingComment = node.content.length > 0 && match.comment(node.content[0]) && node.content[0].sameline ? node.content[0] : null;
    const content2 = leadingComment ? node.content.slice(1) : node.content;
    trim(content2);
    return printArgumentPgfkeys(content2, {
      openMark: node.openMark,
      closeMark: node.closeMark,
      leadingComment
    });
  }
  if (parentRenderInfo.tikzPathCommand) {
    return printTikzArgument(path, print, options);
  }
  const openMark = node.openMark;
  const closeMark = node.closeMark;
  let content = path.map(print, "content");
  content = formatDocArray(node.content, content, options);
  if (match.comment(node.content[node.content.length - 1])) {
    content.push(hardline);
  }
  let rawRet = [openMark, fill(content), closeMark];
  if (renderInfo.inParMode) {
    rawRet = [openMark, ...content, closeMark];
  }
  if (referenceMap) {
    referenceMap.setRenderCache(node, rawRet);
  }
  return rawRet;
}
function hasPreambleCode(nodes) {
  return nodes.some((node) => match.macro(node, "documentclass"));
}
function printRoot(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  const content = path.map(print, "content");
  const rawContent = formatDocArray(node.content, content, options);
  const concatFunction = hasPreambleCode(node.content) ? (x) => x : fill;
  return concatFunction(rawContent);
}
function printComment(path, _print2, _options) {
  const node = path.getNode();
  let leadingWhitespace = "";
  if (node.leadingWhitespace && node.sameline) {
    leadingWhitespace = " ";
  }
  const content = [leadingWhitespace, "%" + printRaw(node.content)];
  return content;
}
function printInlineMath(path, print, options) {
  const node = path.getNode();
  if (node.content.length === 0) {
    return ["$", " ", "$"];
  }
  let content = path.map(print, "content");
  content = formatDocArray(node.content, content, options);
  content = joinWithSoftline(content);
  if (node.content[node.content.length - 1].type === "comment") {
    content.push(hardline);
  }
  return fill(["$", ...content, "$"]);
}
function printDisplayMath(path, print, options) {
  const node = path.getNode();
  let content = path.map(print, "content");
  content = formatDocArray(node.content, content, options);
  content = joinWithSoftline(content);
  const bodyStartToken = [hardline];
  if (node.content.length === 0 || node.content[0].type === "comment" && node.content[0].sameline) {
    bodyStartToken.pop();
  }
  return [
    ESCAPE + "[",
    indent(fill(bodyStartToken.concat(content))),
    hardline,
    ESCAPE + "]"
  ];
}
function printVerbatimEnvironment(path, print, options) {
  const node = path.getNode();
  const env = formatEnvSurround(node);
  return [env.start, node.content, env.end];
}
function printEnvironment(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  const args = node.args ? path.map(print, "args") : [];
  const env = formatEnvSurround(node);
  let content = path.map(print, "content");
  content = formatDocArray(node.content, content, options);
  if (renderInfo.inMathMode) {
    content = joinWithSoftline(content);
  }
  let bodyStartToken = [hardline];
  if (node.content.length === 0 || node.content[0].type === "comment" && node.content[0].sameline) {
    bodyStartToken.pop();
  }
  return [
    env.start,
    ...args,
    indent(fill(bodyStartToken.concat(content))),
    hardline,
    env.end
  ];
}
function printAlignedEnvironment(path, print, options) {
  const node = path.getNode();
  const { renderInfo, previousNode, nextNode, referenceMap } = getNodeInfo(
    node,
    options
  );
  const args = node.args ? path.map(print, "args") : [];
  const env = formatEnvSurround(node);
  const leadingComment = node.content[0] && node.content[0].type === "comment" && node.content[0].sameline ? node.content[0] : null;
  const { rows, rowSeps, trailingComments } = formatAlignedContent(
    leadingComment ? node.content.slice(1) : node.content
  );
  const content = [];
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const rowSep = rowSeps[i];
    const trailingComment = trailingComments[i];
    content.push(row);
    if (rowSep) {
      content.push(printRaw(rowSep));
    }
    if (rowSep && trailingComment) {
      content.push(" ");
    }
    if (trailingComment) {
      content.push(["%", printRaw(trailingComment.content)]);
    }
    if (rowSep || trailingComment) {
      content.push(hardline);
    }
  }
  if (content[content.length - 1] === hardline) {
    content.pop();
  }
  if (leadingComment) {
    content.unshift(
      leadingComment.leadingWhitespace ? " " : "",
      "%" + printRaw(leadingComment.content),
      hardline
    );
    return [env.start, ...args, indent(content), hardline, env.end];
  }
  return [
    env.start,
    ...args,
    indent([hardline, ...content]),
    hardline,
    env.end
  ];
}
function formatAlignedContent(nodes) {
  function getSpace(len = 1) {
    return " ".repeat(len);
  }
  const rows = parseAlignEnvironment(nodes);
  const numCols = Math.max(...rows.map((r) => r.cells.length));
  const rowSeps = rows.map(({ rowSep }) => printRaw(rowSep || []));
  const trailingComments = rows.map(({ trailingComment }) => trailingComment);
  const renderedRows = rows.map(({ cells, colSeps }) => ({
    cells: cells.map((nodes2) => {
      trim(nodes2);
      return printRaw(nodes2);
    }),
    seps: colSeps.map((nodes2) => printRaw(nodes2))
  }));
  const colWidths = [];
  for (let i = 0; i < numCols; i++) {
    colWidths.push(
      Math.max(
        ...renderedRows.map(
          ({ cells, seps }) => ((cells[i] || "") + (seps[i] || "")).length
        )
      )
    );
  }
  const joinedRows = renderedRows.map(({ cells, seps }) => {
    if (cells.length === 1 && cells[0] === "") {
      return "";
    }
    let ret = "";
    for (let i = 0; i < cells.length; i++) {
      const width = colWidths[i] - (seps[i] || "").length;
      ret += (i === 0 ? "" : " ") + cells[i] + getSpace(width - cells[i].length + 1) + (seps[i] || "");
    }
    return ret;
  });
  return { rows: joinedRows, rowSeps, trailingComments };
}
class ReferenceMap {
  constructor(ast) {
    this.ast = ast;
    this.map = /* @__PURE__ */ new Map();
    visit(
      this.ast,
      (nodeList) => {
        for (let i = 0; i < nodeList.length; i++) {
          this.map.set(nodeList[i], {
            previous: nodeList[i - 1],
            next: nodeList[i + 1]
          });
        }
      },
      { includeArrays: true, test: Array.isArray }
    );
  }
  /**
   * Associate render-specific data with this node. This data
   * will be overwritten if `setRenderCache` is called twice.
   *
   * @param {Ast.Ast} node
   * @param {*} data
   * @memberof ReferenceMap
   */
  setRenderCache(node, data) {
    const currData = this.map.get(node) || {};
    this.map.set(node, { ...currData, renderCache: data });
  }
  /**
   * Retrieve data associated with `node` via `setRenderCache`
   *
   * @param {Ast.Ast} node
   * @returns {(object | undefined)}
   * @memberof ReferenceMap
   */
  getRenderCache(node) {
    var _a;
    return (_a = this.map.get(node)) == null ? void 0 : _a.renderCache;
  }
  getPreviousNode(node) {
    return (this.map.get(node) || {}).previous;
  }
  getNextNode(node) {
    return (this.map.get(node) || {}).next;
  }
}
function printLatexAst(path, options, print) {
  const node = path.getValue();
  const { renderInfo } = getNodeInfo(node, options);
  if (node == null) {
    return node;
  }
  if (typeof node === "string") {
    return node;
  }
  switch (node.type) {
    case "root":
      if (options.referenceMap) {
        console.warn(
          "Processing root node, but ReferenceMap already exists. Are there multiple nodes of type 'root'?"
        );
      }
      options.referenceMap = new ReferenceMap(node);
      return printRoot(path, print, options);
    case "argument":
      return printArgument(path, print, options);
    case "comment":
      return printComment(path);
    case "environment":
    case "mathenv":
      if (renderInfo.alignContent) {
        return printAlignedEnvironment(path, print, options);
      }
      return printEnvironment(path, print, options);
    case "displaymath":
      return printDisplayMath(path, print, options);
    case "group":
      const content = printRaw(node.content, {
        asArray: true
      }).map((token) => token === linebreak ? hardline : token);
      return ["{", ...content, "}"];
    case "inlinemath":
      return printInlineMath(path, print, options);
    case "macro":
      return printMacro(path, print, options);
    case "parbreak":
      return [hardline, hardline];
    case "string":
      return node.content;
    case "verb":
      return [
        ESCAPE,
        node.env,
        node.escape,
        printRaw(node.content),
        node.escape
      ];
    case "verbatim":
      return printVerbatimEnvironment(path);
    case "whitespace":
      return line;
    default:
      console.warn(`Printing unknown type ${readableType(node)}`, node);
      return printRaw(node);
  }
}
function readableType(obj) {
  if (obj == null) {
    return "null";
  }
  if (Array.isArray(obj)) {
    return "array";
  }
  return typeof obj;
}
const languages = [
  {
    name: "latex",
    extensions: [".tex"],
    parsers: ["latex-parser"]
  }
];
const parsers = {
  "latex-parser": {
    parse: parse$1,
    astFormat: "latex-ast",
    locStart: (node) => node.position ? node.position.start.offset : 0,
    locEnd: (node) => node.position ? node.position.end.offset : 1
  }
};
const printers = {
  "latex-ast": {
    print: printLatexAst
  }
};
const prettierPluginLatex = { languages, parsers, printers };
export {
  prettierPluginLatex,
  printLatexAst,
  printLatexAst as printer
};
//# sourceMappingURL=index.js.map
