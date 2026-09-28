# 2ec
Text UI Calculator

A text-oriented calculator for the terminal.

[![Rust](https://github.com/kda/2ec/actions/workflows/rust.yml/badge.svg)](https://github.com/kda/2ec/actions/workflows/rust.yml)
[![Windows](https://github.com/kda/2ec/actions/workflows/rust_on_windows.yml/badge.svg)](https://github.com/kda/2ec/actions/workflows/rust_on_windows.yml)
[![MacOS](https://github.com/kda/2ec/actions/workflows/rust_on_macos.yml/badge.svg)](https://github.com/kda/2ec/actions/workflows/rust_on_macos.yml)

# Features (completed and functioning)
-   Support for different bases: 2, 8, 10, 16
-   Support for different numeric mdoes: whole number (integer, no decimals), decimal (3.14), scientific (2.03e+4)
-   Basic math operations: add, subtract, multiply, divide, remainder (modulo)
-   Bit operations: AND, OR, XOR, XNOR, invert, left/right shift
-   10 memory locations, to recall the results of previous calculations.
-   Pre-loaded constants.
-   Customizable constants via config file.
-   Built in help system to show how each key works.

# What is in a name?
The name evolved and here are some of the things that played into it.
-   It was the boring **RTC**: Rust Text Calculator.
-   Then I found the rust crate called [rtc](https://webrtc.rs).
-   Renamed to 2ec.
-   Text User Interface is often abbreviated as TUI.  Which I pronounce: *two-eee*.  (Similar to GUI (*goo-eee*).)  I rendered it as **2e**.  **c** stands for calculator.
-   I wanted a short name.
-   2E may refer to [twice-exceptional](https://en.wikipedia.org/wiki/Twice_exceptional).  Which may be a label that applies to those close to me.
-   When spoken rapidly, it could sound like "*too-eee-zee*", which could sound like "**Too Easy**".  Which is how I find using a text calculator like this, as opposed to the more traditional solutions:
    -   *[HP Voyager](https://en.wikipedia.org/wiki/HP_Voyager)*:
        - Leave my beloved text interface and go to another battery powered device, that uses [Reverse Polish Notation](https://en.wikipedia.org/wiki/Reverse_Polish_notation)?  Unthinkable.
    -   *Mobile*:
        - Go to another device?  (I'm already cereberally attached to my computer, why do I need to pick up my mobile.) Uh, no.
    -   *[bc](https://www.gnu.org/software/bc/)*:
        - Fine for the basics, but then I have to dig through the documentation to do anything slightly advanced (left-shift is not available, that I know of).
    -   *Fingers*:
        - Slow and unable to scale.
    -   *[xcalc](https://gitlab.freedesktop.org/xorg/app/xcalc)*:
        - Okay, I'm still on my computer, but now I'm in a different application which overlays others basically doing a text intensive operation. And I already mentioned [RPN](https://en.wikipedia.org/wiki/Reverse_Polish_notation).
    -   *[calctool](https://www.gnu.org/software/bc/)*:
        - Which I have happily used for years in tty mode.
        - In fact, I patched it a number of times and now have a private repository to avoid having to re-patch.
        - And it seems to be dragging along the baggage of a GUI interfaces by simulating buttons on a text screen (which does not make much sense in a terminal, especially if you don't use a mouse, or at least avoid it for daily tasks).
        - It is very good, but sorely needed to be modernized, IMHO.
        - Which leads us to the next point...
-   2E may refer to a "2nd Edition".  This may be thought of as a second edition of **calctool**.

# todo
## features
-   calc
    -   absolute
    -   trunc
    -   frac
- 	add color (if terminal capable and/or if flag)
- 	check terminal size at startup for available space (exit gracefully if insufficient.)
-   display commas (modal, also consider EURO style (.  <-> ,)) (possibly detect based on locale?)
-   develop tests to cover all features
-   detect and enforce maximum length of entry of value
-   consider a help screen which labels the accumulator and pending operation and current value (quick tour?)
-   add marker in display to show mode
-   possibly show first line of display: summary of last action executed
-   have history of operations, and rewind and fast-forward
-   add 'x' for multiply
## refactor
-   reconsider BigText using width and height
    - also, could be optional, based on command line
## bug
-   conversion breakages:
    -   Octal (Decimal) (27) -> ??? (Scientific) (crashes)
-   entered value does not preserve digits: examples:
    -   load constant E when in integer mode, then switch to decimal (no digits right of decimal point)
    -   load constant E when in decimal mode with 2 fixed, then switch to fixed 9 (all zeroes in digits 3-9)
    -   possible solution: store ValuePair with String accumulator
-   first tilde after equals does not change display (not accumulator)
## command line
-   confirm quit request
## preferences (also, all available via command line)
-   start in decimal or scientific mode (or integer (default))
-   start in hex, oct, or bin base (or decimal (default))
-   retain values of storage registers between runs
-   support upper case hex display
-   support upper case e in scientific display (maybe same as hex UPPER)
-   clear screen (before, after)
-   number of significant digits
-   color mode
-   display commas (modal, also consider EURO style (.  <-> ,))
-   display memory registers
-   confirm quit request
## docs
-   configuration file with examples

## discarded attempts
-   BigText Result: cargo add ratatui tui-big-text
    - Octant size did not render correctly
    - Sextant did not either
    - Quadrant was too big


# Developer hints
-   Insta Review
    -   `cargo install cargo-insta`
    -   `cargo insta review`
-   Install
    -   `cargo install --path .`
