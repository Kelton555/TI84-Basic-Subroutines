# TI84-Basic-Subroutines
Quick and dirty 'compiler' from a custom language into TI84 Basic that allows for 'local' variables, a stack, and function calls

## Features
- REAL COMMENTS EXIST!!! Starting a line with # or // in your .txt file will lead to that line being skipped in 'compilation'!
- "Var" directives can be used to create local variables (real numbers only i think please)
    - They follow more [standard](## "fight me") programming A = {Expression} syntax
    - You should always declare your variables outside of any conditionals and before using them for If, Input, Disp, etc.
    - They might even work with abs(), cos(), tan() other single variable functions
- "ToSys" directives can be used to hack things into working (items on the left side of the arrow are parsed by the 'compiler', while the right side is untouched)
    - If a single variable is on the left, it's parsed and left as a single variable. Having multiple variables on the left (comma separated) will parse them into a list
- You can use system variables in the same statements as your local variables (append a '.' in front of the name)
    - E.g. 'Var A = B + C' uses entirely 'local' variables; 'Var A = B + .C' stores the sum of local variable B and system variable C into local variable A
    - I don't actually know if you could add a dot to the left variable in these scenarios. I already forget my implementation and hacks
- Prefixing a line with ':' ensures that the 'compiler' does not touch it (beyond removing the colon)
- Input and If statements should more or less work probably
    - Note that Input statements are really hacky since the TI doesn't want you to input directly into a list element. If a function uses any Input statements with 'local' variables, a '__TMP' variable is created at the start of the function, the current value of I is stored to it, Input goes into I, I goes into the desired variable, and __TMP is put back into I
- Functions (and return values through ""references"")!
    - To define a function, it starts with a Def {FunctionName}(\[v1,v2,v3...\]) and ends with an End {FunctionName}
    - To call a function, the syntax is Call {FunctionName}(\[v1,v2,v3...\])
        - Parameters can be inline constants/expressions(?) or 'local' variables (and maybe even system variables?)
        - ""Reference"" variables are implemented at the call site rather than the declaration
        - For example, if you want to return R from a function Multiply(X,Y,R) then:
            - The declaration is Def Multiply(X,Y,R)
            - The call is Call Multiply(A,B,&C) (where C is a 'local' variable)
    - Internally implemented through Goto, hence the allusion to subroutines
        - This means that you can only have so many function calls because there's like 1400 allowed labels

### It is worth noting that this language is not designed with the idea of being capable of fully replacing TI-Basic; the idea is that you will have a lot of actual TI-Basic imbedded into the code. The 'compiler' only exists to make procedural programming significantly less complex
