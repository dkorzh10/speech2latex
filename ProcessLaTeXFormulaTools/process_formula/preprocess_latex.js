
var katex = require('./third-party/katex/katex_dist/katex.js')

var readline = require('readline');

var rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
});


rl.on('line', function(line){
    a = line
    if (line[0] == "%") {
        line = line.substr(1, line.length - 1);
    }
    // line = line.split('%')[0];

    line = line.split('\\~').join(' ');

    for (var i = 0; i < 300; i++) {
        line = line.replace(/\\>/, " ");
        line = line.replace('$', ' ');
        line = line.replace(/\\label{.*?}/, "");
    }

    // if (line.indexOf("matrix") == -1 && line.indexOf("cases")==-1 &&
    //     line.indexOf("array")==-1 && line.indexOf("begin")==-1)  {
    //     for (var i = 0; i < 300; i++) {
    //         line = line.replace(/\\\\/, "\\");
    //     }
    // }


    line = line;
    // console.log("LINE", line);
    // global_str is tokenized version (build in parser.js)
    // norm_str is normalized version build by renderer below.
    try {
        if (process.argv[2] == "tokenize") {
            var tree = katex.__parse(line, {throwOnError: true});
            console.log(global_str.replace(/\\label { .*? }/, ""));
        } else {
            for (var i = 0; i < 300; ++i) {
                line = line.replace(/{\\rm/, "\\mathrm{");
                line = line.replace(/{ \\rm/, "\\mathrm{");
                line = line.replace(/\\rm{/, "\\mathrm{");
                if (line.indexOf("{\\rm")==-1 && line.indexOf("{ \\rm")==-1 && line.indexOf("\\rm{")==-1 ) {
                    break;
                }
            }

            var tree = katex.__parse(line, {throwOnError: true});
            // TODO
            // console.log("FULL_TREE", tree)
            buildExpression(tree, {});
            for (var i = 0; i < 300; ++i) {
                norm_str = norm_str.replace('SSSSSS', '$');
                norm_str = norm_str.replace(' S S S S S S', '$');
                norm_str = norm_str.replace('{ \\@not } =', '\\neq');
                if (line.indexOf("SSSSSS")==-1 && line.indexOf(" S S S S S S")==-1 && line.indexOf("{ \\@not } =")==-1 ) {
                    break;
                }
            }
            console.log(norm_str.replace(/\\label { .*? }/, ""));
        }
    } catch (e) {
        console.error(line);
        console.error(norm_str);
        console.error(e);
        console.log("");
    }
    global_str = ""
    norm_str = ""
    prev_end = 0
})



// This is a LaTeX AST to LaTeX Renderer (modified version of KaTeX AST-> MathML).
norm_str = ""
prev_end = 0

var groupTypes = {};

groupTypes.cr = function(group, options) {
    // do nothing
}


groupTypes.mathord = function(group, options) {
    if (options.font == "mathrm"){
        for (i = 0; i < group.length; ++i ) {
            if (group.text[i] == " ") {
                norm_str = norm_str + group.text[i] + "\; ";
            } else {
                norm_str = norm_str + group.text[i];
            }
        }
    } else {
        suffix = ' '
        if (group.text.startsWith('\\')) {
            suffix = '\\\\'
        }
        norm_str = norm_str + group.text + suffix;
    }
};

groupTypes.textord = function(group, options) {
    // suffix = '\\\\'
    suffix = ''
    norm_str = norm_str + group.text + suffix;
};

groupTypes.htmlmathml = function(group, options) {
    buildExpression(group.html)
};


groupTypes.bin = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.rel = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.open = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.close = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.inner = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.punct = function(group) {
    norm_str = norm_str + group.text;
};

groupTypes.ordgroup = function(group, options) {
    norm_str = norm_str + "{";

    buildExpression(group.body, options);

    norm_str = norm_str +  "}";
};

groupTypes.text = function(group, options) {

    // norm_str = norm_str + "\\text {";
    norm_str = norm_str + group.font + '{';

    for (var i = 0; i < group.body.length; i++) {
        if (typeof(group.body[i].text) !== 'undefined') {
            norm_str = norm_str + group.body[i].text;
        } else {
            buildGroup(group.body[i], options);
        }
    }

    // buildExpression(group.body, options);
    norm_str = norm_str + "}";
};

groupTypes.atom = function(group, options) {
    var atom_text = group.text;
    // if (atom_text === '\\@not') {
    //     atom_text = '\\neq'
    // }
    norm_str = norm_str + atom_text + " \\\\ ";
};

groupTypes.kern = function(group, options) {
    // norm_str = norm_str + " \\hspace{" + group.dimension.number + group.dimension.unit + "}";
};


groupTypes.color = function(group, options) {
    buildExpression(group.body, options);

    // var node = new mathMLTree.MathNode("mstyle", inner);

    // node.setAttribute("mathcolor", group.color);

    // return node;
};

groupTypes.supsub = function(group, options) {
    buildGroup(group.base, options);

    if (group.sub) {
        norm_str = norm_str + "_";
        if (group.sub.type != 'ordgroup') {
            norm_str = norm_str + "{";
            buildGroup(group.sub, options);
            norm_str = norm_str + "}";
        } else {
            buildGroup(group.sub, options);
        }

    }

    if (group.sup) {
        norm_str = norm_str + "^";
        if (group.sup.type != 'ordgroup') {
            norm_str = norm_str + "{";
            buildGroup(group.sup, options);
            norm_str = norm_str + "}";
        } else {
            buildGroup(group.sup, options);
        }
    }

};

groupTypes.genfrac = function(group, options) {
    if (!group.hasBarLine) {
        norm_str = norm_str + "\\binom ";
    } else {
        norm_str = norm_str + "\\frac ";
    }
    buildGroup(group.numer, options);
    buildGroup(group.denom, options);

};

groupTypes.array = function(group, options) {
    norm_str = norm_str + "\\begin{" + group.style + "}";

    if (group.style == "array" || group.style == "tabular") {
        norm_str = norm_str + "{";
        if (group.cols) {
            group.cols.map(function(start) {
                if (start) {
                    if (start.type == "align") {
                        norm_str = norm_str + start.align;
                    } else if (start.type == "separator") {
                        norm_str = norm_str + start.separator;
                    }
                }
            });
        } else {
            group.body[0].map(function(start) {
                norm_str = norm_str + "c ";
            } );
        }
        norm_str = norm_str + "}";
    }
    group.body.map(function(row) {
        if (row.length > 1 || row[0].value.length > 0) {
            if (row[0].value[0] && row[0].value[0].value == "\\hline") {
                norm_str = norm_str + "\\hline ";
                row[0].value = row[0].value.slice(1);
            }
            out = row.map(function(cell) {
                buildGroup(cell, options);
                norm_str = norm_str + "& ";
            });
            norm_str = norm_str.substring(0, norm_str.length-2) + "\\\\ ";
        }
    });
    norm_str = norm_str + "\\end{" + group.style + "}";
};

groupTypes.sqrt = function(group, options) {
    var node;
    if (group.index) {
        norm_str = norm_str + "\\sqrt [" + group.index + "]";
        buildGroup(group.body, options);
    } else {
        norm_str = norm_str + "\\sqrt";
        sqrt_body = group.body
        if (sqrt_body.type !== 'ordgroup') {
            sqrt_body = {
                type: 'ordgroup',
                mode: 'math',
                body: [sqrt_body]
            }
        }
        buildGroup(sqrt_body, options);
    }
};

groupTypes.leftright = function(group, options) {

    suffix = ''
    if (group.left.startsWith('\\')) {
        suffix = '\\\\'
    }

    norm_str = norm_str + "\\left" + group.left + suffix;
    buildExpression(group.body, options);
    norm_str = norm_str + "\\right" + group.right;
};

groupTypes.accent = function(group, options) {
    if (group.base.type != 'ordgroup') {
        norm_str = norm_str + group.label + "{";
        buildGroup(group.base, options);
        norm_str = norm_str + "}";
    } else {
        norm_str = norm_str + group.label;
        buildGroup(group.base, options);
    }
};

groupTypes.spacing = function(group) {
    var node;
    if (group.text == " ") {
        norm_str = norm_str + "~ ";
    } else {
        suffix = ''
        if (group.text.startsWith('\\')) {
            suffix = '\\\\'
        }

        norm_str = norm_str + group.text + suffix;
    }
    return node;
};

groupTypes.op = function(group, options) {
    if (typeof(group.name) !== 'undefined') {
        suffix = ' '
        if (group.name.startsWith('\\')) {
            suffix = '\\\\'
        }
        norm_str = norm_str + group.name + suffix;
    } else {
        buildExpression(group.body, options)
    }
};

groupTypes.operatorname = function(group, options) {
    norm_str = norm_str + "\\"
    for (var i = 0; i < group.body.length; i++) {
        var group_i = group.body[i];
        if (group_i.type === 'kern') {
            continue
        }
        // console.log("group_i", group_i)
        if ('loc' in group_i) {
            prev_end = group_i.loc.start
        }
        buildGroup(group_i, options);
    }
};

groupTypes.katex = function(group) {
    var node = new mathMLTree.MathNode(
        "mtext", [new mathMLTree.TextNode("KaTeX")]);

    return node;
};

groupTypes.mclass = function(group, options) {
    buildExpression(group.body, options)
};

groupTypes.lap = function(group, options) {
    buildGroup(group.body, options)
};


groupTypes.font = function(group, options) {
    var font = group.font;
    if (font == "mbox" || font == "hbox") {
        font = "mathrm";
    }
    norm_str = norm_str + "\\" + font + '\\\\';
    buildGroup(group.body, options);
};

groupTypes.delimsizing = function(group) {
    var children = [];
    norm_str = norm_str + group.delim + '\\\\';
};

groupTypes.styling = function(group, options) {
    norm_str = norm_str + group.original;
    buildExpression(group.value, options);

};

groupTypes.sizing = function(group, options) {

    if (group.original == "\\rm") {
        norm_str = norm_str + "\\mathrm {";
        buildExpression(group.value, options);
        norm_str = norm_str + "}";
    } else {
        norm_str = norm_str + group.original;
        buildExpression(group.value, options);
    }
};

groupTypes.overline = function(group, options) {
    norm_str = norm_str + "\\overline {";

    buildGroup(group.body, options);
    norm_str = norm_str + "}";
    norm_str = norm_str;

};

groupTypes.underline = function(group, options) {
    norm_str = norm_str + "\\underline {";
    buildGroup(group.body, options);
    norm_str = norm_str + "}";

    norm_str = norm_str;

};

groupTypes.rule = function(group) {
    norm_str = norm_str + "\\rule { "+group.width.number+" "+group.width.unit+"  } { "+group.height.number+" "+group.height.unit+ " } ";

};

groupTypes.llap = function(group, options) {
    norm_str = norm_str + "\\llap ";
    buildGroup(group.body, options);
};

groupTypes.rlap = function(group, options) {
    norm_str = norm_str + "\\rlap ";
    buildGroup(group.body, options);

};

groupTypes.phantom = function(group, options, prev) {
    norm_str = norm_str + "\\phantom {";
    buildExpression(group.value, options);
    norm_str = norm_str + "}";

};

/**
 * Takes a list of nodes, builds them, and returns a list of the generated
 * MathML nodes. A little simpler than the HTML version because we don't do any
 * previous-node handling.
 */
var buildExpression = function(expression, options) {
    var groups = [];
    for (var i = 0; i < expression.length; i++) {
        var group = expression[i];
        // console.log("group", i, group)
        buildGroup(group, options);
    }
    // console.log(norm_str);
    // return groups;
};

/**
 * Takes a group from the parser and calls the appropriate groupTypes function
 * on it to produce a MathML node.
 */
var buildGroup = function(group, options) {
    // console.error("group", group.type, group)
    if (groupTypes[group.type]) {
        if ('loc' in group && group.loc.start != prev_end) {
            norm_str += " "
        }

        groupTypes[group.type](group, options);

        if ('loc' in group) {
            prev_end = group.loc.end
        }
    } else {
        throw new Error(
            "Got group of unknown type: '" + group.type + "'");
    }
};



