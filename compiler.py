import re

filename = "equilibrium"

localList = "⌊LOCAL"
stackList = "⌊STACK"
subReturn = "R"

labels = set()
if True:
    allowed = "θABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for c in allowed:
        labels.add(c)
        for d in allowed:
            labels.add(c+d)

labels.remove(subReturn)

labelIndex = 0
labelIndexLookup = {}
# gets a new label for a section and returns it
#  must call this to update the return from subroutine logic
def getLabel():
    global labelIndex
    global labelIndexLookup
    label = labels.pop()
    labelIndexLookup[label] = labelIndex
    labelIndexLookup[labelIndex] = label
    labelIndex += 1
    return label

program = ""
with open(f"{filename}.txt", "r", encoding="utf8") as f:
    program = f.read()

# Def (.*?)\((.*?)\)\n([^\0]*?)\nEnd \1
# Group 1 = function name
# Group 2 = params (still a string)
# Group 3 = function body
funcFinder = re.compile("Def (\\S*?)\\((.*?)\\)\\n([^\\0]*?)\\nEnd \\1")

# Local (\S*?) *= *(.*)
# Group 1 = variable name
# Group 2 = expression
localParser = re.compile("Var (\\S*?) *= *(.*)")

# ([A-Za-z0-9.()]+) *(.) *
# Attempt 2: ([A-Za-z0-9.()]+) *([^A-Za-z0-9.()]) *
# Group 1 = variable/const
# Group 2 = operator
# Once a match fails, the remaining string(.strip()) is a variable/const
exprParseStep = re.compile("([A-Za-z0-9.()]+) *([^A-Za-z0-9.()]) *")

# Call (\S*?)\((.*?)\)
# Group 1 = function name
# Group 2 = params
funcCallParse = re.compile("Call (\\S*?)\\((.*?)\\)")

matches = funcFinder.findall(program)

# splits the list of params of a function into a list of string parameter names
def parseParams(params: str) -> list[str]:
    p = []
    for x in params.split(","):
        if x.strip() != "":
            p.append(x.strip())
    return p

#  →  ∟

varCmds = ("Disp","Input","Prompt","If","While")
numericFunctions = ("abs", "cos", "sin", "tan", "cosh", "sinh", "tanh")

