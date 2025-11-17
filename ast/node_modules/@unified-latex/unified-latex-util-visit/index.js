import { match } from "@unified-latex/unified-latex-util-match";
function listMathChildren(node) {
  const NULL_RETURN = { enter: [], leave: [] };
  if (Array.isArray(node)) {
    return NULL_RETURN;
  }
  if (match.math(node)) {
    return { enter: ["content"], leave: [] };
  }
  const renderInfo = node._renderInfo || {};
  if (renderInfo.inMathMode == null) {
    return NULL_RETURN;
  }
  if (match.macro(node)) {
    if (renderInfo.inMathMode === true) {
      return { enter: ["args"], leave: [] };
    } else if (renderInfo.inMathMode === false) {
      return { enter: [], leave: ["args"] };
    }
  }
  if (match.environment(node)) {
    if (renderInfo.inMathMode === true) {
      return { enter: ["content"], leave: [] };
    } else {
      return { enter: [], leave: ["content"] };
    }
  }
  return NULL_RETURN;
}
const CONTINUE = Symbol("continue");
const SKIP = Symbol("skip");
const EXIT = Symbol("exit");
const DEFAULT_CONTEXT = {
  inMathMode: false,
  hasMathModeAncestor: false
};
function visit(tree, visitor, options) {
  const {
    startingContext = DEFAULT_CONTEXT,
    test = () => true,
    includeArrays = false
  } = options || {};
  let enter;
  let leave;
  if (typeof visitor === "function") {
    enter = visitor;
  } else if (visitor && typeof visitor === "object") {
    enter = visitor.enter;
    leave = visitor.leave;
  }
  walk(tree, {
    key: void 0,
    index: void 0,
    parents: [],
    containingArray: void 0,
    context: { ...startingContext }
  });
  function walk(node, { key, index, parents, context, containingArray }) {
    const nodePassesTest = includeArrays ? test(node, { key, index, parents, context, containingArray }) : !Array.isArray(node) && test(node, { key, index, parents, context, containingArray });
    const result = enter && nodePassesTest ? toResult(
      enter(node, {
        key,
        index,
        parents,
        context,
        containingArray
      })
    ) : [CONTINUE];
    if (result[0] === EXIT) {
      return result;
    }
    if (result[0] === SKIP) {
      return leave && nodePassesTest ? toResult(
        leave(node, {
          key,
          index,
          parents,
          context,
          containingArray
        })
      ) : result;
    }
    if (Array.isArray(node)) {
      for (let index2 = 0; index2 > -1 && index2 < node.length; index2++) {
        const item = node[index2];
        const result2 = walk(item, {
          key,
          index: index2,
          parents,
          context,
          containingArray: node
        });
        if (result2[0] === EXIT) {
          return result2;
        }
        if (typeof result2[1] === "number") {
          index2 = result2[1] - 1;
        }
      }
    } else {
      let childProps = ["content", "args"];
      switch (node.type) {
        case "macro":
          childProps = ["args"];
          break;
        case "comment":
        case "string":
        case "verb":
        case "verbatim":
          childProps = [];
          break;
      }
      const mathModeProps = listMathChildren(node);
      for (const key2 of childProps) {
        const value = node[key2];
        const grandparents = [node].concat(parents);
        if (value == null) {
          continue;
        }
        const newContext = { ...context };
        if (mathModeProps.enter.includes(key2)) {
          newContext.inMathMode = true;
          newContext.hasMathModeAncestor = true;
        } else if (mathModeProps.leave.includes(key2)) {
          newContext.inMathMode = false;
        }
        const result2 = walk(value, {
          key: key2,
          index: void 0,
          parents: grandparents,
          context: newContext,
          containingArray: void 0
        });
        if (result2[0] === EXIT) {
          return result2;
        }
      }
    }
    return leave && nodePassesTest ? toResult(
      leave(node, {
        key,
        index,
        parents,
        context,
        containingArray
      })
    ) : result;
  }
}
function toResult(value) {
  if (value == null) {
    return [CONTINUE];
  }
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === "number") {
    return [CONTINUE, value];
  }
  return [value];
}
export {
  CONTINUE,
  EXIT,
  SKIP,
  visit
};
//# sourceMappingURL=index.js.map