# parses a function body into a list of TI-Basic compatible lines of code
#   these compatible lines do not have a leading colon, that's to be added
#   when formatting output
def parseFunctionBody(params: list[str], body: str, isMain: bool = False) -> list[str]:
    global localList
    global stackList

    lines = []
    localVarCount = 0
    localVarIndices = {}
    hasTmpVar = False

    def getVarRef(name: str, new: bool = False):
        if name.startswith("."):
            return name[1:]
        elif name in localVarIndices:
            if new:
                return f"{localList}(dim({localList})+1)"
            else:
                return f"{localList}(dim({localList})-{localVarCount-localVarIndices[name]})"
        elif name in params:
            return f"{stackList}(dim({stackList})-{len(params) -params.index(name)})"
        else:
            if not name.isdecimal():
                print(f"Unknown variable name: {name}")
            return name

    def parseNestedExpression(expr: str):
        if "(" not in expr:
            return getVarRef(expr)
        else:
            s = expr.split("(", 1)
            return f"{s[0]}({parseExpression(s[1][:-1])})"

    def parseExpression(expr: str):
        res = ""

        # parse the expression by variable/const + operator
        m = exprParseStep.match(expr)
        while m != None:
            res += parseNestedExpression(m.group(1)) + m.group(2)
            expr = expr[m.end():]
            m = exprParseStep.match(expr)

        # then add the final variable/const
        res += parseNestedExpression(expr.strip())
        return res

    for line in body.splitlines():
        if line.startswith(":"):
            #starting a line with a colon means the user wants to directly program in
            # TI-Basic; we don't touch it 
            lines.append(line[1:])
        elif line.startswith("#") or line.startswith("//"):
            pass # allow for comments in code!! wahoo
        elif line.startswith("Var"):
            # define or operate on a variable
            m = localParser.match(line)

            if not m:
                print(f"Bad variable assignment! {line}")

            name = m.group(1)
            expression = m.group(2)

            if name.strip() == "":
                print(f"VERY BAD NAME: {line}")

            isNew = False
            if name not in params and name not in localVarIndices:
                localVarIndices[name] = localVarCount+1
                localVarCount += 1
                isNew = True

            lines.append(f"{parseExpression(expression)}→{getVarRef(name, isNew)}")
        elif line.startswith("ToSys"):
            #we do minimal parsing and let the user get their local vars into a system variable
            s = line.split("→")
            ps = parseParams(s[0].removeprefix("ToSys "))
            parsedList = ""
            for p in ps:
                parsedList += parseExpression(p) + ","
            if len(ps) > 1:
                lines.append(f"{{{parsedList[:-1]}}}→{s[1]}")
            else:
                lines.append(f"{parsedList[:-1]}→{s[1]}")
        elif line.startswith("Call"):
            # call a subroutine
            m = funcCallParse.match(line)

            if not m:
                print(f"Bad function call: {line}")

            func = m.group(1)

            if func == "Main":
                print(f"DO NOT CALL MAIN: {func}")

            pars = parseParams(m.group(2))

            returnLabel = getLabel()

            # add the requested variables onto the stack
            for p in pars:
                if p.startswith("&"):
                    p = p[1:]
                lines.append(f"{getVarRef(p)}→{stackList}(dim({stackList})+1)")

            # add our return address to the stack
            lines.append(f"{labelIndexLookup[returnLabel]}→{stackList}(dim({stackList})+1)")

            # add the goto branch
            lines.append(f"Goto {functions[func]["label"]}")

            # add our return label
            lines.append(f"Lbl {returnLabel}")

            # set any reference variables to their counterpart from the stack
            for p in pars:
                if p.startswith("&"):
                    lines.append(f"{stackList}(dim({stackList})-{len(pars) - pars.index(p)})→{getVarRef(p[1:])}")

            # free the stack space used
            lines.append(f"dim({stackList})-{len(pars)+1}→dim({stackList})")
        elif line.startswith(varCmds):
            if line.startswith("Input"):
                s = line.removeprefix("Input ")

                # first, we store the current value of I into __TMP
                #  this is created in any function that uses our Input
                lines.append(f"I→{getVarRef("__TMP")}")

                # now, we just do an input into I, then move from I into our variable
                if "," in s:
                    sp = s.split(",")
                    lines.append(f"Input {sp[0]},I")
                    lines.append(f"I→{getVarRef(sp[1])}")
                else:
                    lines.append(f"Input I")
                    lines.append(f"I→{getVarRef(s)}")

                # then restore I
                lines.append(f"{getVarRef("__TMP")}→I")

            elif line.startswith("Disp"):
                s = line.removeprefix("Disp ")
                vs = s.split(",")
                l = "Disp "
                for v in vs:
                    if "\"" in v:
                        l += v + ","
                    else:
                        l += getVarRef(v) + ","
                lines.append(l[:-1])
            elif line.startswith("Prompt"):
                s = line.removeprefix("Prompt ")
                vs = s.split(",")
                l = "Prompt "
                for v in vs:
                    l += getVarRef(v) + ","
                lines.append(l[:-1])
            elif line.startswith("If"):
                lines.append(f"If {parseExpression(line.removeprefix("If "))}")
            elif line.startswith("While"):
                lines.append(f"While {parseExpression(line.removeprefix("While "))}")
        else:
            lines.append(line) # the user probably knows what they're doing

    # add the ending for each type of function
    lines.append(f"dim({localList})-{localVarCount}→dim({localList})")

    if isMain:
        lines.append("Return")
    else:
        lines.append(f"Goto {subReturn}")

    return lines

functions = {}

for match in matches:
    if match[0] in functions:
        print(f"Duplicate function definition: {match[0]}")

    functions[match[0]] = {
        "name": match[0],
        "params": parseParams(match[1]),
        "body": match[2],
        "label": labels.pop() # note that we can interface with the set directly since a function start doesn't get returned to by a subroutine
    }

for fn in functions:
    f = functions[fn]
    if "\nInput " in f["body"]:
        f["body"] = "Var __TMP = 0\n" + f["body"] # hack to make inputs work
    f["code"] = parseFunctionBody(f["params"], f["body"], fn=="Main")

# function parsing complete; check for integrity then construct the program
if "Main" not in functions:
    print("Program MUST have a 'Main()' function!")

header = [
    f"SetUpEditor {stackList},{localList}"
]

with open(f"{filename}.comp", "w", encoding="utf8") as f:
    def proctorWrite(line: str = ""):
        f.write(f"{line}\n")

    # write the header
    for l in header:
        proctorWrite(l)

    # write the call into main
    proctorWrite(f"Goto {functions["Main"]["label"]}")

    # write the return from subroutine section
    proctorWrite()
    proctorWrite(f"Lbl {subReturn}")
    for i in range(labelIndex):
        proctorWrite(f"If {stackList}(dim({stackList}))={i}:Goto {labelIndexLookup[i]}")
    proctorWrite("Disp \"ERROR: Bad call\"")

    # now write all the functions in the program
    for fn in functions:
        proctorWrite()
        func = functions[fn]
        proctorWrite(f"Lbl {func["label"]}")
        for line in func["code"]:
            proctorWrite(line)

pass